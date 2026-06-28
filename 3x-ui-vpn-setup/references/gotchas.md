# 3X-UI / Xray Gotchas

## Hysteria2 + Xray 26.6.x

| Field | Correct value |
|-------|---------------|
| inbound `protocol` | `hysteria` |
| `stream_settings.network` | `hysteria` (**not** `hysteria2`) |
| `settings.version` | `2` |
| `hysteriaSettings.version` | `2` (required for Xray start) |
| `hysteria2Settings.version` | `2` (required for 3X-UI JSON sub generator) |
| Client credential field | `auth` (not `password`) |
| Share link scheme | `hysteria2://auth@host:port?...` |

**Safe compromise:** keep **both** `hysteriaSettings` and `hysteria2Settings` in `stream_settings` with identical content including `version: 2`.

### Symptom → fix

| Symptom | Likely cause |
|---------|--------------|
| Log: `Failed to build Hysteria config > version != 2` | Missing `version: 2` inside `hysteriaSettings` |
| JSON subscription HTTP 500, plain sub 200 | Stream has only `hysteria2Settings`, missing `hysteriaSettings` |
| All profiles dead, Xray won't start | Hysteria stream misconfigured |
| JSON 500 isolate test | Disable hysteria inbound — if JSON returns 200, fix hysteria stream |

### Stream template

See `templates/hysteria-stream-settings.json`.

## Reality

- `serverName` / SNI = **borrowed** legitimate site (e.g. photography SaaS), not your VPN domain.
- Traffic hits **your VPS IP**; TLS ClientHello mimics visit to SNI domain.
- `flow=xtls-rprx-vision` on Reality inbound; Podkop TCP often needs **empty** flow.
- Latency test `-1` in client does not always mean broken — test real traffic.

## Panel TLS

- `webCertFile` / `webKeyFile` must match `webDomain`.
- Using CDN cert on panel domain → handshake error in browser.

## Subscription

- `subEncrypt=false` → plain text links in body (not base64 blob).
- Truncated `sub_id` → 404.
- Custom paths: old `/sub/` should return 404 after migration.

## nginx vs port 443

- nginx on 443 + Xray VLESS on 443 = conflict.
- Inbound DE-TCP-443 must stay disabled OR nginx must move to another port first.

## Updates

Panel update usually preserves `/etc/x-ui/x-ui.db`. After update:

1. `x-ui status`
2. `xray-linux-amd64 run -test`
3. Sub + JSON HTTP 200
4. Hysteria still has `version: 2` in both settings keys

Backup from panel before upgrading.