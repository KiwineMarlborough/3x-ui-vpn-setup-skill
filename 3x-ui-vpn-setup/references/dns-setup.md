# DNS Setup (Cloudflare and generic)

Before TLS and subscriptions work, DNS must point to VPS with correct proxy mode.

## Records

| Host | Type | Value | Proxy |
|------|------|-------|-------|
| `panel` | A | `<vps-ip>` | **DNS only** (grey cloud) |
| `cdn` | A | `<vps-ip>` | **DNS only** (grey cloud) |

Use same VPS IP for both in single-node setup.

## Cloudflare steps

1. Add site or use existing zone
2. DNS → Add record → A → `panel` → VPS IP → **Proxy status: DNS only**
3. Repeat for `cdn`
4. TTL: Auto or 300s for faster cutover during migration
5. SSL/TLS mode: **Full** or Full (strict) — VPS serves its own LE certs

## Why proxy must be OFF

Orange cloud (proxied) breaks:

- Non-443 VPN ports (8443, 8444, 2053, 2096, 36712)
- UDP Hysteria through Cloudflare proxy
- Direct IP binding for Xray inbounds

CDN fallback nginx on 443 still works with grey cloud — traffic hits VPS directly.

## Propagation check

```bash
dig +short panel.vpn.example.com A
dig +short cdn.vpn.example.com A
# Both must return VPS IP (not Cloudflare anycast if proxy off)
```

From agent machine:

```bash
nslookup panel.vpn.example.com
nslookup cdn.vpn.example.com
```

Wait 5–30 min after create; up to TTL on changes.

## Panel cert timing

Issue LE certs **after** DNS resolves:

```bash
dig +short panel.vpn.example.com @8.8.8.8
dig +short cdn.vpn.example.com @8.8.8.8
```

3X-UI ACME needs HTTP-01 or DNS-01 reachable on panel.

## Migration cutover

1. Lower TTL to 300s one day before
2. Change A records to new VPS IP
3. Wait TTL
4. Re-issue certs on new server if domain moved

See `references/migration.md`.

## Other DNS providers

Same rules: A record → VPS, no CNAME through proxy for VPN ports.

## Related

- `execution-order.md` — Phase 4 DNS before TLS
- `references/nginx-fallback.md` — cdn domain on 443
- `references/panel-settings.md` — webDomain = panel hostname