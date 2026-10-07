# Nginx CDN Fallback

## Goal

Port 443 serves a **legitimate-looking website** (fake CDN landing), not obvious VPN TLS on the standard HTTPS port.
It is also the **ACME validation endpoint** on port 80 (certificate renewal), so it must keep working.

## Port layout

| Port | Service |
|------|---------|
| 80 | nginx: `/.well-known/acme-challenge/` (renewal) + redirect to HTTPS |
| 443 | nginx static / CDN page |
| 8443 | Xray VLESS Reality |
| 8444 | Xray VLESS TCP (Podkop/Forkop) |
| 2053 | Xray VLESS XHTTP |
| 2096 | 3X-UI subscription server |
| 10443 | nginx alt TLS (optional) |
| 36712/udp | Hysteria2 · optional AmneziaWG UDP port |

## Rules

1. **Do not** enable an Xray inbound on 443 while nginx listens there (a leftover test Reality inbound on 443 once took the port from nginx; clients that fetched the subscription URL without an
   explicit port then got `403 Forbidden` — most likely Reality relaying the non-Reality request to the borrowed site, which does not know your host).
2. UFW: allow 80, 443, 10443/tcp.
3. **`sites-enabled/<name>` must be a symlink** to `sites-available/<name>`; never put backup files in `sites-enabled/`.
4. Port 80 must serve `/.well-known/acme-challenge/` *before* redirecting (template does) — otherwise renewal fails silently.
5. Certificates: `cert-renewal-nginx.md` (acme.sh webroot + deploy hook that syncs this nginx copy).
6. `server_tokens off;` (in the template) — do not advertise the nginx version.

## Automated deploy

```bash
export CDN_DOMAIN=cdn.vpn.example.com
export CERT_SRC=/root/cert/cdn.vpn.example.com
sudo env "CDN_DOMAIN=$CDN_DOMAIN" "CERT_SRC=$CERT_SRC" bash scripts/deploy-nginx-fallback.sh   # vhost + landing page, symlinked
sudo env "CDN_DOMAIN=$CDN_DOMAIN" bash scripts/deploy-acme-renewal.sh                          # preflight; then STAGING_TEST=1, APPLY=1
```
Uses `templates/nginx-cdn.conf` + `assets/cdn-fallback/index.html`. `scripts/deploy-cert-hook.sh` is the legacy certbot variant.

## Manual / customize

Edit `index.html` title/branding before deploy. Full vhost: `templates/nginx-cdn.conf`.

## Fallback in an inbound on 443 (optional future)

If VLESS ever shares 443 with nginx via fallbacks:

```json
"fallbacks": [
  {"alpn": "http/1.1", "dest": "127.0.0.1:80", "name": "cdn-http11"},
  {"alpn": "", "dest": "127.0.0.1:80", "name": "cdn-default"}
]
```
Enabling it requires a **migration plan** (move nginx off 443 or drop nginx on 443).

## Verify

```bash
sudo nginx -t && sudo nginx -T | grep -nE 'listen|server_name|acme-challenge'
ls -l /etc/nginx/sites-enabled/                         # symlink, no stray backups
curl -sk -o /dev/null -w '%{http_code}\n' https://cdn.vpn.example.com/        # 200
curl -s -o /dev/null -w '%{http_code}\n' http://cdn.vpn.example.com/.well-known/acme-challenge/x   # 404 from nginx, NOT 301
curl -sI https://cdn.vpn.example.com/ | grep -i '^server:'                    # "nginx" without a version
```

## Related

`cert-renewal-nginx.md` · `dns-setup.md` · `gotchas.md`
