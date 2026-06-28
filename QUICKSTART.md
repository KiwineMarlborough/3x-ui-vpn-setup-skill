# Quickstart (5 minutes)

For you or a friend setting up a personal VPN with any AI agent.

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
| DNS | A records → VPS IP |
| Reality SNI | `pixelforge.pics` (borrowed legit site) |

Copy `.env.example` → `.env.local` (never commit).

## 3. Prompt your agent

```text
Use skill 3x-ui-vpn-setup. Follow references/execution-order.md.

SSH: deploy@203.0.113.10, key ~/.ssh/vps_ed25519
Domains: panel.vpn.example.com, cdn.vpn.example.com
Country label: DE
Reality SNI: pixelforge.pics
Happ routing: SplitRU (.ru direct)
nginx CDN fallback: yes

Execute all phases yourself over SSH. Run scripts/verify-server.sh at the end.
Deliver post-setup handoff from references/post-setup-handoff.md.
```

Agent must have **shell/SSH** tools enabled.

## 4. On phone (Happ Plus)

1. Import subscription URL from handoff
2. Pull to refresh
3. Connect **Reality** profile first

## 5. If something breaks

| Symptom | Doc |
|---------|-----|
| JSON sub 500 | `references/gotchas.md` + `scripts/fix-hysteria-stream.py` |
| Sub 404 | Full `sub_id`, custom paths |
| Xray won't start | Hysteria `version != 2` |
| install.sh fails | `references/install-fallback.md` |

## 6. Repo layout

See [README.md](README.md) for full structure.