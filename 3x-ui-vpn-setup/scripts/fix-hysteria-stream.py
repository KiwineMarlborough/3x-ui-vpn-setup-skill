#!/usr/bin/env python3
"""Fix Hysteria inbound stream_settings in x-ui.db for Xray 26.x + JSON sub.

Finds hysteria protocol inbound and merges templates/hysteria-stream-settings.json.

Usage (on server):
  sudo python3 fix-hysteria-stream.py [--inbound-id 5]

BACKUP FIRST: sudo cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from pathlib import Path

DB = Path("/etc/x-ui/x-ui.db")
TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "hysteria-stream-settings.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inbound-id", type=int, default=0)
    args = parser.parse_args()

    if not DB.exists():
        print("DB not found:", DB)
        return 1
    hy_template = json.loads(TEMPLATE.read_text())
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if args.inbound_id:
        cur.execute("SELECT id,remark,stream_settings FROM inbounds WHERE id=?", (args.inbound_id,))
    else:
        cur.execute("SELECT id,remark,stream_settings FROM inbounds WHERE protocol='hysteria' OR remark LIKE '%Hysteria%' LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("No hysteria inbound found")
        return 1
    iid, remark, stream_raw = row
    stream = json.loads(stream_raw or "{}")
    for key in ("hysteriaSettings", "hysteria2Settings"):
        stream[key] = hy_template[key]
    stream["network"] = "hysteria"
    cur.execute("UPDATE inbounds SET stream_settings=? WHERE id=?", (json.dumps(stream), iid))
    cur.execute("UPDATE inbounds SET settings=? WHERE id=? AND (settings IS NULL OR settings NOT LIKE '%\"version\": 2%')",
                (json.dumps({"version": 2, "clients": []}), iid))
    conn.commit()
    conn.close()
    print(f"Updated inbound #{iid} ({remark})")
    subprocess.run(["x-ui", "restart"], check=False)
    print("Restarted x-ui — run: xray-linux-amd64 run -test -c /usr/local/x-ui/bin/config.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())