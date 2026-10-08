# Execution Order (do not reorder)

Wrong order causes Xray crash, JSON 500, nginx port conflict, a lock-out, or a certificate that silently never renews.

## Phase map

```
0.  Intake (SSH, domains, SNI, ADMIN IPs, panel access mode, agent-account policy, optional AWG)
1.  Baseline: apt update/upgrade, UFW basics (deny incoming; allow SSH first!)
1b. Hardening: Fail2Ban (setup-fail2ban.sh) and IPsum (deploy-ipsum.sh, rollback armed -> confirm)   <- needs ADMIN_IPS
1c. Observability: atop (setup-atop.sh) — CPU/process history so a later CPU alert can be explained
2.  Install 3X-UI (x-ui menu / install.sh)
3.  Panel harden: password, webBasePath, API token; panel port closed in UFW (tunnel-only)
4.  DNS: ONE A record for the CDN name (grey cloud) -> wait propagation   — dns-setup.md (no panel record)
5.  Certificate for the CDN name (3X-UI SSL menu = acme.sh standalone, while port 80 is still FREE)
6.  nginx on 80/443 — deploy-nginx-fallback.sh — BEFORE any inbound on 443
6b. deploy-acme-renewal.sh: STAGING_TEST=1 then APPLY=1 -> webroot renewal + deploy hook + cron   <- mandatory
7.  Panel certificate: self-signed (tunnel-only) — cert-renewal-nginx.md
8.  Inbound Reality 8443
9.  Inbound TCP (Podkop) 8444
10. Inbound XHTTP 2053 (TLS)
11. Client(s) + attach to inbounds
12. Custom sub paths + subEncrypt=false — set-sub-paths.py, panel-settings.md
13. Test plain subscription HTTP 200 (3 profiles)
14. Inbound Hysteria 36712 — fix stream, restart
15. Test JSON subscription HTTP 200
16. Sync the `hosts` table with each inbound (links!) — inbounds.md
17. Happ routing in subRoutingRules (API) — apply-routing.py
18. Optional: AmneziaWG 3.1 — amneziawg.md (UFW udp port, awg-tool.py)
19. UFW final ports (panel port DENY, unused rules removed)
20. scripts/loopback-test.py — real handshake per inbound
21. scripts/verify-server.sh
22. Cleanup + post-setup handoff (accounts audit, agent account expiry) — agent-access-hygiene.md, post-setup-handoff.md
```

## Critical dependencies

| Step | Blocks |
|------|--------|
| ADMIN_IPS known + SSH key login proven | 1b (IPsum/Fail2Ban could lock you out) |
| nginx on 443 | VLESS inbound on 443 |
| Certificate issued **before** nginx (port 80 free) | 6 needs the cert files; then 6b switches renewal to webroot |
| 6b not done | certificate expires ~90 days later, silently, TLS profiles die |
| Hysteria wrong stream | Xray start, ALL profiles dead |
| Hysteria before JSON test | JSON HTTP 500 |
| Panel cert mismatch | Panel TLS handshake error |
| Truncated sub_id | Sub 404 |
| Stale `hosts` row | wrong `security`/`sni` in subscription links |
| IPsum rollback timer left armed | the blocklist is deleted after 5 min |

## Hysteria isolation test

If JSON returns 500:

1. Disable the Hysteria inbound only (`inbounds/setEnable/<id>` with form field `enable=false`, or the panel switch)
2. `x-ui restart`
3. JSON URL → if 200, the problem is the Hysteria stream
4. Apply `templates/hysteria-stream-settings.json` + `version: 2` in both keys
5. Re-enable, re-test

## Routing last

Apply `subEnableRouting` only when: plain sub returns 200 · at least Reality connects (loopback test) · `sub_id` is the full UUID.
User refreshes Happ after a routing change. Restart `x-ui` if you edited the DB instead of using the API.

## Rollback

| Issue | Action |
|-------|--------|
| Xray won't start | Disable the Hysteria inbound, check the log for `version != 2` |
| Locked out of SSH | Provider console → disable UFW / fix rules; IPsum: wait for the auto-rollback or `nft delete table inet ipsum` |
| Panel 403 | You used IP/localhost; use the panel hostname via the hosts entry + tunnel |
| New inbound broke others | `inbounds/setEnable` off or `inbounds/del`; restore `x-ui.db` from backup |
| Certificate problem | `cert-renewal-nginx.md` |

## Related

`repair-only.md` · `testing-methods.md` · `blocklist-ipsum-fail2ban.md` · `panel-tunnel-access.md`
