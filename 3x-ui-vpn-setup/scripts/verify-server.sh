#!/usr/bin/env bash
# Usage: sudo bash verify-server.sh
# Optional env: CDN_DOMAIN, SUB_PATH, JSON_PATH, SUB_ID, PANEL_PORT

set -euo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SUB_PATH="${SUB_PATH:-/sub/}"
JSON_PATH="${JSON_PATH:-/json/}"
SUB_ID="${SUB_ID:-}"
PANEL_PORT="${PANEL_PORT:-29800}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ok()  { echo -e "${GREEN}[OK]${NC} $*"; }
fail(){ echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

echo "=== 3X-UI Server Verification ==="

command -v x-ui >/dev/null 2>&1 || fail "x-ui not found"
sudo x-ui status | grep -qi active && ok "x-ui service active" || fail "x-ui not active"

XRAY_BIN="/usr/local/x-ui/bin/xray-linux-amd64"
CFG="/usr/local/x-ui/bin/config.json"
[[ -f "$XRAY_BIN" && -f "$CFG" ]] || fail "Xray binary or config missing"
sudo "$XRAY_BIN" run -test -c "$CFG" | grep -q "Configuration OK" && ok "Xray config OK" || fail "Xray config test failed"

for p in 8443 8444 2053 2096; do
  ss -tlnp | grep -q ":${p} " && ok "TCP :${p} listening" || fail "TCP :${p} not listening"
done

ss -ulnp | grep -q ":36712 " && ok "UDP :36712 listening" || echo "[WARN] UDP :36712 not listening (Hysteria disabled?)"

if [[ -n "$SUB_ID" ]]; then
  SUB_URL="https://${CDN_DOMAIN}:2096${SUB_PATH}${SUB_ID}"
  JSON_URL="https://${CDN_DOMAIN}:2096${JSON_PATH}${SUB_ID}"
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$SUB_URL")
  [[ "$CODE" == "200" ]] && ok "Subscription HTTP $CODE" || fail "Subscription HTTP $CODE"
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$JSON_URL")
  [[ "$CODE" == "200" ]] && ok "JSON sub HTTP $CODE" || fail "JSON sub HTTP $CODE"
  curl -skI "$SUB_URL" | grep -qi "routing-enable: true" && ok "Routing-Enable header present" || echo "[WARN] Routing-Enable not set"
else
  echo "[SKIP] Set SUB_ID to test subscription URLs"
fi

systemctl is-active nginx >/dev/null 2>&1 && ok "nginx active" || echo "[INFO] nginx not running"
curl -sk -o /dev/null -w '' "https://${CDN_DOMAIN}/" 2>/dev/null && ok "HTTPS :443 CDN page reachable" || echo "[WARN] CDN HTTPS check failed"

echo "=== Done ==="