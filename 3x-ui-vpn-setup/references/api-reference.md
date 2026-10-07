# 3X-UI API Reference (verified against 3X-UI 3.9.0)

All examples use placeholders — load real values from `.env.local`. **The panel documents itself:**
`GET $BASE/panel/api/openapi.json` (with the Bearer token) lists every route and method for *your* version —
check it first when something returns 404.

## Base URL and access

```bash
BASE="https://panel.<domain>:<port>/<webBasePath>"     # no trailing slash
TOKEN="<api-token>"                                    # Settings -> API tokens
R="--resolve panel.<domain>:<port>:127.0.0.1"          # calling from the server itself
curl -sk $R -H "Authorization: Bearer $TOKEN" "$BASE/panel/api/inbounds/list"
```

* `webDomain` is enforced: requests with another `Host` get **403**. From the server use `--resolve` (as above);
  from the admin PC through the tunnel use the hosts-file entry (`panel-tunnel-access.md`).
* Since 3.7 tokens can be scoped/expiring; an expired token returns 401-style `success:false`.
* **Reads are `GET`, writes are `POST`.** `PUT` does not exist (404). A wrong method also answers **404**, not 405.
  (`GET inbounds/get/{id}`, `GET hosts/get/{groupId}`; `POST inbounds/update/{id}`, `POST hosts/update/{groupId}`.)
  Responses: `{"success":bool,"msg":"…","obj":…}`.

## Endpoints used by this skill (3.9.0)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/panel/api/inbounds/list` · `/list/slim` · `/get/{id}` | read inbounds |
| POST | `/panel/api/inbounds/add` | create inbound (full payload) |
| POST | `/panel/api/inbounds/update/{id}` | update inbound (**see behaviour change below**) |
| POST | `/panel/api/inbounds/del/{id}` · `/bulkDel` | delete |
| POST | `/panel/api/inbounds/setEnable/{id}` | enable/disable an inbound, form field `enable=true\|false` (replaces old `on/off`) |
| POST | `/panel/api/clients/add` | create client **and attach to inbounds**: `{"client":{...},"inboundIds":[…]}` |
| POST | `/panel/api/clients/update/{email}` · `/del/{email}` · `/{email}/attach` · `/{email}/detach` | client lifecycle |
| GET | `/panel/api/clients/list` · `/get/{email}` · `/links/{email}` · `/subLinks/{subId}` | read clients / links |
| GET/POST | `/panel/api/hosts/list` · `get/{groupId}` · `byInbound/{id}` · `update/{groupId}` · `add` · `del/{groupId}` | **per-host overrides of subscription links** (see gotcha) |
| POST | `/panel/api/setting/all` · `/setting/update` | read / write panel settings (still POST) |
| GET | `/panel/api/server/status` · `/server/getDb` · `/server/logs/{count}` | status / DB download / logs |
| POST | `/panel/api/server/restartXrayService` · `/setting/restartPanel` | restarts |
| POST | `/panel/api/server/amneziawglogs/{count}` | AmneziaWG interface events + peers (`amneziawg.md`) |
| GET | `/panel/api/openapi.json` | the authoritative route list |

Removed/renamed vs. older versions (do not use): `inbound/add`, `inbound/update/{id}`, `inbound/del/{id}`,
`inbound/on|off/{id}`, `inbound/addClient`, `inbound/updateClient/{id}` (singular `inbound`, per-inbound client calls).

## Behaviour changes that bite

* **3.9.0: `inbounds/update` no longer changes the inbound's clients, their enable/expiry/quota/renewal fields, or the
  inbound's own `enable` flag.** Use the `clients/*` endpoints and `inbounds/setEnable/{id}`. Scripts that edited clients
  through an inbound update silently stop working.
* **Sending an inbound update:** pass the *full* object read from `GET inbounds/get/{id}` with only your change applied;
  the fields in practice: `id, remark, enable, expiryTime, trafficReset, trafficResetDay, listen, port, protocol, tag,
  shareAddrStrategy, shareAddr, disableFlow, settings, streamSettings, sniffing`. Read-only stat fields
  (`up/down/total/clientStats`) are ignored. `settings`/`streamSettings` may be nested objects (preferred) or JSON strings.
  An update **resets the inbound's traffic counters** (observed) and **may restart Xray**.
* Changing an inbound's `streamSettings.security` does **not** update the `hosts` row for that inbound; the subscription
  keeps emitting the old `security=`/`sni=` → update `hosts` too (`gotchas.md`).
* **Settings written directly to SQLite (`UPDATE settings …`) are not seen until `x-ui` restarts** — the panel caches them
  (observed for `subRoutingRules`). Prefer `setting/update`; after a DB edit run `systemctl restart x-ui` and verify
  the subscription response.
* 3.8.5+: saving/enabling an inbound whose port collides is refused with the owner named (this protects Xray from a crash loop).

## setting/update gotcha (unchanged)

1. `POST setting/all` → take the entire `obj`
2. Modify only what you need
3. Remove every key starting with `has` (e.g. `hasSubEncrypt`)
4. `POST setting/update` with the **complete** object — a partial object can be rejected or wipe fields

```python
obj = call("POST", "/panel/api/setting/all", {})["obj"]
for k in [k for k in obj if k.startswith("has")]: obj.pop(k)
obj["subEncrypt"] = False
call("POST", "/panel/api/setting/update", obj)
```
See `scripts/apply-routing.py`, `scripts/set-sub-paths.py`. Settings are also available read-only via SQLite
(`SELECT key,value FROM settings`).

## Examples

```bash
# enable/disable an inbound (Hysteria isolation test). The panel UI sends a FORM field, not JSON:
curl -sk $R -H "Authorization: Bearer $TOKEN" -X POST "$BASE/panel/api/inbounds/setEnable/5" -F enable=false
curl -sk $R -H "Authorization: Bearer $TOKEN" -X POST "$BASE/panel/api/inbounds/setEnable/5" -F enable=true
# (form encoding taken from the panel's own frontend code; not exercised live by the skill author — confirm with inbounds/get/5 .enable)
# add a client to inbound 2 (secrets are generated server-side when omitted; email must be unique)
curl -sk $R -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "$BASE/panel/api/clients/add" \
  -d '{"client":{"email":"user-phone","enable":true,"totalGB":0,"expiryTime":0,"limitIp":0,"comment":"phone"},"inboundIds":[2,3,4]}'
# read subscription-link overrides
curl -sk $R -H "Authorization: Bearer $TOKEN" "$BASE/panel/api/hosts/byInbound/2"
```
## Error responses

| Response | Meaning |
|----------|---------|
| 404, empty body | wrong **method** or path (GET vs POST!), or wrong `webBasePath` |
| 403 HTML | wrong `Host` (IP / localhost instead of `webDomain`) |
| `success:false` | validation (message names the field/port owner) |
| TLS handshake error | panel cert vs `webDomain` mismatch / expired |

## When the API is unavailable

Fallback to SQLite (back up first, restart `x-ui` afterwards): `sudo cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +%F).db`.
Inbound JSON edits in the DB work but prefer the API + the repair scripts.

## Subscription (no token)

```bash
curl -skI "https://cdn.<domain>:2096/<subPath>/<sub_id>" ; curl -skI "https://cdn.<domain>:2096/<subJsonPath>/<sub_id>"
```

## Related

`panel-settings.md` · `panel-tunnel-access.md` · `gotchas.md` · `repair-only.md` · `scripts/audit-server.sh`
