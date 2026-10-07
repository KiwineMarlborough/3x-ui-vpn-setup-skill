#!/usr/bin/env bash
# Make the CDN certificate renew itself: acme.sh in WEBROOT mode (nginx keeps port 80),
# with a deploy hook that syncs the nginx copy and restarts x-ui.
#
# Fixes the classic failure: acme.sh issued by 3X-UI uses `standalone` mode (needs a free port 80),
# but this skill puts nginx on 80/443 -> renewal fails silently -> cert expires after ~90 days.
#
# Usage (as root):
#   export CDN_DOMAIN=cdn.vpn.example.com
#   sudo env "CDN_DOMAIN=$CDN_DOMAIN" bash deploy-acme-renewal.sh                 # preflight only (changes nothing)
#   sudo env "CDN_DOMAIN=$CDN_DOMAIN" STAGING_TEST=1 bash deploy-acme-renewal.sh  # full ACME cycle on the Let's Encrypt STAGING CA,
#                                                       # in a temp dir; the real certificate is untouched
#   sudo env "CDN_DOMAIN=$CDN_DOMAIN" APPLY=1 bash deploy-acme-renewal.sh         # issue/install for real + hook + cron check
#
# NOTE: Ubuntu 26.04 ships sudo-rs, which ignores `sudo -E` — always pass variables with `sudo env VAR=... bash ...`
#       (or run from a root shell).
#
# Env (defaults):
#   WEBROOT=/var/www/cdn-fallback        nginx root that serves /.well-known/acme-challenge/ on port 80
#   CERT_DIR=/root/cert/$CDN_DOMAIN      where 3X-UI reads the cert (subCertFile / inbound certs)
#   NGINX_SSL=/etc/nginx/ssl/cdn         nginx copy (set NGINX_SSL= to skip nginx sync)
#   ACME_HOME=/root/.acme.sh
#   RESTART_XUI=1                        restart x-ui in the deploy hook (it only reads certs at start)
#   FORCE=1                              reissue even if the current cert is still valid
#   ACME_EMAIL=                          optional account e-mail for a new acme.sh install
#
# Prerequisite: templates/nginx-cdn.conf (port 80 block serves the challenge path before redirecting).

set -euo pipefail

: "${CDN_DOMAIN:?set CDN_DOMAIN}"
WEBROOT="${WEBROOT:-/var/www/cdn-fallback}"
CERT_DIR="${CERT_DIR:-/root/cert/${CDN_DOMAIN}}"
NGINX_SSL="${NGINX_SSL-/etc/nginx/ssl/cdn}"
ACME_HOME="${ACME_HOME:-/root/.acme.sh}"
ACME="${ACME_HOME}/acme.sh"
RESTART_XUI="${RESTART_XUI:-1}"
HOOK=/usr/local/sbin/cdn-cert-deploy.sh

ok()   { echo "[OK]   $*"; }
warn() { echo "[WARN] $*"; }
die()  { echo "[FAIL] $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "run as root (use: sudo env CDN_DOMAIN=... bash $0 — sudo -E is ignored on Ubuntu 26.04)"

# ---- preflight --------------------------------------------------------------------------------
[[ -x "$ACME" ]] || die "acme.sh not found at $ACME (3X-UI menu 'SSL Certificate Management' installs it; or set ACME_HOME)"
ok "acme.sh: $("$ACME" --version 2>/dev/null | tail -1)"

systemctl is-active --quiet nginx || die "nginx is not running (it must own :80/:443)"
ok "nginx active"

mkdir -p "$WEBROOT/.well-known/acme-challenge"
probe="probe-$$"
echo "ok-$$" > "$WEBROOT/.well-known/acme-challenge/$probe"
trap 'rm -f "$WEBROOT/.well-known/acme-challenge/$probe"' EXIT
got=$(curl -s -m 10 --resolve "${CDN_DOMAIN}:80:127.0.0.1" "http://${CDN_DOMAIN}/.well-known/acme-challenge/$probe" || true)
[[ "$got" == "ok-$$" ]] || die "http://${CDN_DOMAIN}/.well-known/acme-challenge/ is not served by nginx on :80 (got: '${got:0:60}'). Use templates/nginx-cdn.conf — a server-level 'return 301' hides the location block"
ok "nginx serves the ACME challenge path on :80"

ext=$(curl -s -m 10 -o /dev/null -w '%{http_code}' "http://${CDN_DOMAIN}/.well-known/acme-challenge/$probe" || echo 000)
if [[ "$ext" == "200" ]]; then ok "challenge path reachable through public DNS (HTTP 200)"
else warn "public DNS check returned HTTP $ext — Let's Encrypt validates through public DNS; check the A record / proxy mode (references/dns-setup.md)"; fi

# ---- how will the CURRENT certificate renew? -----------------------------------------------------
NEED_SWITCH=0
conf=""
for c in "$ACME_HOME/${CDN_DOMAIN}_ecc/${CDN_DOMAIN}.conf" "$ACME_HOME/${CDN_DOMAIN}/${CDN_DOMAIN}.conf"; do
  [[ -f "$c" ]] && { conf="$c"; break; }
done
if [[ -n "$conf" ]]; then
  cur_web=$(sed -n "s/^Le_Webroot='\(.*\)'/\1/p" "$conf")
  cur_alt=$(sed -n "s/^Le_Alt='\(.*\)'/\1/p" "$conf")
  if [[ "$cur_web" == "$WEBROOT" ]]; then
    ok "renewal mode: webroot ($cur_web)"
  else
    NEED_SWITCH=1
    warn "renewal mode is '${cur_web:-unknown}' (standalone = 'no' needs a FREE port 80 and fails while nginx owns it) — APPLY switches it to webroot"
  fi
  if [[ -n "$cur_alt" && "$cur_alt" != "no" ]]; then
    NEED_SWITCH=1
    warn "certificate also lists other names ($cur_alt) — a name removed from DNS blocks renewal; APPLY reissues for $CDN_DOMAIN only"
  fi
else
  warn "no acme.sh state for $CDN_DOMAIN under $ACME_HOME (certificate not issued by this acme.sh yet?)"
fi

# ---- staging dry run ---------------------------------------------------------------------------
if [[ "${STAGING_TEST:-0}" == "1" ]]; then
  tmp=$(mktemp -d)
  echo "--- STAGING issuance (temp cert-home: $tmp; real certificate untouched) ---"
  if "$ACME" --issue --staging --server letsencrypt_test --cert-home "$tmp" -d "$CDN_DOMAIN" \
       -w "$WEBROOT" --keylength ec-256 --force 2>&1 | tee "$tmp/log.txt" | grep -E "Verification finished|Cert success|error|Error|invalid"; then :; fi
  if grep -q "Cert success" "$tmp/log.txt"; then ok "staging issuance succeeded — renewal path works"; rc=0
  else warn "staging issuance FAILED — see output above"; rc=1; fi
  rm -rf "$tmp"
  exit $rc
fi

if [[ "${APPLY:-0}" != "1" ]]; then
  echo "Preflight passed. Re-run with STAGING_TEST=1 (safe full test) or APPLY=1 (issue + install)."
  exit 0
fi

# ---- apply -------------------------------------------------------------------------------------
stamp=$(date +%Y%m%d%H%M%S)
if [[ -d "$CERT_DIR" ]]; then
  mkdir -p /root/backups
  tar czf "/root/backups/certs-${stamp}.tgz" "$CERT_DIR" ${NGINX_SSL:+"$NGINX_SSL"} 2>/dev/null || true
  ok "backup: /root/backups/certs-${stamp}.tgz"
fi
mkdir -p "$CERT_DIR"

cat > "$HOOK" <<EOF
#!/bin/bash
# Installed by deploy-acme-renewal.sh — runs after every successful issue/renew.
set -euo pipefail
SRC="${CERT_DIR}"
EOF
if [[ -n "${NGINX_SSL}" ]]; then
cat >> "$HOOK" <<EOF
DST="${NGINX_SSL}"
mkdir -p "\$DST"
cp "\$SRC/fullchain.pem" "\$DST/fullchain.pem"
cp "\$SRC/privkey.pem"   "\$DST/privkey.pem"
chmod 644 "\$DST/fullchain.pem"; chmod 600 "\$DST/privkey.pem"
nginx -t && systemctl reload nginx
EOF
fi
if [[ "$RESTART_XUI" == "1" ]]; then
  echo 'systemctl restart x-ui' >> "$HOOK"
fi
chmod 700 "$HOOK"
ok "deploy hook: $HOOK"

need_issue=1
if [[ -s "$CERT_DIR/fullchain.pem" && "${FORCE:-0}" != "1" && "$NEED_SWITCH" != "1" ]]; then
  if openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -checkend $((30*86400)) >/dev/null 2>&1; then
    need_issue=0; ok "current certificate valid for > 30 days — not reissuing (FORCE=1 to override)"
  fi
fi

if [[ $need_issue -eq 1 ]]; then
  "$ACME" --issue -d "$CDN_DOMAIN" -w "$WEBROOT" --keylength ec-256 --force --server letsencrypt
fi
"$ACME" --install-cert -d "$CDN_DOMAIN" --ecc \
  --fullchain-file "$CERT_DIR/fullchain.pem" --key-file "$CERT_DIR/privkey.pem" \
  --reloadcmd "$HOOK"
ok "certificate installed (hook ran)"

crontab -l 2>/dev/null | grep -q "acme.sh.*--cron" || { "$ACME" --install-cronjob && ok "acme.sh cron installed"; }
crontab -l 2>/dev/null | grep -q "acme.sh.*--cron" && ok "acme.sh daily cron present"

if [[ -x "$(dirname "$0")/check-cert-expiry.sh" ]]; then bash "$(dirname "$0")/check-cert-expiry.sh" "$CERT_DIR/fullchain.pem" || true; fi
echo "Done. Add scripts/check-cert-expiry.sh to monitoring (references/monitoring.md)."
