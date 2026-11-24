#!/usr/bin/env python3
"""Create a client attached to inbounds. Usage: python3 add_client.py EMAIL "comment" 3,4,5,2
Flow is left empty (same as the existing user-main) so it works on every inbound. subId is random:
the subscription URL is https://<domain>:<subPort><subPath><subId> - treat it as a secret."""
import secrets
import sys

from xui import call

email, comment, ids = sys.argv[1], sys.argv[2], [int(i) for i in sys.argv[3].split(",")]
cl = {"email": email, "subId": secrets.token_hex(8), "enable": True, "limitIp": 0, "totalGB": 0,
      "expiryTime": 0, "comment": comment}
r = call("POST", "/panel/api/clients/add", body={"client": cl, "inboundIds": ids})
print("clients/add:", r.get("success"), r.get("msg"))
