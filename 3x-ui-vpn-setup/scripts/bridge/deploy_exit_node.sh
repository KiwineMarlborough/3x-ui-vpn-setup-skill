#!/usr/bin/env bash
# Install a SEPARATE Xray exit node for the country bridge on a VDS that may host other services. Does not touch other Xray instances, nginx or other daemons.
# Run as root:  env HUB_IP=<3x-ui hub ip> [PORT=8447] SNI=<site> bash deploy_exit_node.sh   (expects /tmp/xray = Xray binary)
# Afterwards read /opt/xray-exit/client-params.json (root-only) and add it as an outbound on the 3X-UI side.
set -euo pipefail
D=/opt/xray-exit; HUB_IP="${HUB_IP:?set HUB_IP = public IP of the 3X-UI server}"; PORT="${PORT:-8447}"; SNI="${SNI:?set SNI = a TLS 1.3 + h2 site reachable from this VDS}"
[[ $EUID -eq 0 ]] || { echo "run as root"; exit 1; }
[[ -f /tmp/xray ]] || { echo "missing /tmp/xray"; exit 1; }
[[ -e /etc/systemd/system/xray-exit.service ]] && { echo "already installed - stop"; exit 1; }
ss -tln | grep -q ":${PORT} " && { echo "port ${PORT} busy"; exit 1; }

mkdir -p "$D"; install -m 755 -o root -g root /tmp/xray "$D/xray"
OUT=$("$D/xray" x25519)
PRIV=$(echo "$OUT" | sed -n 's/^PrivateKey: *//p' | head -1)
PUB=$(echo "$OUT" | grep -iE '^(Password|PublicKey)' | head -1 | sed 's/^[^:]*: *//')
[[ -n "$PRIV" && -n "$PUB" ]] || { echo "x25519 parse failed"; echo "$OUT" | sed 's/: .*/: <hidden>/'; exit 1; }
UUID=$("$D/xray" uuid); SID=$(openssl rand -hex 8)

PRIV="$PRIV" PUB="$PUB" UUID="$UUID" SID="$SID" SNI="$SNI" PORT="$PORT" D="$D" python3 - <<'PY'
import json, os
e = os.environ
cfg = {
  "log": {"loglevel": "warning"},
  "inbounds": [{
    "tag": "rubridge-in", "listen": "0.0.0.0", "port": int(e["PORT"]), "protocol": "vless",
    "settings": {"clients": [{"id": e["UUID"], "flow": "xtls-rprx-vision", "email": "de-3xui"}], "decryption": "none"},
    "streamSettings": {"network": "tcp", "security": "reality", "realitySettings": {
        "show": False, "dest": e["SNI"] + ":443", "xver": 0, "serverNames": [e["SNI"]],
        "privateKey": e["PRIV"], "shortIds": [e["SID"]]}},
    "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}}],
  "outbounds": [{"tag": "direct", "protocol": "freedom"}, {"tag": "blocked", "protocol": "blackhole"}],
  "routing": {"rules": [
    {"type": "field", "protocol": ["bittorrent"], "outboundTag": "blocked"},
    # never let a client reach this VDS itself (local services, reverse-tunnel / admin ports, ssh) or private nets
    {"type": "field", "ip": ["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16",
                             "100.64.0.0/10", "::1/128", "fc00::/7", "fe80::/10"], "outboundTag": "blocked"}]}
}
d = e["D"]
json.dump(cfg, open(d + "/config.json", "w"), indent=2)
json.dump({"uuid": e["UUID"], "publicKey": e["PUB"], "shortId": e["SID"], "sni": e["SNI"], "port": int(e["PORT"])},
          open(d + "/client-params.json", "w"))
PY
chown root:nogroup "$D/config.json"; chmod 640 "$D/config.json"; chmod 600 "$D/client-params.json"

cat > "$D/fw.sh" <<EOF
#!/bin/sh
# port ${PORT} is reachable only from the 3X-UI hub; added on service start, removed on stop
R="INPUT -p tcp --dport ${PORT} ! -s ${HUB_IP} -j DROP"
case "\$1" in
  up)   iptables -C \$R 2>/dev/null || iptables -I INPUT 1 -p tcp --dport ${PORT} ! -s ${HUB_IP} -j DROP ;;
  down) iptables -D \$R 2>/dev/null || true ;;
esac
EOF
chmod 755 "$D/fw.sh"

cat > /etc/systemd/system/xray-exit.service <<EOF
[Unit]
Description=Xray RU-bridge exit node (separate from the Hub Xray)
After=network-online.target
Wants=network-online.target

[Service]
User=nobody
Group=nogroup
ExecStartPre=+${D}/fw.sh up
ExecStart=${D}/xray run -config ${D}/config.json
ExecStopPost=+${D}/fw.sh down
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
OOMScoreAdjust=500
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

"$D/xray" run -test -config "$D/config.json" 2>&1 | tail -1
systemctl daemon-reload
systemctl enable --now xray-exit
sleep 3
systemctl is-active xray-exit
ss -tlnp | grep ":${PORT} " | awk '{print "listening:", $4}'
iptables -S INPUT | grep -- "--dport ${PORT}" | head -2
echo "mem: $(systemctl show xray-exit -p MemoryCurrent --value) bytes"
rm -f /tmp/xray
echo "DONE (client params in $D/client-params.json, root-only)"
