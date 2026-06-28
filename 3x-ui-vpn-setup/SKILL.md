---
name: 3x-ui-vpn-setup
description: >
  Autonomous setup of a personal 3X-UI VPN on a fresh Linux VPS via SSH: VLESS Reality
  (primary), XHTTP, TCP Podkop, Hysteria2, Happ routing in subscription (DoH), custom sub
  paths, optional nginx CDN fallback, UFW, Let's Encrypt. Use for new server setup, 3X-UI
  fixes, subscription 404/500, Hysteria version errors. Triggers: 3x-ui, xray, reality,
  hysteria2, happ routing, /3x-ui-vpn-setup. Never patch binaries — panel, API, SQLite only.
license: MIT
compatibility: claude-code, codex, qwen-code, opencode, grok-build, antigravity
metadata:
  author: KiwineMarlborough
  standard: agentskills.io
  version: "1.1"
---

# 3X-UI Personal VPN — Full Server Setup

End-to-end workflow for an AI agent with **SSH access to a clean Linux VPS** (Ubuntu 22.04/24.04).
**Follow `references/execution-order.md` strictly.**

## Start here

1. Read `references/execution-order.md`
2. Collect user inputs (or `.env.local` from `.env.example`)
3. Execute phases over SSH — never instructions-only
4. Run `scripts/verify-server.sh`
5. Deliver `references/post-setup-handoff.md` to user

## Prerequisites from user

| Input | Example | Required |
|-------|---------|----------|
| SSH host | `203.0.113.10` | yes |
| SSH user + key | `deploy`, ed25519 | yes |
| Panel domain | `panel.vpn.example.com` | recommended |
| CDN domain | `cdn.vpn.example.com` | recommended |
| Country label | `DE`, `NL` | yes |
| Reality SNI | `pixelforge.pics` | yes — see `references/reality-sni.md` |
| Happ split .ru? | yes → `happ-routing-profile-ru.json` | default yes |
| nginx on 443? | yes | default yes |

## Hard rules

1. Do **not** patch 3X-UI / Xray binaries
2. Panel + API + SQLite + UFW + nginx only
3. Execute over SSH yourself
4. Verify SSH after firewall changes
5. Hysteria **last** (after sub 200 with 3 profiles)
6. Never commit secrets

## Architecture

```
panel.<domain>:<port>/<webBasePath>  → admin (webDomain lock)
cdn.<domain>                         → VPN + subscription :2096
```

Four inbounds — details: `references/inbounds.md`

| Profile | Port | Protocol |
|---------|------|----------|
| `{CC}-Reality-Vision` | 8443 | VLESS Reality (primary) |
| `{CC}-TCP-Podkop` | 8444 | VLESS TLS, empty flow |
| `{CC}-XHTTP-Mobile` | 2053 | VLESS XHTTP |
| `{CC}-Hysteria2` | 36712/udp | hysteria |

nginx on **443**; **no** VLESS on 443. CDN page: `assets/cdn-fallback/index.html`

## Phases (summary)

| Phase | Action | Reference |
|-------|--------|-----------|
| 1 | apt, UFW | SKILL + `optimization.md` |
| 2 | Install 3X-UI | `install-fallback.md` if blocked |
| 3 | TLS both domains | `panel-security.md` |
| 4 | nginx 443 | `nginx-fallback.md`, `cert-renewal-nginx.md` |
| 5 | Inbounds 8443/8444/2053 | `inbounds.md` |
| 6 | Clients + sub paths | `subEncrypt=false` |
| 7 | Test sub 200 (3 profiles) | `diagnostics.md` |
| 8 | Hysteria + JSON 200 | `gotchas.md`, `fix-hysteria-stream.py` |
| 9 | Happ routing | `happ-routing.md`, `apply-routing.py` |
| 10 | verify + handoff | `verify-server.sh`, `post-setup-handoff.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/verify-server.sh` | End-to-end health check |
| `scripts/apply-routing.py` | Push routing via API |
| `scripts/fix-hysteria-stream.py` | Repair Hysteria stream in DB |

Env vars: see `.env.example`

## Routing templates

| File | Use |
|------|-----|
| `templates/happ-routing-profile-ru.json` | .ru direct (default RU users) |
| `templates/happ-routing-profile.json` | .ru + basic direct |
| `templates/happ-routing-global.json` | Full tunnel |
| `templates/hysteria-stream-settings.json` | Hysteria stream |

## API pattern

```bash
R='--resolve panel.<domain>:<port>:127.0.0.1'
BASE="https://panel.<domain>:<port>/<webBasePath>"
TOKEN='<from-user>'
curl -sk $R -H "Authorization: Bearer $TOKEN" -X POST "$BASE/panel/api/setting/all" -d '{}'
```

## Verification pass criteria

- `xray -test` → Configuration OK
- Sub + JSON → HTTP 200
- 4 profiles in body
- `Routing-Enable: true` if routing enabled
- Ports 8443, 8444, 2053, 2096, 36712/udp

## Optional later

- `references/slave-node.md` — RU second VPS
- `references/warp-optional.md` — Cloudflare egress
- `references/backup-update.md` — panel upgrades
- `references/clients.md` — Happ, router, Android

## Reference index

| File | Content |
|------|---------|
| `references/execution-order.md` | **Phase order** |
| `references/inbounds.md` | **Inbound field recipes** |
| `references/gotchas.md` | Hysteria, JSON 500 |
| `references/happ-routing.md` | Subscription routing |
| `references/nginx-fallback.md` | Port 443 |
| `references/diagnostics.md` | Troubleshooting |
| `references/panel-security.md` | Hardening |
| `references/post-setup-handoff.md` | User deliverable |
| `references/reality-sni.md` | SNI validation |
| `references/install-fallback.md` | Blocked install.sh |
| `references/cert-renewal-nginx.md` | LE → nginx sync |
| `references/backup-update.md` | Updates |
| `references/clients.md` | Client apps |
| `references/slave-node.md` | Second VPS |
| `references/warp-optional.md` | WARP |
| `references/optimization.md` | BBR, swap |
| `references/agent-install.md` | Per-agent install |

## What NOT to do

- VLESS on 443 with nginx
- `network: hysteria2` in stream
- VPN domain as Reality SNI
- Patch binaries
- Commit secrets