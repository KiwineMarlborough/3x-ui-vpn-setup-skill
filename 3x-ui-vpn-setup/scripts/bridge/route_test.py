#!/usr/bin/env python3
"""Ask the RUNNING core which outbound it would pick (no traffic is sent).
Usage: python3 route_test.py EMAIL domain [domain ...]"""
import sys

from xui import call

email = sys.argv[1]
for dom in sys.argv[2:]:
    r = call("POST", "/panel/api/xray/routeTest",
             form={"domain": dom, "email": email, "network": "tcp", "port": 443})
    print(email.split("@")[0].ljust(12), dom.ljust(22), "->", r.get("obj"))
