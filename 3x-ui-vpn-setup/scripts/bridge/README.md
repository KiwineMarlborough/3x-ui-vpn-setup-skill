# scripts/bridge — country bridge toolkit

Run **on the 3X-UI hub** (the panel listens on 127.0.0.1). Secrets only via the environment, never in files:

```bash
sudo env XUI_TOKEN=... XUI_BASE=/<webBasePath> XUI_HOST=<webDomain> python3 route_test.py agent@example.com example.org
```

(Ubuntu 26.04 sudo-rs ignores `sudo -E`: pass variables with `env`.) Design and pitfalls: `references/country-bridge.md`.

| Script | What it does | Changes the server? |
|---|---|---|
| `xui.py` | tiny API client used by the others | — |
| `parse_sub.py` | preview a subscription URL (stdin) without saving | no |
| `link_to_outbound.py` | one share link (vless / hysteria2, stdin) → Xray outbound JSON | no |
| `test_outbound.py` | live check of ONE outbound before use: exit IP/country/sites (temporary loopback client) | no |
| `route_test.py` | which outbound/balancer the running core picks for user+domain | no |
| `add_sub.py` | create an outbound subscription (URL, tag prefix, interval) | yes |
| `add_client.py` | create a client | yes |
| `add_agent.py` | access for an agent: client + Bridge inbounds (`--only`, `--all`); prints `SUBURL=` (**secret**) | yes |
| `add_bridge_profile.py` | new subscription line: inbound + `hosts` row + clients + rule → outbound/balancer; restarts Xray | yes |
| `add_user_rule.py` | rule "user → outbound" (all traffic or a domain list) | yes |
| `set_profile_balancer.py` | profile → balancer by tag prefix (fail-closed by default; prefer `sync_country_balancers.py`) | yes |
| `sync_country_balancers.py` | country pools by FLAG with live exit-country check; copies `ctry-<CC>-<n>`; idempotent | only on change |
| `deploy_country_sync.sh` | installs the hourly systemd timer for the sync (token in a root-only file) | yes |
| `failover_test.py` | live failover test: temporary iptables DROP to the tier-1 node, always removed | temporary |
| `deploy_exit_node.sh` | separate Xray exit node on a VDS (own unit/port, port limited to the hub IP) | yes (on the VDS) |
| `sub_to_xray.py` | **agent side**: subscription → Xray client config with local SOCKS5/HTTP (stdlib only) | no |

Order for a new exit: `link_to_outbound` → `test_outbound` → DB backup → `add_bridge_profile` → `ufw allow` → real handshake as each user.
After any balancer change: verify the exit IP of every profile for every user (not only `xray -test`).
