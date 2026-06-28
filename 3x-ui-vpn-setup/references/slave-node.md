# Slave Node (optional second VPS)

Client-side Happ routing (`.ru` direct) ≠ server cascade. Slave gives **RU exit IP** for selected traffic.

## When to add

- Need Russian IP for banks / .ru services while abroad
- Want RU + DE profiles in one subscription

## Architecture

```
Client → DE Master (panel + cdn) → [optional] RU Slave outbound
```

## On Slave VPS

1. Install 3X-UI (this skill, simplified: 1–2 inbounds)
2. Create client + API token
3. Note: IP, panel port, `webBasePath`

## On Master

1. Panel → Nodes → Add Node (Slave API)
2. Link Slave inbounds to same or new client
3. Optional Xray routing on Master:
   - `geosite:category-ru` → outbound Slave
   - rest → direct

## vs Happ split routing

| | Happ routing | Slave cascade |
|--|--------------|---------------|
| Second VPS | No | Yes |
| RU IP for .ru | No (home IP direct) | Yes (RU VPS IP) |
| Complexity | Low | Medium |

Meridian-style split without Slave is enough for most personal use in Russia.