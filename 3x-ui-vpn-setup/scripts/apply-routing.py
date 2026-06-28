#!/usr/bin/env python3
"""Apply Happ routing profile to 3X-UI subscription settings via API.

Usage (on server or via SSH):
  export PANEL_BASE="https://panel.example.com:29800/<webBasePath>"
  export PANEL_TOKEN="..."
  export ROUTING_TEMPLATE="/path/to/happ-routing-profile.json"
  python3 apply-routing.py

Requires: curl, python3. Run with --resolve if webDomain lock is enabled.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = os.environ.get("PANEL_BASE", "").rstrip("/")
TOKEN = os.environ.get("PANEL_TOKEN", "")
TEMPLATE = Path(os.environ.get("ROUTING_TEMPLATE", "templates/happ-routing-profile.json"))
RESOLVE = os.environ.get("PANEL_RESOLVE", "")  # e.g. panel.example.com:29800:127.0.0.1
ROUTING_NAME = os.environ.get("ROUTING_NAME", "")


def curl_json(method: str, path: str, data: dict | None = None) -> dict:
    cmd = ["curl", "-sk", "-X", method, "-H", f"Authorization: Bearer {TOKEN}", "-H", "Content-Type: application/json"]
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


def main() -> int:
    if not BASE or not TOKEN:
        print("Set PANEL_BASE and PANEL_TOKEN", file=sys.stderr)
        return 1
    if not TEMPLATE.is_file():
        print(f"Template not found: {TEMPLATE}", file=sys.stderr)
        return 1

    profile = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if ROUTING_NAME:
        profile["Name"] = ROUTING_NAME

    rule = "happ://routing/onadd/" + base64.b64encode(
        json.dumps(profile, ensure_ascii=False).encode()
    ).decode()

    resp = curl_json("POST", "/panel/api/setting/all", {})
    obj = resp.get("obj") or resp
    if isinstance(obj, dict) and "obj" in obj:
        obj = obj["obj"]
    for k in list(obj.keys()):
        if k.startswith("has"):
            obj.pop(k, None)
    obj["subEnableRouting"] = True
    obj["subRoutingRules"] = rule

    upd = curl_json("POST", "/panel/api/setting/update", obj)
    print("routing update success:", upd.get("success", upd))
    return 0 if upd.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())