#!/usr/bin/env bash
# Usage: sudo env VAR=... bash verify-server.sh        (Ubuntu 26.04 sudo-rs ignores `sudo -E`)
# Optional env:
#   CDN_DOMAIN, SUB_PATH, JSON_PATH, SUB_ID, PANEL_PORT
#   PANEL_BASE, PANEL_TOKEN, PANEL_RESOLVE  — panel API ping
#   REQUIRE_HYSTERIA=1  — fail if UDP 36712 not listening (default 0)
#   ENABLE_IPSUM=1      — require the IPsum nftables table (default 1; set 0 only if deliberately not deployed)
#   PANEL_ACCESS=tunnel — `tunnel` (default): panel port must NOT be open in UFW; `public`: skip that check
#   LOOPBACK=1          — run loopback-test.py (real handshake per inbound; default 1)
#   TLS_PORTS="443 2096" — ports whose SERVED certificate expiry is checked (what clients actually see)
#   WARN_DAYS=30 FAIL_DAYS=7

set -euo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SUB_PATH="${SUB_PATH:-/sub/}"
JSON_PATH="${JSON_PATH:-/json/}"
SUB_ID="${SUB_ID:-}"
PANEL_PORT="${PANEL_PORT:-29800}"
REQUIRE_HYSTERIA="${REQUIRE_HYSTERIA:-0}"
ENABLE_IPSUM="${ENABLE_IPSUM:-1}"
PANEL_ACCESS="${PANEL_ACCESS:-tunnel}"
LOOPBACK="${LOOPBACK:-1}"
TLS_PORTS="${TLS_PORTS:-443 2096}"
WARN_DAYS="${WARN_DAYS:-30}"
FAIL_DAYS="${FAIL_DAYS:-7}"
PANEL_BASE="${PANEL_BASE:-}"
PANEL_TOKEN="${PANEL_TOKEN:-}"
PANEL_RESOLVE="${PANEL_RESOLVE:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB=/etc/x-ui/x-ui.db

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

# Optional AmneziaWG inbound(s): UDP port must listen if enabled
if [[ -r "$DB" ]]; then
  while IFS='|' read -r awg_id awg_port; do
    [[ -z "$awg_id" ]] && continue
    ss -ulnp | grep -q ":${awg_port} " && ok "AmneziaWG inbound ${awg_id}: UDP :${awg_port} listening" \
      || fail "AmneziaWG inbound ${awg_id} enabled but UDP :${awg_port} not listening"
  done < <(sqlite3 "$DB" "SELECT id,port FROM inbounds WHERE protocol='amneziawg' AND enable=1;" 2>/dev/null || true)
fi

# ---- certificates: what clients actually see -----------------------------------------------------
now=$(date +%s)
for p in $TLS_PORTS; do
  end=$(echo | timeout 8 openssl s_client -connect "127.0.0.1:${p}" -servername "$CDN_DOMAIN" 2>/dev/null \
        | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || true)
  if [[ -z "$end" ]]; then warn "no certificate served on :${p} (not a TLS port here?)"; continue; fi
  days=$(( ($(date -d "$end" +%s) - now) / 86400 ))
  if   (( days < 0 ));          then fail "certificate served on :${p} EXPIRED ${days#-} days ago — references/cert-renewal-nginx.md"
  elif (( days < FAIL_DAYS ));  then fail "certificate served on :${p} expires in ${days} days — renewal is broken (scripts/deploy-acme-renewal.sh)"
  elif (( days < WARN_DAYS ));  then warn "certificate served on :${p} expires in ${days} days"
  else ok "certificate served on :${p}: ${days} days left"; fi
done
[[ -x "$HERE/check-cert-expiry.sh" ]] && { bash "$HERE/check-cert-expiry.sh" || fail "certificate files near/after expiry (see above)"; }

# ---- hardening ------------------------------------------------------------------------------------
if [[ "$ENABLE_IPSUM" == "1" ]]; then
  if nft list set inet ipsum blocklist >/dev/null 2>&1; then
    n=$(nft list set inet ipsum blocklist | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | wc -l)
    (( n > 1000 )) && ok "IPsum blocklist loaded (${n} addresses)" || fail "IPsum table present but nearly empty (${n})"
    systemctl is-enabled ipsum-block.timer >/dev/null 2>&1 && ok "IPsum daily refresh timer enabled" || warn "ipsum-block.timer not enabled — list will go stale"
    systemctl is-active ipsum-rollback.timer >/dev/null 2>&1 && fail "ipsum-rollback.timer is still armed — it will DELETE the blocklist; confirm with: CONFIRM=1 deploy-ipsum.sh"
  else
    fail "IPsum nftables table missing (scripts/deploy-ipsum.sh) — set ENABLE_IPSUM=0 only if intentionally skipped"
  fi
fi

if systemctl is-active fail2ban >/dev/null 2>&1; then
  fail2ban-client status sshd >/dev/null 2>&1 && ok "fail2ban active, sshd jail running" || warn "fail2ban active but sshd jail not running"
else
  warn "fail2ban not active (scripts/setup-fail2ban.sh)"
fi

if [[ "$PANEL_ACCESS" == "tunnel" ]]; then
  if ufw status 2>/dev/null | grep -E "^${PANEL_PORT}/tcp" | grep -q ALLOW; then
    warn "panel port ${PANEL_PORT} is ALLOWED in UFW but PANEL_ACCESS=tunnel — close it (references/panel-tunnel-access.md)"
  else
    ok "panel port ${PANEL_PORT} not open in UFW (tunnel-only)"
  fi
fi

if [[ -r "$DB" ]]; then
  mism=$(sqlite3 "$DB" "SELECT h.inbound_id||':'||h.security||'!='||json_extract(i.stream_settings,'\$.security') FROM hosts h JOIN inbounds i ON i.id=h.inbound_id WHERE json_valid(i.stream_settings) AND h.security NOT IN ('same','') AND h.security != json_extract(i.stream_settings,'\$.security');" 2>/dev/null || true)
  [[ -z "$mism" ]] && ok "hosts table consistent with inbound security" \
    || warn "hosts override differs from inbound (subscription links will be wrong): ${mism//$'\n'/ } — references/gotchas.md"
fi

# ---- subscription ---------------------------------------------------------------------------------
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

# ---- real handshake per inbound (the check that cannot be fooled by a client's ping indicator) -----
if [[ "$LOOPBACK" == "1" && -f "$HERE/loopback-test.py" ]]; then
  echo "--- loopback handshake test ---"
  python3 "$HERE/loopback-test.py" && ok "all tested inbounds passed a real handshake" || fail "an inbound failed the real handshake test (see above)"
fi

echo "=== Done ==="
