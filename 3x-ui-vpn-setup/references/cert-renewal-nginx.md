# Cert Renewal + nginx Sync

When LE renews `cdn.<domain>` cert, nginx copy may stale.

## Layout

```
/root/cert/<cdn-domain>/fullchain.pem
/root/cert/<cdn-domain>/privkey.pem
/etc/nginx/ssl/cdn/fullchain.pem   # copy or symlink
/etc/nginx/ssl/cdn/privkey.pem
```

## After renewal hook

Create `/etc/letsencrypt/renewal-hooks/deploy/sync-nginx-cdn.sh`:

```bash
#!/bin/bash
CDN_DOMAIN="cdn.vpn.example.com"
SRC="/root/cert/${CDN_DOMAIN}"
DST="/etc/nginx/ssl/cdn"
cp "${SRC}/fullchain.pem" "${DST}/fullchain.pem"
cp "${SRC}/privkey.pem" "${DST}/privkey.pem"
nginx -t && systemctl reload nginx
```

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/sync-nginx-cdn.sh
```

If 3X-UI manages certs in `/root/cert/`, sync from there after panel renewal too.

## Test renewal

```bash
sudo certbot renew --dry-run
```