# Protocol Selection Guide

Which inbound to use when — for agents advising users and for multi-user inbound assignment.

## Quick matrix

| Profile | Port | When to use |
|---------|------|-------------|
| **Reality-Vision** | 8443 | Default for iOS/Android — best stealth, primary |
| **TCP-Podkop** | 8444 | Routers, OpenWrt, clients without XHTTP/Hysteria |
| **XHTTP-Mobile** | 2053 | Mobile carrier DPI blocks Reality/TCP |
| **Hysteria2** | 36712/udp | Fast UDP path; when TCP throttled and UDP allowed |

## By client app

| App | Recommended | Avoid |
|-----|-------------|-------|
| Happ Plus (iOS) | Reality → XHTTP → Hysteria | — |
| v2rayNG / Streisand | Reality (flow=vision) | Old builds + XHTTP |
| Hiddify / Nekoray | JSON sub, any profile | — |
| OpenWrt / Passwall | TCP 8444, Reality 8443 | XHTTP, Hysteria on old cores |
| Desktop router VM | TCP 8444 only | Hysteria UDP through NAT |

## By network symptom

| Symptom | Try next |
|---------|----------|
| Latency `-1` on Reality but sites work | Ignore ping; Reality OK |
| Timeout on all TCP profiles | XHTTP 2053 |
| Connects but slow on TCP | Hysteria2 (if UDP open) |
| UDP games/streaming OK, browsing blocked | Reality or XHTTP, not Hysteria |
| Only .ru sites fail with split routing | Happ routing direct path — not VPN issue |
| Everything slow | Check VPS load; not protocol |

## By user role

| User | Inbounds | Notes |
|------|----------|-------|
| `user-phone@` | All 4 | Primary daily driver |
| `user-router@` | 8443 + 8444 | `limitIp` 1–2; see `multi-user.md` |
| `user-guest@` | 8443 only | Easy revoke, traffic cap |

## Stealth vs speed

```
Stealth:  Reality > XHTTP > TCP TLS > Hysteria (UDP fingerprint differs)
Speed:    Hysteria > Reality > TCP > XHTTP (overhead varies by path)
```

Reality mimics TLS to borrowed SNI — preferred in restrictive regions.

## When to change Reality SNI

- Reality connects but resets on specific networks
- SNI domain dead or cert expired (`reality-sni.md`)
- Do **not** switch to your own VPN domain as SNI

## Related

- `references/inbounds.md` — field recipes
- `references/clients.md` — per-app notes
- `references/rkn-and-blocking.md` — blocking context