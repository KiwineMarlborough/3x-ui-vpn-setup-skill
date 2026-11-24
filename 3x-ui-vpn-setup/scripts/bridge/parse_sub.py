#!/usr/bin/env python3
"""Preview a subscription WITHOUT saving anything: lists parsed outbounds (tag | protocol | transport).
Usage (on server):  echo "$URL" | python3 parse_sub.py      (URL on stdin so it never lands in shell history)
Writes the full parsed list to /tmp/parsed.json (used by test_ru_node.py); delete it afterwards."""
import json
import sys

from xui import call

url = sys.stdin.read().strip()
d = call("POST", "/panel/api/xray/outbound-subs/parse", form={"url": url}, timeout=60)
print("success:", d.get("success"), str(d.get("msg"))[:150])
items = d.get("obj") or []
json.dump(items, open("/tmp/parsed.json", "w"))
for o in items:
    st = o.get("streamSettings") or {}
    print(" -", o.get("tag"), "|", o.get("protocol"), "|", st.get("network"), "/", st.get("security"))
print(len(items), "outbounds")
