"""Tiny client for the 3X-UI panel API (3.x). Run ON THE SERVER (panel listens on 127.0.0.1).
Config via env (never hard-code secrets):
  XUI_TOKEN  API token        XUI_BASE  panel base path, e.g. /aBcD1234xyz
  XUI_HOST   webDomain (Host header must match), e.g. panel.example.com   XUI_PORT default 29800
3.x rules: GET reads / POST writes (PUT -> 404)."""
import http.client
import json
import os
import ssl
import urllib.parse

TOKEN = os.environ["XUI_TOKEN"]
BASE = os.environ["XUI_BASE"].rstrip("/")
HOST = os.environ["XUI_HOST"]
PORT = int(os.environ.get("XUI_PORT", "29800"))


def call(method, path, form=None, body=None, timeout=120):
    c = http.client.HTTPSConnection("127.0.0.1", PORT, context=ssl._create_unverified_context(), timeout=timeout)
    h = {"Authorization": "Bearer " + TOKEN, "Host": "%s:%d" % (HOST, PORT)}
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form)
        h["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body)
        h["Content-Type"] = "application/json"
    c.request(method, BASE + path, body=data, headers=h)
    return json.loads(c.getresponse().read().decode())


def template():
    """Returns the dict {xraySetting, outboundTestUrl, ...}; `obj` of POST /panel/api/xray/ is a JSON string."""
    return json.loads(call("POST", "/panel/api/xray/", body={})["obj"])
