# Quickstart (5 minutes) — English

| Language | File |
|----------|------|
| **English** | **QUICKSTART.md** (this file) |
| **Русский** | [QUICKSTART.ru.md](QUICKSTART.ru.md) · [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md) |

For you or a friend setting up a personal VPN with any AI agent.

> **Tired of blocked VPN services?** Install this skill into an AI agent with SSH access — **it does the rest**. You provide the VPS IP, one domain, your own public IP, and a key-only sudo account for the agent.

## 1. Install skill

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

## 2. Prepare

| Item | Example |
|------|---------|
| Fresh Ubuntu VPS | 1 GB+ RAM |
| SSH access | `deploy@203.0.113.10` + key (see `agent-access-hygiene.md` for a time-boxed key-only sudo account) |
| **Your public IP(s)** | `198.51.100.7` — whitelisted in IPsum/Fail2Ban so you can never lock yourself out |
| CDN/VPN domain | `cdn.vpn.example.com` (the only public name; **no panel DNS record**) |
| DNS | one A record → VPS IP, **proxy off** (`dns-setup.md`) |
| Reality SNI | `pixelforge.pics` (borrowed legit site; one per Reality port) |

Copy `.env.example` → `.env.local` (never commit).

## 3. Prompt your agent

**New server:**

```text
Use skill 3x-ui-vpn-setup v1.3. Follow references/execution-order.md.

SSH: deploy@203.0.113.10, key ~/.ssh/vps_ed25519 (key-only sudo)
CDN domain: cdn.vpn.example.com   (no public panel record; panel via SSH tunnel)
ADMIN_IPS: 198.51.100.7
Country label: DE
Reality SNI: pixelforge.pics
Happ routing: SplitRU (happ-routing-profile-ru.json)
nginx CDN fallback: yes
Optional AmneziaWG 3.1: no   (or: yes, port 56100, clients router,phone)

Execute all phases yourself over SSH. Deploy IPsum + Fail2Ban (rollback armed, then confirm).
Make the certificate renew itself (deploy-acme-renewal.sh: STAGING_TEST then APPLY).
Finish with scripts/loopback-test.py and scripts/verify-server.sh (SUB_ID set).
Deliver the post-setup handoff. Follow secrets-management.md.
```

**Broken server:**

```text
Use skill 3x-ui-vpn-setup. Follow references/repair-only.md.
Symptom: <one line>.
Run audit-server.sh, check-cert-expiry.sh and loopback-test.py first. Do not reinstall.
Do not revert server changes before proving the server side (testing-methods.md).
```

**Update the panel:**

```text
Use skill 3x-ui-vpn-setup, references/backup-update.md: back up DB + binaries, read the release notes
("Before you upgrade"), update 3X-UI + Xray together, then loopback-test.py and verify-server.sh.
```

Agent must have **shell/SSH** tools enabled.

## 4. Open the admin panel (it is closed to the internet)

1. Add `127.0.0.1 <panel-hostname>` to your hosts file.
2. `ssh -i <key> -L 29800:127.0.0.1:29800 <user>@<vps-ip>` (keep it open).
3. Browse `https://<panel-hostname>:29800/<webBasePath>/` and accept the self-signed certificate.
   (`localhost` returns 403 — that is correct.) Details: `references/panel-tunnel-access.md`.

## 5. On phone (Happ Plus)

1. Import subscription URL from the handoff
2. Pull to refresh
3. Connect **Reality** first. If a profile shows `n/a`, test real traffic; the indicator is unreliable (`testing-methods.md`).
   AmneziaWG is **not** in the subscription: use the AmneziaVPN/AmneziaWG apps with the `.conf`/QR.

## 6. If something breaks

| Symptom | Doc / script |
|---------|--------------|
| Reality works, TCP/XHTTP/Hysteria/sub dead | **expired certificate** → `check-cert-expiry.sh`, `cert-renewal-nginx.md` |
| Profile "n/a" in a client | `loopback-test.py` → another client → another network (`testing-methods.md`) |
| Lost access from one network only | IPsum false positive → whitelist (`blocklist-ipsum-fail2ban.md`) |
| JSON sub 500 | `gotchas.md` + `fix-hysteria-stream.py` |
| Sub 404 | `panel-settings.md` + `set-sub-paths.py` |
| Sub links show wrong `security`/`sni` | stale `hosts` row (`gotchas.md`) |
| Podkop won't connect | `fix-podkop-flow.py` / check effective flow (`inbounds.md`) |
| Xray won't start | Hysteria `version != 2` |
| install.sh fails | `install-fallback.md` |
| Any diagnosis | `audit-server.sh` |

## 7. Repo layout

See [README.md](README.md) for the full structure.
