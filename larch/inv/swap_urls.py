#!/usr/bin/env python3
"""把線上兩個版子裡的網址照對照表換掉（舊→新），做法同 patch_live.py。可重跑。

2026-09-18 第一次用：調查篇卡片上有 9 張圖是直接指到正篇專案的素材（斑比／貓草／鐵塔／0x／諾亞／
格莉奇／黑洞先生的立繪、謝幕背景、空白立繪），素材打包時抓不到、正篇清素材也會斷。
先把同一份檔上傳到調查篇專案，再用這支把卡片上的網址換過來。

    python3 larch/inv/swap_urls.py 對照表.json --dry
    python3 larch/inv/swap_urls.py 對照表.json
"""
import argparse, datetime, json, pathlib, sys, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_live import request  # noqa: E402

BOARDS = ("board-credits", "board-main")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map"); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    table = json.loads(pathlib.Path(a.map).read_text(encoding="utf-8"))
    for bid in BOARDS:
        payload, etag = request(f"/boards/{bid}")
        board = payload.get("board", payload)
        before = (len(board["nodes"]), len(board["edges"]))
        raw = json.dumps(board["nodes"], ensure_ascii=False)
        hits = {k: raw.count(k) for k in table if k in raw}
        print(f"{bid}：{sum(hits.values())} 處，{len(hits)} 個網址（卡 {before[0]}、邊 {before[1]}）")
        if a.dry or not hits:
            continue
        (HERE / "backups" / f"{bid}-{datetime.datetime.now():%Y%m%d-%H%M}-before-swap.json").write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
        for attempt in range(5):
            raw = json.dumps(board["nodes"], ensure_ascii=False)
            for k, v in table.items():
                raw = raw.replace(k, v)
            try:
                request(f"/boards/{bid}", "PUT", {"name": board.get("name", bid), "kind": board.get("kind", "story"),
                        "mode": board.get("mode", "story"), "nodes": json.loads(raw), "edges": board["edges"],
                        "summary": "swap_urls.py：正篇專案的立繪／背景改指調查篇自己上傳的那份"}, etag)
                break
            except urllib.error.HTTPError as e:
                if e.code != 409 or attempt == 4:
                    raise
                print(f"  409，重讀再送（第 {attempt + 1} 次）")
                payload, etag = request(f"/boards/{bid}"); board = payload.get("board", payload)
        back, _ = request(f"/boards/{bid}"); back = back.get("board", back)
        after = (len(back["nodes"]), len(back["edges"]))
        left = sum(json.dumps(back["nodes"], ensure_ascii=False).count(k) for k in table)
        print(f"  回讀：卡 {after[0]}/{before[0]}　邊 {after[1]}/{before[1]}　舊網址殘留 {left}", "一致" if after == before and not left else "★ 去查")
        assert after == before and not left


if __name__ == "__main__":
    main()
