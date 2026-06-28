# Migration (old VPS → new VPS)

Move 3X-UI setup without rebuilding from scratch — or partial migration.

## What transfers cleanly

| Asset | Path | Notes |
|-------|------|-------|
| Database | `/etc/x-ui/x-ui.db` | All inbounds, clients, settings |
| LE certs | `/root/cert/<domain>/` | Re-issue if domain stays, new IP |
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
5. `sudo x-ui start`
6. `xray -test` + `verify-server.sh`

## Partial migration (rebuild inbounds)

If DB corrupt or version mismatch:

1. Export client list from old panel screenshot / backup sqlite
2. New server full skill setup
3. New Reality keys → users refresh subscription
4. New `sub_id` and custom paths → update Happ

## DNS cutover

```
1. New VPS ready, verify with /etc/hosts or --resolve tests
2. Change panel + cdn A records
3. Wait TTL
4. LE renew or re-request if HTTP-01 failed during overlap
5. deploy-cert-hook.sh on new server
```

## What breaks if forgotten

| Missed step | Symptom |
|-------------|---------|
| Hysteria stream not fixed | JSON 500 after restore |
| Old sub paths in Happ | 404 until refresh URL |
| nginx cert not synced | 443 TLS error on cdn |
| UFW not opened | Timeouts |
| webDomain old cert | Panel TLS error |

## Rollback

Point DNS back to old IP; old server still running with original db.

## Related

- `references/backup-update.md`
- `references/dns-setup.md`
- `references/repair-only.md`