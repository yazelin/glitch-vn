#!/usr/bin/env python3
"""代名詞檢查。這套規則是七個模型會審之後定的:

  「妳」只指格莉奇（黑洞先生與旁白用）
  「你」只指玩家
  格莉奇對黑洞先生說話：句首叫名字，後面省略主語，不用「你」
  旁白：一段連續動作首次用全名，之後可以用「他」
  **黑洞先生不在畫面上時（中午段）一律用全名**（他在中午段有台詞就自動放行） —— 玩家看不到他，代稱一定會誤會
  轉述他的話時把裡面的代名詞拿掉，否則引號裡的「妳」會被讀成在指玩家

原本的規則漏了一條:「你」給玩家、「妳」給格莉奇之後，格莉奇跟黑洞先生當面
講話就沒有第二人稱可用了，硬套會變成「黑洞先生每次都說『妳以前』。黑洞先生
到底知道多少我不記得的事？」——像法庭筆錄。中文可以省略主語，那才是解法。
"""
import pathlib, json, sys, urllib.request

K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
d = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://larch.yapiflow.com/api/agent/projects/{P}",
    headers={"Authorization": f"Bearer {K}"}), timeout=120))

problems = []
for b in d["boards"]:
    if not b["id"].startswith("board-day"):
        continue
    nodes = b["nodes"]
    # 中午段 = 從標題含「中午」的場景卡開始，到下一張場景卡為止
    noon = set()
    inside = False
    order = {n["id"]: i for i, n in enumerate(nodes)}
    for n in sorted(nodes, key=lambda x: order[x["id"]]):
        if n["data"].get("type") == "scene":
            inside = "中午" in (n["data"].get("title") or "")
        if inside:
            noon.add(n["id"])
    # 他在中午段講過話 = 玩家看得到他,代稱就不會誤會(Day 5 他請假整天在家)
    hole_on_screen = any(n["data"].get("speaker") == "黑洞先生" for n in nodes
                         if n["id"] in noon)
    if hole_on_screen:
        noon = set()
    for n in nodes:
        dd = n["data"]; sp = dd.get("speaker")
        texts = [dd.get("text", "")] + [c for c in (dd.get("choices") or []) if isinstance(c, str)]
        for t in texts:
            if not t:
                continue
            if sp == "格莉奇" and "妳" in t:
                problems.append((b["id"], n["id"], "格莉奇不會說「妳」（那是別人對她的稱呼）", t))
            if sp == "黑洞先生" and "你" in t and "存檔" not in t:
                problems.append((b["id"], n["id"], "黑洞先生對格莉奇要用「妳」；對玩家才用「你」", t))
            if "他" in t and "黑洞先生" not in t and n["id"] in noon:
                problems.append((b["id"], n["id"], "中午段他不在畫面上，用「他」會誤會", t))

print(f"檢查 {sum(len(b['nodes']) for b in d['boards'] if b['id'].startswith('board-day'))} 張卡")
if not problems:
    print("代名詞沒有問題。")
for bid, nid, why, t in problems:
    print(f"  [{bid[-4:]}] {nid:18} {why}\n      {t[:60]}")
sys.exit(1 if problems else 0)
