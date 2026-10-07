# Monitoring and Automated Backup

Production hygiene for a personal VPN. The lesson that created this page: **nothing alerted when the certificate
silently stopped renewing**, and the server looked "blocked" for 9 days. Monitor expiry and real handshakes, not just ports.

## What to watch (priority order)

| Check | Tool | Why |
|-------|------|-----|
| Certificate days left (files + served) | `scripts/check-cert-expiry.sh`, `verify-server.sh` | silent expiry (`cert-renewal-nginx.md`) |
| Real handshake per inbound | `scripts/loopback-test.py` | ports can listen while a profile is dead |
| Subscription HTTP 200 + profile count | `verify-server.sh` | |
| IPsum table loaded / rollback timer not armed | `verify-server.sh` | |
| fail2ban + sshd jail | `verify-server.sh` | |
| DB backup freshness | cron below | |

## Cron: daily health + expiry (logs to syslog; add mail/Telegram if you want pushes)

`/usr/local/bin/vpn-healthcheck.sh`:

```bash
#!/bin/bash
CDN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SKILL="${SKILL_DIR:-/opt/3x-ui-vpn-setup/scripts}"
SUB_PATH="${SUB_PATH:-/sub/}"; SUB_ID="${SUB_ID:-}"
# 1) certificates: exit 1 below 7 days / expired
bash "$SKILL/check-cert-expiry.sh" >/tmp/cert-check.txt 2>&1 || logger -t vpn-health "CERT PROBLEM: $(grep -E 'FAIL|WARN' /tmp/cert-check.txt | head -3 | tr '\n' ' ')"
grep -q WARN /tmp/cert-check.txt && logger -t vpn-health "cert warning: $(grep WARN /tmp/cert-check.txt | head -2 | tr '\n' ' ')"
# 2) subscription
if [[ -n "$SUB_ID" ]]; then
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 "https://${CDN}:2096${SUB_PATH}${SUB_ID}")
  [[ "$CODE" == "200" ]] || logger -t vpn-health "sub check failed HTTP $CODE"
fi
# 3) real handshakes
python3 "$SKILL/loopback-test.py" >/tmp/loopback.txt 2>&1 || logger -t vpn-health "HANDSHAKE FAIL: $(grep FAIL /tmp/loopback.txt | head -3 | tr '\n' ' ')"
```

```
17 6 * * * CDN_DOMAIN=cdn.vpn.example.com SUB_PATH=/xK9mP2qR/ SUB_ID=<uuid> /usr/local/bin/vpn-healthcheck.sh
```
Read results: `journalctl -t vpn-health --since -2d`. Cron runs as root (the scripts read `/root/cert` and the DB).

## Daily backup

```bash
sudo mkdir -p /root/backups
sudo crontab -e
```
```
0 4 * * * cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +\%F).db && find /root/backups -name 'x-ui-*.db' -mtime +14 -delete
0 4 * * 0 tar czf /root/backups/certs-$(date +\%F).tgz /root/cert 2>/dev/null
```
Copy weekly backups off the server (encrypted). Backup files contain private keys — protect them like the keys.

## Uptime Kuma (optional)

HTTPS `https://cdn.<domain>/` → 200 (and *certificate expiry* monitor ≥ 14 days) · TCP 8443/2096 · JSON sub URL → 200. Alert via Telegram/e-mail.

## Log watch

```bash
sudo tail -f /var/log/x-ui/3xui.log | grep -iE 'error|hysteria|version'
sudo journalctl -u x-ui -f | grep -iE 'error|fail|migrat'
sudo journalctl -t ipsum --since -2d          # blocklist refresh log
sudo fail2ban-client status sshd
```

## Monthly

Panel release check → `backup-update.md` → `verify-server.sh`; confirm the renewal date: `acme.sh --list` (`Renew` column).

## Incident response

| Alert | Action |
|-------|--------|
| CERT PROBLEM / FAIL days left | `deploy-acme-renewal.sh` (STAGING_TEST → APPLY), `cert-renewal-nginx.md` |
| HANDSHAKE FAIL on one inbound | hint in the output; `repair-only.md` |
| sub != 200 | `audit-server.sh` → `repair-only.md` |
| x-ui down | `systemctl status x-ui`, `journalctl -u x-ui -n 50`, restart |
| user locked out from one network | IPsum false positive (`blocklist-ipsum-fail2ban.md`) |
| disk full | prune `/root/backups`, logs |

## Related

`scripts/audit-server.sh` · `scripts/verify-server.sh` · `references/backup-update.md` · `references/testing-methods.md`
