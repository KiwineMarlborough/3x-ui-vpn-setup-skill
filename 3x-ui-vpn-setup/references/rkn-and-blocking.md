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
## Added in 1.3 — how servers actually get found, and what the skill does about it

| Exposure | Why it matters | Mitigation in this skill |
|----------|----------------|--------------------------|
| Public panel hostname + certificate | listed forever in Certificate Transparency logs; a name like `panel…` says what it is; links your decoy domain to the same IP | no panel DNS record, tunnel-only access (`panel-tunnel-access.md`) |
| Internet-wide port scans + TLS certificate grabs | the same real certificate on 443/8444/2053/2096/10443 = "proxy host" pattern | Reality (borrowed SNI) where the protocol allows; one SNI per Reality port; TLS inbounds are the weak spot (`inbounds.md`) |
| Known scanner/botnet IPs hammering SSH, nginx, panel | noise, attack surface, probing | IPsum drop (`blocklist-ipsum-fail2ban.md`) + Fail2Ban |
| Active probing of VLESS/Reality | probes get relayed to the borrowed site by design | correct `dest`, valid borrowed SNI (`reality-sni.md`) |
| Datacenter IP | scored by classifiers regardless of protocol | **not fixable here** (new provider/IP or an extra egress hop) |
| Cloudflare "to hide the IP" | the orange cloud breaks Reality/UDP/odd ports | never proxy the shared VPN hostname (`dns-setup.md`) |

Reported by research in 2026 (not verified here): TSPU matches TLS ClientHello fingerprints (JA3/JA4) and behaviour, probes suspected
proxies with varied handshakes, and blocked plain VLESS more aggressively than Reality. Use realistic client fingerprints (`firefox`/`chrome`).
Hysteria2/AmneziaWG are UDP: a network that allows UDP can still pass them when TCP profiles are throttled — and the reverse.
No protocol is guaranteed; keep several profiles and test from the networks you use.
