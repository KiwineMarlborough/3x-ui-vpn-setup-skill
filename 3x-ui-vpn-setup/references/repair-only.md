# Repair-Only Mode

Use when a 3X-UI server **already exists** and something broke. Do **not** rerun full install.

## Intake (repair)

1. SSH access confirmed
2. `sudo x-ui status`
3. `scripts/audit-server.sh` (read-only)
4. User symptom in one line

## Decision tree

```
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
├─ 403 by IP → expected; use panel.<domain>
├─ TLS error → webCertFile vs webDomain (panel-security.md)
└─ timeout → UFW / webListen 127.0.0.1 without SSH tunnel

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
| `deploy-cert-hook.sh` | Low | nginx TLS stale after LE renew |

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