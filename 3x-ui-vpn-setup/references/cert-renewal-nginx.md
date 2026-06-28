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

Use skill script:

```bash
export CDN_DOMAIN=cdn.vpn.example.com
export CERT_SRC=/root/cert/cdn.vpn.example.com
sudo -E bash scripts/deploy-cert-hook.sh
```

Installs `/etc/letsencrypt/renewal-hooks/deploy/sync-nginx-cdn.sh`.

If 3X-UI manages certs in `/root/cert/`, sync from there after panel renewal too.

## Test renewal

```bash
sudo certbot renew --dry-run
```