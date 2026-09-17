#!/usr/bin/env python3
"""修正劇情模式的管理員／保全路線，並加入四張調查關係 CG。

只讀最新線上專案後做聚焦合併；不替換封面、縮圖、角色、既有 CG 或其他版子。
"""

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
    {"key": "guard-daughter", "title": "保全的手機", "source": "inv-060",
     "file": "cg-story-guard-daughter.webp"},
    {"key": "clerk-order", "title": "兩顆蘿蔔，一杯無糖", "source": "inv-223",
     "file": "cg-story-clerk-order.webp"},
    {"key": "parts-ledger", "title": "她記得零件", "source": "inv-245",
     "file": "cg-story-parts-ledger.webp"},
    {"key": "reception-sixth", "title": "第六次，仍然沒有印象", "source": "inv-351",
     "file": "cg-story-reception-sixth.webp"},
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


def upload(spec):
    path = ROOT / "art/inv-cg" / spec["file"]
    body = {"name": spec["file"], "mimeType": "image/webp", "category": "cg",
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


def cg_condition(url, title):
    leaf = {"variable": cg_key(url), "variableLabel": title, "op": "eq", "value": False}
    return {"kind": "variable", **leaf, "match": "all", "conditions": [leaf]}


def replace_trust_op(node, variable, kind, value):
    ops = [op for op in node.get("data", {}).get("variableOps", []) if op.get("variable") != variable]
    ops.append({"id": f"op-{variable}", "variable": variable, "kind": kind, "value": value})
    node["data"]["variableOps"] = ops


def add_unlock(board, spec, url):
    nodes, edges = board["nodes"], board["edges"]
    by_id = {node["id"]: node for node in nodes}
    source = by_id[spec["source"]]
    node_id = f"story-cg-unlock-{spec['key']}"
    node = by_id.get(node_id)
    if node is None:
        pos = source.get("position", {"x": 0, "y": 0})
        node = {"id": node_id, "type": "story",
                "position": {"x": pos.get("x", 0) + 180, "y": pos.get("y", 0) + 280},
                "data": {"type": "setVariable"}}
        nodes.append(node)
    node["data"].update({
        "title": f"解鎖：{spec['title']}",
        "text": "新的調查篇角色紀念 CG 已加入收藏。",
        "cgOps": [{"id": f"op-{node_id}-gallery", "url": url, "mode": "unlock"}],
    })
    node["data"].pop("variableOps", None)

    enter_id = f"edge-{node_id}-enter"
    clone_prefix = f"edge-{node_id}-continue-"
    edges[:] = [edge for edge in edges
                if edge.get("id") != enter_id and not edge.get("id", "").startswith(clone_prefix)]
    outgoing = [edge for edge in edges if edge.get("source") == spec["source"]]
    enter = {"id": enter_id, "source": spec["source"], "target": node_id,
             "sourceHandle": "right", "animated": True,
             "data": {"condition": cg_condition(url, spec["title"])}}
    first = next((i for i, edge in enumerate(edges) if edge.get("source") == spec["source"]), len(edges))
    edges.insert(first, enter)
    # 解鎖後重新走原來源的全部出口；因此既有 CG 的跨周目判斷仍會照常執行。
    for i, old in enumerate(outgoing):
        clone = dict(old)
        clone.update({"id": f"{clone_prefix}{i}", "source": node_id, "sourceHandle": "right"})
        edges.append(clone)


def main():
    project, _ = request()
    known = {asset.get("name"): asset.get("url") for asset in project.get("media", [])}
    urls = {}
    for spec in CGS:
        urls[spec["file"]] = known.get(spec["file"]) or upload(spec)

    # 上傳會推進 revision；設定寫入前一定重讀。
    project, project_etag = request()
    local = json.loads((ROOT / "larch/inv/out/board.json").read_text())
    walk = next(v["defaultValue"] for v in local["variables"] if v["name"] == "walk")
    walk_var = next(v for v in project["variables"] if v.get("name") == "walk")
    walk_var["defaultValue"] = walk
    gallery = project.setdefault("settings", {}).setdefault("cgGalleryItems", [])
    gallery_by_title = {item.get("title"): item for item in gallery}
    for spec in CGS:
        item = {"title": spec["title"], "url": urls[spec["file"]], "locked": True}
        if spec["title"] in gallery_by_title:
            gallery_by_title[spec["title"]].update(item)
        else:
            gallery.append(item)
    project["settings"]["cgGalleryEnabled"] = True
    project["settings"]["cgGallerySource"] = "picked"
    request("", "PUT", {"project": project,
            "summary": "劇情模式補足管理員與保全路線，新增四張調查角色關係 CG"}, project_etag)

    payload, board_etag = request(f"/boards/{BOARD_ID}")
    board = payload.get("board", payload)
    original_nodes = len(board["nodes"])
    by_id = {node["id"]: node for node in board["nodes"]}
    for node_id in ("inv-100", "inv-102", "inv-104"):
        replace_trust_op(by_id[node_id], "trust_管理員", "set", 2)
    for node_id in ("inv-106", "inv-108"):
        replace_trust_op(by_id[node_id], "trust_管理員", "add", 1)

    # 保全第四階後時間推到凌晨兩點，直接接高信任的監視器線索。
    board["edges"][:] = [edge for edge in board["edges"]
                         if not (edge.get("source") == "inv-060")
                         and not (edge.get("target") == "inv-425"
                                 and edge.get("data", {}).get("condition", {}).get("variable") == "pick")]
    board["edges"].append({"id": "edge-guard-trust-to-payoff", "source": "inv-060", "target": "inv-425",
                           "sourceHandle": "right", "animated": True})

    for spec in CGS:
        add_unlock(board, spec, urls[spec["file"]])

    request(f"/boards/{BOARD_ID}", "PUT", {
        "name": board.get("name", BOARD_ID), "kind": board.get("kind", "story"),
        "mode": board.get("mode", "story"), "nodes": board["nodes"], "edges": board["edges"],
        "summary": "管理員與保全信任接線修正，四位調查角色補上跨周目 CG 解鎖",
    }, board_etag)
    print(f"完成：版子 {original_nodes} → {len(board['nodes'])} 張卡，新增 {len(CGS)} 張關係 CG。")


if __name__ == "__main__":
    main()
