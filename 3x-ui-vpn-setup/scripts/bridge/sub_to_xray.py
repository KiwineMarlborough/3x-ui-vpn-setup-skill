#!/usr/bin/env python3
"""AGENT SIDE (python3 stdlib only). Turn a 3X-UI subscription into an Xray *client* config that exposes a local
SOCKS5 + HTTP proxy, so any program on the agent's server can reach the Internet through a chosen bridge profile.

Usage:
  SUB_URL='https://.../<sub>' python3 sub_to_xray.py --list                       # show profile names
  SUB_URL='https://.../<sub>' python3 sub_to_xray.py --profile BridgeRUBalancier > /etc/xray-agent/config.json
  options: --sub URL (instead of env SUB_URL)  --link 'vless://...' (single link instead of a subscription)
           --socks 1080  --http 1081  (local ports, bound to 127.0.0.1 only)
--profile is a case-insensitive part of the profile name and must match exactly one line.
Supported profile types: VLESS + Reality (tcp), VLESS + TLS (tcp / xhttp). Hysteria2 lines are listed but skipped.
The subscription URL / link are secrets: pass them via env or a secret store, never commit them."""
import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    body = urllib.request.urlopen(req, timeout=30).read().decode().strip()
    if "://" not in body:
        body = base64.b64decode(body + "=" * (-len(body) % 4)).decode()
    return [l.strip() for l in body.splitlines() if "://" in l]


def name_of(link):
    return urllib.parse.unquote(link.rsplit("#", 1)[-1]) if "#" in link else ""


def build(link, socks, http):
    u = urllib.parse.urlsplit(link)
    if u.scheme != "vless":
        sys.exit("unsupported scheme %s for profile %r" % (u.scheme, name_of(link)))
    q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
    net, sec = q.get("type", "tcp"), q.get("security", "none")
    if net == "raw":  # newer Xray/provider links call plain TCP "raw"
        net = "tcp"
    ss = {"network": net, "security": sec}
    if sec == "reality":
        ss["realitySettings"] = {"serverName": q.get("sni", ""), "fingerprint": q.get("fp", "chrome"),
                                 "publicKey": q["pbk"], "shortId": q.get("sid", ""), "spiderX": q.get("spx", "/")}
    elif sec == "tls":
        ss["tlsSettings"] = {"serverName": q.get("sni", u.hostname),
                             "alpn": q["alpn"].split(",") if q.get("alpn") else None}
        if q.get("fp"):
            ss["tlsSettings"]["fingerprint"] = q["fp"]
        ss["tlsSettings"] = {k: v for k, v in ss["tlsSettings"].items() if v}
    if net == "xhttp":
        ss["xhttpSettings"] = {"path": q.get("path", "/"), "host": q.get("host", ""), "mode": q.get("mode", "auto")}
    elif net != "tcp":
        sys.exit("unsupported transport %s" % net)
    out = {"tag": "bridge", "protocol": "vless",
           "settings": {"vnext": [{"address": u.hostname, "port": u.port,
                                   "users": [{"id": u.username, "encryption": q.get("encryption", "none"),
                                              "flow": q.get("flow", "")}]}]},
           "streamSettings": ss}
    return {"log": {"loglevel": "warning"},
            "inbounds": [{"tag": "socks-in", "listen": "127.0.0.1", "port": socks, "protocol": "socks",
                          "settings": {"udp": True}},
                         {"tag": "http-in", "listen": "127.0.0.1", "port": http, "protocol": "http"}],
            "outbounds": [out, {"tag": "direct", "protocol": "freedom"}],
            "routing": {"rules": [{"type": "field", "inboundTag": ["socks-in", "http-in"], "outboundTag": "bridge"}]}}


ap = argparse.ArgumentParser()
ap.add_argument("--sub"); ap.add_argument("--link"); ap.add_argument("--profile"); ap.add_argument("--list", action="store_true")
ap.add_argument("--socks", type=int, default=1080); ap.add_argument("--http", type=int, default=1081)
a = ap.parse_args()
if a.link:
    links = [a.link]
else:
    url = a.sub or os.environ.get("SUB_URL")
    if not url:
        sys.exit("give --sub URL, env SUB_URL or --link")
    links = fetch(url)
if a.list or not a.profile:
    for l in links:
        print("-", name_of(l) or l[:40], "(%s)" % l.split("://")[0])
    sys.exit(0)
hit = [l for l in links if a.profile.lower() in name_of(l).lower()]
if len(hit) != 1:
    sys.exit("profile %r matches %d lines (need exactly 1); use --list" % (a.profile, len(hit)))
json.dump(build(hit[0], a.socks, a.http), sys.stdout, indent=2, ensure_ascii=False)
print()
