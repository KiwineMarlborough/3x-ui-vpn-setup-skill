# Panel Reachable Only Through an SSH Tunnel (default)

The admin panel is the most scannable, most attack-worthy part of the server and the easiest thing for a
censor or botnet to fingerprint. **Default of this skill: the panel is not reachable from the internet at all.**
You open it through an SSH tunnel when you need it.

## Why

* A publicly resolvable panel hostname + a Let's Encrypt certificate for it is **permanently listed in public
  Certificate Transparency logs** (crt.sh and others). A name like `panel…` tells everyone what it is, and the
  hostname is a stable pointer from your "boring CDN domain" to the same IP. Panel discovery was the likely
  cause of one real IP/domain block in the project this skill came from.
* Hiding the URL path (`webBasePath`) does not hide the login page's fingerprint (response headers, favicon,
  page body); internet-wide scanners index panels regardless of path.
* A closed port cannot be brute-forced, and an unauthenticated vulnerability in the panel is unreachable.

## Design

| Item | Setting |
|------|---------|
| Public DNS for the panel name | **none** (do not create the record; delete it if it exists) |
| Panel certificate | self-signed, no public CA (`cert-renewal-nginx.md`) |
| `webDomain` | keep set to the panel hostname — the panel answers **403** for any other `Host` header |
| UFW | `ufw deny <panel-port>/tcp comment "3xui panel - SSH tunnel only"` (explicit, self-documenting) |
| Access | `ssh -L <port>:127.0.0.1:<port>` + `hosts` entry on the admin machine |

SSH forwarding delivers to the server's loopback, so UFW rules for the public interface do not apply to the tunnel.
The panel process may keep listening on `*` — the firewall closes it. (Binding `webListen=127.0.0.1` is an extra
option; it was not used/tested in the project this skill came from.)

## Open the panel (admin machine)

1. **hosts entry** (once; Windows: `C:\Windows\System32\drivers\etc\hosts`, edit as Administrator; Linux/macOS: `/etc/hosts`):
   ```
   127.0.0.1 panel.vpn.example.com
   ```
   Windows (admin PowerShell): `Add-Content "$env:SystemRoot\System32\drivers\etc\hosts" "127.0.0.1 panel.vpn.example.com"` then `ipconfig /flushdns`.
2. **Tunnel** (keep it open while you work):
   ```bash
   ssh -i ~/.ssh/<key> -L 29800:127.0.0.1:29800 <user>@<vps-ip>
   ```
   MobaXterm: *Tunneling → New SSH tunnel → Local port forwarding*: forwarded port `29800`, remote server
   `127.0.0.1`, remote port `29800`, SSH server `<vps-ip>:22`. The forward is configured **from the admin PC**,
   not by typing a command inside a session that is already on the server.
3. **Browser:** `https://panel.vpn.example.com:29800/<webBasePath>/` — accept the self-signed warning.

Direction, in one line: *local port on your PC → through SSH → the server's own 127.0.0.1:29800*.

## Expected behaviours (not bugs)

| What you see | Meaning |
|--------------|---------|
| `https://localhost:29800/...` or `127.0.0.1` → **403** | tunnel works; the panel refuses any host except `webDomain` |
| hostname resolves to `198.18.x.x` | your VPN client's fake-IP DNS answered; the hosts entry is missing/not applied |
| Timeout without the tunnel | correct: the port is closed to the world |
| Chromium-based browser has no "proceed" button | use another browser, `thisisunsafe`, or trust the cert |

## Automation on the server

API calls from the server: `curl -sk --resolve panel.vpn.example.com:29800:127.0.0.1 -H "Authorization: Bearer $TOKEN" https://panel.vpn.example.com:29800/<webBasePath>/panel/api/...`
(`api-reference.md`).

## Verify from outside

```bash
# must time out / refuse (run from a machine that is NOT the server)
curl -sk -m 8 https://<vps-ip>:29800/ ; echo $?
sudo ufw status | grep <panel-port>        # DENY present, no ALLOW
```
`verify-server.sh` warns if the panel port is ALLOWED while `PANEL_ACCESS=tunnel`.

## If you want public panel access anyway

`PANEL_ACCESS=public`: keep the panel hostname in DNS, issue a certificate, allow the port, enable 2FA, restrict
by source IP in UFW (`ufw allow from <admin-ip> to any port <port> proto tcp`). Expect it to be discovered.

## Related

`panel-security.md` · `dns-setup.md` · `cert-renewal-nginx.md` · `rkn-and-blocking.md`
