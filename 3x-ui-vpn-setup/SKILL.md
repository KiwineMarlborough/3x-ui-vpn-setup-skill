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
---

# 3X-UI Personal VPN — Full Server Setup

End-to-end workflow for an AI agent with **SSH access to a clean Linux VPS** (Ubuntu 22.04/24.04).
Target: personal tunnel (not commercial VPN resale). **Reality is the primary stealth protocol** — not plain TLS on 443.

Compatible agents: Claude Code, OpenAI Codex, Qwen Code, OpenCode, Grok Build, Google Antigravity (Agent Skills open standard).

## Prerequisites from user

Collect before running commands:

| Input | Example | Required |
|-------|---------|----------|
| SSH host | `203.0.113.10` | yes |
| SSH user | `root` or `deploy` | yes |
| SSH key or password | ed25519 key path | yes |
| Panel domain | `panel.vpn.example.com` | recommended |
| VPN/CDN domain | `cdn.vpn.example.com` | recommended |
| Country label | `DE`, `NL`, `FI` | yes (for profile names) |
| Reality SNI (borrowed) | `pixelforge.pics` | yes — legit external site |
| Happ split .ru direct? | yes/no | default yes |
| nginx fake site on 443? | yes/no | default yes |

**Never** hardcode user domains, passwords, tokens, or UUIDs in git or chat logs.

## Hard rules

1. Do **not** patch `/usr/local/x-ui/x-ui`, Xray binaries, or 3X-UI source.
2. Configure via **panel UI**, **3X-UI REST API**, **SQLite** (`/etc/x-ui/x-ui.db`), **UFW**, **nginx**, **certbot**.
3. Execute commands yourself over SSH — do not only tell the user what to run.
4. Confirm SSH still works after `ufw`, `sshd`, or firewall changes.
5. Run verification checklist before claiming success.
6. Tag multi-server steps `[MASTER]` / `[SLAVE]`.

## Target architecture

```
panel.<domain>:29800/<webBasePath>  → 3X-UI admin (LE cert, webDomain lock)
cdn.<domain>                        → VPN endpoints + subscription :2096
```

### Four production inbounds (create all)

| # | Name pattern | Protocol | Port | Purpose |
|---|--------------|----------|------|---------|
| 1 | `{CC}-Reality-Vision` | VLESS Reality | **8443** | **Primary** — `flow=xtls-rprx-vision` |
| 2 | `{CC}-TCP-Podkop` | VLESS TLS TCP | **8444** | Routers / Podkop — **empty flow** |
| 3 | `{CC}-XHTTP-Mobile` | VLESS XHTTP | **2053** | Mobile DPI bypass |
| 4 | `{CC}-Hysteria2` | hysteria | **36712/udp** | UDP profile — `auth` field |

**Do not** put VLESS on port **443** if nginx CDN fallback occupies 443.

`shareAddr` on every inbound: VPN domain (`cdn.<domain>`), strategy `custom`.

### Reality setup (inbound #1)

- `security`: reality
- `serverName` / SNI: **borrowed** legitimate site (user picks or suggest `pixelforge.pics`)
- `dest`: `<sni>:443`
- `fingerprint`: `firefox` or `chrome`
- Generate keypair in panel; set `shortIds`, `publicKey`
- Client `flow`: `xtls-rprx-vision` via `client_inbounds` override

Reality SNI is **not** your VPN domain — it camouflages TLS. Traffic still hits your VPS IP.

## Phase 1 — Baseline server `[MASTER]`

```bash
sudo apt update && sudo apt upgrade -y
sudo ufw enable
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

After creating inbounds, also allow: `29800 2096 8443 8444 2053 10443/tcp` and `36712/udp`.

Prefer SSH keys; disable password auth only after key login verified.

## Phase 2 — Install 3X-UI

```bash
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh)
```

Immediately:
- Change default panel password
- Record `webBasePath` (required in URL)
- Create API token (Panel → API Tokens)
- Note panel port (default 2053 install may differ — often 29800 after hardening)

## Phase 3 — DNS and TLS

1. User creates **A records** for `panel.*` and `cdn.*` → VPS IP.
2. Verify: `dig +short panel.<domain>` returns VPS IP.
3. Issue Let's Encrypt in panel for **both** domains (or certbot).
4. Set `webDomain` = panel domain; `webCertFile` / `webKeyFile` = panel cert paths.
5. Subscription cert on CDN domain.

**Panel TLS mismatch** (cdn cert on panel domain) → browser handshake error.

## Phase 4 — Clients

| User | email pattern | Notes |
|------|---------------|-------|
| Phone | `user-phone@<project>` | All 4 inbounds |
| Router (optional) | `user-router@<project>` | TCP 8444 + Reality 8443 only |

- `limitIp: 0` — phone + router on same user OK
- Separate users — cleaner revoke and stats
- `subEncrypt = false` for plain vless/hysteria2 lines in Happ

## Phase 5 — Custom subscription paths

Replace default `/sub/` and `/json/` (security warning in panel):

1. `POST /panel/api/setting/all` → get full settings
2. Set random paths, e.g. `/xK9mP2qR/` and `/j4nR8wLz3/`
3. `subJsonEnable = true`
4. `POST /panel/api/setting/update` with **full** object (strip `has*` keys)
5. Restart `x-ui`

404 on sub → truncated `sub_id` (must be full 36-char UUID).

## Phase 6 — Happ routing in subscription

Enable split tunnel + encrypted DNS for Happ Plus clients.

1. `subEnableRouting = true`
2. Build profile from `templates/happ-routing-profile.json` (customize `Name`, `DirectSites`)
3. Encode:

```text
happ://routing/onadd/<base64-json>
```

4. Set as `subRoutingRules` via API; restart `x-ui`
5. Verify headers on sub URL: `Routing-Enable: true`

Default profile: `.ru` / `.рф` / `geosite:category-ru` → direct; rest → VPN. Both DNS channels use **DoH**.

Details: `references/happ-routing.md`

## Phase 7 — nginx CDN fallback (recommended)

Serve fake static site on **443**; keep Reality on **8443**.

- Install nginx, vhost for `cdn.<domain>`
- Copy LE cert to nginx ssl dir; sync on renewal
- **Keep inbound on 443 disabled**

Details: `references/nginx-fallback.md`

## Phase 8 — Hysteria2 (critical)

Before enabling inbound #4, read `references/gotchas.md`.

Minimum stream shape — use `templates/hysteria-stream-settings.json`:
- `network`: `hysteria` (never `hysteria2` in stream for Xray 26.x)
- Both `hysteriaSettings` and `hysteria2Settings` with `"version": 2`
- Client field: `auth` (not `password`)

## API pattern (on server)

```bash
R='--resolve panel.<domain>:<panel-port>:127.0.0.1'
BASE="https://panel.<domain>:<panel-port>/<webBasePath>"
TOKEN='<from-user>'

curl -sk $R -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "$BASE/panel/api/setting/all" -d '{}'
```

## Verification (mandatory)

```bash
sudo x-ui status
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
curl -sk -o /dev/null -w 'sub %{http_code}\n' \
  "https://cdn.<domain>:2096/<subPath>/<sub_id>"
curl -sk -o /dev/null -w 'json %{http_code}\n' \
  "https://cdn.<domain>:2096/<jsonPath>/<sub_id>"
ss -tlnp | grep -E '8443|8444|2053|2096'
ss -ulnp | grep 36712
curl -skI "https://cdn.<domain>:2096/<subPath>/<sub_id>" | grep -i routing
```

Pass criteria:
- Xray: `Configuration OK`
- Sub + JSON: HTTP 200
- 4 profiles in subscription body
- Routing header present if enabled

## What NOT to do

- Enable VLESS on 443 while nginx uses 443
- Patch 3X-UI binary
- Change `webBasePath` without updating user bookmarks
- Use VPN domain as Reality SNI
- Set `network: hysteria2` in stream settings (Xray 26.x crash)
- Commit secrets to git

## Reference files

| File | Content |
|------|---------|
| `references/gotchas.md` | Hysteria, JSON 500, Reality |
| `references/happ-routing.md` | Subscription routing + DoH |
| `references/nginx-fallback.md` | Port layout |
| `references/diagnostics.md` | Troubleshooting |
| `references/agent-install.md` | Per-agent install paths |
| `templates/happ-routing-profile.json` | Routing JSON template |
| `templates/happ-routing-profile-ru.json` | .ru direct variant |
| `templates/happ-routing-global.json` | Full tunnel variant |
| `templates/hysteria-stream-settings.json` | Hysteria stream |

## Interactive mode

Work **step by step**: run commands, show output, fix errors, re-verify. On `version != 2` or JSON 500 → go to `references/gotchas.md` immediately.