#!/usr/bin/env bash
# Install the hourly country-balancer sync (sync_country_balancers.py) as a systemd timer on the 3X-UI server.
# Run as root from the folder that contains xui.py and sync_country_balancers.py:
#   sudo env XUI_TOKEN=... XUI_BASE=/path XUI_HOST=domain SUB="sub1 provider" \
#        MAP="US=BridgeUS-balancer,IN=BridgeIN-balancer,RU=BridgeRU-balancer" [TOLERATE="IN=NL"] bash deploy_country_sync.sh
# Rollback: systemctl disable --now country-balancers.timer && rm -rf /opt/country-balancers /etc/default/country-balancers \
#           /etc/systemd/system/country-balancers.*
set -euo pipefail
: "${XUI_TOKEN:?}" "${XUI_BASE:?}" "${XUI_HOST:?}" "${SUB:?}" "${MAP:?}"
D=/opt/country-balancers
install -d -m 755 "$D"
install -m 644 xui.py sync_country_balancers.py "$D/"
umask 077
cat > /etc/default/country-balancers <<EOF
XUI_TOKEN=${XUI_TOKEN}
XUI_BASE=${XUI_BASE}
XUI_HOST=${XUI_HOST}
EOF
chmod 600 /etc/default/country-balancers
cat > /etc/systemd/system/country-balancers.service <<EOF
[Unit]
Description=Sync 3X-UI country balancers with the flags of the outbound subscription
After=x-ui.service

[Service]
Type=oneshot
EnvironmentFile=/etc/default/country-balancers
WorkingDirectory=${D}
ExecStart=/usr/bin/python3 ${D}/sync_country_balancers.py --sub "${SUB}" --map "${MAP}"${TOLERATE:+ --tolerate "${TOLERATE}"}
EOF
cat > /etc/systemd/system/country-balancers.timer <<EOF
[Unit]
Description=Hourly country-balancer sync

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now country-balancers.timer
systemctl list-timers country-balancers.timer --no-pager | head -3
