#!/usr/bin/env python3
"""把 parse.py 解析出來的卡片組成 Larch 的節點、邊、變數。**不碰 Larch，只產 JSON 與報告。**

    python3 larch/inv/build.py                 # 報告
    python3 larch/inv/build.py --out larch/inv/out/board.json

## 架構（為什麼邊這麼簡單）

Larch 一條邊只能掛一個條件（`edge.data.condition = {kind:"variable", variable, op, value}`），
而設計文件裡的觸發是複合的（地點 × 時段 × 三四個變數 × 或）。硬塞進邊會變成
串一堆閘門節點，而且 POST /nodes 還會把條件靜默丟掉。

所以複合判斷**住在兩張插件卡的 JS 裡**，Larch 只路由兩個單一變數：

    調查板(miniGame) ──dest==地點──▶ 地點入口(scene) ──▶ 選單(miniGame)
        ▲                                                   │ pick==段落
        └──────── boardJump ◀── 段落最後一張 ◀───────────────┘

觸發表（rules）是選單卡的資料，這支把它算好放進 JSON。
判讀不到的觸發列在 unresolved，**不猜**，留給人。
"""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import parse as P

ROOT = P.ROOT
BID = "inv"
SLOT = {"上午": 0, "下午": 1, "晚上": 2, "深夜": 3}
LOCS = ["lobby", "roof", "street", "studio", "booth", "tower14",
        "store", "parts", "busstop", "metro", "laundry", "figure"]
# 場景代號→背景。白天／深夜兩套（色溫規格見 design/調查篇-場景.md）。
# 值是 art 檔名的主幹，推送層再換成 Larch 的 asset URL。
BG = {
    "lobby":   ("bg-lobby-day",   "bg-apartment-hall"),
    "roof":    ("bg-roof-day",    "bg-noah-shop"),
    "street":  ("bg-street-day2", "bg-street-night"),
    "studio":  ("bg-studio-day",  "bg-bambi-studio"),
    "booth":   ("bg-booth",       "bg-booth"),
    "tower14": ("bg-tower14-day", "bg-office-14f"),
    "store":   ("bg-store-day",   "bg-store-night"),
    "parts":   ("bg-parts-day",   "bg-parts"),
    "busstop": ("bg-busstop-day", "bg-busstop"),
    "metro":   ("bg-metro-day",   "bg-metro"),
    "laundry": ("bg-laundry-day", "bg-laundry"),
    "figure":  ("bg-figure-day",  "bg-figure"),
    "catgrass_door": ("bg-catgrass-door", "bg-catgrass-door"),
    "catgrass_home": ("bg-catgrass-home", "bg-catgrass-home"),
}
NARRATOR = "旁白"
# 一個地點哪些時段開著（design/調查篇-場景.md 二「時段與誰在」那張表）。
# 規則自己沒寫時段時用這個當預設：顧店那九格的 L1 只寫了 roof 沒寫時段，
# 可是諾亞的店本來就只在上午／下午／晚上開。
LOC_SLOTS = {"lobby": [0, 1, 2, 3], "roof": [0, 1, 2], "street": [0, 1, 2],
             "studio": [1, 2, 3], "booth": [0, 1], "tower14": [0, 1, 2, 3],
             "store": [0, 1, 2, 3], "parts": [0, 1], "busstop": [0, 1, 2],
             "metro": [0, 1, 2], "laundry": [0, 1, 2, 3], "figure": [1, 2]}

# ── 地點與時段：從標題堆疊解析 ──────────────────────────────
# 解析順序（先中的贏）：觸發裡的 dest== 或代號 → 標題堆疊裡的反引號代號
# → 問答矩陣 L2 的人名 → 標題裡的中文地名。全都沒有才算孤兒。
PERSON_LOC = {"管理員": "lobby", "諾亞": "roof", "斑比": "studio", "鐵塔": "street",
              "0x": "tower14", "貓草": "store", "便利商店店員": "store",
              "材料行老闆": "parts"}
CN_LOC = [("車站前", "street"), ("公車站", "busstop"), ("捷運", "metro"),
          ("便利商店", "store"), ("洗衣店", "laundry"), ("手辦店", "figure"),
          ("材料行", "parts"), ("工作室", "studio"), ("十四樓", "tower14"),
          ("錄音間", "booth"), ("收音機店", "roof"), ("頂樓", "roof"),
          ("一樓", "lobby"), ("大廳", "lobby"), ("貓草家", "catgrass_home")]
CODE_IN = re.compile(r"`(" + "|".join(sorted({*LOCS, "catgrass_door", "catgrass_home"})) + r")`")


def loc_from_headings(headings):
    text = " ".join(headings)
    if m := CODE_IN.search(text):
        return m.group(1), "標題代號"
    for h in headings:
        for who, loc in PERSON_LOC.items():
            if h.startswith(("二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、")) and who in h:
                return loc, "人名"
    for cn, loc in CN_LOC:
        if cn in text:
            return loc, "中文地名"
    return None, None


def slots_from_headings(headings):
    text = " ".join(headings)
    if "任一" in text:
        return [0, 1, 2, 3]
    return sorted({SLOT[s] for s in SLOT if s in text})


# ── 總表：問答矩陣「一之一、二十八個問答段」那張表是段落→地點・時段的權威來源 ──
TABLE_ROW = re.compile(r"^\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*\S+\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|")
TABLE_LOC = re.compile(r"`(" + "|".join(LOCS) + r")`")


def load_table():
    """回 [(問誰, 節標籤, dest, slots)]。「同上」繼承上一列的地點與時段。"""
    rows, last = [], (None, [])
    text = (ROOT / "design/調查篇-問答矩陣.md").read_text(encoding="utf-8")
    # 只讀「一、總表」那一段：整份檔還有各人的「觸發條件一覽」表，格式一樣但不是總表，
    # 混進來會讓「該人預設」抓到一列 dest=None 的垃圾（2026-09-05 抓到）。
    start = text.index("## 一、總表")
    end = text.index("\n## ", start + 1)
    for ln in text[start:end].split("\n"):
        m = TABLE_ROW.match(ln)
        if not m or m.group(1) in ("問誰", "缺什麼", "硬缺", "看骰子", "刻意空手", "不在表上"):
            continue
        who, label, cell = m.group(1), m.group(3), m.group(4)
        # 「一、總表」那一段有兩張表：前面是「問誰＼關於誰」的 ○／— 格子矩陣，
        # 表頭、分隔線、每一列都會被上面的正則吃到。只留地點欄真的寫了地點的列。
        if not (cell.startswith("同上") or TABLE_LOC.search(cell)):
            continue
        if cell.startswith("同上"):
            dest, slots = last
        else:
            locs = TABLE_LOC.findall(cell)
            dest = locs[-1] if locs else None          # 「`street` 換 `booth`」取後者
            slots = [0, 1, 2, 3] if "任一" in cell else sorted({SLOT[s] for s in SLOT if s in cell})
            if "櫃檯的班" in cell:
                slots = [0, 1]                          # 櫃檯只在上午／下午（時段表）
            last = (dest, slots)
        rows.append((who, label, dest, slots))
    return rows


def table_match(rows, headings):
    """用 L2 的人名 + 節標籤裡的關鍵詞對回段落。對不到就回 None。"""
    stack = " ".join(headings)
    for who, label, dest, slots in rows:
        if who not in stack:
            continue
        # 標籤形如「二・一Ａ 那台螢幕」「三・Ａ二 她叫什麼名字」「五・格一」「七・三」
        parts = [x for x in re.split(r"[・\s]+", label) if x]
        toks = [x for x in parts if not re.fullmatch(r"[一二三四五六七八九十]+", x)]
        # 一、關鍵詞：「那台螢幕」「失物箱」「她叫什麼名字」
        if any(tok in stack for tok in toks if len(tok) >= 2):
            return dest, slots
        # 二、子節開頭：「Ａ一」「格一」「甲」對到標題開頭
        if any(h.startswith(tok) for tok in toks for h in headings):
            return dest, slots
        # 三、純序數：「七・二」＝該人底下第二個 L3，對到以「二、」開頭的標題
        if len(parts) >= 2 and re.fullmatch(r"[一二三四五六七八九十]+", parts[1]):
            if any(h.startswith(parts[1] + "、") or h.startswith(parts[1] + "・") for h in headings[1:]):
                return dest, slots
    return None


# ── 觸發判讀 ─────────────────────────────────────────────
EXPR = re.compile(r"`\s*([a-zA-Z_][\w]*(?:_[一-鿿0-9x<>誰]+)?)\s*(==|!=|>=|<=|>|<)\s*([^`]+?)\s*`")
BARE_LOC = re.compile(r"`(" + "|".join(LOCS) + r")`|(?<![a-z_])(" + "|".join(LOCS) + r")(?![a-z_])")
OPS = {"==": "eq", "!=": "neq", ">=": "gte", "<=": "lte", ">": "gt", "<": "lt"}


def parse_trigger(text):
    """回 (rule, notes)。rule = {dest, slots, conds, any_slot}；判不完整的放 notes。"""
    rule = {"dest": None, "slots": [], "conds": [], "or": False}
    notes = []
    if not text:
        return None, ["沒有觸發"]
    if "或" in text and "或深夜" not in text and "或下午" not in text and "或晚上" not in text:
        # 「A 或 B」在地點層級＝兩條規則，這裡先標記，不展開
        rule["or"] = True
    for m in EXPR.finditer(text):
        var, op, val = m.group(1), OPS[m.group(2)], m.group(3).strip()
        if var == "dest":
            rule["dest"] = val
            continue
        if var == "slot":
            continue
        if val in ("true", "false"):
            val = val == "true"
        elif re.fullmatch(r"-?\d+", val):
            val = int(val)
        rule["conds"].append({"variable": var, "op": op, "value": val})
    if rule["dest"] is None:
        locs = [a or b for a, b in BARE_LOC.findall(text)]
        if locs:
            rule["dest"] = locs[0]
            if len(set(locs)) > 1:
                rule["or"] = True
                notes.append(f"多個地點 {sorted(set(locs))}，要拆成多條規則")
    if "任一" in text or "任一時段" in text:
        rule["slots"] = [0, 1, 2, 3]
    else:
        rule["slots"] = sorted({SLOT[s] for s in SLOT if s in text})
    if not rule["dest"]:
        notes.append("判不出地點")
    if "<誰>" in text:
        notes.append("含範本 <誰>，要展開成每一個人")
    return rule, notes


# ── 節點 ─────────────────────────────────────────────────
class Board:
    def __init__(self):
        self.nodes, self.edges, self.n, self.x = [], [], 0, 0

    def add(self, data):
        self.n += 1
        nid = f"{BID}-{self.n:03d}"
        self.x += 300
        self.nodes.append({"id": nid, "type": "story",
                           "position": {"x": self.x, "y": 0}, "data": data})
        return nid

    def edge(self, s, t, cond=None):
        e = {"id": f"e{len(self.edges)+1}", "source": s, "target": t,
             "sourceHandle": "right", "animated": True}
        if cond:
            e["data"] = {"condition": {"kind": "variable", **cond}}
        self.edges.append(e)
        return e


def card_node(c):
    """一張解析出來的卡 → Larch dialogue 節點資料。形狀照 novelkit。"""
    lines = [l for l in c["lines"] if not l.get("direction")]
    if not lines:
        return None
    if c["kind"] in ("narrate", "note", "plate"):
        text = "\n".join(l["text"] for l in lines)
        d = {"type": "dialogue", "title": text[:14], "text": text, "speaker": NARRATOR}
        if c["kind"] == "note":
            d["title"] = "筆記：" + text[:10]
            d["speaker"] = "玩家"
        return d
    if c["kind"] == "say":
        text = "\n".join(l["text"] for l in lines)
        d = {"type": "dialogue", "title": f"{c['speaker']}：{text[:10]}",
             "text": text, "speaker": c["speaker"]}
        if c.get("remote"):
            d["remote"] = True          # 推送層據此掛大頭貼、不掛立繪
        return d
    # talk：多講者
    spoken = [l for l in lines if l.get("speaker")]
    if not spoken:
        return None
    dl = [{"id": f"l{i}", "speaker": l["speaker"], "text": l["text"], "emotion": ""}
          for i, l in enumerate(spoken)]
    return {"type": "dialogue", "title": f"{spoken[0]['speaker']}：{spoken[0]['text'][:10]}",
            "text": spoken[0]["text"], "speaker": spoken[0]["speaker"], "dialogueLines": dl}


def build(cards):
    b = Board()
    table = load_table()
    # 1. 調查板
    board_id = b.add({"type": "miniGame", "title": "調查板", "text": "選一個地方去。",
                      "miniGameHtml": "@@larch/cards/board.html",
                      "miniGamePresentation": "fullscreen", "miniGameSkippable": False,
                      "miniGameReadVars": ["day", "slot", "met"] + [f"open_{k}" for k in
                                          ("roof", "laundry", "figure", "parts", "studio", "tower14")],
                      "miniGameWriteVars": ["day", "slot", "dest", "here"], "start": True})
    # 2. 每個地點：入口場景 → 選單
    menu_of = {}
    for loc in LOCS:
        day, night = BG[loc]
        entry = b.add({"type": "scene", "title": loc, "text": "",
                       "background": f"@@{day}", "backgroundNight": f"@@{night}",
                       "transition": "fade", "transitionMs": 340})
        b.edge(board_id, entry, {"variable": "dest", "op": "eq", "value": loc})
        menu = b.add({"type": "miniGame", "title": f"選單：{loc}", "text": "問誰、關於誰。",
                      "miniGameHtml": "@@larch/cards/menu.html",
                      "miniGamePresentation": "fullscreen", "miniGameSkippable": True,
                      "miniGameReadVars": ["day", "slot", "here"], "miniGameWriteVars": ["pick"]})
        b.edge(entry, menu)
        menu_of[loc] = menu
    # 3. 段落：同一 (檔, 章節) 的連續卡片＝一條線
    segs, cur_key, cur = [], None, None
    for c in cards:
        key = (c["file"], c["section"])
        if key != cur_key:
            cur = {"key": key, "cards": [], "trigger": c.get("trigger", {}).get("觸發", "")}
            segs.append(cur)
            cur_key = key
        cur["cards"].append(c)
    rules, unresolved, orphans = [], [], []
    for i, s in enumerate(segs):
        sid = f"seg{i:03d}"
        rule, notes = parse_trigger(s["trigger"])
        heads = s["cards"][0].get("headings", [])
        if rule is None:
            rule, notes = {"dest": None, "slots": [], "conds": [], "or": False}, []
        if not rule["dest"]:
            # 卡頭自己寫的 `scene: xxx` 是最直接的來源，橋段那類場次沒有觸發也沒有
            # 標題代號，地點只在這裡。
            first_scene = next((c["scene"] for c in s["cards"] if c.get("scene")), None)
            if first_scene:
                rule["dest"] = first_scene
                rule["dest_from"] = "卡頭 scene"
            else:
                loc, how = loc_from_headings(heads)
                if loc:
                    rule["dest"] = loc
                    rule["dest_from"] = how
        # 總表是權威：對得到就覆寫地點與時段（它明寫 0x 在 tower14、鐵塔 street 換 booth）
        if s["cards"][0]["file"] == "調查篇-問答矩陣":
            hit = table_match(table, heads)
            if not hit:
                # 對不到具體那一列（池一…池五這種沒關鍵詞的子節）就用該人的第一列當預設
                who = next((w for w in PERSON_LOC if any(w in h for h in heads)), None)
                row = next(((d_, sl) for w, _, d_, sl in table if w == who), None) if who else None
                if row:
                    hit = row
                    rule["dest_from"] = "總表（該人預設）"
            if hit:
                dest, slots = hit
                if dest:
                    rule["dest"] = dest
                    rule.setdefault("dest_from", "總表")
                    if rule["dest_from"] not in ("總表（該人預設）",):
                        rule["dest_from"] = "總表"
                if slots:
                    rule["slots"] = slots
        if rule["dest"]:
            notes = [x for x in notes if x != "判不出地點"]
            if not rule["slots"]:
                rule["slots"] = LOC_SLOTS.get(rule["dest"], [])
                rule["slots_from"] = "地點預設"
        if not rule["slots"]:
            rule["slots"] = slots_from_headings(heads)
        first = prev = None
        for c in s["cards"]:
            d = card_node(c)
            if not d:
                continue
            d["segment"] = sid
            for v in c["vars"]:
                d.setdefault("variableOps", []).append(
                    {"variable": v["name"], "kind": "add" if v["add"] else "set",
                     "value": int(v["add"]) if v["add"] else v["set"]})
            nid = b.add(d)
            if prev:
                b.edge(prev, nid)
            first = first or nid
            prev = nid
        if not first:
            continue
        back = b.add({"type": "boardJump", "title": "回調查板", "jumpBoardId": BID,
                      "jumpNodeId": board_id})
        b.edge(prev, back)
        if rule and rule["dest"] in ("catgrass_door", "catgrass_home"):
            rule["scene_only"] = rule["dest"]
            rule["dest"] = "store"       # 私人場景掛在原地點的選單底下（變數帳一）
        if rule and rule["dest"] in menu_of:
            b.edge(menu_of[rule["dest"]], first, {"variable": "pick", "op": "eq", "value": sid})
            rules.append({"segment": sid, "section": s["key"][1], "file": s["key"][0], **rule})
            if notes:
                unresolved.append({"segment": sid, "section": s["key"][1], "notes": notes,
                                   "text": s["trigger"]})
        else:
            orphans.append({"segment": sid, "file": s["key"][0], "section": s["key"][1],
                            "trigger": s["trigger"], "notes": notes})
    return b, rules, unresolved, orphans, len(segs)


def variables():
    v = [("day", "number", 1), ("slot", "number", 0), ("dest", "string", ""),
         ("here", "string", ""), ("pick", "string", ""), ("met", "string", ""),
         ("notes", "string", "[]"), ("notes_free", "string", "[]"),
         ("hole_sightings", "number", 0), ("noah_stage", "number", 0),
         ("bambi_asked_at", "number", 0)]
    for k in ("roof", "laundry", "figure", "parts", "studio", "tower14"):
        v.append((f"open_{k}", "boolean", False))
    for who in ("斑比", "店員", "鐵塔", "貓草", "管理員", "保全", "諾亞"):
        v.append((f"trust_{who}", "number", 0))
    return [{"id": n, "name": n, "label": n, "type": t, "defaultValue": d} for n, t, d in v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    cards = []
    for d in P.DOCS:
        cs, _ = P.parse_file(d)
        cards += cs
    b, rules, unresolved, orphans, nseg = build(cards)
    vs = variables()

    # 可達性：每個段落入口都要有一條 pick 邊
    seg_entries = {n["data"]["segment"]: n["id"] for n in b.nodes if n["data"].get("segment")}
    firsts = {}
    for n in b.nodes:
        s = n["data"].get("segment")
        if s and s not in firsts:
            firsts[s] = n["id"]
    reachable = {e["target"] for e in b.edges if e.get("data", {}).get("condition", {}).get("variable") == "pick"}
    unreached = [s for s, nid in firsts.items() if nid not in reachable]

    print(f"卡片 {len(cards)} 張 → 節點 {len(b.nodes)}、邊 {len(b.edges)}、變數 {len(vs)}")
    print(f"段落 {nseg} 條：接上選單 {len(rules)} 條、判不出地點 {len(orphans)} 條、判讀有保留 {len(unresolved)} 條")
    print(f"段落入口沒有任何 pick 邊進來的：{len(unreached)} 條")
    print(f"時段判讀：任一 {sum(1 for r in rules if len(r['slots'])==4)}、指定 {sum(1 for r in rules if 0<len(r['slots'])<4)}、沒寫 {sum(1 for r in rules if not r['slots'])}")
    print(f"含「或」要拆的規則：{sum(1 for r in rules if r['or'])} 條")
    if orphans:
        print("\n判不出地點的段落（前 12）：")
        for o in orphans[:12]:
            print(f"  ・{o['file']}｜{o['section'][:22]}｜{(o['trigger'] or '（無觸發）')[:60]}")
    if unresolved:
        print("\n判讀有保留（前 8）：")
        for u in unresolved[:8]:
            print(f"  ・{u['section'][:22]}｜{'；'.join(u['notes'])}")
    if a.out:
        out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"boardId": BID, "nodes": b.nodes, "edges": b.edges,
                                   "variables": vs, "rules": rules,
                                   "unresolved": unresolved, "orphans": orphans},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n寫出 {out}")
    # 自我檢查：兩種路由變數以外不可以有任何條件邊
    bad = [e for e in b.edges if e.get("data") and
           e["data"]["condition"]["variable"] not in ("dest", "pick")]
    assert not bad, f"有 {len(bad)} 條邊掛了 dest/pick 以外的條件，複合判斷不該變成邊"
    return 0


if __name__ == "__main__":
    sys.exit(main())
