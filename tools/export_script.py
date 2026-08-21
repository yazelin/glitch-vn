#!/usr/bin/env python3
"""把整個遊戲匯出成一份看得懂的劇本。

dump_board.py 是把節點圖照順序印出來，分支會被攤平成一條直線——拿去給人審
會誤判（會以為玩家一次要讀完全部分支）。這一支照圖的結構走，分支標出來、
縮排開，讀的人看得出「這裡岔開了，玩家只走一條」。

用法：python3 export_script.py > docs/script.txt
"""
import collections, json, pathlib, sys

P = json.load(open(pathlib.Path.home() / "glitch-vn/backup/project.json"))
DAYS = sorted([b for b in P["boards"] if b["id"].startswith("board-day")],
              key=lambda b: int(b["id"].replace("board-day", "")))
OP = {"eq": "＝", "neq": "≠", "gt": "＞", "gte": "≥", "lt": "＜", "lte": "≤"}
V = {v["name"]: (v.get("label") or v["name"]) for v in P["variables"]}
out = []


def cond_text(c):
    if not c:
        return ""
    return f'{V.get(c["variable"], c["variable"])} {OP.get(c["op"], c["op"])} {c["value"]}'


def walk(board, nid, seen, depth, edges_out, N):
    pad = "　" * depth
    while True:
        if nid in seen:
            out.append(f"{pad}↩︎（回到前面的「{N[nid]['data'].get('title') or nid}」）")
            return
        seen.add(nid)
        d = N[nid]["data"]
        t = d.get("type") or "dialogue"
        who = d.get("speaker")
        txt = (d.get("text") or "").strip()

        if t == "scene":
            out.append(f"\n{pad}── {d.get('title','')} ──　{txt}")
        elif t == "choice":
            out.append(f"{pad}【選擇】{txt.splitlines()[0]}")
        elif t == "input":
            out.append(f"{pad}【玩家打字 → {d.get('inputVariable')}】{txt.splitlines()[0]}")
        elif t == "boardJump":
            out.append(f"{pad}→ 接到 {d.get('jumpBoardId')}")
            return
        elif t == "setVariable":
            ops = "、".join(f'{V.get(o["variable"], o["variable"])}'
                            + (f'＝{o.get("value")}' if o["kind"] == "set" else
                               f'{"+" if str(o.get("value","0")).lstrip("-").isdigit() and float(o.get("value",0))>0 else ""}{o.get("value")}'
                               if o["kind"] == "add" else f' {o["kind"]}')
                            for o in (d.get("variableOps") or []))
            if txt:
                out.append(f"{pad}{txt}" + (f"　〔{ops}〕" if ops else ""))
            elif ops:
                out.append(f"{pad}〔{ops}〕")
        else:
            for line in txt.splitlines():
                out.append(f"{pad}{who + '：' if who and who != '旁白' else ''}{line}")

        es = edges_out.get(nid, [])
        if not es:
            return
        if len(es) == 1 and not (es[0].get("data") or {}).get("condition"):
            nid = es[0]["target"]; continue
        # 分支
        opts = d.get("choices") or []
        for e in es:
            h = e.get("sourceHandle") or "right"
            c = cond_text((e.get("data") or {}).get("condition"))
            if h.startswith("choice-") and h != "choice-all":
                i = int(h[7:]) if h[7:].isdigit() else None
                label = opts[i] if i is not None and i < len(opts) else h
                head = f"{pad}　◆ 選「{label}」" + (f"（{c} 才走這條）" if c else "")
            else:
                head = f"{pad}　◆ " + (f"{c} 的話" if c else "其他情況")
            out.append(head)
            walk(board, e["target"], seen, depth + 1, edges_out, N)
        return


for b in DAYS:
    out.append(f"\n\n{'═' * 56}\n{b['name']}\n{b.get('description','')}\n{'═' * 56}")
    N = {n["id"]: n for n in b["nodes"]}
    eo = collections.defaultdict(list)
    for e in b["edges"]:
        eo[e["source"]].append(e)
    for k in eo:
        eo[k].sort(key=lambda e: ((e.get("sourceHandle") or "right"),
                                  0 if (e.get("data") or {}).get("condition") else 1))
    start = next((n["id"] for n in b["nodes"] if n["data"].get("start")), b["nodes"][0]["id"])
    walk(b, start, set(), 0, eo, N)

print("\n".join(out))
