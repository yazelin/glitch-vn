#!/usr/bin/env python3
"""把 larch/inv/out/board.json 推上 Larch。**這是唯一會碰 Larch 的一支。**

    python3 larch/inv/build.py --out larch/inv/out/board.json   # 先產
    python3 larch/inv/push.py --dry                             # 只組 payload、印統計，不連線
    python3 larch/inv/push.py                                   # 建專案（第一次）、上素材、推版子、回讀比對

專案 id 存在 larch/inv/state.json（第一次跑會建一個新專案）；免登入預覽網址寫在 larch/inv/preview.json（不進 repo）。
**調查篇是獨立的新專案，不是正文那個**（正文 id 在 larch/config.py，別混）。

推送層做的事（build.py 刻意不做的）：
  一、@@larch/cards/*.html → 檔案內容（選單卡另外注入該地點的規則）
  二、@@bg-xxx → 素材網址（新背景上傳到新專案；正文已有的沿用 R2 網址）
  三、補三種 build.py 沒有的節點：調查板與每個選單的「沒選到就回板」預設邊、
      翻開守則本的 interrupt 卡（背包 HUD 的常駐入口，見 design/調查篇-背包與謎題.md 八）
  四、變數表：board.json 的加規則用到的、背包插件的、筆記卡的
  五、版面：一段一列，不然四百多張卡排成一條線

推完一定回讀比對卡數與帶條件的邊數。整包 PUT 專案會清版子，所以
順序固定是「PUT 專案設定 → PUT 版子」，不能反過來。
"""
import argparse, base64, json, pathlib, re, sys, time, urllib.error, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
STATE = HERE / "state.json"
BOARD_JSON = HERE / "out" / "board.json"
CARDS = ROOT / "larch/cards"
MAIN_ASSETS = json.loads((ROOT / "larch/assets.json").read_text(encoding="utf-8"))
NEW_BG_DIR = ROOT / "art/bg-investigation"

# 立繪：新五個在 art/inv-cast（2026-09-05 codex 生、09-07 去背），正文七個沿用 assets.json 的網址。
# 鍵是調查板 here 裡的名字。黑洞先生刻意不上台：他在這款裡只能是旁白描述的「穿西裝的先生」。
SPRITE_LOCAL = {"管理員": "art/inv-cast/sprite-admin.png", "店員": "art/inv-cast/sprite-clerk.png",
                "保全": "art/inv-cast/sprite-guard.png", "老闆": "art/inv-cast/sprite-parts.png",
                "櫃檯": "art/inv-cast/sprite-reception.png"}
SPRITE_MAIN = {"諾亞": "sprite-noah", "斑比": "sprite-bambi", "鐵塔": "sprite-tower",
               "貓草": "sprite-catgrass", "0x": "sprite-zerox"}
SPRITE_SCALE = {"諾亞": .98, "斑比": .92, "鐵塔": 1.04, "貓草": .98, "0x": .94}
# 格莉奇講話的卡掛哪一種螢幕（art/screens，tools/make_screens.py 合成）：地點 → (道具, 縮放, 抬高)
SCREEN_FOR = {"lobby": ("notice", .72, 0), "store": ("standee", .78, 0), "figure": ("standee", .78, 0),
              "street": ("billboard", .62, 0), "busstop": ("billboard", .62, 0), "metro": ("billboard", .62, 0),
              "parts": ("tv", .7, 0), "phone": ("phone", .76, 0)}   # 抬高靠圖底下補的透明邊（tools/make_screens.py），不靠 offsetY
ITEM_LOCAL = {"rulebook": "art/items/item-rulebook.png", "phone": "art/items/item-phone.png", "recorder": "art/items/item-recorder.png",
              "tape": "art/items/item-tape.png"}

API = "https://larch.ink/api/agent"
KEY_PATH = pathlib.Path.home() / ".config/larch/key"

NAME = "格莉奇與黑洞先生・調查篇"
DESC = ("AI 主播格莉奇說她只有 4KB 的記憶。全世界當成哏，只有你當真。\n"
        "十一天，八個地點，一本買來的守則本。去問每一個認識她的人：她真的會忘嗎，為什麼沒有人把她修好。\n"
        "同一家店去五次，店員就不再說歡迎光臨。")

# 場景代號 → (白天, 夜晚) 背景，跟 build.py 的 BG 一致；只給段落中途換場景用
BG_MAP = {"lobby": ("bg-lobby-day", "bg-apartment-hall"), "roof": ("bg-roof-day", "bg-noah-shop"),
          "street": ("bg-street-day2", "bg-street-night"), "studio": ("bg-studio-day", "bg-bambi-studio"),
          "booth": ("bg-booth-hall", "bg-booth-hall"), "tower14": ("bg-tower14-day", "bg-tower14-night"),
          "store": ("bg-store-day", "bg-store-night"), "parts": ("bg-parts-day", "bg-parts"),
          "busstop": ("bg-busstop-day", "bg-busstop"), "metro": ("bg-metro-day", "bg-metro"),
          "laundry": ("bg-laundry-day", "bg-laundry"), "figure": ("bg-figure-day", "bg-figure"),
          "catgrass_door": ("bg-catgrass-door", "bg-catgrass-door"), "catgrass_home": ("bg-catgrass-home", "bg-catgrass-home")}
# 玩家看得到的人名：她不知道鐵塔叫鐵塔，只知道他是經紀人。變數與規則裡仍用「鐵塔」，只有顯示換掉
DISPLAY = {"鐵塔": "經紀人"}
# 板與選單用的：問到名字（asked_斑比_鐵塔）之前叫「畫她的人」
DISPLAY_UI = {"鐵塔": "經紀人", "斑比": {"until": "asked_斑比_鐵塔", "name": "畫她的人"}}
LOC_NAME = {"lobby": "一樓", "roof": "頂樓收音機店", "street": "車站前那條街", "studio": "斑比工作室",
            "booth": "錄音間門口", "tower14": "十四樓大廳", "store": "便利商店", "parts": "材料行",
            "busstop": "車站前站牌", "metro": "南港站二號出口", "laundry": "自助洗衣店", "figure": "手辦店"}
# 卡片講者 → 調查板 here 裡用的名字。玩家、旁白、格莉奇（只在螢幕上）不算「誰在」。
WHO_MAP = {"材料行老闆": "老闆", "住戶": "路人", "路人乙": "路人", "高中生": "路人", "阿姨": "路人",
           "送貨的": "路人", "發傳單的": "路人", "上班族": "路人"}
NOT_WHO = {"玩家", "旁白", "格莉奇"}
# 每個地點可能在場的人（board.html 的常駐加訪客）。段落裡講話的人不在這張表上，
# 就不用「誰在」擋它（鐵塔在街上、0x 在十四樓那種：設計上就是別的方式碰到）。
POSSIBLE = {"lobby": {"管理員", "黑洞先生"}, "roof": {"諾亞"}, "street": {"路人"}, "busstop": {"路人"},
            "metro": {"路人"}, "store": {"店員", "貓草", "鐵塔", "斑比"}, "parts": {"老闆", "諾亞"},
            "laundry": {"貓草", "斑比"}, "figure": {"店員", "貓草"}, "studio": {"斑比"},
            "booth": {"鐵塔"}, "tower14": {"櫃檯", "保全"}}

INVENTORY_DEFAULT = json.dumps([
    {"id": "rulebook", "n": "守則本", "d": "一千二。第一頁還是空的。", "c": False,
     "e": "set", "v": "open_notes", "x": True},
    {"id": "phone", "n": "手機", "d": "訊息、她的頁面、直播。沒有人會打來。", "c": False,
     "e": "set", "v": "open_phone", "x": True},
    # 錄音機本身不是動作道具：對話裡有人講話的時候才按得下去（那時候會跳「開錄音機」）。放在包包裡是讓玩家知道它在
    {"id": "recorder", "n": "錄音機", "d": "轉盤會卡，頂樓那個人修好之前錄不了。有人講話的時候按得下去。", "c": False,
     "useConditionVariable": "recorder_now", "useConditionValue": True,
     "useConditionMessage": "現在沒有人在講話。有人講話的時候，畫面上會跳出開錄音機。"},
], ensure_ascii=False)


# ── API ─────────────────────────────────────────────────
def key():
    return KEY_PATH.read_text().strip()


def api(method, path, body=None, tries=4):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(API + path, data, {"Authorization": "Bearer " + key(),
                                                     "Content-Type": "application/json"}, method=method)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode("utf-8", "replace")
            if e.code < 500 or i == tries - 1:
                raise SystemExit(f"{method} {path} → {e.code} {msg}")
            print(f"  Larch 回 {e.code}，{2 ** i * 5} 秒後重試")
            time.sleep(2 ** i * 5)


def upload(pid, path, category="scene"):
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}[path.suffix.lower()]
    r = api("POST", f"/projects/{pid}/media", {"name": path.name, "mimeType": mime, "category": category,
                                             "base64": base64.b64encode(path.read_bytes()).decode()})
    return r["asset"]["url"]


# ── payload ─────────────────────────────────────────────
def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def bg_url(key_, state, pid=None, dry=False):
    """@@bg-xxx → 網址。順序：新專案已上傳的 → 正文專案的 R2 網址 → 本機 art/bg-investigation 上傳。"""
    assets = state.setdefault("assets", {})
    if key_ in assets:
        return assets[key_]
    if key_ in MAIN_ASSETS:
        return MAIN_ASSETS[key_]
    local = NEW_BG_DIR / f"{key_}.jpg"
    if local.exists():
        if dry:
            return f"(上傳) {local.name}"
        assets[key_] = upload(pid, local)
        save_state(state)
        return assets[key_]
    return None


def local_asset(rel, state, pid, dry, category):
    key_ = pathlib.Path(rel).stem
    assets = state.setdefault("assets", {})
    if key_ in assets:
        return assets[key_]
    if dry:
        return f"(上傳) {rel}"
    assets[key_] = upload(pid, ROOT / rel, category)
    save_state(state)
    return assets[key_]


def sprite_url(name, state, pid, dry):
    if name in SPRITE_LOCAL:
        return local_asset(SPRITE_LOCAL[name], state, pid, dry, "character")
    if name in SPRITE_MAIN:
        return MAIN_ASSETS[SPRITE_MAIN[name]]
    return None


def pick_bg(day_key, night_key, state, pid, dry):
    """白天版還沒畫（2026-09-06），有哪一張用哪一張。都沒有就留空讓推送報出來。"""
    for k in (day_key, night_key):
        u = bg_url(k, state, pid, dry)
        if u:
            return u, k
    return None, None


def who_of(seg_nodes):
    who = set()
    for n in seg_nodes:
        d = n["data"]
        if d.get("remote"):
            continue
        spk = [d.get("speaker")] + [l.get("speaker") for l in d.get("dialogueLines", [])]
        for s in spk:
            if not s or s in NOT_WHO:
                continue
            who.add(WHO_MAP.get(s, s))
    return sorted(who)


def label_of(section):
    # 「二・一Ａ 那台螢幕」→「那台螢幕」；「池一・信箱第三排（一張卡）」→「信箱第三排」
    s = re.sub(r"（.*?）", "", section)
    # 只剝「二、」「二之三・」「Ａ・」「池一・」「格一・」「甲・」這種序號，「一樓」的一不能剝
    num = r"(?:[一二三四五六七八九十]+(?:之[一二三四五六七八九十]+)?|[ＡＢＣＤ甲乙丙丁][一二三四五六七八九十]*|池[一二三四五六七八九十]+|格[一二三四五六七八九十]+|[0-9]+)"
    s = re.sub(r"^(?:" + num + r"[、・\.]\s*)+", "", s)
    return s.strip() or section


def infer_type(v):
    if isinstance(v, bool):
        return "boolean", v
    if isinstance(v, (int, float)):
        return "number", v
    return "string", v


def assemble(board, state, pid=None, dry=False, real_bid="inv"):
    nodes = json.loads(json.dumps(board["nodes"]))
    edges = json.loads(json.dumps(board["edges"]))
    rules = board["rules"]
    by_seg = {}
    for n in nodes:
        s = n["data"].get("segment")
        if s:
            by_seg.setdefault(s, []).append(n)
    rule_by_loc = {}
    cond_vars = set()
    for r in rules:
        who = [w for w in who_of(by_seg.get(r["segment"], [])) if w in POSSIBLE.get(r["dest"], set())]
        r2 = {"seg": r["segment"], "label": r.get("label") or label_of(r["section"]), "slots": r["slots"],
              "conds": r["conds"], "who": who}
        rule_by_loc.setdefault(r["dest"], []).append(r2)
        for c in r["conds"]:
            for cc in (c.get("any") or [c]):
                cond_vars.add((cc["variable"], cc["value"]))

    item_url = {k: local_asset(v, state, pid, dry, "prop") for k, v in ITEM_LOCAL.items()}
    ghost = MAIN_ASSETS["sprite-none"]
    # 每一段誰在台上：段落的 who（最多兩個），有立繪的才上
    stage_of = {}
    for seg, sn in by_seg.items():
        cast = [w for w in who_of(sn) if sprite_url(w, state, pid, dry)][:2]
        stage_of[seg] = cast
    # 誰從哪一張卡開始站上台：那個人第一次講話的那張。之前的卡（旁白鋪陳）他還沒出現。
    first_speak = {}
    for seg, sn in by_seg.items():
        for idx, n in enumerate(sn):
            d = n["data"]
            if d.get("type") != "dialogue" or d.get("remote"):
                continue
            for sp in [d.get("speaker")] + [l.get("speaker") for l in d.get("dialogueLines", [])]:
                w = WHO_MAP.get(sp, sp)
                if w and w not in NOT_WHO and (seg, w) not in first_speak:
                    first_speak[(seg, w)] = idx
    exit_at = {}
    for seg, sn in by_seg.items():
        for idx, n in enumerate(sn):
            for w in n["data"].get("exits", []):
                exit_at.setdefault((seg, WHO_MAP.get(w, w)), idx)
    seg_index = {n["id"]: i for sn in by_seg.values() for i, n in enumerate(sn)}
    seg_dest_of = {r["segment"]: r["dest"] for r in rules}
    seg_slots_of = {**board.get("seg_slots", {}), **{r["segment"]: r.get("slots") or [] for r in rules}}
    for n in nodes:
        d = n["data"]
        seg = d.get("segment")
        if d.get("type") != "dialogue" or not seg:
            continue
        idx = seg_index.get(n["id"], 0)
        cast = [] if d.get("remote") else [w for w in stage_of.get(seg, [])
                                          if first_speak.get((seg, w), 10**9) <= idx and idx <= exit_at.get((seg, w), 10**9)]
        d.pop("exits", None)
        hint = d.pop("castHint", None)
        if hint and sprite_url(WHO_MAP.get(hint, hint), state, pid, dry):
            cast = [WHO_MAP.get(hint, hint)]
        slots = ["center"] if len(cast) == 1 else ["left", "right"]
        actors, layers = [], []
        for w, slot in zip(cast, slots):
            u = sprite_url(w, state, pid, dry)
            actors.append({"id": f"actor-{w}-{slot}", "url": u, "name": w, "slot": slot,
                           "scale": SPRITE_SCALE.get(w, 1.0), "offsetX": 0, "offsetY": 0,
                           "enter": "fade", "loop": "breathe", "loopSpeed": 1, "loopStrength": 1})
            layers.append({"id": f"layer-{w}-{slot}", "url": u, "position": slot, "x": 0, "y": 0,
                           "scale": SPRITE_SCALE.get(w, 1.0), "opacity": 1, "flipX": False})
        scr = d.pop("screen", "")
        if d.get("remote") and d.get("speaker") == "格莉奇":
            loc = scr or seg_dest_of.get(seg, "")
            if loc in SCREEN_FOR:
                prop, sc, oy = SCREEN_FOR[loc]
                u = local_asset(f"art/screens/screen-{prop}.png", state, pid, dry, "prop")
                actors = [{"id": f"actor-screen-{prop}", "url": u, "name": "", "slot": "right", "scale": sc,
                           "offsetX": 0, "offsetY": oy, "enter": "fade", "loop": "none"}]
                layers = [{"id": f"layer-screen-{prop}", "url": u, "position": "right", "x": 0, "y": oy, "scale": sc, "opacity": 1, "flipX": False}]
        disp = {**DISPLAY, **(d.pop("display", None) or {})}
        if d.get("speaker") in disp:
            d["speaker"] = disp[d["speaker"]]
        for l in d.get("dialogueLines", []):
            if l.get("speaker") in disp:
                l["speaker"] = disp[l["speaker"]]
        for a_ in actors:
            a_["name"] = disp.get(a_["name"], a_["name"])
        # 台上沒人要放一個看不見的演員，不然上一張的人會留著（novelkit 實測）
        d["stage"] = {"actors": actors or [{"id": "actor-none", "url": ghost, "name": "", "slot": "center",
                                            "scale": 0.01, "offsetX": 0, "offsetY": 0, "enter": "fade", "loop": "none"}]}
        d["characterLayers"] = layers or [{"id": "layer-none", "url": ghost, "position": "center", "x": 0, "y": 0,
                                           "scale": 0.01, "opacity": 1, "flipX": False}]
    todo_js = (CARDS / "todo.js").read_text(encoding="utf-8")
    board_html = (CARDS / "board.html").read_text(encoding="utf-8").replace("/*@@TODO@@*/", todo_js)
    menu_html = (CARDS / "menu.html").read_text(encoding="utf-8")
    notes_html = (CARDS / "notes.html").read_text(encoding="utf-8").replace("/*@@TODO@@*/", todo_js)
    missing_bg = []
    board_id = None
    menus = []
    for n in nodes:
        d = n["data"]
        seg_of_card = d.pop("segment", None)     # 下面換場景那一段還要用，先留著
        if d.get("type") == "miniGame":
            # showButton:false 時播放器在 larch:complete 之後 240ms 自己接下一張（Preview bundle 讀出來的），
            # 不然玩家每過一個時段都要多按一次「套用結果並繼續」。
            d["miniGameFrame"] = {"showButton": False, "showTitle": False}
            if d["miniGameHtml"].endswith("board.html"):
                # 拍立得的照片：各地點日版／夜版背景
                photos = {}
                for loc, (dk, nk) in BG_MAP.items():
                    if loc.startswith("catgrass"):
                        continue
                    du, _ = pick_bg(dk, dk, state, pid, dry)
                    nu, _ = pick_bg(nk, nk, state, pid, dry)
                    eu, _ = pick_bg(f"bg-{loc}-evening", nk, state, pid, dry)
                    photos[loc] = {"day": du or nu or "", "evening": eu or nu or "", "night": nu or du or ""}
                d["miniGameHtml"] = (board_html.replace("/*@@PHOTOS@@*/{}", json.dumps(photos, ensure_ascii=False))
                                     .replace("/*@@DISPLAY@@*/{}", json.dumps(DISPLAY_UI, ensure_ascii=False)))
                board_id = n["id"]
            elif d["miniGameHtml"].endswith("menu.html"):
                loc = d["title"].split("：", 1)[1]
                rs = rule_by_loc.get(loc, [])
                html = (menu_html.replace("@@LOC_NAME@@", LOC_NAME.get(loc, loc)).replace("@@LOC@@", loc)
                        .replace("/*@@RULES@@*/[]", json.dumps(rs, ensure_ascii=False))
                        .replace("/*@@DISPLAY@@*/{}", json.dumps(DISPLAY_UI, ensure_ascii=False)))
                d["miniGameHtml"] = html
                vs = sorted({cc["variable"] for r in rs for c in r["conds"] for cc in (c.get("any") or [c])})
                d["miniGameReadVars"] = ["day", "slot", "here", "asked_斑比_鐵塔"] + vs
                d["miniGameWriteVars"] = ["pick"]
                menus.append(n["id"])
        elif d.get("type") == "dialogue" and d.get("sceneCode"):
            # 段落中途換場景的卡：帶背景（play 時進這張卡就換）。日夜先都用夜版，白天版由入口決定。
            code = d.pop("sceneCode")
            seg_dest = seg_dest_of.get(seg_of_card)
            if not seg_dest and seg_of_card and seg_of_card.startswith("greet-"):
                seg_dest = seg_of_card.split("-")[1]      # 招呼卡與材料行前奏：greet-<地點>-…，本來就在那個地點，不換背景
            if (code != seg_dest or seg_of_card in board.get("force_bg", [])) and code in BG_MAP:
                # 這一段幾點演，換的場景就用幾點的那張：全在晚上／深夜的段落用晚版／夜版，其他用日版
                day_key, night_key = BG_MAP[code]
                slots = seg_slots_of.get(seg_of_card) or []
                if slots and all(x >= 2 for x in slots):
                    keys = [f"bg-{code}-evening", night_key] if 2 in slots else [night_key, f"bg-{code}-evening"]
                else:
                    keys = [day_key, night_key]
                url, _ = pick_bg(keys[0], keys[1], state, pid, dry)
                if url:
                    d["background"] = url
        elif d.get("type") == "plugin" and d.get("pluginCardId") == "grant-item":
            if not d["pluginValues"].get("itemImage"):
                d["pluginValues"]["itemImage"] = item_url["tape"]
        elif d.get("type") == "scene":
            d["stage"] = {"actors": [{"id": "actor-none", "url": ghost, "name": "", "slot": "center",
                                      "scale": 0.01, "offsetX": 0, "offsetY": 0, "enter": "fade", "loop": "none"}]}
            day_key = d["background"].replace("@@", "")
            night_key = d.pop("backgroundNight", "").replace("@@", "")
            url, used = pick_bg(day_key, night_key, state, pid, dry)
            if not url:
                missing_bg.append(d["title"])
                d["background"] = ""
            else:
                d["background"] = url
                base = d["title"].replace("@n", "").replace("@e", "")
                d["title"] = LOC_NAME.get(base, base) + {"@n": "（夜）", "@e": "（晚）"}.get(d["title"][-2:], "")
            # 入口場景沒有字，停在那裡等點一下很怪；轉場完直接進選單。
            d["autoAdvance"] = {"enabled": True, "mode": "delay", "delayMs": 500}
        elif d.get("type") == "boardJump":
            if d.get("jumpBoardId") != CREDITS_BID:      # 結局跳謝幕那一塊版子的，id 已經是真的
                d["jumpBoardId"] = real_bid
    assert board_id, "board.json 裡沒有調查板"

    # 預設邊：板上什麼都沒選（休息）、選單什麼都沒挑，都回調查板。**要排在條件邊後面。**
    def add_node(nid, data, x, y):
        nodes.append({"id": nid, "type": "story", "position": {"x": x, "y": y}, "data": data})

    def add_edge(s, t, cond=None):
        e = {"id": f"e-x-{len(edges)}", "source": s, "target": t, "sourceHandle": "right", "animated": True}
        if cond:
            e["data"] = {"condition": {"kind": "variable", **cond}}
        edges.append(e)

    add_node("inv-rest", {"type": "boardJump", "title": "回調查板（休息）", "jumpBoardId": real_bid,
                          "jumpNodeId": board_id}, 0, 0)
    add_edge(board_id, "inv-rest")
    for m in menus:
        add_node(f"{m}-back", {"type": "boardJump", "title": "回調查板", "jumpBoardId": real_bid,
                               "jumpNodeId": board_id}, 0, 0)
        add_edge(m, f"{m}-back")
    # 翻開守則本：HUD 用道具 → open_notes=true → 這張 interrupt 插播 → 筆記卡 → 回原處
    add_node("inv-notes-int", {"type": "interrupt", "title": "翻開守則本", "text": "",
                               "interruptCondition": {"kind": "variable", "variable": "open_notes",
                                                      "op": "eq", "value": True},
                               "interruptOnce": False, "interruptExit": "return"}, 0, 0)
    # 筆記卡查的是 notes 逗號清單，可是故事卡只會把 see_x／clue_x 設成 true（對話卡設不了清單）。
    # 所以卡片端 has() 也認旗標，這裡把 notes.html 裡出現的每一個代號列進白名單並宣告成變數。
    note_codes = sorted(set(re.findall(r"'((?:see|clue|name)_[a-z_]+)'", notes_html)))
    add_node("inv-notes", {"type": "miniGame", "title": "調查筆記", "text": "",
                           "miniGameHtml": notes_html, "miniGamePresentation": "fullscreen",
                           "miniGameSkippable": True, "miniGameFrame": {"showButton": False, "showTitle": False},
                           "miniGameReadVars": ["notes", "notes_free", "met", "page1", "day", "night_visits", "hole_sightings",
                                                "laundry_night1", "trust_斑比", "strikes", "open_roof", "open_parts", "open_laundry",
                                                "open_studio", "met_諾亞", "met_材料行老闆"] + note_codes,
                           "miniGameWriteVars": ["notes_free", "page1", "page1_text", "page1_lead", "open_notes"]}, 0, 0)
    add_edge("inv-notes-int", "inv-notes")
    phone_src = (HERE.parent / "cards/phone.html").read_text(encoding="utf-8")
    posts, old_thread = phone_feed()
    def phone_card(mode, banner=None):
        """她的手機（design/調查篇-手機.md）。full＝從背包打開；banner＝收到訊息的橫幅，兩秒自己走。"""
        html = (phone_src.replace("/*@@MODE@@*/'full'", json.dumps(mode))
                .replace("/*@@BANNER@@*/null", json.dumps(banner, ensure_ascii=False))
                .replace("/*@@POSTS@@*/[]", json.dumps(posts, ensure_ascii=False))
                .replace("/*@@OLD@@*/[]", json.dumps(old_thread, ensure_ascii=False))
                .replace("/*@@AVATAR@@*/''", json.dumps(MAIN_ASSETS.get("avatar-glitch", ""))))
        d = {"type": "miniGame", "title": ("手機：" + banner["who"]) if banner else "她的手機", "text": "",
             "miniGameHtml": html, "miniGamePresentation": "fullscreen", "miniGameSkippable": True,
             "miniGameFrame": {"showButton": False, "showTitle": False},
             "miniGameReadVars": ["day", "slot", "phone_log", "phone_day_seen", "open_studio", "met_櫃檯"],
             "miniGameWriteVars": ["phone_log", "open_phone", "phone_day_seen"]}
        return d
    def phone_data(contact, messages):
        return phone_card("banner", {"who": contact, "text": messages})
    # 給卡片測試用的注入版（不進 repo）：tools/card_test.mjs 開這兩個檔
    (HERE.parent / "cards/.phone-test.html").write_text(phone_card("full")["miniGameHtml"], encoding="utf-8")
    (HERE.parent / "cards/.phone-banner-test.html").write_text(phone_data("斑比", "有空來工作室。稿子帶著。")["miniGameHtml"], encoding="utf-8")
    def _unused_plugin_receive(contact, messages):
        return {"type": "plugin", "title": f"手機：{contact}", "text": "",
                       "pluginId": "phone-chat", "pluginCardId": "receive", "pluginName": "格莉奇手機",
                       "pluginCardName": "收到訊息", "pluginIcon": "bell", "pluginColor": "#5b8def",
                       "pluginVersion": "0.3.4", "platforms": ["web"], "pluginAssets": [], "pluginHtml": phone_html,
                       "pluginValues": {"contactName": contact, "avatar": "", "messages": messages, "sound": "",
                                        "historyVar": "phone_log", "duration": 3, "dim": 0, "bgImage": "none", "bgColor": "none"},
                       "pluginReadVars": ["phone_log"], "pluginWriteVars": ["phone_log"],
                       "pluginSkippable": True, "pluginPresentation": "fullscreen"}
    def receive(nid, contact, messages, x, y):
        add_node(nid, phone_data(contact, messages), x, y)
    # 從背包打開手機：open_phone=true → 插播 → 手機卡 → 收起來回原處（跟守則本同一條路）
    add_node("inv-phone-int", {"type": "interrupt", "title": "打開手機", "text": "",
                               "interruptCondition": {"kind": "variable", "variable": "open_phone", "op": "eq", "value": True},
                               "interruptOnce": False, "interruptExit": "return"}, 0, 0)
    add_node("inv-phone", phone_card("full"), 0, 0)
    add_edge("inv-phone-int", "inv-phone")
    # 建置層放的手機卡（直播那三晚的橫幅，design/調查篇-直播.md）換成橫幅模式的手機卡
    for n in nodes:
        if n["data"].get("type") == "phone":
            d = n["data"]
            n["data"] = {**phone_data(d["contact"], d["msg"]), "segment": d.get("segment")}
    # 她的手機只收不回（背包與謎題 五）：直播開始那三晚由建置層接段落；斑比約你、公關窗口自動回覆
    phones = [("phone-bambi", "未儲存的號碼", "有空來工作室。稿子帶著。", [("open_studio", "eq", True)]),   # 她這時候還不知道名字
              ("phone-pr", "公關窗口", "您的來信已收到，我們將於三至五個工作天內回覆。", [("met_櫃檯", "gte", 1)])]
    for i, (nid, contact, msg, conds) in enumerate(phones):
        cond = {"kind": "variable", "variable": conds[0][0], "op": conds[0][1], "value": conds[0][2], "match": "all",
                "conditions": [{"variable": v, "op": o, "value": val} for v, o, val in conds]}
        add_node(f"{nid}-int", {"type": "interrupt", "title": f"手機響：{contact}", "text": "",
                                "interruptCondition": cond, "interruptOnce": True, "interruptExit": "return"}, 0, 1400 + i * 240)
        receive(nid, contact, msg, 400, 1400 + i * 240)
        add_edge(f"{nid}-int", nid)
    tapes = board.get("tapes", [])
    if tapes:
        add_node("inv-tape-int", {"type": "interrupt", "title": "播錄音", "text": "",
                                  # 兩個條件都要成立：有人用了一卷，而且不是在劇情的背包卡裡用的
                                  "interruptCondition": {"kind": "variable", "variable": "open_tape", "op": "eq", "value": True,
                                                         "match": "all",
                                                         "conditions": [{"variable": "open_tape", "op": "eq", "value": True},
                                                                        {"variable": "in_bag", "op": "eq", "value": False}]},
                                  "interruptOnce": False, "interruptExit": "return"}, 0, 0)
        for i, t in enumerate(tapes):
            nid = f"inv-tape-{t['id']}"
            # 先一張旁白讓玩家知道那是錄音機，再播那一句（講者與文字跟原場一模一樣，配音才會是同一份）
            add_node(f"{nid}-pre", {"type": "dialogue", "title": f"錄音機：{t['name']}", "text": "錄音機轉了一下。",
                                    "speaker": "旁白",
                                    "variableOps": [{"id": "op-tape", "variable": "open_tape", "kind": "set", "value": False}]},
                     400 + i * 320, 850)
            add_node(nid, {"type": "dialogue", "title": f"播：{t['name']}", "text": t["quote"],
                           "speaker": t["who"], "remote": True},   # 錄音機裡的聲音，不上立繪
                     400 + i * 320, 1000)
            add_edge("inv-tape-int", f"{nid}-pre", {"variable": "inventoryLastUsed", "op": "eq", "value": t["name"]})
            add_edge(f"{nid}-pre", nid)
        # 沒對到任何一卷（不該發生）：關掉旗標就回去
        add_node("inv-tape-none", {"type": "setVariable", "title": "（沒有這一卷）", "text": "",
                                   "variableOps": [{"id": "op-tape", "variable": "open_tape", "kind": "set", "value": False}]},
                 0, 900)
        add_edge("inv-tape-int", "inv-tape-none")

    # 變數
    vs = {v["name"]: v for v in board["variables"]}
    for name, val in sorted(cond_vars):
        if name in vs or name == "inventory":   # inventory 的預設值在下面那張表，hasItem 條件不可以把它蓋成空字串
            continue
        t, _ = infer_type(val)
        default = False if t == "boolean" else 0 if t == "number" else ""
        vs[name] = {"id": name, "name": name, "label": name, "type": t, "defaultValue": default}
    inv_default = json.loads(INVENTORY_DEFAULT)
    for it in inv_default:
        it["i"] = item_url.get(it["id"], "")
    for name, t, default, label in [
        ("inventory", "string", json.dumps(inv_default, ensure_ascii=False), "背包（守則本、手機、錄音）"),
        ("inventoryCount", "number", 2, "背包件數"),
        ("inventoryLastUsed", "string", "", "最後用的道具（名稱）"),
        ("open_notes", "boolean", False, "翻開守則本"),
        ("open_phone", "boolean", False, "從背包打開手機"),
        ("recorder_now", "boolean", False, "永遠是假：錄音機在對話裡按，不在包包裡按"),
        ("phone_day_seen", "number", 0, "她翻到第幾天的貼文（紅點用）"),
        ("rec_ok", "boolean", False, "錄音機清過毛了"),
        ("page1", "string", "", "第一頁：六個 ID 各對到誰"),
        ("page1_text", "string", "第一頁。她一個字都沒有寫。", "第一頁：收尾旁白唸的版本（沒看到牆的人唸預設）"),
        ("page1_lead", "string", "是空的。", "收尾翻到最後一頁那一句（有第一頁的人換成七條線）"),
        ("inventoryHudVisible", "boolean", True, "背包按鈕顯示與否；謝幕那一塊版子一開始關掉"),
        ("open_tape", "boolean", False, "播錄音（HUD 用了哪一卷）"),
        ("phone_log", "string", "[]", "手機收到的訊息（格莉奇手機插件）"),
        ("in_bag", "boolean", False, "劇情正在開背包（擋掉 HUD 重聽的插播）"),
    ]:
        vs.setdefault(name, {"id": name, "name": name, "label": label, "type": t, "defaultValue": default})

    for code in note_codes:
        vs.setdefault(code, {"id": code, "name": code, "label": code, "type": "boolean", "defaultValue": False})
    # 卡片會寫的、邊會判的（招呼那些 met_*／slot）也都要宣告，沒宣告的變數測試覆寫填不進去、編輯器也看不到
    written = {}
    for n in nodes:
        for o in n["data"].get("variableOps", []):
            written.setdefault(o["variable"], "number" if o["kind"] == "add" or isinstance(o["value"], int) and not isinstance(o["value"], bool) else "boolean" if isinstance(o["value"], bool) else "string")
    for e in edges:
        c = (e.get("data") or {}).get("condition")
        if c and c.get("variable") and c["variable"] not in written:
            written[c["variable"]] = "number" if isinstance(c["value"], int) and not isinstance(c["value"], bool) else "boolean" if isinstance(c["value"], bool) else "string"
    for name, t in written.items():
        if name in vs or name in ("inventory", "inventoryLastUsed", "pluginResult"):
            continue
        vs[name] = {"id": name, "name": name, "label": name, "type": t,
                    "defaultValue": 0 if t == "number" else False if t == "boolean" else ""}

    # ── 版面：人看得懂的白板 ────────────────────────────────────
    # 左邊一欄是系統卡（調查板、休息、筆記、錄音播放、收尾插播）。
    # 每個地點一個群組框：第一列日版入口、夜版入口、選單、回板；底下一段一列，卡片照走的順序從左到右，
    # 一列最多 WRAP 張，超過折到下一列。群組是 Larch 的「故事區段」卡（type group），子卡用 parentId。
    CW, CH = 360, 240            # 一格的間距（卡片本身約 280×140，帶立繪的到 200 高）
    WRAP = 8
    PAD = 40
    by_id = {n["id"]: n for n in nodes}
    out_edges = {}
    for e in edges:
        out_edges.setdefault(e["source"], []).append(e)

    def chain(start_id, stop=lambda nid: False):
        """從一張卡沿出邊走完整段（含分支），照發現順序回傳 id 清單"""
        seen, order, stack = set(), [], [start_id]
        while stack:
            nid = stack.pop(0)
            if nid in seen or nid not in by_id or stop(nid):
                continue
            seen.add(nid); order.append(nid)
            for e in out_edges.get(nid, []):
                stack.append(e["target"])
        return order

    placed = {}

    def put(nid, x, y, parent=None):
        n = by_id[nid]
        n["position"] = {"x": x, "y": y}
        if parent:
            n["parentId"] = parent
            n["extent"] = "parent"
        placed[nid] = True

    # 左欄
    col = 0
    put(board_id, 0, 0)
    put("inv-rest", 0, CH)
    put("inv-notes-int", 0, 2 * CH); put("inv-notes", CW, 2 * CH)
    y = 3 * CH
    if "inv-tape-int" in by_id:
        put("inv-tape-int", 0, y)
        tapes_ids = [n["id"] for n in nodes if n["id"].startswith("inv-tape-rec_")]
        for i, t in enumerate(tapes_ids):
            put(t, CW * (1 + i % 3), y + CH * (i // 3))
        put("inv-tape-none", 0, y + CH * ((len(tapes_ids) + 2) // 3))
        y += CH * ((len(tapes_ids) + 2) // 3 + 1)
    for n in nodes:
        if n["data"].get("type") == "interrupt" and n["id"] not in ("inv-notes-int", "inv-tape-int"):
            ids = chain(n["id"])
            for i, nid in enumerate(ids):
                put(nid, CW * (i % WRAP), y + CH * (i // WRAP))
            y += CH * ((len(ids) + WRAP - 1) // WRAP)

    # 群組：地點
    group_nodes = []
    entry_slots = []   # (該地點的入口場景 ids, 群組的 x)
    # 群組橫排、樞紐（調查板、插播）排在上面一列：從板到各地點入口的邊往下扇出，不穿過別的群組
    # （2026-09-08 試玩抓到：直排的時候那三十幾條邊斜穿整面白板，看起來像沒接到卡的斷線）
    gx, gy = 0, 0
    group_h = 0
    menu_loc = {}
    for m in menus:
        menu_loc[m] = by_id[m]["data"]["title"].split("：", 1)[1]
    for m in menus:
        loc = menu_loc[m]
        gid = f"grp-{loc}"
        rows = []            # 每列一串 id
        entries = [e["source"] for e in edges if e["target"] == m and e["source"] != board_id]
        rows.append([m, f"{m}-back"])          # 入口場景不進群組：排在群組正上方那一列，板到入口的邊就不會穿過別的群組
        entry_slots.append((entries, gx))
        for en in entries:
            ids = [x for x in chain(en, stop=lambda nid: nid == m or nid in placed) if x != en]
            for k in range(0, len(ids), WRAP):
                rows.append(ids[k:k + WRAP])
            for nid in ids:
                placed[nid] = True
        seg_entries = [e["target"] for e in out_edges.get(m, []) if e.get("data")]
        for se in seg_entries:
            ids = chain(se, stop=lambda nid: nid in placed or nid == m)
            for k in range(0, len(ids), WRAP):
                rows.append(ids[k:k + WRAP])
            for nid in ids:
                placed[nid] = True
        width = PAD * 2 + CW * max(len(r) for r in rows)
        height = PAD * 2 + CH * len(rows) + 40
        group_nodes.append({"id": gid, "type": "story", "position": {"x": gx, "y": gy},
                            "width": width, "height": height, "style": {"width": width, "height": height},
                            "data": {"type": "group", "title": LOC_NAME.get(loc, loc), "text": "",
                                     "groupColor": "#667257"}})
        for r_i, row in enumerate(rows):
            for c_i, nid in enumerate(row):
                if nid in by_id:
                    put(nid, PAD + CW * c_i, PAD + 40 + CH * r_i, parent=gid)
        gx += width + CW
        group_h = max(group_h, height)

    # 入口場景：各自群組正上方一列（日／晚／夜三張）
    for entries, x0 in entry_slots:
        for i, en in enumerate(entries):
            if en in by_id:
                by_id[en]["position"] = {"x": x0 + PAD + CW * i, "y": -CH * 2}
                by_id[en].pop("parentId", None); by_id[en].pop("extent", None)
                placed[en] = True
    # 樞紐與沒排到的（調查板、插播、共用閘、收尾、直播）：再上面一整列，橫著排；調查板放最左
    total_w = gx
    start_ids = [n["id"] for n in nodes if n["data"].get("start")]
    opening = set(chain(start_ids[0], stop=lambda nid: nid == board_id)) if start_ids else set()
    gids = {g["id"] for g in group_nodes}
    entry_ids = {en for entries, _ in entry_slots for en in entries}
    hub_ids = [n["id"] for n in nodes if not n.get("parentId") and n["id"] not in gids
               and n["id"] not in opening and n["id"] not in entry_ids]
    hub_ids.sort(key=lambda i: 0 if i == board_id else 1)
    cols = 24            # 樞紐列一排二十四張，往上疊
    for x_i, nid in enumerate(hub_ids):
        by_id[nid]["position"] = {"x": CW * (x_i % cols), "y": -CH * 5 - CH * (x_i // cols)}
        by_id[nid].pop("parentId", None); by_id[nid].pop("extent", None)
    # 開場那一段自成一列，放在群組下面（它從 start 卡開始，沒有 pick 邊）
    if start_ids:
        ids = chain(start_ids[0], stop=lambda nid: nid == board_id)
        for i, nid in enumerate(ids):
            by_id[nid]["position"] = {"x": CW * (i % cols), "y": group_h + CH * 2 + CH * (i // cols)}
            by_id[nid].pop("parentId", None); by_id[nid].pop("extent", None)
    nodes[:0] = group_nodes          # 群組要排在子卡前面

    stats = {"nodes": len(nodes), "edges": len(edges),
             "cond_edges": sum(1 for e in edges if e.get("data")),
             "variables": len(vs), "menus": len(menus), "missing_bg": missing_bg,
             "read_vars_max": max(len(n["data"].get("miniGameReadVars", [])) for n in nodes)}
    return nodes, edges, list(vs.values()), stats


def phone_feed():
    """design/調查篇-手機.md：貼文表（| 天 | 貼文 | 指向 | 留言 |）與「兩年前那一串」那段引言。"""
    text = (ROOT / "design/調查篇-手機.md").read_text(encoding="utf-8")
    posts = []
    for row in re.findall(r"^\| (\d+) \| (.+?) \| (.+?) \| (.+?) \|$", text, re.M):
        day, body, to, cms = row
        comments = []
        for c in cms.split("／"):
            c = c.strip()
            m = re.match(r"(@\S+?)(?:（(\d{2}:\d{2})）)?：(.*)", c)
            if m:
                comments.append({"id": m.group(1), "text": m.group(3).strip(), "tm": m.group(2) or ""})
            elif c.startswith("路人 ID"):
                who = c.split("：", 1)[1].strip() if "：" in c else ""
                comments.append({"id": "@路人", "text": who or "早安", "tm": ""})
        posts.append({"day": int(day), "text": body.strip(), "to": to.strip(), "comments": comments})
    old = []
    for m in re.finditer(r"^> \*\*(@?\S+?)\*\*(（帳號已刪除）)?：(.*)$", text, re.M):
        old.append({"id": m.group(1), "text": m.group(3).strip(), "deleted": bool(m.group(2)), "self": m.group(1) == "格莉奇"})
    assert posts and old, "手機設計文件的貼文表或兩年前那一串讀不到"
    return posts, old


CREDITS_BID = "board-credits"


def credits_board(state, pid, dry=False):
    """謝幕那一塊版子（design/調查篇-謝幕.md）：放映廳 → 旁白「完」 → 片尾字卷 → 謝幕 → 格莉奇那句。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("inv_parse", HERE / "parse.py")
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    res = P.parse_file(ROOT / "design/調查篇-謝幕.md")
    cards = res[0] if isinstance(res, tuple) else res
    cards = [c for c in cards if c["lines"]]
    assert len(cards) == 2, f"謝幕檔要剛好兩張卡（旁白、格莉奇），現在 {len(cards)}"
    ghost = MAIN_ASSETS["sprite-none"]
    stage0 = {"actors": [{"id": "actor-none", "url": ghost, "name": "", "slot": "center",
                          "scale": 0.01, "offsetX": 0, "offsetY": 0, "enter": "fade", "loop": "none"}]}
    def txt(c):
        return "\n".join(l["text"] for l in c["lines"] if not l.get("direction"))
    html = (HERE.parent / "cards/credits.html").read_text(encoding="utf-8")
    sprites = {w: sprite_url(w, state, pid, dry) for w in list(SPRITE_LOCAL) + list(SPRITE_MAIN)}
    sprites["格莉奇"] = MAIN_ASSETS["sprite-glitch"]; sprites["黑洞先生"] = MAIN_ASSETS["sprite-blackhole"]
    html = (html.replace("/*@@SPRITES@@*/{}", json.dumps({k: v for k, v in sprites.items() if v}, ensure_ascii=False))
                .replace("/*@@LOC_NAME@@*/{}", json.dumps(LOC_NAME, ensure_ascii=False))
                .replace("/*@@DISPLAY@@*/{}", json.dumps(DISPLAY, ensure_ascii=False))
                .replace("/*@@HALL@@*/''", MAIN_ASSETS["bg-credits-cinema"]))   # 在 style 屬性裡，不能帶雙引號
    met_vars = [f"met_{w}" for w in ("管理員", "諾亞", "斑比", "鐵塔", "0x", "貓草", "店員", "材料行老闆", "櫃檯", "保全")]
    seq = [
        # 片尾不要有背包按鈕：背包插件的 HUD 看 inventoryHudVisible（show-hud／hide-hud 兩張卡寫的就是它）
        ("credits-hud", {"type": "setVariable", "title": "（收起背包按鈕）", "text": "", "start": True,
                         "variableOps": [{"id": "op-hud", "variable": "inventoryHudVisible", "kind": "set", "value": False}]}),
        ("credits-hall", {"type": "scene", "title": "放映廳", "text": "燈暗下來。", "background": MAIN_ASSETS["bg-credits-cinema"],
                          "transition": "fade", "transitionMs": 900, "stage": stage0}),
        ("credits-end", {"type": "dialogue", "title": "完", "text": txt(cards[0]), "speaker": "旁白", "stage": stage0}),
        ("credits-roll", {"type": "miniGame", "title": "片尾字卷", "text": "", "miniGameHtml": html,
                          "miniGamePresentation": "fullscreen", "miniGameSkippable": True,
                          "miniGameFrame": {"showButton": False, "showTitle": False},
                          "miniGameReadVars": ["page1_text", "met", "visited", "day", "night_visits", "hole_sightings", "names_seen"] + met_vars,
                          "miniGameWriteVars": []}),
        ("credits-bow", {"type": "scene", "title": "謝幕", "text": "燈亮了。",
                         "background": bg_url("bg-curtain-call-inv", state, pid, dry) or MAIN_ASSETS["bg-curtain-call"],   # 十二人合照（正文七個加調查篇五個）
                         "transition": "fade", "transitionMs": 700, "stage": stage0}),
        ("credits-line", {"type": "dialogue", "title": "格莉奇：謝謝你看到這裡", "text": txt(cards[1]), "speaker": "格莉奇", "stage": stage0}),
    ]
    nodes = [{"id": nid, "type": "story", "position": {"x": 80 + i * 420, "y": 120}, "data": d} for i, (nid, d) in enumerate(seq)]
    edges = [{"id": f"credits-e{i}", "source": seq[i][0], "target": seq[i + 1][0]} for i in range(len(seq) - 1)]
    return nodes, edges


def settings_patch(settings, bag_image=""):
    settings = dict(settings or {})
    plugins = dict(settings.get("plugins") or {})
    # HUD 的位置與欄位照官方範例「背包功能使用教學」，顏色換成調查板那一套（夜色街區）
    plugins["larch-inventory"] = {"enabled": True, "settings": {
        **(plugins.get("larch-inventory", {}).get("settings") or {}),
        "hudEnabled": True, "bagVar": "inventory",
        "hudPosition": "right", "buttonPositionMode": "custom", "buttonX": 89.3, "buttonY": 10.4,
        "buttonPivot": "top-left", "buttonStyle": "image", "buttonSize": 76, "buttonShowCount": True,
        "buttonImage": bag_image, "buttonLabel": "",
        "slotCount": 12, "radius": 8,
        "surfaceColor": "#141a30", "surfaceOpacity": 0.94, "itemColor": "#1f2747",
        "textColor": "#ece9f4", "accentColor": "#7fd6e8",
        "motionStyle": "gentle", "shadowStyle": "soft"}}
    plugins.pop("phone-chat", None)      # 通知改由自己的手機卡做（design/調查篇-手機.md）
    settings["plugins"] = plugins
    settings.setdefault("stageFit", "auto")
    settings.setdefault("keepActorsInFrame", False)
    settings.setdefault("titleScreenEnabled", True)
    settings.setdefault("resolution", {"width": 1920, "height": 1080})
    settings["cgGalleryEnabled"] = False   # 沒有 CG，標題那顆「CG 收藏」要收掉（不然它會把 12 張背景當畫廊）
    return settings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--set", action="append", default=[],
                    help="測試用：覆寫變數預設值，例 --set rec_ok=true。驗完要再推一次正常版")
    a = ap.parse_args()
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    state = load_state()

    if a.dry:
        nodes, edges, vs, st = assemble(board, state, dry=True)
        print(json.dumps(st, ensure_ascii=False, indent=1))
        out = HERE / "out" / "payload.json"
        out.write_text(json.dumps({"nodes": nodes, "edges": edges, "variables": vs}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"payload 寫在 {out}（不連線）")
        return

    # 1. 專案
    if "projectId" not in state:
        r = api("POST", "/projects", {"name": NAME, "description": DESC})
        pid = (r.get("project") or r).get("id") or r.get("id")
        assert pid, f"拿不到專案 id：{json.dumps(r, ensure_ascii=False)[:300]}"
        state["projectId"] = pid
        save_state(state)
        print("建了新專案", pid)
    pid = state["projectId"]

    # 2. 版子 id（預設版子）
    if "boardId" not in state:
        bl = api("GET", f"/projects/{pid}/boards")
        bl = bl.get("boards") or bl
        assert isinstance(bl, list) and bl, f"找不到預設版子：{bl}"
        state["boardId"] = bl[0]["id"]
        save_state(state)
    bid = state["boardId"]

    # 3. 組 payload（順便上傳缺的背景）
    nodes, edges, vs, st = assemble(board, state, pid=pid, real_bid=bid)
    for kv in a.set:
        k, v = kv.split("=", 1)
        v = True if v == "true" else False if v == "false" else int(v) if re.fullmatch(r"-?\d+", v) else v
        for var in vs:
            if var["name"] == k:
                var["defaultValue"] = v
                print(f"★ 測試覆寫 {k} = {v!r}（驗完要重推正常版）")
    print("payload：", json.dumps(st, ensure_ascii=False))

    # 4. 專案設定與變數（整包 PUT 會清版子，所以在推版子之前做）
    proj = api("GET", f"/projects/{pid}")
    proj = proj.get("project") or proj
    proj["name"], proj["description"] = NAME, DESC
    bag_image = local_asset("art/items/bag.png", state, pid, False, "prop") if (ROOT / "art/items/bag.png").exists() else ""
    proj["settings"] = settings_patch(proj.get("settings"), bag_image)
    proj["variables"] = vs
    api("PUT", f"/projects/{pid}", {"project": proj})
    print("PUT 專案設定與變數：ok")

    # 5. 版子
    api("PUT", f"/projects/{pid}/boards/{bid}",
        {"name": "調查篇", "nodes": nodes, "edges": edges, "summary": "push.py 從 board.json 推上來"})
    back = api("GET", f"/projects/{pid}/boards/{bid}")
    back = back.get("board") or back
    got_nodes, got_edges = len(back.get("nodes", [])), len(back.get("edges", []))
    got_cond = sum(1 for e in back.get("edges", []) if e.get("data", {}).get("condition"))
    print(f"回讀：卡片 {got_nodes}/{len(nodes)}　邊 {got_edges}/{len(edges)}　帶條件的邊 {got_cond}/{st['cond_edges']}")
    ok = got_nodes == len(nodes) and got_edges == len(edges) and got_cond == st["cond_edges"]
    print("比對", "一致" if ok else "★ 不一致，去查")

    # 5b. 謝幕那一塊版子（結局跳過來；沒有它 boardJump 會跳到不存在的版子）
    cn, ce = credits_board(state, pid)
    api("PUT", f"/projects/{pid}/boards/{CREDITS_BID}",
        {"name": "謝幕", "kind": "story", "mode": "story", "nodes": cn, "edges": ce, "summary": "design/調查篇-謝幕.md"})
    cb = api("GET", f"/projects/{pid}/boards/{CREDITS_BID}")
    cb = cb.get("board") or cb
    print(f"謝幕版子：卡片 {len(cb.get('nodes', []))}/{len(cn)}　邊 {len(cb.get('edges', []))}/{len(ce)}")

    # 6. 預覽
    pv = api("GET", f"/projects/{pid}/preview?boardId={bid}&hours=168")
    # 預覽連結免登入就能玩，是私人的，不進 repo（.gitignore 有它）；state.json 只留 id 與素材網址
    (HERE / "preview.json").write_text(json.dumps(pv, ensure_ascii=False, indent=1), encoding="utf-8")
    print("預覽：", pv.get("playUrl"))
    print("白板：", pv.get("boardUrl"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
