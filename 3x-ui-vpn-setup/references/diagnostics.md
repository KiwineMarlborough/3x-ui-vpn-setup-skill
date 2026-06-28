# Diagnostics Cheat Sheet

## Automated verify

```bash
export CDN_DOMAIN=cdn.vpn.example.com
export SUB_PATH=/xK9mP2qR/
export JSON_PATH=/j4nR8wLz3k/
export SUB_ID=<full-uuid>
sudo bash scripts/verify-server.sh
```

## Service status

```bash
sudo x-ui status
sudo tail -50 /var/log/x-ui/3xui.log
sudo systemctl status nginx
```

## Xray config test

```bash
sudo /usr/local/x-ui/bin/xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json
```

## Listening ports

```bash
ss -tlnp | grep -E '8443|8444|2053|2096|29800|443|80'
ss -ulnp | grep 36712
sudo ufw status numbered
```

## Subscription

```bash
SUB='https://cdn.vpn.example.com:2096/<subPath>/<sub_id>'
curl -sk -o /dev/null -w 'sub %{http_code}\n' "$SUB"
curl -sk -o /dev/null -w 'json %{http_code}\n' "https://cdn.vpn.example.com:2096/<jsonPath>/<sub_id>"
curl -skI "$SUB" | grep -iE 'routing|http'
```

## Read-only audit

```bash
export CDN_DOMAIN=cdn.vpn.example.com SUB_ID=<uuid>
bash scripts/audit-server.sh
```

## SQLite quick queries

```bash
sudo sqlite3 /etc/x-ui/x-ui.db \
  'SELECT id,remark,port,protocol,enable FROM inbounds ORDER BY id;'

sudo sqlite3 /etc/x-ui/x-ui.db \
  'SELECT stream_settings FROM inbounds WHERE protocol="hysteria" OR remark LIKE "%Hysteria%";'
```

## Common HTTP codes

| Code | Meaning |
|------|---------|
| 404 sub | Wrong path or truncated sub_id |
| 500 json | Hysteria stream_settings shape |
| 403 panel | webDomain mismatch (access by IP) |

## Decision tree

```
Profiles don't connect
├─ xray -test fails → fix Hysteria version / stream (gotchas.md)
├─ ports not listening → x-ui restart, check enable flags
├─ sub 404 → sub_id / custom paths
└─ sub 200 but client fails → client profile / flow / Reality params

JSON 500 only
└─ hysteriaSettings + version 2 in stream
```