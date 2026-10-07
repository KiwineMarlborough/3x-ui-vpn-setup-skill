# Backup and Panel / System Updates

## Backup (before any major change)

**Panel UI:** Settings → Backup → download `.db`. **SSH (also keep the binaries — they are your rollback):**

```bash
S=$(date +%F-%H%M); sudo mkdir -p /root/xui-backups
sudo cp /etc/x-ui/x-ui.db            /root/xui-backups/x-ui.db.$S
sudo cp /usr/local/x-ui/x-ui         /root/xui-backups/x-ui.bin.$S
sudo cp /usr/local/x-ui/bin/xray-linux-amd64 /root/xui-backups/xray.bin.$S
sudo cp /usr/bin/x-ui                /root/xui-backups/x-ui.sh.$S
sudo tar czf /root/xui-backups/certs.$S.tgz /root/cert /etc/nginx/ssl 2>/dev/null
```
Store copies off-server, encrypted. Do **not** put backups inside `/etc/nginx/sites-enabled/`.

## Update 3X-UI + Xray core together

`x-ui update` (menu option "Update") updates the panel **and** the bundled Xray core, keeps `/etc/x-ui/x-ui.db`,
verifies the release checksum and runs DB migrations. Update both together: a new panel with an old core (or the reverse)
is the likelier source of breakage.

```bash
# read the release notes FIRST (look for "Before you upgrade" / "Action required")
curl -s https://api.github.com/repos/MHSanaei/3x-ui/releases/latest | grep -E 'tag_name|published_at'
echo "" | sudo x-ui update        # the script asks y/N (Enter = yes); sudo-rs: no -E needed here
```
Observed in 3.9.0: a migration may log `duplicate column name` once and succeed on the automatic restart. A **migration
failure stops the panel** → restore from the backup above.

**Mandatory checks after the update (all of them):**

```bash
sudo systemctl is-active x-ui nginx fail2ban ssh ; sudo x-ui status
sudo /usr/local/x-ui/bin/xray-linux-amd64 -version | head -1
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
sudo journalctl -u x-ui --since -10min | grep -iE 'error|migrat'      # NRestarts, migration errors
sudo python3 scripts/loopback-test.py                                  # real handshake per inbound
sudo env CDN_DOMAIN=… SUB_PATH=… SUB_ID=… bash scripts/verify-server.sh
```
Hysteria regression (`version != 2` in the log) → `scripts/fix-hysteria-stream.py`.

## System updates

```bash
sudo apt update && apt list --upgradable        # kernel / openssh / nginx in the list?
sudo DEBIAN_FRONTEND=noninteractive apt upgrade -y
[ -f /var/run/reboot-required ] && cat /var/run/reboot-required.pkgs
```
`apt upgrade` (not `dist-upgrade`/`do-release-upgrade`) does not remove packages. A pending kernel needs a **reboot**: it drops all
profiles for ~1 minute — schedule it, keep a provider console open, and afterwards check: kernel (`uname -r`), `reboot-required` gone,
services active, ports listening, `verify-server.sh`. UFW, fail2ban and the acme.sh cron persist by themselves; the IPsum nft table does not (it is rebuilt by `ipsum-block.timer` 2 minutes after boot —
the unit was verified to rebuild it from a clean state, a full reboot with IPsum installed was not exercised, so confirm `verify-server.sh` after the first reboot).

## Restore

```bash
sudo x-ui stop
sudo cp /root/xui-backups/x-ui.db.<stamp> /etc/x-ui/x-ui.db        # DB only
# panel binary rollback if the new version misbehaves:
sudo cp /root/xui-backups/x-ui.bin.<stamp> /usr/local/x-ui/x-ui ; sudo cp /root/xui-backups/xray.bin.<stamp> /usr/local/x-ui/bin/xray-linux-amd64
sudo x-ui start
```

## What updates preserve / may change

* Preserved: `/etc/x-ui/x-ui.db` (inbounds, clients, settings, hosts), `/root/cert/`, nginx, UFW, IPsum, fail2ban jails (the updater re-writes the `3x-ipl` jail).
* May change: Xray core (retest Hysteria + Reality), panel API behaviour (3.9: `inbounds/update` no longer edits clients — `api-reference.md`),
  `webBasePath` must be unchanged (verify), panel UI.

## Related

`compatibility.md` · `testing-methods.md` · `monitoring.md` · `gotchas.md`
