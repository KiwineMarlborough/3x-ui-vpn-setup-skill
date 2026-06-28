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
  version: "1.2.1"
---

# 3X-UI Personal VPN — Full Server Setup

End-to-end workflow for an AI agent with **SSH access to a clean Linux VPS** (Ubuntu 22.04/24.04).
**Follow `references/execution-order.md` strictly.**

Broken server? → `references/repair-only.md` first (do not reinstall).

## Start here

1. Run **intake questionnaire** (below)
2. Read `references/execution-order.md` or `references/repair-only.md`
3. Load secrets from `.env.local` (`.env.example`) — `references/secrets-management.md`
4. Execute phases over SSH — never instructions-only
5. Run `scripts/verify-server.sh` (set `SUB_ID`, optional `REQUIRE_HYSTERIA=1`)
6. Deliver `references/post-setup-handoff.md` to user

## Intake questionnaire (Phase 0)

Ask user or read `.env.local`:

| # | Question | Required |
|---|----------|----------|
| 1 | SSH host, user, key path | yes |
| 2 | Fresh install or repair? | yes |
| 3 | Panel + CDN domains | recommended |
| 4 | DNS provider — Cloudflare proxy off? | yes if CF |
| 5 | Country label (`DE`, `NL`) | yes |
| 6 | Reality SNI (borrowed site) | yes |
| 7 | Happ routing template (`profile-ru` / `banks-ru` / `global`) | default `profile-ru` |
| 8 | nginx CDN fallback on 443? | default yes |
| 9 | Second user for router? | optional |
| 10 | RU Slave VPS later? | optional note only |

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
6. Never commit secrets — `references/secrets-management.md`

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
| 0 | Intake + `.env.local` | this file |
| 1 | apt, UFW | `optimization.md` |
| 2 | Install 3X-UI | `install-fallback.md` if blocked |
| 3 | DNS A records | `dns-setup.md` |
| 4 | TLS both domains | `panel-security.md` |
| 5 | nginx 443 | `deploy-nginx-fallback.sh`, `nginx-fallback.md` |
| 6 | Inbounds 8443/8444/2053 | `inbounds.md` |
| 7 | Clients + sub paths | `set-sub-paths.py`, `panel-settings.md` |
| 8 | Test sub 200 (3 profiles) | `diagnostics.md` |
| 9 | Hysteria + JSON 200 | `gotchas.md`, `fix-hysteria-stream.py` |
| 10 | Happ routing | `apply-routing.py`, `happ-routing.md` |
| 11 | verify + handoff | `verify-server.sh`, `post-setup-handoff.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/audit-server.sh` | Read-only diagnostics |
| `scripts/verify-server.sh` | End-to-end health check |
| `scripts/deploy-nginx-fallback.sh` | nginx CDN vhost + landing |
| `scripts/deploy-cert-hook.sh` | LE renewal → nginx sync |
| `scripts/set-sub-paths.py` | Custom sub paths + subEncrypt=false |
| `scripts/apply-routing.py` | Push routing via API |
| `scripts/fix-hysteria-stream.py` | Repair Hysteria stream in DB |
| `scripts/fix-podkop-flow.py` | Empty flow for Podkop TCP |

Env vars: see `.env.example`

## Routing templates

| File | Use |
|------|-----|
| `templates/happ-routing-profile-ru.json` | .ru direct (default RU users) |
| `templates/happ-routing-banks-ru.json` | Banks + gosuslugi direct |
| `templates/happ-routing-corporate.json` | .ru + LAN + corp domains |
| `templates/happ-routing-profile.json` | Basic split |
| `templates/happ-routing-global.json` | Full tunnel |
| `templates/hysteria-stream-settings.json` | Hysteria stream |
| `templates/nginx-cdn.conf` | nginx vhost template |

## API pattern

```bash
R='--resolve panel.<domain>:<port>:127.0.0.1'
BASE="https://panel.<domain>:<port>/<webBasePath>"
TOKEN='<from-user>'
curl -sk $R -H "Authorization: Bearer $TOKEN" -X POST "$BASE/panel/api/setting/all" -d '{}'
```

Full reference: `references/api-reference.md`

## Verification pass criteria

- `xray -test` → Configuration OK
- Sub + JSON → HTTP 200
- ≥3 `vless://` + ≥1 `hysteria2://` in sub body
- `Routing-Enable: true` if routing enabled
- Ports 8443, 8444, 2053, 2096, 36712/udp

## Optional later

- `references/slave-node.md` — RU second VPS
- `references/warp-optional.md` — Cloudflare egress
- `references/backup-update.md` — panel upgrades
- `references/migration.md` — move to new VPS
- `references/monitoring.md` — backup cron
- `references/clients.md` — Happ, router, Android
- `references/protocol-selection.md` — which profile when
- `references/multi-user.md` — router user

## Reference index

| File | Content |
|------|---------|
| `references/execution-order.md` | **Phase order** |
| `references/repair-only.md` | **Fix existing server** |
| `references/panel-settings.md` | **Settings keys** |
| `references/api-reference.md` | **API endpoints** |
| `references/secrets-management.md` | **No leaks** |
| `references/inbounds.md` | **Inbound field recipes** |
| `references/gotchas.md` | Hysteria, JSON 500 |
| `references/happ-routing.md` | Subscription routing |
| `references/nginx-fallback.md` | Port 443 |
| `references/diagnostics.md` | Troubleshooting |
| `references/dns-setup.md` | Cloudflare / A records |
| `references/panel-security.md` | Hardening |
| `references/post-setup-handoff.md` | User deliverable |
| `references/reality-sni.md` | SNI validation |
| `references/protocol-selection.md` | Profile choice |
| `references/multi-user.md` | Router/guest users |
| `references/rkn-and-blocking.md` | Blocking context |
| `references/install-fallback.md` | Blocked install.sh |
| `references/cert-renewal-nginx.md` | LE → nginx sync |
| `references/backup-update.md` | Updates |
| `references/migration.md` | VPS migration |
| `references/monitoring.md` | Backup / healthcheck |
| `references/compatibility.md` | Version matrix |
| `references/vps-providers.md` | Provider notes |
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
- Route bare VPS IP in Podkop for panel admin