#!/usr/bin/env python3
"""把 CG 跨周目測試版改成由連線條件直接讀取 CG 收藏。"""

import json
import pathlib
import urllib.request


PROJECT = "project-34f94fd6-343b-466a-9548-39144637d1de"
BOARD = "board-main"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
URL = f"https://larch.ink/api/agent/projects/{PROJECT}/boards/{BOARD}"
CG_KEY = "__larch_cg__:51-3ndgia"


def request(method="GET", payload=None, etag=None):
    headers = {"Authorization": f"Bearer {KEY}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if etag:
        headers["If-Match"] = etag
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response), response.headers.get("ETag")


raw, etag = request()
board = raw.get("board", raw)
nodes = {node["id"]: node for node in board["nodes"]}

nodes["unlock-gate"]["data"] = {
    "type": "dialogue",
    "title": "直接查 CG 收藏",
    "text": "按下繼續時，連線會直接讀取 CG 收藏（跨周目）：尚未解鎖才會播放並解鎖；已解鎖則略過。",
}
nodes["query-gate"]["data"] = {
    "type": "dialogue",
    "title": "查詢目前 CG 狀態",
    "text": "按下繼續後，連線條件會直接讀取這張 CG 的跨周目收藏狀態。",
}

def condition(value):
    return {
        "kind": "variable",
        "variable": CG_KEY,
        "variableLabel": "跨周目測試 CG",
        "op": "eq",
        "value": value,
        "match": "all",
        "conditions": [{
            "variable": CG_KEY,
            "variableLabel": "跨周目測試 CG",
            "op": "eq",
            "value": value,
        }],
    }

board["edges"] = [
    edge for edge in board["edges"]
    if edge["id"] not in {"e-gate-unlock", "e-gate-first", "e-query-yes", "e-query-no"}
]
board["edges"].extend([
    {
        "id": "e-gate-first",
        "source": "unlock-gate",
        "target": "unlock",
        "animated": True,
        "data": {"condition": condition(False)},
    },
    {
        "id": "e-gate-unlock",
        "source": "unlock-gate",
        "target": "skip",
        "animated": True,
    },
    {
        "id": "e-query-yes",
        "source": "query-gate",
        "target": "query-yes",
        "animated": True,
        "data": {"condition": condition(True)},
    },
    {
        "id": "e-query-no",
        "source": "query-gate",
        "target": "query-no",
        "animated": True,
    },
])

payload = {
    "name": board["name"],
    "kind": board.get("kind", "story"),
    "mode": board.get("mode", "story"),
    "nodes": board["nodes"],
    "edges": board["edges"],
    "summary": "驗證 CG 收藏跨周目條件：未解鎖才播放，已解鎖則略過",
}
result, _ = request("PUT", payload, etag)
print(json.dumps(result, ensure_ascii=False, indent=2))
