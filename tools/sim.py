#!/usr/bin/env python3
"""帶變數狀態的模擬器：從 board.json 出發，看結局走不走得到、哪些段落永遠開不了。

    python3 tools/sim.py            # 貪婪走法：每個時段把所有能開的段落都走一遍
    python3 tools/sim.py --days 16

不是玩家會怎麼玩，是「規則有沒有把路堵死」。做法：
  一天四個時段，每個時段依序到每個地點，把當下能開的段落全部播掉（套它們的 variableOps），
  出門就照調查板那套加 met、night_visits、日期；筆記含刪除線加 strikes。
  最後印：走過幾段、沒走到的段落與它們卡在哪一個條件、結局有沒有開。
單純可達性抓不到的（例如 trust 永遠到不了 3）這裡抓得到。
"""
import argparse, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
b = json.loads((ROOT / "larch/inv/out/board.json").read_text(encoding="utf-8"))
nodes = {n["id"]: n for n in b["nodes"]}
edges = b["edges"]
rules = b["rules"]

# 調查板的常駐表（跟 larch/cards/board.html 一樣）
LIVE = {"lobby": ["管理員", "管理員", "", ""], "roof": ["諾亞", "諾亞", "諾亞", None],
        "street": ["路人"] * 3 + [""], "busstop": ["路人"] * 3 + [""], "metro": ["路人"] * 3 + [""],
        "store": ["店員"] * 4, "parts": ["老闆", "老闆", None, None], "laundry": [""] * 4,
        "figure": [None, "店員", "店員", None], "studio": [None, "斑比", "斑比", "斑比"],
        "booth": ["鐵塔", "鐵塔", None, None], "tower14": ["櫃檯", "櫃檯", "保全", "保全"]}
GATE = {"roof": "open_roof", "laundry": "open_laundry", "figure": "open_figure", "parts": "open_parts",
        "studio": "open_studio", "tower14": "open_tower14"}
VISITS = [("lobby", 2, "黑洞先生"), ("store", 3, "貓草"), ("store", 3, "鐵塔"), ("store", 2, "斑比"),
          ("figure", 1, "貓草"), ("figure", 2, "貓草"), ("laundry", 3, "貓草"), ("laundry", 2, "斑比"), ("parts", 1, "諾亞")]
NOT_WHO = {"玩家", "旁白", "格莉奇"}
WHO_MAP = {"材料行老闆": "老闆", "住戶": "路人", "路人乙": "路人", "高中生": "路人", "阿姨": "路人",
           "送貨的": "路人", "發傳單的": "路人", "上班族": "路人"}


def norm(v):
    if v in ("true", True):
        return True
    if v in ("false", False):
        return False
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


def ok(V, c):
    if "any" in c:
        return any(ok(V, a) for a in c["any"])
    return cmp(V.get(c["variable"]), c["op"], c["value"])


def cmp(a, op, bv):
    if op == "hasItem":
        return any(i.get("id") == bv for i in json.loads(a or "[]"))
    if op == "lacksItem":
        return not cmp(a, "hasItem", bv)
    a, bv = norm(a), norm(bv)
    if a is None or a == "":
        a = 0 if isinstance(bv, int) else False if isinstance(bv, bool) else ""
    try:
        return {"gt": a > bv, "gte": a >= bv, "lt": a < bv, "lte": a <= bv, "neq": a != bv}.get(op, a == bv)
    except TypeError:
        return False


def seg_nodes(sid):
    """段落的卡片：從 pick 邊的目標一路沿無條件邊走到回板卡"""
    entry = next((e["target"] for e in edges if e.get("data", {}).get("condition", {}).get("value") == sid), None)
    out, cur, seen = [], entry, set()
    while cur and cur not in seen:
        seen.add(cur)
        out.append(nodes[cur])
        nxt = [e for e in edges if e["source"] == cur]
        # 有條件的邊：rec_ok／inventoryLastUsed 那些先走預設；選擇卡走第一項
        plain = [e for e in nxt if not e.get("data")]
        cur = (plain[0]["target"] if plain else (nxt[0]["target"] if nxt else None))
    return out


def who_of(ns):
    who = set()
    for n in ns:
        d = n["data"]
        if d.get("remote"):
            continue
        for s in [d.get("speaker")] + [l.get("speaker") for l in d.get("dialogueLines", [])]:
            if s and s not in NOT_WHO:
                who.add(WHO_MAP.get(s, s))
    return who


def apply(ns, V):
    for n in ns:
        for o in n["data"].get("variableOps", []):
            if o["kind"] == "add":
                V[o["variable"]] = (norm(V.get(o["variable"], 0)) or 0) + o["value"]
            else:
                V[o["variable"]] = o["value"]
        if n["data"].get("pluginCardId") == "grant-item":
            inv = json.loads(V.get("inventory", "[]"))
            inv.append({"id": n["data"]["pluginValues"]["itemId"]})
            V["inventory"] = json.dumps(inv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=16)
    ap.add_argument("--luck", action="store_true", help="訪客一律在場（黑洞先生、貓草那些機率）")
    a = ap.parse_args()
    V = {v["name"]: v["defaultValue"] for v in b["variables"]}
    V.setdefault("inventory", "[]")
    played, log = set(), []
    segs = {r["segment"]: r for r in rules}
    cache = {sid: seg_nodes(sid) for sid in segs}
    who_c = {sid: who_of(ns) for sid, ns in cache.items()}
    # 開場那一段（固定，不在規則裡）：從 start 卡沿無條件邊走到回板卡
    start = next(n["id"] for n in b["nodes"] if n["data"].get("start"))
    cur, opening, seen = start, [], set()
    while cur and cur not in seen:
        seen.add(cur); opening.append(nodes[cur])
        nxt = [e for e in edges if e["source"] == cur and not e.get("data")]
        cur = nxt[0]["target"] if nxt else None
    apply(opening, V)
    POSSIBLE = {loc: set(x for x in live if x) | {w for l, s2, w in VISITS if l == loc} for loc, live in LIVE.items()}
    CN = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十", 11: "十一"}
    def wrapup(n_day):
        """換日插播的「第 N 天收尾」：從那張 interrupt 卡沿邊走完，套變數（刪除線在這裡）"""
        intr = next((n for n in b["nodes"] if n["data"].get("type") == "interrupt" and n["data"]["title"] == f"第{CN.get(n_day, '')}天收尾"), None)
        if not intr:
            return
        cur, ns, seen = intr["id"], [], set()
        while cur and cur not in seen:
            seen.add(cur); ns.append(nodes[cur])
            nxt = [e for e in edges if e["source"] == cur and not e.get("data")]
            cur = nxt[0]["target"] if nxt else None
        apply(ns, V)
    for day in range(1, a.days + 1):
        V["day"] = day
        if day >= 2:
            wrapup(day - 1)
        for slot in range(4):
            V["slot"] = slot
            if slot == 3 and day < 4:
                continue                       # 深夜第四天才亮
            for loc, live in LIVE.items():
                if loc in GATE and not norm(V.get(GATE[loc])):
                    continue
                if live[slot] is None or loc == "booth":
                    continue
                here = {live[slot]} if live[slot] else set()
                for l, s2, w in VISITS:
                    if l == loc and s2 == slot and (a.luck or w != "黑洞先生"):
                        here.add(w)
                # 出門：met
                for p in here:
                    if p in ("路人", "黑洞先生"):
                        continue
                    k = "met_" + ("材料行老闆" if p == "老闆" else p)
                    V[k] = (norm(V.get(k, 0)) or 0) + 1
                if slot == 3:
                    V["night_visits"] = (norm(V.get("night_visits", 0)) or 0) + 1
                for r in rules:
                    if r["dest"] != loc or slot not in r["slots"]:
                        continue
                    if any(not ok(V, c) for c in r["conds"]):
                        continue
                    w = who_c[r["segment"]] & POSSIBLE[loc]
                    if w and not (w & here):
                        continue
                    ns = cache[r["segment"]]
                    # 掉信任的段落（問第三次那種）是玩家自己選的，貪婪走法不走它
                    if any(o["kind"] == "add" and o["value"] < 0 for n in ns for o in n["data"].get("variableOps", [])):
                        continue
                    apply(ns, V)
                    if any("~~" in (n["data"].get("text") or "") for n in ns):
                        pass  # strikes 已經在 variableOps 裡
                    if r["segment"] not in played:
                        log.append((day, slot, loc, r["label"] if r.get("label") else r["section"][:20]))
                    played.add(r["segment"])
    never = [r for r in rules if r["segment"] not in played]
    print(f"走過 {len(played)} 段，沒走到 {len(never)} 段（{a.days} 天，{'訪客全在' if a.luck else '黑洞先生不在'}）")
    ending = [r for r in rules if "最後一頁" in r["section"] or "最後那一頁" in r["section"]]
    for r in ending:
        print("結局：", r["section"][:20], "開了" if r["segment"] in played else "沒開",
              [(c["variable"], c["op"], c["value"], V.get(c["variable"])) for c in r["conds"] if "any" not in c])
    print("關鍵變數：", {k: V.get(k) for k in ("day", "night_visits", "strikes", "clue_list", "trust_管理員", "trust_貓草", "trust_斑比", "met_諾亞", "met_管理員", "hole_sightings", "rec_ok")})
    for r in never[:40]:
        bad = [(c["variable"], c["op"], c["value"], V.get(c["variable"])) for c in r["conds"] if not ok(V, c)]
        w = who_c[r["segment"]]
        print(f"  ・{r['dest']:8s} {r['section'][:24]:26s} 卡在 {bad if bad else ('誰在：' + '、'.join(w) if w else '時段/地點')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
