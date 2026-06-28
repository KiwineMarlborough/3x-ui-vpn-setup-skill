# Panel Security Hardening

## Minimum (always)

1. Change default panel password immediately after install
2. Set unique `webBasePath` (random string)
3. Create API token; do not share in git
4. `webDomain` = panel hostname only
5. Panel LE cert matches `webDomain`

## Recommended: panel not on public internet

Bind panel to localhost, access via SSH tunnel:

```bash
# On server (panel settings or sqlite):
# webListen = 127.0.0.1
# Keep panel port e.g. 29800

# On laptop:
ssh -N -L 29800:127.0.0.1:29800 user@vps-ip
# Open https://panel.<domain>:29800/<webBasePath>/ locally
```

UFW: **do not** expose panel port publicly if using tunnel only.

## fail2ban (SSH)

```bash
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
```

Default jail `sshd` protects brute force on port 22.

## ICMP

Optional drop ping (stealth, not security):

```bash
# /etc/ufw/before.rules — ICMP DROP rules (test SSH first)
```

## Podkop / split admin access

If using Podkop on phone for .ru direct:
- Route **only** `panel.<domain>` through VPN for admin
- **Do not** route bare VPS IP through VPN (VPN-in-VPN loop risk)

## API access from server

When `webDomain` is set, curl from server needs:

```bash
R='--resolve panel.<domain>:29800:127.0.0.1'
```

## Backup before changes

Panel → Settings → Backup, or:

```bash
sudo cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +%F).db
sudo tar czf /root/backups/certs-$(date +%F).tar.gz /root/cert/
```