#!/usr/bin/env python3
"""Add a new "Bridge" profile (separate line in the subscription) whose whole traffic exits through one outbound
or balancer. Run ON THE 3X-UI SERVER (env XUI_TOKEN / XUI_BASE / XUI_HOST, see xui.py).

Usage:
  python3 add_bridge_profile.py REMARK PORT TAG EMAIL[,EMAIL...] [--balancer] [--template 4] [--outbound-file FILE]
    REMARK   name shown in the app, start it with the country flag emoji (Happ draws the flag from it),
             e.g. "🇺🇸 BridgeUS-ViaProvider"
    PORT     free TCP port of the new inbound on the 3X-UI server (also open it in UFW: sudo ufw allow PORT/tcp)
    TAG      outbound tag (e.g. sub1-usa-1) - or, with --balancer, a balancer tag
    EMAIL    existing clients that get the new line
    --template N   copy stream/sniffing settings (Reality keys, SNI) and the public address from inbound N (default 4)
What it does: creates the inbound, the `hosts` row (public address - without it the link would carry the panel
domain), attaches the clients, appends the routing rule inboundTag -> TAG (after the block rules) and restarts Xray.
Back up /etc/x-ui/x-ui.db first; verify afterwards with route_test.py and a loopback test."""
import json
import sys

from xui import call, template

argv = sys.argv[1:]
balancer = "--balancer" in argv
tpl = 4
ob_file = None
if "--template" in argv:
    k = argv.index("--template")
    tpl = int(argv[k + 1])
    del argv[k:k + 2]
if "--outbound-file" in argv:      # outbound JSON from link_to_outbound.py; its "tag" must equal TAG
    k = argv.index("--outbound-file")
    ob_file = argv[k + 1]
    del argv[k:k + 2]
args = [a for a in argv if not a.startswith("--")]
if len(args) != 4:
    sys.exit(__doc__)
remark, port, tag, emails = args[0], int(args[1]), args[2], args[3].split(",")

if any(i["port"] == port for i in call("GET", "/panel/api/inbounds/list")["obj"]):
    sys.exit("an inbound on port %d already exists" % port)
src = call("GET", "/panel/api/inbounds/get/%d" % tpl)["obj"]
load = lambda v: json.loads(v) if isinstance(v, str) else v
host = call("GET", "/panel/api/hosts/byInbound/%d" % tpl)["obj"][0]
address = host["hosts"][0].rsplit(":", 1)[0]

r = call("POST", "/panel/api/inbounds/add", body={
    "enable": True, "remark": remark, "listen": "", "port": port, "protocol": "vless", "expiryTime": 0, "total": 0,
    "settings": {"clients": [], "decryption": "none", "fallbacks": []},
    "streamSettings": load(src["streamSettings"]), "sniffing": load(src["sniffing"])})
if not r.get("success"):
    sys.exit("inbounds/add failed: %s" % r.get("msg"))
iid, itag = r["obj"]["id"], r["obj"]["tag"]
print("inbound %d tag %s created" % (iid, itag))
print("hosts/add:", call("POST", "/panel/api/hosts/add", body={
    "inboundIds": [iid], "remark": remark, "hosts": [address], "port": port, "security": host["security"],
    "sni": host["sni"], "fingerprint": host["fingerprint"]}).get("success"))
print("attach:", call("POST", "/panel/api/clients/bulkAttach", body={"emails": emails, "inboundIds": [iid]}).get("success"))

t = template()
x = t["xraySetting"]
if ob_file:
    ob = json.load(open(ob_file))
    if ob["tag"] != tag:
        sys.exit("outbound tag %r in the file differs from TAG %r" % (ob["tag"], tag))
    if not any(o.get("tag") == tag for o in x["outbounds"]):
        x["outbounds"].append(ob)      # appended AFTER 'direct' so the default outbound does not change
        print("outbound %s added to the template" % tag)
rule = {"type": "field", "inboundTag": [itag]}
rule["balancerTag" if balancer else "outboundTag"] = tag
if not any(q.get("inboundTag") == [itag] for q in x["routing"]["rules"]):
    x["routing"]["rules"].append(rule)
print("xray/update:", call("POST", "/panel/api/xray/update", form={
    "xraySetting": json.dumps(x, ensure_ascii=False),
    "outboundTestUrl": t.get("outboundTestUrl") or "https://www.google.com/generate_204"}).get("success"))
print("restart:", call("POST", "/panel/api/server/restartXrayService", body={}).get("success"))
print("DONE. Do not forget: sudo ufw allow %d/tcp" % port)
