#!/usr/bin/env python3
"""把七章的支線抓下來存成 design/vn-routes.json。

小說站要介紹 VN 版的遊玩路徑，可是網站產生器不該連網。
所以這一支負責抓，gen_novel.py 只負責讀。改了支線就重跑這一支。
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import ROOT, api  # noqa: E402

p = api()
out = []
for b in sorted(p["boards"], key=lambda b: b["id"]):
    nodes = {n["id"]: n for n in b["nodes"]}
    out_edges = {}
    for e in b["edges"]:
        out_edges.setdefault(e["source"], []).append(e)
    for n in b["nodes"]:
        d = n["data"]
        if d.get("type") != "choice":
            continue
        arms = []
        for e in sorted(out_edges.get(n["id"], []), key=lambda e: e.get("sourceHandle", "")):
            texts, cur = [], e["target"]
            # 沿著這一條走到匯流之前（下一張有多個入邊的就是匯流點）
            indeg = {}
            for e2 in b["edges"]:
                indeg[e2["target"]] = indeg.get(e2["target"], 0) + 1
            while cur and indeg.get(cur, 0) == 1:
                texts.append(nodes[cur]["data"].get("text", ""))
                nxt = out_edges.get(cur, [])
                cur = nxt[0]["target"] if len(nxt) == 1 else None
            arms.append({"label": e.get("label", ""), "text": texts})
        out.append({"board": b["id"], "chapter": b["name"],
                    "prompt": d.get("text", ""), "arms": arms})
path = ROOT / "design/vn-routes.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(out)} 個支線點 → {path}")
for r in out:
    print(f"  {r['board']}　{r['prompt'][:22]}　{[a['label'] for a in r['arms']]}")
