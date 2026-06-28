# Choosing a Reality SNI (borrowed front)

Reality `serverName` must point to a **real HTTPS site** on port 443, not your VPN domain.

## Good candidates

- Legitimate SaaS / login pages (static front)
- Sites on CDN (Cloudflare, Bunny)
- TLS 1.3 + valid cert chain
- Not on obvious VPN blocklists

## Validate before use

```bash
SNI=pixelforge.pics
curl -skI --resolve "${SNI}:443:$(dig +short $SNI | head -1)" "https://${SNI}/" | head -5
openssl s_client -connect "${SNI}:443" -servername "$SNI" </dev/null 2>/dev/null | openssl x509 -noout -subject -dates
```

Check:
- HTTP 200/301/302 (not connection reset)
- Cert not expired
- Site loads in browser (optional)

## Bad choices

| Avoid | Why |
|-------|-----|
| Your `cdn.*` / `panel.*` domain | Links VPN to your infra |
| `google.com`, `microsoft.com` | Wrong cert / blocking |
| Dead domains | Reality handshake fails |
| Sites blocked in your country only | OK for server in DE; test from client region |

## Examples used in community

- `pixelforge.pics` — SaaS login page
- Other `.pics` / neutral SaaS fronts

Rotate SNI if blocked — update inbound + client subscription.

## dest field

Always `dest: "<sni>:443"` matching `serverName`.