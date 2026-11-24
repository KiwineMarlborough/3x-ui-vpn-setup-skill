# Country bridge — extra subscription lines that exit through another country (optional module)

Goal: one 3X-UI hub, one subscription, and extra **"Bridge" lines**. A client (or an AI agent on another server) picks a line and its
traffic exits from a chosen country: your own second VPS (for example a Russian exit for sites that block foreign IPs), nodes taken
from a third-party provider subscription, or a pool of such nodes with automatic failover.

Verified on 3X-UI 3.11.0 / Xray 26.11.9 / Ubuntu 26.04 hub, Ubuntu 24.04 exit VDS. Scripts: `scripts/bridge/` (see its README).
What is **not** verified is listed at the end — do not claim it.

## 1. The basic building block: one inbound per exit

```
client ──VLESS Reality──► hub inbound "BridgeXX" (own port) ──routing rule inboundTag→outbound──► exit node ──► Internet
```

- The client always speaks VLESS to the **hub**. The protocol between hub and exit (VLESS Reality, Hysteria2, …) is a separate leg and
  does not matter to the client. A "US via Hysteria2" line is therefore just another VLESS line on the hub with a hysteria outbound behind it.
- `scripts/bridge/add_bridge_profile.py` creates the inbound (copy of an existing Reality inbound: same keys/SNI, own port), the **`hosts` row**
  (without it the subscription link carries the panel's own hostname — wrong from outside), attaches clients, appends the rule
  `inboundTag → outbound|balancer` **after** the block rules, restarts Xray. Remember `ufw allow <port>/tcp`.
- Put a country flag emoji **at the start of the line's name** (`🇺🇸 BridgeUS-…`): Happ/Throne draw the flag from it; without it you get a globe.
- Back up the DB first; verify with `route_test.py` and a real handshake (below).

## 2. Where exits come from

**a) Your own VDS (preferred for anything personal).** `scripts/bridge/deploy_exit_node.sh` installs a **separate** Xray process (own binary copy,
own config, own systemd unit, own port), never touching an existing Xray/nginx/other daemons on that VDS (shared binaries: do not replace them).
The unit adds an iptables rule "this port only from the hub IP" on start and removes it on stop; routing blocks bittorrent, loopback/private
ranges **and the VDS's own public IP** (otherwise an authenticated client could reach local admin/tunnel ports through the exit). No memory limit
is needed on a 700 MB VDS (it used ~10 MB); `OOMScoreAdjust=500` makes it the first victim instead of the neighbours. On the hub add the exit as an
outbound (`link_to_outbound.py` or the panel).

**b) Provider subscription nodes.** The panel can import an external subscription (`POST /panel/api/xray/outbound-subs`: URL → outbounds,
tag prefix, refresh interval; `…/parse` previews without saving). Single share links: `link_to_outbound.py` (vless / hysteria2) →
`test_outbound.py` (temporary client on loopback: exit IP, country, a few sites) → `add_bridge_profile.py --outbound-file`.
**Third-party nodes see your traffic metadata. Never route other people's personal data through them** — use your own VDS.

## 3. Balancers, failover, fail-closed

- `routing.balancers[]` with `strategy: leastPing` needs an observatory: `burstObservatory` (`subjectSelector`, `interval 30s`, `sampling 2`).
  Measured: failover to the fallback in ~76 s, return to the primary ~15 s (2 min interval: ~220 s — too slow).
- `fallbackTag` is used **only when no selected outbound is alive**. Set it to an own exit for "primary → backup", or to `blocked`
  (blackhole) for **fail-closed**. **Without any fallback Xray silently sends the traffic out of the hub's own IP** — the client believes it is
  in country X and is not. Fail-closed is the default in these scripts.
- Only one `fallbackTag` per balancer: a 3-tier priority (provider → own VDS → router) needs a `loopback` outbound chain (designed, **not**
  tested in production).
- **Selectors are PREFIX matches** on outbound tags: `x-jp` also selects `x-jp-1` (another node, another country). Never use bare names as selectors.
- **Provider tags are not country names.** A panel tag is derived from the node's *name at the panel's last refresh*; providers reshuffle which
  server carries which name. A node labelled "USA" sat under the tag `…-jp`. Select by the **flag in the subscription** and match to the panel's
  outbound by address + id, not by tag.

## 4. Automatic country pools by flag (`sync_country_balancers.py`)

Run from a systemd timer (`deploy_country_sync.sh`, hourly). For each managed country it: reads the provider subscription (URL taken from
the panel), takes the **flag emoji** of every link (two regional-indicator symbols = ISO code), finds the matching panel outbound
(address + uuid/auth, then address + port if unique), stores a **copy** under a stable tag `ctry-<CC>-<n>`, points the balancer `selector` and
the observatory at the prefix `ctry-<CC>-`, and verifies the **real exit country** of each node through a temporary Xray client and two
independent geo services. A node that definitely exits elsewhere is excluded; if all are excluded the pool becomes a blackhole (fail-closed).
`--tolerate IN=NL` accepts a documented exception (a provider's "India" addresses geolocate to the Netherlands). It only touches the panel and
restarts Xray when something changed; every run is logged to `/var/log/country-balancers.log`; fetch failures are retried and never break the run.
The panel API token lives in a root-only `/etc/default/country-balancers` — **rotate it there too**.
An "Unavailable" line in a client usually means an empty pool: read the log (`ERROR`, `EXCLUDED`, `black hole`).

## 5. Access for AI agents / devices

- One 3X-UI **client per consumer** (`add_agent.py`: attaches only the Bridge inbounds; `--only <text>` for a single line; `--all`): separate
  traffic stats and independent revoke. The personal subscription URL is a **secret** — store it in a local file, never in chat/git.
- On the agent's server `sub_to_xray.py` (stdlib only) turns the subscription into an Xray client config with a local SOCKS5/HTTP proxy;
  `--profile` selects a line by (part of) its name. (`type=raw` in provider links means plain TCP.)
- Two usage modes: **A** the agent picks a Bridge line (all its traffic exits there); **B** the agent uses a normal line and the hub routes only
  a domain list through the exit via a rule on `user` (`add_user_rule.py`; geo lists must exist in the Xray asset folder — validate with
  `POST /panel/api/xray/geodata/validate`).
- Default recommendation: agents go **through the hub**, not directly to exit nodes (one place for stats, revoke, failover; provider links stay on the hub).

## 6. Proving it works

1. `route_test.py <email> <domain>` — `POST /panel/api/xray/routeTest`: which outbound/balancer the running core would pick.
2. A temporary loopback client built from the inbound's own credentials, fetching an IP-echo URL → the **exit IP** per profile **per user**.
3. `failover_test.py` — temporarily `iptables -I OUTPUT -d <tier-1 node> -j DROP` (always removed in `finally`), watches the exit switch and return.
4. After **any** balancer/observatory change repeat step 2 for every profile: a faulty script once left two lines exiting from the hub IP for
   two minutes (observatory subjects dropped → balancer saw no alive node → no fallback → default outbound). `xray -test` does not catch this.

## 7. Client-side notes

- Do not enable client-side "WARP in chain" (Hiddify "Extra security", WARP configs in Throne, …) together with Bridge lines: sites then see
  Cloudflare's IP and the country exit is lost. WARP on the *server* did not help latency in our tests (`warp-optional.md`).
- sing-box "extended" builds support XHTTP; stock sing-box does not.
- A client's latency indicator is not evidence in either direction; use the loopback test.

## Not verified / open

- 3-tier fallback via `loopback` outbound; an entry node inside the censoring country (cascade: it decrypts all traffic — privacy trade-off).
- A router running Forkop (sing-box) listed the lines but showed no latency for the Bridge lines while desktop clients on the same network did;
  cause not found (ruled out: DNS, time, subscription format, XHTTP, the latency URL, server firewall). Do not promise Forkop compatibility.
