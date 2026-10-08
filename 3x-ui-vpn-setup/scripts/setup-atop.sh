#!/usr/bin/env bash
# Install atop and record system/process history, so a CPU alert can be explained AFTER it happened.
#
# A panel/Telegram alert ("CPU 87% > 80%") names no culprit and short spikes are gone by the time
# you look; top/vnstat only show "now" / traffic. atop writes per-process CPU, memory, disk and network
# every LOGINTERVAL seconds to /var/log/atop and can replay any minute.
#
# Usage (as root):
#   sudo bash setup-atop.sh                       # install + 60 s interval + keep 28 days
#   sudo env INTERVAL=30 GENERATIONS=14 bash setup-atop.sh
#   sudo env DRY_RUN=1 bash setup-atop.sh         # print the plan, change nothing
#
# Env: INTERVAL=60 (seconds between samples), GENERATIONS=28 (days of daily logs kept), DRY_RUN=0
# Idempotent: re-running with the same values only re-checks. Original config is saved once as
# /etc/default/atop.skill-orig. Cost: a few KB per minute of disk, negligible CPU, no open ports.

set -euo pipefail

INTERVAL="${INTERVAL:-60}"
GENERATIONS="${GENERATIONS:-28}"
DRY_RUN="${DRY_RUN:-0}"
CONF=/etc/default/atop

ok()  { echo "[OK]   $*"; }
die() { echo "[FAIL] $*" >&2; exit 1; }
run() { if [[ "$DRY_RUN" == "1" ]]; then echo "[dry]  $*"; else eval "$@"; fi; }

[[ $EUID -eq 0 ]] || die "run as root (sudo env VAR=... bash $0)"
[[ "$INTERVAL" =~ ^[0-9]+$ && "$GENERATIONS" =~ ^[0-9]+$ ]] || die "INTERVAL and GENERATIONS must be integers"
(( INTERVAL >= 10 )) || die "INTERVAL below 10 s is pointless and grows the logs"

if ! command -v atop >/dev/null 2>&1; then
  run "DEBIAN_FRONTEND=noninteractive apt-get install -y atop >/dev/null"
  [[ "$DRY_RUN" == "1" ]] || ok "atop installed: $(atop -V 2>&1 | head -1)"
else
  ok "atop already installed: $(atop -V 2>&1 | head -1)"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry]  would set LOGINTERVAL=$INTERVAL LOGGENERATIONS=$GENERATIONS in $CONF, enable+restart atop and atopacct"
  exit 0
fi

[[ -f "$CONF.skill-orig" ]] || cp "$CONF" "$CONF.skill-orig"
setkey() { # key value
  if grep -qE "^$1=" "$CONF"; then sed -i "s/^$1=.*/$1=$2/" "$CONF"; else echo "$1=$2" >> "$CONF"; fi
}
cur_i=$(sed -n 's/^LOGINTERVAL=//p' "$CONF"); cur_g=$(sed -n 's/^LOGGENERATIONS=//p' "$CONF")
setkey LOGINTERVAL "$INTERVAL"
setkey LOGGENERATIONS "$GENERATIONS"

systemctl enable atop atopacct >/dev/null 2>&1 || true
if [[ "$cur_i" != "$INTERVAL" || "$cur_g" != "$GENERATIONS" ]] || ! systemctl is-active --quiet atop; then
  systemctl restart atop
fi
systemctl is-active --quiet atopacct || systemctl start atopacct 2>/dev/null || true
sleep 3

systemctl is-active --quiet atop || die "atop service is not active (journalctl -u atop)"
LOG="/var/log/atop/atop_$(date +%Y%m%d)"
[[ -s "$LOG" ]] || die "no log file $LOG yet (wait a minute and re-run)"
ok "atop active, logging every ${INTERVAL}s, keeping ${GENERATIONS} days -> $LOG ($(du -sh /var/log/atop | cut -f1))"

cat <<EOF

Use (log times are UTC):
  sudo atopsar -c -r $LOG -b HH:MM -e HH:MM        # CPU per sample for a time range
  sudo atop -r $LOG -b HH:MM                       # replay: t/T next/previous sample, b jump to time,
                                                   #         C sort by CPU, m memory, d disk, n network
  du -sh /var/log/atop                             # check real disk use after a few days
EOF
