# Migration (old VPS → new VPS)

Move 3X-UI setup without rebuilding from scratch — or partial migration.

## What transfers cleanly

| Asset | Path | Notes |
|-------|------|-------|
| Database | `/etc/x-ui/x-ui.db` | All inbounds, clients, settings |
| LE certs | `/root/cert/<domain>/` | Re-issue on the new server with `deploy-acme-renewal.sh` (the acme.sh state/renewal mode is NOT in this folder) |
| nginx site | `/etc/nginx/sites-available/cdn-fallback` | Redeploy from skill templates |
| SSH keys | `~/.ssh/authorized_keys` | Add new key before cutover |

## Pre-migration checklist

- [ ] Backup `x-ui.db` + certs off-server
- [ ] Note: `webBasePath`, sub paths, all domains
- [ ] Lower DNS TTL to 300s
- [ ] Document Reality publicKey / shortId (in panel after restore)

## Full DB migration

**Old server:**

```bash
sudo x-ui stop
sudo tar czf /tmp/x-ui-migrate.tar.gz /etc/x-ui/x-ui.db /root/cert/
# scp to new server
```

**New server:**

1. Fresh Ubuntu + install 3X-UI (`execution-order.md` phases 1–2 only)
2. Stop x-ui, restore db and certs
3. Update DNS A records → new IP
4. Fix panel cert paths if domains unchanged
5. Install nginx + `deploy-acme-renewal.sh` (STAGING_TEST, then APPLY) — a restored certificate whose acme.sh state is missing will never renew
6. Re-run `deploy-ipsum.sh` / `setup-fail2ban.sh` with your `ADMIN_IPS` (not part of the DB)
7. `sudo x-ui start`
8. `xray -test` + `loopback-test.py` + `verify-server.sh`

## Partial migration (rebuild inbounds)

If DB corrupt or version mismatch:

1. Export client list from old panel screenshot / backup sqlite
2. New server full skill setup
3. New Reality keys → users refresh subscription
4. New `sub_id` and custom paths → update Happ

## DNS cutover

```
1. New VPS ready, verify with /etc/hosts or --resolve tests
2. Change the cdn A record (there is no public panel record)
3. Wait TTL
4. Re-issue the certificate on the new server (HTTP-01 through nginx :80: `deploy-acme-renewal.sh`)
5. Check `check-cert-expiry.sh` + `verify-server.sh`; update the UFW/IPsum whitelist for your admin IPs
```

## What breaks if forgotten

| Missed step | Symptom |
|-------------|---------|
| Hysteria stream not fixed | JSON 500 after restore |
| Old sub paths in Happ | 404 until refresh URL |
| nginx cert not synced / renewal still standalone | 443 TLS error on cdn now, or expiry in ~90 days |
| UFW not opened | Timeouts |
| webDomain old cert | Panel TLS error |

## Rollback

Point DNS back to old IP; old server still running with original db.

## Related

- `references/backup-update.md`
- `references/dns-setup.md`
- `references/repair-only.md`