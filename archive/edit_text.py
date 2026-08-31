#!/usr/bin/env python3
"""改台詞。整批重建的腳本掉過一次,所以單句修改直接打 API,不重建。

用法:
    python3 edit_text.py "舊的字" "新的字"          # 全專案取代
    python3 edit_text.py --node d1n-ask "整段新文字"  # 換掉某張卡的整段
"""
import pathlib, json, sys, urllib.request
K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
BASE = f"https://larch.ink/api/agent/projects/{P}"
H = {"Authorization": f"Bearer {K}", "Content-Type": "application/json"}
proj = json.load(urllib.request.urlopen(urllib.request.Request(BASE, headers=H), timeout=120))
hits = []
if sys.argv[1] == "--node":
    nid, new = sys.argv[2], sys.argv[3]
    for b in proj["boards"]:
        for n in b["nodes"]:
            if n["id"] == nid:
                n["data"]["text"] = new; hits.append(nid)
    summary = f"改 {nid} 的台詞"
else:
    old, new = sys.argv[1], sys.argv[2]
    for b in proj["boards"]:
        for n in b["nodes"]:
            t = n["data"].get("text", "")
            if old in t:
                n["data"]["text"] = t.replace(old, new); hits.append(n["id"])
            cs = n["data"].get("choices") or []
            for i, c in enumerate(cs):
                if isinstance(c, str) and old in c:
                    cs[i] = c.replace(old, new); hits.append(n["id"] + f"[選項{i+1}]")
    summary = f"台詞取代：{old[:16]} → {new[:16]}"
if not hits:
    sys.exit("沒有找到要改的地方，什麼都沒動")
json.load(urllib.request.urlopen(urllib.request.Request(BASE,
    json.dumps({"project": proj, "summary": summary}).encode(), H, method="PUT"), timeout=180))
print("改了:", hits)
