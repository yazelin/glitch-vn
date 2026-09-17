#!/usr/bin/env python3
"""線上補段落收尾清場卡（larch/inv/clear_stage.py）：先讀線上版子再插、再放回去。樂園那些卡原封不動。

    python3 larch/add_clear_stage.py --dry
    python3 larch/add_clear_stage.py
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "larch/inv"))
import clear_stage as CS

PROJECT_ID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BOARD_ID = "board-main"
BASE = f"https://larch.ink/api/agent/projects/{PROJECT_ID}"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()


def request(path="", method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        headers["If-Match"] = etag
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data, headers, method=method), timeout=300) as r:
        raw = r.read()
        return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    payload, etag = request(f"/boards/{BOARD_ID}"); board = payload.get("board", payload)
    n0 = (len(board["nodes"]), len(board["edges"]))
    board_card = next(n["id"] for n in board["nodes"] if "function walkMap()" in (n["data"].get("miniGameHtml") or ""))
    ghost = next(a["url"] for n in board["nodes"] for a in (n["data"].get("stage") or {}).get("actors") or [] if a["id"] == "actor-none")
    n = CS.apply(board["nodes"], board["edges"], board_card, ghost)
    m = CS.apply_autorecord(board["nodes"], board["edges"])
    print(f"插 {n} 張清場卡、{m} 條劇情模式自動錄音邊（版子 {n0[0]}→{len(board['nodes'])} 卡、{n0[1]}→{len(board['edges'])} 邊）")
    if a.dry or not (n or m):
        return 0
    for attempt in range(5):
        try:
            request(f"/boards/{BOARD_ID}", "PUT", {"name": board.get("name", BOARD_ID), "kind": board.get("kind", "story"),
                                                 "mode": board.get("mode", "story"), "nodes": board["nodes"], "edges": board["edges"],
                                                 "summary": "段落收尾清場卡：回板前把台上的人清掉，手機橫幅跳出時畫面沒有人"}, etag)
            break
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            time.sleep(2); payload, etag = request(f"/boards/{BOARD_ID}")
    back, _ = request(f"/boards/{BOARD_ID}"); back = back.get("board", back)
    print(f"回讀：卡 {len(back['nodes'])}　邊 {len(back['edges'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
