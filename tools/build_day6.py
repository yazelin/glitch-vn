#!/usr/bin/env python3
"""Day 6・那一頁不是我寫的 —— 關係第一次反轉。

前五天都是玩家幫她保管,今天換她主動把東西託給全世界最不該被託付的人。

那張空白頁的來歷,玩家在 Day 5 晚上親眼看過(她把筆遞給他,他握了很久,
一個字都沒寫)。她忘了。所以這天從頭到尾是「玩家知道、她不知道」——
比原本設計成謎題還好。

骨架出自 glm-5.2,選擇卡也是它的(處理空白頁的方式決定她晚上怎麼交麵包)。
晚上多插一張填空卡,出自 minimax 的建議:讓玩家替她想那句託付的話。
那是整個遊戲玩家能施力最重的一刻。

觸手數與版本號改成吃變數,不寫死。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE, A

b = Board("board-day6", "Day 6・那一頁不是我寫的",
          "早：守則本裡多了一頁沒有編號的空白　中：他承認是他放的　晚：她把麵包託給他保管")

# ══════════ 早 ══════════
b.prev = b.scene("d6m-scene", "第六天・清晨", "守則本已經攤開在桌上，翻到中間某一頁。", "早",
                 bgm=A["bgm-theme"], start=True)
b.chain([
    ("d6m-boot",  "逼——嗶！", "當機", G),
    ("d6m-page",  "那一頁全空白。沒有字，沒有日期，右下角沒有版本號。", "平常", None),
    ("d6m-flip",  "她翻遍整本。每一頁右下角都有編號，從第一版到第 {{ruleVersion}} 版，只有這頁什麼都沒有。", "平常", None),
    ("d6m-not",   "這頁不是我寫的。", "平常", G),
    ("d6m-num",   "我每天都會編號。你看，連第一天那句蠢話都編了第一版。", "平常", G),
    ("d6m-same",  "紙一樣，墨水一樣，可是這頁上什麼都沒有寫過。連一個標點都沒有。", "發呆", G),
    ("d6m-there", "有人放了一張空白的紙進來，然後讓它待在那裡，像它一直都在。", "發呆", G),
    ("d6m-who",   "我記憶體只有 4KB。你幫我想，這間房子裡除了我還有誰會碰這本？", "平常", G),
])

# ══════════ 中 ══════════
cur = b.scene("d6n-scene", "第六天・中午", "他還沒出門。他站在玄關，正在套外套。", "中")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d6n-hand",  "她把守則本遞過去，翻到那頁空白。", "平常", None),
    ("d6n-ask",   "這是你放的嗎。", "平常", G),
    ("d6n-look",  "他看了很久。靴子在地板上沒有動，公事包掛在觸手上，沒有拿下來也沒有放下。", "平常", None),
    ("d6n-mine",  "是我放的。", "預設", HOLE),
    ("d6n-why",   "為什麼是空白的？", "平常", G),
    ("d6n-idk",   "我不知道要寫什麼。", "預設", HOLE),
    ("d6n-shut",  "她張了張嘴，又閉上。他把外套扣子扣到最上面一顆。", "平常", None),
    ("d6n-never", "等一下。你從來不碰我的守則本。", "平常", G),
    ("d6n-yes",   "對。", "預設", HOLE),
    ("d6n-but",   "那你為什麼——", "平常", G),
    ("d6n-door",  "門關上了。他今天上班沒有再多說一個字。", "平常", None),
    ("d6n-thumb", "她盯著那頁空白，拇指按在紙面上，指紋印上去又淡掉。", "平常", None),
    ("d6n-lazy",  "黑洞先生從來不解釋自己，可是這次連掩飾都懶得做。", "平常", G),
    ("d6n-put",   "放一頁空白進來，說不知道要寫什麼，然後就出門。", "平常", G),
    ("d6n-wait",  "你知道嗎，我覺得黑洞先生在等我替他想。", "發呆", G),
    ("d6n-how",   "你覺得這頁要怎麼辦？", "平常", G),
])
q = b.choice("d6n-q", "這頁空白守則，你要她怎麼處理？",
             ["撕掉（那不是她的格式）", "留著空白，什麼都不動", "在頁緣寫「晚上你寫」"])
b.link(b.prev, q)
nx = b.col()
opts = []
for i, (tag, txt) in enumerate([
        ("tear", "她撕了那頁。碎片留在桌上，她沒有掃。\n"
                 "「他要寫的東西寫不進紙。那就別給他紙了。」"),
        ("keep", "她把本子合上，放回桌角，指腹在封面上停了一下。\n"
                 "「空著就空著。可是我還是想給他一個位置。」"),
        ("ask",  "她在頁緣寫了四個小字：「晚上你寫」。字跡有點抖。\n"
                 "「只寫一行太少了。我再多給一樣東西，看他挑哪個。」")]):
    n = b.setvar(f"d6n-opt-{tag}", [{"variable": "blankPage", "kind": "set", "value": tag}],
                 text=txt, title={"tear": "撕掉", "keep": "留著", "ask": "等他寫"}[tag],
                 x=nx, y=(i - 1) * 260)
    b.link(q, n, f"choice-{i}")
    opts.append(n)

lead = b.say("d6n-lead", "還有一件事。冰箱裡那塊麵包，我不記得自己包過的那塊，紙條還在上面。"
                         "我今天想把它交給黑洞先生——不給他吃，是要他收著。",
             who=G, face="平常", title="她的決定", x=nx + 320, y=0)
for n in opts: b.link(n, lead)
line = b.add("d6n-line", {"type": "input", "title": "替她想一句話",
    "text": "她要對黑洞先生說一句話，好讓他分得出「吃」跟「保管」的差別。\n你替她想。她會照著念。",
    "inputVariable": "handoverLine", "inputPlaceholder": "寫一句話…",
    "inputSuggestions": ["不准吃。", "保管，不是吃。你懂嗎。",
                         "你每天吃掉一件我忘掉的東西。今天這件我要你留著。"]}, x=nx + 640, y=0)
b.link(lead, line); b.prev = line

# ══════════ 晚 ══════════
ex = b.col()
ev = b.scene("d6e-scene", "第六天・傍晚", "門開了。他今天的觸手比早上少一隻，有一雙靴子空著在晃。", "晚",
             x=ex, y=0)
b.link(b.prev, ev)
b.prev = ev

bx = b.col()
BR = {
 "tear": [
    ("d6e-t1", "桌上還有撕碎的紙片。他掃了一眼，沒有問。", "平常", None),
    ("d6e-t2", "她從冰箱裡把麵包撈出來，連同那張紙條，一把推到他胸口。", "平常", None),
    ("d6e-t3", "你拿著。拿在手上，放進口袋，隨便你。", "平常", G),
    ("d6e-t4", "{{handoverLine}}", "平常", G),
    ("d6e-t5", "他低頭看那塊麵包。觸手末端慢慢伸出來，接過，收進西裝內袋。", "平常", None),
    ("d6e-t6", "我分得清楚。", "預設", HOLE),
    ("d6e-t7", "你最好分得清楚。因為我明天醒來就忘了，到時候只有你知道這塊麵包是吃了還是還在。", "平常", G),
    ("d6e-t8", "他看了她一會兒，觸手在內袋的位置輕輕按了一下。", "平常", None),
    ("d6e-t9", "還在。", "預設", HOLE),
 ],
 "keep": [
    ("d6e-k1", "守則本合著，擺在桌上。她坐在旁邊，麵包已經從冰箱裡拿出來放在膝蓋上。", "平常", None),
    ("d6e-k2", "你早上說你不知道要寫什麼。", "平常", G),
    ("d6e-k3", "我每天寫一句話給明天的自己。你每天都看著我寫，看了六天，還是不知道要寫什麼。", "平常", G),
    ("d6e-k4", "那這個給你。", "平常", G),
    ("d6e-k5", "她站起來，把麵包放進他伸出來的觸手裡，動作很輕，紙條朝上。", "平常", None),
    ("d6e-k6", "{{handoverLine}}", "平常", G),
    ("d6e-k7", "我懂。", "預設", HOLE),
    ("d6e-k8", "你以前說過懂嗎？", "平常", G),
    ("d6e-k9", "沒有。", "預設", HOLE),
    ("d6e-k10","那你今天是第一次說懂。", "平常", G),
    ("d6e-k11","他把麵包收進西裝內袋。靴子在地板上挪了一下，像是重心多了一點什麼。", "平常", None),
 ],
 "ask": [
    ("d6e-a1", "她左手拿守則本，右手拿麵包，兩樣東西一起遞過去。", "平常", None),
    ("d6e-a2", "守則本翻到那頁空白，旁邊我寫了「晚上你寫」。", "平常", G),
    ("d6e-a3", "你說你不知道要寫什麼。那你寫「今天格莉奇託我一塊麵包，我沒有吃」。", "平常", G),
    ("d6e-a4", "這塊麵包也給你。你保管麵包，也保管那句話。", "平常", G),
    ("d6e-a5", "{{handoverLine}}", "平常", G),
    ("d6e-a6", "他接過守則本和麵包。觸手把本子翻到空白頁，停了很久，公事包還掛在另一隻觸手上。", "平常", None),
    ("d6e-a7", "這樣寫。", "預設", HOLE),
    ("d6e-a8", "他從內袋拿出一支筆，在空白頁上寫了一行，闔上本子還給她。麵包收進內袋。", "平常", None),
    ("d6e-a9", "她打開本子看了一眼。", "平常", None),
    ("d6e-a10","頁面上沒有她教的那句話。只有三個字：「她給的。」", "平常", None),
 ],
}
ends = []
for i, tag in enumerate(("tear", "keep", "ask")):
    made = b.chain(BR[tag], y=(i - 1) * 420, x=bx, link_prev=False)
    cond = None if tag == "ask" else {"variable": "blankPage", "op": "eq", "value": tag}
    b.link(ev, made[0], "right", cond=cond)
    ends.append(made[-1])

mx = bx + 300 * 12
kept = b.setvar("d6e-kept", [{"variable": "breadKept", "kind": "set", "value": 1},
                             {"variable": "givenCount", "kind": "add", "value": 1}],
                text="麵包在他身上了。", title="託付出去", x=mx, y=0)
for e in ends: b.link(e, kept)
b.prev = kept
b.chain([
    ("d6e-rule",  "她翻到下一頁，寫今天的守則。", "平常", None),
])
cur = b.add("d6e-rulein", {"type": "input", "title": "填空位",
    "text": "空位在這裡。今天要留什麼給明天的我？",
    "inputVariable": "ruleLine6", "inputPlaceholder": "寫一句話…",
    "inputSuggestions": ["黑洞先生會把東西吃掉，也會把東西收起來。這兩件事同時是真的。",
                         "我託了一塊麵包給他。明天問他還在不在。",
                         "守則本裡有一頁不是我寫的。"]})
b.link(b.prev, cur); b.prev = cur
cur = b.setvar("d6e-rulever", [{"variable": "ruleVersion", "kind": "add", "value": 1},
                               {"variable": "dayCount", "kind": "set", "value": 6}],
               text="她寫上去。第 {{ruleVersion}} 版，完成。", title="守則 +1")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d6e-save",  "記得存檔。今天我把一個東西放到我自己拿不回來的地方了。", "平常", G),
    ("d6e-sleep", "她躺下來。西裝內袋的位置鼓起一小塊，在黑暗裡看不出形狀。", "平常", None),
])
b.link(b.prev, b.jump("d6e-jump", "board-day7", "d7m-scene"))
b.push("Day 6 關係反轉:她主動把麵包託給他保管;空白頁的處理方式決定晚上怎麼交;玩家替她寫託付的那句話")
