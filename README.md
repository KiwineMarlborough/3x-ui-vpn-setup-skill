# 3x-ui-vpn-setup — Universal Agent Skill v1.2

Open-source [Agent Skill](https://agentskills.io/) for AI agents to **autonomously set up a personal 3X-UI VPN** on a fresh Linux VPS via SSH.

**Stack:** VLESS **Reality** + XHTTP + TCP Podkop + Hysteria2 + Happ routing (DoH) + nginx CDN fallback.

📄 **[QUICKSTART.md](QUICKSTART.md)** — 5-minute guide  
📄 **[CHANGELOG.md](CHANGELOG.md)** — version history

## Install

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

Copy [`.env.example`](.env.example) → `.env.local` (gitignored).

## Supported agents

Claude Code · OpenAI Codex · Qwen Code · OpenCode · Grok Build · Google Antigravity

Details: [`references/agent-install.md`](3x-ui-vpn-setup/references/agent-install.md)

## What's in v1.2

| Category | New in 1.2 |
|----------|------------|
| **Core docs** | `panel-settings`, `api-reference`, `repair-only`, `secrets-management` |
| **Ops** | `dns-setup`, `migration`, `monitoring`, `protocol-selection`, `multi-user` |
| **Context** | `rkn-and-blocking`, `compatibility`, `vps-providers` |
| **Deploy** | `nginx-cdn.conf`, `deploy-nginx-fallback.sh`, `deploy-cert-hook.sh` |
| **Scripts** | `audit-server.sh`, `set-sub-paths.py`, `fix-podkop-flow.py` |
| **Routing** | `happ-routing-banks-ru.json`, `happ-routing-corporate.json`, DoH/DoT/DoU docs |

v1.1: `inbounds.md`, `execution-order.md`, `verify-server.sh`, 15+ references.

## Structure

```
3x-ui-vpn-setup/
├── SKILL.md
├── scripts/             # 8 automation scripts
├── templates/           # routing, hysteria, nginx
├── references/          # 25 guides
└── assets/cdn-fallback/
```

## Principles

- Never patch 3X-UI / Xray binaries
- Reality primary — not plain TLS on 443
- Fresh install → `execution-order.md`; repair → `repair-only.md`
- No secrets in repo

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) — PRs welcome.

## License

MIT — [LICENSE](LICENSE)

**Repo:** https://github.com/KiwineMarlborough/3x-ui-vpn-setup-skill