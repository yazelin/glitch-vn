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
    "tower14": ("bg-tower14-day", "bg-tower14-night"),
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


# 收尾門檻（design/調查篇-信心.md 五）：四樣裡的前三樣。第四樣在收尾那一場自己花掉。
# 不用 ending_ready 旗標，直接把三個條件擺進規則，選單卡自己判。
ENDING_CONDS = ({"variable": "day", "op": "gte", "value": 4},
                {"variable": "night_visits", "op": "gte", "value": 3},
                {"variable": "strikes", "op": "gte", "value": 3})
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11}
# 整份檔都是同一天的
FILE_DAY = {"調查篇-第一天-定稿": 1, "調查篇-第二天": 2}


def day_conds(file, headings):
    """從檔名與標題讀出這一段哪幾天才會播。回 conds 清單（可能是空的）。
    「第五到第七天之間」→ 5..7；「第八到第十一天之間」→ 8..11；「最後一天」→ >= 11；
    「第二天」→ == 2。判不出來就不加，寧可少擋不要亂擋。"""
    if file in FILE_DAY:
        return [{"variable": "day", "op": "eq", "value": FILE_DAY[file]}]
    text = " ".join(headings)
    m = re.search(r"第([一二三四五六七八九十]+)到第([一二三四五六七八九十]+)天", text)
    if m:
        return [{"variable": "day", "op": "gte", "value": CN_NUM[m.group(1)]},
                {"variable": "day", "op": "lte", "value": CN_NUM[m.group(2)]}]
    if "最後一天" in text or "最後那一頁" in text or "最後一頁" in text:
        return list(ENDING_CONDS)
    m = re.search(r"第([一二三四五六七八九十]+)天(以後|之後|起)", text)
    if m:
        return [{"variable": "day", "op": "gte", "value": CN_NUM[m.group(1)]}]
    m = re.search(r"第([一二三四五六七八九十]+)天", text)
    if m:
        return [{"variable": "day", "op": "eq", "value": CN_NUM[m.group(1)]}]
    return []


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
            dest = locs[0] if locs else None           # 「`street` 換 `booth`」取前者：玩家是在街上被擋的，觸發寫 dest == street
            slots = [0, 1, 2, 3] if "任一" in cell else sorted({SLOT[s] for s in SLOT if s in cell})
            if "櫃檯的班" in cell:
                slots = [0, 1]                          # 櫃檯只在上午／下午（時段表）
            last = (dest, slots)
        rows.append((who, label, dest, slots))
    return rows


def table_match(rows, headings):
    """用 L2 的人名 + 節標籤裡的關鍵詞對回段落。對不到就回 None。"""
    stack = " ".join(headings)
    # 問答矩陣的 L2 是「人」：先對那個人的列，再對別人的。不然「乙、問她・關於諾亞」會對到諾亞的列（頂樓）
    person = next((w for h in headings[:2] for w in PERSON_LOC if h.startswith(w) or f"、{w}" in h), None)
    rows = sorted(rows, key=lambda r: 0 if r[0] == person else 1)
    for who, label, dest, slots in rows:
        if who not in stack:
            continue
        # 標籤形如「二・一Ａ 那台螢幕」「三・Ａ二 她叫什麼名字」「五・格一」「七・三」
        parts = [x for x in re.split(r"[・\s]+", label) if x]
        toks = [x for x in parts if not re.fullmatch(r"[一二三四五六七八九十]+", x)]
        # 一、關鍵詞：「那台螢幕」「失物箱」「她叫什麼名字」
        if any(tok in stack for tok in toks if len(tok) >= 2):
            return dest, slots
        # 二、子節開頭：「Ａ一」「格一」「甲」對到標題開頭；「乙（含乙之二）」先把括號拿掉
        toks2 = [re.sub(r"（.*?）", "", tok) for tok in toks]
        if any(t and h.startswith(t) for t in toks2 for h in headings):
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
    if "ending_ready" in text:
        rule["conds"].extend(ENDING_CONDS)
    for m in EXPR.finditer(text):
        var, op, val = m.group(1), OPS[m.group(2)], m.group(3).strip()
        if var in ("dest", "ending_ready"):
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
    for m in re.finditer(r"`(hasItem|lacksItem)\s+([a-z0-9_]+)`", text):
        rule["conds"].append({"variable": "inventory", "op": m.group(1), "value": m.group(2)})
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

    def add(self, data, nid=None):
        self.n += 1
        nid = nid or f"{BID}-{self.n:03d}"
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


def expand_rec(b, prev, c, sid, tapes):
    """錄音巨集：prev ─rec_ok─▶ 選擇（開錄音機／不開）─0─▶ 反應 talk ─▶ 取得道具 ─▶（接下一張）
                     └─預設──────────────────────────────────────────────▶（接下一張）
    回傳「下一張卡要接在哪些節點後面」的匯流節點 id。
    Larch 一個出口只認第一條成立的邊，所以 prev 的兩條邊順序是條件在前、預設在後。"""
    who, _, when = c["meta"].strip().partition("・")     # 「斑比・深夜」＝只有深夜給錄；「貓草・拒」＝開了就掉信任、當場結束
    refuse = when.strip() == "拒"
    slot_need = SLOT.get(when.strip()) if (when and not refuse) else None
    reaction = [l for l in c["lines"] if l.get("speaker")]
    quote = " ".join(l["text"] for l in c["lines"] if not l.get("speaker") and not l.get("direction"))
    item_id = "rec_" + TAPE_ID.get(who, re.sub(r"[^a-z0-9]", "", who.lower()) or f"{sid}")
    name = f"錄音・{who}"
    tapes.append({"id": item_id, "name": name, "who": who, "quote": quote})
    choice = b.add({"type": "choice", "title": f"錄音：{who}", "text": "錄音機在包包裡。",
                    "choices": ["開錄音機", "不開"], "choiceMode": "branch", "segment": sid})
    # 匯流點：一張空的 setVariable 卡（沒有字會自動跳過），兩條路都接到它，下一張卡再接它
    merge = b.add({"type": "setVariable", "title": "（匯流）", "text": "", "variableOps": [], "segment": sid})
    if slot_need is None:
        b.edge(prev, choice, {"variable": "rec_ok", "op": "eq", "value": True})
        b.edge(prev, merge)
    else:
        # 一條邊只掛一個條件：rec_ok 先過一張空卡，再判時段
        gate = b.add({"type": "setVariable", "title": f"（{who}只有{when}給錄）", "text": "", "variableOps": [], "segment": sid})
        b.edge(prev, gate, {"variable": "rec_ok", "op": "eq", "value": True})
        b.edge(prev, merge)
        b.edge(gate, choice, {"variable": "slot", "op": "eq", "value": slot_need})
        b.edge(gate, merge)
    grant = b.add({"type": "plugin", "title": f"取得：{name}", "text": "",
                   "pluginId": "larch-inventory", "pluginCardId": "grant-item",
                   "pluginVersion": "1.9.0", "pluginName": "背包系統", "pluginCardName": "取得道具",
                   "pluginIcon": "box", "pluginColor": "#78a67d",
                   "pluginPresentation": "fullscreen", "pluginSkippable": False,
                   "pluginValues": {"autoCollect": False, "itemId": item_id, "itemName": name,
                                    "itemImage": "", "itemNote": quote, "itemCount": 1,
                                    "hideAfterCollect": True, "bagVar": "inventory", "countVar": "inventoryCount",
                                    "consumable": False, "effectKind": "set", "effectVar": "open_tape",
                                    "effectValue": "true", "storyNodeId": ""},
                   "pluginReadVars": ["inventory", "inventoryCount"],
                   "pluginWriteVars": ["inventory", "inventoryCount", "pluginResult"],
                   "segment": sid})
    if refuse:
        # 不給錄的人：反應那張卡之後掉一級，直接回調查板（這一場就此結束）
        dl = [{"id": f"l{i}", "speaker": l["speaker"], "text": l["text"], "emotion": ""}
              for i, l in enumerate(reaction)] or [{"id": "l0", "speaker": who, "text": "你錄音？", "emotion": ""}]
        react = b.add({"type": "dialogue", "title": f"{who}：對錄音機", "text": dl[0]["text"],
                       "speaker": dl[0]["speaker"], "dialogueLines": dl, "segment": sid,
                       "variableOps": [{"id": "op-trust", "variable": f"trust_{who}", "kind": "add", "value": -1}]})
        b.edge(choice, react); b.edges[-1]["sourceHandle"] = "choice-0"
        out = b.add({"type": "boardJump", "title": "回調查板（被趕走）", "jumpBoardId": BID, "jumpNodeId": "@@board"})
        b.edge(react, out)
        b.edge(choice, merge); b.edges[-1]["sourceHandle"] = "choice-1"
        tapes.pop()                       # 沒有這一卷
        b.nodes.remove(next(n for n in b.nodes if n["id"] == grant))
        return merge
    if reaction:
        dl = [{"id": f"l{i}", "speaker": l["speaker"], "text": l["text"], "emotion": ""}
              for i, l in enumerate(reaction)]
        react = b.add({"type": "dialogue", "title": f"{who}：對錄音機", "text": reaction[0]["text"],
                       "speaker": reaction[0]["speaker"], "dialogueLines": dl, "segment": sid})
        b.edge(choice, react); b.edges[-1]["sourceHandle"] = "choice-0"
        b.edge(react, grant)
    else:
        b.edge(choice, grant); b.edges[-1]["sourceHandle"] = "choice-0"
    b.edge(choice, merge); b.edges[-1]["sourceHandle"] = "choice-1"
    b.edge(grant, merge)
    return merge


TAPE_ID = {"諾亞": "noah", "店員": "clerk", "便利商店店員": "clerk", "材料行老闆": "parts",
           "保全": "guard", "斑比": "bambi", "管理員": "admin"}


COUNTERS = ("met_", "trust_", "hole_sightings", "noah_stage", "night_visits", "strikes")


def var_op(v):
    """一個標記 → 一個 variableOp。「**→ `hole_sightings`**」這種計數型沒寫值＝加一，旗標沒寫值＝true。"""
    if v["add"]:
        return {"id": f"op-{v['name']}", "variable": v["name"], "kind": "add", "value": int(v["add"])}
    if v["set"] is None and v["name"].startswith(COUNTERS):
        return {"id": f"op-{v['name']}", "variable": v["name"], "kind": "add", "value": 1}
    return {"id": f"op-{v['name']}", "variable": v["name"], "kind": "set", "value": var_value(v["set"])}


def var_value(raw):
    """「**→ `see_x`**」沒寫值＝設 true；「← true**」那個 ** 是 markdown 的粗體收尾，要剝掉；
    true/false/整數轉型，其餘留字串。之前直接把 None 與 'true**' 寫進去，旗標從來沒真的變 true（2026-09-07 抓到）。"""
    if raw is None:
        return True
    v = re.match(r"[^\s*（(]+", str(raw).strip())
    v = (v.group(0) if v else "").strip()
    if v in ("true", "是"):
        return True
    if v in ("false", "否"):
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def card_node(c):
    """一張解析出來的卡 → Larch dialogue 節點資料。形狀照 novelkit。"""
    lines = [l for l in c["lines"] if not l.get("direction")]
    if not lines:
        return None
    if c["kind"] in ("narrate", "note", "plate"):
        text = "\n".join(l["text"] for l in lines)
        d = {"type": "dialogue", "title": text[:14], "text": text, "speaker": NARRATOR}
        if c.get("scene"):
            d["sceneCode"] = c["scene"]      # 卡頭的 `scene: xxx`：段落中途換場景（貓草家、錄音間）
        if c.get("exits"):
            d["exits"] = c["exits"]
        if c["kind"] == "note":
            d["title"] = "筆記：" + text[:10]
            d["speaker"] = "玩家"
            if "~~" in text:
                # 他劃掉自己寫過的結論。收尾門檻之一（信心.md 五：至少三條刪除線）
                d["variableOps"] = [{"id": "op-strikes", "variable": "strikes", "kind": "add", "value": 1}]
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
    d = {"type": "dialogue", "title": f"{spoken[0]['speaker']}：{spoken[0]['text'][:10]}",
         "text": spoken[0]["text"], "speaker": spoken[0]["speaker"], "dialogueLines": dl}
    if c.get("scene"):
        d["sceneCode"] = c["scene"]
    if c.get("exits"):
        d["exits"] = c["exits"]
    return d


def build(cards):
    b = Board()
    table = load_table()
    # 1. 調查板
    board_id = b.add({"type": "miniGame", "title": "調查板", "text": "選一個地方去。",
                      "miniGameHtml": "@@larch/cards/board.html",
                      "miniGamePresentation": "fullscreen", "miniGameSkippable": False,
                      "miniGameReadVars": ["day", "slot", "met", "dest", "night_visits", "seen_booth", "visited",
                                           "names_seen", "see_stairs", "hole_sightings", "see_admin", "laundry_night1",
                                           "trust_斑比", "strikes", "clue_list", "rec_ok"] + [f"open_{k}" for k in
                                          ("roof", "laundry", "figure", "parts", "studio", "tower14")] + MET_VARS,
                      "miniGameWriteVars": ["day", "slot", "dest", "here", "night_visits", "met", "visited"] + MET_VARS})
    # 2. 每個地點：入口場景 → 選單
    menu_of, entries_of, greetings = {}, {}, []
    for loc in LOCS:
        day, night = BG[loc]
        # 一個地點兩張入口：白天（上午／下午）與夜晚（晚上／深夜），調查板用 dest 尾巴的 @n 分
        entry = b.add({"type": "scene", "title": loc, "text": "",
                       "background": f"@@{day}", "backgroundNight": f"@@{night}",
                       "transition": "fade", "transitionMs": 340})
        b.edge(board_id, entry, {"variable": "dest", "op": "eq", "value": loc})
        entry_n = b.add({"type": "scene", "title": f"{loc}@n", "text": "",
                         "background": f"@@{night}", "backgroundNight": f"@@{night}",
                         "transition": "fade", "transitionMs": 340})
        b.edge(board_id, entry_n, {"variable": "dest", "op": "eq", "value": f"{loc}@n"})
        # 第三張：晚上（slot 2）。晚上版沒畫的地點（貓草、經紀公司）推送層會退回夜版。
        entry_e = b.add({"type": "scene", "title": f"{loc}@e", "text": "",
                         "background": f"@@bg-{loc}-evening", "backgroundNight": f"@@{night}",
                         "transition": "fade", "transitionMs": 340})
        b.edge(board_id, entry_e, {"variable": "dest", "op": "eq", "value": f"{loc}@e"})
        menu = b.add({"type": "miniGame", "title": f"選單：{loc}", "text": "問誰、關於誰。",
                      "miniGameHtml": "@@larch/cards/menu.html",
                      "miniGamePresentation": "fullscreen", "miniGameSkippable": True,
                      "miniGameReadVars": ["day", "slot", "here"], "miniGameWriteVars": ["pick"]})
        entries_of[loc] = (entry, entry_n, entry_e)
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
    rules, unresolved, orphans, tapes = [], [], [], []
    labels, unlabeled = load_labels(), []
    choice_links, seg_first, seg_end = [], {}, {}
    for i, s in enumerate(segs):
        sid = f"seg{i:03d}"
        rule, notes = parse_trigger(s["trigger"])
        heads = s["cards"][0].get("headings", [])
        if rule is None:
            rule, notes = {"dest": None, "slots": [], "conds": [], "or": False}, []
        if s["cards"][0]["file"] == "調查篇-招呼":
            heads = s["cards"][0].get("headings", [])
            loc_, _ = loc_from_headings(heads)
            m_met = re.search(r"`(met_[^`]+) >= (\d+)`", " ".join(heads))
            if not loc_ or not m_met:
                continue
            who_ = heads[-2].split("（")[0] if len(heads) >= 2 else ""
            gid = f"greet-{loc_}-{m_met.group(1)}-{m_met.group(2)}"
            first = prev = None
            for c in s["cards"]:
                d = card_node(c)
                if not d:
                    continue
                d["segment"] = gid
                d["castHint"] = who_          # 旁白只寫動作，可是那個人要在台上
                nid = b.add(d)
                if prev:
                    b.edge(prev, nid)
                first = first or nid
                prev = nid
            if first:
                greetings.append({"loc": loc_, "var": m_met.group(1), "n": int(m_met.group(2)),
                                  "slots": slots_from_headings(heads), "first": first, "last": prev})
            continue
        m_end = re.search(r"第([一二三四五六七八九十]+)天收尾", s["key"][1])
        if m_end:
            n_day = CN_NUM[m_end.group(1)]
            first = prev = None
            intr = b.add({"type": "interrupt", "title": f"第{m_end.group(1)}天收尾", "text": "",
                          "interruptCondition": {"kind": "variable", "variable": "day", "op": "eq", "value": n_day + 1},
                          "interruptOnce": True, "interruptExit": "return"})
            prev = intr
            for c in s["cards"]:
                d = card_node(c)
                if not d:
                    continue
                d["segment"] = sid
                for v in c["vars"]:
                    d.setdefault("variableOps", []).append(var_op(v))
                nid = b.add(d)
                b.edge(prev, nid)
                prev = nid
            continue
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
                # 標題自己寫了時段（「一樓晚上」）就用它，沒寫才退到地點預設
                hs = slots_from_headings(heads)
                if hs and len(hs) < 4:
                    rule["slots"] = hs
                    rule["slots_from"] = "標題"
                else:
                    rule["slots"] = LOC_SLOTS.get(rule["dest"], [])
                    rule["slots_from"] = "地點預設"
        if not rule["slots"]:
            rule["slots"] = slots_from_headings(heads)
        # 標題括號裡寫的條件（「Ａ一・她叫什麼名字（`met_諾亞 >= 2`）」）也是觸發。
        # 觸發列寫在段落層、卡片在更深一層標題底下時 meta 會被標題重置，所以標題是更可靠的來源。
        if not rule["conds"]:
            for m in re.finditer(r"`(hasItem|lacksItem)\s+([a-z0-9_]+)`", " ".join(heads)):
                rule["conds"].append({"variable": "inventory", "op": m.group(1), "value": m.group(2)})
            for m in EXPR.finditer(" ".join(heads)):
                var, op, val = m.group(1), OPS[m.group(2)], m.group(3).strip()
                if var in ("dest", "slot"):
                    continue
                val = (val == "true") if val in ("true", "false") else int(val) if re.fullmatch(r"-?\d+", val) else val
                rule["conds"].append({"variable": var, "op": op, "value": val})
            # 「`trust_管理員` 3」沒寫運算子的當等於；「`trust_店員` 1 以上」當大於等於
            for m in re.finditer(r"`(trust_[^`]+|met_[^`]+|noah_stage)`\s+([0-9])\b(\s*以上)?", " ".join(heads)):
                if not any(c["variable"] == m.group(1) for c in rule["conds"]):
                    rule["conds"].append({"variable": m.group(1), "op": "gte" if m.group(3) else "eq", "value": int(m.group(2))})
        # 貓草深夜便利商店那三次（橋段2 七）：第一次 trust 0、第二次 1、第三次 2，子節跟著父節的「次」
        if s["cards"][0]["file"] == "調查篇-橋段2" and any(h.startswith("七、深夜的便利商店") for h in heads):
            m_n = re.search(r"第([一二三])次", " ".join(heads[1:]))
            if m_n:
                # 三次都在 trust 0（父節的觸發），差別是來過幾次：調查板每趟加的 met_貓草
                n_ = CN_NUM[m_n.group(1)]
                # 到店幾次：cat_visits，由「第一次」「第二次」那兩段自己加（在那一段的最後一張卡）
                rule["conds"] = [c for c in rule["conds"] if c["variable"] not in ("met_貓草", "cat_visits")]
                # 「第一次」本身在 0 播完加成 1；它底下的「甲」分支在 1 播（同一趟或下一趟）
                sub = s["key"][1].startswith(("甲", "乙", "他先開口"))
                rule["conds"].append({"variable": "cat_visits", "op": "gte" if n_ == 3 else "eq", "value": n_ if sub else n_ - 1})
                if n_ < 3 and s["key"][1].startswith(("第一次", "第二次")):
                    last_card = next(c_ for c_ in reversed(s["cards"]) if c_["kind"] not in ("rec", "bag"))
                    last_card["vars"].append({"name": "cat_visits", "set": None, "add": "1", "from": None})
        if s["key"][1].startswith("Ｂ・頂樓收音機店（隔天"):
            rule["slots"] = [0, 1, 2]
            rule["conds"].append({"variable": "names_seen", "op": "eq", "value": True})
        # 標記寫「`trust_貓草` 2 → 3」＝這一段要在 2 的時候才播（沒有別的條件管同一個變數時）
        for c_ in s["cards"]:
            for v_ in c_["vars"]:
                if v_.get("from") is not None and not any(c["variable"] == v_["name"] for c in rule["conds"]):
                    rule["conds"].append({"variable": v_["name"], "op": "eq", "value": int(v_["from"])})
        # 管理員那五格閒話每問一次加一級信任，滿了就不再列（不然無限加上去，失物箱那格 lte/gte 都對不上）
        if s["key"][1].startswith("池") and s["cards"][0]["file"] == "調查篇-問答矩陣":
            rule["conds"].append({"variable": "trust_管理員", "op": "lte", "value": 2})
        # 含範本 <誰> 的條件（五之三）：用〈關於格莉奇〉那一格的兩個旗標（問答矩陣寫明「看的是 bambi_revised」）
        if any(c["variable"].endswith("_") or "<" in str(c["value"]) for c in rule["conds"]):
            rule["conds"] = [c for c in rule["conds"] if not c["variable"].endswith("_") and "<" not in str(c["value"])]
            rule["conds"] += [{"variable": "asked_斑比_格莉奇", "op": "eq", "value": True},
                              {"variable": "bambi_revised", "op": "eq", "value": True},
                              {"variable": "bambi_third", "op": "eq", "value": False}]
            notes = [x for x in notes if "範本" not in x]
        for c in rule["conds"]:
            # trust 用 add 一路加上去會超過 3，「== 3」要當「>= 3」
            if c["variable"].startswith("trust_") and c["op"] == "eq" and c["value"] == 3:
                c["op"] = "gte"
        # 日期閘：觸發裡沒寫 day 的，從檔名與標題補
        if not any(c["variable"] == "day" for c in rule["conds"]):
            rule["conds"] = rule["conds"] + day_conds(s["cards"][0]["file"], heads)
        first = prev = None
        after_choice = None
        back_id = None          # 這一段的回板卡，背包巨集的「沒挑到」要接到它，所以先預留 id
        pending_bag = None      # 背包巨集：下一張卡要接在 pick 條件邊後面
        for c in s["cards"]:
            if c["kind"] == "rec":
                if not prev:
                    continue    # 錄音前面一定要有一張卡（錄的是它）
                prev = expand_rec(b, prev, c, sid, tapes)
                first = first or prev
                continue
            if c["kind"] == "bag":
                if not back_id:
                    back_id = f"{BID}-back-{sid}"
                # 錄音卷的使用效果是 open_tape=true（HUD 隨時重聽用）。在劇情裡打開背包挑它時
                # 這個效果也會發，interrupt 卡就會插播，回來又停在背包卡上（2026-09-07 實測）。
                # 所以 interrupt 的條件多一項 in_bag == false：進背包場景前設 true，挑完或放棄都設回 false。
                gate = b.add({"type": "setVariable", "title": "（進背包）", "text": "",
                              "variableOps": [{"id": "op-inbag", "variable": "in_bag", "kind": "set", "value": True}],
                              "segment": sid})
                if prev:
                    b.edge(prev, gate)
                first = first or gate
                prev = gate
                bag = b.add({"type": "plugin", "title": f"背包：{c['meta']}", "text": "",
                             "pluginId": "larch-inventory", "pluginCardId": "open-bag",
                             "pluginVersion": "1.9.0", "pluginName": "背包系統", "pluginCardName": "打開背包",
                             "pluginIcon": "backpack", "pluginColor": "#6f9474",
                             "pluginPresentation": "inline", "pluginSkippable": True,
                             "pluginValues": {"title": "拿什麼出來", "bagVar": "inventory",
                                              "pickVar": "inventoryLastUsed", "consume": False, "allowSkip": True,
                                              "emptyText": "包包裡沒有東西。"},
                             "pluginReadVars": ["inventory", "inventoryCount", "inventoryLastUsed"],
                             "pluginWriteVars": ["inventory", "inventoryCount", "inventoryLastUsed", "pluginResult"],
                             "segment": sid})
                if prev:
                    b.edge(prev, bag)
                first = first or bag
                pending_bag = (bag, c["meta"].strip())   # 條件邊接下一張時才掛，預設邊排在它後面
                prev = bag
                continue
            if c["kind"] == "choice":
                prompt = "\n".join(l["text"] for l in c["lines"] if not l.get("direction"))
                nid = b.add({"type": "choice", "title": f"選擇：{prompt[:12]}", "text": prompt,
                             "choices": [o["label"] for o in c["options"]], "choiceMode": "branch", "segment": sid})
                if prev:
                    b.edge(prev, nid)
                first = first or nid
                prev = nid
                after_choice = None
                for k_, o in enumerate(c["options"]):
                    if o["target"] == "筆記":
                        after_choice = (nid, k_)        # 「今天到這裡 → 筆記」＝接這一段裡選擇卡後面那一張
                    else:
                        choice_links.append((nid, k_, c["file"], " / ".join(c["headings"][:-1]), o["target"]))
                continue
            d = card_node(c)
            if not d:
                continue
            d["segment"] = sid
            for v in c["vars"]:
                d.setdefault("variableOps", []).append(var_op(v))
            nid = b.add(d)
            if after_choice:
                b.edge(after_choice[0], nid); b.edges[-1]["sourceHandle"] = f"choice-{after_choice[1]}"
                after_choice = None
                first = first or nid
                prev = nid
                continue
            if pending_bag:
                bag, want = pending_bag
                b.edge(bag, nid, {"variable": "inventoryLastUsed", "op": "eq", "value": want})
                d.setdefault("variableOps", []).extend([
                    {"id": "op-inbag", "variable": "in_bag", "kind": "set", "value": False},
                    {"id": "op-tape", "variable": "open_tape", "kind": "set", "value": False}])
                leave = b.add({"type": "setVariable", "title": "（放棄，出背包）", "text": "",
                               "variableOps": [{"id": "op-inbag", "variable": "in_bag", "kind": "set", "value": False},
                                               {"id": "op-tape", "variable": "open_tape", "kind": "set", "value": False}],
                               "segment": sid})
                b.edge(bag, leave)              # 預設：沒挑到就回板。一定排在條件邊後面
                b.edge(leave, back_id)
                pending_bag = None
            elif prev:
                b.edge(prev, nid)
            first = first or nid
            prev = nid
        if not first:
            continue
        if pending_bag:                          # 背包卡是最後一張：只剩預設邊
            leave = b.add({"type": "setVariable", "title": "（出背包）", "text": "",
                           "variableOps": [{"id": "op-inbag", "variable": "in_bag", "kind": "set", "value": False}],
                           "segment": sid})
            b.edge(pending_bag[0], leave)
            b.edge(leave, back_id)
        if s["key"][0] == "調查篇-直播":
            back = None          # 插播裡的段落：演完沒有下一張就回到板（interruptExit return），不跳板
        else:
            back = b.add({"type": "boardJump", "title": "回調查板", "jumpBoardId": BID,
                          "jumpNodeId": board_id}, nid=back_id)
            if not (prev and next(n for n in b.nodes if n["id"] == prev)["data"].get("type") == "choice"):
                b.edge(prev, back)
        seg_first[(s["key"][0], " / ".join(s["cards"][0]["headings"][:-1]), s["key"][1])] = (first, sid)
        seg_end[sid] = (prev, back)
        if rule and rule["dest"] in ("catgrass_door", "catgrass_home"):
            rule["scene_only"] = rule["dest"]
            rule["dest"] = "store"       # 私人場景掛在原地點的選單底下（變數帳一）
        if rule and rule.get("or") and "多個地點" in " ".join(notes):
            # 「store 或 laundry」：同一段掛在兩個選單底下
            locs = re.findall(r"`(" + "|".join(LOCS) + r")`", s["trigger"])
            if locs and rule["dest"] not in locs:
                rule["dest"] = locs[0]          # 總表給的預設地點不算數，觸發寫的才是
            for extra in sorted(set(locs) - {rule["dest"]}):
                b.edge(menu_of[extra], first, {"variable": "pick", "op": "eq", "value": sid})
                rules.append({**rule, "segment": sid, "section": s["key"][1], "file": s["key"][0], "dest": extra})
            notes = [x for x in notes if "多個地點" not in x]
        if rule and rule["dest"] in menu_of:
            b.edge(menu_of[rule["dest"]], first, {"variable": "pick", "op": "eq", "value": sid})
            menu_label = (s["cards"][0].get("trigger", {}).get("選單", "").strip()
                          or (LABEL_DAY1.get((rule["dest"], s["key"][1])) if s["key"][0] == "調查篇-第一天-定稿" else None)
                          or labels.get((s["key"][0], s["key"][1])))
            if menu_label:
                rule["label"] = menu_label
            else:
                unlabeled.append((s["key"][0], s["key"][1]))
            rules.append({"segment": sid, "section": s["key"][1], "file": s["key"][0], **rule})
            if notes:
                unresolved.append({"segment": sid, "section": s["key"][1], "notes": notes,
                                   "text": s["trigger"]})
        elif s["key"][0] != "調查篇-直播":
            orphans.append({"segment": sid, "file": s["key"][0], "section": s["key"][1],
                            "trigger": s["trigger"], "notes": notes})
    # 選擇卡的選項接到同一場裡的節（「→ 二」＝那一場底下以「二・」開頭的節），那些節不再列在選單上
    for nid, k_, file_, l1, target in choice_links:
        if target.startswith("共用卡"):
            kids = [(sec, f_, sid_) for (ff, ll, sec), (f_, sid_) in seg_first.items()
                    if ff == file_ and target in ll and l1.split(" / ")[0] in ll]
            ask = next((k for k in kids if "問她" in k[0]), None)
            turn = next((k for k in kids if "轉身" in k[0]), None)
            if ask and turn:
                gate = b.add({"type": "setVariable", "title": "（問幾次了）", "text": "", "variableOps": []})
                b.edge(nid, gate); b.edges[-1]["sourceHandle"] = f"choice-{k_}"
                b.edge(gate, turn[1], {"variable": "cat_asked_glitch", "op": "gte", "value": 3})
                b.edge(gate, ask[1])
                for k in kids:
                    b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == k[2]
                                                        and e["data"]["condition"].get("variable") == "pick")]
                    rules[:] = [r for r in rules if r["segment"] != k[2]]
                continue
        hit = next(((f_, sid_) for (ff, ll, sec), (f_, sid_) in seg_first.items()
                    if ff == file_ and (ll == l1 or ll.startswith(l1) or l1.startswith(ll))
                    and (sec == target or sec.startswith(target + "・") or sec.startswith(target + "、")
                         or (len(target) >= 2 and sec.startswith(target)))), None)
        if not hit:
            unresolved.append({"segment": "", "section": f"選項 → {target}", "notes": ["對不到那一節"], "text": l1})
            continue
        b.edge(nid, hit[0]); b.edges[-1]["sourceHandle"] = f"choice-{k_}"
        b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == hit[1]
                                            and e["data"]["condition"].get("variable") == "pick")]
        rules[:] = [r for r in rules if r["segment"] != hit[1]]
    # 她開台的晚上（調查篇-直播）：「第Ｎ天直播」＝板上的插播，橫幅那張卡由這裡放，推送層換成手機插件卡
    for (ff, _l, sec), (first, sid_) in list(seg_first.items()):
        m_live = re.search(r"第([一二三四五六七八九十]+)天直播", sec) if ff == "調查篇-直播" else None
        if not m_live:
            continue
        n_day = CN_NUM[m_live.group(1)]
        intr = b.add({"type": "interrupt", "title": f"第{m_live.group(1)}天直播", "text": "",
                      "interruptCondition": {"kind": "variable", "variable": "day", "op": "eq", "value": n_day, "match": "all",
                                             "conditions": [{"variable": "day", "op": "eq", "value": n_day},
                                                            {"variable": "slot", "op": "eq", "value": 2}]},
                      "interruptOnce": True, "interruptExit": "return"})
        banner = b.add({"type": "phone", "title": "手機：格莉奇", "text": "", "contact": "格莉奇",
                        "msg": "格莉奇 開始直播了", "segment": sid_})
        b.edge(intr, banner)
        b.edge(banner, first)
    # 直接接下去的段落（設計寫「進門就是這一格，不用選」那種）：上一段演完不回板，進這一段；這一段不上選單
    for file_, from_sec, to_sec in CHAINS:
        frm = next((sid_ for (ff, _l, sec), (_f, sid_) in seg_first.items() if ff == file_ and sec.startswith(from_sec)), None)
        to = next(((f_, sid_) for (ff, _l, sec), (f_, sid_) in seg_first.items() if ff == file_ and sec.startswith(to_sec)), None)
        assert frm and to, f"接不上：{file_} {from_sec} → {to_sec}"
        last, back = seg_end[frm]
        b.edges = [e for e in b.edges if not (e["source"] == last and e["target"] == back)]
        b.edge(last, to[0])
        b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == to[1]
                                            and e["data"]["condition"].get("variable") == "pick")]
        rules[:] = [r for r in rules if r["segment"] != to[1]]
    # 第十二天：一開板就進收尾那一場，不管條件（沒查完就是沒查完的版本）
    ending = next((r for r in rules if r["section"].startswith("十二、最後一頁")), None)
    if ending:
        first_end = next(n["id"] for n in b.nodes if n["data"].get("segment") == ending["segment"])
        b.add({"type": "interrupt", "title": "第十二天，收尾", "text": "",
               "interruptCondition": {"kind": "variable", "variable": "day", "op": "gte", "value": 12},
               "interruptOnce": True, "interruptExit": "jump", "interruptTargetNodeId": first_end})
    # 進門那一下：入口 ─met>=N─▶ 閘（判時段）─▶ 招呼卡 ─▶ 選單；閘的預設與入口的預設都直接進選單。
    # 門檻高的先判（第五次起排在第三次起前面），入口→選單的無條件邊最後接。
    def slot_cond(slots):
        s_ = sorted(slots)
        if not s_ or len(s_) == 4:
            return None
        if s_ == list(range(s_[0], s_[-1] + 1)):
            if s_[0] == 0:
                return {"variable": "slot", "op": "lte", "value": s_[-1]}
            if s_[-1] == 3:
                return {"variable": "slot", "op": "gte", "value": s_[0]}
        return {"variable": "slot", "op": "eq", "value": s_[0]}
    for loc, ens in entries_of.items():
        menu = menu_of[loc]
        gs = sorted([g for g in greetings if g["loc"] == loc], key=lambda g: -g["n"])
        for k, en in enumerate(ens):
            for g in gs:
                sc = slot_cond(g["slots"])
                gate = b.add({"type": "setVariable", "title": f"（{loc} 第{g['n']}次起）", "text": "", "variableOps": []})
                b.edge(en, gate, {"variable": g["var"], "op": "gte", "value": g["n"]})
                if sc:
                    b.edge(gate, g["first"], sc)
                    b.edge(gate, menu)
                else:
                    b.edge(gate, g["first"])
                if k == 0:
                    b.edge(g["last"], menu)
            b.edge(en, menu)
    b.unlabeled = unlabeled
    return b, rules, unresolved, orphans, len(segs), tapes


# 問答矩陣鐵塔那一場：場面 → 格一（進門就是這一格，不用選）；格三演完 → 收尾（三格共用）
CHAINS = [("調查篇-問答矩陣", "一、場面（三格共用）", "格一・問鐵塔關於格莉奇"),
          ("調查篇-問答矩陣", "格三・問鐵塔關於斑比", "收尾（三格共用）")]
MET_VARS = [f"met_{w}" for w in ("管理員", "諾亞", "斑比", "鐵塔", "0x", "貓草", "店員", "材料行老闆", "櫃檯", "保全")]
LABELS_MD = ROOT / "design/調查篇-選單標籤.md"
# 第一天定稿的「上午／下午／晚上」節標題在五個地點重複，靠地點分
LABEL_DAY1 = {("lobby", "下午"): "再去一樓", ("lobby", "晚上"): "抄信箱的名牌",
              ("street", "上午"): "問看板的事", ("street", "下午"): "隨便問一個人",
              ("busstop", "上午"): "問藍十五", ("busstop", "下午"): "等一班車", ("busstop", "晚上"): "問車怎麼這麼久",
              ("metro", "上午"): "跟發傳單的講話", ("metro", "下午"): "接一張傳單", ("metro", "晚上"): "站在二號出口",
              ("store", "上午"): "問立牌可不可以買", ("store", "下午"): "再進去一次", ("store", "晚上"): "問店員一件事"}


def load_labels():
    """design/調查篇-選單標籤.md 的表：{(檔, 節): 選單}。"""
    out = {}
    if not LABELS_MD.exists():
        return out
    for ln in LABELS_MD.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(調查篇[^|]*?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", ln)
        if m and m.group(1) != "檔":
            out[(m.group(1), m.group(2))] = m.group(3)
    return out


def variables():
    v = [("day", "number", 1), ("slot", "number", 0), ("dest", "string", ""),
         ("here", "string", ""), ("pick", "string", ""), ("met", "string", ""),
         ("notes", "string", "[]"), ("notes_free", "string", "[]"),
         ("hole_sightings", "number", 0), ("noah_stage", "number", 0),
         ("night_visits", "number", 0), ("strikes", "number", 0), ("visited", "string", ""),
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
    b, rules, unresolved, orphans, nseg, tapes = build(cards)
    vs = variables()

    bid_ = next(n["id"] for n in b.nodes if n["data"].get("type") == "miniGame" and n["data"]["title"] == "調查板")
    for n in b.nodes:
        if n["data"].get("jumpNodeId") == "@@board":
            n["data"]["jumpNodeId"] = bid_
    # 固定開場：第一天上午一樓（一之一）從它的第一張卡開始，不經過調查板
    board_node = next(n for n in b.nodes if n["data"].get("type") == "miniGame" and n["data"]["title"] == "調查板")
    opening = next((r for r in rules if r["file"] == "調查篇-第一天-定稿" and r["section"].startswith("一之一")), None)
    if opening:
        first_id = next(n["id"] for n in b.nodes if n["data"].get("segment") == opening["segment"])
        board_node["data"].pop("start", None)
        first_node = next(n for n in b.nodes if n["id"] == first_id)
        # 起點是一張有背景的入口場景卡，不然開場那一段沒有背景（2026-09-07 抓到）
        day_bg, night_bg = BG["lobby"]
        open_scene = b.add({"type": "scene", "title": "開場・一樓", "text": "",
                            "background": f"@@{day_bg}", "backgroundNight": f"@@{night_bg}",
                            "transition": "fadeBlack", "transitionMs": 600, "start": True,
                            "autoAdvance": {"enabled": True, "mode": "delay", "delayMs": 500}})
        b.edge(open_scene, first_id)
        first_node["data"].pop("start", None)
        # 開場那一趟 here 是管理員；板之後的第一次開板不該再推進時間（dest 是空的，本來就不會）
        # 開場那一段從選單拿掉：它只演一次，而且是遊戲自己開的
        b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == opening["segment"])]
        rules.remove(opening)
        first_node["data"].setdefault("variableOps", []).extend([
            {"id": "op-dest", "variable": "dest", "kind": "set", "value": "lobby"},   # 回到板上算一個時段
            {"id": "op-here", "variable": "here", "kind": "set", "value": "管理員"},
            {"id": "op-met", "variable": "met", "kind": "set", "value": "管理員"},
            {"id": "op-met-admin", "variable": "met_管理員", "kind": "add", "value": 1}])
    # 可達性：每個段落入口都要有一條 pick 邊
    seg_entries = {n["data"]["segment"]: n["id"] for n in b.nodes if n["data"].get("segment")}
    firsts = {}
    for n in b.nodes:
        s = n["data"].get("segment")
        if s and s not in firsts:
            firsts[s] = n["id"]
    reachable = {e["target"] for e in b.edges if e.get("data", {}).get("condition", {}).get("variable") == "pick"}
    unreached = [s for s, nid in firsts.items() if nid not in reachable]

    print(f"卡片 {len(cards)} 張 → 節點 {len(b.nodes)}、邊 {len(b.edges)}、變數 {len(vs)}、錄音 {len(tapes)} 卷")
    print(f"段落 {nseg} 條：接上選單 {len(rules)} 條、判不出地點 {len(orphans)} 條、判讀有保留 {len(unresolved)} 條")
    print(f"段落入口沒有任何 pick 邊進來的：{len(unreached)} 條")
    print(f"時段判讀：任一 {sum(1 for r in rules if len(r['slots'])==4)}、指定 {sum(1 for r in rules if 0<len(r['slots'])<4)}、沒寫 {sum(1 for r in rules if not r['slots'])}")
    print(f"含「或」要拆的規則：{sum(1 for r in rules if r['or'])} 條")
    if b.unlabeled:
        print(f"沒有選單標籤的段落（退回節標題）：{len(b.unlabeled)} 條")
        for f_, sec in b.unlabeled[:12]:
            print(f"  ・{f_}｜{sec[:40]}")
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
                                   "variables": vs, "rules": rules, "tapes": tapes,
                                   "unresolved": unresolved, "orphans": orphans},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n寫出 {out}")
    # 自我檢查：兩種路由變數以外不可以有任何條件邊
    bad = [e for e in b.edges if e.get("data") and
           e["data"]["condition"]["variable"] not in ("dest", "pick", "rec_ok", "inventoryLastUsed", "slot", "cat_asked_glitch")
           and not e["data"]["condition"]["variable"].startswith("met_")]
    assert not bad, f"有 {len(bad)} 條邊掛了 dest/pick 以外的條件，複合判斷不該變成邊"
    return 0


if __name__ == "__main__":
    sys.exit(main())
