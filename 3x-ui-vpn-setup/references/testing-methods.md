# Reliable Testing — what proves a profile works (and what does not)

A client app's latency column is **not evidence** in either direction:

* Reality profiles often show `n/a`/`-1` while working (a documented quirk; one Happ desktop build showed `n/a`
  for a perfectly working Reality profile while another client and the phone on mobile data connected fine).
* An expired certificate, a blocked IP and a wrong key all look the same in the list: "n/a".

Use evidence in this order (cheapest first). Do **not** change server config until step 1–3 point at the server.

## 1. Real handshake on the server itself — `scripts/loopback-test.py`

```bash
sudo python3 scripts/loopback-test.py                 # every enabled VLESS inbound
sudo python3 scripts/loopback-test.py --email user-phone --only 8443,8444
```
It reads uuid/flow/Reality keys/SNI/TLS name/XHTTP path from the panel DB, starts a temporary Xray **client**,
connects to `127.0.0.1:<port>` and fetches a URL through a local SOCKS port. `HTTP 200` = the inbound works end to end,
including certificate validity — with the network between you and the server taken out of the equation.
Failures print a hint (`certificate has expired`, `Reality handshake rejected`, …). Hysteria and AmneziaWG are skipped
(UDP/other clients); for AWG check `amneziawglogs` (peer endpoint + traffic, `amneziawg.md`).
Manual equivalent: build the client config yourself, `xray run -c client.json`, `curl --socks5-hostname 127.0.0.1:<p> https://example.com`.

Stop test processes with `kill <PID>`; **never `pkill -f <text>` inside a command sent over SSH** — the command line
contains that text, so it kills your own SSH session (exit 255, "connection reset").

## 2. Externally, without credentials

```bash
curl -s -m 10 https://cdn.vpn.example.com/ -o /dev/null -w '%{http_code} verify=%{ssl_verify_result}\n'   # no -k: strict TLS
echo | openssl s_client -connect <ip>:8443 -servername <reality-sni> | grep -E 'subject=|Protocol'   # Reality answers as the SNI site
timeout 6 bash -c '</dev/tcp/<ip>/<port>' && echo open                                              # plain TCP reachability
```
A Reality port answers the borrowed SNI's real certificate, and for any other SNI the borrowed site's behaviour — a good sign.

## 3. A different client, then a different network

If steps 1–2 pass but the user's client says `n/a`/fails:

1. **Another client app on the same machine** (Throne, v2rayN, Hiddify…) — if it works, the first client is the problem.
2. **Another network** (phone on mobile data vs home Wi‑Fi) — if only one network fails, it is that ISP/router, not the server.

Only then touch the server. (In the case behind this rule, hours went into reverting correct server changes while the real
cause was one client build.)

## 4. Verify the whole server — `scripts/verify-server.sh`

Fails on: inactive services, invalid Xray config, expired/near-expiry certificates (files **and** what is served),
missing IPsum table, still-armed rollback timer, inbound failing the real handshake, bad subscription. Warns on:
panel port open in UFW, `hosts` overrides disagreeing with inbounds, fail2ban inactive.

## Typical false alarms

| Looks like | Actually |
|------------|----------|
| `n/a` on Reality in one client | client quirk — step 1 shows HTTP 200 |
| All TLS profiles dead, Reality fine | expired certificate (`check-cert-expiry.sh`) |
| One client app can't open the panel URL | self-signed certificate; that browser hides "proceed" |
| Subscription link says `security=tls` after switching an inbound to Reality | stale `hosts` override (`gotchas.md`) |
| Subscription shows old routing after a DB edit | panel keeps settings in memory — `systemctl restart x-ui` |
| Test on a fresh inbound "fails" over SSH with exit 255 | `pkill -f` killed the SSH session (see above) |

## Related

`diagnostics.md` · `repair-only.md` · `gotchas.md` · `clients.md`
