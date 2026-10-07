# DNS Setup (Cloudflare and generic)

TLS and subscriptions need DNS that points to the VPS with the right proxy mode — and **fewer names are better**:
every hostname that ever gets a public certificate is permanently listed in Certificate Transparency logs.

## Records

| Host | Type | Value | Proxy | Notes |
|------|------|-------|-------|-------|
| `cdn` (VPN + subscription + decoy site) | A | `<vps-ip>` | **DNS only** (grey cloud) | the only record the VPN needs |
| ~~`panel`~~ | — | — | — | **do not create** (default `PANEL_ACCESS=tunnel`, `panel-tunnel-access.md`); delete it if it exists |

Pick unremarkable names (`cdn`, `static`, `assets`) — not `vpn`, `panel`, `proxy`, `xray`. The name is public forever.
Panel access without DNS: hosts-file entry on the admin machine + SSH tunnel. The panel keeps `webDomain` set to its
(non-public) hostname; it only needs to resolve **on the admin PC**.

If you must keep a public panel record (`PANEL_ACCESS=public`): A record, grey cloud, restrict the port by source IP in UFW.

## Where DNS lives

DNS is managed wherever the domain's **nameservers** point (registrar's DNS, Cloudflare, …). Editing records at the
registrar does nothing while the nameservers point to Cloudflare, and vice versa. Cloudflare's free plan hosts the
**whole zone** (you move the nameservers); individual records can still be proxied or DNS-only independently.

## Why the VPN hostname must stay DNS-only (grey cloud)

Cloudflare's proxy (orange cloud) terminates TLS at its edge and only forwards a fixed list of ports (check
Cloudflare's current "network ports" page; it includes 443/2053/2083/2087/2096/8443 for HTTPS, not 8444, no UDP):

* **Reality (8443) breaks**: Reality needs the *raw* ClientHello to reach your server; a TLS-terminating proxy destroys it.
* Ports outside the list (8444, UDP Hysteria2/AmneziaWG) simply do not exist behind the proxy.
* The subscription (2096) and XHTTP (2053) might pass, but WAF/bot rules can block client apps (the same way
  User-Agent filters behave on nginx).

So `cdn` (which serves VPN ports **and** the decoy site under one name) cannot be proxied as a whole.

**Idea, not implemented/tested by the skill author:** put the *decoy website only* on a **second hostname** (e.g. `www`) that
is proxied, keep `cdn` grey for VPN ports. That hides the origin IP from casual resolution of the decoy name without touching VPN
ports; it needs an origin certificate for that name and an extra nginx `server` block. Do not enable the orange cloud on the
shared VPN hostname "to hide the IP" — it breaks protocols.

## Cloudflare steps (grey-cloud setup)

1. Add the site (free plan) → scan/import records, compare with the registrar's zone (MX/TXT for mail!).
2. A record `cdn` → VPS IP → **DNS only**.
3. Change nameservers at the registrar to the two Cloudflare ones; wait for "Active".
4. SSL/TLS mode **Full (strict)** (irrelevant for grey-cloud records, required if you later proxy a decoy name).

## Propagation check

```bash
dig +short cdn.vpn.example.com A @8.8.8.8      # must return the VPS IP, not a Cloudflare anycast address
nslookup cdn.vpn.example.com
```
Wait 5–30 min after create; up to TTL after changes.

## Certificate timing

Issue the CDN certificate **after** DNS resolves, with webroot validation through nginx on port 80
(`cert-renewal-nginx.md`). Only the CDN name goes on the certificate.

## Migration cutover

1. Lower TTL to 300 s a day before. 2. Change the A record to the new VPS. 3. Wait TTL.
4. Re-issue the certificate on the new server (`deploy-acme-renewal.sh`). See `migration.md`.

## Related

`panel-tunnel-access.md` · `cert-renewal-nginx.md` · `nginx-fallback.md` · `rkn-and-blocking.md`
