#!/usr/bin/env bash
# Deploy the IPsum blocklist (nftables) safely: whitelist first, auto-rollback armed, SSH peers protected.
#
# Usage (as root; Ubuntu 26.04 sudo-rs ignores `sudo -E`, so pass variables with `sudo env`):
#   sudo env "ADMIN_IPS=203.0.113.7 198.51.100.0/24" bash deploy-ipsum.sh
#   # open a NEW ssh session and confirm you are still in, THEN:
#   sudo env CONFIRM=1 bash deploy-ipsum.sh        # cancels the auto-rollback
#
# Env:
#   ADMIN_IPS      space/comma separated IPs/CIDRs that must never be blocked (your home/office IPs).
#                  Current SSH client addresses are added automatically.
#   MIN_LEVEL=3    IPsum level: address appears on >= N independent blocklists (2: ~32k, 3: ~16k, 4: ~9k)
#   ROLLBACK_MIN=5 minutes until the table is deleted automatically unless CONFIRM=1 (0 = no rollback timer)
#   DRY_RUN=1      print what would be done, change nothing
#
# Result: table `inet ipsum` (priority -10, before UFW), daily refresh via systemd timer,
#         whitelist /etc/ipsum/whitelist.txt, cache /var/lib/ipsum/blocklist.txt.
# Emergency off: nft delete table inet ipsum    (permanent: systemctl disable --now ipsum-block.timer)

set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_LEVEL="${MIN_LEVEL:-3}"
ROLLBACK_MIN="${ROLLBACK_MIN:-5}"
DRY_RUN="${DRY_RUN:-0}"
WL=/etc/ipsum/whitelist.txt

ok()   { echo "[OK]   $*"; }
warn() { echo "[WARN] $*"; }
die()  { echo "[FAIL] $*" >&2; exit 1; }
run()  { if [[ "$DRY_RUN" == "1" ]]; then echo "[dry]  $*"; else eval "$@"; fi; }

[[ $EUID -eq 0 ]] || die "run as root (sudo env VAR=... bash $0)"

if [[ "${CONFIRM:-0}" == "1" ]]; then
  systemctl stop ipsum-rollback.timer 2>/dev/null && ok "auto-rollback cancelled — IPsum stays active" || warn "no rollback timer was pending"
  systemctl reset-failed ipsum-rollback.service 2>/dev/null || true
  exit 0
fi

command -v nft >/dev/null || die "nft not found (apt install nftables)"
command -v curl >/dev/null || die "curl not found"
[[ -f "$SELF_DIR/ipsum-update.sh" ]] || die "ipsum-update.sh must sit next to this script"

# ---- collect addresses that must never be blocked ---------------------------------------------
declare -a keep=()
admin_ips="${ADMIN_IPS:-}"
for ip in ${admin_ips//,/ }; do keep+=("$ip"); done
if [[ -n "${SSH_CONNECTION:-}" ]]; then keep+=("${SSH_CONNECTION%% *}"); fi
while read -r peer; do
  [[ -n "$peer" ]] && keep+=("${peer%:*}")
done < <(ss -Htn state established '( sport = :22 )' 2>/dev/null | awk '{print $4}' | grep -E '^[0-9.]+:[0-9]+$' || true)

mapfile -t keep < <(printf '%s\n' "${keep[@]:-}" | grep -E '^[0-9]{1,3}(\.[0-9]{1,3}){3}(/[0-9]{1,2})?$' | sort -u)
[[ ${#keep[@]} -gt 0 ]] || die "no admin address known. Set ADMIN_IPS=<your public IP> — otherwise you could lock yourself out"
ok "never-block list: ${keep[*]}"

# ---- install ----------------------------------------------------------------------------------
run "install -m 755 '$SELF_DIR/ipsum-update.sh' /usr/local/sbin/ipsum-update.sh"
run "mkdir -p /etc/ipsum /var/lib/ipsum"
if [[ "$DRY_RUN" != "1" ]]; then
  [[ -f "$WL" ]] || printf '# Never blocked by IPsum: one IP/CIDR per line (comments allowed)\n' > "$WL"
  for ip in "${keep[@]}"; do grep -qxF "$ip" "$WL" || grep -qE "^${ip//./\\.}([[:space:]]|\$)" "$WL" || echo "$ip  # added by deploy-ipsum.sh" >> "$WL"; done
else
  echo "[dry]  would ensure whitelist $WL contains: ${keep[*]}"
fi

if [[ "$DRY_RUN" != "1" ]]; then
cat > /etc/systemd/system/ipsum-block.service <<EOF
[Unit]
Description=Update IPsum blocklist in nftables
After=network-online.target ufw.service
Wants=network-online.target

[Service]
Type=oneshot
Environment=MIN_LEVEL=${MIN_LEVEL}
ExecStart=/usr/local/sbin/ipsum-update.sh
EOF
cat > /etc/systemd/system/ipsum-block.timer <<'EOF'
[Unit]
Description=Daily IPsum blocklist refresh

[Timer]
OnBootSec=2min
OnCalendar=*-*-* 04:30:00
RandomizedDelaySec=20min
Persistent=true

[Install]
WantedBy=timers.target
EOF
  systemctl daemon-reload
else
  echo "[dry]  would write ipsum-block.service/.timer (MIN_LEVEL=$MIN_LEVEL) and daemon-reload"
fi

# ---- safety net + first load --------------------------------------------------------------------
if [[ "$ROLLBACK_MIN" != "0" ]]; then
  run "systemd-run --on-active=${ROLLBACK_MIN}m --unit=ipsum-rollback /usr/sbin/nft delete table inet ipsum >/dev/null"
  [[ "$DRY_RUN" == "1" ]] || ok "auto-rollback armed: table is deleted in ${ROLLBACK_MIN} min unless you run CONFIRM=1"
fi

run "MIN_LEVEL=$MIN_LEVEL /usr/local/sbin/ipsum-update.sh"
run "systemctl enable --now ipsum-block.timer >/dev/null 2>&1"

if [[ "$DRY_RUN" != "1" ]]; then
  n=$(nft list set inet ipsum blocklist 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | wc -l)
  ok "blocklist loaded: ${n} addresses (level >= ${MIN_LEVEL})"
  echo
  echo "NEXT: open a NEW ssh session (and test your VPN client). If everything works:"
  echo "      sudo env CONFIRM=1 bash $0"
  echo "If you are locked out, wait ${ROLLBACK_MIN} min — the table removes itself."
fi
