# Changelog

## [1.2.1] — 2026-06-29

### Added
- `README.ru.md` — Russian overview with «give skill to AI agent» intro
- `ИНСТРУКЦИЯ.md` — full Russian step-by-step guide
- `QUICKSTART.ru.md` — Russian 5-minute quickstart
- English README intro block + links to Russian docs

## [1.2.0] — 2026-06-29

### Added — documentation
- `references/panel-settings.md` — settings key dictionary
- `references/api-reference.md` — API patterns and gotchas
- `references/repair-only.md` — fix-existing-server decision tree
- `references/secrets-management.md` — `.env.local`, rotation, audit
- `references/protocol-selection.md` — when to use each profile
- `references/multi-user.md` — router/guest users, limitIp
- `references/dns-setup.md` — Cloudflare grey cloud, propagation
- `references/rkn-and-blocking.md` — blocking context for RU users
- `references/migration.md` — VPS migration checklist
- `references/monitoring.md` — backup cron, healthcheck
- `references/compatibility.md` — version matrix
- `references/vps-providers.md` — provider notes

### Added — scripts & templates
- `templates/nginx-cdn.conf` — full nginx vhost
- `scripts/deploy-nginx-fallback.sh` — deploy CDN page + vhost
- `scripts/deploy-cert-hook.sh` — LE renewal → nginx sync
- `scripts/set-sub-paths.py` — custom sub paths via API
- `scripts/fix-podkop-flow.py` — empty flow for Podkop
- `scripts/audit-server.sh` — read-only diagnostics
- `templates/happ-routing-corporate.json` — LAN/corp DirectSites
- `templates/happ-routing-banks-ru.json` — extended .ru direct list

### Changed
- `scripts/verify-server.sh` — profile count, hysteria log check, panel API ping, `REQUIRE_HYSTERIA`
- `references/happ-routing.md` — DoH vs DoT vs DoU section, template table fix
- `references/diagnostics.md` — consistent `cdn.vpn.example.com` examples
- `references/slave-node.md` — expanded API steps
- `SKILL.md` — v1.2, intake questionnaire, new index entries
- `README.md`, `QUICKSTART.md` — v1.2 highlights

## [1.1.0] — 2026-06-29

- `inbounds.md`, `execution-order.md`, `happ-routing-profile-ru.json`
- `verify-server.sh`, `apply-routing.py`, `fix-hysteria-stream.py`
- CDN `index.html`, 15+ reference docs, `QUICKSTART.md`

## [1.0.0] — 2026-06-29

- Initial public release
- Universal skill without project-specific branding