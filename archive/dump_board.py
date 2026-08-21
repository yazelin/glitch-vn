#!/usr/bin/env python3
"""把一塊板子的卡片依連線順序印成可讀劇本,拿去給人(或 AI)審。"""
import json, sys, collections
P = json.load(open("/home/ct/glitch-vn/backup/project.json"))
bid = sys.argv[1]
# 卡片掛在 boards 底下,不是頂層的 nodes——頂層那份只是主板
B = next(b for b in P["boards"] if b["id"] == bid)
nodes = {n["id"]: n for n in B["nodes"]}
edges = [e for e in B["edges"] if e["source"] in nodes]
out = collections.defaultdict(list)
for e in edges: out[e["source"]].append(e)
indeg = collections.Counter(e["target"] for e in edges)
start = [n for n in nodes.values() if not indeg[n["id"]]]
seen, order = set(), []
def walk(nid):
    if nid in seen: return
    seen.add(nid); order.append(nid)
    for e in out[nid]: walk(e["target"])
for s in start: walk(s["id"])
for nid in order:
    d = nodes[nid]["data"]; t = d.get("type")
    who = d.get("characterName") or ""
    if t == "scene":   print(f"\n### {d.get('title','')} — {d.get('text','')}")
    elif t == "choice":
        print(f"  [選擇] {d.get('text','').splitlines()[0]}")
        for i, c in enumerate(d.get("choices", [])): print(f"    {i}. {c.get('text', c) if isinstance(c,dict) else c}")
    elif t == "setVariable": 
        if d.get("text"): print(f"  ({d.get('title','')}) {d['text']}")
    elif t == "input":  print(f"  [填空] {d.get('text','')}")
    elif t == "boardJump": print(f"  → 跳到 {d.get('jumpBoardId')}")
    else:
        print(f"  {who + '：' if who else ''}{d.get('text','')}")
