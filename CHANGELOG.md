# Changelog

## [1.4.0] — 2026-11-24

Optional **country-bridge** module: extra subscription lines that exit through another country, used day-to-day for ~2 weeks on a real
hub (3X-UI 3.11.0 / Xray 26.11.9). Everything in `scripts/bridge/` was run live; items not verified are listed in the reference.

### Added
- `references/country-bridge.md`: design (one inbound per exit + `hosts` row + routing rule), own exit VDS vs provider nodes, balancers with
  fail-closed, country pools by subscription flag, per-agent access, how to prove it works, and what is NOT verified.
- `scripts/bridge/`: `deploy_exit_node.sh` (separate Xray exit node, port limited to the hub IP, blocks private/loopback/own IP), `add_bridge_profile.py`,
  `link_to_outbound.py` (vless / hysteria2 link → outbound), `test_outbound.py`, `sync_country_balancers.py` + `deploy_country_sync.sh` (hourly timer: nodes
  chosen by **flag**, stable copies `ctry-<CC>-<n>`, live exit-country check, `--tolerate`, blackhole when empty), `set_profile_balancer.py`,
  `failover_test.py`, `route_test.py`, `add_agent.py`, `sub_to_xray.py` (agent-side local proxy from a subscription), small API helpers.
- Lessons recorded in the references: balancer `selector` is a **prefix** match; provider tags are not country names (providers reshuffle which
  server carries which name); a balancer with no `fallbackTag` silently exits from the hub IP; failover timing (observatory 30 s → ~76 s);
  WARP findings (`warp-optional.md`); BBR only affects new connections (`optimization.md`).
- Hard rules 14–15 in `SKILL.md`; intake question 15; phase 23.

### Known limits
- 3-tier priority via a `loopback` outbound chain and entry nodes inside the censoring country are designs, not verified.
- A Forkop (sing-box) router did not show latency for the bridge lines while desktop clients did; cause unknown — no compatibility claim.

## [1.3.1] — 2026-10-08

### Added
- `scripts/setup-atop.sh`: installs `atop` and records per-process CPU/memory/disk/network history (60 s interval, 28 days, idempotent, `DRY_RUN=1`),
  so a panel/Telegram "CPU 87%" alert can be explained after the fact. Verified on a live server (dry-run, input validation, idempotent real run, `atopsar`
  replay); atop itself was installed and run there.
- `references/monitoring.md`: "CPU alerts: explain them after the fact" — what atop is, replay commands, and the investigation procedure that worked
  (own sudo log → panel history API `/panel/api/server/history/cpu/{bucket}` → atop → attack indicators → hypervisor steal → single blip is normal on 1 vCPU).
- `verify-server.sh` warns when atop is not recording; `execution-order.md` phase 1c; `repair-only.md` "CPU high" branch.

## [1.3.0] — 2026-10-08

Lessons from operating a real server for months. The scripts below were exercised against a live 3X-UI 3.9.0 / Xray 26.9.30 / Ubuntu 26.04 server (see "Known limits" for the paths that were only
run as preflight/dry-run/staging); what could not be verified is marked in `references/compatibility.md` and in the documents themselves.

### Fixed — the silent failure that took the VPN down
- Certificate renewal: 3X-UI's acme.sh issues in *standalone* mode, nginx owns :80 → renewal never succeeded, the CDN cert expired and every TLS profile
  died while Reality kept working. `references/cert-renewal-nginx.md` rewritten (was certbot-based); new `scripts/deploy-acme-renewal.sh`
  (webroot, deploy hook, STAGING_TEST, detects standalone mode and extra SAN names), `scripts/check-cert-expiry.sh`; `templates/nginx-cdn.conf`
  serves `/.well-known/acme-challenge/` on :80 before redirecting.
- `scripts/deploy-cert-hook.sh` marked legacy (certbot-only). All `sudo -E` usage replaced with `sudo env VAR=… bash` (Ubuntu 26.04 sudo-rs ignores `-E`).

### Added
- **Hardening by default:** `scripts/deploy-ipsum.sh` + `ipsum-update.sh` (IPsum level ≥3 in its own nftables table, whitelist first, SSH peers protected,
  5-min auto-rollback, daily timer), `scripts/setup-fail2ban.sh` (sshd jail with admin `ignoreip`), `references/blocklist-ipsum-fail2ban.md`.
- **Panel not public:** `references/panel-tunnel-access.md` (no DNS record, closed port, SSH tunnel + hosts entry, self-signed cert); `panel-security.md`, `dns-setup.md`
  rewritten (what the Cloudflare orange cloud breaks; one public name).
- **Testing:** `scripts/loopback-test.py` (real VLESS handshake per inbound from the panel DB; hints for expired certs / Reality rejection),
  `references/testing-methods.md` (what proves a profile works; client `n/a` is not evidence).
- **AmneziaWG 3.1 (optional module):** `scripts/awg-tool.py` (create / rotate obfuscation / render `.conf`), `references/amneziawg.md`.
- **Access hygiene:** `references/agent-access-hygiene.md` (agent account, expiry, leftovers audit).
- `scripts/verify-server.sh`: served-certificate expiry, IPsum table + armed rollback timer, fail2ban, panel port closed, `hosts` consistency, AWG UDP port, loopback handshakes.
- `scripts/audit-server.sh`: certificates + renewal mode, accounts/sudoers/SSH keys, hardening state, `hosts` mismatches, nginx `sites-enabled` copies, pending reboot.
- Routing templates: `100.64.0.0/10` (carrier-grade NAT) added to `DirectIp`.

### Changed
- `references/api-reference.md` rewritten for 3X-UI 3.9.0: GET vs POST (a wrong method answers 404), `GET /panel/api/openapi.json`, new `inbounds/*`, `clients/*`,
  `hosts/*` routes, `setEnable` form field, **`inbounds/update` no longer edits clients/enable**.
- `references/gotchas.md`: `hosts` table overrides subscription links; DB-edited settings are served stale until `x-ui` restarts; XHTTP+Reality broken on Xray 26.7.28
  (not re-tested on 26.9.30); nginx `sites-enabled` copies/backups; sudo-rs; `pkill -f` kills the SSH session; update migration race.
- `references/execution-order.md`, `SKILL.md` (v1.3.0), `repair-only.md`, `inbounds.md`, `compatibility.md`, `backup-update.md`, `monitoring.md`, `nginx-fallback.md`,
  `post-setup-handoff.md`, `protocol-selection.md`, `clients.md`, `happ-routing.md`, `rkn-and-blocking.md`, `secrets-management.md`, README/QUICKSTART/ИНСТРУКЦИЯ (EN + RU).
- `.env.example`: `ADMIN_IPS`, `PANEL_ACCESS`, IPsum, certificate and AWG variables. `.gitignore`: `awg/`, `*.tgz`, `*.db`, backup dirs.

### Known limits (stated honestly in the docs)
- `deploy-acme-renewal.sh APPLY`, `deploy-ipsum.sh` (real run), `setup-fail2ban.sh` (real run) and `awg-tool.py create` (live) were exercised via preflight/dry-run/staging and
  the equivalent manual steps; their real-run paths were not re-run end to end on a clean server.
- AmneziaWG on OpenWrt/Forkop, `setEnable` form call, `webListen=127.0.0.1` were not verified by the author.
- The server's IP remains a datacenter address and TLS inbounds still show the CDN certificate on odd ports — documented, not fixable by the skill.

## [1.2.2] — 2026-06-29

### Fixed
- `fix-hysteria-stream.py` — preserve existing Hysteria clients when setting `version: 2`
- `fix-podkop-flow.py` — default scopes to Podkop inbound clients only; `--all` for global (dangerous)
- `set-sub-paths.py` — `--sqlite-only` works without API creds; fallback returns failure if DB missing
- `verify-server.sh` — CDN HTTPS check validates HTTP 200, not curl exit code

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