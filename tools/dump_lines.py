#!/usr/bin/env python3
"""印出一塊板子上「某個角色」的每一句台詞，帶卡片編號。

給改寫用。dump_board 是給人讀劇情的，沒有編號就套不回去——
上一輪 gemini 自己編了 CARD-01 這種號碼，結果整份沒辦法機械套用。
前後各帶一句當上下文，不然改寫的人不知道這句接在哪裡。

用法：python3 dump_lines.py board-day1 [說話者]
"""
import collections, json, pathlib, sys

P = json.load(open(pathlib.Path.home() / "glitch-vn/backup/project.json"))
bid = sys.argv[1]
who = sys.argv[2] if len(sys.argv) > 2 else "格莉奇"
B = next(b for b in P["boards"] if b["id"] == bid)
N = {n["id"]: n for n in B["nodes"]}
inc = collections.defaultdict(list)
out = collections.defaultdict(list)
for e in B["edges"]:
    inc[e["target"]].append(e["source"])
    out[e["source"]].append(e["target"])

def brief(nid):
    if nid not in N: return ""
    d = N[nid]["data"]
    sp = d.get("speaker") or "旁白"
    t = (d.get("text") or "").replace("\n", "／")[:34]
    return f"{sp}：{t}" if t else f"〔{d.get('title') or d.get('type')}〕"

for n in B["nodes"]:
    d = n["data"]
    if d.get("speaker") != who: continue
    t = (d.get("text") or "").replace("\n", "\\n")
    if not t: continue
    prev = "／".join(brief(x) for x in inc[n["id"]][:2]) or "（開頭）"
    nxt = "／".join(brief(x) for x in out[n["id"]][:2]) or "（結尾）"
    print(f"{n['id']}\t{t}")
    print(f"\t　前：{prev}")
    print(f"\t　後：{nxt}")
