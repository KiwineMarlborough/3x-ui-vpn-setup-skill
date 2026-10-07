# Version Compatibility Matrix

"Verified" = exercised end to end by the skill author on a live server. Anything else: run `verify-server.sh` after every change.

## Stack verified in production (2026-10)

| Component | Version | Notes |
|-----------|---------|-------|
| OS | **Ubuntu 26.04 LTS** (kernel 7.0.x), also written for 22.04/24.04 | 26.04 uses **sudo-rs**: `sudo -E` is ignored → `sudo env VAR=… bash` |
| 3X-UI | **3.9.0** (updated 3.4 → 3.7 → 3.9) | `x-ui update` keeps `/etc/x-ui/x-ui.db`; runs DB migrations |
| Xray core | **26.9.30** (bundled; updated from 26.6.x/26.7.x) | Hysteria needs `version: 2`; `finalmask` warning is non-blocking |
| nginx | 1.28 (Ubuntu 26.04) | `listen … http2` prints a deprecation warning on ≥ 1.25.1; works (24.04's 1.24 lacks `http2 on;`) |
| acme.sh | 3.1.x | installed by 3X-UI's SSL menu; standalone mode by default (`cert-renewal-nginx.md`) |
| fail2ban | 1.1 | `3x-ipl` jail created by 3X-UI, `sshd` jail from the skill |
| nftables | ships with Ubuntu | IPsum table (`blocklist-ipsum-fail2ban.md`) |

## Protocol/transport matrix

| Combination | Status |
|-------------|--------|
| VLESS + TCP + REALITY (+ `xtls-rprx-vision`) | **verified** works (Xray 26.7.28 and 26.9.30) |
| VLESS + TCP + TLS (+ vision flow) | **verified** (needs a valid certificate!) |
| VLESS + XHTTP + TLS (`packet-up`) | **verified** |
| VLESS + **XHTTP + REALITY** | **broken on Xray 26.7.28** — the XHTTP request got `EOF` right after dialing (tried empty `host`, `mode: auto`). **Not re-tested on 26.9.30.** Don't use without a loopback test (`testing-methods.md`) |
| Hysteria2 (`protocol hysteria`, network `hysteria`) | **verified**; both `hysteriaSettings`/`hysteria2Settings` with `version: 2` |
| AmneziaWG 3.1 (native inbound, 3X-UI ≥ 3.7) | **verified** on iPhone; OpenWrt unverified (`amneziawg.md`) |

## Xray 26.x + Hysteria2

Mandatory — see `gotchas.md`: `protocol: hysteria`, `stream_settings.network: hysteria`, both
`hysteriaSettings` and `hysteria2Settings` with `version: 2`.

## 3X-UI API

Stable concept, **changing paths** across 3.x: the skill's API doc is verified for 3.9.0 (`api-reference.md`). On 404 read
`GET /panel/api/openapi.json` — the panel documents its own routes (method matters: GET vs POST).
3.9.0 behaviour change: `inbounds/update` no longer edits clients or the inbound's `enable`.

## Client apps

| Client | Reality | XHTTP | Hysteria2 | AmneziaWG |
|--------|---------|-------|-----------|-----------|
| Happ Plus | yes (latency column may say `n/a`) | yes | yes | **no** (AWG is not in the subscription) |
| Throne (desktop) | yes | yes | yes | — |
| v2rayNG 1.8+ | yes | varies | yes | — |
| Hiddify | yes | yes | yes | — |
| OpenWrt Passwall/Podkop family | yes | often no | often no | via an AWG package (unverified) |
| AmneziaVPN / AmneziaWG apps | — | — | — | yes (3.1-capable versions for 3.1 fields) |

## After a panel/Xray update (checklist)

```bash
sudo x-ui status
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
sudo python3 scripts/loopback-test.py                 # real handshake per inbound
sudo env REQUIRE_HYSTERIA=1 CDN_DOMAIN=… SUB_PATH=… SUB_ID=… bash scripts/verify-server.sh
```
If Hysteria breaks: `scripts/fix-hysteria-stream.py`. See `backup-update.md` for the update procedure and rollback.

## Related

`backup-update.md` · `vps-providers.md` · `gotchas.md` · `testing-methods.md`
