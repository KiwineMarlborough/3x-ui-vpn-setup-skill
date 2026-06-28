#!/usr/bin/env bash
# Read-only server audit — no changes.
#
# Usage:
#   export CDN_DOMAIN=cdn.vpn.example.com
#   export SUB_PATH=/xK9mP2qR/
#   export JSON_PATH=/j4nR8wLz3k/
#   export SUB_ID=<uuid>   # optional
#   bash audit-server.sh

set -uo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SUB_PATH="${SUB_PATH:-/sub/}"
JSON_PATH="${JSON_PATH:-/json/}"
SUB_ID="${SUB_ID:-}"

echo "=== 3X-UI Audit (read-only) ==="
date -Is 2>/dev/null || date

echo ""
echo "--- Services ---"
command -v x-ui >/dev/null && sudo x-ui status 2>/dev/null | head -5 || echo "x-ui: not found"
systemctl is-active nginx >/dev/null 2>&1 && echo "nginx: active" || echo "nginx: inactive"

echo ""
echo "--- Xray test ---"
XRAY="/usr/local/x-ui/bin/xray-linux-amd64"
CFG="/usr/local/x-ui/bin/config.json"
if [[ -f "$XRAY" && -f "$CFG" ]]; then
  sudo "$XRAY" run -test -c "$CFG" 2>&1 | tail -3
else
  echo "Xray binary/config missing"
fi

echo ""
echo "--- Ports ---"
ss -tlnp 2>/dev/null | grep -E ':8443 |:8444 |:2053 |:2096 |:443 |:29800 ' || echo "No expected TCP ports"
ss -ulnp 2>/dev/null | grep ':36712 ' || echo "UDP 36712: not listening"

echo ""
echo "--- UFW ---"
sudo ufw status 2>/dev/null | head -20 || echo "ufw: n/a"

echo ""
echo "--- Inbounds (sqlite) ---"
sudo sqlite3 /etc/x-ui/x-ui.db \
  "SELECT id,remark,port,protocol,enable FROM inbounds ORDER BY id;" 2>/dev/null \
  || echo "sqlite: cannot read x-ui.db"

echo ""
echo "--- Panel settings (sqlite) ---"
sudo sqlite3 /etc/x-ui/x-ui.db \
  "SELECT key,value FROM settings WHERE key IN (
    'webDomain','webPort','webBasePath','subPath','subJsonPath',
    'subEncrypt','subJsonEnable','subEnableRouting'
  ) ORDER BY key;" 2>/dev/null || true

echo ""
echo "--- Recent log (hysteria/version) ---"
sudo tail -20 /var/log/x-ui/3xui.log 2>/dev/null | grep -iE 'error|hysteria|version' || \
  sudo tail -5 /var/log/x-ui/3xui.log 2>/dev/null || echo "no log"

if [[ -n "$SUB_ID" ]]; then
  echo ""
  echo "--- Subscription ---"
  SUB="https://${CDN_DOMAIN}:2096${SUB_PATH}${SUB_ID}"
  JSON="https://${CDN_DOMAIN}:2096${JSON_PATH}${SUB_ID}"
  curl -sk -o /dev/null -w "plain sub: %{http_code}\n" "$SUB"
  curl -sk -o /dev/null -w "json sub:  %{http_code}\n" "$JSON"
  curl -skI "$SUB" 2>/dev/null | grep -iE 'routing|http/' || true
  BODY=$(curl -sk "$SUB" 2>/dev/null || true)
  echo "profile hints: vless=$(echo "$BODY" | grep -c vless || echo 0) hysteria2=$(echo "$BODY" | grep -c hysteria2 || echo 0)"
fi

echo ""
echo "=== Audit done ==="