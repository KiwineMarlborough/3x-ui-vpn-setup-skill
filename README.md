# 3x-ui-vpn-setup — Agent Skill

Open-source [Agent Skill](https://skills.sh/) for AI assistants (Grok, Cursor, Claude Code, Codex) to set up and maintain a **personal** [3X-UI](https://github.com/MHSanaei/3x-ui) VPN server.

Battle-tested patterns: VLESS Reality, XHTTP, Podkop TCP, Hysteria2, custom subscription paths, nginx CDN fallback, Happ Plus Meridian routing (DoH), UFW, Let's Encrypt.

**No secrets in this repo** — all credentials are placeholders. Bring your own SSH keys and panel tokens.

## Install

### Skills CLI (recommended)

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

### Grok

Copy or symlink to `~/.grok/skills/3x-ui-vpn-setup/` (must contain `SKILL.md`).

### Cursor / Claude Code

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

## Usage

Invoke automatically when you ask:

- «Настрой новый сервер 3X-UI»
- «Fix Hysteria version != 2»
- «JSON subscription 500»
- `/3x-ui-vpn-setup`

Or slash command: `/3x-ui-vpn-setup`

## Structure

```
3x-ui-vpn-setup/
  SKILL.md                        # Main agent workflow
  references/
    gotchas.md                    # Hysteria, Reality, JSON sub
    happ-routing.md               # Meridian + DoH
    nginx-fallback.md             # Port 443 layout
    diagnostics.md                # Commands
  templates/
    meridian-routing.json         # Happ routing profile
    hysteria-stream-settings.json # Working stream shape
```

## Principles

1. Never patch 3X-UI or Xray binaries
2. Panel + API + SQLite only
3. Verify after every risky change
4. Personal tunnel — not a commercial VPN playbook

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. Do **not** submit real server credentials, API tokens, or private keys.