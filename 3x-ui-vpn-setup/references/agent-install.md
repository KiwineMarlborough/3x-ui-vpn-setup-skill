# Install This Skill Per Agent

This skill follows the [Agent Skills open standard](https://agentskills.io/) (`SKILL.md` + optional `references/` + `templates/`).

## Verified compatible agents

| Agent | Skills support | Install path(s) |
|-------|----------------|-----------------|
| **Claude Code** | Yes | `~/.claude/skills/3x-ui-vpn-setup/` or `.claude/skills/` in repo |
| **OpenAI Codex** | Yes | `~/.agents/skills/3x-ui-vpn-setup/` or `$REPO/.agents/skills/` |
| **Qwen Code** | Yes | `~/.qwen/skills/3x-ui-vpn-setup/` (also reads `~/.agents/skills/`) |
| **OpenCode** | Yes | `~/.config/opencode/skills/` or `.opencode/skills/` or `.agents/skills/` |
| **Grok Build** | Yes | `~/.grok/skills/3x-ui-vpn-setup/` or `.grok/skills/` in repo |
| **Google Antigravity** | Yes | Agent Skills standard (see [agentskills.io clients](https://agentskills.io/)) |

All listed agents support the same `SKILL.md` frontmatter (`name`, `description`).

## One-command install (Skills CLI)

Works across most agents into the shared user skills directory:

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

Browse: https://skills.sh/KiwineMarlborough/3x-ui-vpn-setup-skill/3x-ui-vpn-setup

## Manual install

```bash
git clone https://github.com/KiwineMarlborough/3x-ui-vpn-setup-skill.git
cp -r 3x-ui-vpn-setup-skill/3x-ui-vpn-setup ~/.agents/skills/
# Also copy to agent-specific dir if needed, e.g.:
# cp -r ... ~/.grok/skills/3x-ui-vpn-setup
# cp -r ... ~/.claude/skills/3x-ui-vpn-setup
# cp -r ... ~/.qwen/skills/3x-ui-vpn-setup
```

## Invoke

- **Automatic:** agent loads when task matches `description` (e.g. "set up 3X-UI on new VPS")
- **Explicit:** `/3x-ui-vpn-setup` or `/skills 3x-ui-vpn-setup` (agent-dependent)

## What to give the agent

Minimum prompt:

```text
Use the 3x-ui-vpn-setup skill. SSH: user@IP, key at ~/.ssh/id_ed25519.
Domains: panel.vpn.example.com, cdn.vpn.example.com.
Set up Reality + XHTTP + Hysteria2 + Happ routing in subscription.
```

Agent must have **shell/SSH tools** enabled.