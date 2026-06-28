# 3x-ui-vpn-setup — Universal Agent Skill

Open-source [Agent Skill](https://agentskills.io/) for AI coding agents to **autonomously set up a personal 3X-UI VPN** on a fresh Linux VPS via SSH.

**Stack:** VLESS **Reality** (primary) + XHTTP + TCP Podkop + Hysteria2 + Happ routing in subscription (DoH) + optional nginx CDN fallback.

No vendor lock-in — any domain, any VPS. **No secrets in repo.**

## Supported agents (verified)

| Agent | Install |
|-------|---------|
| Claude Code | `npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y` |
| OpenAI Codex | same |
| Qwen Code | same (+ `~/.qwen/skills/`) |
| OpenCode | same (+ `.opencode/skills/`) |
| Grok Build | same (+ `~/.grok/skills/`) |
| Google Antigravity | Agent Skills open standard |

Details: [`references/agent-install.md`](3x-ui-vpn-setup/references/agent-install.md)

## Quick start

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

Then tell your agent:

```text
Use 3x-ui-vpn-setup skill. Fresh Ubuntu VPS.
SSH: deploy@203.0.113.10, key ~/.ssh/vps_ed25519
Domains: panel.vpn.example.com, cdn.vpn.example.com
Reality SNI: pixelforge.pics
Happ split routing for .ru direct.
```

Agent needs **SSH/shell** access.

## What the agent will do

1. Harden VPS (UFW, SSH)
2. Install 3X-UI (MHSanaei)
3. TLS for panel + CDN domains
4. Create 4 inbounds: **Reality 8443**, TCP 8444, XHTTP 2053, Hysteria2 UDP
5. Custom subscription paths (not `/sub/`)
6. Push Happ routing profile into subscription
7. Optional nginx fake site on 443
8. Verify Xray config, HTTP 200 sub/json

## Structure

```
3x-ui-vpn-setup/
├── SKILL.md
├── references/
│   ├── gotchas.md
│   ├── happ-routing.md
│   ├── nginx-fallback.md
│   ├── diagnostics.md
│   └── agent-install.md
└── templates/
    ├── happ-routing-profile.json
    ├── happ-routing-global.json
    └── hysteria-stream-settings.json
```

## Principles

- Never patch 3X-UI / Xray binaries
- Panel + API + SQLite only
- Reality over plain TLS on 443
- Personal tunnel — not commercial VPN resale

## License

MIT — [LICENSE](LICENSE)

## Contributing

PRs welcome. **Never** commit real credentials, API tokens, or private keys.