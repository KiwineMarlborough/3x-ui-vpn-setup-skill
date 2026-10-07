# Certificate Lifecycle (acme.sh), nginx sync and expiry monitoring

**The #1 silent failure of this setup:** the CDN certificate expires after ~90 days, nothing complains, and
TLS-based profiles (TCP/XHTTP/Hysteria2), the subscription and the CDN page suddenly stop validating.
Clients show "n/a"/no connection — it looks exactly like "the VPN got blocked". Only Reality is unaffected
(it needs no real certificate), which makes the symptom even more confusing.

## How certificates are really issued here

3X-UI's SSL menu (`x-ui` → *SSL Certificate Management*) installs **acme.sh** (not certbot) in `/root/.acme.sh`
and issues in **standalone** mode (`Le_Webroot='no'`): acme.sh itself must bind **port 80** during issue *and*
every renewal.

This skill puts **nginx on 80/443** → port 80 is busy → renewal fails **silently** (cron output is discarded)
→ the certificate expires. A second trap: a certificate issued with the panel hostname as an extra name (SAN)
cannot be renewed once that DNS record is removed (see `panel-tunnel-access.md`).

| Symptom | Cause |
|---------|-------|
| Cert dated ~90 days ago, `Le_NextRenewTimeStr` in the past | renewal never succeeded |
| `acme.sh --list` shows `Le_Webroot='no'` | standalone mode + nginx on :80 |
| TLS profiles dead, Reality works | expired certificate |
| `certificate has expired or is not yet valid` in `loopback-test.py` / Xray client log | expired certificate |
| nginx copy older than `/root/cert/...` | no deploy hook (`check-cert-expiry.sh` prints *stale copy*) |

## Layout

```
/root/.acme.sh/                          acme.sh + per-domain state (*_ecc)
/root/cert/<cdn-domain>/fullchain.pem    what 3X-UI reads (subCertFile, inbound certs)
/root/cert/<cdn-domain>/privkey.pem
/etc/nginx/ssl/cdn/{fullchain,privkey}.pem   nginx copy (synced by the deploy hook)
/var/www/cdn-fallback/.well-known/acme-challenge/   webroot for HTTP-01
```

## Fix / set up (one command, idempotent)

Prerequisite: nginx port-80 block from `templates/nginx-cdn.conf` — it serves the challenge path **before**
redirecting (a server-level `return 301` hides the `location` block).

```bash
export CDN_DOMAIN=cdn.vpn.example.com
# 1. preflight: acme.sh present, nginx serves the challenge on :80, reachable through public DNS
sudo env "CDN_DOMAIN=$CDN_DOMAIN" bash scripts/deploy-acme-renewal.sh
# 2. prove the whole ACME cycle on the Let's Encrypt STAGING CA (temp dir; real cert untouched)
sudo env "CDN_DOMAIN=$CDN_DOMAIN" STAGING_TEST=1 bash scripts/deploy-acme-renewal.sh
# 3. issue in webroot mode + install + deploy hook + cron
sudo env "CDN_DOMAIN=$CDN_DOMAIN" APPLY=1 bash scripts/deploy-acme-renewal.sh
```

The deploy hook (`/usr/local/sbin/cdn-cert-deploy.sh`) copies the cert to nginx, reloads nginx and **restarts x-ui**
(a restart is the safe way to make the panel, subscription server and inbounds pick up the new files). acme.sh remembers `--reloadcmd`, so every future renewal runs it.
Issue only the names you really need: **do not add the panel hostname** (it may disappear from DNS).
Ubuntu 26.04 note: `sudo -E` is ignored (sudo-rs) — pass variables with `sudo env VAR=... bash`.

`scripts/deploy-cert-hook.sh` is the old **certbot**-only hook; it does nothing when acme.sh issued the cert.

## Monitoring (mandatory — this is what was missing)

```bash
sudo bash scripts/check-cert-expiry.sh        # exit 1 if < FAIL_DAYS (7) or expired; WARN < 30 days; flags stale copies
```

`verify-server.sh` also checks the certificate **actually served** on 443/2096 (what clients see) and fails below
7 days. Add `check-cert-expiry.sh` to cron/healthcheck (`monitoring.md`) and always run it when entering a server.
acme.sh's own schedule: ARI window, normally first renewal attempt ~30 days before expiry.

## Panel certificate

If the panel is reachable **only through an SSH tunnel** (recommended, `panel-tunnel-access.md`) it does not need a
public Let's Encrypt certificate: use a long-lived self-signed one and remove the panel name from acme.sh —

```bash
D=/root/cert/panel.vpn.example.com
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes -days 3650 \
  -keyout $D/privkey.pem -out $D/fullchain.pem \
  -subj "/CN=panel.vpn.example.com" -addext "subjectAltName=DNS:panel.vpn.example.com"
chmod 600 $D/privkey.pem; systemctl restart x-ui
/root/.acme.sh/acme.sh --remove -d panel.vpn.example.com --ecc    # stop daily failing renewals
```

The browser shows a one-time warning (some Chromium-based browsers hide the "proceed" button — use another
browser for the panel, or type `thisisunsafe` on the error page, or import the cert as trusted).
Never request a public cert for the panel name: every issued name lands in public Certificate Transparency logs.

## Test renewal path any time

`STAGING_TEST=1` (above) — full ACME validation through port 80 without spending production rate limits.

## Related

`nginx-fallback.md` · `monitoring.md` · `gotchas.md` · `repair-only.md` (cert expired branch) · `panel-tunnel-access.md`
