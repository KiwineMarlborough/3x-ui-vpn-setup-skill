#!/usr/bin/env python3
"""Set custom subscription paths via 3X-UI API (with SQLite fallback).

Usage:
  export PANEL_BASE="https://panel.example.com:29800/<webBasePath>"
  export PANEL_TOKEN="..."
  export CDN_DOMAIN="cdn.example.com"
  export SUB_PATH="/xK9mP2qR/"
  export JSON_PATH="/j4nR8wLz3k/"
  export SUB_PORT=2096
  export PANEL_RESOLVE="panel.example.com:29800:127.0.0.1"  # optional
  python3 set-sub-paths.py
  python3 set-sub-paths.py --sqlite-fallback   # try API, then DB if API fails
  python3 set-sub-paths.py --sqlite-only       # skip API when panel unreachable

Also sets subEncrypt=false and subJsonEnable=true.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

BASE = os.environ.get("PANEL_BASE", "").rstrip("/")
TOKEN = os.environ.get("PANEL_TOKEN", "")
RESOLVE = os.environ.get("PANEL_RESOLVE", "")
CDN = os.environ.get("CDN_DOMAIN", "cdn.vpn.example.com")
SUB_PATH = os.environ.get("SUB_PATH", "/sub/")
JSON_PATH = os.environ.get("JSON_PATH", "/json/")
SUB_PORT = int(os.environ.get("SUB_PORT", "2096"))
DB = Path("/etc/x-ui/x-ui.db")


def curl_json(method: str, path: str, data: dict | None = None) -> dict:
    cmd = [
        "curl", "-sk", "-X", method,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
    ]
    if RESOLVE:
        cmd.extend(["--resolve", RESOLVE])
    url = f"{BASE}{path}"
    if data is not None:
        cmd.extend(["-d", json.dumps(data)])
    else:
        cmd.extend(["-d", "{}"])
    cmd.append(url)
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def sqlite_patch() -> bool:
    if not DB.exists():
        print(f"SQLite fallback skipped: DB not found at {DB}", file=sys.stderr)
        return False
    sub_uri = f"https://{CDN}:{SUB_PORT}{SUB_PATH}"
    json_uri = f"https://{CDN}:{SUB_PORT}{JSON_PATH}"
    pairs = {
        "subPath": SUB_PATH,
        "subJsonPath": JSON_PATH,
        "subURI": sub_uri,
        "subJsonURI": json_uri,
        "subEncrypt": "false",
        "subJsonEnable": "true",
    }
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for k, v in pairs.items():
        if cur.execute("SELECT 1 FROM settings WHERE key=?", (k,)).fetchone():
            cur.execute("UPDATE settings SET value=? WHERE key=?", (v, k))
        else:
            cur.execute("INSERT INTO settings(key, value) VALUES(?, ?)", (k, v))
    conn.commit()
    conn.close()
    print("SQLite patch applied")
    return True


def try_api_update() -> bool:
    if not BASE or not TOKEN:
        return False
    try:
        resp = curl_json("POST", "/panel/api/setting/all", {})
        obj = resp.get("obj") or resp
        if isinstance(obj, dict) and "obj" in obj:
            obj = obj["obj"]
        for k in list(obj.keys()):
            if k.startswith("has"):
                obj.pop(k, None)

        sub_uri = f"https://{CDN}:{SUB_PORT}{SUB_PATH}"
        json_uri = f"https://{CDN}:{SUB_PORT}{JSON_PATH}"
        obj["subPath"] = SUB_PATH
        obj["subJsonPath"] = JSON_PATH
        obj["subURI"] = sub_uri
        obj["subJsonURI"] = json_uri
        obj["subEncrypt"] = False
        obj["subJsonEnable"] = True

        upd = curl_json("POST", "/panel/api/setting/update", obj)
        ok = bool(upd.get("success"))
        print("API update:", ok, upd.get("msg", ""))
        return ok
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError) as exc:
        print(f"API update failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sqlite-fallback",
        action="store_true",
        help="If API fails, patch /etc/x-ui/x-ui.db directly",
    )
    parser.add_argument(
        "--sqlite-only",
        action="store_true",
        help="Skip API entirely (no PANEL_BASE/PANEL_TOKEN required)",
    )
    args = parser.parse_args()

    sub_uri = f"https://{CDN}:{SUB_PORT}{SUB_PATH}"
    json_uri = f"https://{CDN}:{SUB_PORT}{JSON_PATH}"

    if args.sqlite_only:
        if not sqlite_patch():
            return 1
        subprocess.run(["x-ui", "restart"], check=False)
        print(f"subURI={sub_uri}")
        print(f"subJsonURI={json_uri}")
        return 0

    api_ok = try_api_update()
    if api_ok:
        subprocess.run(["x-ui", "restart"], check=False)
        print(f"subURI={sub_uri}")
        print(f"subJsonURI={json_uri}")
        return 0

    if args.sqlite_fallback:
        if sqlite_patch():
            subprocess.run(["x-ui", "restart"], check=False)
            print(f"subURI={sub_uri}")
            print(f"subJsonURI={json_uri}")
            return 0
        return 1

    if not BASE or not TOKEN:
        print(
            "Set PANEL_BASE and PANEL_TOKEN, or use --sqlite-only / --sqlite-fallback",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())