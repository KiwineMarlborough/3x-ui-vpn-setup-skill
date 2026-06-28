#!/usr/bin/env bash
# Deploy nginx CDN fallback page + vhost.
#
# Usage (on server, as root):
#   export CDN_DOMAIN=cdn.vpn.example.com
#   export CERT_SRC=/root/cert/cdn.vpn.example.com   # 3X-UI LE path
#   sudo -E bash deploy-nginx-fallback.sh
#
# Optional: SKILL_ROOT=/path/to/3x-ui-vpn-setup (defaults to script parent dir)

set -euo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
CERT_SRC="${CERT_SRC:-/root/cert/${CDN_DOMAIN}}"
NGINX_SSL="/etc/nginx/ssl/cdn"
WEB_ROOT="/var/www/cdn-fallback"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="${SKILL_ROOT:-$(dirname "$SCRIPT_DIR")}"
TEMPLATE_CONF="${SKILL_ROOT}/templates/nginx-cdn.conf"
INDEX_SRC="${SKILL_ROOT}/assets/cdn-fallback/index.html"

[[ -f "$TEMPLATE_CONF" ]] || { echo "Missing $TEMPLATE_CONF"; exit 1; }
[[ -f "$INDEX_SRC" ]] || { echo "Missing $INDEX_SRC"; exit 1; }
[[ -f "${CERT_SRC}/fullchain.pem" && -f "${CERT_SRC}/privkey.pem" ]] || {
  echo "Certs not found in CERT_SRC=${CERT_SRC}"
  exit 1
}

command -v nginx >/dev/null || { echo "Install nginx first: apt install -y nginx"; exit 1; }

mkdir -p "$NGINX_SSL" "$WEB_ROOT"
cp "${CERT_SRC}/fullchain.pem" "${NGINX_SSL}/fullchain.pem"
cp "${CERT_SRC}/privkey.pem" "${NGINX_SSL}/privkey.pem"
chmod 644 "${NGINX_SSL}/fullchain.pem"
chmod 600 "${NGINX_SSL}/privkey.pem"

cp "$INDEX_SRC" "${WEB_ROOT}/index.html"

sed "s/__CDN_DOMAIN__/${CDN_DOMAIN}/g" "$TEMPLATE_CONF" \
  > /etc/nginx/sites-available/cdn-fallback

ln -sf /etc/nginx/sites-available/cdn-fallback /etc/nginx/sites-enabled/cdn-fallback
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

nginx -t
systemctl enable nginx
systemctl reload nginx

CODE=$(curl -sk -o /dev/null -w '%{http_code}' "https://${CDN_DOMAIN}/" || echo "000")
echo "HTTPS check https://${CDN_DOMAIN}/ → HTTP ${CODE}"
[[ "$CODE" == "200" ]] && echo "OK" || echo "WARN: expected 200"