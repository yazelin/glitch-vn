#!/usr/bin/env python3
"""Replace the four relationship-CG images without touching cover or other media."""

from __future__ import annotations

import base64
import json
import pathlib
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BOARD_ID = "board-main"
BASE = f"https://larch.ink/api/agent/projects/{PROJECT_ID}"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()

CGS = [
    ("guard-daughter", "保全的手機", "cg-story-guard-daughter.webp"),
    ("clerk-order", "兩顆蘿蔔，一杯無糖", "cg-story-clerk-order.webp"),
    ("parts-ledger", "她記得零件", "cg-story-parts-ledger.webp"),
    ("reception-sixth", "第六次，仍然沒有印象", "cg-story-reception-sixth.webp"),
]


def request(path="", method="GET", body=None, etag=None, timeout=300):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        headers["If-Match"] = etag
    req = urllib.request.Request(BASE + path, data, headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        return (json.loads(raw) if raw else {}), response.headers.get("ETag")


def upload(key, filename):
    path = ROOT / "art/inv-cg" / filename
    name = filename.removesuffix(".webp") + "-direction-v2.webp"
    body = {"name": name, "mimeType": "image/webp", "category": "cg",
            "base64": base64.b64encode(path.read_bytes()).decode()}
    result, _ = request("/media", "POST", body)
    return result["asset"]["url"]


def base36(number):
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while number:
        out = chars[number % 36] + out
        number //= 36
    return out or "0"


def cg_key(url):
    value = 2166136261
    for char in url:
        value ^= ord(char)
        value = (value * 16777619) & 0xFFFFFFFF
    return f"__larch_cg__:{base36(len(url))}-{base36(value)}"


def condition(url, title):
    leaf = {"variable": cg_key(url), "variableLabel": title, "op": "eq", "value": False}
    return {"kind": "variable", **leaf, "match": "all", "conditions": [leaf]}


def main():
    project, project_etag = request()
    gallery = project.setdefault("settings", {}).setdefault("cgGalleryItems", [])
    by_title = {item.get("title"): item for item in gallery}
    media_by_name = {item.get("name"): item.get("url") for item in project.get("media", [])}
    urls = {}
    for key, title, filename in CGS:
        v2_name = filename.removesuffix(".webp") + "-direction-v2.webp"
        urls[key] = media_by_name.get(v2_name) or upload(key, filename)

    # Uploads advance the project revision. Re-read only when an upload was needed.
    if any(by_title.get(title, {}).get("url") != urls[key] for key, title, _filename in CGS):
        project, project_etag = request()
        gallery = project.setdefault("settings", {}).setdefault("cgGalleryItems", [])
        by_title = {item.get("title"): item for item in gallery}
    for key, title, _filename in CGS:
        by_title[title].update({"url": urls[key], "locked": True})
    request("", "PUT", {"project": project,
            "summary": "四張關係 CG 依俯視站位圖修正櫃台與入口方向"}, project_etag)

    payload, board_etag = request(f"/boards/{BOARD_ID}")
    board = payload.get("board", payload)
    by_id = {node["id"]: node for node in board["nodes"]}
    for key, title, _filename in CGS:
        node_id = f"story-cg-unlock-{key}"
        node = by_id[node_id]
        old_ops = node.get("data", {}).get("cgOps", [])
        legacy = [op for op in old_ops if op.get("url") and op.get("url") != urls[key]]
        node["data"]["cgOps"] = legacy + [{
            "id": f"op-{node_id}-gallery-v2", "url": urls[key], "mode": "unlock"
        }]
        edge_id = f"edge-{node_id}-enter"
        edge = next(edge for edge in board["edges"] if edge.get("id") == edge_id)
        edge.setdefault("data", {})["condition"] = condition(urls[key], title)

    request(f"/boards/{BOARD_ID}", "PUT", {
        "name": board.get("name", BOARD_ID), "kind": board.get("kind", "story"),
        "mode": board.get("mode", "story"), "nodes": board["nodes"], "edges": board["edges"],
        "summary": "四張關係 CG 換成入口位於玩家背後的修正版",
    }, board_etag)
    print(json.dumps(urls, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
