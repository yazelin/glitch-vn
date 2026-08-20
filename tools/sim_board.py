#!/usr/bin/env python3
"""帶變數狀態模擬一張白板:照條件連線走,random 把每個可能值都試過。

單純的可達性檢查不夠——有條件連線之後,要真的照 set/add/random 更新變數、
照條件挑邊,才驗得出哪些卡實際走不到、數值有沒有算錯。

用法:
    python3 sim_board.py board-day2            # 用變數預設值跑
    python3 sim_board.py board-day2 savedOk=1  # 指定進場時的變數狀態
"""
import pathlib, json, sys, urllib.request

K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"

d = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://larch.yapiflow.com/api/agent/projects/{P}",
    headers={"Authorization": f"Bearer {K}"}), timeout=120))
BID = sys.argv[1]
b = [x for x in d["boards"] if x["id"] == BID][0]
N = {n["id"]: n for n in b["nodes"]}
defaults = {v["name"]: v.get("defaultValue", "") for v in d["variables"]}
out = {}
for e in b["edges"]:
    out.setdefault(e["source"], []).append(e)

def cmp_(a, op, bv):
    num = isinstance(a, (int, float)) or isinstance(bv, (int, float))
    try:
        x, y = (float(a), float(bv)) if num else (str(a), str(bv))
    except (TypeError, ValueError):
        x, y = str(a), str(bv)
    return {"gt": x > y, "gte": x >= y, "lt": x < y, "lte": x <= y, "neq": x != y}.get(op, x == y)

def guarded(e):
    c = (e.get("data") or {}).get("condition")
    return bool(c and c.get("variable"))

def pick(es, st):
    """有條件的先判,再吃第一條無條件的當預設"""
    for e in [x for x in es if guarded(x)]:
        c = e["data"]["condition"]
        if cmp_(st.get(c["variable"], ""), c.get("op", "eq"), c.get("value")):
            return e
    plain = [x for x in es if not guarded(x)]
    return plain[0] if plain else None

visited, terms, problems, runs = set(), {}, [], [0]

def run(nid, st, depth=0):
    if depth > 500:
        problems.append("深度爆炸,可能有環"); return
    visited.add(nid)
    dd = N[nid]["data"]; st = dict(st)
    rand = []
    for op in dd.get("variableOps", []):
        v, k, val = op["variable"], op["kind"], op.get("value")
        cur = st.get(v, "")
        if k == "set": st[v] = val
        elif k == "add": st[v] = (float(cur) if str(cur) not in ("", "None") else 0) + float(val)
        elif k == "toggle": st[v] = not bool(cur)
        elif k == "random": rand.append((v, int(op.get("min", 0)), int(op.get("max", 1))))
    if dd.get("inputVariable"): st[dd["inputVariable"]] = "(玩家輸入)"
    states = [st]
    for v, lo, hi in rand:                       # random 的每個可能值都要走一次
        states = [{**s, v: n} for s in states for n in range(lo, hi + 1)]
    es = out.get(nid, [])
    if not es:
        runs[0] += len(states); terms[nid] = terms.get(nid, 0) + len(states); return
    for s in states:
        if dd.get("type") == "choice":
            for i in range(len(dd["choices"])):
                grp = [e for e in es if e.get("sourceHandle") == f"choice-{i}"]
                if not grp: problems.append(f"{nid} 選項{i+1} 沒有出線"); continue
                nx = pick(grp, s)
                if nx is None: problems.append(f"{nid} 選項{i+1} 全部有條件、沒有預設線"); continue
                run(nx["target"], s, depth + 1)
        else:
            grp = [e for e in es if e.get("sourceHandle", "right") == "right"] or es
            nx = pick(grp, s)
            if nx is None: problems.append(f"{nid} 沒有可走的出線"); continue
            run(nx["target"], s, depth + 1)

starts = [n["id"] for n in b["nodes"] if n["data"].get("start")]
print(f"【{b['name']}】卡片 {len(N)} 邊 {len(b['edges'])} start {len(starts)}")
if len(starts) != 1:
    print("  start 卡數量不對!")
init = dict(defaults)
for kv in sys.argv[2:]:
    k, v = kv.split("=", 1)
    init[k] = float(v) if v.replace("-", "").replace(".", "").isdigit() else v
run(starts[0], init)
print(f"  模擬玩法 {runs[0]} 條  終點 {terms}")
un = sorted(set(N) - visited)
print(f"  沒走到的卡 {len(un)}:", un[:20])
for p in dict.fromkeys(problems):
    print("  問題:", p)
