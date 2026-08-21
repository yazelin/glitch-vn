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
        sp = dd.get("speaker")
        t = (dd.get("text") or "").strip()
        if not t:
            prev_named = prev_named
            continue
        named = "黑洞先生" in t
        why = []
        # 只數次數是錯的規則。先講名字再一路用「他」是正確的中文,不該報。
        # 真正累的是**沒有錨點**的代名詞:整張卡都沒有出現名字。
        if t.count("他") >= 3 and not named:
            why.append(f"「他」{t.count('他')} 次而且整張卡沒有名字")
        if t.lstrip("「（").startswith("他") and not named and not prev_named:
            why.append("開頭就是「他」，前後都沒有名字")
        # 跟「他」同一個道理:開頭點過名字之後一路用「她」是正確的中文。
        if t.count("她") >= 4 and "格莉奇" not in t:
            why.append(f"「她」{t.count('她')} 次而且整張卡沒有名字")
        for s_ in SENT.findall(readable(t)):
            s_ = s_.strip()
            if len(s_) > 30:
                why.append(f"一句 {len(s_)} 字")
                break
        # 黑洞先生一次最多兩句短的。標成他卻講了一長串,通常是說話者標錯——
        # 這種錯代名詞檢查抓不到（句子裡沒有你／妳）。Day 2 有一句這樣錯了很久。
        if sp == "黑洞先生":
            n_sent = len([x for x in re.split(r"[。！？\n]", t) if x.strip()])
            # 三個五字短句是他的講法（「每天都數。每天我都說。每天妳都忘。」）,
            # 用 OR 會把最好的台詞報成 bug。要句數多**而且**真的長才算。
            if n_sent > 2 and len(t) > 26:
                why.append(f"標成黑洞先生但講了 {n_sent} 句 / {len(t)} 字")
        # 旁白被整段包引號:上一輪改寫留下來的痕跡。
        # 只看頭尾是錯的規則——「台詞。」「台詞。」這種交錯也是頭尾都引號。
        # 要看**第一個引號是不是到最後一個字才閉合**,那才是整段被包起來。
        st = t.strip()
        if sp in (None, "旁白") and st.startswith("「"):
            depth = 0
            for k, ch in enumerate(st):
                depth += (ch == "「") - (ch == "」")
                if depth == 0:
                    if k == len(st) - 1:
                        why.append("旁白被整段包了引號")
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
