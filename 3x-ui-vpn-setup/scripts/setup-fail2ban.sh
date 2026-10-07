#!/usr/bin/env bash
# Fail2Ban for SSH (sshd jail) with admin addresses exempt from bans.
#
# Usage (as root):
#   sudo env "ADMIN_IPS=203.0.113.7" bash setup-fail2ban.sh
#   sudo env "ADMIN_IPS=203.0.113.7" DRY_RUN=1 bash setup-fail2ban.sh
#
# Env:
#   ADMIN_IPS   space/comma separated IPs/CIDRs added to `ignoreip` (strongly recommended: with password login
#               as root a few typos otherwise ban YOUR address for BANTIME)
#   MAXRETRY=5  FINDTIME=10m  BANTIME=1h
#
# Notes:
# - 3X-UI's installer/updater also creates the `3x-ipl` jail (per-client IP limit, bans only when a
#   client has limitIp > 0). It is independent of this script and is left untouched.
# - IPsum (deploy-ipsum.sh) drops known-bad IPs before they reach sshd; Fail2Ban covers everyone else.

set -euo pipefail

MAXRETRY="${MAXRETRY:-5}"
FINDTIME="${FINDTIME:-10m}"
BANTIME="${BANTIME:-1h}"
DRY_RUN="${DRY_RUN:-0}"
admin_ips="${ADMIN_IPS:-}"
JAIL=/etc/fail2ban/jail.d/10-sshd-hardening.local

ok()  { echo "[OK]   $*"; }
die() { echo "[FAIL] $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "run as root (sudo env VAR=... bash $0)"

ignore="127.0.0.1/8 ::1"
for ip in ${admin_ips//,/ }; do ignore="$ignore $ip"; done
[[ -n "${SSH_CONNECTION:-}" ]] && ignore="$ignore ${SSH_CONNECTION%% *}"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry] would apt-get install fail2ban (if missing)"
  echo "[dry] would write $JAIL:"
  printf '      [sshd]\n      enabled = true\n      backend = systemd\n      maxretry = %s\n      findtime = %s\n      bantime = %s\n      ignoreip = %s\n' "$MAXRETRY" "$FINDTIME" "$BANTIME" "$ignore"
  exit 0
fi

if ! command -v fail2ban-client >/dev/null; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y fail2ban >/dev/null
  ok "fail2ban installed"
fi

cat > "$JAIL" <<EOF
# Managed by deploy skill (setup-fail2ban.sh)
[sshd]
enabled  = true
backend  = systemd
maxretry = ${MAXRETRY}
findtime = ${FINDTIME}
bantime  = ${BANTIME}
ignoreip = ${ignore}
EOF

fail2ban-client -t >/dev/null && ok "fail2ban config test passed"
systemctl enable --now fail2ban >/dev/null 2>&1
systemctl restart fail2ban
sleep 2
fail2ban-client status sshd | sed 's/^/        /'
fail2ban-client get sshd ignoreip | sed 's/^/        ignoreip: /'
ok "sshd jail active (maxretry=${MAXRETRY}, findtime=${FINDTIME}, bantime=${BANTIME})"
