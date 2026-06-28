# Contributing

Thanks for improving this open-source agent skill.

## Rules

1. **Never** commit real passwords, API tokens, UUIDs, private keys, or user domains
2. Keep examples generic (`example.com`, `vpn.example.com`)
3. Do not patch 3X-UI binaries — document panel/API/SQLite workflows only
4. Match [Agent Skills](https://agentskills.io/) format: `SKILL.md` + optional folders

## Pull requests

- One topic per PR (e.g. "add router section", "fix hysteria script")
- Test scripts on Ubuntu 22.04/24.04 if you change `scripts/`
- Update `SKILL.md` reference table when adding docs
- Update `CHANGELOG.md` for user-visible changes

## Issues

Include:
- Agent used (Claude Code, Codex, etc.)
- 3X-UI / Xray version
- Error log snippet (redact secrets)

## Local test

```bash
npx skills add ./3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

## License

MIT — see [LICENSE](LICENSE).