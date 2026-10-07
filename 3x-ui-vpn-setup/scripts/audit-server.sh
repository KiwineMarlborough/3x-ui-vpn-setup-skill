#!/usr/bin/env bash
# Read-only server audit — changes nothing.
#
# Usage (as root or via sudo):
#   sudo env CDN_DOMAIN=cdn.vpn.example.com SUB_PATH=/xK9mP2qR/ JSON_PATH=/zP4mQ8vN2c/ SUB_ID=<uuid> bash audit-server.sh
#   (Ubuntu 26.04 sudo-rs ignores `sudo -E`; pass variables with `sudo env VAR=... bash ...`)
#
# Looks for the problems that actually hurt in production:
#   expired/stale certificates, leftover users + temporary sudo rules + extra SSH keys (previous
#   agents/installers), UFW exposure, missing IPsum/Fail2Ban, subscription-link overrides (`hosts`
#   table) that disagree with the inbound, nginx sites-enabled copies, pending reboot.

set -uo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SUB_PATH="${SUB_PATH:-/sub/}"
JSON_PATH="${JSON_PATH:-/json/}"
SUB_ID="${SUB_ID:-}"
PANEL_PORT="${PANEL_PORT:-29800}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB=/etc/x-ui/x-ui.db
SQ() { sudo sqlite3 "$DB" "$1" 2>/dev/null; }

echo "=== 3X-UI Audit (read-only) ==="
date -Is 2>/dev/null || date

echo ""
echo "--- System ---"
. /etc/os-release 2>/dev/null && echo "OS: $PRETTY_NAME"; uname -r
[[ -f /var/run/reboot-required ]] && echo "REBOOT PENDING: $(tr '\n' ' ' < /var/run/reboot-required.pkgs 2>/dev/null)" || echo "reboot: not pending"
echo "sudo: $(sudo --version 2>/dev/null | head -1)  (sudo-rs ignores 'sudo -E')"

echo ""
echo "--- Services ---"
command -v x-ui >/dev/null && sudo x-ui status 2>/dev/null | head -5 || echo "x-ui: not found"
for s in nginx fail2ban ufw ssh; do systemctl is-active "$s" >/dev/null 2>&1 && echo "$s: active" || echo "$s: INACTIVE"; done
sudo grep -hE "^(Version|Current x-ui)" /usr/local/x-ui/*.txt 2>/dev/null | head -1
/usr/local/x-ui/bin/xray-linux-amd64 -version 2>/dev/null | head -1

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
echo "--- Certificates (files + served) ---"
if [[ -x "$HERE/check-cert-expiry.sh" ]]; then sudo bash "$HERE/check-cert-expiry.sh"; else echo "check-cert-expiry.sh not found next to this script"; fi
for p in 443 2096; do
  end=$(echo | timeout 8 openssl s_client -connect "127.0.0.1:${p}" -servername "$CDN_DOMAIN" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  echo "served on :${p}: ${end:-none}"
done
echo "acme.sh renewals:"; sudo /root/.acme.sh/acme.sh --list 2>/dev/null || echo "  acme.sh not at /root/.acme.sh"
sudo crontab -l 2>/dev/null | grep -E "acme|certbot" || echo "  NO acme/certbot cron entry in root crontab"
sudo grep -E "^Le_Webroot|^Le_Alt|^Le_NextRenewTimeStr" /root/.acme.sh/*_ecc/*.conf 2>/dev/null | sed 's/^/  /' | head -12
echo "  (Le_Webroot='no' = standalone: needs a FREE port 80 -> fails while nginx owns it)"

echo ""
echo "--- Ports ---"
ss -tlnp 2>/dev/null | grep -E ':8443 |:8444 |:2053 |:2096 |:443 |:80 |:29800 ' || echo "No expected TCP ports"
ss -ulnp 2>/dev/null | grep -E ':36712 |:56100 ' || echo "UDP 36712/AWG: not listening"

echo ""
echo "--- UFW ---"
sudo ufw status 2>/dev/null | head -30 || echo "ufw: n/a"
sudo ufw status 2>/dev/null | grep -E "^${PANEL_PORT}/tcp" | grep -q ALLOW && echo "NOTE: panel port ${PANEL_PORT} is open to the world"

echo ""
echo "--- Hardening: IPsum + Fail2Ban ---"
if sudo nft list set inet ipsum blocklist >/dev/null 2>&1; then
  echo "IPsum: loaded, $(sudo nft list set inet ipsum blocklist | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | wc -l) addresses"
  echo "  counters: $(sudo nft list chain inet ipsum input 2>/dev/null | grep counter | sed 's/^ *//')"
  echo "  whitelist: $(sudo grep -vE '^\s*(#|$)' /etc/ipsum/whitelist.txt 2>/dev/null | tr '\n' ' ')"
  systemctl is-active ipsum-rollback.timer >/dev/null 2>&1 && echo "  !! ipsum-rollback.timer ARMED (will delete the table)"
else
  echo "IPsum: NOT deployed (scripts/deploy-ipsum.sh)"
fi
sudo fail2ban-client status 2>/dev/null | sed 's/^/  /' || echo "fail2ban: n/a"
sudo fail2ban-client status sshd 2>/dev/null | grep -E "Currently|Total" | sed 's/^/  sshd: /'

echo ""
echo "--- Accounts that can log in / sudo (leftovers from installers or earlier agents?) ---"
getent passwd | awk -F: '$7 ~ /(bash|sh|zsh)$/ && $7 !~ /nologin|false/ {print "  user: "$1" (uid "$3") home="$6}'
echo "  sudo group: $(getent group sudo | cut -d: -f4)"
for f in /etc/sudoers.d/*; do [[ -f "$f" ]] && echo "  sudoers.d/$(basename "$f"): $(sudo grep -vE '^\s*(#|$)' "$f" 2>/dev/null | head -2 | tr '\n' ';')"; done
for h in /root /home/*; do
  if sudo test -s "$h/.ssh/authorized_keys" 2>/dev/null; then
    sudo ssh-keygen -lf "$h/.ssh/authorized_keys" 2>/dev/null | awk -v h="$h" '{print "  ssh key ["h"]: "$2" "$3" "$4}'
  fi
done
sudo chage -l root 2>/dev/null | grep -i "account expires" | sed 's/^/  root: /'
for u in $(getent passwd | awk -F: '$7 ~ /(bash|sh)$/ && $1!="root" {print $1}'); do
  echo "  $u: $(sudo chage -l "$u" 2>/dev/null | grep -i 'account expires' | sed 's/^ *//')"
done
echo "  sshd match/overrides: $(grep -hE '^(Match|PermitRootLogin|PasswordAuthentication)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null | tr '\n' ';')"

echo ""
echo "--- Inbounds (sqlite) ---"
SQ "SELECT id,remark,port,protocol,enable,CASE WHEN json_valid(stream_settings) THEN COALESCE(json_extract(stream_settings,'\$.network'),'-')||'/'||COALESCE(json_extract(stream_settings,'\$.security'),'-') ELSE '-/-' END FROM inbounds ORDER BY id;" \
  || echo "sqlite: cannot read x-ui.db"
echo "hosts overrides that DISAGREE with the inbound (wrong sub links):"
SQ "SELECT '  inbound '||h.inbound_id||': hosts.security='||h.security||' vs inbound='||json_extract(i.stream_settings,'\$.security')||'  hosts.sni='||h.sni FROM hosts h JOIN inbounds i ON i.id=h.inbound_id WHERE json_valid(i.stream_settings) AND h.security NOT IN ('same','') AND h.security != json_extract(i.stream_settings,'\$.security');" | grep . || echo "  none"

echo ""
echo "--- Panel settings (sqlite) ---"
SQ "SELECT key,value FROM settings WHERE key IN (
    'webDomain','webPort','webBasePath','webListen','subPath','subJsonPath',
    'subEncrypt','subJsonEnable','subEnableRouting','subCertFile','subClashEnable'
  ) ORDER BY key;" || true

echo ""
echo "--- nginx ---"
if [[ -d /etc/nginx/sites-enabled ]]; then
  for f in /etc/nginx/sites-enabled/*; do
    [[ -e "$f" ]] || continue
    if [[ -L "$f" ]]; then echo "  $(basename "$f"): symlink -> $(readlink "$f")"; else echo "  $(basename "$f"): REGULAR FILE (copy!) — edits in sites-available are ignored; backups here become live server blocks"; fi
  done
  ls /etc/nginx/sites-enabled | grep -E '\.(bak|old|orig)|~$' | sed 's/^/  stray backup in sites-enabled: /'
fi
grep -rn "acme-challenge" /etc/nginx/sites-enabled/ 2>/dev/null | head -2 | sed 's/^/  /' || true
[[ -n "$(grep -rln "acme-challenge" /etc/nginx/sites-enabled/ 2>/dev/null)" ]] || echo "  no acme-challenge location on :80 (webroot renewal impossible)"
sudo nginx -t 2>&1 | tail -2

echo ""
echo "--- Recent log (errors) ---"
sudo tail -40 /var/log/x-ui/3xui.log 2>/dev/null | grep -iE 'error|hysteria|version|fail' | tail -8 || \
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
  echo "links: $(echo "$BODY" | grep -oE '(security=[a-z]+|sni=[^&#]+)' | tr '\n' ' ')"
fi

echo ""
echo "=== Audit done === (next: scripts/loopback-test.py for a real handshake per inbound)"
