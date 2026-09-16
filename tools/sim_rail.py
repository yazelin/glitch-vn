#!/usr/bin/env python3
"""照劇情軌道走一遍的模擬器：每個時段只去攻略指定的地點、只播攻略指定的那一格。

    python3 tools/sim_rail.py            # 訪客一律在場（黑洞先生、貓草那些機率）
    python3 tools/sim_rail.py --no-luck  # 機率訪客不在

跟 tools/sim.py 同一套變數規則（直接 import 它），差別是走法：sim.py 是貪婪把能開的全開，
這支是「玩家照劇情模式走」。印出來的是：軌道哪一格開不了（卡在哪個條件）、哪幾張劇情 CG
的來源卡有沒有走到、結局門檻的變數到哪裡。**不會開瀏覽器**——自動玩家（tools/autoplay.mjs）
在 CG 解鎖卡之後會無聲停住（2026-09-17，沒查出來），這支是它的替身。

CG 的來源卡是線上才有的解鎖卡掛在哪張卡後面（larch/add_*.py 補的），本機 board.json 沒有
那些解鎖卡，所以用來源卡的 id 對（id 兩邊一樣）。
"""
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "larch/inv"))
import sim as S
import build as B

# 劇情 CG → 解鎖卡掛在哪張卡後面（2026-09-17 從線上版子讀出來的；加 CG 要補這裡）
CG_SOURCE = {"金色的帽子": "inv-070", "斑比的牆": "inv-328", "深夜的便利商店": "inv-342", "兩分鐘": "inv-351",
             "第六次，仍然沒有印象": "inv-351", "我答應過他": "inv-408", "失物箱的空白守則本": "inv-423",
             "第七行": "inv-455", "四次": "inv-459", "這集有我": "inv-531", "保全的手機": "inv-060",
             "兩顆蘿蔔，一杯無糖": "inv-223", "她記得零件": "inv-245"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-luck", action="store_true")
    ap.add_argument("--live", help="GET /projects/:id 存下來的 JSON；把線上卡片的 variableOps 蓋到本機同 id 的卡上。"
                                   "管理員的 trust 是 larch/add_relationship_cgs.py 直接改在線上的，本機 board.json 沒有，不蓋的話 trust_管理員 永遠 0")
    a = ap.parse_args()
    luck = not a.no_luck
    if a.live:
        proj = json.loads(pathlib.Path(a.live).read_text(encoding="utf-8"))
        lb = next(x for x in proj["boards"] if x["id"] == "board-main")
        n_over = 0
        for n in lb["nodes"]:
            if n["id"] in S.nodes and n["data"].get("variableOps") != S.nodes[n["id"]]["data"].get("variableOps"):
                S.nodes[n["id"]]["data"]["variableOps"] = n["data"].get("variableOps", []); n_over += 1
        print(f"線上 variableOps 蓋過本機：{n_over} 張卡")
    V = {v["name"]: v["defaultValue"] for v in S.b["variables"]}
    V.setdefault("inventory", "[]")
    segs = {r["segment"]: r for r in S.rules}
    cache = {sid: S.seg_nodes(sid) for sid in segs}
    who_c = {sid: S.who_of(ns) for sid, ns in cache.items()}
    start = next(n["id"] for n in S.b["nodes"] if n["data"].get("start"))
    cur, opening, seen = start, [], set()
    while cur and cur not in seen:
        seen.add(cur); opening.append(S.nodes[cur])
        nxt = [e for e in S.edges if e["source"] == cur and not e.get("data")]
        cur = nxt[0]["target"] if nxt else None
    S.apply(opening, V)
    played_nodes = {n["id"] for n in opening}
    POSSIBLE = {loc: set(x for x in live if x) | {w for l, s2, w in S.VISITS if l == loc} for loc, live in S.LIVE.items()}
    CN = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十", 11: "十一", 12: "十二", 13: "十三"}

    def wrapup(n_day):
        intr = next((n for n in S.b["nodes"] if n["data"].get("type") == "interrupt" and n["data"]["title"] == f"第{CN.get(n_day, '')}天收尾"), None)
        if not intr:
            return
        cur, ns, seen = intr["id"], [], set()
        while cur and cur not in seen:
            seen.add(cur); ns.append(S.nodes[cur])
            nxt = [e for e in S.edges if e["source"] == cur and not e.get("data")]
            cur = nxt[0]["target"] if nxt else None
        S.apply(ns, V); played_nodes.update(n["id"] for n in ns)

    route, _ = B.load_route()
    steps = {(r["day"], r["slot"]): r for r in route}
    broken, chancy = [], []
    for day in range(1, 15):
        V["day"] = day
        if day >= 2:
            wrapup(day - 1)
        for slot in range(4):
            V["slot"] = slot
            if slot == 3 and day < 4:
                continue
            st = steps.get((day, slot))
            if not st:
                continue
            loc = st["loc"]
            # 軌道自己解鎖目的地（board.html 2026-09-17 的規則）
            if loc in S.GATE:
                V[S.GATE[loc]] = True
            live = S.LIVE[loc]
            if live[slot] is None:
                broken.append((day, slot, loc, st["label"], "這個時段沒開")); continue
            here = {live[slot]} if live[slot] else set()
            for l, s2, w in S.VISITS:
                if l == loc and s2 == slot:
                    if luck or w != "黑洞先生":
                        here.add(w)
                    chancy.append((day, slot, loc, w))
            for p in here:
                if p in ("路人", "黑洞先生"):
                    continue
                k = "met_" + ("材料行老闆" if p == "老闆" else p)
                V[k] = (S.norm(V.get(k, 0)) or 0) + 1
            if slot == 3:
                V["night_visits"] = (S.norm(V.get("night_visits", 0)) or 0) + 1
            if not st["label"]:
                continue                                  # 只是去一趟（算 met）
            cands = [r for r in S.rules if r["dest"] == loc and slot in r["slots"] and (r.get("label") or r["section"]) == st["label"]]
            if not cands:
                broken.append((day, slot, loc, st["label"], "選單上沒有這一格")); continue
            r = cands[0]
            bad = [(c["variable"], c["op"], c["value"], V.get(c["variable"])) for c in r["conds"] if not S.ok(V, c)]
            w = who_c[r["segment"]] & POSSIBLE[loc]
            if w and not (w & here):
                bad.append(("誰在", "需要", "、".join(sorted(w)), "、".join(sorted(here))))
            if bad:
                broken.append((day, slot, loc, st["label"], bad)); continue
            ns = cache[r["segment"]]
            S.apply(ns, V); played_nodes.update(n["id"] for n in ns)
    print(f"軌道 {len(route)} 步：開不了的 {len(broken)} 步" + ("" if luck else "（機率訪客不在）"))
    for x in broken:
        print("  ★", x)
    print("靠機率訪客的步：", [(d, s, l, w) for d, s, l, w in chancy if w != "黑洞先生"][:12])
    hit = {t: (src in played_nodes) for t, src in CG_SOURCE.items()}
    print("劇情 CG 來源卡走到：", sum(hit.values()), "/", len(hit))
    for t, ok_ in hit.items():
        print("  ", "✓" if ok_ else "✗", t)
    print("結局門檻：", {k: V.get(k) for k in ("day", "night_visits", "strikes", "names_seen", "trust_管理員", "trust_貓草", "trust_斑比", "hole_sightings")})
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
