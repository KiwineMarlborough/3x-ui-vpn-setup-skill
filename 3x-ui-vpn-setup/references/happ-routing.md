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
| `templates/happ-routing-profile-ru.json` | **Default for RU users** — `.ru` + geosite direct |
| `templates/happ-routing-profile.json` | Basic split (lighter DirectSites list) |
| `templates/happ-routing-banks-ru.json` | Extended banks / gosuslugi / Yandex direct |
| `templates/happ-routing-corporate.json` | `.ru` + `.local` + corp domains |
| `templates/happ-routing-global.json` | Full tunnel, no direct sites |
| Customize `DirectSites` | Add your domains to any template |

Rename `"Name"` field to anything (e.g. `SplitHome`, `MyVPN`) — visible in Happ routing list.

## DNS (DoH both channels — recommended)

| Channel | Type | Endpoint | IP pin |
|---------|------|----------|--------|
| Remote (VPN) | DoH | `https://cloudflare-dns.com/dns-query` | 1.1.1.1 |
| Domestic (direct) | DoH | `https://dns.google/dns-query` | 8.8.8.8 |

`DnsHosts` prevents ISP poisoning of resolver hostnames.

### DoH vs DoT vs DoU

| Type | Happ fields | Pros | Cons |
|------|-------------|------|------|
| **DoH** | `RemoteDNSType: DoH` + `RemoteDNSDomain` URL | HTTPS camouflage, works on restrictive Wi‑Fi | Slightly more overhead |
| **DoT** | `DoT` + hostname | Standard TLS DNS | Distinct port 853, easier to block |
| **DoU** | `DoU` + IP | Fast UDP | Plain UDP DNS — ISP can see queries on direct path |

**Skill default: DoH for both Remote and Domestic** — matches commercial VPN apps and resists domestic ISP DNS hijacking on split-tunnel direct path.

To use DoT instead, change e.g. `DomesticDNSType` to `DoT`, `DomesticDNSDomain` to `dns.google`, keep `DomesticDNSIP` pinned in `DnsHosts`.

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
## Added in 1.3

* **Compare with commercial profiles:** a typical "Liberty-style" profile decodes to the same idea as `happ-routing-profile-ru.json`
  (`domain:.ru`, `domain:.xn--p1ai`, `geosite:category-ru` direct; private ranges direct; DoH both channels; Loyalsoldier geo files).
  Optional extra direct range seen there: `100.64.0.0/10` (carrier-grade NAT, also Tailscale) — the shipped templates include it.
  Pinning resolver hostnames in `DnsHosts` (as the templates do) is the safer variant.
* **Decode a profile (yours or someone's):** the part after `happ://routing/add/` or `/onadd/` is base64 of JSON:
  `python3 -c "import sys,base64,json;b=sys.argv[1];print(json.dumps(json.loads(base64.b64decode(b+'='*(-len(b)%4))),indent=1))" <base64>`.
* **After a direct SQLite edit of `subRoutingRules` the panel keeps serving the OLD value until `systemctl restart x-ui`.**
  Verify what is really served: `curl -skD- -o/dev/null <sub-url> | grep -i '^Routing:'` and decode it. Prefer `scripts/apply-routing.py`
  (API) which avoids the stale cache.
* **Scope:** routing is a Happ feature carried in the subscription. It does not apply to AmneziaVPN/AmneziaWG or OpenWrt
  tunnels (`amneziawg.md`); there, split routing is the router tool's job.
* Routing profile applies on the client only; server-side Xray routing cannot make `.ru` sites see the client's own IP.
