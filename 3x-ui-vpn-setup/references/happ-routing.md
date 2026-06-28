# Happ Plus Meridian Routing

## Purpose

Client-side split tunnel in Happ:

- `.ru`, `.рф`, `geosite:category-ru`, private IPs → **direct** (no VPN)
- Everything else → **through VPN**

DNS is configured per path (encrypted DoH for both channels in recommended profile).

## Enable in 3X-UI

1. Panel → Subscription settings: `subEnableRouting = true`
2. Set `subRoutingRules` to:

```
happ://routing/onadd/<base64-encoded-json>
```

3. Restart `x-ui`
4. Subscription response must include headers:
   - `Routing-Enable: true`
   - `Routing: happ://routing/onadd/...`

## Recommended profile (Liberty-style DNS)

Use `templates/meridian-routing.json`:

| Field | Value | Role |
|-------|-------|------|
| RemoteDNSType | DoH | Foreign/proxied sites |
| RemoteDNSDomain | `https://cloudflare-dns.com/dns-query` | |
| RemoteDNSIP | `1.1.1.1` | DnsHosts pin |
| DomesticDNSType | DoH | Direct .ru sites |
| DomesticDNSDomain | `https://dns.google/dns-query` | |
| DomesticDNSIP | `8.8.8.8` | DnsHosts pin |
| DnsHosts | cloudflare + dns.google | Anti-poisoning |
| FakeDNS | false | Avoid app breakage |
| GlobalProxy | true | |
| DomainStrategy | IPIfNonMatch | |

## Apply via API (Python example)

```python
import base64, json

profile = json.load(open("templates/meridian-routing.json"))
rule = "happ://routing/onadd/" + base64.b64encode(
    json.dumps(profile, ensure_ascii=False).encode()
).decode()

# PATCH setting/all → subEnableRouting=True, subRoutingRules=rule
# POST setting/update with full obj (no has* keys)
```

## Client refresh

User: Happ Plus → pull subscription down to refresh. Re-import not required if routing header updates.

## Server Xray DNS vs Happ DNS

- **Happ routing DNS** = on phone (what this doc covers)
- **Panel Xray Settings → DNS** = server-side; can stay empty if all split is on client
- Enable server DNS when using router without Happ routing or server-side geosite rules

## Verify

```bash
curl -skI 'https://cdn01.example.com:2096/<subPath>/<sub_id>' | grep -i routing
```

Decode base64 after `happ://routing/onadd/` to confirm `DomesticDNSType: DoH`.