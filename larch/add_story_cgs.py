#!/usr/bin/env python3
"""把調查篇紀念 CG 接到正確的劇情節點，並修正貓草房背景。

這支腳本只處理既有 Larch 專案的設定、調查篇版子與謝幕版子。每一張 CG
都直接查詢「CG 收藏（跨周目）」；已解鎖的玩家不會重複看到解鎖畫面。
"""

from __future__ import annotations

import json
import pathlib
import urllib.request


PROJECT_ID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BASE = f"https://larch.ink/api/agent/projects/{PROJECT_ID}"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()

CATGRASS_OLD = (
    "https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/"
    "2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/"
    "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4/"
    "1788746747783_bg-catgrass-home.jpg"
)

CGS = [
    {
        "key": "golden-hat",
        "title": "金色的帽子",
        "source": "inv-070",
        "file": "cg-story-golden-hat-v2.webp",
        "board": "board-main",
    },
    {
        "key": "bambi-wall",
        "title": "斑比的牆",
        "source": "inv-328",
        "file": "cg-story-bambi-wall-v4.webp",
        "board": "board-main",
    },
    {
        "key": "midnight-manager",
        "title": "深夜的便利商店",
        "source": "inv-342",
        "file": "cg-story-midnight-manager-v2.webp",
        "board": "board-main",
    },
    {
        "key": "two-minutes",
        "title": "兩分鐘",
        "source": "inv-351",
        "file": "cg-story-two-minutes-v2.webp",
        "board": "board-main",
    },
    {
        "key": "promise",
        "title": "我答應過他",
        "source": "inv-408",
        "file": "cg-story-promise-v3.webp",
        "board": "board-main",
    },
    {
        "key": "lost-notebook",
        "title": "失物箱的空白守則本",
        "source": "inv-423",
        "file": "cg-story-lost-notebook-v1.webp",
        "board": "board-main",
    },
    {
        "key": "seventh-line",
        "title": "第七行",
        "source": "inv-455",
        "file": "cg-story-seventh-line-v1.webp",
        "board": "board-main",
    },
    {
        "key": "four-times",
        "title": "四次",
        "source": "inv-459",
        "file": "cg-story-four-times-v2.webp",
        "board": "board-main",
    },
    {
        "key": "this-episode",
        "title": "這集有我",
        "source": "inv-531",
        "file": "cg-story-this-episode-v3.webp",
        "board": "board-main",
    },
    {
        "key": "curtain",
        "title": "調查篇・謝幕",
        "source": "credits-line",
        "file": "cg-story-curtain-v2.webp",
        "board": "board-credits",
    },
]


def request(path: str = "", method: str = "GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        headers["If-Match"] = etag
    req = urllib.request.Request(BASE + path, data, headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as response:
        raw = response.read()
        result = json.loads(raw) if raw else {}
        return result, response.headers.get("ETag")


def by_filename(project: dict) -> dict[str, str]:
    urls = {}
    for asset in project.get("media", []):
        name = asset.get("name")
        if name:
            urls[name] = asset.get("url", "")
    return urls


def base36(number: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if number == 0:
        return "0"
    result = ""
    while number:
        result = digits[number % 36] + result
        number //= 36
    return result


def cg_condition_key(url: str) -> str:
    """產生 Larch 對 CG 網址使用的跨周目條件鍵。"""
    value = 2166136261
    for char in url:
        value ^= ord(char)
        value = (value * 16777619) & 0xFFFFFFFF
    return f"__larch_cg__:{base36(len(url))}-{base36(value)}"


def cg_condition(url: str, title: str, unlocked: bool) -> dict:
    key = cg_condition_key(url)
    leaf = {
        "variable": key,
        "variableLabel": title,
        "op": "eq",
        "value": unlocked,
    }
    return {
        "kind": "variable",
        **leaf,
        "match": "all",
        "conditions": [leaf],
    }


def add_unlock(board: dict, spec: dict, url: str) -> None:
    nodes = board["nodes"]
    edges = board["edges"]
    node_id = f"story-cg-unlock-{spec['key']}"
    existing = next((node for node in nodes if node["id"] == node_id), None)
    if existing:
        existing["data"].update(
            {
                "title": f"解鎖：{spec['title']}",
                "text": "新的調查篇紀念 CG 已加入收藏。",
                "cgOps": [
                    {"id": f"op-{node_id}-gallery", "url": url, "mode": "unlock"}
                ],
            }
        )
        existing["data"].pop("variableOps", None)
    else:
        source = next(node for node in nodes if node["id"] == spec["source"])
        outgoing = [edge for edge in edges if edge.get("source") == spec["source"]]
        target = outgoing[0]["target"] if outgoing else None
        pos = source.get("position", {"x": 0, "y": 0})
        nodes.append(
            {
                "id": node_id,
                "type": "story",
                "position": {"x": pos.get("x", 0) + 300, "y": pos.get("y", 0) + 180},
                "data": {
                    "type": "setVariable",
                    "title": f"解鎖：{spec['title']}",
                    "text": "新的調查篇紀念 CG 已加入收藏。",
                    "cgOps": [
                        {"id": f"op-{node_id}-gallery", "url": url, "mode": "unlock"}
                    ],
                },
            }
        )
        if target:
            edges.append(
                {
                    "id": f"edge-{node_id}-leave",
                    "source": node_id,
                    "target": target,
                    "animated": True,
                    "sourceHandle": "right",
                }
            )

    conditional = {
        "id": f"edge-{node_id}-enter",
        "source": spec["source"],
        "target": node_id,
        "animated": True,
        "sourceHandle": "right",
        "data": {
            "condition": cg_condition(url, spec["title"], False)
        },
    }
    # 同一來源的有條件邊必須排在原本的無條件續接邊之前。
    edges[:] = [edge for edge in edges if edge.get("id") != conditional["id"]]
    first = next(
        (i for i, edge in enumerate(edges) if edge.get("source") == spec["source"]),
        len(edges),
    )
    edges.insert(first, conditional)


def main() -> None:
    project, project_etag = request()
    original_board_counts = {
        board["id"]: len(board.get("nodes", [])) for board in project.get("boards", [])
    }
    media = by_filename(project)
    missing = [spec["file"] for spec in CGS if not media.get(spec["file"])]
    if "bg-catgrass-home-corrected.jpg" not in media:
        missing.append("bg-catgrass-home-corrected.jpg")
    if missing:
        raise RuntimeError(f"Larch 素材庫缺少：{missing}")

    settings = project.setdefault("settings", {})
    gallery = settings.setdefault("cgGalleryItems", [])
    gallery_by_title = {item.get("title"): item for item in gallery}
    for spec in CGS:
        url = media[spec["file"]]
        if spec["title"] in gallery_by_title:
            gallery_by_title[spec["title"]].update({"url": url, "locked": True})
        else:
            gallery.append({"url": url, "title": spec["title"], "locked": True})
    settings["cgGalleryEnabled"] = True
    settings["cgGallerySource"] = "picked"
    obsolete_variables = {
        f"cg_story_{spec['key'].replace('-', '_')}_unlocked" for spec in CGS
    }
    project["variables"] = [
        variable
        for variable in project.get("variables", [])
        if variable.get("name") not in obsolete_variables
    ]

    # 專案層只寫設定與變數；版子使用各自的更新端點，避免混淆 active board。
    request("", "PUT", {"project": project}, project_etag)

    boards = {board["id"]: board for board in project["boards"]}
    new_catgrass = media["bg-catgrass-home-corrected.jpg"]
    for node in boards["board-main"]["nodes"]:
        data = node.get("data", {})
        for key in ("background", "backgroundNight"):
            if data.get(key) == CATGRASS_OLD:
                data[key] = new_catgrass

    for spec in CGS:
        add_unlock(boards[spec["board"]], spec, media[spec["file"]])

    summaries = {
        "board-main": "九張調查篇紀念 CG 改用跨周目收藏判斷，已解鎖不重播",
        "board-credits": "調查篇全員謝幕 CG 改用跨周目收藏判斷，已解鎖不重播",
    }
    for board_id in ("board-main", "board-credits"):
        current, etag = request(f"/boards/{board_id}")
        current = current.get("board", current)
        board = boards[board_id]
        # 寫入前再次確認版子沒有在剛才被別處修改。
        if len(current.get("nodes", [])) != original_board_counts[board_id]:
            raise RuntimeError(f"{board_id} 在處理期間被修改，已停止寫入")
        payload = {
            "name": board.get("name", current.get("name", board_id)),
            "kind": board.get("kind", current.get("kind", "story")),
            "mode": board.get("mode", current.get("mode", "story")),
            "nodes": boards[board_id]["nodes"],
            "edges": boards[board_id]["edges"],
            "summary": summaries[board_id],
        }
        request(f"/boards/{board_id}", "PUT", payload, etag)

    print("10 張調查篇 CG 已改為直接查詢跨周目收藏；已解鎖時不再重播。")


if __name__ == "__main__":
    main()
