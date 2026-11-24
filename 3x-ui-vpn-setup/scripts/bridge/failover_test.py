#!/usr/bin/env python3
"""Live failover test of a balancer profile: temporarily DROPs outbound traffic to the tier-1 node, watches the
exit IP of the balancer profile switch to the fallback, then removes the block and waits for the return.
Run as root ON THE 3X-UI SERVER. The block is a single iptables OUTPUT rule that is always removed (try/finally).
Usage: sudo env XUI_TOKEN=.. XUI_BASE=/path XUI_HOST=domain python3 failover_test.py \
          INBOUND_ID EMAIL TIER1_OUTBOUND_TAG TIER1_EXIT_IP FALLBACK_EXIT_IP
Example: ... failover_test.py 9 agent@example.com sub1-ru 203.0.113.10 203.0.113.20
It builds a temporary local Xray client from the inbound's own credentials (loopback), so it needs no phone."""
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

XRAY = "/usr/local/x-ui/bin/xray-linux-amd64"
TOKEN, BASE, HOST = os.environ["XUI_TOKEN"], os.environ["XUI_BASE"].rstrip("/"), os.environ["XUI_HOST"]
iid, email, tier1_tag, tier1_ip, fb_ip = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
LIMIT_BLOCK, LIMIT_BACK = int(os.environ.get("LIMIT_BLOCK", 330)), int(os.environ.get("LIMIT_BACK", 300))

db = sqlite3.connect("/etc/x-ui/x-ui.db")
node = [o for o in json.load(open("/usr/local/x-ui/bin/config.json"))["outbounds"] if o["tag"] == tier1_tag][0]


def find_addr(d):
    if isinstance(d, dict):
        if isinstance(d.get("address"), str):
            return d["address"]
        for v in d.values():
            r = find_addr(v)
            if r:
                return r
    if isinstance(d, list):
        for v in d:
            r = find_addr(v)
            if r:
                return r


node_ip = socket.gethostbyname(find_addr(node["settings"]))
port = db.execute("select port from inbounds where id=?", (iid,)).fetchone()[0]
ss = json.loads(db.execute("select stream_settings from inbounds where id=?", (iid,)).fetchone()[0])["realitySettings"]
cl = [x for x in json.loads(db.execute("select settings from inbounds where id=?", (iid,)).fetchone()[0])["clients"]
      if x["email"] == email][0]
ob = {"tag": "p", "protocol": "vless",
      "settings": {"vnext": [{"address": "127.0.0.1", "port": port,
                              "users": [{"id": cl["id"], "encryption": "none", "flow": cl.get("flow", "")}]}]},
      "streamSettings": {"network": "tcp", "security": "reality", "realitySettings": {
          "serverName": ss["serverNames"][0], "fingerprint": "chrome", "publicKey": ss["settings"]["publicKey"],
          "shortId": ss["shortIds"][0], "spiderX": "/"}}}
cfg = {"log": {"loglevel": "error"},
       "inbounds": [{"tag": "i", "listen": "127.0.0.1", "port": 19301, "protocol": "socks", "settings": {"udp": False}}],
       "outbounds": [ob]}
f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
json.dump(cfg, f)
f.close()
p = subprocess.Popen([XRAY, "run", "-c", f.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)


def exit_ip():
    o = subprocess.run(["curl", "-s", "-m", "8", "--socks5-hostname", "127.0.0.1:19301", "https://ipinfo.io/ip"],
                       capture_output=True, text=True)
    return o.stdout.strip() or "-"


def observatory():
    o = subprocess.run(["curl", "-sk", "--resolve", "%s:29800:127.0.0.1" % HOST, "-H", "Authorization: Bearer " + TOKEN,
                        "https://%s:29800%s/panel/api/server/xrayObservatory" % (HOST, BASE)],
                       capture_output=True, text=True)
    try:
        return {x["tag"]: x["alive"] for x in json.loads(o.stdout)["obj"]}
    except Exception:
        return {}


RULE = ["OUTPUT", "-d", node_ip, "-j", "DROP"]


def ipt(action):
    return subprocess.run(["iptables", action] + RULE, capture_output=True).returncode


t0 = time.time()
print("before: exit", exit_ip(), "observatory", observatory(), flush=True)
try:
    subprocess.run(["iptables", "-I", "OUTPUT", "1", "-d", node_ip, "-j", "DROP"], check=True)
    print("BLOCKED outbound to the tier-1 node (temporary)", flush=True)
    switched = None
    while time.time() - t0 < LIMIT_BLOCK:
        time.sleep(15)
        e = exit_ip()
        print("  t+%3ds exit=%s obs=%s" % (time.time() - t0, e, observatory()), flush=True)
        if e.startswith(fb_ip):
            switched = time.time() - t0
            break
    print("FAILOVER to fallback after ~%ds" % switched if switched else "NO FAILOVER within %ds" % LIMIT_BLOCK, flush=True)
finally:
    while ipt("-C") == 0:
        ipt("-D")
    print("block removed; rule still present:", ipt("-C") == 0, flush=True)
t1 = time.time()
back = None
while time.time() - t1 < LIMIT_BACK:
    time.sleep(15)
    e = exit_ip()
    print("  recover t+%3ds exit=%s obs=%s" % (time.time() - t1, e, observatory()), flush=True)
    if e.startswith(tier1_ip):
        back = time.time() - t1
        break
print("BACK to tier-1 after ~%ds" % back if back else "did not return to tier-1 within %ds" % LIMIT_BACK, flush=True)
p.terminate()
os.unlink(f.name)
