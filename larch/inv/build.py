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
# 地點代號 → 板上那張便條的地名。**跟 larch/inv/push.py 的 LOC_NAME 是同一張表。**
# 這裡要它是因為通關路線那份逐字稿記的是地名（自動玩家照板上讀的），要換回代號。
# 兩邊漂掉的話：路線裡那個地名對不到代號，軌道就會少一步，
# tools/pathlint.py 第八項會紅（走不到的一步）。
LOC_NAME = {"lobby": "一樓", "roof": "頂樓收音機店", "street": "車站前那條街", "studio": "斑比工作室",
            "booth": "錄音間門口", "tower14": "十四樓大廳", "store": "便利商店", "parts": "材料行",
            "busstop": "車站前站牌", "metro": "南港站二號出口", "laundry": "自助洗衣店", "figure": "手辦店"}
NAME_LOC = {v: k for k, v in LOC_NAME.items()}
ROUTE = ROOT / "design/調查篇-通關路線.txt"
# 場景代號→背景。白天／深夜兩套（色溫規格見 design/調查篇-場景.md）。
# 值是 art 檔名的主幹，推送層再換成 Larch 的 asset URL。
BG = {
    "lobby":   ("bg-lobby-day",   "bg-apartment-hall"),
    "roof":    ("bg-roof-day",    "bg-noah-shop"),
    "street":  ("bg-street-day2", "bg-street-night"),
    "studio":  ("bg-bambi-studio-day",  "bg-bambi-studio"),   # 不可以叫 bg-studio-day，會撞正篇（見 push.py 的 BG）
    "booth":   ("bg-booth-hall",  "bg-booth-hall"),   # 十一樓走廊，錄音間在走廊底那扇開著的門裡（2026-09-08 生的）
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
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
          "十一": 11, "十二": 12, "十三": 13, "十四": 14}
# 整份檔都是同一天的
FILE_DAY = {"調查篇-第一天-定稿": 1, "調查篇-第二天": 2}


def day_conds(file, headings):
    """從檔名與標題讀出這一段哪幾天才會播。回 conds 清單（可能是空的）。
    「第五到第九天之間」→ 5..9；「第十到第十三天之間」→ 10..13；「最後一天」→ 收尾門檻；
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


def _val(val):
    if val in ("true", "false"):
        return val == "true"
    return int(val) if re.fullmatch(r"-?\d+", val) else val


def parse_trigger(text):
    """回 (rule, notes)。rule = {dest, slots, conds, any_slot}；判不完整的放 notes。"""
    rule = {"dest": None, "slots": [], "conds": [], "or": False}
    notes = []
    if not text:
        return None, ["沒有觸發"]
    if "或" in re.sub(r"（[^（）]*）", "", text) and "或深夜" not in text and "或下午" not in text and "或晚上" not in text:
        # 「A 或 B」在地點層級＝兩條規則，這裡先標記，不展開
        rule["or"] = True
    if "ending_ready" in text:
        rule["conds"].extend(ENDING_CONDS)
    # 括號裡用「或」接的幾個條件＝任一成立（材料行甲：see_admin 或 see_noah）
    for g in re.findall(r"（([^（）]*`[^（）]*或[^（）]*)）", text):
        alts = [{"variable": m.group(1), "op": OPS[m.group(2)], "value": _val(m.group(3).strip())} for m in EXPR.finditer(g)]
        if len(alts) >= 2:
            rule["conds"].append({"variable": "任一", "op": "any", "value": "", "any": alts})   # 其他讀 c["variable"] 的地方不用改
            text = text.replace(g, "")
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


def desk_scene(b, after, sid):
    """插播（每天收尾、她開台的晚上）都是她在自己桌前，背景換成那一張，不然會停在上一趟去的地方。"""
    sc = b.add({"type": "scene", "title": "桌前", "text": "", "background": "@@bg-desk-night",
                "backgroundNight": "@@bg-desk-night", "transition": "fade", "transitionMs": 340, "segment": sid})
    b.edge(after, sc)
    return sc


# ── 節點 ─────────────────────────────────────────────────
class Board:
    def __init__(self):
        self.nodes, self.edges, self.n, self.x = [], [], 0, 0
        self.en = 0                  # 邊的流水號自己算：有幾處會過濾 b.edges，
                                     # 拿 len(self.edges) 當號碼會在刪掉邊之後重號，撞 id 的線 react-flow 只會畫一條

    def add(self, data, nid=None):
        self.n += 1
        nid = nid or f"{BID}-{self.n:03d}"
        self.x += 300
        self.nodes.append({"id": nid, "type": "story",
                           "position": {"x": self.x, "y": 0}, "data": data})
        return nid

    def edge(self, s, t, cond=None):
        self.en += 1
        e = {"id": f"e{self.en}", "source": s, "target": t,
             "sourceHandle": "right", "animated": True}
        if cond:
            e["data"] = {"condition": {"kind": "variable", **cond}}
        self.edges.append(e)
        return e


# 背包裡每一件東西都有「用了它」的效果（守則本 open_notes、手機 open_phone、錄音卷 open_tape），
# 而那三個效果各自掛著一張 interrupt。劇情裡開背包挑東西時效果照樣會發，插播完又回到背包卡，
# 玩家會覺得卡住。所以進背包前設 in_bag=true（interrupt 的條件都多一項 in_bag==false），
# 挑完或放棄再一次把三個旗標全部清掉。少清一個就會在離開那一刻補插播。
BAG_CLEAR = [{"id": "op-inbag", "variable": "in_bag", "kind": "set", "value": False},
             {"id": "op-tape", "variable": "open_tape", "kind": "set", "value": False},
             {"id": "op-notes", "variable": "open_notes", "kind": "set", "value": False},
             {"id": "op-phone", "variable": "open_phone", "kind": "set", "value": False}]


def bag_card(b, meta, sid):
    """一張打開背包卡"""
    return b.add({"type": "plugin", "title": f"背包：{meta}", "text": "",
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
                    "choices": ["開錄音機", "不開"], "choiceMode": "branch", "segment": sid,
                    "choiceConditions": [None, None]})
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
                   # 自動收下（2026-09-10 改）：原本要玩家在外掛的畫面上按一下收，
                   # 而那張畫面在自動試玩裡完全找不到可以按的東西，整輪停在那裡。
                   # 她按下錄音鍵就等於錄到了，中間那一下確認沒有敘事上的作用。
                   "pluginPresentation": "fullscreen", "pluginSkippable": True,
                   "pluginValues": {"autoCollect": True, "itemId": item_id, "itemName": name,
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
    if c["kind"] in ("narrate", "note", "plate", "screen"):
        text = "\n".join(re.sub(r"^（旁白・描述動作）", "", l["text"])
                         for l in c["lines"] if l["text"])
        d = {"type": "dialogue", "title": text[:14], "text": text, "speaker": NARRATOR}
        if c["kind"] == "screen":
            d["speaker"] = ""            # 畫面：只有字，沒有講者名，不配音（橋段2 十二 排卡註一）
            d["title"] = "畫面：" + text[:10]
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
        # 單一講者的卡裡也可能夾舞台指示（貓草那兩支剪輯就是靠中間那一句隔開，
        # 橋段2 十之三：兩支的文字要一個字都一樣）。夾了就改用 dialogueLines，
        # 指示那一行講者留空，才不會算成格莉奇在講話。
        if any(l.get("direction") for l in c["lines"]):
            d["dialogueLines"] = [
                {"id": f"l{i}",
                 "speaker": NARRATOR if l.get("direction") else c["speaker"],
                 "text": re.sub(r"^（旁白・描述動作）", "", l["text"]),
                 "emotion": "描述動作" if l.get("direction") else ""}
                for i, l in enumerate(c["lines"]) if l["text"]]
        if c.get("remote"):
            d["remote"] = True          # 推送層據此不掛立繪
            # 格莉奇只在螢幕上：哪一種螢幕看地點（直播那三晚是手機），推送層換成合成好的螢幕道具（tools/make_screens.py）
            d["screen"] = "phone" if c["file"] == "調查篇-直播" else (c.get("scene") or "")
        return d
    # talk：多講者
    spoken = [l for l in lines if l.get("speaker")]
    if not spoken:
        return None
    # 舞台指示（斜體那幾行）留在卡上。parse.py 寫的是「不進配音」，不是不進卡片；
    # 先前整行丟掉，管理員那句「你也有。」前面少了她把本子拿出來並排的那一下，變成沒頭沒腦。
    # **講者要填「旁白」，不可以留空字串**：實測空字串的那一行會沿用上一個講者的名牌，
    # 動作句會掛成上一個角色在講話（2026-09-10 在測試專案量過）。
    # 情緒填「描述動作」，那是設計稿給旁白動作句用的值（橋段.md 排卡註），配音要跳過這些行時認它。
    seq = [l for l in c["lines"] if l.get("speaker") or l.get("direction")]
    dl = [{"id": f"l{i}",
           "speaker": NARRATOR if l.get("direction") else l["speaker"],
           "text": re.sub(r"^（旁白・描述動作）", "", l["text"]),
           "emotion": "描述動作" if l.get("direction") else ""}
          for i, l in enumerate(seq)]
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
                      "miniGameReadVars": ["day", "slot", "met", "dest", "night_visits", "seen_booth", "visited", "tries",
                                           "names_seen", "see_stairs", "hole_sightings", "see_admin", "laundry_night1",
                                           "trust_斑比", "strikes", "clue_list", "rec_ok",
                                           "note_mailbox", "trust_店員", "trust_貓草", "cat_visits", "zero_answered",
                                           # 結局名單那一頁的註解：板每個時段組一次 list_text
                                           "seen_catgrass_home", "clue_notfix", "asked_0x_黑洞", "asked_諾亞_帳號", "page1", "trust_保全", "met_保全", "guard_told", "see_clerk", "see_parts", "see_noah",
                                           "asked_鐵塔_斑比", "asked_貓草_斑比", "asked_貓草_鐵塔", "asked_貓草_格莉奇", "seen_catgrass_home", "tube_bought", "tube_given", "asked_斑比_鐵塔"] + [f"open_{k}" for k in
                                          ("roof", "laundry", "figure", "parts", "studio", "tower14")] + MET_VARS,
                      # page1 只有劇情模式會寫：那六格是守則本上的工具動作，
                      # 軌道擋得住「去哪裡」「選哪一格」，擋不住「要不要翻開本子填」。
                      # 自由探索一個字都不碰（2026-09-11 拍板）。
                      "miniGameWriteVars": ["day", "slot", "dest", "here", "night_visits", "met", "visited", "tries", "list_text", "page1", "page1_text", "page1_lead", "page1_gaps"] + MET_VARS})
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
    choice_links, seg_first, seg_end, leftover_notes = [], {}, {}, []
    choice_skips = []          # （閘, 選擇卡, 反向條件, 走哪一格的目標）：條件成立就整張跳過
    for i, s in enumerate(segs):
        sid = f"seg{i:03d}"
        if (s["key"][0], s["key"][1]) in SKIP_SECTIONS:
            continue
        rule, notes = parse_trigger(s["trigger"])
        heads = s["cards"][0].get("headings", [])
        trig_dest = rule["dest"] if rule else None     # 觸發列自己寫了地點的，總表不可以蓋掉（六之二在便利商店，總表寫的是工作室）
        if rule is None:
            rule, notes = {"dest": None, "slots": [], "conds": [], "or": False}, []
        if s["cards"][0]["file"] == "調查篇-問答矩陣" and s["key"][1].startswith("進場"):
            # 材料行第一趟的前奏：入口 ─met_材料行老闆==1─▶ 這兩張 ─▶ 選單。跟招呼卡同一種接法，只演第一次
            first = prev = None
            for c in s["cards"]:
                d = card_node(c)
                if not d:
                    continue
                d["segment"] = "greet-parts-first"
                nid = b.add(d)
                if prev:
                    b.edge(prev, nid)
                first = first or nid
                prev = nid
            if first:
                greetings.append({"loc": "parts", "var": "met_材料行老闆", "n": 1, "op": "eq",
                                  "slots": [0, 1], "first": first, "last": prev})
            continue
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
            prev = desk_scene(b, intr, sid)
            for c in s["cards"]:
                d = card_node(c)
                if not d:
                    continue
                d["segment"] = sid
                d.pop("sceneCode", None)     # 收尾在桌前，不吃檔案裡上一場留下來的 scene
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
                if dest and not trig_dest:
                    rule["dest"] = dest
                    rule.setdefault("dest_from", "總表")
                    if rule["dest_from"] not in ("總表（該人預設）",):
                        rule["dest_from"] = "總表"
                if slots and not rule["slots"]:      # 觸發列自己寫了時段的也照它
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
        named_yet = False       # 斑比那一格：她講出名字之後的卡才能寫「斑比」
        pending_skip = None     # 「掛 `var`」的條件卡：閘的預設邊要接到再下一張
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
                bag = bag_card(b, c["meta"], sid)
                if prev:
                    b.edge(prev, bag)
                first = first or bag
                pending_bag = (bag, c["meta"].strip())   # 條件邊接下一張時才掛，預設邊排在它後面
                prev = bag
                continue
            if c["kind"] == "choice":
                prompt = "\n".join(l["text"] for l in c["lines"] if not l.get("direction"))
                conds = [o.get("cond") for o in c["options"]]
                nid = b.add({"type": "choice", "title": f"選擇：{prompt[:12]}", "text": prompt,
                             "choices": [o["label"] for o in c["options"]], "choiceMode": "branch", "segment": sid,
                             "choiceConditions": [choice_cond([x] if x else []) for x in conds]})
                # 只剩一格有條件、其餘無條件的卡：條件不成立的時候整張跳過，直接去第一格無條件的目標。
                # 不補這個閘的話，走廊兩格都問完之後會跑出一張「一格灰的、一格不問了」的選擇卡，
                # 而它以前是直接收尾的（收回複製卡不可以順手把體感改掉）。
                # 一條邊只掛得下一個條件，所以這件事只有「恰好一格有條件」的時候做得到。
                onec = [i for i, x in enumerate(conds) if x]
                plain = [i for i, x in enumerate(conds) if not x]
                if len(onec) == 1 and plain:
                    v = conds[onec[0]]
                    gate = b.add({"type": "setVariable", "title": f"（{v['variable']}？）", "text": "",
                                  "variableOps": [], "segment": sid})
                    if prev:
                        b.edge(prev, gate)
                    first = first or gate
                    # 兩條邊都等選項接好了才拉：條件邊一定要排在預設邊前面
                    choice_skips.append((gate, nid, {**v, "op": NEG[v["op"]]}, plain[0]))
                elif prev:
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
            # 斑比：她在「三、問斑比・關於鐵塔」那一格才說自己叫斑比（問答矩陣 2027 行）。之前卡上不能寫這個名字。
            spk = [d.get("speaker")] + [l.get("speaker") for l in d.get("dialogueLines", [])]
            if "斑比" in spk:
                sec, f_ = s["key"][1], s["key"][0]
                pre = None
                if sec.startswith("六、路上問不到") or (rule and rule.get("dest") == "laundry"):
                    pre = "洗衣店那個人"
                elif f_ == "調查篇-問答矩陣" and sec.startswith(("零、到訪", "一、問斑比", "二、問斑比", "短版", "深夜版")):
                    pre = "畫她的人"
                elif f_ == "調查篇-問答矩陣" and sec.startswith("三、問斑比") and not named_yet:
                    pre = "畫她的人"
                if pre:
                    d["display"] = {"斑比": pre}
                if "叫斑比" in d.get("text", ""):
                    named_yet = True
            hang = re.search(r"掛 `([A-Za-z_][\w]*)`", c.get("meta") or "")
            nid = b.add(d)
            if pending_skip:                      # 上一張是條件卡：它的閘還要一條預設邊直接到這一張
                b.edge(pending_skip, nid)
                pending_skip = None
            if hang and not after_choice:
                gate = b.add({"type": "setVariable", "title": f"（{hang.group(1)}？）", "text": "", "variableOps": [], "segment": sid})
                if prev:
                    b.edge(prev, gate)
                b.edge(gate, nid, {"variable": hang.group(1), "op": "eq", "value": True})
                first = first or gate
                prev = nid
                pending_skip = gate
                continue
            if after_choice:
                b.edge(after_choice[0], nid); b.edges[-1]["sourceHandle"] = f"choice-{after_choice[1]}"
                after_choice = None
                first = first or nid
                prev = nid
                continue
            if pending_bag:
                bag, want = pending_bag
                cond = {"variable": "inventoryLastUsed", "op": "eq", "value": want}
                b.edge(bag, nid, cond)
                d.setdefault("variableOps", []).extend(BAG_CLEAR)
                # 第二次機會：沒挑到不直接把人送回板，先講一句她還沒走，再開一次包包。
                # 這幾場都是一次性的，第一次關掉包包就永久錯過那一段，而玩家不會知道自己錯過什麼。
                # 第二次還是不挑，那是他的決定，遊戲不再追（走廊與顧店同一個原則）。
                again_say = b.add({"type": "dialogue", "title": "包包還在她手上。",
                                   "text": "包包還在她手上。\n她沒有走。",
                                   "speaker": NARRATOR, "segment": sid})
                again = bag_card(b, want, sid)
                leave = b.add({"type": "setVariable", "title": "（放棄，出背包）", "text": "",
                               "variableOps": list(BAG_CLEAR), "segment": sid})
                b.edge(bag, again_say)          # 預設：沒挑到。一定排在條件邊後面
                b.edge(again_say, again)
                b.edge(again, nid, dict(cond))  # 第二次挑對了，接的是同一張
                b.edge(again, leave)            # 還是不挑就回板
                b.edge(leave, back_id)
                pending_bag = None
            elif prev:
                b.edge(prev, nid)
            first = first or nid
            prev = nid
        if after_choice:
            # 「今天到這裡 → 筆記」可是這一節在選擇卡就結束了：筆記在下一節（貓草那三晚），先記著，最後接
            leftover_notes.append((after_choice, sid))
            after_choice = None
        if not first:
            continue
        if pending_bag:                          # 背包卡是最後一張：只剩預設邊
            leave = b.add({"type": "setVariable", "title": "（出背包）", "text": "",
                           "variableOps": list(BAG_CLEAR), "segment": sid})
            b.edge(pending_bag[0], leave)
            b.edge(leave, back_id)
        if s["key"][0] == "調查篇-直播":
            back = None          # 插播裡的段落演完就回板（interruptExit return）
        elif s["key"][1].startswith("十二、最後一頁"):
            back = None          # 收尾拆成三段：這一段只有那張選擇卡，往下走由選項接（2026-09-09）
        elif s["key"][1].startswith("寫完・"):
            # 結局演完跳到謝幕那一塊版子（design/調查篇-謝幕.md；推送層把 board-credits 換成真的 id）
            back = b.add({"type": "boardJump", "title": "（謝幕）", "text": "", "jumpBoardId": "board-credits",
                          "jumpNodeId": "credits-hud", "segment": sid})
            b.edge(prev, back)
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
    # 選項接走的段落等一下會從 rules 拿掉，可是推送層換場景要知道它幾點演：先把每一段的時段留一份
    b.seg_slots = {r["segment"]: r.get("slots") or [] for r in rules}
    for nid, k_, file_, l1, target in choice_links:
        if target.startswith("共用卡"):
            kids = [(sec, f_, sid_) for (ff, ll, sec), (f_, sid_) in seg_first.items()
                    if ff == file_ and target in ll and l1.split(" / ")[0] in ll]
            ask = next((k for k in kids if "問她" in k[0]), None)
            turn = next((k for k in kids if "轉身" in k[0]), None)
            if ask and turn:
                # 走乙這條路也算來過一晚（甲那條的筆記卡上有同樣的加法）
                gate = b.add({"type": "setVariable", "title": "（問幾次了）", "text": "",
                              "variableOps": [{"id": "op-met", "variable": "met_貓草", "kind": "add", "value": 1},
                                              {"id": "op-visits", "variable": "cat_visits", "kind": "add", "value": 1}]})
                b.edge(nid, gate); b.edges[-1]["sourceHandle"] = f"choice-{k_}"
                b.edge(gate, turn[1], {"variable": "cat_asked_glitch", "op": "gte", "value": 3})
                b.edge(gate, ask[1])
                for k in kids:
                    b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == k[2]
                                                        and e["data"]["condition"].get("variable") == "pick")]
                    rules[:] = [r for r in rules if r["segment"] != k[2]]
                continue
        cands = [(f_, sid_) for (ff, ll, sec), (f_, sid_) in seg_first.items()
                 if ff == file_ and (ll == l1 or ll.startswith(l1) or l1.startswith(ll))
                 and (sec == target or sec.startswith(target + "・") or sec.startswith(target + "、")
                      or (len(target) >= 2 and sec.startswith(target)))]
        # 同一個字開頭的節不只一個（貓草三晚各有一節「甲」）：取選擇卡後面最近的那一節
        here_sid = next((n["data"].get("segment") or "" for n in b.nodes if n["id"] == nid), "")
        after = sorted([c for c in cands if c[1] > here_sid], key=lambda c: c[1])
        hit = after[0] if after else (cands[0] if cands else None)
        if not hit:
            unresolved.append({"segment": "", "section": f"選項 → {target}", "notes": ["對不到那一節"], "text": l1})
            continue
        b.edge(nid, hit[0]); b.edges[-1]["sourceHandle"] = f"choice-{k_}"
        # 那一格如果是某張卡的「整張跳過」出口，閘的兩條邊在這裡才拉得出來（目標剛剛才算出來）
        for gate, cnid, neg, k0 in choice_skips:
            if cnid == nid and k0 == k_:
                b.edge(gate, hit[0], neg)      # 條件成立＝那一格已經沒得選了，整張跳過
                b.edge(gate, cnid)             # 預設：照樣演這張卡
        b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == hit[1]
                                            and e["data"]["condition"].get("variable") == "pick")]
        rules[:] = [r for r in rules if r["segment"] != hit[1]]
    for (nid_, k_), sid_ in leftover_notes:
        nxt = next((n["id"] for n in b.nodes if (n["data"].get("segment") or "") > sid_
                    and n["data"].get("title", "").startswith("筆記：")), None)
        assert nxt, f"選項 → 筆記 接不到（{sid_}）"
        b.edge(nid_, nxt); b.edges[-1]["sourceHandle"] = f"choice-{k_}"
    # 推劇情的段落只演一次：它自己設的旗標當門檻（2026-09-08 試玩抓到深夜的鐵塔可以一直重播）。
    # 設計寫了「可以重來」的不在這張表上（乙・幫誰畫的、櫃檯迴圈、路人）。
    for r in rules:
        for sec_prefix, flag in ONCE_BY_FLAG.items():
            if r["section"].startswith(sec_prefix) and not any(c.get("variable") == flag for c in r["conds"]):
                r["conds"] = r["conds"] + [{"variable": flag, "op": "eq", "value": False}]
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
        b.edge(desk_scene(b, banner, sid_), first)
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
    # 第十四天：一開板就進收尾那一場，不管條件（沒查完就是沒查完的版本）
    ending = next((r for r in rules if r["section"].startswith("十二、最後一頁")), None)
    if ending:
        # 這一段是插播跳進來的，不經過頂樓那張入口場景：卡頭寫了場景的卡都要自己帶背景（推送層看 force_bg）
        # 收尾固定在最後一天（2026-09-09 拍板）：頂樓那一格不再進選單，只有這張插播叫得動它。
        # 提早收尾會讓玩得順的人跳過第十與第十一天的收尾筆記，那兩則是最後兩條刪除線。
        end_segs = sorted({n["data"]["segment"] for n in b.nodes
                           if (n["data"].get("segment") or "").startswith("seg")
                           and n["data"].get("segment") in
                           {sid_ for (ff, _l, sec), (_f, sid_) in seg_first.items()
                            if ff == "調查篇-橋段2" and (sec.startswith("十二、最後一頁")
                                                        or sec.startswith("再看・") or sec.startswith("寫完・"))}})
        b.force_bg = end_segs or [ending["segment"]]
        first_end = next(n["id"] for n in b.nodes if n["data"].get("segment") == ending["segment"])
        rules[:] = [r for r in rules if r is not ending]
        b.add({"type": "interrupt", "title": "第十四天，收尾", "text": "",
               "interruptCondition": {"kind": "variable", "variable": "day", "op": "gte", "value": 14},
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
                b.edge(en, gate, {"variable": g["var"], "op": g.get("op", "gte"), "value": g["n"]})
                if sc:
                    b.edge(gate, g["first"], sc)
                    b.edge(gate, menu)
                else:
                    b.edge(gate, g["first"])
                if k == 0:
                    b.edge(g["last"], menu)
            b.edge(en, menu)
    # 「整張跳過」的閘一定要兩條邊都接上（條件邊 ＋ 預設邊），少一條就是選項目標沒對到，
    # 那張卡會變成走不出去的死路。
    for gate, cnid, _neg, k0 in choice_skips:
        outs = [e for e in b.edges if e["source"] == gate]
        assert len(outs) == 2, f"跳過閘 {gate} 只接了 {len(outs)} 條邊（選擇卡 {cnid} 第 {k0} 格）"
    b.unlabeled = unlabeled
    return b, rules, unresolved, orphans, len(segs), tapes


# 被後來的定稿取代、可是同一份檔裡其他節還在用的段落（整份檔不能作廢）
SKIP_SECTIONS = {("調查篇-第二天", "場景三・一樓（第二天・晚上七點多）"),      # 正本是橋段「一、第一次擦身而過」
                 ("調查篇-問答矩陣", "三、那一張卡（三格都在裡面）")}          # 0x 那張卡的抄本，正本在橋段六（2026-09-08 試玩抓到：沒預約就在櫃檯撞到 0x）
# 只演一次的段落：節標題開頭 → 它自己設的旗標（演完為真，選單就收掉）
ONCE_BY_FLAG = {
    "二、問管理員・關於黑洞先生": "see_admin", "Ｃ、給諾亞看信箱那一頁": "asked_諾亞_信箱", "Ｂ、問諾亞・關於黑洞先生": "asked_諾亞_黑洞",
    "深夜版": "open_tower14", "五之一、第二次問": "bambi_revised",
    "二、關於黑洞先生（`store`": "asked_貓草_黑洞", "三、關於鐵塔（`store`": "asked_貓草_鐵塔",
    "四、關於 0x（`figure`": "asked_貓草_0x", "五、關於斑比（`figure`": "asked_貓草_斑比", "七、她是不是真的會忘": "deadend_cat",
    "二、問店員・關於黑洞先生": "see_clerk", "Ａ・斑比的工作室": "names_seen", "五、深夜的鐵塔": "clue_notfix",
    "Ａ・問她的事": "deadend_cat_glitch", "Ｂ・問他手上那個": "cat_room_mentioned", "九、你不要寫出去喔": "seen_catgrass_home",
    "第一晚": "laundry_night1", "甲・桌上那幾張": "open_studio",
    # 路人那五格是死路，設計上要有內容，可是同一段看第二次就沒有內容了（2026-09-10）
    "等車的阿姨": "seen_aunt", "跑馬燈": "seen_ticker", "發傳單的": "seen_flyer",
    "趕時間的": "seen_rush", "看板底下": "seen_board",
}
# 問答矩陣鐵塔那一場：場面 → 格一（進門就是這一格，不用選）；格三演完 → 收尾（三格共用）
CHAINS = [("調查篇-問答矩陣", "一、場面（三格共用）", "格一・問鐵塔關於格莉奇"),
          ("調查篇-橋段2", "再看・第一頁", "寫完・那一場"),
          # 第三晚的甲跟乙都要走到「他先開口」（那一張才給 trust 1），可是甲原本演完就回板，
          # 選「問他吃的那一份」的人拿不到「三次了」，整條線停在零階（2026-09-10 實測）
          ("調查篇-橋段2", "甲・那一份（第三次）", "他先開口（第三次"),
          # 2026-09-11：走廊原本複製出來的格二之二、格三之二已經收回同一張卡（選項吃條件），
          # 兩條接收尾的線跟著刪掉。格三演完接收尾這一條還在，因為格三後面那張選擇卡
          # 在兩格都問過的時候會被閘整張跳過（choice_skip），跳過之後就要有人接住。
          ("調查篇-問答矩陣", "格三・問鐵塔關於斑比", "收尾（三格共用）")]
MET_VARS = [f"met_{w}" for w in ("管理員", "諾亞", "斑比", "鐵塔", "0x", "貓草", "店員", "材料行老闆", "櫃檯", "保全")]
LABELS_MD = ROOT / "design/調查篇-選單標籤.md"
# 第一天定稿的「上午／下午／晚上」節標題在五個地點重複，靠地點分
LABEL_DAY1 = {("lobby", "下午"): "再去一樓", ("lobby", "晚上"): "抄信箱的名牌",
              ("street", "上午"): "問看板的事", ("street", "下午"): "隨便問一個人",
              ("busstop", "上午"): "問藍十五", ("busstop", "下午"): "等一班車", ("busstop", "晚上"): "問車怎麼這麼久",
              ("metro", "上午"): "跟發傳單的講話", ("metro", "下午"): "接一張傳單", ("metro", "晚上"): "站在二號出口",
              ("store", "上午"): "問立牌可不可以買", ("store", "下午"): "再進去一次", ("store", "晚上"): "問店員一件事"}


# ── 開場選模式（design/調查篇.md 七之〇）────────────────────────────────────
# 劇情模式的軌道來自 design/調查篇-通關路線.txt，那是一輪真的跑完的完美通關逐字稿。
# 這裡只解析它，不重跑：板上每一個時段該去哪、劇情裡每一張選擇卡該選哪一格。
NEG = {"eq": "neq", "neq": "eq", "gte": "lt", "lt": "gte", "lte": "gt", "gt": "lte"}
# 掛上去＝只有自由探索按得下去，劇情模式那一格會 disabled。
# **寫 `mode == free` 不寫 `mode != story` 是故意的**：字串的 eq 這塊板子上已經在用了
# （`dest == lobby` 那批邊），neq 配字串還沒在平台上驗過。萬一 neq 判反，
# 壞掉的會是自由探索——那是預設玩法，不可以拿它去賭一個沒驗過的運算子。
STORY_OFF = {"variable": "mode", "op": "eq", "value": "free"}


def choice_cond(clauses):
    """一格選項的條件。形狀跟邊的條件一樣（2026-09-11 在測試專案實測），
    多條用 conditions 陣列裝、match=all，最外層再抄第一條（平台兩邊都讀）。
    沒有條件的那一格要填 None，不可以省略——choiceConditions 是跟 choices 一一對應的陣列。"""
    if not clauses:
        return None
    c0 = clauses[0]
    return {"kind": "variable", "variable": c0["variable"], "op": c0["op"], "value": c0["value"],
            "match": "all", "conditions": [dict(x) for x in clauses]}


MODE_KEYS = ("題目", "劇情模式", "自由探索")


def load_mode_card():
    """開場那張卡的字：design/調查篇.md 七之〇 最後那張兩欄表。稿子是來源，這裡只讀。"""
    out = {}
    for ln in (ROOT / "design/調查篇.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(題目|劇情模式|自由探索)\s*\|\s*(.+?)\s*\|\s*$", ln)
        if m and m.group(2) not in ("內容", "行為"):
            out.setdefault(m.group(1), m.group(2))
    assert all(k in out for k in MODE_KEYS), f"design/調查篇.md 七之〇 少了開場那張卡的字：{out}"
    return out


def load_route():
    """通關路線逐字稿 → 一輪完美通關的每一步。

        board   [{day, slot, loc, label}]     板上那個時段去哪、在選單上選哪一段
        choices [(day, slot, [選項標籤…], 選了第幾格)]

    來源格式是 tools/autoplay.mjs 印出來的：`=== 板 第 N 天 ・ 時段` 起一段，
    `→ 去 地名`、`→ 選「選單標籤」`、`[選項] 01甲 | 02乙 → 選 01甲`。
    解析法跟 tools/gen_guide.py 的 build_walkthrough() 同一套。"""
    board, choices, cur = [], [], None
    if not ROUTE.exists():
        return board, choices
    for ln in ROUTE.read_text(encoding="utf-8").split("\n"):
        if m := re.match(r"^=== 板 第 (\d+) 天 ・ (上午|下午|晚上|深夜)", ln):
            cur = {"day": int(m.group(1)), "slot": SLOT[m.group(2)], "loc": None, "label": ""}
            board.append(cur)
            continue
        if cur is None:
            continue
        if m := re.match(r"^→ 去 (\S+)", ln):
            cur["loc"] = NAME_LOC.get(m.group(1))
            cur["place"] = m.group(1)
            continue
        if m := re.search(r"→ 選「(.+?)」", ln):
            if not cur["label"]:
                cur["label"] = m.group(1)
            continue
        if m := re.search(r"\[選項\] (.+?) → 選 (\d\d)", ln):
            labels = [re.sub(r"^\d\d", "", x.strip()) for x in m.group(1).split("|")]
            choices.append((cur["day"], cur["slot"], labels, int(m.group(2)) - 1))
    return board, choices


def rail(b, rules, board, choices):
    """把通關路線那一輪的每一步對到板上，回傳 ({節點 id: 該選第幾格}, 對不上的步)。

    **每一步都要逐項查過**，不是只看對得上幾張（2026-09-11 退回過一次：
    軌道只擋「去哪裡」不擋「選單選哪一格」，自動玩家在第 2 天晚上就選了別的，
    貓草那條線整條斷掉，結局少兩行註解，而 build 只報了「對上 10/11」）：

      一、地名對得到地點代號嗎（`NAME_LOC`，跟 push.py 的 LOC_NAME 同一張表）
      二、那個地點的選單上真的有這一格嗎（規則的 dest ＋ label）
      三、那一格在這個時段開著嗎（規則的 slots）
      四、那一步的選擇卡對得到板上哪一張（標籤一模一樣、段落在選單那一段之後）

    選擇卡只靠標籤會對錯：「開錄音機／不開」全篇有五張，答案還不一樣（貓草那一張是不開）。
    四項任何一項不過就進 miss，build 會印出來，tools/pathlint.py 第九項會把它判紅。"""
    picks, used, miss = {}, set(), []
    seg_of, rule_of = {}, {}
    for r in rules:
        if r.get("label"):
            seg_of.setdefault((r["dest"], r["label"]), r["segment"])
            rule_of.setdefault((r["dest"], r["label"]), []).append(r)
    step = {}
    for s in board:
        tag = {"day": s["day"], "slot": s["slot"]}
        if not s.get("loc"):
            miss.append({**tag, "labels": [s.get("place", "")], "why": "地名對不到地點代號"})
            continue
        step[(s["day"], s["slot"])] = s
        if not s["label"]:
            continue                      # 那一趟在選單上什麼都沒選（選單是空的），不必擋
        rs = rule_of.get((s["loc"], s["label"]))
        if not rs:
            miss.append({**tag, "labels": [s["label"]], "why": f"{s['loc']} 的選單上沒有這一格"})
            continue
        if not any((not r["slots"]) or s["slot"] in r["slots"] for r in rs):
            miss.append({**tag, "labels": [s["label"]],
                         "why": f"{s['loc']}「{s['label']}」這個時段不開（開在時段 "
                                + "／".join(str(x) for r in rs for x in (r["slots"] or ["任一"])) + "）"})
            continue
        s["seg"] = rs[0]["segment"]
    chnodes = [n for n in b.nodes if (n["data"].get("type") == "choice")]
    for day, slot, labels, k in choices:
        s = step.get((day, slot)) or {}
        sid0 = seg_of.get((s.get("loc"), s.get("label")), "")
        cands = [n for n in chnodes if n["data"].get("choices") == labels and n["id"] not in used]
        after = [n for n in cands if (n["data"].get("segment") or "") >= sid0]
        hit = (after or cands or [None])[0]
        if hit is None:
            # 同一張卡在逐字稿裡被記了兩次（結局那一張，自動玩家重播了一次）：
            # 已經對上而且答案一樣就當重複，不算對不到。
            same = [n for n in chnodes if n["data"].get("choices") == labels and picks.get(n["id"]) == k]
            if not same:
                miss.append({"day": day, "slot": slot, "labels": labels, "why": "對不到選擇卡"})
            continue
        used.add(hit["id"])
        picks[hit["id"]] = k
    return picks, miss


def walk_str(board):
    """軌道字串：`天|時段|地點代號|選單標籤`，一步一段，分號隔開。

    欄位分隔用半形 `|`，因為選單標籤裡有全形逗號（「深夜，去工作室」），
    也有頓號。標籤要一起送進去，不然選單那一張擋不了「選哪一格」——
    2026-09-11 就是少了它，劇情模式走得完可是走不出完美結局。"""
    return ";".join(f"{s['day']}|{s['slot']}|{s['loc']}|{s.get('label', '')}"
                    for s in board if s.get("loc"))


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


def variables(walk=""):
    # mode：開場那張卡寫的。'story' 劇情模式（板只開攻略的下一步、選擇卡只開該選的那一格）、
    #       'free' 自由探索。預設 free：萬一沒經過開場那張卡，玩到的就是原本那一版。
    # walk：劇情模式的軌道，"天|時段|地點代號|選單標籤" 用分號串起來（見 walk_str）。
    #       放在變數的預設值裡，板卡與選單卡讀它就好，不必再多一條注入管線
    #       （兩張都是 sandbox 的 iframe，載不了外部檔案）。
    v = [("mode", "string", "free"), ("walk", "string", walk),
         ("day", "number", 1), ("slot", "number", 0), ("dest", "string", ""),
         ("here", "string", ""), ("pick", "string", ""), ("met", "string", ""),
         ("notes", "string", "[]"), ("notes_free", "string", "[]"),
         ("hole_sightings", "number", 0), ("noah_stage", "number", 0),
         ("night_visits", "number", 0), ("strikes", "number", 0), ("visited", "string", ""),
         ("tries", "string", ""), ("list_text", "string", ""),
         ("page1_gaps", "string", "她把本子翻到第一頁。"),
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
                            "transition": "fadeBlack", "transitionMs": 600,
                            "autoAdvance": {"enabled": True, "mode": "delay", "delayMs": 500}})
        b.edge(open_scene, first_id)
        first_node["data"].pop("start", None)
        # 真正的第一張卡是選模式（design/調查篇.md 七之〇）。兩格各接一張設變數卡，
        # 設完都進開場那張場景。choice 卡自己的 variableOps 是進卡就發，分不出玩家選了哪一格。
        mc = load_mode_card()
        mode_pick = b.add({"type": "choice", "title": "開場：這一輪要怎麼玩", "text": mc["題目"],
                           "choices": [mc["劇情模式"], mc["自由探索"]], "choiceMode": "branch",
                           "choiceConditions": [None, None], "start": True})
        for k_, val in enumerate(("story", "free")):
            setm = b.add({"type": "setVariable", "title": f"（mode ← {val}）", "text": "",
                          "variableOps": [{"id": "op-mode", "variable": "mode", "kind": "set", "value": val}]})
            b.edge(mode_pick, setm); b.edges[-1]["sourceHandle"] = f"choice-{k_}"
            b.edge(setm, open_scene)
        # 開場那一趟 here 是管理員；板之後的第一次開板不該再推進時間（dest 是空的，本來就不會）
        # 開場那一段從選單拿掉：它只演一次，而且是遊戲自己開的
        b.edges = [e for e in b.edges if not (e.get("data") and e["data"]["condition"].get("value") == opening["segment"])]
        rules.remove(opening)
        first_node["data"].setdefault("variableOps", []).extend([
            {"id": "op-dest", "variable": "dest", "kind": "set", "value": "lobby"},   # 回到板上算一個時段
            {"id": "op-here", "variable": "here", "kind": "set", "value": "管理員"},
            {"id": "op-met", "variable": "met", "kind": "set", "value": "管理員"},
            {"id": "op-met-admin", "variable": "met_管理員", "kind": "add", "value": 1}])
    # 劇情模式的軌道：板上每個時段去哪、每一張選擇卡該選哪一格（design/調查篇.md 七之〇）
    route_board, route_choices = load_route()
    picks, rail_miss = rail(b, rules, route_board, route_choices)
    vs = variables(walk_str(route_board))
    for n in b.nodes:
        d = n["data"]
        if d.get("type") != "choice":
            continue
        cc = list(d.get("choiceConditions") or [None] * len(d.get("choices") or []))
        if len(cc) != len(d.get("choices") or []):
            cc = [None] * len(d["choices"])
        if n["id"] in picks:
            # 不該選的那幾格掛 mode != story：劇情模式按不下去，自由探索照舊全開
            for i in range(len(cc)):
                if i == picks[n["id"]]:
                    continue
                old = (cc[i] or {}).get("conditions") or []
                cc[i] = choice_cond(list(old) + [dict(STORY_OFF)])
        d["choiceConditions"] = cc
    board_node["data"]["miniGameReadVars"] = ["mode", "walk"] + board_node["data"]["miniGameReadVars"]

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
    _n_loc = sum(1 for s in route_board if s.get("loc"))
    _n_seg = sum(1 for s in route_board if s.get("seg"))
    _n_nolabel = sum(1 for s in route_board if s.get("loc") and not s.get("label"))
    print(f"劇情模式軌道：板上 {len(route_board)} 步 → 地名對到 {_n_loc}、"
          f"選單那一格對到規則 {_n_seg}、選單上沒東西可選 {_n_nolabel}；"
          f"選擇卡對上 {len(picks)}/{len(route_choices)} 張"
          + (f"　★ 對不到 {len(rail_miss)} 步" if rail_miss else ""))
    for m_ in rail_miss[:8]:
        print(f"  ・第 {m_['day']} 天 時段{m_['slot']}　{m_['why']}　{'｜'.join(m_['labels'])[:40]}")
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
        out.write_text(json.dumps({"boardId": BID, "nodes": b.nodes, "edges": b.edges, "seg_slots": getattr(b, "seg_slots", {}), "force_bg": getattr(b, "force_bg", []),
                                   "variables": vs, "rules": rules, "tapes": tapes,
                                   "walk": {"board": route_board, "picks": picks, "miss": rail_miss},
                                   "unresolved": unresolved, "orphans": orphans},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n寫出 {out}")
    # 自我檢查：兩種路由變數以外不可以有任何條件邊
    hung = {n["data"]["title"][1:-2] for n in b.nodes if n["data"].get("title", "").endswith("？）")}   # 「掛 `var`」的閘
    bad = [e for e in b.edges if e.get("data") and
           e["data"]["condition"]["variable"] not in ("dest", "pick", "rec_ok", "inventoryLastUsed", "slot", "cat_asked_glitch")
           and not e["data"]["condition"]["variable"].startswith("met_") and e["data"]["condition"]["variable"] not in hung]
    assert not bad, f"有 {len(bad)} 條邊掛了 dest/pick 以外的條件，複合判斷不該變成邊：{sorted({e['data']['condition']['variable'] for e in bad})}"
    return 0


if __name__ == "__main__":
    sys.exit(main())
