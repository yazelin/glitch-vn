#!/usr/bin/env python3
"""CG 解鎖條件的鍵跟著收藏格的網址重算（2026-11-04 修遊樂園「離不開」）。

Larch 的 CG 條件變數寫成 `__larch_cg__:<鍵>`。收藏格沒填 conditionKey 的時候，鍵是照圖片網址算的：
網址長度的 36 進位 + "-" + 網址 FNV-1a（32 位元）的 36 進位（拿 2026-10-07 換網址前的備份驗過，27 個鍵全對）。
所以**換收藏圖的網址，條件就斷了**，而且不會報錯。10-07 素材改走 jsDelivr 之後：
- 遊樂園玩完一款，往 CG 那幾條線全部不成立，只剩接回自己那條，畫面停在遊戲裡（「離不開」）
- 16 張劇情 CG 與謝幕 CG 的「還沒解鎖就先繞去解鎖」那幾條線走不進去

這支照條件自己帶的 variableLabel（就是收藏格的標題）找現在的鍵換上。只改連接線上的條件，卡片不動。
swap_urls.py 換網址（--project）之後會自動跑這支。

    python3 larch/inv/fix_cg_keys.py --dry
    python3 larch/inv/fix_cg_keys.py
"""
import argparse, copy, datetime, json, pathlib, sys, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_live import request  # noqa: E402

BOARDS = ("board-credits", "board-f375ecf1-87ad-4a9c-b8fc-fb126c9c5000", "board-main")
PREFIX = "__larch_cg__:"


def b36(n):
    s, o = "0123456789abcdefghijklmnopqrstuvwxyz", ""
    while True:
        n, r = divmod(n, 36); o = s[r] + o
        if not n: return o


def cg_key(url):
    f = 2166136261
    for ch in url: f = ((f ^ ord(ch)) * 16777619) & 0xffffffff
    return f"{b36(len(url))}-{b36(f)}"


def keys_now(proj):
    """收藏格標題 → 現在的鍵（有 conditionKey 就用它）。"""
    return {it.get("title"): it.get("conditionKey") or cg_key(it["url"]) for it in proj["settings"].get("cgGalleryItems") or []}


def fix(edges, by_title):
    """就地改；回傳（換了幾處, 找不到標題的）。"""
    current, n, miss = set(by_title.values()), 0, []
    def walk(o):
        nonlocal n
        if isinstance(o, dict):
            v = o.get("variable")
            if isinstance(v, str) and v.startswith(PREFIX) and v[len(PREFIX):] not in current:
                k = by_title.get(o.get("variableLabel"))
                if k: o["variable"] = PREFIX + k; n += 1
                else: miss.append((v, o.get("variableLabel")))
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(edges)
    return n, miss


def run(dry):
    proj, _ = request(""); proj = proj.get("project", proj)
    by_title = keys_now(proj)
    for bid in BOARDS:
        payload, etag = request(f"/boards/{bid}"); board = payload.get("board", payload)
        if PREFIX in json.dumps(board["nodes"], ensure_ascii=False):
            print(f"  ★ {bid} 卡片裡也有 CG 條件，這支只改連接線，要另外看")
        edges = copy.deepcopy(board["edges"]); n, miss = fix(edges, by_title)
        print(f"{bid}：換 {n} 處" + (f"，對不到標題 {miss}" if miss else ""))
        if dry or not n: continue
        (HERE / "backups" / f"{bid}-{datetime.datetime.now():%Y%m%d-%H%M}-before-cgkeys.json").write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
        before = (len(board["nodes"]), len(board["edges"]))
        for attempt in range(5):
            try:
                request(f"/boards/{bid}", "PUT", {"name": board.get("name", bid), "kind": board.get("kind", "story"), "mode": board.get("mode", "story"),
                        "nodes": board["nodes"], "edges": edges, "summary": "CG 解鎖條件換成現在收藏格網址算出來的鍵（10-07 換 jsDelivr 後斷掉）"}, etag)
                break
            except urllib.error.HTTPError as e:
                if e.code != 409 or attempt == 4: raise
                print(f"  409，重讀再送（第 {attempt + 1} 次）")
                payload, etag = request(f"/boards/{bid}"); board = payload.get("board", payload)
                edges = copy.deepcopy(board["edges"]); fix(edges, by_title)
        back, _ = request(f"/boards/{bid}"); back = back.get("board", back)
        left, _ = fix(copy.deepcopy(back["edges"]), by_title)
        same_nodes = json.dumps(back["nodes"], sort_keys=True) == json.dumps(board["nodes"], sort_keys=True)
        print(f"  回讀：卡 {len(back['nodes'])}/{before[0]}　邊 {len(back['edges'])}/{before[1]}　還對不到的條件 {left}　卡片{'沒變' if same_nodes else '★ 有變'}")
        assert (len(back["nodes"]), len(back["edges"])) == before and not left


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    run(ap.parse_args().dry)
