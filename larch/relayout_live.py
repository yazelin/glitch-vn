#!/usr/bin/env python3
"""線上白板重排：只動卡片的 position／parentId／extent 與群組框的大小，**不動任何邊、不動任何卡片內容**。

排法跟 push.py 的「版面：人看得懂的白板」同一套：
  上面幾列＝樞紐（調查板、休息、筆記、錄音播放、各種插播）；
  中間一排群組＝每個地點一個「故事區段」框：第一列選單＋回板，再來入口場景走出來的卡，再來每個段落一列（一列最多 WRAP 張）；
  遊樂園自成一框；開場那段在最下面一列。
後來零星補上去的卡（CG 解鎖卡、清場卡、錄音帶 CG…）都在段落的走法裡，會自動排進該地點的框。

    python3 larch/relayout_live.py --dry [--snapshot 備份.json]   # 只算、畫預覽圖、印統計，不推
    python3 larch/relayout_live.py                                # 推之前先自己對：邊、卡片 data 一個位元都沒變才推

推之前請先備份：GET /projects 存成 larch/inv/backups/inv-live-<時間>.json（2026-09-17 他要求的）。
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BOARD_ID = "board-main"
BASE = f"https://larch.ink/api/agent/projects/{PROJECT_ID}"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()

CW, CH, WRAP, PAD = 360, 240, 8, 40


def request(path="", method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        headers["If-Match"] = etag
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data, headers, method=method), timeout=300) as r:
        raw = r.read()
        return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def layout(nodes, edges):
    by_id = {n["id"]: n for n in nodes}
    out_edges, in_edges = {}, {}
    for e in edges:
        out_edges.setdefault(e["source"], []).append(e); in_edges.setdefault(e["target"], []).append(e)
    board_id = next(n["id"] for n in nodes if "function walkMap()" in (n["data"].get("miniGameHtml") or ""))
    menus = [n["id"] for n in nodes if n["data"].get("type") == "miniGame" and (n["data"].get("title") or "").startswith("選單：")]
    groups_old = {n["id"]: n for n in nodes if n["data"].get("type") == "group"}
    placed = {}

    def chain(start_id, stop=lambda nid: False):
        seen, order, stack = set(), [], [start_id]
        while stack:
            nid = stack.pop(0)
            if nid in seen or nid not in by_id or stop(nid):
                continue
            seen.add(nid); order.append(nid)
            for e in out_edges.get(nid, []):
                stack.append(e["target"])
        return order

    def put(nid, x, y, parent=None):
        n = by_id[nid]
        n["position"] = {"x": x, "y": y}
        if parent:
            n["parentId"] = parent; n["extent"] = "parent"
        else:
            n.pop("parentId", None); n.pop("extent", None)
        placed[nid] = True

    # 左欄：系統卡與插播
    put(board_id, 0, 0)
    y = CH
    for nid in ("inv-rest", "inv-notes-int", "inv-notes"):
        if nid in by_id:
            put(nid, 0 if nid != "inv-notes" else CW, y if nid != "inv-notes" else y - CH)
            if nid != "inv-notes":
                y += CH
    if "inv-tape-int" in by_id:
        put("inv-tape-int", 0, y)
        tapes = [n["id"] for n in nodes if n["id"].startswith("inv-tape-rec_")]
        for i, t in enumerate(tapes):
            put(t, CW * (1 + i % 3), y + CH * (i // 3))
        if "inv-tape-none" in by_id:
            put("inv-tape-none", 0, y + CH * ((len(tapes) + 2) // 3))
        y += CH * ((len(tapes) + 2) // 3 + 1)
    for n in nodes:
        if n["data"].get("type") == "interrupt" and n["id"] not in placed:
            ids = [x for x in chain(n["id"], stop=lambda nid: nid in placed)]
            for i, nid in enumerate(ids):
                put(nid, CW * (i % WRAP), y + CH * (i // WRAP))
            y += CH * ((len(ids) + WRAP - 1) // WRAP)
    hub_h = y

    # 地點群組
    groups, entry_slots = [], []
    gx, gy = 0, hub_h + CH * 3
    group_h = 0

    def group_box(gid, title, rows, color):
        nonlocal gx, group_h
        width = PAD * 2 + CW * max(len(r) for r in rows)
        height = PAD * 2 + CH * len(rows) + 40
        g = groups_old.get(gid) or {"id": gid, "type": "story", "data": {"type": "group", "title": title, "text": "", "groupColor": color}}
        g.update({"position": {"x": gx, "y": gy}, "width": width, "height": height, "style": {"width": width, "height": height}})
        g.pop("parentId", None); g.pop("extent", None)
        groups.append(g)
        for r_i, row in enumerate(rows):
            for c_i, nid in enumerate(row):
                if nid in by_id:
                    put(nid, PAD + CW * c_i, PAD + 40 + CH * r_i, parent=gid)
        gx += width + CW
        group_h = max(group_h, height)

    for m in menus:
        loc_name = by_id[m]["data"]["title"].split("：", 1)[1]
        gid = next((g for g in groups_old if groups_old[g]["data"].get("title") == loc_name), f"grp-{loc_name}")
        rows = [[m] + [x for x in (f"{m}-back",) if x in by_id]]
        entries = [e["source"] for e in in_edges.get(m, []) if e["source"] != board_id and by_id[e["source"]]["data"].get("type") == "scene"]
        entry_slots.append((entries, gx))
        for en in entries:
            ids = [x for x in chain(en, stop=lambda nid: nid == m or nid in placed) if x != en]
            for k in range(0, len(ids), WRAP):
                rows.append(ids[k:k + WRAP])
            for nid in ids:
                placed[nid] = True
        for se in [e["target"] for e in out_edges.get(m, []) if e.get("data")]:
            ids = chain(se, stop=lambda nid: nid in placed or nid == m)
            for k in range(0, len(ids), WRAP):
                rows.append(ids[k:k + WRAP])
            for nid in ids:
                placed[nid] = True
        group_box(gid, loc_name, rows, "#667257")

    # 遊樂園：自成一框，從被外面接進來的那張開始走
    park = [n["id"] for n in nodes if n["id"].startswith("inv-park-")]
    if park:
        entry = next((p for p in park if any(e["source"] not in park for e in in_edges.get(p, []))), park[0])
        ids = [x for x in chain(entry, stop=lambda nid: nid in placed or not nid.startswith("inv-park-"))]
        ids += [p for p in park if p not in ids]
        rows = [ids[k:k + WRAP] for k in range(0, len(ids), WRAP)]
        group_box(next((g for g in groups_old if groups_old[g]["data"].get("title") == "遊樂園"), "grp-park"), "遊樂園", rows, "#6b5a7a")

    # 入口場景：各自群組正上方一列
    for entries, x0 in entry_slots:
        for i, en in enumerate(entries):
            put(en, x0 + PAD + CW * i, gy - CH * 2)

    # 開場那段：最下面一列
    start_ids = [n["id"] for n in nodes if n["data"].get("start")]
    opening = chain(start_ids[0], stop=lambda nid: nid == board_id or nid in placed) if start_ids else []
    for i, nid in enumerate(opening):
        put(nid, CW * (i % 24), gy + group_h + CH * 2 + CH * (i // 24))

    # 沒排到的：樞紐列下面一列，橫著排
    rest = [n["id"] for n in nodes if n["id"] not in placed and n["data"].get("type") != "group"]
    for i, nid in enumerate(rest):
        put(nid, CW * (i % 24), hub_h + CH * (i // 24))
    gids = {g["id"] for g in groups}
    others = [n for n in nodes if n["data"].get("type") == "group" and n["id"] not in gids]
    body = [n for n in nodes if n["data"].get("type") != "group"]
    nodes[:] = groups + others + body            # 群組要排在子卡前面
    return {"groups": [(g["data"]["title"], sum(1 for n in nodes if n.get("parentId") == g["id"])) for g in groups],
            "rest": rest, "opening": len(opening), "hub_rows": hub_h // CH, "old_groups_unused": [g["id"] for g in others]}


def preview(nodes, path):
    from PIL import Image, ImageDraw
    xs = [n["position"]["x"] for n in nodes]; ys = [n["position"]["y"] for n in nodes]
    x0, y0 = min(xs) - 400, min(ys) - 400
    W = max(xs) - x0 + 800; H = max(ys) - y0 + 800; s = 5000 / max(W, H)
    im = Image.new("RGB", (int(W * s) + 1, int(H * s) + 1), "white"); d = ImageDraw.Draw(im)
    by = {n["id"]: n for n in nodes}
    for n in nodes:
        if n["data"].get("type") == "group":
            p = n["position"]; d.rectangle([(p["x"] - x0) * s, (p["y"] - y0) * s, (p["x"] - x0 + n["width"]) * s, (p["y"] - y0 + n["height"]) * s], outline="green", width=2)
            d.text(((p["x"] - x0) * s + 4, (p["y"] - y0) * s + 2), n["data"]["title"], fill="green")
    for n in nodes:
        if n["data"].get("type") == "group":
            continue
        p = dict(n["position"])
        if n.get("parentId") and n["parentId"] in by:
            gp = by[n["parentId"]]["position"]; p = {"x": p["x"] + gp["x"], "y": p["y"] + gp["y"]}
        c = {"boardJump": "gray", "setVariable": "orange", "interrupt": "red", "miniGame": "blue", "scene": "purple", "choice": "brown", "plugin": "teal"}.get(n["data"].get("type"), "black")
        d.rectangle([(p["x"] - x0) * s, (p["y"] - y0) * s, (p["x"] - x0 + 280) * s, (p["y"] - y0 + 140) * s], fill=c)
    im.save(path)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--snapshot"); a = ap.parse_args()
    if a.snapshot:
        p = json.loads(pathlib.Path(a.snapshot).read_text(encoding="utf-8")); p = p.get("project", p)
        board, etag = next(b for b in p["boards"] if b["id"] == BOARD_ID), None
    else:
        payload, etag = request(f"/boards/{BOARD_ID}"); board = payload.get("board", payload)
    before_edges = json.dumps(board["edges"], ensure_ascii=False, sort_keys=True)
    before_data = {n["id"]: json.dumps(n["data"], ensure_ascii=False, sort_keys=True) for n in board["nodes"]}
    n0 = len(board["nodes"])
    stats = layout(board["nodes"], board["edges"])
    # 推之前的保險：邊一個位元沒動、每張卡的 data 沒動、卡數不變（除了新開的群組框）
    assert json.dumps(board["edges"], ensure_ascii=False, sort_keys=True) == before_edges, "邊被動到了"
    changed = [n["id"] for n in board["nodes"] if n["id"] in before_data and json.dumps(n["data"], ensure_ascii=False, sort_keys=True) != before_data[n["id"]]]
    assert not changed, f"卡片內容被動到了：{changed[:5]}"
    new_groups = [n["id"] for n in board["nodes"] if n["id"] not in before_data]
    print(f"卡 {n0}→{len(board['nodes'])}（新群組框 {new_groups}）、邊不動")
    for t, c in stats["groups"]:
        print(f"  {t}：{c} 張")
    print(f"  開場 {stats['opening']} 張、樞紐 {stats['hub_rows']} 列、沒排到（另列）{len(stats['rest'])} 張 {stats['rest'][:8]}、閒置舊群組 {stats['old_groups_unused']}")
    out = ROOT / "larch/inv/backups/relayout-preview.png"; preview(board["nodes"], out); print("預覽圖", out)
    if a.dry:
        return 0
    for attempt in range(5):
        try:
            request(f"/boards/{BOARD_ID}", "PUT", {"name": board.get("name", BOARD_ID), "kind": board.get("kind", "story"), "mode": board.get("mode", "story"),
                                                 "nodes": board["nodes"], "edges": board["edges"], "summary": "白板重排：只動位置與群組，邊與卡片內容不動"}, etag)
            break
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            time.sleep(2); payload, etag = request(f"/boards/{BOARD_ID}")
    back, _ = request(f"/boards/{BOARD_ID}"); back = back.get("board", back)
    print(f"回讀：卡 {len(back['nodes'])}　邊 {len(back['edges'])}",
          "邊一致" if json.dumps(back["edges"], ensure_ascii=False, sort_keys=True) == before_edges else "!! 邊不一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
