# Multi-User Management

Separate clients for phone, router, and guests — independent revoke, stats, and limits.

## Why separate users

| Benefit | Explanation |
|---------|-------------|
| Revoke router | Disable `user-router@` without touching phone |
| `limitIp` | Router user: 1–2 IPs; phone: 0 (unlimited) |
| Traffic cap | `totalGB` per user for guests |
| Stats | Per-device usage in panel |

Speed and stealth are **unchanged** — same inbounds, different credentials.

## Recommended layout

| Email | Device | Inbounds | limitIp | totalGB |
|-------|--------|----------|---------|---------|
| `user-phone@project` | iPhone | all 4 | 0 | 0 |
| `user-router@project` | OpenWrt | 8443, 8444 | 2 | 0 |
| `user-guest@project` | Friend | 8443 | 3 | 50 |

Each user gets own UUID and `sub_id` → separate subscription URL.

## Create router user (panel)

1. Clients → Add client `user-router@project`
2. Assign inbounds: **Reality 8443** + **TCP 8444** only
3. Set `limitIp` = 2 (home + backup IP)
4. Podkop: run `fix-podkop-flow.py --email user-router`
5. Copy subscription URL with router's `sub_id`

## Revoke

```bash
# Panel: disable client or delete
# Or API: inbound/delClient
```

Router stops immediately; phone user unaffected.

## API fields (client object)

```json
{
  "email": "user-router@project",
  "enable": true,
  "expiryTime": 0,
  "totalGB": 0,
  "limitIp": 2,
  "flow": ""
}
```

`flow` empty for Podkop; `xtls-rprx-vision` only on Reality inbound attachment.

## Podkop admin access

When phone uses split routing (.ru direct):
- Route **panel subdomain** through VPN for admin
- **Do not** route bare VPS IP (VPN loop risk) — `panel-security.md`

## Subscription per user

```
https://cdn.<domain>:2096/<subPath><router-sub_id>
```

Different `sub_id` — do not share phone URL to router.

## Related

- `protocol-selection.md` — which inbounds per role
- `references/clients.md` — OpenWrt notes
- `scripts/fix-podkop-flow.py` — flow reset