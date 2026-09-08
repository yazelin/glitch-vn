#!/usr/bin/env python3
"""板上路徑的靜態檢查。跑：python3 tools/pathlint.py

抓三類實際踩過的路徑 bug：
 一、同一個地點同一個時段有兩格標籤一樣，而且條件可以同時成立
     → 玩家會點到錯的那一張（工作室問 0x 那格中過，白天的短版蓋掉深夜版）
 二、條件比對的值沒有任何一張卡設得到 → 那一格永遠開不了
 三、條件讀的變數沒有任何地方會寫 → 通常是打錯字
可達性不在這裡，那是 tools/sim.py 的事。
"""
import json, re, sys, collections, pathlib, itertools

ROOT = pathlib.Path(__file__).resolve().parent.parent
b = json.loads((ROOT / "larch/inv/out/board.json").read_text(encoding="utf-8"))

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

print("\n".join(bad) if bad else "路徑檢查：沒有問題")
print(f"—— 規則 {len(b['rules'])} 條，問題 {len(bad)} 件")
sys.exit(1 if bad else 0)
