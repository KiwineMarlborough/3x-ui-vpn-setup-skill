# Secrets Management

How agents and users handle credentials without leaking them to git, chat logs, or public repos.

## Golden rules

1. **One source of truth:** `.env.local` (gitignored) — copy from `.env.example`
2. **Never** commit passwords, API tokens, UUIDs, `sub_id`, private keys, real domains
3. **Never** hardcode secrets in skill repo scripts or docs
4. **Handoff** goes to user's password manager — not into GitHub issues or PRs

## `.env.local` workflow

```bash
cp .env.example .env.local
# Fill after install phases:
# WEB_BASE_PATH, PANEL_TOKEN, PANEL_PASSWORD, SUB_ID, SUB_PATH, JSON_PATH
```

| Variable | Stored where after setup |
|----------|--------------------------|
| `SSH_KEY_PATH` | User machine only |
| `PANEL_PASSWORD` | Password manager |
| `PANEL_TOKEN` | Password manager |
| `SUB_ID` | Subscription URL in Happ |
| Sudo password | **Not** in repo — SSH key + sudo on server |

Scripts read env vars; they do not embed values.

## What agents should do

- Load secrets from `.env.local` or user message (one-time)
- Use `references/post-setup-handoff.md` template for delivery
- Redact secrets in issue reports: `TOKEN=***`, `sub_id=baef****`
- Run `grep` audit before any git push (see checklist below)

## Pre-push audit checklist

```bash
# From skill repo root — must return no matches for real values
grep -rE 'password|token|BEGIN OPENSSH|sub_id' --include='*.md' --include='*.py' --include='*.sh' .
# Only .env.example placeholders allowed
```

Forbidden in tracked files:

- Real IPs, panel URLs with `webBasePath`
- API tokens, panel passwords, Hysteria `auth` strings
- Client UUIDs, full `sub_id`

## Rotation procedure

Rotate if secrets appeared in: public repo, screenshot, shared chat export, compromised laptop.

| Secret | How to rotate |
|--------|---------------|
| Panel password | Panel → Profile → change password |
| API token | Panel → revoke old, create new → update `.env.local` |
| `sub_id` | New client or regenerate in panel → new subscription URL |
| Hysteria auth | Regenerate client auth on inbound → refresh sub |
| SSH key | `ssh-keygen` new key → `authorized_keys` → remove old |
| Sudo password | `passwd` on VPS |
| Reality keys | Regenerate in inbound → clients refresh sub |

After rotation: run `verify-server.sh`, deliver updated handoff.

## Local project layout (user machine)

Recommended (not in skill repo):

```
~/.vpn-setup/
  .env.local          # secrets
  handoff.md          # generated, gitignored
  keys/
    vps_ed25519       # chmod 600
```

Add to user's global `.gitignore`:

```
.env.local
handoff*.md
*_ed25519
```

## Session / terminal logs

AI agent sessions and terminal history may contain secrets typed in commands.

- Prefer env vars over inline passwords in SSH commands
- Use `SSH_ASKPASS` or key-based sudo where possible
- If concerned: rotate panel + API token (see above)

## Handoff delivery

Give user:

- Panel URL (with `webBasePath`)
- Subscription URLs (full `sub_id`)
- Reality public key + shortId (from panel)
- **Not** sudo password in plain text chat — use password manager share

## Related

- `CONTRIBUTING.md` — no secrets in PRs
- `.gitignore` — `*.pem`, `keys/`, `.env.local`
- `references/post-setup-handoff.md` — user deliverable template