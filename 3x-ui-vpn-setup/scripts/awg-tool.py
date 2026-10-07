#!/usr/bin/env python3
"""AmneziaWG 3.1 in 3X-UI (>= 3.7, native inbound): create / rotate obfuscation / render client .conf.

Run ON THE SERVER (the panel is normally closed to the internet; the API is reached on 127.0.0.1).

Environment (never hard-code secrets):
    XUI_TOKEN   panel API token (Settings -> API tokens)
    XUI_BASE    panel webBasePath, e.g. /AbCdEf123456          (create, rotate)
    XUI_HOST    panel hostname = `webDomain` (sent as Host header; the panel answers 403 for any other)
    XUI_PORT    panel port (default 29800)

Subcommands:
  create   [--profile full|minimal] [--dry-run]
           env: AWG_PORT=56100  AWG_SUBNET=10.66.66.0/24  AWG_DNS=1.1.1.1,8.8.8.8
                AWG_REMARK="DE-AWG-3.1"  SHARE_ADDR=<public hostname for Endpoint>
                AWG_CLIENTS=router,phone   (one client per device = own keys, own stats, revocable)
           full    = generated AmneziaWG 3.1 set (junk, padding, H1-H4, I1, HeaderProtectionKey, timings...)
           minimal = classic values, H1-H4 blank, no 3.1 extras: a conservative starter that is useful to
                     prove the UDP path first, but easier to fingerprint. Move to `full` once traffic flows.
  rotate   [--apply]     replace obfuscation on an existing inbound (env INBOUND_ID). Keys/subnet/clients kept.
                         All client configs must be re-rendered and re-imported afterwards.
  render   --host H --out DIR [--inbound ID]    write <email>.conf per client from the panel database (root).

Open the UDP port in the firewall yourself (ufw allow <AWG_PORT>/udp) — this tool does not touch UFW.
Generator mirrors frontend/src/lib/xray/amneziawg-obfuscation.ts of 3X-UI v3.9.0; the panel validates on save.
"""
import argparse
import base64
import http.client
import json
import os
import random
import sqlite3
import ssl
import sys

rnd = random.SystemRandom()
ri = lambda a, b: rnd.randint(a, b)


def gen_full():
    jmin = ri(40, 89)
    s1, s2 = ri(15, 150), ri(15, 150)
    while s1 + 56 == s2:
        s2 = ri(15, 150)
    band = (2147483647 - 5 + 1) // 4
    h = [str(ri(5 + i * band, 5 + i * band + band - 1)) for i in range(4)]
    cp_lo = ri(8, 24)
    cp_hi = cp_lo + ri(8, 40)
    rk_lo = ri(100, 120)
    rk_hi = rk_lo + ri(10, 40)
    rj_lo = rk_hi + ri(30, 60)
    rt_lo, ka_lo, at_lo = ri(3, 6), ri(8, 12), ri(15, 25)
    s4 = ri(12, 27)
    o = dict(
        jc=ri(3, 6), jmin=jmin, jmax=jmin + ri(50, 250), s1=s1, s2=s2, s3=ri(12, 55), s4=s4,
        h1=h[0], h2=h[1], h3=h[2], h4=h[3], i1="<r %d>" % ri(32, 256), i2="", i3="", i4="", i5="",
        headerProtectionKey=base64.b64encode(os.urandom(32)).decode(),
        contentPaddingAddition="%d-%d" % (cp_lo, cp_hi),
        rekeyAfterTime="%d-%d" % (rk_lo, rk_hi), rekeyTimeout="%d-%d" % (rt_lo, rt_lo + ri(1, 4)),
        rejectAfterTime="%d-%d" % (rj_lo, rj_lo + ri(30, 90)), keepaliveTimeout="%d-%d" % (ka_lo, ka_lo + ri(2, 8)),
        maxHandshakeAttempts="%d-%d" % (at_lo, at_lo + ri(5, 25)), randomTrailers=True, disableCookies=True)
    # The panel's default MTU (1420 - S4) ignores ContentPaddingAddition/RandomTrailers: keep headroom
    # so padded packets do not fragment ("connected, but nothing loads").
    o["mtu"] = max(1280, min(1380, 1500 - 60 - s4 - cp_hi - 32))
    return o


def gen_minimal():
    return dict(jc=4, jmin=48, jmax=128, s1=20, s2=119, s3=55, s4=17, h1="", h2="", h3="", h4="",
                i1="", i2="", i3="", i4="", i5="", headerProtectionKey="", contentPaddingAddition="",
                rekeyAfterTime="", rekeyTimeout="", rejectAfterTime="", keepaliveTimeout="",
                maxHandshakeAttempts="", randomTrailers=False, disableCookies=False, mtu=1380)


def validate(o):
    assert o["jmin"] <= o["jmax"], "Jmin must not exceed Jmax"
    assert 0 <= o["s1"] <= 1552 and 0 <= o["s2"] <= 1608 and o["s1"] + 56 != o["s2"], "S1/S2 invalid (S1+56 must differ from S2)"
    if o["headerProtectionKey"]:
        assert all(o[k] >= 12 for k in ("s1", "s2", "s3", "s4")), "with HeaderProtectionKey every S1-S4 must be >= 12"
        hs = [int(o["h%d" % i]) for i in range(1, 5)]
        assert len(set(hs)) == 4 and min(hs) > 4, "H1-H4 must be 4 distinct values > 4"
        assert int(o["rekeyAfterTime"].split("-")[1]) < int(o["rejectAfterTime"].split("-")[0]), "RekeyAfter must stay below RejectAfter"


class Panel:
    def __init__(self):
        self.token = os.environ["XUI_TOKEN"]
        self.base = os.environ["XUI_BASE"].rstrip("/")
        self.host = os.environ["XUI_HOST"]
        self.port = int(os.environ.get("XUI_PORT", "29800"))

    def call(self, method, path, body=None):
        c = http.client.HTTPSConnection("127.0.0.1", self.port, context=ssl._create_unverified_context(), timeout=30)
        h = {"Authorization": "Bearer " + self.token, "Host": "%s:%d" % (self.host, self.port)}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        c.request(method, self.base + path, body=data, headers=h)
        r = c.getresponse()
        txt = r.read().decode()
        ok = r.status == 200 and '"success":true' in txt.replace(" ", "")
        return ok, r.status, txt


def mask(o):
    m = dict(o)
    if m.get("headerProtectionKey"):
        m["headerProtectionKey"] = m["headerProtectionKey"][:6] + "...(hidden)"
    return m


def cmd_create(a):
    obf = gen_full() if a.profile == "full" else gen_minimal()
    validate(obf)
    port = int(os.environ.get("AWG_PORT", "56100"))
    net, _, cidr = os.environ.get("AWG_SUBNET", "10.66.66.0/24").partition("/")
    dns = (os.environ.get("AWG_DNS", "1.1.1.1,8.8.8.8").split(",") + ["8.8.8.8"])[:2]
    share = os.environ.get("SHARE_ADDR", "")
    server = dict(subnetIp=net, subnetCidr=int(cidr or 24), primaryDns=dns[0].strip(), secondaryDns=dns[1].strip(),
                  externalInterface="", ipv6Enabled=False, ipv6Subnet="", ipv6ExternalInterface="")
    server.update(obf)
    payload = {
        "remark": os.environ.get("AWG_REMARK", "AWG-3.1"), "enable": True, "listen": "", "port": port,
        "protocol": "amneziawg", "expiryTime": 0, "total": 0, "trafficReset": "never",
        "settings": {"server": server, "clients": []}, "streamSettings": {},
        "sniffing": {"enabled": False, "destOverride": ["http", "tls"], "metadataOnly": False, "routeOnly": False},
    }
    if share:
        payload.update({"shareAddrStrategy": "custom", "shareAddr": share})
    clients = [c.strip() for c in os.environ.get("AWG_CLIENTS", "").split(",") if c.strip()]
    if a.dry_run:
        p = json.loads(json.dumps(payload))
        p["settings"]["server"] = mask(p["settings"]["server"])
        print(json.dumps(p, indent=1, ensure_ascii=False))
        print("clients to add:", clients or "(none)")
        return 0
    panel = Panel()
    ok, st, txt = panel.call("POST", "/panel/api/inbounds/add", payload)
    print("inbounds/add:", st, txt[:160])
    if not ok:
        return 1
    iid = json.loads(txt)["obj"]["id"]
    for email in clients:
        ok, st, txt = panel.call("POST", "/panel/api/clients/add", {
            "client": {"email": email, "enable": True, "totalGB": 0, "expiryTime": 0, "limitIp": 0, "keepAlive": 25,
                       "comment": "AmneziaWG " + email}, "inboundIds": [iid]})
        print("clients/add %s:" % email, st, txt[:120])
        if not ok:
            return 1
    print("inbound id =", iid, "| next: ufw allow %d/udp, then render configs: awg-tool.py render --host <endpoint> --out <dir>" % port)
    return 0


def cmd_rotate(a):
    iid = os.environ.get("INBOUND_ID", "")
    if not iid:
        sys.exit("set INBOUND_ID")
    panel = Panel()
    ok, st, txt = panel.call("GET", "/panel/api/inbounds/get/%s" % iid)
    if not ok:
        sys.exit("cannot read inbound: %s %s" % (st, txt[:200]))
    ib = json.loads(txt)["obj"]
    settings = ib["settings"] if isinstance(ib["settings"], dict) else json.loads(ib["settings"])
    new = gen_full()
    validate(new)
    settings["server"].update(new)
    payload = {k: ib[k] for k in ("id", "remark", "enable", "expiryTime", "trafficReset", "trafficResetDay", "listen",
                                  "port", "protocol", "tag", "shareAddrStrategy", "shareAddr", "disableFlow") if k in ib}
    payload["settings"] = settings
    payload["streamSettings"] = ib.get("streamSettings") or {}
    payload["sniffing"] = ib.get("sniffing") or {"enabled": False, "destOverride": ["http", "tls"], "metadataOnly": False, "routeOnly": False}
    print("new obfuscation:", json.dumps(mask(new), ensure_ascii=False))
    print("kept: server keys, subnet, DNS, %d client(s)" % len(settings.get("clients", [])))
    if not a.apply:
        print("(dry-run; add --apply). After applying: re-render and re-import EVERY client config.")
        return 0
    ok, st, txt = panel.call("POST", "/panel/api/inbounds/update/%s" % iid, payload)
    print("inbounds/update:", st, txt[:160])
    return 0 if ok else 1


def eff_mtu(m, s4):
    return m if m and m > 0 else max(1420 - max(s4 or 0, 0), 1280)


def cmd_render(a):
    db = sqlite3.connect("file:%s?mode=ro" % os.environ.get("XUI_DB", "/etc/x-ui/x-ui.db"), uri=True)
    port, settings = db.execute("SELECT port, settings FROM inbounds WHERE id=?", (a.inbound,)).fetchone()
    st = json.loads(settings)
    s = st["server"]
    os.makedirs(a.out, exist_ok=True)
    for c in st["clients"]:
        L = ["[Interface]", "PrivateKey = " + c["privateKey"], "Address = " + c["allowedIPs"][0]]
        dns = [d for d in (s.get("primaryDns"), s.get("secondaryDns")) if d]
        if dns:
            L.append("DNS = " + ", ".join(dns))
        L.append("MTU = %d" % eff_mtu(s.get("mtu"), s.get("s4")))
        L += ["Jc = %d" % s["jc"], "Jmin = %d" % s["jmin"], "Jmax = %d" % s["jmax"], "S1 = %d" % s["s1"], "S2 = %d" % s["s2"]]
        if s.get("s3"):
            L.append("S3 = %d" % s["s3"])
        if s.get("s4"):
            L.append("S4 = %d" % s["s4"])
        for i in range(1, 5):
            v = (s.get("h%d" % i) or "").strip()
            L.append("H%d = %s" % (i, v if v else i))
        for i in range(1, 6):
            v = (s.get("i%d" % i) or "").strip()
            if v:
                L.append("I%d = %s" % (i, v))
        for label, key in [("HeaderProtectionKey", "headerProtectionKey"), ("ContentPaddingAddition", "contentPaddingAddition"),
                           ("RekeyAfterTime", "rekeyAfterTime"), ("RekeyTimeout", "rekeyTimeout"),
                           ("RejectAfterTime", "rejectAfterTime"), ("KeepaliveTimeout", "keepaliveTimeout"),
                           ("MaxHandshakeAttempts", "maxHandshakeAttempts")]:
            v = (s.get(key) or "").strip()
            if v:
                L.append("%s = %s" % (label, v))
        if s.get("randomTrailers"):
            L.append("RandomTrailers = on")
        if s.get("disableCookies"):
            L.append("DisableCookies = on")
        L += ["", "# " + c["email"], "[Peer]", "PublicKey = " + s["publicKey"]]
        if c.get("preSharedKey"):
            L.append("PresharedKey = " + c["preSharedKey"])
        L += ["AllowedIPs = 0.0.0.0/0, ::/0", "Endpoint = %s:%d" % (a.host, port)]
        if (c.get("keepAlive") or 0) > 0:
            L.append("PersistentKeepalive = %d" % c["keepAlive"])
        path = os.path.join(a.out, c["email"] + ".conf")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", newline="\n") as f:
            f.write("\n".join(L) + "\n")
        print("wrote", path, c["allowedIPs"])
    print("Files contain private keys (mode 600): deliver via a secure channel, never commit.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--profile", choices=["full", "minimal"], default="full")
    c.add_argument("--dry-run", action="store_true")
    r = sub.add_parser("rotate")
    r.add_argument("--apply", action="store_true")
    n = sub.add_parser("render")
    n.add_argument("--host", required=True, help="public hostname/IP clients connect to (Endpoint)")
    n.add_argument("--out", required=True)
    n.add_argument("--inbound", type=int, default=int(os.environ.get("INBOUND_ID", "0") or 0))
    a = ap.parse_args()
    if a.cmd == "render" and not a.inbound:
        sys.exit("give --inbound ID (or INBOUND_ID)")
    sys.exit({"create": cmd_create, "rotate": cmd_rotate, "render": cmd_render}[a.cmd](a))


if __name__ == "__main__":
    main()
