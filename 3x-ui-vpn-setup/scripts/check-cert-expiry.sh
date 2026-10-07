#!/usr/bin/env bash
# Certificate expiry + stale-copy check (read-only).
#
# Usage (as root, certs under /root/cert are not world-readable):
#   sudo bash check-cert-expiry.sh                 # default locations
#   sudo bash check-cert-expiry.sh /path/a.pem ... # explicit files
#
# Env:
#   WARN_DAYS=30   print WARN below this many days
#   FAIL_DAYS=7    exit 1 below this many days (or already expired)
#   CERT_GLOBS     extra space-separated globs, e.g. "/opt/certs/*/fullchain.pem"
#
# Why this exists: acme.sh/certbot can fail silently (port 80 busy, DNS record removed),
# and nothing else notices until clients start failing TLS verification.
# Also detects a stale nginx copy (same CN, different fingerprint as the source cert).

set -uo pipefail

WARN_DAYS="${WARN_DAYS:-30}"
FAIL_DAYS="${FAIL_DAYS:-7}"

files=("$@")
if [[ ${#files[@]} -eq 0 ]]; then
  shopt -s nullglob
  # shellcheck disable=SC2206
  files=(/root/cert/*/fullchain.pem /etc/nginx/ssl/*/fullchain.pem /etc/letsencrypt/live/*/fullchain.pem ${CERT_GLOBS:-})
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "[WARN] no certificate files found"
  exit 0
fi

now=$(date +%s)
rc=0
declare -A fp_by_cn

for f in "${files[@]}"; do
  [[ -r "$f" ]] || { echo "[WARN] cannot read $f (run with sudo?)"; continue; }
  subj=$(openssl x509 -in "$f" -noout -subject 2>/dev/null | sed 's/^subject= *//') || continue
  end=$(openssl x509 -in "$f" -noout -enddate 2>/dev/null | cut -d= -f2) || continue
  issuer=$(openssl x509 -in "$f" -noout -issuer 2>/dev/null | sed 's/^issuer= *//')
  fp=$(openssl x509 -in "$f" -noout -fingerprint -sha256 2>/dev/null | cut -d= -f2)
  end_ts=$(date -d "$end" +%s 2>/dev/null) || continue
  days=$(( (end_ts - now) / 86400 ))
  kind="CA-signed"
  [[ "$subj" == "$issuer" ]] && kind="self-signed"

  if (( days < 0 )); then
    echo "[FAIL] $f  EXPIRED $(( -days )) days ago ($end)  [$subj, $kind]"; rc=1
  elif (( days < FAIL_DAYS )); then
    echo "[FAIL] $f  ${days}d left ($end)  [$subj, $kind]"; rc=1
  elif (( days < WARN_DAYS )); then
    echo "[WARN] $f  ${days}d left ($end)  [$subj, $kind]"
  else
    echo "[OK]   $f  ${days}d left ($end)  [$subj, $kind]"
  fi

  cn=$(echo "$subj" | sed -n 's/.*CN *= *\([^,\/]*\).*/\1/p')
  if [[ -n "$cn" && "$kind" == "CA-signed" ]]; then
    if [[ -n "${fp_by_cn[$cn]:-}" && "${fp_by_cn[$cn]}" != "$fp" ]]; then
      echo "[WARN] stale copy: two different certificates for CN=$cn (source vs nginx copy?) — see references/cert-renewal-nginx.md"
    fi
    fp_by_cn[$cn]="$fp"
  fi
done

exit $rc
