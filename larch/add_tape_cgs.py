#!/usr/bin/env python3
"""五卷錄音帶各配一張 CG：三張新的（諾亞、斑比、店員）掛上線，兩張既有的（材料行老闆、保全）換成有錄音機的版本。

**先讀線上再補**（跟 larch/add_relationship_cgs.py 同一種寫法）：不重建、不整包推，樂園那些卡原封不動。
解鎖卡掛在該場錄音那一格的來源卡後面（錄音機 grant-item 之後、回板之前的最後一張玩家卡），
條件「這張 CG 還沒收」才進，進了再接回原本的出口（跨周目不重播）。

    python3 larch/add_tape_cgs.py --dry     # 只印會掛在哪張卡後面
    python3 larch/add_tape_cgs.py
"""
import argparse, base64, json, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "larch/inv"))
PROJECT_ID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BOARD_ID = "board-main"
BASE = f"https://larch.ink/api/agent/projects/{PROJECT_ID}"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()

# 段落標籤（design 選單標籤）→ CG。file 在 art/inv-cg。
NEW = [
    # 換圖要用新檔名：媒體庫照檔名快取，同名會拿到舊圖。v2＝帶俯視圖與固定道具圖重畫（art/inv-cg/CG畫法.md）
    # v3／v4：錄音機立起來、按鍵在頂邊（第二版寫「lying」被畫成平躺）
    {"key": "tape-noah",  "title": "頂樓・錄音機開著",   "label": "問諾亞那個穿西裝的", "file": "cg-tape-noah-v2.webp"},
    # bambi v5：v4 改太多次出現波紋，改從立繪＋俯視圖＋道具圖全新生成
    {"key": "tape-bambi", "title": "工作室・她一個人住嗎", "label": "問斑比她一個人住嗎", "file": "cg-tape-bambi-v5.webp"},
    # clerk v4：背景照 bg-store-night（台灣 7-11 亮色調），v3 被畫成灰暗倉庫
    {"key": "tape-clerk", "title": "便利商店・穿西裝的那個", "label": "問店員那個穿西裝的", "file": "cg-tape-clerk-v4.webp"},
]
# 既有 CG 換圖（標題不變，收藏格不變，只換 url）
REPLACE = [
    {"title": "她記得零件", "file": "cg-tape-parts-v4.webp"},   # v3：道具放在看得見的水平檯面上；v4：按鍵一紅三黑
    {"title": "保全的手機", "file": "cg-tape-guard-v3.webp"},
    # 劇情 CG 也能從這裡換圖（解鎖卡的命名跟 add_story_cgs.py 同形）：v3 袖口不再抄格莉奇、線圈筆記本換守則本
    {"title": "這集有我", "file": "cg-story-this-episode-v3.webp"},
]


def request(path="", method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        headers["If-Match"] = etag
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data, headers, method=method), timeout=300) as r:
        raw = r.read()
        return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def upload(fn):
    p = ROOT / "art/inv-cg" / fn
    body = {"name": fn, "mimeType": "image/webp", "category": "cg", "base64": base64.b64encode(p.read_bytes()).decode()}
    r, _ = request("/media", "POST", body)
    return r["asset"]["url"]


def base36(n):
    s = "0123456789abcdefghijklmnopqrstuvwxyz"; out = ""
    while n:
        out = s[n % 36] + out; n //= 36
    return out or "0"


def cg_key(url):
    v = 2166136261
    for ch in url:
        v ^= ord(ch); v = (v * 16777619) & 0xFFFFFFFF
    return f"__larch_cg__:{base36(len(url))}-{base36(v)}"


def cg_condition(url, title):
    leaf = {"variable": cg_key(url), "variableLabel": title, "op": "eq", "value": False}
    return {"kind": "variable", **leaf, "match": "all", "conditions": [leaf]}


def source_card(board, label):
    """該場的來源卡：從 pick 邊進段落，沿邊走到 grant-item（錄音機）之後、回板之前的最後一張對話卡。"""
    import sim as S
    r = next(r for r in S.rules if (r.get("label") or r["section"]) == label)
    by = {n["id"]: n for n in board["nodes"]}
    entry = next(e["target"] for e in board["edges"] if e.get("data", {}).get("condition", {}).get("value") == r["segment"])
    # 先找 grant-item 卡（走「開錄音機」那條）
    seen, fr, grant = set(), [entry], None
    while fr and not grant:
        c = fr.pop(0)
        if c in seen or c not in by:
            continue
        seen.add(c)
        if by[c]["data"].get("pluginCardId") == "grant-item":
            grant = c; break
        fr += [e["target"] for e in board["edges"] if e["source"] == c and by.get(e["target"], {}).get("data", {}).get("type") != "boardJump"]
    cur, last = grant or entry, grant or entry
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        d = by[cur]["data"]
        if d.get("type") == "dialogue":
            last = cur
        nxt = [e for e in board["edges"] if e["source"] == cur]
        nxt = [e for e in nxt if by.get(e["target"], {}).get("data", {}).get("type") != "boardJump"] or nxt
        if not nxt or by[nxt[0]["target"]]["data"].get("type") == "boardJump":
            break
        cur = nxt[0]["target"]
    return last


def add_unlock(board, spec, url):
    nodes, edges = board["nodes"], board["edges"]
    by = {n["id"]: n for n in nodes}
    src = spec["source"]
    node_id = f"story-cg-unlock-{spec['key']}"
    node = by.get(node_id)
    if node is None:
        pos = by[src].get("position", {"x": 0, "y": 0})
        node = {"id": node_id, "type": "story", "position": {"x": pos.get("x", 0) + 180, "y": pos.get("y", 0) + 280}, "data": {"type": "setVariable"}}
        nodes.append(node)
    node["data"].update({"title": f"解鎖：{spec['title']}", "text": "新的調查篇紀念 CG 已加入收藏。",
                         "cgOps": [{"id": f"op-{node_id}-gallery", "url": url, "mode": "unlock"}]})
    node["data"].pop("variableOps", None)
    enter_id = f"edge-{node_id}-enter"; clone_prefix = f"edge-{node_id}-continue-"
    edges[:] = [e for e in edges if e.get("id") != enter_id and not e.get("id", "").startswith(clone_prefix)]
    outgoing = [e for e in edges if e.get("source") == src]
    enter = {"id": enter_id, "source": src, "target": node_id, "sourceHandle": "right", "animated": True, "data": {"condition": cg_condition(url, spec["title"])}}
    first = next((i for i, e in enumerate(edges) if e.get("source") == src), len(edges))
    edges.insert(first, enter)
    for i, old in enumerate(outgoing):
        clone = dict(old); clone.update({"id": f"{clone_prefix}{i}", "source": node_id, "sourceHandle": "right"})
        edges.append(clone)


def put_board(board, why):
    for attempt in range(5):
        payload, etag = request(f"/boards/{BOARD_ID}")
        try:
            request(f"/boards/{BOARD_ID}", "PUT", {"name": board.get("name", BOARD_ID), "kind": board.get("kind", "story"), "mode": board.get("mode", "story"),
                                                 "nodes": board["nodes"], "edges": board["edges"], "summary": why}, etag)
            return
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            time.sleep(2)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    payload, _ = request(f"/boards/{BOARD_ID}"); board = payload.get("board", payload)
    n0 = (len(board["nodes"]), len(board["edges"]))
    by = {n["id"]: n for n in board["nodes"]}
    for spec in NEW:
        spec["source"] = source_card(board, spec["label"])
        d = by[spec["source"]]["data"]
        print(f"{spec['title']} ← {spec['source']} {d.get('speaker')}：{(d.get('text') or '')[:30]!r}")
    if a.dry:
        return 0
    # 換圖那兩張的檔還沒生好的話先跳過，之後再跑一次只補它們（NEW 那邊靠 id 冪等）
    REPLACE[:] = [s for s in REPLACE if (ROOT / "art/inv-cg" / s["file"]).exists()]
    project, _ = request(); project = project.get("project", project)
    known = {m.get("name"): m.get("url") for m in project.get("media", [])}
    urls = {s["file"]: known.get(s["file"]) or upload(s["file"]) for s in NEW + REPLACE}
    # 專案：收藏格（新增三格、換兩格的圖）
    project, etag = request(); project = project.get("project", project)
    gallery = project.setdefault("settings", {}).setdefault("cgGalleryItems", [])
    by_title = {it.get("title"): it for it in gallery}
    for s in NEW:
        item = {"title": s["title"], "url": urls[s["file"]], "locked": True}
        (by_title[s["title"]].update(item) if s["title"] in by_title else gallery.append(item))
    for s in REPLACE:
        if s["title"] in by_title:
            by_title[s["title"]]["url"] = urls[s["file"]]
    project["settings"]["cgGalleryEnabled"] = True
    request("", "PUT", {"project": project, "summary": "五卷錄音帶各一張 CG：新增三格、換兩格的圖"}, etag)
    # 版子：三張新解鎖卡；兩張既有解鎖卡換 url
    for s in NEW:
        add_unlock(board, s, urls[s["file"]])
    for n in board["nodes"]:
        for op in n["data"].get("cgOps") or []:
            for s in REPLACE:
                if n["data"].get("title") == f"解鎖：{s['title']}":
                    op["url"] = urls[s["file"]]
        # 進解鎖卡的邊條件也綁 url，一起換
    for e in board["edges"]:
        c = e.get("data", {}).get("condition") or {}
        for s in REPLACE:
            tgt = f"story-cg-unlock-{s['title']}"   # 既有的 id 不是這個形狀，靠 variableLabel 對
        if c.get("variableLabel") in {s["title"] for s in REPLACE}:
            s = next(s for s in REPLACE if s["title"] == c["variableLabel"])
            e["data"]["condition"] = cg_condition(urls[s["file"]], s["title"])
    put_board(board, "五卷錄音帶各一張 CG：三張新解鎖卡、兩張換圖")
    back, _ = request(f"/boards/{BOARD_ID}"); back = back.get("board", back)
    n1 = (len(back["nodes"]), len(back["edges"]))
    print(f"版子 {n0[0]}→{n1[0]} 卡、{n0[1]}→{n1[1]} 邊（預期 +3 卡、+3+複製的出口邊）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
