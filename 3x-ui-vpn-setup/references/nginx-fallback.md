# Nginx CDN Fallback

## Goal

Port 443 serves a **legitimate-looking website** (fake CDN landing), not obvious VPN TLS on standard HTTPS port.

## Port layout

| Port | Service |
|------|---------|
| 80 | nginx → redirect HTTPS |
| 443 | nginx static / CDN page |
| 8443 | Xray VLESS Reality |
| 8444 | Xray VLESS TCP (Podkop) |
| 10443 | nginx alt TLS (optional) |

## Rules

1. **Do not** enable Xray inbound on 443 while nginx listens there.
2. UFW: allow 80, 443, 10443/tcp.
3. Sync LE cert: when `cdn01` cert renews, copy or symlink to nginx ssl dir.

## Automated deploy

```bash
export CDN_DOMAIN=cdn.vpn.example.com
export CERT_SRC=/root/cert/cdn.vpn.example.com
sudo -E bash scripts/deploy-nginx-fallback.sh
sudo -E bash scripts/deploy-cert-hook.sh
```

Uses `templates/nginx-cdn.conf` + `assets/cdn-fallback/index.html`.

## Manual / customize

Edit `index.html` title/branding before deploy. Full vhost: `templates/nginx-cdn.conf`.

## Fallback in disabled inbound #1 (optional future)

If VLESS ever shares 443 with nginx via fallbacks:

```json
"fallbacks": [
  {"alpn": "http/1.1", "dest": "127.0.0.1:80", "name": "cdn-http11"},
  {"alpn": "", "dest": "127.0.0.1:80", "name": "cdn-default"}
]
```

Enabling inbound #1 requires a **migration plan** (move nginx off 443 or drop nginx on 443).

## Verify

```bash
sudo nginx -t
curl -sk -o /dev/null -w '%{http_code}\n' https://cdn01.example.com/
curl -sk -o /dev/null -w '%{http_code}\n' https://cdn01.example.com:10443/
```

Expect `200`.