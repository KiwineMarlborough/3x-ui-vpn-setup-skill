# 3x-ui-vpn-setup — Universal Agent Skill v1.3

> **Tired of blocked VPN services?** Spin up **your own** server in an evening — no manual Xray configs.
>
> **How it works:** install this skill into an AI agent and **hand it the job**. The agent SSHes into your VPS and sets up 3X-UI, Reality, XHTTP, Hysteria2, an optional AmneziaWG 3.1 tunnel, the subscription and Happ routing by itself — and hardens and monitors the server.
>
> **You only provide:**
> - VPS **IP** and **one domain** for the VPN/CDN name (the admin panel gets **no public DNS record** by default)
> - **SSH access** (ed25519 **key** preferred over password)
> - **Your own public IP(s)** — they are whitelisted so the hardening can never lock you out
> - **Sudo** for setup — ideally a key-only, time-boxed agent account (`references/agent-access-hygiene.md`)
>
> Everything else — certificates, inbounds, routing, blocklist, monitoring — the agent handles via the skill playbook.

Open-source [Agent Skill](https://agentskills.io/) for AI agents to **set up, harden, update and repair a personal 3X-UI VPN** on a Linux VPS via SSH.

**Stack:** VLESS **Reality** + XHTTP + TCP Podkop + Hysteria2 (+ optional **AmneziaWG 3.1**) + Happ routing (DoH) + nginx CDN fallback,
panel reachable **only through an SSH tunnel**, **self-renewing certificates**, **IPsum blocklist + Fail2Ban**.

## Documentation / Документация

| | English | Русский |
|---|---------|---------|
| Overview | [README.md](README.md) | [README.ru.md](README.ru.md) |
| Quickstart | **[QUICKSTART.md](QUICKSTART.md)** | **[QUICKSTART.ru.md](QUICKSTART.ru.md)** |
| Full guide | — | [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) | [CHANGELOG.md](CHANGELOG.md) |

## Install

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

Copy [`.env.example`](.env.example) → `.env.local` (gitignored).

## Supported agents

Claude Code · OpenAI Codex · Qwen Code · OpenCode · Grok Build · Google Antigravity

Details: [`references/agent-install.md`](3x-ui-vpn-setup/references/agent-install.md)

## What's new in v1.3 (lessons from running it in production)

| Area | What changed |
|------|--------------|
| **Certificates** | The #1 silent failure fixed: 3X-UI's acme.sh renews in *standalone* mode, which breaks the moment nginx owns port 80 → certificate expires after ~90 days and every TLS profile dies while Reality keeps working. New `deploy-acme-renewal.sh` (webroot + deploy hook, staging self-test), `check-cert-expiry.sh`, expiry checks in `verify-server.sh`/monitoring |
| **Hardening (default)** | IPsum blocklist in its own nftables table (whitelist first, auto-rollback, daily refresh) + Fail2Ban `sshd` with admin `ignoreip` |
| **Panel** | Not public by default: no DNS record, closed port, SSH tunnel + hosts entry, self-signed cert |
| **Testing** | `loopback-test.py`: a real VLESS handshake per inbound on the server — proves a profile works regardless of a client's unreliable `n/a` |
| **AmneziaWG 3.1** | Optional native inbound module (`awg-tool.py`: create / rotate obfuscation / render `.conf`) |
| **API** | `api-reference.md` rewritten for 3X-UI **3.9.0** (GET vs POST, `openapi.json`, `inbounds/update` no longer edits clients) |
| **Gotchas** | `hosts` table overrides subscription links; panel caches settings; XHTTP+Reality broken on Xray 26.7.28; nginx `sites-enabled` copies; Ubuntu 26.04 `sudo -E` is ignored; `pkill -f` kills your SSH session |
| **Audit** | `audit-server.sh` finds leftover accounts/sudo rules/keys, stale configs, mismatched links |

Honest scope: what was verified live vs. not is marked in each document (`compatibility.md`).

## Structure

```
3x-ui-vpn-setup/
├── SKILL.md
├── scripts/             # 16 scripts: setup, hardening, certificates, testing, monitoring, AWG
├── templates/           # routing, hysteria, nginx
├── references/          # 34 guides
└── assets/cdn-fallback/
```

## Principles

- Never patch 3X-UI / Xray binaries
- Reality primary — not plain TLS on 443
- Prove with a real handshake before blaming (or reverting) the server
- Fresh install → `execution-order.md`; repair → `repair-only.md`
- No secrets in the repo; no real hostnames in examples you don't want public

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) — PRs welcome.

## License

MIT — [LICENSE](LICENSE)

**Repo:** https://github.com/KiwineMarlborough/3x-ui-vpn-setup-skill
