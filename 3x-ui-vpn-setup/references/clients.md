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