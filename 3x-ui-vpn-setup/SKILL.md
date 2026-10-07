---
name: 3x-ui-vpn-setup
description: >
  Autonomous setup, hardening and repair of a personal 3X-UI VPN on a Linux VPS via SSH: VLESS Reality
  (primary), XHTTP, TCP Podkop, Hysteria2, optional native AmneziaWG 3.1 inbound, Happ routing in the
  subscription (DoH), custom sub paths, nginx CDN fallback, UFW, panel reachable only through an SSH tunnel,
  self-renewing Let's Encrypt (acme.sh webroot) with expiry monitoring, IPsum blocklist (nftables) + Fail2Ban,
  real-handshake testing. Use for new server setup, 3X-UI/Xray updates, fixes, expired certificates,
  subscription 404/500, Hysteria version errors, client "n/a". Triggers: 3x-ui, xray, reality, hysteria2,
  amneziawg, happ routing, ipsum, /3x-ui-vpn-setup. Never patch binaries — panel, API, SQLite, UFW, nginx only.
license: MIT
compatibility: claude-code, codex, qwen-code, opencode, grok-build, antigravity
metadata:
  author: KiwineMarlborough
  standard: agentskills.io
  version: "1.3.0"
---

# 3X-UI Personal VPN — Setup, Hardening, Repair

End-to-end workflow for an AI agent with **SSH access to a Linux VPS** (verified on Ubuntu 26.04; written for 22.04/24.04).
**Fresh server: follow `references/execution-order.md` strictly. Existing server that "broke": `references/repair-only.md` first (do not reinstall).**

## Start here

1. Run the **intake questionnaire** (below)
2. Read `references/execution-order.md` or `references/repair-only.md`
3. Load secrets from `.env.local` (`.env.example`) — `references/secrets-management.md`
4. Execute phases over SSH — never instructions-only
5. Run `scripts/loopback-test.py` and `scripts/verify-server.sh` (set `SUB_ID`, optional `REQUIRE_HYSTERIA=1`)
6. Deliver `references/post-setup-handoff.md` to the user
7. Update your own session notes/handoff with versions, accounts, backups (see "Leave a handoff")

## Intake questionnaire (Phase 0)

| # | Question | Required |
|---|----------|----------|
| 1 | SSH host, user, key path | yes |
| 2 | Fresh install or repair? | yes |
| 3 | **CDN domain** (one name; no separate panel record by default) | recommended |
| 4 | DNS provider — Cloudflare proxy **off** for the VPN name? | yes if CF |
| 5 | Country label (`DE`, `NL`) | yes |
| 6 | Reality SNI (borrowed site) — one per Reality port | yes |
| 7 | Happ routing template (`profile-ru` / `banks-ru` / `global`) | default `profile-ru` |
| 8 | nginx CDN fallback on 443? | default yes |
| 9 | **Admin public IPs to never block (`ADMIN_IPS`)** — needed for IPsum + Fail2Ban | **yes** |
| 10 | Panel access: `tunnel` (default, no public DNS/port) or `public` | default tunnel |
| 11 | Agent account policy: key-only, expiry date, who removes it | yes |
| 12 | Second user for a router? | optional |
| 13 | **AmneziaWG 3.1** (OpenWrt router / Amnezia apps)? port + clients | optional module |
| 14 | RU Slave VPS later? | optional note only |

## Hard rules

1. Do **not** patch 3X-UI / Xray binaries
2. Panel + API + SQLite + UFW + nginx + nftables only
3. Execute over SSH yourself
4. Verify SSH after every firewall/sshd/IPsum change (open a **second** session before closing the first)
5. Hysteria **last** (after sub 200 with 3 profiles)
6. Never commit secrets — `references/secrets-management.md`
7. **IPsum and Fail2Ban are part of the default setup; never deploy them without `ADMIN_IPS` and the rollback timer**
8. **The certificate must renew itself** (acme.sh webroot via `deploy-acme-renewal.sh`) and be monitored — never leave 3X-UI's standalone mode next to nginx on :80
9. **Prove, don't assume:** after any inbound/cert/panel change run `loopback-test.py`; a client's `n/a` is not evidence (`testing-methods.md`)
10. After changing an inbound's security/SNI/port, sync its `hosts` row (subscription links come from it)
11. Back up before changes (DB **and** binaries); use `sudo env VAR=… bash` (Ubuntu 26.04 sudo-rs ignores `sudo -E`)
12. Never `pkill -f <text>` inside an SSH command; kill by PID
13. Revert only what you changed and proved wrong — test from another client/network before reverting server config

## Architecture

```
cdn.<domain>   → nginx 80/443 (decoy + ACME) · VPN ports · subscription :2096     (the only public name)
panel          → NOT public: no DNS record, UFW deny, SSH tunnel + hosts entry (references/panel-tunnel-access.md)
```

| Profile | Port | Protocol |
|---------|------|----------|
| `{CC}-Reality-Vision` | 8443 | VLESS Reality (primary) |
| `{CC}-TCP-Podkop` | 8444 | VLESS TLS (certificate required!) |
| `{CC}-XHTTP-Mobile` | 2053 | VLESS XHTTP + TLS |
| `{CC}-Hysteria2` | 36712/udp | hysteria |
| `{CC}-AWG-3.1` *(optional)* | own UDP port | AmneziaWG 3.1 — not in the subscription |

nginx on **443**; **no** VLESS on 443. CDN page: `assets/cdn-fallback/index.html`. Details: `references/inbounds.md`.

## Phases (summary — full list in `execution-order.md`)

| Phase | Action | Reference / script |
|-------|--------|--------------------|
| 0 | Intake + `.env.local` | this file |
| 1 | apt, UFW | `optimization.md`, `backup-update.md` |
| 1b | **Fail2Ban + IPsum** | `setup-fail2ban.sh`, `deploy-ipsum.sh`, `blocklist-ipsum-fail2ban.md` |
| 2 | Install 3X-UI | `install-fallback.md` if blocked |
| 3 | Panel harden, panel port closed | `panel-security.md`, `panel-tunnel-access.md` |
| 4 | DNS (CDN record only) | `dns-setup.md` |
| 5–6b | Certificate → nginx → **webroot renewal** | `deploy-nginx-fallback.sh`, `deploy-acme-renewal.sh`, `cert-renewal-nginx.md` |
| 7 | Panel self-signed cert | `cert-renewal-nginx.md` |
| 8–10 | Inbounds 8443 / 8444 / 2053 | `inbounds.md` |
| 11–13 | Clients, sub paths, sub 200 | `set-sub-paths.py`, `panel-settings.md` |
| 14–15 | Hysteria + JSON 200 | `gotchas.md`, `fix-hysteria-stream.py` |
| 16–17 | `hosts` sync, Happ routing | `apply-routing.py`, `happ-routing.md` |
| 18 | Optional AmneziaWG | `awg-tool.py`, `amneziawg.md` |
| 19–21 | UFW final, **loopback test**, verify | `loopback-test.py`, `verify-server.sh` |
| 22 | Handoff + account cleanup | `post-setup-handoff.md`, `agent-access-hygiene.md` |

## Scripts

| Script | Purpose | Risk |
|--------|---------|------|
| `scripts/audit-server.sh` | Read-only diagnostics: certs, accounts/sudo leftovers, UFW, hardening, `hosts` mismatches, nginx | none |
| `scripts/verify-server.sh` | End-to-end health check (certs served, IPsum, fail2ban, panel closed, subscription, handshakes) | none |
| `scripts/loopback-test.py` | Real VLESS handshake per inbound, on the server | none |
| `scripts/check-cert-expiry.sh` | Certificate expiry + stale-copy check (cron-able) | none |
| `scripts/deploy-acme-renewal.sh` | acme.sh webroot renewal + deploy hook (`STAGING_TEST=1` safe) | low–medium |
| `scripts/deploy-ipsum.sh` (+ `ipsum-update.sh`) | IPsum nftables blocklist with whitelist + auto-rollback | medium |
| `scripts/setup-fail2ban.sh` | sshd jail with admin `ignoreip` | low |
| `scripts/awg-tool.py` | AmneziaWG create / rotate / render `.conf` | medium |
| `scripts/deploy-nginx-fallback.sh` | nginx CDN vhost + landing (symlinked) | low |
| `scripts/set-sub-paths.py` | Custom sub paths + subEncrypt=false | medium |
| `scripts/apply-routing.py` | Push routing via API | medium |
| `scripts/fix-hysteria-stream.py` | Repair Hysteria stream in DB | medium |
| `scripts/fix-podkop-flow.py` | Empty flow for Podkop TCP | low |
| `scripts/deploy-cert-hook.sh` | **legacy** certbot-only hook | low |

Env vars: see `.env.example`. Ubuntu 26.04: pass variables with `sudo env "VAR=value" bash script.sh`.

## Routing templates

| File | Use |
|------|-----|
| `templates/happ-routing-profile-ru.json` | .ru direct (default RU users) |
| `templates/happ-routing-banks-ru.json` | Banks + gosuslugi direct |
| `templates/happ-routing-corporate.json` | .ru + LAN + corp domains |
| `templates/happ-routing-profile.json` | Basic split |
| `templates/happ-routing-global.json` | Full tunnel |
| `templates/hysteria-stream-settings.json` | Hysteria stream |
| `templates/nginx-cdn.conf` | nginx vhost (ACME location on :80, `server_tokens off`) |

## API pattern (3X-UI 3.9)

```bash
R='--resolve <panel-host>:<port>:127.0.0.1'
BASE="https://<panel-host>:<port>/<webBasePath>"
TOKEN='<from-user>'
curl -sk $R -H "Authorization: Bearer $TOKEN" "$BASE/panel/api/inbounds/list"                  # reads: GET
curl -sk $R -H "Authorization: Bearer $TOKEN" -X POST "$BASE/panel/api/setting/all" -d '{}'    # writes/most settings: POST
curl -sk $R -H "Authorization: Bearer $TOKEN" "$BASE/panel/api/openapi.json"                   # the panel documents its routes
```
Full reference and the 3.9 behaviour changes: `references/api-reference.md`.

## Verification pass criteria

- `xray -test` → Configuration OK
- `loopback-test.py` → every tested inbound HTTP 200
- Certificates (files **and** served) > 30 days; renewal mode webroot; `check-cert-expiry.sh` clean
- Sub + JSON → HTTP 200; ≥3 `vless://` + ≥1 `hysteria2://`; `Routing-Enable: true` if routing enabled
- Ports 8443, 8444, 2053, 2096, 36712/udp (+ AWG udp port if installed)
- IPsum table loaded, rollback timer **not** armed; fail2ban sshd jail active
- Panel port not open in UFW (tunnel mode); `hosts` consistent with inbounds
- Only the intended accounts/keys/sudo rules exist (`audit-server.sh`)

## Leave a handoff

Write down for the owner and the next agent (not in the public repo): versions (panel/Xray/OS), accounts + expiries, ports,
backup locations, certificate renewal date, whitelisted IPs, what is verified vs. unverified, open decisions.

## Optional later

`slave-node.md` · `warp-optional.md` · `migration.md` · `clients.md` · `protocol-selection.md` · `multi-user.md` · `amneziawg.md`

## Reference index

| File | Content |
|------|---------|
| `references/execution-order.md` | **Phase order** |
| `references/repair-only.md` | **Fix existing server (decision tree)** |
| `references/cert-renewal-nginx.md` | **Certificate lifecycle, renewal, monitoring** |
| `references/blocklist-ipsum-fail2ban.md` | **IPsum + Fail2Ban** |
| `references/panel-tunnel-access.md` | **Panel without public exposure** |
| `references/testing-methods.md` | **What proves a profile works** |
| `references/agent-access-hygiene.md` | **Agent account, leftovers audit** |
| `references/amneziawg.md` | **Optional AmneziaWG 3.1** |
| `references/api-reference.md` | **API (3.9.0 verified)** |
| `references/gotchas.md` | Hysteria, hosts table, nginx, sudo-rs, updates |
| `references/inbounds.md` | Inbound recipes + 1.3 warnings |
| `references/panel-settings.md` | Settings keys |
| `references/secrets-management.md` | No leaks |
| `references/monitoring.md` | Health checks, cron, backups |
| `references/backup-update.md` | Backups, panel/system updates, rollback |
| `references/compatibility.md` | Verified version matrix |
| `references/dns-setup.md` | DNS / Cloudflare (what breaks with the orange cloud) |
| `references/nginx-fallback.md` | Port 443 decoy + ACME |
| `references/panel-security.md` | Hardening |
| `references/rkn-and-blocking.md` | How servers get found / blocking context |
| `references/happ-routing.md` | Subscription routing |
| `references/diagnostics.md` | Troubleshooting |
| `references/post-setup-handoff.md` | User deliverable |
| `references/reality-sni.md` | SNI validation |
| `references/protocol-selection.md` | Profile choice |
| `references/multi-user.md` | Router/guest users |
| `references/install-fallback.md` | Blocked install.sh |
| `references/migration.md` | VPS migration |
| `references/clients.md` | Client apps |
| `references/vps-providers.md` | Provider notes |
| `references/slave-node.md` | Second VPS |
| `references/warp-optional.md` | WARP |
| `references/optimization.md` | BBR, swap |
| `references/agent-install.md` | Per-agent install |

## What NOT to do

- VLESS on 443 with nginx
- `network: hysteria2` in stream
- VPN domain as Reality SNI; one SNI/dest shared by several Reality ports
- XHTTP + Reality without a passing loopback test on your core version
- Orange-cloud (Cloudflare proxy) on the shared VPN hostname
- A public DNS record / public certificate for the panel hostname (tunnel mode)
- Leave acme.sh in standalone mode while nginx owns :80; trust "renewal is configured" without `STAGING_TEST`
- Deploy IPsum/Fail2Ban without `ADMIN_IPS`, or leave the rollback timer armed
- Edit `sites-available` when `sites-enabled` is a copy; keep backups in `sites-enabled`
- Change an inbound's security/SNI and forget its `hosts` row
- Edit settings in SQLite and expect them live without restarting `x-ui`
- `sudo -E` on Ubuntu 26.04; `pkill -f` over SSH
- Revert server changes because one client shows `n/a`
- Patch binaries · commit secrets · route the bare VPS IP in Podkop for panel admin
