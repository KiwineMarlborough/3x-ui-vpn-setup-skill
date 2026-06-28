# Execution Order (do not reorder)

Wrong order causes Xray crash, JSON 500, or nginx port conflict.

## Phase map

```
0. Intake (SSH, domains, SNI)
1. Baseline (apt, UFW basics)
2. Install 3X-UI
3. Panel harden (password, webBasePath, API token)
4. DNS A records → wait propagation — `dns-setup.md`
5. TLS certs (panel + cdn)
6. nginx on 443 — `deploy-nginx-fallback.sh` + `deploy-cert-hook.sh` — BEFORE any inbound on 443
7. Inbound Reality 8443
8. Inbound TCP Podkop 8444
9. Inbound XHTTP 2053
10. Client(s) + attach to inbounds
11. Custom sub paths + subEncrypt=false — `set-sub-paths.py`, `panel-settings.md`
12. Test plain subscription HTTP 200 (3 profiles)
13. Inbound Hysteria 36712 — fix stream, restart
14. Test JSON subscription HTTP 200
15. Happ routing in subRoutingRules
16. UFW final ports
17. verify-server.sh
18. post-setup handoff to user
```

## Critical dependencies

| Step | Blocks |
|------|--------|
| nginx on 443 | VLESS inbound on 443 |
| Hysteria wrong stream | Xray start, ALL profiles dead |
| Hysteria before JSON test | JSON HTTP 500 |
| Panel cert mismatch | Panel TLS handshake error |
| Truncated sub_id | Sub 404 |

## Hysteria isolation test

If JSON returns 500:

1. Disable Hysteria inbound only
2. `x-ui restart`
3. JSON URL → if 200, problem is Hysteria stream
4. Apply `templates/hysteria-stream-settings.json` + `version: 2` in both keys
5. Re-enable, re-test

## Routing last

Apply `subEnableRouting` only when:
- Plain sub returns 200
- At least Reality connects from client
- `sub_id` is full UUID

User refreshes Happ subscription after routing change.

## Rollback

| Issue | Action |
|-------|--------|
| Xray won't start | Disable inbound #4 (Hysteria), check log for `version != 2` |
| Locked out SSH | Provider console → disable UFW or fix rules |
| Panel 403 | Access via domain not IP; check `webDomain` |