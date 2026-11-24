#!/usr/bin/env python3
"""Create access for a new agent/service in the RU-bridge: one 3X-UI client attached to the bridge profiles.
Run ON THE 3X-UI SERVER (needs XUI_TOKEN / XUI_BASE / XUI_HOST, see xui.py).

Usage:  python3 add_agent.py EMAIL ["comment"] [--all]
  EMAIL      unique client name, convention <name>@<domain>, e.g. agent-name@example.com
  default    attaches the client only to inbounds whose remark contains "Bridge" (the RU-bridge lines)
  --all      attaches to every enabled vless/hysteria inbound (like a personal account)
  --only TXT attaches only to inbounds whose remark contains TXT, e.g. --only OwnVDS (own node only,
             for data that must not pass through third-party provider nodes)
Prints one line  SUBURL=<personal subscription url>  -> that URL is a SECRET: redirect it into a local file
(ssh ... > agents/<name>-sub.txt), never paste it into chat, git or logs.
Revoke:  POST /panel/api/clients/del/<EMAIL>   (or disable it in the panel)."""
import secrets
import sys

from xui import call

argv = sys.argv[1:]
only = None
if "--only" in argv:                       # --only TEXT : attach only to inbounds whose remark contains TEXT
    k = argv.index("--only")
    only = argv[k + 1].lower()
    del argv[k:k + 2]
args = [a for a in argv if not a.startswith("--")]
all_inbounds = "--all" in argv
if not args:
    sys.exit(__doc__)
email = args[0]
comment = args[1] if len(args) > 1 else "agent access (RU-bridge)"

if call("GET", "/panel/api/clients/get/" + email).get("obj"):
    sys.exit("client %s already exists" % email)
inbounds = call("GET", "/panel/api/inbounds/list")["obj"]
ids = [i["id"] for i in inbounds
       if i.get("enable") and i.get("protocol") in ("vless", "hysteria")
       and (all_inbounds or (only or "bridge") in (i.get("remark") or "").lower())]
if not ids:
    sys.exit("no matching inbounds found")

sub_id = secrets.token_hex(8)
cl = {"email": email, "subId": sub_id, "enable": True, "limitIp": 0, "totalGB": 0, "expiryTime": 0, "comment": comment}
r = call("POST", "/panel/api/clients/add", body={"client": cl, "inboundIds": ids})
if not r.get("success"):
    sys.exit("clients/add failed: %s" % r.get("msg"))
base = call("POST", "/panel/api/setting/all", body={})["obj"]["subURI"]
sys.stderr.write("created %s on inbounds %s\n" % (email, ids))
print("SUBURL=" + base.rstrip("/") + "/" + sub_id)
