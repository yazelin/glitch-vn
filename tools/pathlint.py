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
 八、選項條件（`choiceConditions`）壞掉的三種樣子
     ・陣列長度跟 `choices` 對不上 → 平台按索引取，錯位等於把條件掛到別格去
     ・一張選擇卡在劇情模式下每一格都被擋掉 → 那張卡走不出去（劇情模式的死路）
     ・劇情模式的軌道有對不到卡的步（`walk.miss`）→ 那一步沒有人擋，鐵路在那裡斷掉
     （選項吃條件是 2026-09-11 實測的，見 design/調查篇.md 七。以前以為不吃，
       所以走廊那一場把劇情複製了一份繞過去）
可達性不在這裡，那是 tools/sim.py 的事。

**八項每一項都有負控制**，在 `tools/pathlint_selftest.py`：它把故障注進板子的副本，
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

# 八、選項條件
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

print("\n".join(bad) if bad else "路徑檢查：沒有問題")
print(f"—— 規則 {len(b['rules'])} 條、舞台指示 {_dirs} 行，問題 {len(bad)} 件")
sys.exit(1 if bad else 0)
