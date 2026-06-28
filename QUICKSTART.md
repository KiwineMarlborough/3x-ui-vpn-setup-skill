# Quickstart (5 minutes)

🇷🇺 Русская инструкция: [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md) · [README.ru.md](README.ru.md)

For you or a friend setting up a personal VPN with any AI agent.

> Give the skill to your AI agent with SSH access — it does the rest. You only provide IP, domains, and temporary sudo (≤ 30 days) or SSH key.

## 1. Install skill

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

## 2. Prepare

| Item | Example |
|------|---------|
| Fresh Ubuntu VPS | 1 GB+ RAM |
| SSH access | `deploy@203.0.113.10` + key |
| Panel domain | `panel.vpn.example.com` |
| CDN domain | `cdn.vpn.example.com` |
| DNS | A records → VPS IP, **proxy off** (`dns-setup.md`) |
| Reality SNI | `pixelforge.pics` (borrowed legit site) |

Copy `.env.example` → `.env.local` (never commit).

## 3. Prompt your agent

**New server:**

```text
Use skill 3x-ui-vpn-setup v1.2. Follow references/execution-order.md.

SSH: deploy@203.0.113.10, key ~/.ssh/vps_ed25519
Domains: panel.vpn.example.com, cdn.vpn.example.com
Country label: DE
Reality SNI: pixelforge.pics
Happ routing: SplitRU (happ-routing-profile-ru.json)
nginx CDN fallback: yes

Execute all phases yourself over SSH.
Run scripts/verify-server.sh with SUB_ID at the end.
Deliver post-setup handoff. Follow secrets-management.md.
```

**Broken server:**

```text
Use skill 3x-ui-vpn-setup. Follow references/repair-only.md.
Symptom: JSON subscription returns HTTP 500.
Run audit-server.sh first. Do not reinstall.
```

Agent must have **shell/SSH** tools enabled.

## 4. On phone (Happ Plus)

1. Import subscription URL from handoff
2. Pull to refresh
3. Connect **Reality** profile first

## 5. If something breaks

| Symptom | Doc / script |
|---------|--------------|
| JSON sub 500 | `gotchas.md` + `fix-hysteria-stream.py` |
| Sub 404 | `panel-settings.md` + `set-sub-paths.py` |
| Podkop won't connect | `fix-podkop-flow.py` |
| Xray won't start | Hysteria `version != 2` |
| install.sh fails | `install-fallback.md` |
| Any diagnosis | `audit-server.sh` |

## 6. Repo layout

See [README.md](README.md) for full structure.