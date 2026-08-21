#!/usr/bin/env python3
"""讀一遍就要懂的檢查。

作者的原話：「你用太多代名詞，我難以理解，用講給國中生的方式寫對話。」

check_pronouns.py 只管「用錯人稱」，這一支管「讀起來累」：
  1. 一張卡出現 3 次以上「他」——連續代名詞讀起來要自己接
  2. 卡片開頭就是「他」，而這張卡跟前一張都沒有出現全名——不知道在講誰
  3. 一句話超過 30 個字——國中生讀一遍會斷氣
  4. 一張卡的「她」超過 3 次

不是每一個代名詞都要換掉。中文本來就會省略主語，全部換成全名會變成法庭筆錄
（原本的代名詞規則就踩過這個坑）。這裡只抓「讀者得停下來想一下」的那些。
"""
import json, os, pathlib, re, sys, urllib.request

K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
d = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://larch.yapiflow.com/api/agent/projects/{P}",
    headers={"Authorization": f"Bearer {K}"}), timeout=120))
DAYS = sorted([b for b in d["boards"] if b["id"].startswith("board-day")],
              key=lambda b: int(b["id"].replace("board-day", "")))

SENT = re.compile(r"[^。！？\n]+[。！？]?")
VAR = re.compile(r"\{\{[^}]+\}\}")

def readable(t):
    """算長度之前先把變數換成短字——{{slot1}} 執行時是「窗台上的圓印」這種，
    不是八個字元的樣板。另外狀態列那一行是括號裡的數字，不是要讀的句子。"""
    t = VAR.sub("○○○", t)
    return "\n".join(l for l in t.split("\n")
                      if not (l.startswith("（") and l.endswith("）")))
problems = []
for b in DAYS:
    prev_named = False
    for n in b["nodes"]:
        dd = n["data"]
        t = (dd.get("text") or "").strip()
        if not t:
            prev_named = prev_named
            continue
        named = "黑洞先生" in t
        why = []
        if t.count("他") >= 3:
            why.append(f"「他」{t.count('他')} 次")
        if t.lstrip("「（").startswith("他") and not named and not prev_named:
            why.append("開頭就是「他」，前後都沒有名字")
        if t.count("她") >= 4:
            why.append(f"「她」{t.count('她')} 次")
        for s_ in SENT.findall(readable(t)):
            s_ = s_.strip()
            if len(s_) > 30:
                why.append(f"一句 {len(s_)} 字")
                break
        if why:
            problems.append((b["id"][-4:], n["id"], dd.get("speaker") or "旁白",
                             "、".join(why), t))
        prev_named = named

print(f"檢查 {sum(len(b['nodes']) for b in DAYS)} 張卡，{len(problems)} 張讀起來會卡")
by_day = {}
for day, *_ in problems:
    by_day[day] = by_day.get(day, 0) + 1
print("  " + "　".join(f"{k} {v}" for k, v in sorted(by_day.items())))
if "-v" in sys.argv:
    for day, nid, sp, why, t in problems:
        print(f"\n[{day}] {nid}　{sp}　（{why}）\n  {t}")
sys.exit(1 if problems else 0)
