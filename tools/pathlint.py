#!/usr/bin/env python3
"""板上路徑的靜態檢查。跑：python3 tools/pathlint.py

抓三類實際踩過的路徑 bug：
 一、同一個地點同一個時段有兩格標籤一樣，而且條件可以同時成立
     → 玩家會點到錯的那一張（工作室問 0x 那格中過，白天的短版蓋掉深夜版）
 二、條件比對的值沒有任何一張卡設得到 → 那一格永遠開不了
 三、條件讀的變數沒有任何地方會寫 → 通常是打錯字
 四、兩條邊撞同一個 id → react-flow 拿 id 當 key，撞號的只會畫一條，多的那些線直接消失
     （2026-09-10 中過：build.py 有五處會過濾 b.edges，用 len(edges)+1 當號碼就會重號，
       29 條選項線被吃掉，白板上選擇卡旁邊一條線都沒有）
 五、選擇卡的選項數跟它接出去的 choice-N 邊數對不上
 六、設計稿裡的舞台指示（斜體那幾行）有沒有真的進到卡上
 七、有沒有講者留空字串的台詞行
     （空字串會沿用上一個講者的名牌，動作句會掛成上一個角色在講話，2026-09-10 實測）
     （2026-09-10 中過：card_node 把 direction 整行過濾掉，204 行動作全部沒演，
       「你也有。」前面少了她把本子拿出來並排的那一下）

 八、板上有沒有名字長得不像變數的 variableOps
     （2026-09-11 中過：設計稿把箭頭寫進反引號裡「`trust_斑比 ← 3`」，
       解析器把整串當變數名，那張卡就沒把 trust_斑比 設成 3，斑比五之一那條路默默失效）
 九、選項條件（`choiceConditions`）壞掉的三種樣子
     ・陣列長度跟 `choices` 對不上 → 平台按索引取，錯位等於把條件掛到別格去
     ・一張選擇卡在劇情模式下每一格都被擋掉 → 那張卡走不出去（劇情模式的死路）
     ・劇情模式的軌道有對不到卡的步（`walk.miss`）→ 那一步沒有人擋，鐵路在那裡斷掉
     ・軌道字串（`walk` 變數的預設值）少了選單那一格的標籤 → 擋得住「去哪裡」，
       擋不住「選哪一格」，玩家走得完可是走不出完美結局（2026-09-11 退回過一次）
     （選項吃條件是 2026-09-11 實測的，見 design/調查篇.md 七。以前以為不吃，
       所以走廊那一場把劇情複製了一份繞過去）
 十、台詞裡寫死的天數跟實際流程對不上
     （2026-09-09 把全篇從十二天拉到十四天，板上改了，散在別處的數字沒有全部跟上；
       「第Ｎ天收尾」的條件是 day eq N+1，那是刻意的差一——日記第 Ｎ 天寫，第 Ｎ+1 天才讀到）
 十一、板上有 @@bg- 代號對不到任何圖檔
     （對不到的話 push.py 會把 background 寫成空字串，而卡數／邊數的回讀完全一致，
       看起來像推成功了。2026-09-12 中過：白天那批重畫成 .png，push.py 寫死找 .jpg，
       線上 22 張場景卡沒有背景）
可達性不在這裡，那是 tools/sim.py 的事。

**十一項每一項都有負控制**，在 `tools/pathlint_selftest.py`：它把故障注進板子的副本，
跑這一支，確認該項會紅、還原後會綠。改這裡的規則要順手改那一支，不然那一項等於沒在驗。
`PATHLINT_BOARD` 可以指定要檢查哪一份板子（自我測試用的）。
"""
import json, os, re, sys, collections, pathlib, itertools

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 板子的路徑可以換掉，tools/pathlint_selftest.py 靠這個把注入故障的副本餵進來。
BOARD = pathlib.Path(os.environ.get("PATHLINT_BOARD") or ROOT / "larch/inv/out/board.json")
b = json.loads(BOARD.read_text(encoding="utf-8"))

sets, adds, card_writes = collections.defaultdict(set), collections.defaultdict(set), set()
for n in b["nodes"]:
    s = json.dumps(n, ensure_ascii=False)
    card_writes.update(n["data"].get("miniGameWriteVars") or [])
    for m in re.finditer(r'"variable": "([^"]+)", "kind": "(set|add)", "value": ([^,}]+)', s):
        (sets if m.group(2) == "set" else adds)[m.group(1)].add(m.group(3).strip())
defaults = {v["name"]: v.get("defaultValue") for v in b["variables"]}
FREE = {"day", "slot", "inventory", "here", "met", "visited", "tries", "任一"}
bad = []


def conflict(a, c):
    """兩組條件不可能同時成立？只看同一個變數上的明顯矛盾。"""
    for x in a:
        for y in c:
            if x["variable"] != y["variable"]:
                continue
            xv, yv, xo, yo = x["value"], y["value"], x["op"], y["op"]
            if xo == yo == "eq" and xv != yv:
                return True
            if {xo, yo} == {"eq", "gte"} and isinstance(xv, int) and isinstance(yv, int):
                e, g = (xv, yv) if xo == "eq" else (yv, xv)
                if e < g:
                    return True
            if {xo, yo} == {"eq", "lte"} and isinstance(xv, int) and isinstance(yv, int):
                e, l = (xv, yv) if xo == "eq" else (yv, xv)
                if e > l:
                    return True
    return False


seen = collections.defaultdict(list)
for r in b["rules"]:
    if r.get("label"):
        for s in r["slots"]:
            seen[(r["dest"], s, r["label"])].append(r)
for (dest, slot, label), rs in sorted(seen.items()):
    for x, y in itertools.combinations(rs, 2):
        if not conflict(x["conds"], y["conds"]):
            bad.append(f"重複標籤　{dest}／時段{slot}　「{label}」　"
                       f"→ {x['section'][:22]} ＋ {y['section'][:22]}")
            break

NUMOPS = {"gte": ">=", "lte": "<=", "gt": ">", "lt": "<"}
for r in b["rules"]:
    who = f"{r['dest']}　「{r.get('label') or r['section'][:20]}」"
    for c in r["conds"]:
        var, op, val = c["variable"], c["op"], c["value"]
        if var in FREE:
            continue
        if var not in sets and var not in adds and var not in card_writes:
            bad.append(f"沒有人寫　{who}　讀 {var}")
            continue
        if var in card_writes or var in adds:
            continue                      # 板上加的次數，靜態算不出上限
        vals = {v.strip('"').lower() for v in sets[var]} | {str(defaults.get(var, False)).lower()}
        if op == "eq" and str(val).lower() not in vals:
            bad.append(f"值對不到　{who}　{var} == {val}，只設得到 {sorted(vals)}")
        if op in NUMOPS and isinstance(val, int):
            nums = [int(v) for v in sets[var] if re.fullmatch(r"-?\d+", v)]
            if nums and ((op in ("gte", "gt") and val > max(nums))
                         or (op in ("lte", "lt") and val < min(nums))):
                bad.append(f"值到不了　{who}　{var} {NUMOPS[op]} {val}，最高只到 {max(nums)}")

# 四、撞 id 的邊
seen = collections.defaultdict(list)
for e in b["edges"]:
    seen[e["id"]].append(e)
for eid, es in seen.items():
    if len(es) > 1:
        bad.append(f"邊撞 id　{eid} 有 {len(es)} 條：" +
                   "、".join(f"{e['source']}→{e['target']}" for e in es[:4]))

# 五、選擇卡的選項數 vs 接出去的 choice-N 邊數
out_ch = collections.Counter()
for e in b["edges"]:
    if str(e.get("sourceHandle", "")).startswith("choice-"):
        out_ch[e["source"]] += 1
for n in b["nodes"]:
    d = n.get("data") or {}
    if d.get("type") != "choice":
        continue
    want, got = len(d.get("choices") or []), out_ch[n["id"]]
    if want != got:
        bad.append(f"選項沒接好　{n['id']}　{d.get('title')}：{want} 個選項只有 {got} 條線")

# 六、舞台指示有沒有進到卡上
sys.path.insert(0, str(ROOT / "larch/inv"))
import parse as _P                                                  # noqa: E402
_blob = json.dumps(b["nodes"], ensure_ascii=False)
_dirs = 0
for _d in _P.DOCS:
    for _c, _ in [(x, None) for x in _P.parse_file(_d)[0]]:
        for _l in _c["lines"]:
            if not _l.get("direction"):
                continue
            _dirs += 1
            _t = re.sub(r"^（旁白・描述動作）", "", _l["text"])[:14]
            if _t not in _blob:
                bad.append(f"指示沒進卡　{_c['file']}　{_l['text'][:30]}")

# 七、講者留空的行
for _n in b["nodes"]:
    for _l in ((_n.get("data") or {}).get("dialogueLines") or []):
        if not _l.get("speaker"):
            bad.append(f"講者留空　{_n['id']}　{str(_l.get('text'))[:26]}")

# 八、變數名長得對不對
_VARNAME = re.compile(r"[a-z][A-Za-z0-9_\u4e00-\u9fff]*")
for _n in b["nodes"]:
    for _o in ((_n.get("data") or {}).get("variableOps") or []):
        _v = _o.get("variable") or ""
        if not _VARNAME.fullmatch(_v):
            bad.append(f"變數名怪　{_n['id']}　「{_v}」"
                       f"（設計稿多半是把箭頭或註解寫進反引號裡了）")

# 九、選項條件
def _blocks_story(cond):
    """這一格在劇情模式下按不按得下去：條件裡掛了 mode（== free）就是按不下去。"""
    for c in (cond or {}).get("conditions") or [cond or {}]:
        if c.get("variable") == "mode":
            return True
    return False


for _n in b["nodes"]:
    _d = _n.get("data") or {}
    if _d.get("type") != "choice":
        continue
    _ch, _cc = _d.get("choices") or [], _d.get("choiceConditions")
    if _cc is None:
        bad.append(f"選項條件缺陣列　{_n['id']}　{_d.get('title')}：{len(_ch)} 個選項沒有 choiceConditions")
        continue
    if len(_cc) != len(_ch):
        bad.append(f"選項條件對不上　{_n['id']}　{_d.get('title')}：{len(_ch)} 個選項配 {len(_cc)} 格條件")
        continue
    if _ch and all(_blocks_story(c) for c in _cc):
        bad.append(f"劇情模式走不出去　{_n['id']}　{_d.get('title')}：每一格都掛了 mode")
for _m in (b.get("walk") or {}).get("miss") or []:
    bad.append(f"軌道斷了　第 {_m.get('day')} 天 時段{_m.get('slot')}　{_m.get('why')}　"
               + "｜".join(_m.get("labels") or [])[:40])
# 軌道字串（walk 變數的預設值）要連選單那一格的標籤一起帶。少了它，劇情模式擋得住
# 「去哪裡」擋不住「選哪一格」，玩家走得完可是走不出完美結局（2026-09-11 退回過一次）。
_walkvar = next((v.get("defaultValue") for v in b["variables"] if v["name"] == "walk"), None)
if _walkvar is None:
    bad.append("軌道沒有 walk 變數")
else:
    _steps = {}
    for _s in str(_walkvar).split(";"):
        _p = _s.split("|")
        if len(_p) >= 4:
            _steps[(_p[0], _p[1])] = _p[3]
    for _s in (b.get("walk") or {}).get("board") or []:
        if _s.get("label") and _steps.get((str(_s.get("day")), str(_s.get("slot")))) != _s["label"]:
            bad.append(f"軌道少了選單那一格　第 {_s['day']} 天 時段{_s['slot']}　「{_s['label']}」")

# ── 十、台詞裡寫死的天數要跟實際流程一致 ──────────────────────────
# 2026-09-12 加。2026-09-09 把全篇從十二天拉到十四天的時候，板上的卡跟著改了，
# 可是散在別處的數字沒有全部跟上（市集簡介還寫「十一天」）。這一項只管板子，
# 板子以外的（push.py 的 DESC、板子插件的註解、設計稿）驗不到，那些要靠人看。
#
# 規矩有三條，都是從板子自己讀出來的，不寫死任何一個數字：
#   ・「第Ｎ天，收尾」那張插播的 `day gte X` 就是全篇長度，標題的 Ｎ 要等於 X
#   ・「第Ｎ天收尾」是**第 Ｎ 天寫的日記，第 Ｎ+1 天一開板才讀到**，所以條件是 day eq N+1
#     （這個差一不是 bug，是 build.py 第 602 行寫死的 n_day + 1，別「修」掉它）
#   ・「第Ｎ天直播」是當天晚上的插播，條件是 day eq N
# 然後拿全篇長度去對台詞：「這Ｎ天」要等於全篇長度，最後那則收尾的日期要等於全篇長度減一。
_CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,
       "十一":11,"十二":12,"十三":13,"十四":14,"十五":15,"十六":16}

def _day_of(cond):
    """插播條件裡的 day：回傳 (op, 值)。條件可能是單條，也可能包一層 conditions。"""
    for c in (cond.get("conditions") or [cond]):
        if c.get("variable") == "day":
            return c.get("op"), c.get("value")
    return None, None

_last_day = _fin = None
_wrap = {}          # 第Ｎ天收尾 → 條件那一天
for _n in b["nodes"]:
    _d = _n["data"]
    if _d.get("type") != "interrupt":
        continue
    _t = _d.get("title") or ""
    _m = re.search(r"第([一二三四五六七八九十]+)天", _t)
    if not _m or _m.group(1) not in _CN:
        continue
    _say = _CN[_m.group(1)]
    _op, _val = _day_of(_d.get("interruptCondition") or {})
    if "收尾" in _t and _op == "gte":                      # 最後那一天
        _last_day, _fin = _val, _n["id"]
        if _say != _val:
            bad.append(f"天數對不上　{_n['id']}　標題寫第{_say}天，可是它在 day>={_val} 才進來")
    elif "收尾" in _t:                                      # 每天的收尾日記
        _wrap[_say] = (_n["id"], _op, _val)
        if not (_op == "eq" and _val == _say + 1):
            bad.append(f"天數對不上　{_n['id']}　「{_t}」要在第 {_say+1} 天一開板讀到"
                       f"（day eq {_say+1}），現在是 day {_op} {_val}")
    elif "直播" in _t:
        if not (_op == "eq" and _val == _say):
            bad.append(f"天數對不上　{_n['id']}　「{_t}」要 day eq {_say}，現在是 day {_op} {_val}")

if _last_day is None:
    bad.append("天數對不上　板上找不到「第Ｎ天，收尾」那張插播，全篇有幾天無從驗起")
else:
    _miss = [d for d in range(1, _last_day) if d not in _wrap]
    if _miss:
        bad.append(f"天數對不上　收尾日記缺了第 {'、'.join(map(str, _miss))} 天"
                   f"（全篇 {_last_day} 天，第 1 到 {_last_day-1} 天每天都要有一則）")
    _tail = max(_wrap) if _wrap else None
    for _n in b["nodes"]:
        _d = _n["data"]
        _txt = " ".join([_d.get("title") or "", _d.get("text") or ""]
                        + [l.get("text") or "" for l in (_d.get("dialogueLines") or [])])
        for _m in re.finditer(r"這([一二三四五六七八九十]+)天", _txt):
            if _CN.get(_m.group(1)) not in (None, _last_day):
                bad.append(f"天數對不上　{_n['id']}　台詞說「這{_m.group(1)}天」，"
                           f"實際走完是 {_last_day} 天")
        # 收尾那一場的旁白會報最後一則日記的日期（「第十三天她寫到四點」）。
        for _m in re.finditer(r"第([一二三四五六七八九十]+)天她寫到", _txt):
            if _tail and _CN.get(_m.group(1)) != _tail:
                bad.append(f"天數對不上　{_n['id']}　台詞說「第{_m.group(1)}天她寫到」，"
                           f"最後一則收尾日記是第 {_tail} 天")

# ── 十一、板上每個 @@bg- 代號都要對得到圖 ────────────────────────────
# 2026-09-12 加。這一項防的是「推成功了但線上沒有背景」：
# push.py 找不到圖的時候 bg_url() 回 None，呼叫端把 background 寫成空字串，
# 卡數與邊數完全一致，回讀比對也說「一致」，看起來像推成功了。
# 實際上線上 22 張場景卡沒有背景，而 missing_bg 只印在 log 最前面那一行。
# 真因是 push.py 把副檔名寫死成 .jpg，而白天那批重畫成了 .png。
# 所以這裡**不比對副檔名**，只問「這個代號有沒有對應的檔案」。
_bgdir = pathlib.Path(__file__).resolve().parent.parent / "art/bg-investigation"
_mainassets = pathlib.Path(__file__).resolve().parent.parent / "larch/assets.json"
_shared = set(json.loads(_mainassets.read_text(encoding="utf-8"))) if _mainassets.exists() else set()
_codes = {}
def _scan_bg(o, nid):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("background", "sceneCode") and isinstance(v, str) and v.startswith("@@"):
                _codes.setdefault(v[2:], []).append(nid)
            _scan_bg(v, nid)
    elif isinstance(o, list):
        for v in o:
            _scan_bg(v, nid)
for _n in b["nodes"]:
    _scan_bg(_n["data"], _n["id"])
for _k in sorted(_codes):
    if _k in _shared:                                   # 刻意共用正篇素材的那幾張
        continue
    if not list(_bgdir.glob(_k + ".*")):
        bad.append(f"代號對不到圖　{_k}　用在 {len(_codes[_k])} 張卡（{_codes[_k][0]}…）"
                   f"：art/bg-investigation 底下沒有這個名字的檔案。"
                   f"push.py 的 pick_bg 會默默改用同一地點別的時段那張"
                   f"（三個時段全缺才會列進 missing_bg），"
                   f"所以玩家會在早上看到晚上的那張，而推送不會有任何抱怨")

print("\n".join(bad) if bad else "路徑檢查：沒有問題")
print(f"—— 規則 {len(b['rules'])} 條、舞台指示 {_dirs} 行，問題 {len(bad)} 件")
sys.exit(1 if bad else 0)
