#!/usr/bin/env bash
# Install LE renewal hook to sync certs to nginx ssl dir.
#
# Usage (on server, as root):
#   export CDN_DOMAIN=cdn.vpn.example.com
#   export CERT_SRC=/root/cert/cdn.vpn.example.com
#   sudo -E bash deploy-cert-hook.sh

set -euo pipefail

CDN_DOMAIN="${CDN_DOMAIN:-cdn.vpn.example.com}"
CERT_SRC="${CERT_SRC:-/root/cert/${CDN_DOMAIN}}"
NGINX_SSL="/etc/nginx/ssl/cdn"
HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
HOOK="${HOOK_DIR}/sync-nginx-cdn.sh"

mkdir -p "$HOOK_DIR" "$NGINX_SSL"

cat > "$HOOK" <<EOF
#!/bin/bash
set -euo pipefail
SRC="${CERT_SRC}"
DST="${NGINX_SSL}"
[[ -f "\${SRC}/fullchain.pem" ]] || exit 0
cp "\${SRC}/fullchain.pem" "\${DST}/fullchain.pem"
cp "\${SRC}/privkey.pem" "\${DST}/privkey.pem"
chmod 644 "\${DST}/fullchain.pem"
chmod 600 "\${DST}/privkey.pem"
nginx -t && systemctl reload nginx
EOF

chmod +x "$HOOK"
echo "Installed renewal hook: $HOOK"

if command -v certbot >/dev/null 2>&1; then
  certbot renew --dry-run || echo "WARN: certbot dry-run failed (3X-UI may manage certs)"
else
  echo "certbot not installed — hook ready for when LE renews via panel"
fi

# Initial sync
if [[ -f "${CERT_SRC}/fullchain.pem" ]]; then
  cp "${CERT_SRC}/fullchain.pem" "${NGINX_SSL}/fullchain.pem"
  cp "${CERT_SRC}/privkey.pem" "${NGINX_SSL}/privkey.pem"
  nginx -t && systemctl reload nginx
  echo "Initial cert sync OK"
fi