# Panel and Server Security Hardening

## Always

1. Change the default panel credentials immediately after install.
2. Unique random `webBasePath` (necessary, **not sufficient** — see `panel-tunnel-access.md`).
3. API token scoped/expiring where the version allows; never in git (`secrets-management.md`).
4. `webDomain` = panel hostname; the panel cert must match it (a self-signed cert is fine when tunnel-only).
5. UFW: default deny incoming; open only what is used (22, 80, 443, 10443?, 8443, 8444, 2053, 2096, 36712/udp and, if
   AmneziaWG is installed, its UDP port). **Close the panel port** and remove unused rules.
6. IPsum blocklist + Fail2Ban (`blocklist-ipsum-fail2ban.md`) — part of the default setup.
7. SSH: key login for admin accounts, no shared passwords, an audited list of accounts and sudo rules
   (`agent-access-hygiene.md`).

## Default: panel not on the public internet

Full procedure in `panel-tunnel-access.md`: no public DNS record for the panel name, self-signed certificate,
`ufw deny <panel-port>/tcp`, access via `ssh -L` plus a hosts-file entry. This also removes the panel name from public
Certificate Transparency logs and from internet-wide scanners.

```bash
sudo ufw deny 29800/tcp comment "3xui panel - SSH tunnel only"
```

## SSH

* `PasswordAuthentication no` globally, with explicit `Match User` exceptions only where you really need passwords
  (e.g. `Match User root` → `PasswordAuthentication yes`). Anyone who can log in as root with a password is the weakest
  link in the whole design; prefer key-only root (`PermitRootLogin prohibit-password`) once your key works.
* Global options go **above** the first `Match` block (`sshd -t` rejects e.g. `DebianBanner` inside `Match`).
* Hide the distro suffix from the banner: `DebianBanner no` (protocol still reveals `OpenSSH_x.y` — unavoidable).
* nginx: `server_tokens off;` (in the vhost template).
* After every sshd/UFW change: `sshd -t`, then open a **second** session before closing the first.

## ICMP

Dropping ping is optional obscurity, not security: `/etc/ufw/before.rules` ICMP rules — test SSH first.

## Split admin access on phones

If a router/phone tool routes `.ru` direct: route **only** the panel hostname through the VPN, **never** the bare VPS IP
(VPN-in-VPN loop).

## Backups before any change

```bash
sudo mkdir -p /root/backups
sudo cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +%F-%H%M).db
sudo cp /usr/local/x-ui/x-ui /root/backups/x-ui.bin.$(date +%F)       # for rollback after a panel update
sudo cp /usr/local/x-ui/bin/xray-linux-amd64 /root/backups/xray.bin.$(date +%F)
sudo tar czf /root/backups/certs-$(date +%F).tgz /root/cert /etc/nginx/ssl 2>/dev/null
```
Never keep backups of `sites-enabled` *inside* `sites-enabled` (nginx includes every file there).

## What a censor/scanner can still see (be honest with the user)

The IP is a datacenter address (flagged by classifiers regardless of protocol); several listening non-standard ports on one
IP with the **same real TLS certificate** is a recognisable "proxy host" pattern (`rkn-and-blocking.md`,
`inbounds.md`). The panel, panel hostname and SSH noise are the parts you *can* remove.

## Related

`panel-tunnel-access.md` · `blocklist-ipsum-fail2ban.md` · `agent-access-hygiene.md` · `dns-setup.md` · `secrets-management.md`
