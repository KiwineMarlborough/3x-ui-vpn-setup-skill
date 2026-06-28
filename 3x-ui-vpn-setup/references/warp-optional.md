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