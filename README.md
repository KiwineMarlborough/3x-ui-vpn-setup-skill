# 3x-ui-vpn-setup — Universal Agent Skill v1.1

Open-source [Agent Skill](https://agentskills.io/) for AI agents to **autonomously set up a personal 3X-UI VPN** on a fresh Linux VPS via SSH.

**Stack:** VLESS **Reality** + XHTTP + TCP Podkop + Hysteria2 + Happ routing (DoH) + nginx CDN fallback.

📄 **[QUICKSTART.md](QUICKSTART.md)** — 5-minute guide for you or a friend.

## Install

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

Copy [`.env.example`](.env.example) → `.env.local` (gitignored).

## Supported agents

Claude Code · OpenAI Codex · Qwen Code · OpenCode · Grok Build · Google Antigravity

Details: [`references/agent-install.md`](3x-ui-vpn-setup/references/agent-install.md)

## What's in v1.1

| Category | Files |
|----------|-------|
| **P0** | `inbounds.md`, `execution-order.md`, `happ-routing-profile-ru.json` |
| **P1** | `verify-server.sh`, `apply-routing.py`, `fix-hysteria-stream.py`, `panel-security.md`, `post-setup-handoff.md` |
| **P2+** | CDN `index.html`, `slave-node.md`, `QUICKSTART`, `CONTRIBUTING`, 10+ reference docs |

## Structure

```
3x-ui-vpn-setup/
├── SKILL.md
├── scripts/
│   ├── verify-server.sh
│   ├── apply-routing.py
│   └── fix-hysteria-stream.py
├── references/          # 15 guides
├── templates/           # routing + hysteria JSON
└── assets/cdn-fallback/ # nginx landing page
```

## Principles

- Never patch 3X-UI / Xray binaries
- Reality primary — not plain TLS on 443
- Follow `execution-order.md` (Hysteria last)
- No secrets in repo

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) — PRs welcome.

## License

MIT — [LICENSE](LICENSE)

**Repo:** https://github.com/KiwineMarlborough/3x-ui-vpn-setup-skill