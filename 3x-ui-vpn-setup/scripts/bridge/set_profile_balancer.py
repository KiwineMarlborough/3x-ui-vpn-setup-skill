#!/usr/bin/env python3
"""Make a profile pick its exit nodes BY NAME PREFIX instead of one fixed outbound tag.
Run ON THE 3X-UI SERVER (env XUI_TOKEN / XUI_BASE / XUI_HOST, see xui.py).

Usage:  python3 set_profile_balancer.py INBOUND_TAG BALANCER_TAG PREFIX[,PREFIX...] [--fallback OUTBOUND_TAG]
Example: python3 set_profile_balancer.py in-8448-tcp BridgeUS-balancer sub1-usa

How it works: outbound tags that come from a subscription are "<prefix of the subscription>-<node name>" (flag emoji
removed, lower case), e.g. sub1-usa-1. An Xray balancer `selector` is matched as a tag PREFIX, so every node whose
name starts with "usa" is in the pool - including nodes the provider adds or renames later - and the
subscription refresh (every 3 h) keeps their addresses current. Strategy leastPing (needs the observatory: the prefixes
are added to burstObservatory.subjectSelector). If no pool node is alive the balancer uses --fallback OUTBOUND_TAG (default `blocked` = the connection fails; without any
fallback Xray would silently send the traffic out of the 3X-UI server's own IP, i.e. from the wrong country).
Back up /etc/x-ui/x-ui.db first; verify with route_test.py / balancerStatus and a loopback test."""
import json
import sys

from xui import call, template

argv = sys.argv[1:]
fallback = "blocked"          # fail closed: if no pool node is alive the connection is dropped instead of leaking out of DE
if "--fallback" in argv:
    k = argv.index("--fallback")
    fallback = argv[k + 1]
    del argv[k:k + 2]
if len(argv) != 3:
    sys.exit(__doc__)
inbound_tag, bal_tag, prefixes = argv[0], argv[1], argv[2].split(",")

t = template()
x = t["xraySetting"]
bal = {"tag": bal_tag, "selector": prefixes, "strategy": {"type": "leastPing"}}
if fallback:
    bal["fallbackTag"] = fallback
x["routing"]["balancers"] = [b for b in x["routing"].get("balancers") or [] if b.get("tag") != bal_tag] + [bal]

obs = x.setdefault("burstObservatory", {"subjectSelector": [],
                                        "pingConfig": {"destination": "http://www.gstatic.com/generate_204",
                                                       "interval": "30s", "sampling": 2, "timeout": "5s"}})
for p in prefixes:
    if p not in obs["subjectSelector"]:
        obs["subjectSelector"].append(p)

hit = False
for r in x["routing"]["rules"]:
    if r.get("inboundTag") == [inbound_tag]:
        r.pop("outboundTag", None)
        r["balancerTag"] = bal_tag
        hit = True
if not hit:
    sys.exit("no routing rule for inbound %s" % inbound_tag)
res = call("POST", "/panel/api/xray/update", form={
    "xraySetting": json.dumps(x, ensure_ascii=False),
    "outboundTestUrl": t.get("outboundTestUrl") or "https://www.google.com/generate_204"})
print("xray/update:", res.get("success"), res.get("msg"))
print("restart:", call("POST", "/panel/api/server/restartXrayService", body={}).get("success"))
