# Cloudflare WARP (optional — usually NOT needed)

## What it does on VPS

Routes **server outbound** through Cloudflare — changes exit IP seen by websites.

## When it helps

- VPS IP blocked by OpenAI / banks / APIs
- Need different egress reputation

## When to skip (default for personal DE tunnel)

- Want honest geo IP (Frankfurt shows as Frankfurt)
- Everything works with VPS IP directly
- Avoid extra hop latency

## Does NOT help

- Hiding VPN from RKN on **inbound**
- Replacing Reality stealth

## If enabling

- Selective routing only (problem domains → WARP)
- Do not set WARP as first outbound for all traffic
- Personal use only; not commercial resale

See 3X-UI Outbounds → socks `127.0.0.1:40000` after `warp-cli` install.

## Tested on 3X-UI 3.11 / Xray 26.11 (panel-native WARP)

- Registration works via `POST /panel/api/xray/warp/reg` (client generates the WireGuard key pair; `regMasque` registers a MASQUE device).
- The WireGuard outbound only carried traffic with `"noKernelTun": true` (without it Xray logs "Using kernel TUN" and nothing flows).
- Requests to a **literal IP** through WARP worked (~74 ms) but were slower than the server's direct path (~37 ms, 6 ms RTT to large CDNs);
  requests by **domain name** hung in every variant tried (ForceIP/ForceIPv4, a `dns` block with public resolvers, DNS through the tunnel).
  Cause not found — try the MASQUE variant before relying on WARP for domain traffic.
- A high latency number in a client (e.g. 500 ms) is not the server's outbound path: client delay tests include several round trips over the
  mobile link and connection setup. A WARP chain configured *in the client* can look much faster simply because it keeps one persistent UDP tunnel.
- Never chain client-side WARP with country-bridge lines: the exit becomes Cloudflare's IP.