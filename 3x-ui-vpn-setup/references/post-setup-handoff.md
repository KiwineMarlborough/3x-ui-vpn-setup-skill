# Post-Setup Handoff (give to user)

Agent must deliver this checklist when setup passes `verify-server.sh`. Customise the bracketed parts.

## Credentials (user stores locally — NOT in git)

| Item | Where |
|------|-------|
| Panel URL | `https://<panel-host>:<port>/<webBasePath>/` — **open only through the SSH tunnel** (below) |
| Panel login / password | password manager |
| API token | password manager |
| SSH key / agent account | `~/.ssh/...`; the agent account's expiry/removal date |
| Subscription URL | below |

## How to open the panel (it is closed to the internet by design)

1. hosts entry on your PC: `127.0.0.1 <panel-host>` (Windows: `C:\Windows\System32\drivers\etc\hosts`, as Administrator).
2. Tunnel: `ssh -i <key> -L <port>:127.0.0.1:<port> <user>@<vps-ip>` (or MobaXterm → Tunneling → Local port forwarding:
   forwarded port `<port>`, remote `127.0.0.1:<port>`, SSH server `<vps-ip>:22`). Keep it open.
3. Browser → `https://<panel-host>:<port>/<webBasePath>/` → accept the self-signed certificate warning.
   `localhost`/IP gives **403** — that is the protection working. Details: `panel-tunnel-access.md`.

## Subscription URLs

```
https://<cdn-domain>:2096/<subPath>/<full-36-char-sub_id>
https://<cdn-domain>:2096/<jsonPath>/<full-36-char-sub_id>
```
Truncated `sub_id` → 404.

## Client setup (Happ Plus)

1. Add the subscription URL, pull down to refresh.
2. Enable the routing profile if prompted (SplitRU).
3. Test **real traffic** on Reality first; the latency column may show `n/a` while it works (`testing-methods.md`).

## Profiles delivered

| Name | Port | Protocol |
|------|------|----------|
| *-Reality-Vision | 8443 | VLESS Reality |
| *-TCP-Podkop | 8444 | VLESS TLS |
| *-XHTTP-Mobile | 2053 | VLESS XHTTP (TLS) |
| *-Hysteria2 | 36712/udp | hysteria2 |
| *-AWG-3.1 (optional) | `<udp port>` | AmneziaWG 3.1 — **not in the subscription**, `.conf`/QR per device |

## Reality params (manual import)

```
SNI: <borrowed-sni>   Public key: <from panel>   Short ID: <from panel>   Fingerprint: firefox   Flow: xtls-rprx-vision
```

## What was hardened (tell the user)

* Panel: no public DNS record, closed port, tunnel access.
* IPsum blocklist (≈17k known-bad IPs dropped, daily refresh) + Fail2Ban on SSH. **Your own IPs are whitelisted:** `<ADMIN_IPS>`;
  if you or a client lose access from one network only, send the public IP — a false positive is fixed by whitelisting.
* Certificate renews itself (acme.sh webroot, deploy hook); next renewal ≈ `<date>`; expiry check runs daily.
* Accounts on the server: `<list>`; the agent's account `<name>` expires/gets removed on `<date>`.

## Verification the user can run

* Site through the VPN shows the VPS country; `.ru` sites go direct with split routing.
* The panel is **not** reachable without the tunnel.
* `sudo bash scripts/verify-server.sh` (needs the skill scripts on the server or ask the agent).

## Maintenance reminders

* Monthly: check the 3X-UI release notes → backup → update → `loopback-test.py` + `verify-server.sh` (`backup-update.md`).
* Certificate: automatic, but check `acme.sh --list` / `check-cert-expiry.sh` when you log in.
* Backup `x-ui.db` before panel updates; keep off-server copies encrypted.
* If the JSON subscription returns 500: `gotchas.md`. If one profile "doesn't work": `testing-methods.md` first.
* End of engagement: remove the agent account and its sudo rule (`agent-access-hygiene.md`), rotate secrets it saw.
