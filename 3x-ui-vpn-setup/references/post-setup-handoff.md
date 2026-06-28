# Post-Setup Handoff (give to user)

Agent must deliver this checklist when setup passes `verify-server.sh`.

## Credentials (user stores locally — NOT in git)

| Item | Where |
|------|-------|
| Panel URL | `https://panel.<domain>:<port>/<webBasePath>/` |
| Panel login / password | password manager |
| API token | password manager |
| SSH key | `~/.ssh/...` |
| Subscription URL | see below |
| JSON sub URL | optional for advanced clients |

## Subscription URLs

```
https://<cdn-domain>:2096/<subPath>/<full-36-char-sub_id>
https://<cdn-domain>:2096/<jsonPath>/<full-36-char-sub_id>
```

Warn: truncated `sub_id` → 404.

## Client setup (Happ Plus)

1. Add subscription URL
2. Pull down to refresh (routing updates)
3. Enable routing profile if prompted (`SplitHome` / `SplitRU`)
4. Test: Reality 8443 primary, XHTTP if mobile issues

## Router (optional second user)

- Profiles: TCP 8444 + Reality 8443 only
- Separate `user-router@...` recommended

## Profiles delivered (expect 4)

| Name | Port | Protocol |
|------|------|----------|
| *-Reality-Vision | 8443 | VLESS Reality |
| *-TCP-Podkop | 8444 | VLESS TLS |
| *-XHTTP-Mobile | 2053 | VLESS XHTTP |
| *-Hysteria2 | 36712/udp | hysteria2 |

## Reality params (for manual import)

```
SNI: <borrowed-sni>
Public key: <from-panel>
Short ID: <from-panel>
Fingerprint: firefox
Flow: xtls-rprx-vision
```

## Verification user can run

- Open site through VPN — IP shows VPS country
- `.ru` sites with split routing — direct (home IP) if configured
- Panel opens only via domain (403 by IP = correct)

## Maintenance reminders

- Backup `x-ui.db` before panel update
- After LE renewal: sync nginx cert copy (`references/cert-renewal-nginx.md`)
- If JSON 500: see `references/gotchas.md`