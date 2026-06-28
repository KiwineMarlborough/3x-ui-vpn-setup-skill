#!/usr/bin/env python3
"""Reset VLESS flow to empty for Podkop TCP clients.

Podkop and many routers break when flow=xtls-rprx-vision on TLS TCP inbound.

Usage (on server):
  sudo python3 fix-podkop-flow.py
  sudo python3 fix-podkop-flow.py --email user-router@project
  sudo python3 fix-podkop-flow.py --port 8444

BACKUP FIRST: sudo cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from pathlib import Path

DB = Path("/etc/x-ui/x-ui.db")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="", help="Client email filter (substring)")
    parser.add_argument("--port", type=int, default=8444, help="Podkop inbound port")
    args = parser.parse_args()

    if not DB.exists():
        print("DB not found:", DB)
        return 1

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if args.email:
        cur.execute("UPDATE clients SET flow='' WHERE email LIKE ?", (f"%{args.email}%",))
        print(f"Updated clients.flow for email like %{args.email}% → {cur.rowcount} rows")
    else:
        cur.execute("UPDATE clients SET flow=''")
        print(f"Updated all clients.flow → {cur.rowcount} rows")

    cur.execute("SELECT id, settings FROM inbounds WHERE port=?", (args.port,))
    row = cur.fetchone()
    if row:
        iid, settings_raw = row
        settings = json.loads(settings_raw or "{}")
        clients = settings.get("clients", [])
        for c in clients:
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