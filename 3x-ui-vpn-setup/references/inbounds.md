# Inbound Recipes (3X-UI Panel)

Exact settings for four production profiles. Replace `<CC>`, `<cdn-domain>`, `<sni>`.

**Global on all inbounds:**
- Protocol: VLESS (except Hysteria)
- `shareAddr`: `<cdn-domain>`
- `share strategy`: custom
- Sniffing: enabled, `destOverride`: `http`, `tls`, `quic`, `fakedns`

---

## 1. `{CC}-Reality-Vision` — PRIMARY

| Field | Value |
|-------|-------|
| Port | `8443` |
| Protocol | VLESS |
| Security | **Reality** |
| Network | TCP |
| Flow (client default) | `xtls-rprx-vision` |

**Reality settings:**
```
serverName (SNI):  <sni>          # borrowed site, NOT your VPN domain
dest:              <sni>:443
fingerprint:       firefox         # or chrome
show:              false
xver:              0
```

Generate keypair in panel → save `publicKey`, pick `shortId` (e.g. 8 hex chars).

**client_inbounds override** for this inbound:
- `flow`: `xtls-rprx-vision`

**Verify SNI:** `references/reality-sni.md`

---

## 2. `{CC}-TCP-Podkop`

| Field | Value |
|-------|-------|
| Port | `8444` |
| Security | TLS |
| Network | TCP |
| Flow | **empty** (critical for Podkop) |

**TLS:**
- Cert: LE for `<cdn-domain>`
- ALPN: `h2`, `http/1.1`

**client_inbounds override:**
- `flow`: `` (empty string)

**client settings DB:** `UPDATE clients SET flow='' WHERE email='...'` if panel re-adds flow.

---

## 3. `{CC}-XHTTP-Mobile`

| Field | Value |
|-------|-------|
| Port | `2053` |
| Security | TLS |
| Network | **XHTTP** |

**XHTTP (typical mobile bypass):**
```
path:     /api/v2/uploads    # or /cdn/v2/data — pick one, stay consistent
mode:     packet-up
host:     <cdn-domain>
alpn:     h2, http/1.1
```

**TLS:** same cert as CDN domain.

Flow: empty for this inbound unless client requires vision (usually empty for XHTTP).

---

## 4. `{CC}-Hysteria2`

| Field | Value |
|-------|-------|
| Port | `36712` |
| Protocol | **hysteria** (panel may label Hysteria2) |
| Network | `hysteria` |

**Inbound settings:**
```json
{ "version": 2 }
```

**stream_settings:** copy `templates/hysteria-stream-settings.json` exactly.

**Client credential:** field `auth` (random 32+ char string), NOT `password` or uuid.

**Share link format:**
```
hysteria2://<auth>@<cdn-domain>:36712?insecure=0&sni=<cdn-domain>&alpn=h3#ProfileName
```

Enable **last** — after other three work. See `references/execution-order.md`.

---

## Disabled: VLESS on 443

Do **not** enable if nginx CDN fallback uses 443. See `references/nginx-fallback.md`.

---

## Profile names with flag (optional)

Remark examples: `🇩🇪 DE-Reality-Vision`, `🇩🇪 DE-XHTTP-Mobile`

Happ shows remark in subscription list.

---

## SQLite quick fixes

```bash
# Podkop flow empty
sudo sqlite3 /etc/x-ui/x-ui.db \
  "UPDATE clients SET flow='' WHERE email='user-phone@project';"

# Reality flow on client_inbounds (if stored per-inbound in settings JSON)
# Prefer panel API; inspect: SELECT settings FROM inbounds WHERE port=8443;
```