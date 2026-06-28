# Monitoring and Automated Backup

Optional production hygiene for personal VPN servers.

## Daily backup cron

```bash
sudo mkdir -p /root/backups
sudo crontab -e
```

```
0 4 * * * cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +\%F).db && find /root/backups -name 'x-ui-*.db' -mtime +14 -delete
0 4 * * 0 tar czf /root/backups/certs-$(date +\%F).tar.gz /root/cert/ 2>/dev/null
```

Copy weekly backups off-server (encrypted USB / cloud).

## Subscription healthcheck

`/usr/local/bin/vpn-healthcheck.sh`:

```bash
#!/bin/bash
CDN="${CDN_DOMAIN:-cdn.vpn.example.com}"
SUB_PATH="${SUB_PATH:-/sub/}"
SUB_ID="${SUB_ID:-}"
[[ -z "$SUB_ID" ]] && exit 0
URL="https://${CDN}:2096${SUB_PATH}${SUB_ID}"
CODE=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 "$URL")
[[ "$CODE" == "200" ]] || logger -t vpn-health "sub check failed HTTP $CODE"
```

Cron every 5 minutes:

```
*/5 * * * * CDN_DOMAIN=cdn.vpn.example.com SUB_PATH=/xK9mP2qR/ SUB_ID=<uuid> /usr/local/bin/vpn-healthcheck.sh
```

## Uptime Kuma (optional)

Monitor:

- HTTPS `https://cdn.<domain>/` → 200
- TCP port 8443, 2096 on VPS IP
- JSON sub URL → 200

Alert via Telegram/email.

## Log watch

```bash
sudo tail -f /var/log/x-ui/3xui.log | grep -iE 'error|hysteria|version'
```

## Panel update reminder

Monthly: check 3X-UI release → `backup-update.md` → `verify-server.sh`.

## Incident response

| Alert | Action |
|-------|--------|
| sub != 200 | `audit-server.sh` → `repair-only.md` |
| x-ui down | `systemctl restart x-ui` |
| disk full | prune `/root/backups`, logs |

## Related

- `scripts/audit-server.sh`
- `scripts/verify-server.sh`
- `references/backup-update.md`