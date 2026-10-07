# Client Apps

## Happ Plus (iOS) — primary

- Subscription URL import
- Pull refresh for routing updates
- Routing profile from `Routing` header (SplitHome / SplitRU / GlobalVPN)
- Latency `-1` on Reality may still work — test real traffic

## v2rayNG / Streisand (Android)

- Same subscription URL
- May ignore Happ routing — use app rules or full tunnel template
- Reality: enable `flow=xtls-rprx-vision`

## OpenWrt / Passwall / ShellCrash

- Prefer TCP 8444 or Reality 8443
- Skip XHTTP/Hysteria if firmware old
- Separate `user-router@` with 2 inbounds only

## Desktop (Hiddify, Nekoray)

- JSON sub URL sometimes easier
- Import all 4 profiles

## Router vs phone users

| Device | User | Inbounds |
|--------|------|----------|
| Phone | user-phone@ | all 4 |
| Router | user-router@ | 8443 + 8444 |

See `post-setup-handoff.md` for URLs.
## Added in 1.3

* **Happ latency column** can show `n/a` for a working Reality profile on some builds/networks. Judge by real traffic, then by
  another client on the same PC, then by another network (`testing-methods.md`).
* **Throne** (desktop, Xray-based): all four profile types tested OK in the originating project; a good second opinion client.
* **Happ routing (SplitRU) is a Happ feature** — it is delivered in the subscription header and applies only inside Happ.
  It does not affect AmneziaVPN/AmneziaWG or an OpenWrt tunnel.
* **AmneziaVPN / AmneziaWG apps** (iOS/Android/desktop): import the `.conf`/QR/`vpn://` for the optional AWG inbound (`amneziawg.md`).
  Use the latest version for 3.1 fields.
* **OpenWrt + Podkop/Forkop:** for the VLESS profiles use TCP 8444 / Reality 8443; for AWG install an AWG 3.1 package and point
  the policy tool at the AWG interface (unverified for Forkop). Watch `AllowedIPs = 0.0.0.0/0` hijacking the default route.
* **Browsers for the panel:** a Chromium-based browser may refuse the self-signed panel certificate without a "proceed" option;
  use another browser or trust the certificate (`panel-tunnel-access.md`).
