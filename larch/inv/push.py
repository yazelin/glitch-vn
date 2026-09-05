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

API = "https://larch.ink/api/agent"
KEY_PATH = pathlib.Path.home() / ".config/larch/key"

NAME = "格莉奇與黑洞先生・調查篇"
DESC = ("你在收集不該存在的東西。她說她只有 4KB，全世界當成哏，只有你當真。\n"
        "十一天，八個地點，一本買來的守則本。你要證明的事，每一個認識她的人都在用同一種方式對待。")

LOC_NAME = {"lobby": "一樓", "roof": "頂樓收音機店", "street": "車站前那條街", "studio": "斑比工作室",
            "booth": "錄音間門口", "tower14": "十四樓大廳", "store": "便利商店", "parts": "材料行",
            "busstop": "公車站", "metro": "捷運出口", "laundry": "自助洗衣店", "figure": "手辦店"}
# 卡片講者 → 調查板 here 裡用的名字。玩家、旁白、格莉奇（只在螢幕上）不算「誰在」。
WHO_MAP = {"材料行老闆": "老闆", "住戶": "路人", "路人乙": "路人", "高中生": "路人", "阿姨": "路人",
           "送貨的": "路人", "發傳單的": "路人", "上班族": "路人"}
NOT_WHO = {"玩家", "旁白", "格莉奇"}

INVENTORY_DEFAULT = json.dumps([
    {"id": "rulebook", "n": "守則本", "d": "一千二。第一頁還是空的。", "c": False,
     "e": "set", "v": "open_notes", "x": True},
    {"id": "phone", "n": "手機", "d": "沒有人會打來。", "c": False,
     "useConditionVariable": "phone_ringing", "useConditionValue": True,
     "useConditionMessage": "沒有人會打來。"},
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
        r2 = {"seg": r["segment"], "label": r.get("label") or label_of(r["section"]), "slots": r["slots"],
              "conds": r["conds"], "who": who_of(by_seg.get(r["segment"], []))}
        rule_by_loc.setdefault(r["dest"], []).append(r2)
        for c in r["conds"]:
            cond_vars.add((c["variable"], c["value"]))

    board_html = (CARDS / "board.html").read_text(encoding="utf-8")
    menu_html = (CARDS / "menu.html").read_text(encoding="utf-8")
    notes_html = (CARDS / "notes.html").read_text(encoding="utf-8")
    missing_bg = []
    board_id = None
    menus = []
    for n in nodes:
        d = n["data"]
        d.pop("segment", None)
        if d.get("type") == "miniGame":
            # showButton:false 時播放器在 larch:complete 之後 240ms 自己接下一張（Preview bundle 讀出來的），
            # 不然玩家每過一個時段都要多按一次「套用結果並繼續」。
            d["miniGameFrame"] = {"showButton": False, "showTitle": False}
            if d["miniGameHtml"].endswith("board.html"):
                d["miniGameHtml"] = board_html
                board_id = n["id"]
            elif d["miniGameHtml"].endswith("menu.html"):
                loc = d["title"].split("：", 1)[1]
                rs = rule_by_loc.get(loc, [])
                html = (menu_html.replace("@@LOC_NAME@@", LOC_NAME.get(loc, loc)).replace("@@LOC@@", loc)
                        .replace("/*@@RULES@@*/[]", json.dumps(rs, ensure_ascii=False)))
                d["miniGameHtml"] = html
                vs = sorted({c["variable"] for r in rs for c in r["conds"]})
                d["miniGameReadVars"] = ["day", "slot", "here"] + vs
                d["miniGameWriteVars"] = ["pick"]
                menus.append(n["id"])
        elif d.get("type") == "scene":
            day_key = d["background"].replace("@@", "")
            night_key = d.pop("backgroundNight", "").replace("@@", "")
            url, used = pick_bg(day_key, night_key, state, pid, dry)
            if not url:
                missing_bg.append(d["title"])
                d["background"] = ""
            else:
                d["background"] = url
                d["title"] = LOC_NAME.get(d["title"], d["title"])
            # 入口場景沒有字，停在那裡等點一下很怪；轉場完直接進選單。
            d["autoAdvance"] = {"enabled": True, "mode": "delay", "delayMs": 500}
        elif d.get("type") == "boardJump":
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
                           "miniGameReadVars": ["notes", "notes_free", "met", "page1"] + note_codes,
                           "miniGameWriteVars": ["notes_free", "page1", "open_notes"]}, 0, 0)
    add_edge("inv-notes-int", "inv-notes")
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
            add_node(nid, {"type": "dialogue", "title": f"播：{t['name']}", "text": t["quote"],
                           "speaker": t["who"], "remote": True,
                           "variableOps": [{"id": "op-tape", "variable": "open_tape", "kind": "set", "value": False}]},
                     400 + i * 320, 900)
            add_edge("inv-tape-int", nid, {"variable": "inventoryLastUsed", "op": "eq", "value": t["name"]})
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
    for name, t, default, label in [
        ("inventory", "string", INVENTORY_DEFAULT, "背包（守則本、手機、錄音）"),
        ("inventoryCount", "number", 2, "背包件數"),
        ("inventoryLastUsed", "string", "", "最後用的道具（名稱）"),
        ("open_notes", "boolean", False, "翻開守則本"),
        ("phone_ringing", "boolean", False, "永遠不會響"),
        ("rec_ok", "boolean", False, "錄音機清過毛了"),
        ("page1", "string", "", "第一頁：六個 ID 各對到誰"),
        ("open_tape", "boolean", False, "播錄音（HUD 用了哪一卷）"),
        ("in_bag", "boolean", False, "劇情正在開背包（擋掉 HUD 重聽的插播）"),
    ]:
        vs.setdefault(name, {"id": name, "name": name, "label": label, "type": t, "defaultValue": default})

    for code in note_codes:
        vs.setdefault(code, {"id": code, "name": code, "label": code, "type": "boolean", "defaultValue": False})

    # 版面：板與地點在左邊兩欄；每一段一列
    pos = {board_id: (0, 0)}
    y = 0
    for i, m in enumerate(menus):
        pos[m] = (800, i * 220)
    entries = [e["source"] for e in edges if e["target"] in menus and e["source"] != board_id]
    for i, en in enumerate(entries):
        pos[en] = (400, i * 220)
    row = 0
    for seg, sn in by_seg.items():
        for j, n in enumerate(sn):
            pos[n["id"]] = (1400 + j * 320, 3200 + row * 200)
        row += 1
    for n in nodes:
        if n["id"] in pos:
            n["position"] = {"x": pos[n["id"]][0], "y": pos[n["id"]][1]}
        elif n["id"].endswith("-back"):
            src = n["id"][:-5]
            n["position"] = {"x": 1100, "y": pos.get(src, (0, 0))[1]}
        elif n["data"].get("type") == "boardJump":
            # 每一段的回板卡接在該段最後一張後面
            prev = next((e["source"] for e in edges if e["target"] == n["id"]), None)
            px, py = pos.get(prev, (1400, 3200))
            n["position"] = {"x": px + 320, "y": py}
    for n in nodes:
        n.setdefault("position", {"x": 0, "y": 0})
    nodes[[n["id"] for n in nodes].index("inv-rest")]["position"] = {"x": 0, "y": 300}
    nodes[[n["id"] for n in nodes].index("inv-notes-int")]["position"] = {"x": 0, "y": 600}
    nodes[[n["id"] for n in nodes].index("inv-notes")]["position"] = {"x": 400, "y": 600}

    stats = {"nodes": len(nodes), "edges": len(edges),
             "cond_edges": sum(1 for e in edges if e.get("data")),
             "variables": len(vs), "menus": len(menus), "missing_bg": missing_bg,
             "read_vars_max": max(len(n["data"].get("miniGameReadVars", [])) for n in nodes)}
    return nodes, edges, list(vs.values()), stats


def settings_patch(settings):
    settings = dict(settings or {})
    plugins = dict(settings.get("plugins") or {})
    plugins["larch-inventory"] = {"enabled": True, "settings": {**(plugins.get("larch-inventory", {}).get("settings") or {}),
                                                              "hudEnabled": True, "bagVar": "inventory"}}
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
    proj["settings"] = settings_patch(proj.get("settings"))
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

    # 6. 預覽
    pv = api("GET", f"/projects/{pid}/preview?boardId={bid}&hours=168")
    # 預覽連結免登入就能玩，是私人的，不進 repo（.gitignore 有它）；state.json 只留 id 與素材網址
    (HERE / "preview.json").write_text(json.dumps(pv, ensure_ascii=False, indent=1), encoding="utf-8")
    print("預覽：", pv.get("playUrl"))
    print("白板：", pv.get("boardUrl"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
