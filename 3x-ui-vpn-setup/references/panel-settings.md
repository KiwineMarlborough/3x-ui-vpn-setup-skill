# Panel Settings Reference

Single source of truth for 3X-UI settings keys used by this skill. Values live in SQLite table `settings` and panel API `setting/all` → `obj`.

## Panel access

| Key | Purpose | Example |
|-----|---------|---------|
| `webPort` | Panel HTTPS port | `29800` |
| `webBasePath` | Secret URL prefix | `/a8Kx9mP2qR/` (random) |
| `webDomain` | Hostname lock — panel opens only via this domain | `panel.vpn.example.com` |
| `webListen` | Bind address | `0.0.0.0` or `127.0.0.1` (tunnel-only) |
| `webCertFile` | Panel TLS cert | `/root/cert/panel.vpn.example.com/fullchain.pem` |
| `webKeyFile` | Panel TLS key | `/root/cert/panel.vpn.example.com/privkey.pem` |

**403 by IP is correct** when `webDomain` is set. Access via `https://panel.<domain>:<port>/<webBasePath>/`.

## Subscription

| Key | Purpose | Production value |
|-----|---------|------------------|
| `subEnable` | Subscription service on | `true` |
| `subPort` | Subscription listener | `2096` |
| `subPath` | Custom plain sub path prefix | `/xK9mP2qR/` (random, trailing `/`) |
| `subJsonPath` | Custom JSON sub path prefix | `/j4nR8wLz3k/` |
| `subURI` | Full plain sub base URL | `https://cdn.<domain>:2096<xK9mP2qR/>` |
| `subJsonURI` | Full JSON sub base URL | `https://cdn.<domain>:2096<j4nR8wLz3k/>` |
| `subJsonEnable` | JSON subscription endpoint | `true` |
| `subEncrypt` | Base64-encrypt sub body | **`false`** (plain links) |
| `subUpdates` | Show update notices in sub | optional |

**Client URL format:**

```
https://<cdn-domain>:2096/<subPath><full-36-char-sub_id>
https://<cdn-domain>:2096/<subJsonPath><full-36-char-sub_id>
```

Truncated `sub_id` → HTTP 404. Old `/sub/` and `/json/` should 404 after migration.

## Happ routing (subscription)

| Key | Purpose |
|-----|---------|
| `subEnableRouting` | Inject routing into sub response |
| `subRoutingRules` | `happ://routing/onadd/<base64-json>` |
| `subRoutingProfileName` | Optional label (legacy; rules carry `Name`) |

After change: `x-ui restart`, client pull-refresh in Happ.

## Share / client links

Per-inbound in panel:

- `shareAddr` → CDN domain (not panel domain)
- Share strategy → **custom** (uses `subURI` paths)

## SQLite inspection

```bash
sudo sqlite3 /etc/x-ui/x-ui.db \
  "SELECT key, value FROM settings WHERE key IN (
    'webDomain','webPort','webBasePath','webListen',
    'webCertFile','webKeyFile',
    'subPath','subJsonPath','subURI','subJsonURI',
    'subJsonEnable','subEncrypt','subEnableRouting'
  ) ORDER BY key;"
```

## SQLite patch (when API update fails)

```bash
sudo cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak
sudo sqlite3 /etc/x-ui/x-ui.db <<'SQL'
UPDATE settings SET value='/xK9mP2qR/' WHERE key='subPath';
UPDATE settings SET value='/j4nR8wLz3k/' WHERE key='subJsonPath';
UPDATE settings SET value='https://cdn.vpn.example.com:2096/xK9mP2qR/' WHERE key='subURI';
UPDATE settings SET value='https://cdn.vpn.example.com:2096/j4nR8wLz3k/' WHERE key='subJsonURI';
UPDATE settings SET value='false' WHERE key='subEncrypt';
SQL
sudo x-ui restart
```

Prefer API via `scripts/set-sub-paths.py`.

## API update pattern

```bash
# 1. GET full object
ALL=$(curl -sk $R -H "Authorization: Bearer $TOKEN" \
  -X POST "$BASE/panel/api/setting/all" -d '{}')

# 2. Patch fields, strip has* keys
PATCHED=$(echo "$ALL" | python3 -c "
import sys, json
o = json.load(sys.stdin)['obj']
o['subEncrypt'] = False
o['subJsonEnable'] = True
[o.pop(k) for k in list(o.keys()) if k.startswith('has')]
print(json.dumps(o))
")

# 3. POST full object back
curl -sk $R -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "$BASE/panel/api/setting/update" -d "$PATCHED"
```

## Common misconfigurations

| Symptom | Check |
|---------|-------|
| Panel TLS error | `webCertFile` must match `webDomain` cert |
| Sub 404 | `subPath` + full `sub_id`; not old `/sub/` |
| Sub gibberish | `subEncrypt=true` — set `false` |
| JSON 500 | Hysteria stream — not a panel setting |
| Routing missing | `subEnableRouting` + `subRoutingRules`; restart `x-ui` |
| 403 panel | Access by domain; `webDomain` set |

## Related

- `references/api-reference.md` — endpoints
- `scripts/set-sub-paths.py` — automate sub paths
- `references/post-setup-handoff.md` — deliver URLs to user