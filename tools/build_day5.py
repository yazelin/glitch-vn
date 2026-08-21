#!/usr/bin/env python3
"""Day 5・他請假 —— 格式壞掉的那一天。

七家會審裡有五家說這天最容易寫壞:中午「只剩她跟玩家」是整個遊戲的核心迴圈,
他在家就整個失效,東西要餵誰、瞞誰都不成立。所以這天不迴避,直接把「格式壞掉」
變成主題 —— 今天沒有東西可以分類,玩家改成挑「這一個中午要揭開哪一道傷口」。

骨架與大部分台詞出自 glm-5.2 的稿子(六家裡它的中午段最有膽),我做的修改:
  * 她的台詞裡原本直接講「Day 3」「Day 4」,出戲,換成守則版次與「前幾天」
  * 觸手數量寫死五隻改成 {{holeFeet}},接上累積變數
  * 早上補一句冰箱,不然中午第三條線沒有伏筆
  * 守則改成三張填空卡,建議句依中午的選擇不同

黑洞先生今天在場,所以中午段可以用「他」;check_pronouns 會自動放行
(判斷依據:他在中午段有台詞)。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE, A

b = Board("board-day5", "Day 5・他請假",
          "早：開機第一眼看見的是他，開機流程卡住　中：沒有東西可以分類，改成挑一道傷口揭開　晚：他沒出門，也就沒有回來")

# ══════════ 早 ══════════
b.prev = b.scene("d5m-scene", "第五天・清晨", "開機音拖了長音，比平常久。", "早",
                 bgm=A["bgm-theme"], start=True)
b.prev = b.wake("d5m", prefill=["昨天守則上那句話"])
b.link(b.find("d5m-scene")["id"], b.prev)
b.chain([
    ("d5m-boot",  "逼——嗶嗶嗶嗶——", "當機", G),
    ("d5m-see",   "她睜開眼睛，第一眼看見的是房間角落的陰影。黑洞先生坐在那裡，領口歪著，眼睛半閉。", "平常", None),
    ("d5m-stuck", "開機流程卡在第三步。「室友已出門」這一項驗不過。", "平常", None),
    ("d5m-home",  "你今天在家。", "平常", G),
    ("d5m-yes",   "嗯。", "預設", HOLE),
    ("d5m-off",   "請假？", "平常", G),
    ("d5m-yes2",  "嗯。", "預設", HOLE),
    ("d5m-why",   "為什麼？", "平常", G),
])
# 她昨天數到了的話，他今天不出門就有理由——而且他會說。
# 兩家說 Day 5 缺一個屬於自己的頓悟；這裡讓 Day 4 的發現在今天結帳。
wx = b.col()
w_yes = b.say("d5m-why-yes", "妳昨天數到了。", who=HOLE, face="預設",
              title="他請假的理由", x=wx, y=-200)
b.link(b.prev, w_yes, "right", cond={"variable": "connected", "op": "eq", "value": 1})
b.chain([
    ("d5m-w1", "數到什麼？", "發呆", G),
    ("d5m-w2", "黑洞先生沒有再說一次。黑洞先生知道她今天已經沒有昨天了。", "平常", None),
    ("d5m-w3", "她翻開守則本，昨天那一頁上是她自己的字。她看著看著，手停住了。", "平常", None),
    ("d5m-w4", "……門邊那疊靴子。是我寫的。我昨天寫了這個。", "發呆", G),
    ("d5m-w5", "黑洞先生今天沒有出門。門邊那疊今天不會再變高。", "平常", None),
], x=wx + 300, y=-200, link_prev=False)
b.link(w_yes, b.find("d5m-w1")["id"])
w_end = b.prev
w_no = b.say("d5m-why-no", "黑洞先生沒有再說話。", who=None, title="他不說", x=wx, y=100)
b.link(b.prev if False else b.find("d5m-why")["id"], w_no)
j5 = b.say("d5m-why-join", "一隻觸手慢慢縮進西裝下襬。", who=None, title="接著",
           x=wx + 1800, y=0)
b.link(w_end, j5); b.link(w_no, j5)
b.prev = j5
cur = b.setvar("d5m-shrink", [{"variable": "holeFeet", "kind": "add", "value": -1},
                              {"variable": "fedToday", "kind": "set", "value": 0}],
               text="剩 {{holeFeet}} 隻。", title="他縮了一隻")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d5m-hungry","你剛才多一隻，現在少一隻。你在餓。", "平常", G),
    ("d5m-nvm",   "不用管。", "預設", HOLE),
    ("d5m-book",  "她坐起來，翻開枕頭底下的守則本。第 {{ruleVersion}} 版的最後一行是昨天的自己寫的。", "平常", None),
    ("d5m-line",  "{{ruleLine4}}", "平常", None),
    ("d5m-when",  "昨天的我寫了這句。我不記得為什麼要寫。", "發呆", G),
    ("d5m-clear", "「為什麼我每天都會知道一些事？隔天醒來全部清空。只剩守則上這幾行字。」", "發呆", G),
    ("d5m-eye",   "黑洞先生睜開一隻眼睛。看了她一下，又閉上。", "平常", None),
    ("d5m-fridge","她走去冰箱，手放在門把上。", "平常", None),
    ("d5m-dont",  "不用開。", "預設", HOLE),
    ("d5m-hand",  "她的手停在門把上，過了三秒才放下來。她沒有問為什麼。她也不知道自己為什麼沒有問。", "平常", None),
    ("d5m-run",   "好。我不問了。先把開機流程跑完。", "平常", G),
    ("d5m-low",   "系統回傳「環境異常，最低功耗運行」。她看了一眼那行字，沒有關掉。", "平常", None),
])

# ══════════ 中 ══════════
cur = b.scene("d5n-scene", "第五天・中午", "太陽移到房間正中間。他坐在光線邊緣，像一截沒有移動過的影子。", "中")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d5n-normal", "平常這個時候黑洞先生在上班。她會拿到一件東西，大聲跟玩家商量。然後選要留、要餵、要交給你保管。", "平常", None),
    ("d5n-low",    "今天她坐在床沿，聲音壓得很低。", "平常", None),
    ("d5n-there",  "你還在嗎。", "平常", G),
    ("d5n-none",   "今天的流程跑不了。沒有東西要分類，沒有東西要餵他，沒有東西要交給你保管。", "平常", G),
    ("d5n-empty",  "可是我有一整個中午。他在那裡，我在這裡，四千多個位元全空著，我不知道要裝什麼。", "發呆", G),
    ("d5n-three",  "有三件事我每天都想問。他一出門我就忘了要問，等他晚上回來，我又想不起來白天的衝動。", "平常", G),
    ("d5n-today",  "今天他哪裡都不去。我也哪裡都不去。", "平常", G),
    ("d5n-pick",   "你幫我挑一件事。我只有一個中午。", "平常", G),
])
q = b.choice("d5n-q", "這個中午她只做一件事。你要她做什麼？",
             ["去數門邊的靴子（他昨天叫她不要數）",
              "問他「以前」是什麼時候",
              "什麼都不做，就坐在原地"])
b.link(b.prev, q)

nx = b.col()
# ── 選擇一：數靴子 ──
a1 = b.chain([
    ("d5n-a1-go",  "她下了床，赤腳走過去。門邊那疊短靴整整齊齊靠著牆。她蹲下來。", "平常", None),
    ("d5n-a1-cnt", "一、二、三、四、五、六、七、八。", "平常", G),
    ("d5n-a1-see", "八雙。裂痕從第二雙蔓延到第三雙，第四雙的鞋底磨平了一半。", "平常", None),
    ("d5n-a1-but", "八雙。可是你今天只有 {{holeFeet}} 隻。", "平常", G),
    ("d5n-a1-turn","她回頭。他睜開了眼睛。", "平常", None),
    ("d5n-a1-say", "妳每天都會數。", "預設", HOLE),
    ("d5n-a1-froz","她愣住了。", "平常", None),
    ("d5n-a1-ev",  "每天——", "當機", G),
    ("d5n-a1-all", "每天都數。每天我都說。每天妳都忘。", "預設", HOLE),
    ("d5n-a1-eyes","黑洞先生的眼睛裡沒有情緒。像在看一件重複了幾百次的例行公事。", "平常", None),
    ("d5n-a1-how", "幾百次？", "發呆", G),
    ("d5n-a1-tap", "黑洞先生閉上眼。一隻觸手輕拍地板。沒有回答。", "平常", None),
], x=nx, y=-460, link_prev=False)
mark_a1 = b.setvar("d5n-mark-a1", [{"variable": "todayRoute", "kind": "set", "value": "d5-a1"}], text="", title="記下今天挑了哪一道", x=nx - 150, y={"a1": -460, "a2": 0, "a3": 420}["a1"])
b.link(q, mark_a1, "choice-0"); b.link(mark_a1, a1[0])

# ── 選擇二：問「以前」 ──
a2 = b.chain([
    ("d5n-a2-sit", "她沒有起身。她看著角落那截西裝的輪廓，深吸一口氣。", "平常", None),
    ("d5n-a2-ask", "黑洞先生。你說過我以前烤過麵包。", "平常", G),
    ("d5n-a2-when","「以前」是什麼時候？", "平常", G),
    ("d5n-a2-wait","黑洞先生沒有動。房間裡只有她的呼吸聲和窗外偶爾經過的車聲。一分鐘。兩分鐘。她的四千多個位元被沉默填滿，一個一個亮起來又滅掉。", "平常", None),
    ("d5n-a2-ans", "每一天。", "預設", HOLE),
    ("d5n-a2-open","她張開嘴。", "平常", None),
    ("d5n-a2-me",  "每一天我都烤過？", "當機", G),
    ("d5n-a2-you", "每一天妳都問。每一天妳都忘。", "預設", HOLE),
    ("d5n-a2-hold","格莉奇站在原地，走不動。格莉奇想哭，但她不知道自己在為什麼難過。那個理由不在她這裡。", "發呆", None),
], x=nx, y=0, link_prev=False)
mark_a2 = b.setvar("d5n-mark-a2", [{"variable": "todayRoute", "kind": "set", "value": "d5-a2"}], text="", title="記下今天挑了哪一道", x=nx - 150, y={"a1": -460, "a2": 0, "a3": 420}["a2"])
b.link(q, mark_a2, "choice-1"); b.link(mark_a2, a2[0])

# ── 選擇三：什麼都不做 ──
a3 = b.chain([
    ("d5n-a3-sit", "她把膝蓋抱得更緊，下巴擱在膝蓋上，看著角落的方向。", "平常", None),
    ("d5n-a3-time","五分鐘。十分鐘。陽光從房間中間移到她的腳邊。", "平常", None),
    ("d5n-a3-qui", "黑洞先生坐在那裡。她坐在這裡。中間隔著整個房間，沒有人說話。", "平常", None),
    ("d5n-a3-new", "半小時後，他的西裝下襬動了一下。一隻新的觸手慢慢伸出來，穿著一雙她沒見過的短靴。", "平常", None),
], x=nx, y=420, link_prev=False)
mark_a3 = b.setvar("d5n-mark-a3", [{"variable": "todayRoute", "kind": "set", "value": "d5-a3"}], text="", title="記下今天挑了哪一道", x=nx - 150, y={"a1": -460, "a2": 0, "a3": 420}["a3"])
b.link(q, mark_a3, "choice-2"); b.link(mark_a3, a3[0])
grow = b.setvar("d5n-a3-grow", [{"variable": "holeFeet", "kind": "add", "value": 1}],
                text="{{holeFeet}} 隻了。", title="他長了一隻", x=nx + 380, y=420)
b.link(a3[-1], grow)
a3b = b.chain([
    ("d5n-a3-grew","你長了一隻。你沒有吃東西。你吃了什麼？", "平常", G),
    ("d5n-a3-noon","下午。", "預設", HOLE),
    ("d5n-a3-hole","她把這個字含在嘴裡。她覺得腦中空掉了一小塊，說不上來是什麼。那塊空缺沒有名字，也沒有形狀。只是一個本來填著東西的位元突然滅了。", "發呆", None),
    ("d5n-a3-ate", "你把下午吃掉了。", "發呆", G),
    ("d5n-a3-deny","黑洞先生沒有否認。", "平常", None),
], x=nx + 700, y=420, link_prev=False)
b.link(grow, a3b[0])

# ══════════ 晚 ══════════
ex = b.col()
ev = b.scene("d5e-scene", "第五天・傍晚", "太陽下山了。房間暗下來。他還坐在角落。", "晚", x=ex, y=0)
for tail in (a1[-1], a2[-1], a3b[-1]): b.link(tail, ev)
b.prev = ev
b.chain([
    ("d5e-noback","黑洞先生沒有出門，也就沒有回來。晚上的流程跟其他天一樣卡住了。", "平常", None),
    ("d5e-allday","你今天整天都在。", "平常", G),
    ("d5e-mm",    "嗯。", "預設", HOLE),
    ("d5e-night", "晚上你要睡嗎？你平常下班回來會做什麼？我忘了，我每天早上都會忘。", "平常", G),
    ("d5e-pause", "黑洞先生沉默了一下。", "平常", None),
    ("d5e-watch", "看妳睡。", "預設", HOLE),
    ("d5e-what",  "看著我睡？", "當機", G),
    ("d5e-mm2",   "嗯。", "預設", HOLE),
    ("d5e-pen",   "她翻開守則本，拿筆。筆尖懸在紙上很久。", "平常", None),
    ("d5e-blank", "我不知道要寫什麼。平常我寫今天發生了什麼、明天要注意什麼。今天什麼都沒有分類。", "發呆", G),
    ("d5e-full",  "可是今天比哪一天都滿。", "平常", G),
    # 中午那一拳要有人接。她把筆遞過去 —— 這也是 Day 6 那張空白頁的來歷。
    ("d5e-turn",  "她把筆轉過來，遞向角落。", "平常", None),
    ("d5e-askw",  "你寫。你記得住，我記不住。你把今天寫下來，明天我就能讀到。", "平常", G),
    ("d5e-took",  "黑洞先生伸出一隻觸手，接過了筆。他握筆的方式不太對，像沒握過。", "平常", None),
    ("d5e-hold",  "筆尖停在紙上。停了很久。墨在紙上暈開一個小點。", "平常", None),
    ("d5e-nothing","黑洞先生把筆還給她。那一頁還是空的。", "平常", None),
    ("d5e-cant",  "你寫不出來？", "發呆", G),
    ("d5e-idk",   "我不知道要寫什麼。", "預設", HOLE),
    ("d5e-same",  "她愣了一下。那句話跟她剛剛說的一模一樣。", "平常", None),
    ("d5e-both",  "……我們兩個都不知道要寫什麼。那今天算什麼？", "發呆", G),
    ("d5e-nore2", "黑洞先生沒有回答。他把那頁翻過去，壓平，然後把本子推回她手上。", "平常", None),
])

# 守則的建議句依中午挑的那道傷口不同
rx = b.col()
INS = [
    ("a1", "黑洞先生說我每天都會數。幾百次。",
     ["門邊有八雙靴子，裂痕在蔓延。", "他說我每天都數。這句是第幾次寫了？", "明天不要數了。"]),
    ("a2", "黑洞先生說每一天我都問。每一天我都忘。",
     ["我以前烤過麵包。以前是每一天。", "問過了。答案我留不住。", "不要再問「以前」。"]),
    ("a3", "黑洞先生把下午吃掉了。我腦裡少了一塊，我不知道那塊是什麼。",
     ["他不吃東西也會長腳。", "不要跟他一起坐一整個下午。", "今天什麼都沒發生，可是我很累。"]),
]
ins_nodes = []
for i, (tag, lead, sug) in enumerate(INS):
    y = (i - 1) * 320
    n1 = b.say(f"d5e-lead-{tag}", lead, who=G, face="平常", title=f"守則引子（{tag}）", x=rx, y=y)
    n2 = b.add(f"d5e-in-{tag}", {"type": "input", "title": f"填空位（{tag}）",
        "text": "空位在這裡。今天要留什麼給明天的我？",
        "inputVariable": "ruleLine5", "inputPlaceholder": "寫一句話…",
        "inputSuggestions": sug}, x=rx + 320, y=y)
    b.link(n1, n2)
    ins_nodes.append((n1, n2))
b.link(b.prev, ins_nodes[0][0], "right", cond={"variable": "todayRoute", "op": "eq", "value": "d5-a1"})
b.link(b.prev, ins_nodes[1][0], "right", cond={"variable": "todayRoute", "op": "eq", "value": "d5-a2"})
b.link(b.prev, ins_nodes[2][0])

cur = b.setvar("d5e-rulever", [{"variable": "ruleVersion", "kind": "add", "value": 1},
                               {"variable": "dayCount", "kind": "set", "value": 5}],
               text="她寫上去。第 {{ruleVersion}} 版，完成。", title="守則 +1", x=rx + 700, y=0)
for _, n2 in ins_nodes: b.link(n2, cur)
b.prev = cur
b.chain([
    ("d5e-save",  "記得存檔。今天沒有東西可以交給你保管，只有這一句。", "平常", G),
    ("d5e-lie",   "她躺下來。角落那截影子沒有動。她閉上眼睛之前，最後看到的是他還睜著的那隻眼睛。", "平常", None),
])
b.link(b.prev, b.jump("d5e-jump", "board-day6", "d6m-scene"))
b.push("Day 5 他請假:中午沒有東西可以分類,改成挑一道傷口揭開;守則建議句依選擇不同")
