# Slave Node (optional second VPS)

Client-side Happ routing (`.ru` direct) ≠ server cascade. Slave gives **RU exit IP** for selected traffic.

## When to add

- Need Russian IP for banks / .ru services while abroad (not home IP)
- Want RU + DE profiles in one subscription
- Master already stable (`verify-server.sh` passes)

## Architecture

```
Client → DE Master (panel + cdn + routing) → outbound tag → RU Slave Xray
```

## On Slave VPS

1. Run skill phases 1–10 **simplified**:
   - 1–2 inbounds only (e.g. Reality 8443 + TCP 8444)
   - Same or separate CDN domain (or IP:port only for node link)
2. Panel → create API token on Slave
3. Record: Slave IP, panel port, `webBasePath`, token

```bash
# Slave verify
export SUB_ID=<slave-client-uuid>
bash scripts/audit-server.sh
```

## On Master — add node (panel UI)

1. Panel → **Nodes** → Add Node
2. Fields:
   - Name: `RU-Slave`
   - Address: `<slave-ip>`
   - Port: panel API port (e.g. `29800`)
   - API path: `/<webBasePath>/`
   - Token: Slave API token
3. Test connection → enable node

## On Master — link outbound

1. Panel → Outbounds (or Xray routing section per 3X-UI version)
2. Add outbound pointing to Slave node
3. Routing rule example:

```
geosite:category-ru → outbound: ru-slave
default → direct or block
```

Exact UI varies by 3X-UI version — inspect generated `config.json` after save:

```bash
sudo grep -A2 'category-ru' /usr/local/x-ui/bin/config.json
```

## API approach (when UI insufficient)

```bash
# Master: list nodes
curl -sk $R -H "Authorization: Bearer $MASTER_TOKEN" \
  -X GET "$MASTER_BASE/panel/api/..." 
```

Paths differ by version — capture from browser Network tab during manual add, document in issue/PR.

## Subscription presentation

Options:

- **Single sub on Master** — routing sends .ru to Slave outbound (transparent)
- **Dual profiles** — DE + RU inbounds on Master linked to Slave (advanced)

Most users: server-side routing on Master, one Happ subscription URL unchanged.

## vs Happ split routing

| | Happ routing | Slave cascade |
|--|--------------|---------------|
| Second VPS | No | Yes |
| RU traffic exit IP | Home ISP (direct) | RU VPS IP |
| Complexity | Low | Medium |
| Cost | 1 VPS | 2 VPS |

Happ SplitRU is enough for most personal use in Russia.

## Security

- Slave API token — password manager only
- Restrict Slave panel with `webDomain` + UFW
- Do not expose Slave panel publicly if unused

## Related

- `references/rkn-and-blocking.md`
- `references/multi-user.md`
- `references/api-reference.md`