# Version Compatibility Matrix

Tested combinations for this skill. Other versions may work — run `verify-server.sh` after any change.

## Recommended stack

| Component | Version | Notes |
|-----------|---------|-------|
| OS | Ubuntu 22.04 / 24.04 LTS | Debian 12 often works |
| 3X-UI | MHSanaei latest stable | Install via official `install.sh` |
| Xray core | 26.6.x (bundled with 3X-UI) | Hysteria requires `version: 2` |
| nginx | 1.18+ | CDN fallback on 443 |
| Happ Plus | Current App Store | Routing via subscription headers |

## Xray 26.x + Hysteria2

Mandatory — see `gotchas.md`:

- `protocol`: `hysteria`
- `stream_settings.network`: `hysteria`
- Both `hysteriaSettings` and `hysteria2Settings` with `version: 2`

## 3X-UI API

Panel API paths stable across recent releases. If endpoint 404:

1. Open panel in browser → DevTools → Network
2. Match path for your version
3. Update `api-reference.md` via PR

## Client cores

| Client | Reality | XHTTP | Hysteria2 |
|--------|---------|-------|-----------|
| Happ Plus | yes | yes | yes |
| v2rayNG 1.8+ | yes | varies | yes |
| Hiddify | yes | yes | yes |
| OpenWrt Passwall | yes | often no | often no |

## After panel update

```bash
sudo x-ui status
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
sudo REQUIRE_HYSTERIA=1 bash scripts/verify-server.sh
```

If Hysteria breaks: `scripts/fix-hysteria-stream.py`

## Related

- `references/backup-update.md`
- `references/vps-providers.md`