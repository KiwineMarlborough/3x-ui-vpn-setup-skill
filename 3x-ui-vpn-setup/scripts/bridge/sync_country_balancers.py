#!/usr/bin/env python3
"""Keep country pools in sync with the FLAG emoji of the nodes in an outbound subscription (v2).
Run ON THE 3X-UI SERVER (env XUI_TOKEN / XUI_BASE / XUI_HOST, see xui.py). Safe to run often: it only touches the
panel (and restarts Xray) when something really changes.

Usage:
  python3 sync_country_balancers.py --sub "sub1 provider" --map US=BridgeUS-balancer,IN=BridgeIN-balancer \
          [--map RU=BridgeRU-balancer,RU=BridgeRU-provider-balancer] [--dry-run]
  --sub   remark of the outbound subscription in the panel (its URL is read from the panel)
  --map   COUNTRY=BALANCER_TAG pairs (ISO code of the flag; one country may feed several balancers)
  --tolerate FLAG=EXITCC[,...]  extra exit countries that are accepted for a flag, e.g. IN=NL: the provider's "India"
          nodes sit on addresses that public geo databases place in the Netherlands, so without this the live check
          would exclude every India node (profile unavailable). Everything else stays strict.

How it works (why v2 copies nodes):
  * The provider's names/flags and the panel's outbound TAGS do not stay in step: the provider reshuffles which server
    carries which name, and the panel derives a tag from a name only at its own refresh time (a node labelled "USA" can
    sit under the tag sub1-jp). So tags cannot be used as country names.
  * An Xray balancer `selector` is matched as a tag PREFIX: the tag sub1-jp also matches sub1-jp-1 (another node,
    another country). So even a "correct" tag list can pull in a wrong neighbour.
  Therefore for every managed country the script (1) reads the subscription links, (2) takes the flag (two regional
  indicator symbols = ISO country code) of each link, (3) finds the matching outbound in the panel by address + uuid / auth
  (then address + port if unique), (4) stores a COPY of that outbound in the Xray template under the stable tag
  `ctry-<CC>-<n>` (e.g. ctry-US-1), and (5) points the balancer `selector` at the prefix `ctry-<CC>-` and the observatory at
  the same prefix. Copies are refreshed on every run, so address changes at the provider are picked up within the hour.
  If a country has no node at the moment, its copies and balancers are left untouched (warning in the log).
Run it from a systemd timer (see deploy_country_sync.sh)."""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

from xui import call, template

argv = sys.argv[1:]
dry = "--dry-run" in argv
sub_remark, pairs = None, []
tolerate = {}                               # flag country -> extra exit countries accepted for it (e.g. IN -> {NL})
i = 0
while i < len(argv):
    if argv[i] == "--sub":
        sub_remark = argv[i + 1]
        i += 2
    elif argv[i] == "--map":
        pairs += [tuple(p.split("=", 1)) for p in argv[i + 1].split(",")]
        i += 2
    elif argv[i] == "--tolerate":
        for fc, ec in (p.split("=", 1) for p in argv[i + 1].split(",")):
            tolerate.setdefault(fc, set()).add(ec)
        i += 2
    else:
        i += 1
if not sub_remark or not pairs:
    sys.exit(__doc__)
managed = sorted({c for c, _ in pairs})


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    try:
        with open("/var/log/country-balancers.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def flag_country(name):
    cps = [ord(c) for c in name[:4]]
    if len(cps) >= 2 and all(0x1F1E6 <= c <= 0x1F1FF for c in cps[:2]):
        return "".join(chr(c - 0x1F1E6 + 65) for c in cps[:2])
    return None


def host_port(u):
    """host/port of a link; tolerates IPv6 hosts written without brackets"""
    netloc = u.netloc.rsplit("@", 1)[-1]
    if netloc.startswith("["):
        host, _, port = netloc[1:].partition("]")
        port = port.lstrip(":")
    else:
        host, _, port = netloc.rpartition(":")
    return host, (int(port) if port.isdigit() else None)


def addr_port(o):
    s = o.get("settings") or {}
    if s.get("address") and s.get("port"):
        return s["address"], s["port"]
    v = (s.get("vnext") or s.get("servers") or [{}])[0]
    return v.get("address"), v.get("port")


sub = [s for s in call("GET", "/panel/api/xray/outbound-subs")["obj"] if s["remark"] == sub_remark]
if not sub:
    sys.exit("outbound subscription %r not found" % sub_remark)
sub = sub[0]
req = urllib.request.Request(sub["url"], headers={"User-Agent": sub.get("userAgent") or "3x-ui-outbound-sub/1.0"})
body = None
for attempt in range(1, 4):                 # a provider hiccup must not break the hourly run
    try:
        body = urllib.request.urlopen(req, timeout=30).read().decode().strip()
        break
    except Exception as e:                  # noqa: BLE001
        log("subscription fetch failed (attempt %d/3): %s" % (attempt, str(e)[:100]))
        time.sleep(5 * attempt)
if body is None:
    log("giving up this run; nothing changed")
    sys.exit(0)
if "://" not in body:
    import base64
    body = base64.b64decode(body + "=" * (-len(body) % 4)).decode()
links = [l.strip() for l in body.splitlines() if "://" in l]

t = template()
outs = t["subscriptionOutbounds"]


def find_outbound(u):
    host, port = host_port(u)
    for o in outs:
        s = o.get("settings") or {}
        if o["protocol"] == "vless" and s.get("address") == host and s.get("id") == u.username and s.get("port") == port:
            return o
        if o["protocol"] == "hysteria" and s.get("address") == host and s.get("port") == port:
            auth = ((o.get("streamSettings") or {}).get("hysteriaSettings") or {}).get("auth")
            if auth == urllib.parse.unquote(u.username or ""):
                return o
    cand = [o for o in outs if addr_port(o) == (host, port)]
    return cand[0] if len(cand) == 1 else None


XRAY = "/usr/local/x-ui/bin/xray-linux-amd64"


def mask(host):
    p = (host or "").split(".")
    return ".".join(p[:2] + ["x", "x"]) if len(p) == 4 and all(q.isdigit() for q in p) else (host or "")[:8] + "..."


def exit_countries(o, port):
    """LIVE check: country codes that two independent geo services report for the exit of this node (empty = no answer)"""
    cfg = {"log": {"loglevel": "error"},
           "inbounds": [{"tag": "i", "listen": "127.0.0.1", "port": port, "protocol": "socks", "settings": {"udp": False}}],
           "outbounds": [dict(o, tag="v")],
           "routing": {"rules": [{"type": "field", "inboundTag": ["i"], "outboundTag": "v"}]}}
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(cfg, f)
    f.close()
    p = subprocess.Popen([XRAY, "run", "-c", f.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    got = set()
    try:
        time.sleep(3)
        for url in ("https://ipinfo.io/country", "https://ipapi.co/country/"):
            r = subprocess.run(["curl", "-sk", "-m", "12", "--socks5-hostname", "127.0.0.1:%d" % port, "-A", "Mozilla/5.0", url],
                               capture_output=True, text=True)
            v = r.stdout.strip().upper()
            if len(v) == 2 and v.isalpha():
                got.add(v)
    finally:
        p.terminate()
        time.sleep(1)
        os.unlink(f.name)
    return got


nodes = {c: [] for c in managed}            # country -> [outbound dicts in subscription order]
for l in links:
    u = urllib.parse.urlsplit(l)
    c = flag_country(urllib.parse.unquote(u.fragment))
    if c in nodes:
        o = find_outbound(u)
        if o is None:
            log("note: a %s-flagged link has no matching panel outbound (not merged yet?) - retried next run" % c)
        elif o not in nodes[c]:
            nodes[c].append(o)

x = t["xraySetting"]
prefix = lambda c: "ctry-%s-" % c
touched = [c for c in managed if nodes[c]]
flagged_count = {c: len(nodes[c]) for c in managed}

# VERIFY every chosen node live: audit line per node; a node that definitely exits in ANOTHER country is excluded
for c in touched:
    keep = []
    for n, o in enumerate(nodes[c]):
        host, port = addr_port(o)
        got = exit_countries(o, 19800 + n)
        what = "%s <- flag %s, %s:%s" % (prefix(c) + str(len(keep) + 1), c, mask(host), port)
        if not got:
            log("AUDIT %s: exit check gave no answer (node down?) - kept" % what)
            keep.append(o)
        elif c in got:
            log("AUDIT %s: exit country %s matches the flag - ok" % (what, "/".join(sorted(got))))
            keep.append(o)
        elif got & tolerate.get(c, set()):
            log("AUDIT %s: exit country %s is not %s but is explicitly tolerated for this flag - kept" % (what, "/".join(sorted(got)), c))
            keep.append(o)
        else:
            log("ERROR %s: node exits in %s, NOT %s - EXCLUDED from the pool" % (what, "/".join(sorted(got)), c))
    nodes[c] = keep
for c in managed:
    if not nodes[c]:
        log("WARNING: no node with flag %s in the subscription - its copies and balancers are left unchanged" % c)

# 1) copies of the chosen nodes under stable tags
def clone(o, tag):
    d = json.loads(json.dumps(o))
    d["tag"] = tag
    return d


old_clones = {o["tag"]: o for o in x["outbounds"] if any(o["tag"].startswith(prefix(c)) for c in touched)}
new_clones = {}
for c in touched:
    for n, o in enumerate(nodes[c], 1):
        new_clones["%s%d" % (prefix(c), n)] = clone(o, "%s%d" % (prefix(c), n))
    if not nodes[c]:        # every flagged node failed the check: a black hole keeps the pool valid and traffic fail-closed
        new_clones[prefix(c) + "0"] = {"tag": prefix(c) + "0", "protocol": "blackhole"}
        log("ERROR no verified node for %s - the pool is a black hole until a good node appears" % c)
changed = []
if old_clones != new_clones:
    changed.append("node copies: %s -> %s" % (sorted(old_clones), sorted(new_clones)))
    x["outbounds"] = [o for o in x["outbounds"] if o["tag"] not in old_clones] + [new_clones[k] for k in sorted(new_clones)]

# 2) balancers select the stable prefix
bals = {b["tag"]: b for b in x["routing"].get("balancers") or []}
for c, btag in pairs:
    if c not in touched:
        continue
    want = [prefix(c)]
    if btag in bals:
        if bals[btag].get("selector") != want:
            changed.append("%s selector %s -> %s" % (btag, bals[btag].get("selector"), want))
            bals[btag]["selector"] = want
    else:
        changed.append("%s created (selector %s)" % (btag, want))
        x["routing"].setdefault("balancers", []).append(
            {"tag": btag, "selector": want, "strategy": {"type": "leastPing"}, "fallbackTag": "blocked"})

# 3) observatory probes the same prefixes (drops the old sub1-* entries earlier versions added)
obs = x.setdefault("burstObservatory", {"subjectSelector": [], "pingConfig": {
    "destination": "http://www.gstatic.com/generate_204", "interval": "30s", "sampling": 2, "timeout": "5s"}})
old_obs = list(obs["subjectSelector"])
desired = [s for s in old_obs if not s.startswith("sub1-")] + [prefix(c) for c in managed if prefix(c) not in old_obs and (c in touched or prefix(c) in old_obs)]
if desired != old_obs:
    changed.append("observatory subjects: %s -> %s" % (old_obs, desired))
    obs["subjectSelector"] = desired

if not changed:
    log("no change; managed countries (verified nodes): " + json.dumps({c: len(nodes[c]) for c in managed}))
    sys.exit(0)
for c in changed:
    log("CHANGE " + c)
if dry:
    log("dry-run: nothing applied")
    sys.exit(0)
r = call("POST", "/panel/api/xray/update", form={"xraySetting": json.dumps(x, ensure_ascii=False),
         "outboundTestUrl": t.get("outboundTestUrl") or "https://www.google.com/generate_204"})
log("xray/update: %s" % r.get("success"))
if r.get("success"):
    log("restart: %s" % call("POST", "/panel/api/server/restartXrayService", body={}).get("success"))
