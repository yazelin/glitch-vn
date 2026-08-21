"""走一塊板子，吐出「一條可讀劇本」的事件流。

export_script.py（純文字）跟 gen_script_site.py（HTML）共用這一支——
走圖的邏輯只能有一份，不然兩邊會慢慢長歪。

事件是 dict，`kind` 決定怎麼渲染：
    scene / say / choice / input / jump / vars / branch / loop
`depth` 是分支縮排層數。
"""
import collections, json, pathlib

P = json.load(open(pathlib.Path.home() / "glitch-vn/backup/project.json"))
# 線上跑的是新前提版。舊版的板子還在專案裡，但劇本輸出以線上那條為準。
DAYS = sorted([b for b in P["boards"] if b["id"].startswith("board-v2-day")],
              key=lambda b: int(b["id"].split("day")[-1]))
OP = {"eq": "＝", "neq": "≠", "gt": "＞", "gte": "≥", "lt": "＜", "lte": "≤"}
V = {v["name"]: (v.get("label") or v["name"]) for v in P["variables"]}


def cond_text(c):
    if not c:
        return ""
    return f'{V.get(c["variable"], c["variable"])} {OP.get(c["op"], c["op"])} {c["value"]}'


def _ops_text(d):
    parts = []
    for o in (d.get("variableOps") or []):
        name = V.get(o["variable"], o["variable"])
        if o["kind"] == "set":
            parts.append(f'{name}＝{o.get("valueFrom") or o.get("value")}')
        elif o["kind"] == "add":
            v = o.get("value", 0)
            sign = "+" if str(v).lstrip("-").isdigit() and float(v) > 0 else ""
            parts.append(f"{name}{sign}{v}")
        else:
            parts.append(f'{name} {o["kind"]}')
    return "、".join(parts)


def _reach(nid, eo):
    out, stack = set(), [nid]
    while stack:
        n = stack.pop()
        if n in out:
            continue
        out.add(n)
        stack += [e["target"] for e in eo.get(n, [])]
    return out


def _merge_point(nid, es, eo):
    """幾條分支後來又併回同一張卡的話，那張卡就是「主線」的續集。

    不找出來的話，深度優先會把整天的續集吃進第一條分支裡——讀的人會看到
    主線縮排在一個罕見分支底下，而且縮排會一路往右爬（實測爬到 21 層）。
    找到匯流點之後：每條分支只走到匯流點為止，主線回到外層繼續。
    """
    sets = [_reach(e["target"], eo) for e in es]
    if len(sets) < 2:
        return None
    common = set.intersection(*sets)
    if not common:
        return None
    q, seen = collections.deque([nid]), {nid}
    while q:                      # 從分岔點 BFS，第一個碰到的共同節點就是最近的匯流點
        n = q.popleft()
        for e in eo.get(n, []):
            t = e["target"]
            if t in common:
                return t
            if t not in seen:
                seen.add(t)
                q.append(t)
    return None


def walk(nid, seen, depth, eo, N, stop=frozenset()):
    while True:
        if nid in stop:
            return                # 匯流點交給外層走，分支到這裡為止
        if nid in seen:
            yield {"kind": "loop", "depth": depth,
                   "text": N[nid]["data"].get("title") or nid}
            return
        seen.add(nid)
        d = N[nid]["data"]
        t = d.get("type") or "dialogue"
        txt = (d.get("text") or "").strip()

        if t == "scene":
            yield {"kind": "scene", "depth": depth, "title": d.get("title", ""), "text": txt}
        elif t == "choice":
            yield {"kind": "choice", "depth": depth, "text": txt.splitlines()[0]}
        elif t == "input":
            yield {"kind": "input", "depth": depth, "var": d.get("inputVariable"),
                   "text": txt.splitlines()[0]}
        elif t == "boardJump":
            yield {"kind": "jump", "depth": depth, "to": d.get("jumpBoardId")}
            return
        elif t == "setVariable":
            ops = _ops_text(d)
            if txt or ops:
                yield {"kind": "vars", "depth": depth, "text": txt, "ops": ops}
        else:
            yield {"kind": "say", "depth": depth, "who": d.get("speaker"),
                   "lines": txt.splitlines()}

        es = eo.get(nid, [])
        if not es:
            return
        if len(es) == 1 and not (es[0].get("data") or {}).get("condition"):
            nid = es[0]["target"]
            continue
        opts = d.get("choices") or []
        merge = _merge_point(nid, es, eo)
        inner = stop | ({merge} if merge else set())
        for e in es:
            h = e.get("sourceHandle") or "right"
            c = cond_text((e.get("data") or {}).get("condition"))
            label = None
            if h.startswith("choice-") and h != "choice-all":
                i = int(h[7:]) if h[7:].isdigit() else None
                label = opts[i] if i is not None and i < len(opts) else h
            yield {"kind": "branch", "depth": depth, "label": label, "cond": c}
            yield from walk(e["target"], seen, depth + 1, eo, N, inner)
        if merge and merge not in seen and merge not in stop:
            nid = merge          # 主線回到外層繼續
            continue
        return


def board_events(b):
    N = {n["id"]: n for n in b["nodes"]}
    eo = collections.defaultdict(list)
    for e in b["edges"]:
        eo[e["source"]].append(e)
    # 照引擎的真實判斷順序：有條件的先判，第一條無條件的當預設。
    # 主線會不會被縮排進罕見分支，是 _merge_point 在管，不是靠這裡排序。
    for k in eo:
        eo[k].sort(key=lambda e: ((e.get("sourceHandle") or "right"),
                                  0 if (e.get("data") or {}).get("condition") else 1))
    start = next((n["id"] for n in b["nodes"] if n["data"].get("start")), b["nodes"][0]["id"])
    yield from walk(start, set(), 0, eo, N)
