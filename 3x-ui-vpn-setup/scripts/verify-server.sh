#!/usr/bin/env bash
# Usage: sudo bash verify-server.sh
# Optional env:
#   CDN_DOMAIN, SUB_PATH, JSON_PATH, SUB_ID, PANEL_PORT
#   PANEL_BASE, PANEL_TOKEN, PANEL_RESOLVE  — panel API ping
#   REQUIRE_HYSTERIA=1  — fail if UDP 36712 not listening (default 0)

set -euo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SUB_PATH="${SUB_PATH:-/sub/}"
JSON_PATH="${JSON_PATH:-/json/}"
SUB_ID="${SUB_ID:-}"
PANEL_PORT="${PANEL_PORT:-29800}"
REQUIRE_HYSTERIA="${REQUIRE_HYSTERIA:-0}"
PANEL_BASE="${PANEL_BASE:-}"
PANEL_TOKEN="${PANEL_TOKEN:-}"
PANEL_RESOLVE="${PANEL_RESOLVE:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

echo "=== 3X-UI Server Verification ==="

command -v x-ui >/dev/null 2>&1 || fail "x-ui not found"
sudo x-ui status | grep -qi active && ok "x-ui service active" || fail "x-ui not active"

XRAY_BIN="/usr/local/x-ui/bin/xray-linux-amd64"
CFG="/usr/local/x-ui/bin/config.json"
[[ -f "$XRAY_BIN" && -f "$CFG" ]] || fail "Xray binary or config missing"
if sudo "$XRAY_BIN" run -test -c "$CFG" 2>&1 | grep -q "Configuration OK"; then
  ok "Xray config OK"
else
  fail "Xray config test failed"
fi

if sudo tail -30 /var/log/x-ui/3xui.log 2>/dev/null | grep -qi 'version != 2'; then
  fail "Log contains hysteria version != 2 — run fix-hysteria-stream.py"
fi

for p in 8443 8444 2053 2096; do
  ss -tlnp | grep -q ":${p} " && ok "TCP :${p} listening" || fail "TCP :${p} not listening"
done

if ss -ulnp | grep -q ":36712 "; then
  ok "UDP :36712 listening"
elif [[ "$REQUIRE_HYSTERIA" == "1" ]]; then
  fail "UDP :36712 not listening (REQUIRE_HYSTERIA=1)"
else
  warn "UDP :36712 not listening (Hysteria disabled?)"
fi

if [[ -n "$SUB_ID" ]]; then
  SUB_URL="https://${CDN_DOMAIN}:2096${SUB_PATH}${SUB_ID}"
  JSON_URL="https://${CDN_DOMAIN}:2096${JSON_PATH}${SUB_ID}"
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$SUB_URL")
  [[ "$CODE" == "200" ]] && ok "Subscription HTTP $CODE" || fail "Subscription HTTP $CODE"
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$JSON_URL")
  [[ "$CODE" == "200" ]] && ok "JSON sub HTTP $CODE" || fail "JSON sub HTTP $CODE"

  BODY=$(curl -sk "$SUB_URL")
  VLESS_COUNT=$(echo "$BODY" | grep -o 'vless://' | wc -l | tr -d ' ')
  HY2_COUNT=$(echo "$BODY" | grep -o 'hysteria2://' | wc -l | tr -d ' ')
  TOTAL=$((VLESS_COUNT + HY2_COUNT))
  [[ "$VLESS_COUNT" -ge 3 ]] && ok "Found ${VLESS_COUNT} vless:// links" || fail "Expected ≥3 vless://, got ${VLESS_COUNT}"
  [[ "$HY2_COUNT" -ge 1 ]] && ok "Found ${HY2_COUNT} hysteria2:// link" || warn "No hysteria2:// in sub (Hysteria off?)"
  [[ "$TOTAL" -ge 4 ]] && ok "Total profiles in sub: ${TOTAL}" || warn "Expected 4 profiles, got ${TOTAL}"

  curl -skI "$SUB_URL" | grep -qi "routing-enable: true" && ok "Routing-Enable header present" || warn "Routing-Enable not set"
else
  warn "Set SUB_ID to test subscription URLs and profile count"
fi

if [[ -n "$PANEL_BASE" && -n "$PANEL_TOKEN" ]]; then
  CURL_CMD=(curl -sk -X POST -H "Authorization: Bearer ${PANEL_TOKEN}" -H "Content-Type: application/json" -d '{}')
  [[ -n "$PANEL_RESOLVE" ]] && CURL_CMD+=(--resolve "$PANEL_RESOLVE")
  CURL_CMD+=("${PANEL_BASE}/panel/api/setting/all")
  if "${CURL_CMD[@]}" | grep -q '"success":true'; then
    ok "Panel API reachable"
  else
    warn "Panel API check failed"
  fi
fi

systemctl is-active nginx >/dev/null 2>&1 && ok "nginx active" || warn "nginx not running"
CDN_CODE=$(curl -sk -o /dev/null -w '%{http_code}' "https://${CDN_DOMAIN}/" 2>/dev/null || echo "000")
[[ "$CDN_CODE" == "200" ]] && ok "HTTPS :443 CDN page HTTP $CDN_CODE" || warn "CDN HTTPS check failed (HTTP $CDN_CODE, expected 200)"

echo "=== Done ==="