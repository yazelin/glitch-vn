#!/usr/bin/env python3
"""把立繪差分掛到線上版子（larch/inv/poses.py 的規則）。先讀線上再改，**只改舞台上那個人的圖片網址**。

    python3 larch/apply_poses.py --dry            # 只印表：哪張卡、誰、換哪張；不上傳、不寫
    python3 larch/apply_poses.py --backup 備份.json   # 先把 GET /projects 存下來，再改；改完逐張比對只有 url 變

保證：卡數、邊數不變；每張被改的卡除了 stage.actors[].url／characterLayers[].url 之外一個位元都不變（改完會驗，不符就報錯）。
回滾：python3 larch/apply_poses.py --restore 備份.json   （把那幾張卡的 url 放回備份裡的值）
"""
import argparse, base64, json, pathlib, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "larch/inv")); sys.path.insert(0, str(ROOT / "tools"))
import poses as P

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


def segments_of(board):
    """線上版子的段落：從每條 pick 邊（條件值 segNNN）進去沿邊走到回板，照發現順序；結局從收尾插播走。"""
    import sim as S
    by = {n["id"]: n for n in board["nodes"]}; out = {}
    for e in board["edges"]:
        out.setdefault(e["source"], []).append(e)

    def chain(start):
        seen, order, fr = set(), [], [start]
        while fr:
            c = fr.pop(0)
            if c in seen or c not in by:
                continue
            seen.add(c); order.append(by[c])
            if by[c]["data"].get("type") == "boardJump":
                continue
            fr += [e["target"] for e in out.get(c, [])]
        return order
    segs = set(r["segment"] for r in S.rules)
    starts = [e["target"] for e in board["edges"] if (e.get("data", {}).get("condition") or {}).get("value") in segs]
    starts += [n["id"] for n in board["nodes"] if n["data"].get("type") == "interrupt"]
    return [chain(s) for s in starts]


def upload(rel):
    p = ROOT / rel
    body = {"name": p.name, "mimeType": "image/png", "category": "character", "base64": base64.b64encode(p.read_bytes()).decode()}
    r, _ = request("/media", "POST", body)
    return r["asset"]["url"]


TABLE = ROOT / "design/調查篇-立繪姿勢.tsv"


def plan(board):
    """回傳 [(card_id, 誰, 姿勢, 演員索引)]。**來源是表**（tools/pose_table.py 產、人審過）：決定欄有值用決定，空的用提案；
    base 或沒有差分檔的組合就不換。只列舞台上真的有那個人的卡。"""
    import csv
    want = {}
    for r in csv.DictReader(open(TABLE, encoding="utf-8"), delimiter="\t"):
        pose = (r.get("決定") or r["提案"]).strip()
        if pose and pose != "base" and (r["誰"], pose) in P.FILES:
            want[(r["卡"], r["誰"])] = pose
    by = {n["id"]: n for n in board["nodes"]}
    rows = []
    for (cid, who), pose in want.items():
        if cid not in by:
            print(f"  ★ 表裡的卡不在線上：{cid}"); continue
        actors = (by[cid]["data"].get("stage") or {}).get("actors") or []
        for i, a in enumerate(actors):
            if P.who_of_name(a.get("name")) == who:
                rows.append((cid, who, pose, i))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--backup"); ap.add_argument("--restore")
    a = ap.parse_args()
    payload, etag = request(f"/boards/{BOARD_ID}"); board = payload.get("board", payload)
    n0 = (len(board["nodes"]), len(board["edges"]))
    by = {n["id"]: n for n in board["nodes"]}

    if a.restore:
        snap = json.loads(pathlib.Path(a.restore).read_text(encoding="utf-8")); snap = snap.get("project", snap)
        old = {n["id"]: n for b in snap["boards"] if b["id"] == BOARD_ID for n in b["nodes"]}
        changed = 0
        for cid, n in by.items():
            o = old.get(cid)
            if not o:
                continue
            for k in ("stage", "characterLayers"):
                if json.dumps(n["data"].get(k), sort_keys=True) != json.dumps(o["data"].get(k), sort_keys=True):
                    n["data"][k] = o["data"].get(k); changed += 1
        print(f"回滾 {changed} 處")
        rows = []
    else:
        rows = plan(board)
        from collections import Counter
        c = Counter((w, p) for _, w, p, _ in rows)
        print(f"要換的卡 {len(set(r[0] for r in rows))} 張、演員 {len(rows)} 個：", "、".join(f"{w}-{p} {n}" for (w, p), n in sorted(c.items())))
        for cid, who, pose, i in rows:
            d = by[cid]["data"]; t = (d.get("text") or (d.get("dialogueLines") or [{}])[0].get("text") or "")[:28].replace("\n", "／")
            print(f"  {cid:<10}{who:<4}{pose:<7}{d.get('speaker') or '':<7}{t}")
        if a.dry:
            return 0
        if a.backup:
            proj, _ = request()
            pathlib.Path(a.backup).write_text(json.dumps(proj, ensure_ascii=False), encoding="utf-8"); print("備份", a.backup)
        proj, _ = request(); proj = proj.get("project", proj)
        known = {m.get("name"): m.get("url") for m in proj.get("media", [])}
        urls = {}
        for key, rel in P.FILES.items():
            name = pathlib.Path(rel).name
            urls[key] = known.get(name) or upload(rel)
        before = {n["id"]: json.dumps(n, ensure_ascii=False, sort_keys=True) for n in board["nodes"]}
        for cid, who, pose, i in rows:
            d = by[cid]["data"]; u = urls[(who, pose)]
            d["stage"]["actors"][i]["url"] = u
            layers = d.get("characterLayers") or []
            if i < len(layers):
                layers[i]["url"] = u
        # 保險：除了那兩個 url 之外沒有東西變
        for n in board["nodes"]:
            if before[n["id"]] == json.dumps(n, ensure_ascii=False, sort_keys=True):
                continue
            o = json.loads(before[n["id"]]); nn = json.loads(json.dumps(n, ensure_ascii=False))
            for k in ("stage", "characterLayers"):
                o["data"].pop(k, None); nn["data"].pop(k, None)
            assert json.dumps(o, sort_keys=True) == json.dumps(nn, sort_keys=True), f"{n['id']} 有 url 以外的改動"
            # 而且 stage 裡除了 url 也不可以動
            oa = json.loads(before[n["id"]])["data"]; na = n["data"]
            strip = lambda s: json.dumps([{k: v for k, v in x.items() if k != "url"} for x in (s or {}).get("actors", [])], sort_keys=True)
            assert strip(oa.get("stage")) == strip(na.get("stage")), f"{n['id']} 舞台除了 url 還有別的改動"
    for attempt in range(5):
        try:
            request(f"/boards/{BOARD_ID}", "PUT", {"name": board.get("name", BOARD_ID), "kind": board.get("kind", "story"), "mode": board.get("mode", "story"),
                                                 "nodes": board["nodes"], "edges": board["edges"], "summary": "立繪差分：只換舞台上那個人的圖片網址"}, etag)
            break
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            time.sleep(2); payload, etag = request(f"/boards/{BOARD_ID}")
    back, _ = request(f"/boards/{BOARD_ID}"); back = back.get("board", back)
    print(f"回讀：卡 {len(back['nodes'])}/{n0[0]}　邊 {len(back['edges'])}/{n0[1]}", "一致" if (len(back["nodes"]), len(back["edges"])) == n0 else "!! 不一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
