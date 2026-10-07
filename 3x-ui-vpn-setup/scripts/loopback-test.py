#!/usr/bin/env python3
"""End-to-end test of every VLESS inbound with a REAL client handshake, on the server itself.

Builds a temporary Xray *client* config per inbound straight from the panel database
(uuid, flow, Reality public key / shortId / SNI, TLS serverName, XHTTP path ...), connects to
127.0.0.1:<inbound port> and fetches a URL through the local SOCKS port. HTTP 200 = the inbound
works end to end (TLS certificate validity included), independent of the network between you
and the server and of what the client app's ping indicator shows.

Why: a client's latency "n/a"/-1 is unreliable in BOTH directions (Reality often shows n/a while
working), and an expired certificate looks identical to "VPN is blocked". This test tells them apart.

Usage (as root — reads /etc/x-ui/x-ui.db, never writes to it):
    sudo python3 loopback-test.py
    sudo python3 loopback-test.py --email user-main --url https://example.com --only 8443,8444

Skipped (reported, not tested): hysteria (UDP, needs a hysteria client), amneziawg
(check `POST /panel/api/server/amneziawglogs/50`: peer endpoint + traffic), other protocols.
Exit code: 0 if every tested inbound returned HTTP 200, 1 otherwise.
"""
import argparse
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

XRAY = os.environ.get("XRAY_BIN", "/usr/local/x-ui/bin/xray-linux-amd64")
DB = os.environ.get("XUI_DB", "/etc/x-ui/x-ui.db")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def j(v):
    if isinstance(v, (dict, list)) or v is None:
        return v
    try:
        return json.loads(v)
    except Exception:
        return None


def pick_client(settings, email):
    for c in (settings or {}).get("clients", []):
        if c.get("enable", True) and (not email or c.get("email") == email):
            return c
    return None


def flow_for(db, inbound_id, client):
    try:
        row = db.execute(
            "SELECT ci.flow_override FROM client_inbounds ci JOIN clients c ON c.id = ci.client_id "
            "WHERE ci.inbound_id = ? AND c.email = ?", (inbound_id, client.get("email"))).fetchone()
        if row and row[0] is not None:
            return row[0]
    except sqlite3.Error:
        pass
    return client.get("flow", "") or ""


def build_stream(ss):
    """Return (streamSettings, note) for the client outbound, or (None, reason)."""
    net, sec = ss.get("network", "tcp"), ss.get("security", "none")
    st = {"network": net}
    if sec == "reality":
        rs = ss.get("realitySettings", {})
        inner = rs.get("settings", {})
        names = rs.get("serverNames") or [inner.get("serverName", "")]
        ids = rs.get("shortIds") or [""]
        st["security"] = "reality"
        st["realitySettings"] = {
            "serverName": names[0], "fingerprint": inner.get("fingerprint", "chrome"),
            "shortId": ids[0], "publicKey": inner.get("publicKey", ""), "spiderX": inner.get("spiderX", "/"),
        }
    elif sec == "tls":
        ts = ss.get("tlsSettings", {})
        st["security"] = "tls"
        st["tlsSettings"] = {"serverName": ts.get("serverName", "")}
        if ts.get("alpn"):
            st["tlsSettings"]["alpn"] = ts["alpn"]
    else:
        return None, "security=%s not supported by this tester" % sec
    if net == "xhttp":
        xs = ss.get("xhttpSettings", {})
        host = xs.get("host") or (ss.get("tlsSettings", {}).get("serverName") if sec == "tls" else "")
        st["xhttpSettings"] = {"path": xs.get("path", "/"), "mode": xs.get("mode", "auto")}
        if host:
            st["xhttpSettings"]["host"] = host
    elif net != "tcp":
        return None, "network=%s not supported by this tester" % net
    return st, ""


def run_one(row, db, args):
    iid, remark, port, listen, settings_s, stream_s = row
    settings, ss = j(settings_s), j(stream_s) or {}
    client = pick_client(settings, args.email)
    if not client:
        return "SKIP", "no enabled client%s" % (" with that email" if args.email else "")
    st, note = build_stream(ss)
    if st is None:
        return "SKIP", note
    user = {"id": client["id"], "encryption": "none"}
    flow = flow_for(db, iid, client)
    if flow:
        user["flow"] = flow
    socks = free_port()
    cfg = {
        "log": {"loglevel": "warning"},
        "inbounds": [{"listen": "127.0.0.1", "port": socks, "protocol": "socks", "settings": {"udp": False}}],
        "outbounds": [{"protocol": "vless", "settings": {"vnext": [{
            "address": listen if listen not in ("", "0.0.0.0", "::") else "127.0.0.1",
            "port": port, "users": [user]}]}, "streamSettings": st}],
    }
    with tempfile.TemporaryDirectory() as d:
        cfg_path, log_path = os.path.join(d, "c.json"), os.path.join(d, "x.log")
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)
        with open(log_path, "w") as lf:
            proc = subprocess.Popen([XRAY, "run", "-c", cfg_path], stdout=lf, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                try:
                    socket.create_connection(("127.0.0.1", socks), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.1)
            out = subprocess.run(
                ["curl", "-s", "--socks5-hostname", "127.0.0.1:%d" % socks, "-m", str(args.timeout),
                 "-o", os.devnull, "-w", "%{http_code}", args.url],
                capture_output=True, text=True).stdout.strip() or "000"
        finally:
            proc.terminate()
            try:
                proc.wait(3)
            except subprocess.TimeoutExpired:
                proc.kill()
        log = open(log_path, errors="replace").read()
    hint = ""
    if out != "200":
        if "certificate has expired" in log:
            hint = "TLS certificate on this inbound is EXPIRED (references/cert-renewal-nginx.md)"
        elif "x509" in log:
            hint = "TLS certificate problem: " + log.strip().splitlines()[-1][-160:]
        elif "REALITY" in log or "reality" in log:
            hint = "Reality handshake rejected — check publicKey/shortId/SNI/dest"
        elif log.strip():
            hint = log.strip().splitlines()[-1][-160:]
    return ("OK" if out == "200" else "FAIL"), "HTTP %s%s" % (out, ("  <- " + hint) if hint else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email", help="test with this client (default: first enabled client of each inbound)")
    ap.add_argument("--url", default=os.environ.get("TEST_URL", "https://example.com"))
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--only", help="comma-separated inbound ports to test")
    args = ap.parse_args()

    if not os.path.exists(XRAY):
        sys.exit("xray binary not found: %s (set XRAY_BIN)" % XRAY)
    db = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    only = {int(p) for p in args.only.split(",")} if args.only else None
    rows = db.execute("SELECT id, remark, port, listen, settings, stream_settings, protocol, enable FROM inbounds ORDER BY id").fetchall()

    bad = 0
    print("%-4s %-28s %-6s %-22s %s" % ("id", "remark", "port", "transport", "result"))
    for iid, remark, port, listen, settings_s, stream_s, proto, enable in rows:
        if only and port not in only:
            continue
        ss = j(stream_s) or {}
        transport = "%s/%s" % (ss.get("network", "-"), ss.get("security", "-"))
        label = (remark or "")[:28]
        if not enable:
            print("%-4s %-28s %-6s %-22s SKIP  disabled" % (iid, label, port, proto))
            continue
        if proto == "vless":
            status, msg = run_one((iid, remark, port, listen, settings_s, stream_s), db, args)
        elif proto == "hysteria":
            status, msg = "SKIP", "UDP — test with a real hysteria client"
        elif proto == "amneziawg":
            status, msg = "SKIP", "check amneziawglogs: peer endpoint + client traffic (references/amneziawg.md)"
        else:
            status, msg = "SKIP", "protocol %s not covered" % proto
        if status == "FAIL":
            bad += 1
        if ss.get("security") == "reality" and ss.get("network") == "xhttp":
            msg += "  [note: XHTTP+REALITY was broken on Xray 26.7.28 — references/gotchas.md]"
        print("%-4s %-28s %-6s %-22s %-5s %s" % (iid, label, port, transport, status, msg))
    print("\n%s" % ("ALL TESTED INBOUNDS OK" if not bad else "%d inbound(s) FAILED" % bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
