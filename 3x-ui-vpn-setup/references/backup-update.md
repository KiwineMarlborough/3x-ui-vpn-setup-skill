# Backup and Panel Updates

## Backup (before any major change)

**Panel UI:** Settings → Backup → download `.db` file

**SSH:**
```bash
sudo cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +%F).db
sudo tar czf /root/backups/le-certs-$(date +%F).tar.gz /root/cert/ 2>/dev/null
```

Store backups off-server (encrypted).

## Update 3X-UI

Use panel update or `x-ui update` per official docs.

**After update — mandatory checks:**

```bash
sudo x-ui status
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
bash scripts/verify-server.sh   # with SUB_ID set
```

**Hysteria regression:** if `version != 2` in log → `scripts/fix-hysteria-stream.py`

## Restore

```bash
sudo x-ui stop
sudo cp /root/backups/x-ui-YYYY-MM-DD.db /etc/x-ui/x-ui.db
sudo x-ui start
```

## What updates usually preserve

- `/etc/x-ui/x-ui.db` — all inbounds, clients, settings
- `/root/cert/` — LE certs

## What may change

- Xray core version — retest Hysteria + Reality
- Panel UI — verify `webBasePath` unchanged