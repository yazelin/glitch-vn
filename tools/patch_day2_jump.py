#!/usr/bin/env python3
"""Day 2 結尾接到 Day 3。

build_day2.py 在 scratchpad 被清掉的時候弄丟了,所以這天沒辦法重建,只能就地補。
原本結尾停在「第三天還沒做」的佔位卡 —— 那是 Day 3 還沒蓋的時候留的,現在
七天都蓋好了,那張要換成正式的過場並接上 board-day3。
"""
import json, pathlib, urllib.request
K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
BASE = f"https://larch.yapiflow.com/api/agent/projects/{P}"
H = {"Authorization": f"Bearer {K}", "Content-Type": "application/json"}
proj = json.load(urllib.request.urlopen(urllib.request.Request(BASE, headers=H), timeout=120))
B = next(b for b in proj["boards"] if b["id"] == "board-day2")
tbc = next(n for n in B["nodes"] if n["id"] == "d2e-tbc")
tbc["data"]["text"] = "她躺回床上。門邊那疊短靴裡，裂開的那一雙在最上面。"
tbc["data"]["title"] = "旁白"
if not any(n["id"] == "d2e-jump" for n in B["nodes"]):
    B["nodes"].append({"id": "d2e-jump", "type": "story",
        "position": {"x": tbc["position"]["x"] + 300, "y": tbc["position"]["y"]},
        "data": {"type": "boardJump", "title": "下一天", "text": "天亮了。",
                 "jumpBoardId": "board-day3", "jumpNodeId": "d3m-scene"}})
    B["edges"].append({"id": "e-d2e-tbc-d2e-jump", "source": "d2e-tbc",
                       "target": "d2e-jump", "sourceHandle": "right", "data": {}})
json.load(urllib.request.urlopen(urllib.request.Request(
    BASE, json.dumps({"project": proj, "summary": "Day 2 接上 Day 3"}).encode(),
    H, method="PUT"), timeout=180))
print("Day 2 -> Day 3 接好了")
