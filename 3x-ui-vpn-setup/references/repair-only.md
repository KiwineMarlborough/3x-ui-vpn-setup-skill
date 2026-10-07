# Repair-Only Mode

Use when a 3X-UI server **already exists** and something broke. Do **not** rerun full install.

## Intake (repair)

1. SSH access confirmed
2. `sudo x-ui status`
3. `scripts/audit-server.sh` (read-only)
4. User symptom in one line

## Decision tree

```
Reality works, but TCP-TLS / XHTTP / Hysteria2 / subscription / CDN page all fail
└─ EXPIRED CERTIFICATE (most likely) -> sudo bash scripts/check-cert-expiry.sh
   ├─ expired / <7d -> cert-renewal-nginx.md: deploy-acme-renewal.sh (STAGING_TEST=1, then APPLY=1)
   └─ also check why renewal failed: acme.sh Le_Webroot='no' (standalone) + nginx on :80, or a removed DNS name inside the cert

Client shows n/a / won't connect, server looks fine
└─ testing-methods.md: loopback-test.py (HTTP 200?) -> another client -> another network. Do NOT revert server changes first.

User lost access from ONE network only (others fine)
└─ IPsum false positive (CGNAT range) -> nft get element inet ipsum blocklist '{ ip }' -> whitelist (blocklist-ipsum-fail2ban.md)

Locked out after enabling IPsum/Fail2Ban
└─ wait for the 5-min auto-rollback, or provider console: nft delete table inet ipsum ; fail2ban-client unban <ip>

ALL profiles dead / x-ui inactive
├─ xray -test FAIL
│  ├─ log: version != 2 → fix-hysteria-stream.py (gotchas.md)
│  ├─ disable Hysteria inbound → restart → if OK, fix Hysteria only
│  └─ bad stream JSON → restore x-ui.db backup
├─ xray -test OK but ports down → x-ui restart; check inbound enable flags
└─ UFW blocked → ufw status; restore SSH first

Plain sub HTTP 404
├─ truncated sub_id → use full UUID from panel
├─ wrong path → panel-settings.md; set-sub-paths.py
└─ subEncrypt=true → set false via API

JSON sub HTTP 500 (plain sub 200)
└─ Hysteria stream_settings → fix-hysteria-stream.py
   Test: disable Hysteria inbound → JSON should return 200

One profile fails (others OK)
├─ Reality → SNI blocked? reality-sni.md, protocol-selection.md
├─ TCP Podkop → flow must be empty → fix-podkop-flow.py
├─ XHTTP → path/host mismatch with inbound; TLS cert on cdn domain
└─ Hysteria → UDP 36712 blocked on network; or stream version

Panel won't open
├─ 403 by IP / localhost → expected (webDomain lock); use the panel hostname + hosts entry + SSH tunnel (panel-tunnel-access.md)
├─ hostname resolves to 198.18.x.x → hosts entry missing / VPN client fake-DNS answered
├─ browser refuses the self-signed cert → another browser, `thisisunsafe`, or trust the cert
├─ TLS error → webCertFile vs webDomain (panel-security.md); expired panel cert (check-cert-expiry.sh)
└─ timeout → closed port is CORRECT without the tunnel; with the tunnel check it is up and the forward is local-port -> 127.0.0.1:<port>

Subscription links show security=tls/sni=<domain> after an inbound was switched to Reality (or any wrong link field)
└─ stale `hosts` row -> inbounds.md / gotchas.md (GET/POST /panel/api/hosts/*)

Subscription/routing shows an old value after a direct SQLite edit
└─ systemctl restart x-ui (the panel caches settings)

Profile "works" in the list but nothing loads (AmneziaWG)
└─ amneziawg.md troubleshooting: UFW udp port, peer endpoint in amneziawglogs, MTU, return to minimal profile

Routing not applied in Happ
├─ subEnableRouting false → apply-routing.py
├─ client didn't refresh → pull subscription down
└─ curl -I sub URL → check Routing-Enable header

After panel update
└─ backup-update.md → xray -test → verify-server.sh → fix-hysteria if needed
```

## Repair scripts (in order of safety)

| Script | Risk | Use when |
|--------|------|----------|
| `audit-server.sh` | None (read-only) | Always first |
| `verify-server.sh` | None | Confirm fix |
| `fix-podkop-flow.py` | Low | Podkop TCP won't connect (default: port 8444 clients only; `--all` is global) |
| `set-sub-paths.py` | Medium | Sub 404; `--sqlite-only` if API unreachable |
| `apply-routing.py` | Medium | Routing headers missing |
| `fix-hysteria-stream.py` | Medium | JSON 500 / Xray won't start |
| `check-cert-expiry.sh` | None (read-only) | Any TLS problem — first check |
| `loopback-test.py` | None (temp local client) | Prove an inbound with a real handshake |
| `deploy-acme-renewal.sh` | Low–Medium (`STAGING_TEST=1` is safe; `APPLY=1` reissues) | Expired / non-renewing certificate |
| `deploy-ipsum.sh` / `setup-fail2ban.sh` | Medium (auto-rollback / ignoreip safeguards) | Hardening missing |
| `awg-tool.py` | Medium | Optional AmneziaWG create / rotate / render |
| `deploy-cert-hook.sh` | Low | legacy **certbot**-only sync hook |

**Always backup** before DB-touching scripts:

```bash
sudo cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +%F).db
```

## Hysteria isolation test (mandatory for JSON 500)

```bash
# 1. Note Hysteria inbound id
sudo sqlite3 /etc/x-ui/x-ui.db \
  "SELECT id,remark,enable FROM inbounds WHERE protocol='hysteria';"

# 2. Disable via API or panel
# 3. sudo x-ui restart
# 4. curl JSON sub URL → expect 200
# 5. sudo python3 scripts/fix-hysteria-stream.py
# 6. Re-enable Hysteria, restart, re-test
```

## Quick commands

```bash
sudo bash scripts/audit-server.sh        # read-only picture first
sudo bash scripts/check-cert-expiry.sh
sudo python3 scripts/loopback-test.py
sudo x-ui status
sudo tail -30 /var/log/x-ui/3xui.log
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
ss -tlnp | grep -E '8443|8444|2053|2096'
ss -ulnp | grep 36712
```

## When to escalate to full reinstall

- Corrupted `x-ui.db` with no backup
- Multiple manual binary patches (violates skill rules — restore from clean install)
- Compromised panel (rotate all credentials — `secrets-management.md`)

## Related

- `references/diagnostics.md` — HTTP codes, SQLite queries
- `references/gotchas.md` — Hysteria version, Reality, nginx 443
- `references/execution-order.md` — only for fresh setup