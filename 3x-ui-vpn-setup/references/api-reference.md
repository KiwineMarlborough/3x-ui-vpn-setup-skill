# 3X-UI API Reference

Patterns for agents automating panel operations. All examples use placeholders — load real values from `.env.local`.

## Base URL

```
BASE="https://panel.<domain>:<port>/<webBasePath>"
TOKEN="<api-token-from-panel>"
```

When `webDomain` is set, curl from the **server** needs SNI resolve:

```bash
R='--resolve panel.<domain>:29800:127.0.0.1'
```

## Authentication

1. Panel → Settings → Create API token
2. Every request: `Authorization: Bearer $TOKEN`
3. Content-Type: `application/json` for POST bodies

Login API exists but prefer long-lived token for automation.

## Core endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/panel/api/setting/all` | Read all panel settings (`obj`) |
| POST | `/panel/api/setting/update` | Write settings (full `obj`, no `has*` keys) |
| GET | `/panel/api/inbounds/list` | List inbounds |
| POST | `/panel/api/inbound/add` | Create inbound |
| POST | `/panel/api/inbound/update/<id>` | Update inbound |
| POST | `/panel/api/inbound/del/<id>` | Delete inbound |
| POST | `/panel/api/inbound/on/<id>` | Enable inbound |
| POST | `/panel/api/inbound/off/<id>` | Disable inbound |
| GET | `/panel/api/inbound/get/<id>` | Get one inbound |
| POST | `/panel/api/inbound/addClient` | Add client to inbound |
| POST | `/panel/api/inbound/updateClient/<clientId>` | Update client |
| POST | `/panel/api/inbound/<id>/delClient/<clientId>` | Remove client |
| POST | `/panel/api/server/status` | Xray status |
| POST | `/panel/api/server/restartXrayService` | Restart Xray |

Exact paths may vary slightly by 3X-UI version — if 404, check panel Network tab while clicking UI actions.

## setting/update gotcha

**Always:**

1. `POST setting/all` → take entire `obj`
2. Modify needed fields only
3. Remove all keys starting with `has` (e.g. `hasSubEncrypt`)
4. `POST setting/update` with **complete** object

**Never** send partial JSON like `{"subEncrypt": false}` alone — panel may reject or wipe fields.

```python
obj = curl_json("POST", "/panel/api/setting/all", {})["obj"]
for k in list(obj.keys()):
    if k.startswith("has"):
        obj.pop(k, None)
obj["subEncrypt"] = False
curl_json("POST", "/panel/api/setting/update", obj)
```

See `scripts/apply-routing.py` and `scripts/set-sub-paths.py`.

## Example: read settings

```bash
curl -sk $R \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "$BASE/panel/api/setting/all" \
  -d '{}' | python3 -m json.tool
```

## Example: enable routing

Use `scripts/apply-routing.py` or:

```bash
python3 scripts/apply-routing.py
# env: PANEL_BASE, PANEL_TOKEN, ROUTING_TEMPLATE, PANEL_RESOLVE, ROUTING_NAME
```

## Example: list inbounds

```bash
curl -sk $R \
  -H "Authorization: Bearer $TOKEN" \
  -X GET "$BASE/panel/api/inbounds/list" | python3 -m json.tool
```

## Example: toggle inbound (Hysteria isolation test)

```bash
# Disable Hysteria inbound id=5
curl -sk $R -H "Authorization: Bearer $TOKEN" \
  -X POST "$BASE/panel/api/inbound/off/5" -d '{}'

# Re-enable
curl -sk $R -H "Authorization: Bearer $TOKEN" \
  -X POST "$BASE/panel/api/inbound/on/5" -d '{}'
```

Then `sudo x-ui restart` or `POST .../server/restartXrayService`.

## Example: add client

Payload shape depends on inbound protocol. Minimum VLESS client:

```json
{
  "id": 3,
  "settings": "{\"clients\":[{\"id\":\"<uuid>\",\"email\":\"user-phone@project\",\"enable\":true,\"expiryTime\":0,\"totalGB\":0,\"limitIp\":0,\"flow\":\"xtls-rprx-vision\"}]}"
}
```

Prefer panel UI for first client, then clone pattern via API. Podkop inbound: `flow` must be `""`.

## Error responses

| Response | Meaning |
|----------|---------|
| `success: false`, 401 | Bad/expired token |
| 403 HTML | Wrong host (IP vs `webDomain`) |
| TLS handshake error | Cert/domain mismatch |
| Empty `obj` | Token ok but path wrong (`webBasePath`) |

## When API is blocked

Fallback to SQLite on server (backup first):

```bash
sudo cp /etc/x-ui/x-ui.db /root/backups/x-ui-$(date +%F).db
sudo sqlite3 /etc/x-ui/x-ui.db "SELECT key,value FROM settings LIMIT 5;"
```

Inbound edits in DB are possible but prefer API + `scripts/fix-hysteria-stream.py` for stream JSON.

## Subscription (no API token)

Public endpoints on port 2096:

```bash
curl -skI "https://cdn.<domain>:2096/<subPath>/<sub_id>"
curl -skI "https://cdn.<domain>:2096/<subJsonPath>/<sub_id>"
```

## Related

- `references/panel-settings.md` — field dictionary
- `references/repair-only.md` — symptom → action
- `scripts/audit-server.sh` — read-only health without changes