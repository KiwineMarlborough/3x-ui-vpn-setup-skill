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
---

## Added in 1.3 — read before creating or changing inbounds

**1. Sync the `hosts` row after every change.** Subscription links take `security`/`sni`/address/port/path/fingerprint from the
per-host override table, not from the inbound (`gotchas.md`). After creating or editing an inbound:

```bash
sudo sqlite3 /etc/x-ui/x-ui.db "SELECT id,inbound_id,address,port,security,sni,path FROM hosts ORDER BY inbound_id;"
# fix through the API: GET /panel/api/hosts/get/<groupId>, edit, POST /panel/api/hosts/update/<groupId>
```
`audit-server.sh` flags rows that disagree with the inbound.

**2. Check the *effective* flow, not the one you remember.** Per-inbound flow overrides live in `client_inbounds.flow_override`
and the client's own `flow` field. In the originating install the "TCP/Podkop" inbound turned out to carry
`xtls-rprx-vision` although the notes said it was empty (cause unknown — possibly a panel migration):
```bash
sudo sqlite3 /etc/x-ui/x-ui.db "SELECT ci.inbound_id, c.email, ci.flow_override FROM client_inbounds ci JOIN clients c ON c.id=ci.client_id;"
```
If a router client (Podkop/Forkop/Passwall) needs an empty flow, set it and re-test that client — don't assume.

**3. Reality ports: one borrowed SNI per port.** Do not reuse the same `dest`/SNI/keys on several ports; they would correlate.
Validate every SNI (`reality-sni.md`: TLS 1.3, reachable from the VPS, large CDN-fronted site).

**4. TLS inbounds (TCP 8444, XHTTP 2053) present the CDN certificate on non-standard ports** — a recognisable pattern
(`rkn-and-blocking.md`). TCP can be converted to Reality (works, verified). **XHTTP + Reality failed on Xray 26.7.28** — keep XHTTP on TLS
unless a loopback test passes on your core version (`testing-methods.md`). Both TLS inbounds die when the certificate expires.

**5. Always run `scripts/loopback-test.py` after creating/changing an inbound** — it proves the profile with a real handshake before
a client ever sees it.

**6. Optional 5th profile: AmneziaWG 3.1** (UDP, `amneziawg.md`). It never appears in the subscription (so it does not change the
"3× vless + 1× hysteria2" count that `verify-server.sh` expects).

**7. `inbounds/update` (3.9)** no longer changes clients or the inbound's enable flag (`api-reference.md`).
