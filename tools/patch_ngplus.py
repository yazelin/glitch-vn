#!/usr/bin/env python3
"""二週目知識閘門,插在 Day 1 最前面。

Larch 的變數是專案層級、有預設值,新開一場就回預設 —— 平台沒有 NG+。
但這個遊戲不需要平台支援:玩家本人就是存檔。所以開場由**旁白直接問玩家**
(不經過格莉奇,才不會踩到她的失憶設定),問一件只有玩完的人才會知道的事。

答對的暗號都是遊戲裡真的出現過、而且**猜不到**的句子:
  「她給的」   Day 6 選了第三條路,他寫在空白頁上的三個字
  「不要數」   Day 4 晚上他說的
  「看妳睡」   Day 5 晚上他說的
  「以前」     他每次被追問就停在這兩個字
標點有沒有打都收,免得玩家答對了卻被字串比對擋掉。

Day 1 的建置腳本弄丟了(暫存目錄被清空),所以只能就地補。
"""
import json, pathlib, urllib.request

K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
BASE = f"https://larch.yapiflow.com/api/agent/projects/{P}"
H = {"Authorization": f"Bearer {K}", "Content-Type": "application/json"}

TOKENS = ["她給的", "她給的。", "不要數", "不要數。", "看妳睡", "看妳睡。", "以前", "以前。"]

proj = json.load(urllib.request.urlopen(urllib.request.Request(BASE, headers=H), timeout=120))
B = next(b for b in proj["boards"] if b["id"] == "board-day1")
have = {n["id"] for n in B["nodes"]}
scene = next(n for n in B["nodes"] if n["id"] == "d1m-scene")
x0, y0 = scene["position"]["x"], scene["position"]["y"]

def node(nid, data, dx, dy=0):
    if nid in have: return nid
    B["nodes"].append({"id": nid, "type": "story",
                       "position": {"x": x0 + dx, "y": y0 + dy}, "data": data})
    return nid

def say(nid, text, dx, dy=0, who=None):
    d = {"type": "dialogue", "title": "旁白" if who is None else text[:14],
         "text": text, "speaker": "旁白" if who is None else who,
         "characterPosition": "center"}
    return node(nid, d, dx, dy)

def link(a, b, handle="right", cond=None):
    eid = f"e-{a}-{b}" + (f"-{cond['value']}" if cond else "")
    if any(e["id"] == eid for e in B["edges"]): return
    e = {"id": eid, "source": a, "target": b, "sourceHandle": handle, "data": {}}
    if cond: e["data"]["condition"] = {"kind": "variable", **cond}
    B["edges"].append(e)

ask = say("d1ng-ask", "在她醒來之前。\n如果這不是你第一次來，你會知道一件她不知道的事。", -900, -200)
inp = node("d1ng-in", {"type": "input", "title": "暗號",
    "text": "寫一句這個房子裡有人說過、而她記不住的話。\n第一次來的話直接跳過就好。",
    "inputVariable": "ngToken", "inputPlaceholder": "（第一次來就留空）"}, -600, -200)
hub = say("d1ng-hub", "……", -300, -200)
link(ask, inp); link(inp, hub)

yes = node("d1ng-yes", {"type": "setVariable", "title": "你以前來過",
    "text": "", "variableOps": [{"id": "op-0", "variable": "ngPlus", "kind": "set", "value": 1}]},
    -300, -520)
for t in TOKENS:
    link(hub, yes, "right", {"variable": "ngToken", "op": "eq", "value": t})

y1 = say("d1ng-y1", "你打的那幾個字留在畫面上，過了三秒才淡掉。", 0, -520)
y2 = say("d1ng-y2", "她還沒醒。她不會知道你打過什麼，明天也不會。", 300, -520)
y3 = say("d1ng-y3", "可是你知道。這一次你不是新來的。", 600, -520)
link(yes, y1); link(y1, y2); link(y2, y3)

# 兩條路都回到原本的開場
link(y3, "d1m-boot")
link(hub, "d1m-boot")

# 起點還是 d1m-scene —— 背景與 BGM 掛在那張上,拔掉遊戲會沒有背景。
# 閘門插在它後面:場景 → 閘門 → 原本的開機。
B["edges"] = [e for e in B["edges"]
              if not (e["source"] == "d1m-scene" and e["target"] == "d1m-boot")]
link("d1m-scene", ask)

json.load(urllib.request.urlopen(urllib.request.Request(
    BASE, json.dumps({"project": proj, "summary": "Day 1 加二週目知識閘門"}).encode(),
    H, method="PUT"), timeout=180))
print("閘門裝好了。收的暗號：", "、".join(TOKENS[::2]))
