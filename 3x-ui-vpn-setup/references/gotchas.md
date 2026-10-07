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
---

## Added in 1.3 — traps found in production

### Certificates: silent expiry
acme.sh from 3X-UI issues in standalone mode; nginx owns :80 → renewal never succeeds → the cert expires ~90 days later and
every TLS profile + the subscription dies while Reality keeps working. Fix: `scripts/deploy-acme-renewal.sh`; detect:
`scripts/check-cert-expiry.sh`. Details: `cert-renewal-nginx.md`.

### Subscription links ignore the inbound: the `hosts` table
Subscription/links take `security`, `sni`, address, port, `fingerprint`, … from a **per-host override** row (table `hosts`,
API `/panel/api/hosts/*`), not from the inbound's `streamSettings`. Changing an inbound (e.g. TLS → Reality) via the API leaves the
old `security=tls&sni=<domain>` in the links → clients cannot connect although the server is fine.
After ANY change of security/SNI/port/path: `SELECT * FROM hosts WHERE inbound_id=<id>;` and update it with
`POST /panel/api/hosts/update/<groupId>` (full object from `GET hosts/get/<groupId>`). `audit-server.sh`/`verify-server.sh`
flag mismatches.

### Settings edited in SQLite are served stale
`UPDATE settings SET value=… WHERE key='subRoutingRules'` (same for other `sub*` keys) is not picked up until `systemctl restart x-ui`.
Verify by decoding the `Routing:` response header (`happ-routing.md`).

### XHTTP + REALITY
Failed on Xray 26.7.28 (client dials, then `failed to GET …/<path>/<uuid>: EOF`); not re-tested on 26.9.30. XHTTP stays on TLS here.
TCP + REALITY + vision is the working Reality form. Test a new combination with `loopback-test.py` **before** publishing it in the subscription.

### TLS inbounds expose the real certificate on odd ports
TCP-TLS (8444) and XHTTP-TLS (2053) present the CDN certificate on non-standard ports: a port+certificate scan links them to the
CDN name and to each other ("proxy host" pattern). Reality ports present the borrowed site's certificate instead. Converting a TLS inbound to
Reality is the mitigation where the protocol allows it (not XHTTP, see above). Use a **different borrowed SNI per Reality port**.

### nginx
* `sites-enabled/<name>` must be a **symlink** to `sites-available/<name>`. A copy silently ignores later edits (we edited
  `sites-available`, saw no effect, and misdiagnosed a reload problem). Check with `ls -l /etc/nginx/sites-enabled/`.
* Backups placed inside `sites-enabled/` are loaded as server blocks → `duplicate default server`. Keep backups elsewhere.
* The port-80 server needs a `location ^~ /.well-known/acme-challenge/` *and* the redirect inside `location /` — a server-level `return 301`
  runs first and hides the location (renewal breaks).
* Verify what is really loaded: `nginx -T | grep -nE 'listen|server_name'`.

### SSH / sudo
* Ubuntu 26.04 `sudo-rs` ignores `sudo -E` ("preserving the entire environment is not supported") → scripts lose their variables.
  Use `sudo env "VAR=value" bash script.sh`.
* `pkill -f <text>` inside an SSH command kills the SSH session itself (the command text matches). Kill by PID.
* A locked password (`passwd -l`) + sudo that needs a password never works; use key login + `NOPASSWD` (`agent-access-hygiene.md`).
* Account expiry (`chage -E`) ends logins with `Your account has expired`. Renew as root from a local shell on the server.
* `sshd_config.d`: global options above `Match` blocks; `DebianBanner` is invalid inside `Match`.

### Panel update (3.7 → 3.9)
* The updater restarts the panel; one run logged `Error initializing database: duplicate column name: user_agent` (the migration
  collided with itself) and systemd restarted it successfully (`NRestarts=1`). Check the unit really ended up `active` and all inbounds exist.
* Back up `x-ui.db` **and** the binaries (`/usr/local/x-ui/x-ui`, `bin/xray-linux-amd64`) before updating — a migration failure stops the panel from starting.
* After the update test with `loopback-test.py` — `xray -test` accepts configs that real clients cannot use.

### Client indicators
`n/a`/`-1` in a client's list is unreliable (`testing-methods.md`). A client build may show `n/a` for a working Reality profile while another client
connects. Test on the server, then with another client, then from another network — before reverting any server change.

### Adding an AmneziaWG inbound restarts Xray
A one-second blip for all profiles (log: "forcing a full restart"). Not an outage.
