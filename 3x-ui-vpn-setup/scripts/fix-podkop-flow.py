#!/usr/bin/env python3
"""Reset VLESS flow to empty for Podkop TCP clients.

Podkop and many routers break when flow=xtls-rprx-vision on TLS TCP inbound.

Usage (on server):
  sudo python3 fix-podkop-flow.py
  sudo python3 fix-podkop-flow.py --email user-router@project
  sudo python3 fix-podkop-flow.py --port 8444
  sudo python3 fix-podkop-flow.py --all   # dangerous: all clients globally

Default: only clients attached to the Podkop inbound (port 8444).

BACKUP FIRST: sudo cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

DB = Path("/etc/x-ui/x-ui.db")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="", help="Client email filter (substring)")
    parser.add_argument("--port", type=int, default=8444, help="Podkop inbound port")
    parser.add_argument(
        "--all",
        action="store_true",
        help="DANGEROUS: clear flow on ALL clients, not only Podkop inbound",
    )
    args = parser.parse_args()

    if not DB.exists():
        print("DB not found:", DB)
        return 1

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if args.all:
        print("WARNING: --all clears flow on every client (may break Reality Vision)", file=sys.stderr)
        if args.email:
            cur.execute("UPDATE clients SET flow='' WHERE email LIKE ?", (f"%{args.email}%",))
            print(f"Updated clients.flow for email like %{args.email}% → {cur.rowcount} rows")
        else:
            cur.execute("UPDATE clients SET flow=''")
            print(f"Updated all clients.flow → {cur.rowcount} rows")
    else:
        cur.execute("SELECT id, settings FROM inbounds WHERE port=?", (args.port,))
        row = cur.fetchone()
        if not row:
            print(f"No inbound on port {args.port}")
            conn.close()
            return 1

        iid, settings_raw = row
        settings = json.loads(settings_raw or "{}")
        emails = [
            c["email"]
            for c in settings.get("clients", [])
            if isinstance(c, dict) and c.get("email")
        ]
        if args.email:
            emails = [e for e in emails if args.email in e]

        if not emails:
            print(f"No clients on inbound #{iid} port {args.port}")
            conn.close()
            return 1

        placeholders = ",".join("?" * len(emails))
        cur.execute(f"UPDATE clients SET flow='' WHERE email IN ({placeholders})", emails)
        print(f"Updated clients.flow for Podkop inbound → {cur.rowcount} rows ({len(emails)} emails)")

        for c in settings.get("clients", []):
            if isinstance(c, dict):
                c["flow"] = ""
        cur.execute("UPDATE inbounds SET settings=? WHERE id=?", (json.dumps(settings), iid))
        print(f"Cleared flow in inbound #{iid} port {args.port}")

    if args.all:
        cur.execute("SELECT id, settings FROM inbounds WHERE port=?", (args.port,))
        row = cur.fetchone()
        if row:
            iid, settings_raw = row
            settings = json.loads(settings_raw or "{}")
            for c in settings.get("clients", []):
                if isinstance(c, dict):
                    c["flow"] = ""
            cur.execute("UPDATE inbounds SET settings=? WHERE id=?", (json.dumps(settings), iid))
            print(f"Cleared flow in inbound #{iid} port {args.port}")

    conn.commit()
    conn.close()
    subprocess.run(["x-ui", "restart"], check=False)
    print("Restarted x-ui")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())