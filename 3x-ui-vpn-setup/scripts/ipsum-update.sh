#!/bin/bash
# IPsum (stamparm/ipsum) blocklist -> nftables, atomic reload. Installed to /usr/local/sbin by deploy-ipsum.sh.
#
# Own nftables table `inet ipsum` (input hook, priority -10: before UFW) so that `ufw reload`
# never touches it and a bad update can never leave a half-loaded set.
#
# Env overrides: MIN_LEVEL (default 3), MIN_ENTRIES (sanity floor, default 5000), URL.
# Whitelist: /etc/ipsum/whitelist.txt (IPs/CIDRs, one per line, comments allowed) — ALWAYS accepted first.
set -euo pipefail

URL="${URL:-https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt}"
MIN_LEVEL="${MIN_LEVEL:-3}"
MIN_ENTRIES="${MIN_ENTRIES:-5000}"
WL=/etc/ipsum/whitelist.txt
STATE=/var/lib/ipsum
CACHE=$STATE/blocklist.txt

mkdir -p "$STATE"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if curl -fsS -m 60 --retry 2 "$URL" -o "$WORK/raw.txt"; then
    grep -v '^#' "$WORK/raw.txt" \
        | awk -v l="$MIN_LEVEL" '$2+0>=l {print $1}' \
        | grep -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$' | sort -u > "$WORK/ips.txt" || true
    n=$(wc -l < "$WORK/ips.txt")
    if [ "$n" -lt "$MIN_ENTRIES" ]; then
        logger -t ipsum "список подозрительно мал ($n < $MIN_ENTRIES), оставляю предыдущий"
        [ -s "$CACHE" ] || exit 1
    else
        cp "$WORK/ips.txt" "$CACHE"
    fi
else
    logger -t ipsum "не удалось скачать список, использую кэш"
    [ -s "$CACHE" ] || exit 1
fi

# белый список: IP и CIDR, комментарии допустимы
{
    echo "127.0.0.0/8"; echo "10.0.0.0/8"; echo "172.16.0.0/12"; echo "192.168.0.0/16"
    [ -f "$WL" ] && grep -vE '^\s*(#|$)' "$WL" | awk '{print $1}' || true
} | sort -u > "$WORK/wl.txt"

join_commas() { paste -sd, -; }

{
    echo "add table inet ipsum"
    echo "delete table inet ipsum"
    echo "table inet ipsum {"
    echo "  set whitelist { type ipv4_addr; flags interval; elements = { $(join_commas < "$WORK/wl.txt") } }"
    echo "  set blocklist { type ipv4_addr; elements = { $(join_commas < "$CACHE") } }"
    echo "  chain input {"
    echo "    type filter hook input priority -10; policy accept;"
    echo "    ip saddr @whitelist accept"
    echo "    ip saddr @blocklist counter drop"
    echo "  }"
    echo "}"
} > "$WORK/ipsum.nft"

nft -c -f "$WORK/ipsum.nft"
nft -f "$WORK/ipsum.nft"
logger -t ipsum "загружено $(wc -l < "$CACHE") адресов (уровень >= $MIN_LEVEL), белый список: $(wc -l < "$WORK/wl.txt")"
