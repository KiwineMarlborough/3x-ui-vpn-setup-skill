# RKN and Blocking Context (RU users)

Informational — not legal advice. Helps agents explain behavior to Russian users.

## Why borrowed Reality SNI works

Reality uses a **legitimate third-party SNI** (e.g. `pixelforge.pics`) in TLS ClientHello:

- Traffic goes to **your VPS IP**, not the SNI site's server
- RKN registry blocks **domains/IPs listed** — a random SaaS SNI not in registry is usually not blocked as your VPN
- Your `panel.*` / `cdn.*` domains are separate — not exposed in Reality handshake

**Do not** use your own VPN domain as Reality SNI — links infra to VPN.

## What can still get blocked

| Target | Effect | Mitigation |
|--------|--------|------------|
| VPS IP added to registry | All protocols fail | New IP / provider; optional WARP |
| Port blocking on mobile | TCP fails | XHTTP 2053 |
| UDP blocked | Hysteria fails | Reality / XHTTP |
| SNI filtering | Reality fails | Change SNI (`reality-sni.md`) |
| DPI on carrier | Intermittent | XHTTP, Hysteria |

## Happ split routing vs blocking

`.ru` direct (SplitRU) sends Russian sites **outside VPN** — home ISP IP:

- Banks see home IP — often required
- RKN blocking of foreign VPN IP does not affect .ru direct path
- Foreign sites use DE/NL VPS IP

This is **client-side** routing — no second VPS needed.

## When to add RU Slave

Need **Russian exit IP** while abroad (not home IP):

- See `references/slave-node.md`
- Server-side cascade — more complex

## WARP on VPS

Optional egress if VPS IP blocked — `references/warp-optional.md`.

Usually **not** needed for personal DE VPS. Last resort.

## Rotation playbook

1. Test from client: which profile fails?
2. All fail → likely IP block → ping VPS, check provider
3. Only Reality → new SNI
4. Only TCP → try XHTTP
5. Only Hysteria → UDP block — use TCP/Reality

## Related

- `references/reality-sni.md` — SNI validation
- `references/protocol-selection.md` — profile choice
- `references/warp-optional.md` — Cloudflare egress