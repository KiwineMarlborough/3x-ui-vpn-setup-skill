#!/usr/bin/env python3
"""Turn ONE share link into an Xray *outbound* JSON (stdlib only). The link is read from stdin (it is a secret).
Usage:  echo "$LINK" | python3 link_to_outbound.py TAG > outbound.json
Supported: vless:// (Reality or TLS, tcp/raw or xhttp) and hysteria2:// (hy2://, TLS, version 2).
Not supported (exits with an error instead of guessing): obfs/salamander on hysteria2, insecure=1 without a pinned cert.
The result is the object for `outbounds[]` of the 3X-UI Xray template (see add_bridge_profile.py --outbound-file)."""
import json
import sys
import urllib.parse

tag = sys.argv[1]
link = sys.stdin.read().strip()
u = urllib.parse.urlsplit(link)
q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}

if u.scheme == "vless":
    net, sec = q.get("type", "tcp"), q.get("security", "none")
    net = "tcp" if net == "raw" else net
    ss = {"network": net, "security": sec}
    if sec == "reality":
        ss["realitySettings"] = {"serverName": q.get("sni", ""), "fingerprint": q.get("fp", "chrome"),
                                 "publicKey": q["pbk"], "shortId": q.get("sid", ""), "spiderX": q.get("spx", "/")}
    elif sec == "tls":
        ss["tlsSettings"] = {k: v for k, v in {"serverName": q.get("sni", u.hostname), "fingerprint": q.get("fp"),
                                               "alpn": q["alpn"].split(",") if q.get("alpn") else None}.items() if v}
    if net == "xhttp":
        ss["xhttpSettings"] = {"path": q.get("path", "/"), "host": q.get("host", ""), "mode": q.get("mode", "auto")}
    elif net != "tcp":
        sys.exit("unsupported transport: " + net)
    out = {"tag": tag, "protocol": "vless",
           "settings": {"vnext": [{"address": u.hostname, "port": u.port,
                                   "users": [{"id": u.username, "encryption": q.get("encryption", "none"),
                                              "flow": q.get("flow", "")}]}]},
           "streamSettings": ss}
elif u.scheme in ("hysteria2", "hy2"):
    if q.get("obfs"):
        sys.exit("hysteria2 obfs is not supported by this converter")
    if q.get("insecure") in ("1", "true") and not q.get("pinSHA256"):
        sys.exit("insecure=1 without pinSHA256 is not supported (allowInsecure is deprecated in Xray)")
    tls = {"serverName": q.get("sni", u.hostname), "alpn": ["h3"], "fingerprint": "", "echConfigList": "",
           "pinnedPeerCertSha256": q.get("pinSHA256", ""), "verifyPeerCertByName": ""}
    out = {"tag": tag, "protocol": "hysteria",
           "settings": {"address": u.hostname, "port": u.port, "version": 2},
           "streamSettings": {"network": "hysteria", "security": "tls", "tlsSettings": tls,
                              "hysteriaSettings": {"auth": urllib.parse.unquote(u.username or ""),
                                                   "udpIdleTimeout": 60, "version": 2}}}
else:
    sys.exit("unsupported scheme: " + u.scheme)
json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
print()
