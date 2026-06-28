---
name: 3x-ui-vpn-setup
description: >
  Set up and maintain a personal 3X-UI (MHSanaei) VPN server: VLESS Reality, XHTTP,
  Podkop TCP, Hysteria2, custom subscription paths, nginx CDN fallback, Happ Plus
  Meridian routing, UFW, Let's Encrypt. Use when asked to configure a new VPS,
  fix 3X-UI/Xray, subscription 404/500, Hysteria version errors, or /3x-ui-vpn-setup.
  Never patch 3X-UI binaries — panel, API, and SQLite only.
---

# 3X-UI VPN Setup Skill

Expert workflow for **personal** 3X-UI v3.x + Xray VPN servers. Works with Grok, Cursor, Claude Code, and `npx skills add`.

## Hard rules

1. **Do not patch** `/usr/local/x-ui/x-ui`, Xray binaries, or 3X-UI source.
2. Configure via **panel**, **3X-UI API**, **SQLite** (`/etc/x-ui/x-ui.db`), **UFW**, **nginx**, **certbot**.
3. **Never commit or paste** real passwords, API tokens, UUIDs, or private keys into public docs.
4. Ask the user for credentials via secure channel; use placeholders in examples.
5. After risky changes (`ufw`, `sshd`, `x-ui restart`) — verify connectivity before continuing.
6. Tag commands `[MASTER]` / `[SLAVE]` when multiple servers.

## Intake (ask first)

| Question | Why |
|----------|-----|
| Master location (DE/EU)? Slave (RU) later? | Architecture |
| Domain(s): panel vs CDN/VPN split? | TLS + SNI |
| Client: Happ Plus, router, both? | Routing + profiles |
| Protocols: Reality, XHTTP, TCP Podkop, Hysteria2? | Inbound plan |
| Nginx fallback on 443? | Port conflict |
| Custom sub paths (not `/sub/`)? | Security |

## Recommended architecture (2026 personal tunnel)

```
panel01.example.com:29800  → 3X-UI panel (LE cert, webDomain lock)
cdn01.example.com          → VPN inbounds + subscription :2096
```

**Active inbounds (example):**

| Profile | Protocol | Port | Notes |
|---------|----------|------|-------|
| DE-Reality-Vision | VLESS Reality | 8443 | `flow=xtls-rprx-vision`, borrowed SNI (e.g. legit site) |
| DE-TCP-Podkop | VLESS TLS TCP | 8444 | `flow` empty for Podkop |
| DE-XHTTP-Mobile | VLESS XHTTP | 2053 | Mobile bypass |
| DE-Hysteria2 | hysteria | 36712/udp | `auth` field, see gotchas |

**Disabled:** VLESS on **443** if nginx CDN fallback uses 443.

`shareAddr` on all inbounds: VPN domain (e.g. `cdn01.example.com`), strategy `custom`.

## Phase 1 — Server baseline

```bash
apt update && apt upgrade -y
ufw enable
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# Add VPN ports after inbounds exist — see references/diagnostics.md
```

SSH: key-based auth, optional ICMP drop. Confirm reconnect after `sshd` changes.

## Phase 2 — Install 3X-UI

```bash
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh)
```

Immediately: change panel password, note `webBasePath`, create API token.

## Phase 3 — TLS and domains

- **Panel cert** must match `webDomain` (panel01) — mismatch causes TLS handshake errors.
- **Subscription cert** on CDN domain (cdn01).
- Root panel URL without `webBasePath` → 404 by design.

## Phase 4 — Inbounds and client

- One client per device type (phone vs router) is optional but recommended.
- `limitIp: 0` allows phone + router on same user; separate users = cleaner revoke/stats.
- `subEncrypt = false` if client expects plain vless/hysteria2 lines.

## Phase 5 — Custom subscription paths

Replace default `/sub/` and `/json/` via API `setting/update` (full settings object, strip `has*` keys):

```
subPath     → /s7kM2pQx9v/   (example — generate random)
subJsonPath → /j4nR8wLz3k/
subJsonEnable = true
```

404 on subscription → check full `sub_id` (36-char UUID, not truncated).

## Phase 6 — Happ Meridian routing

Enable `subEnableRouting = true`. Push profile via `subRoutingRules` as:

```
happ://routing/onadd/<base64-json>
```

Use template: `templates/meridian-routing.json` (DoH for both Remote and Domestic).

After update: user pull-to-refreshes subscription in Happ Plus.

Details: `references/happ-routing.md`

## Phase 7 — Nginx CDN fallback (optional)

nginx on 443 serves fake CDN site; Xray Reality on 8443. **Do not enable inbound on 443** without moving nginx.

Details: `references/nginx-fallback.md`

## Critical gotchas

Read `references/gotchas.md` before touching Hysteria2 or JSON subscription.

Quick list:

- Hysteria: `network=hysteria`, `settings.version=2`, **both** `hysteriaSettings` and `hysteria2Settings` with `version: 2`
- Client field: `auth` not `password`
- Xray 26.x: `network: hysteria2` in stream → crash
- JSON sub HTTP 500 → often Hysteria stream shape
- `version != 2` in log → fix inbound #5 stream_settings
- Reality SNI = borrowed domain, not your VPN domain

## API pattern (run on server)

```bash
R='--resolve panel01.example.com:29800:127.0.0.1'
BASE='https://panel01.example.com:29800/<webBasePath>'
TOKEN='<api-token>'

curl -sk $R -H "Authorization: Bearer $TOKEN" \
  -X POST "$BASE/panel/api/setting/all" -d '{}'
```

`setting/update` requires **complete** settings object.

## Verification checklist

```bash
sudo x-ui status
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
curl -sk -o /dev/null -w '%{http_code}\n' 'https://cdn01.example.com:2096/<subPath>/<sub_id>'
curl -sk -o /dev/null -w '%{http_code}\n' 'https://cdn01.example.com:2096/<jsonPath>/<sub_id>'
ss -tlnp | grep -E '8443|8444|2053|2096'
ss -ulnp | grep 36712
```

Expect: Xray `Configuration OK`, subscription + JSON `200`, 4 profiles in sub.

Full diagnostics: `references/diagnostics.md`

## Slave node (future)

Meridian routing (client-side .ru direct) ≠ server cascade. For RU IP on .ru sites: add Slave node in panel → Nodes, outbound + routing on Master. See handoff pattern in references.

## What NOT to do

- Change `webBasePath` without updating bookmarks/scripts
- Revert to `/sub/` without reason
- Enable inbound #1 on 443 while nginx holds 443
- Route bare VPS IP in Podkop when split-routing panel only (VPN-in-VPN risk)

## Reference files

| File | Content |
|------|---------|
| `references/gotchas.md` | Hysteria, JSON sub, Reality |
| `references/happ-routing.md` | Meridian profile, DoH |
| `references/nginx-fallback.md` | Port 443 layout |
| `references/diagnostics.md` | Commands cheat sheet |
| `templates/meridian-routing.json` | Routing profile JSON |
| `templates/hysteria-stream-settings.json` | Working Hysteria stream |