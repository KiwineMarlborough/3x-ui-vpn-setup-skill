#!/usr/bin/env python3
"""Live check of ONE outbound before it goes into production: a temporary Xray client (loopback only) -> exit IP,
country, provider and a few sites. Nothing is saved to the panel. Run on the 3X-UI server.
Usage:  python3 test_outbound.py outbound.json            (file made by link_to_outbound.py)
        python3 test_outbound.py --tag sub1-xxx            (an outbound that is already in the running config)"""
import json
import os
import subprocess
import sys
import tempfile
import time

XRAY = "/usr/local/x-ui/bin/xray-linux-amd64"
if sys.argv[1] == "--tag":
    ob = [o for o in json.load(open("/usr/local/x-ui/bin/config.json"))["outbounds"] if o["tag"] == sys.argv[2]][0]
else:
    ob = json.load(open(sys.argv[1]))
tag = ob["tag"]
cfg = {"log": {"loglevel": "error"},
       "inbounds": [{"tag": "i", "listen": "127.0.0.1", "port": 19620, "protocol": "socks", "settings": {"udp": False}}],
       "outbounds": [ob], "routing": {"rules": [{"type": "field", "inboundTag": ["i"], "outboundTag": tag}]}}
f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
json.dump(cfg, f)
f.close()
t = subprocess.run([XRAY, "run", "-test", "-c", f.name], capture_output=True, text=True)
if "Configuration OK" not in t.stdout + t.stderr:
    print("config invalid:", (t.stdout + t.stderr).strip().splitlines()[-1])
    sys.exit(1)
p = subprocess.Popen([XRAY, "run", "-c", f.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)


def cu(*a):
    o = subprocess.run(["curl", "-sk", "-m", "15", "--socks5-hostname", "127.0.0.1:19620", "-A", "Mozilla/5.0"] + list(a),
                       capture_output=True, text=True)
    return o.stdout.strip() or "-"


print("tag:", tag)
print("exit ip:", cu("https://ipinfo.io/ip"), "| country:", cu("https://ipinfo.io/country"), "| org:", cu("https://ipinfo.io/org"))
for u in ("https://www.google.com/generate_204", "https://chatgpt.com/", "https://www.netflix.com/"):
    print("  %-38s" % u, cu("-o", "/dev/null", "-w", "%{http_code} %{time_total}s", u))
p.terminate()
os.unlink(f.name)
