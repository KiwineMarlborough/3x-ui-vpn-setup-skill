# VPS Provider Notes

Generic guidance — not endorsements. Skill targets small personal VPN (1–2 users).

## Minimum specs

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 1 GB | 2 GB |
| CPU | 1 vCPU | 2 vCPU |
| Disk | 10 GB | 20 GB |
| Traffic | 500 GB/mo | 1 TB+ |
| IPv4 | Required | Required |
| IPv6 | Optional | Nice for future |

## Location

| Label | Use case |
|-------|----------|
| DE / NL / FI | Low latency EU, common for RU users |
| US | Streaming geo, higher latency to RU |

Match `COUNTRY_LABEL` in inbound names (e.g. `DE-Reality-Vision`).

## Providers community uses

| Provider | Pros | Watchouts |
|----------|------|-----------|
| Hetzner | Price, DE/FI DCs | IP occasionally flagged — rotate |
| OVH | EU locations | Verify UDP not filtered |
| Vultr | Many regions | Check TOS on VPN |
| DigitalOcean | Simple | Higher $/GB |
| Timeweb / Selectel | RU billing | DE VPS for exit, not RU DC for censorship bypass |

Always check **TOS** — personal use assumed.

## IP quality check

After purchase:

```bash
curl -4 ifconfig.me
# Test from client: Reality connect, speedtest
```

If IP pre-blocked in RU: request replacement IP or try WARP (`warp-optional.md`).

## Firewall at provider

Some panels have **provider firewall** separate from UFW — open:

- 22/tcp (SSH)
- 80, 443/tcp
- 8443, 8444, 2053, 2096/tcp
- 36712/udp
- 29800/tcp (panel — or tunnel only)

## Related

- `references/optimization.md` — swap, BBR
- `references/dns-setup.md`
- `references/rkn-and-blocking.md`