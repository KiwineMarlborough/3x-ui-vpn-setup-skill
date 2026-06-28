# Happ Plus Routing in Subscription

Embed **client-side split routing** in the 3X-UI subscription response so Happ Plus applies rules automatically on import/refresh.

## What it does

- Selected domains/IPs → **direct** (bypass VPN)
- Everything else → **through VPN**
- Separate **encrypted DNS** (DoH) for proxied vs direct paths

## Enable in 3X-UI

1. `subEnableRouting = true`
2. `subRoutingRules` = `happ://routing/onadd/<base64-json>`
3. Restart `x-ui`
4. Subscription response headers:
   - `Routing-Enable: true`
   - `Routing: happ://routing/onadd/...`

## Profile templates

| File | Use case |
|------|----------|
| `templates/happ-routing-profile.json` | Split: `.ru` direct, rest VPN (default for RU users) |
| `templates/happ-routing-global.json` | Full tunnel, no direct sites |
| Customize `DirectSites` | Add `.local`, corporate domains, etc. |

Rename `"Name"` field to anything (e.g. `SplitHome`, `MyVPN`) — visible in Happ routing list.

## DNS (DoH both channels)

| Channel | Type | Endpoint | IP pin |
|---------|------|----------|--------|
| Remote (VPN) | DoH | `https://cloudflare-dns.com/dns-query` | 1.1.1.1 |
| Domestic (direct) | DoH | `https://dns.google/dns-query` | 8.8.8.8 |

`DnsHosts` prevents ISP poisoning of resolver hostnames.

## Apply via API

```python
import base64, json

with open("templates/happ-routing-profile.json") as f:
    profile = json.load(f)

profile["Name"] = "SplitHome"  # user-visible label

rule = "happ://routing/onadd/" + base64.b64encode(
    json.dumps(profile, ensure_ascii=False).encode()
).decode()

# GET settings via setting/all
# SET subEnableRouting=True, subRoutingRules=rule
# POST setting/update (full object, no has* keys)
```

## Client refresh

Happ Plus → pull subscription down to refresh routing. Full re-import usually not needed.

## Verify

```bash
curl -skI "https://cdn.<domain>:2096/<subPath>/<sub_id>" | grep -i routing
```

Decode base64 after `happ://routing/onadd/` — confirm `DomesticDNSType: DoH`.

## Server Xray DNS vs Happ routing DNS

- **This doc** = DNS on **client** (Happ), pushed via subscription
- **Panel → Xray → DNS** = server-side; optional if all split is on client
- Enable server DNS for routers without Happ routing support