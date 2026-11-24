#!/usr/bin/env python3
"""Route one client (by email) to an outbound/balancer, optionally only for some domains.
Usage: python3 add_user_rule.py EMAIL OUTBOUND_TAG [domain-token ...]
  no domains  -> ALL traffic of that user goes to OUTBOUND_TAG
  domains     -> only those (e.g. ext:geosite_RU.dat:RU-AVAILABLE-ONLY-INSIDE domain:example.ru), the rest stays direct
Inserts the rule right after the built-in api rule; refuses if a rule for this user already exists.
Back up /etc/x-ui/x-ui.db first and run `xray run -test` after; restart: POST /panel/api/server/restartXrayService."""
import json
import sys

from xui import call, template

email, tag, domains = sys.argv[1], sys.argv[2], sys.argv[3:]
geo = [d for d in domains if d.startswith(("geosite:", "ext:"))]
if geo:
    v = call("POST", "/panel/api/xray/geodata/validate", form={"tokens": ",".join(geo)})
    print("unresolved geo tokens (empty = all found):", v.get("obj"))
t = template()
x = t["xraySetting"]
rule = {"type": "field", "user": [email], "outboundTag": tag}
if domains:
    rule["domain"] = domains
if any(r.get("user") == [email] for r in x["routing"]["rules"]):
    sys.exit("rule for this user already exists - edit it in the panel")
x["routing"]["rules"].insert(1, rule)
r = call("POST", "/panel/api/xray/update",
         form={"xraySetting": json.dumps(x, ensure_ascii=False),
               "outboundTestUrl": t.get("outboundTestUrl") or "https://www.google.com/generate_204"})
print("update:", r.get("success"), r.get("msg"))
