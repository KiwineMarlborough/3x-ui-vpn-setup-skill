# Inbound Hardening: IPsum blocklist (nftables) + Fail2Ban

Two layers, both **part of the default setup** (`execution-order.md`, phase 1b):

| Layer | What it stops | Mechanism |
|-------|---------------|-----------|
| **IPsum** ([stamparm/ipsum](https://github.com/stamparm/ipsum), refreshed daily by its author) | Scanners/botnets that are already on several public blocklists — dropped before they reach SSH, nginx, the panel or any inbound | own nftables table, whole address dropped on every port |
| **Fail2Ban** `sshd` jail | Everyone else who guesses SSH passwords | bans after N failures from the journal |

3X-UI's installer additionally creates the `3x-ipl` jail (per-client IP limit; acts only when a client has
`limitIp > 0`). It is independent and left untouched.

## Why IPsum is NOT inside Fail2Ban

Fail2Ban reacts to log lines and keeps every ban in its own database; loading ~17 000 static entries is slow
and bloats it. A static list belongs in a kernel set: one atomic `nft -f` load, no per-entry processes.

## Design (what `scripts/deploy-ipsum.sh` installs)

```
table inet ipsum
  set whitelist  { ipv4_addr, interval }  admin IPs + private ranges
  set blocklist  { ipv4_addr }            IPsum level >= 3  (~17k addresses)
  chain input  { hook input priority -10; policy accept;     # before UFW (priority 0)
      ip saddr @whitelist accept
      ip saddr @blocklist counter drop }
```

* Separate table → `ufw reload` / `ufw enable` never touch it; no package needed (nft ships with Ubuntu).
* **Level 3** = the address is on at least 3 independent blocklists (author's recommended threshold;
  2 → ~32k entries, more false positives; 4 → ~9k). Set with `MIN_LEVEL`.
* Whitelist is evaluated first and always: private ranges + `ADMIN_IPS` + the SSH peers connected at deploy time.
* Safety in the updater (`/usr/local/sbin/ipsum-update.sh`): refuses a list below 5000 entries (outage or
  tampered source), falls back to the cached list when GitHub is unreachable, validates with `nft -c`
  before applying, loads atomically (a failed update leaves the previous set active).
* Refresh: systemd timer (2 min after boot, then daily ~04:30 UTC). Counters reset on each refresh (table is recreated).
* IPv4 only (IPsum has no IPv6).

## Safe rollout — never skip

```bash
# 1. arm: whitelist + auto-rollback timer (table deletes itself in 5 min unless confirmed)
sudo env "ADMIN_IPS=<your.public.ip>" bash scripts/deploy-ipsum.sh
# 2. open a NEW ssh session AND test a VPN profile from your usual network
# 3. confirm (cancels the rollback)
sudo env CONFIRM=1 bash scripts/deploy-ipsum.sh
```

`ADMIN_IPS` is mandatory unless an SSH session is detectable; the script refuses to run with no admin address
(otherwise it could lock you out). `DRY_RUN=1` prints the plan. `verify-server.sh` fails while the rollback timer is
still armed (it would silently remove the protection).

## False positives (the only real risk)

Mobile-carrier addresses (CGNAT, shared by thousands of subscribers) occasionally land on blocklists because of
infected neighbours. Symptom: a user (or you) loses access **only from one network**. Procedure:

1. Get the user's public IP (what-is-my-ip from that network).
2. `sudo nft get element inet ipsum blocklist '{ A.B.C.D }'` → present?
3. Add it to `/etc/ipsum/whitelist.txt`, then `sudo systemctl start ipsum-block.service`.

Always test a VPN profile from **your** network right after deploying. Add admin/home IPs *before* deploying.

## Operations

```bash
sudo nft list chain inet ipsum input              # counters = packets dropped since last refresh
sudo journalctl -t ipsum                          # update log
sudo nft delete table inet ipsum                  # emergency off (returns at the next refresh)
sudo systemctl disable --now ipsum-block.timer    # permanent off
```

## Fail2Ban (`scripts/setup-fail2ban.sh`)

```bash
sudo env "ADMIN_IPS=<your.public.ip>" bash scripts/setup-fail2ban.sh
```

Writes `/etc/fail2ban/jail.d/10-sshd-hardening.local` (sshd, systemd backend, 5 failures / 10 min → 1 h ban)
with `ignoreip` = loopback + admin IPs. **Put your own address in `ignoreip`**: with password login as root, five typos
otherwise ban *you*. Key-only logins (the recommended default for agent accounts) cannot trigger bans by mistake.
Fail2Ban reads the journal (`_SYSTEMD_UNIT=ssh.service`); an `sshd` `Match User` block in sshd_config has no
effect on it.

## Related

`panel-tunnel-access.md` · `agent-access-hygiene.md` · `monitoring.md` · `gotchas.md`
