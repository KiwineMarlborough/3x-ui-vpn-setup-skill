#!/usr/bin/env python3
"""Create an outbound subscription (persisted; Xray picks its outbounds up on the next restart).
Usage: echo "$URL" | python3 add_sub.py "sub1 provider" sub1- [interval_seconds=10800]
Tags become <prefix><remark-text> (e.g. sub1-ru). Refresh now: POST /panel/api/xray/outbound-subs/{id}/refresh."""
import sys

from xui import call

url = sys.stdin.read().strip()
remark, prefix = sys.argv[1], sys.argv[2]
interval = int(sys.argv[3]) if len(sys.argv) > 3 else 10800
d = call("POST", "/panel/api/xray/outbound-subs",
         form={"remark": remark, "url": url, "tagPrefix": prefix, "updateInterval": interval, "enabled": "true"})
print("create:", d.get("success"), str(d.get("msg"))[:150])
o = d.get("obj") or {}
if o.get("id"):
    r = call("POST", "/panel/api/xray/outbound-subs/%d/refresh" % o["id"], body={})
    print("refresh:", r.get("success"), "outbounds:", len(r.get("obj") or []))
