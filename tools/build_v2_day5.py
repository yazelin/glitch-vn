"""Day 5・企劃：做菜。這一天玩家的留言送不出去，只能看。

只有一個地方可以動手：聊天室在猜黑洞先生是誰，而你是唯一知道的人。
這是全劇唯一一個「你能做的事只有傷害她」的選擇。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from daykit import Board, G, HOLE

b = Board("board-v2-day5", "新一・第五天：做菜", "只能看。麵包那條線在幾千人面前裂開。")

b.scene("d5-open", "第五天・開播前", "直播室的倒數顯示 30:00。桌上排著麵粉、酵母、鹽、水。", "開播前", start=True)
b.prev = "d5-open"
# 醒來就帶著兩格：四格會在這一天第一次被擠爆。
w = b.wake("d5", day=5, prefill=["今天要做菜", "烤箱不知道誰先開的"])
b.link("d5-open", w); b.prev = w
b.addops(w, [{"variable": "savesLeft", "kind": "set", "value": 0},
             {"variable": "savedCount", "kind": "set", "value": 0},
             {"variable": "settleAt", "kind": "set", "value": 0},
             {"variable": "told", "kind": "set", "value": 0}])

b.chain([
 ("d5-p1", "她翻開守則本，唸出昨天那一句：「{{ruleLine4}}」", "平常", "旁白"),
 ("d5-p2", "喔。好喔。", "開心", G),
 ("d5-p3", "今天要做菜！", "開心", G),
 ("d5-p4", "我先說喔，我沒做過。", "開心", G),
 ("d5-p5", "不過應該很簡單吧。", "開心", G),
 ("d5-p6", "她已經把烤箱預熱好了。她不記得自己什麼時候按的。", "平常", "旁白"),
])

sc = b.scene("d5-live", "第五天・直播中", "留言區開了。", "直播中")
b.link(b.prev, sc); b.prev = sc
b.chain([
 ("d5-l1", "逼——嗶！大家好，我是格莉奇！", "當機", G),
 ("d5-l2", "今天要烤麵包！人生第一次！", "開心", G),
 ("d5-l3", "她把麵粉倒進盆子。沒有量。倒完剛剛好。", "平常", "旁白"),
 ("d5-l4", "從這裡開始，你的留言送不出去。輸入框是灰的。", "平常", "旁白"),
 ("d5-l5", "她開始揉。壓、推、摺、轉。", "平常", "旁白"),
 ("d5-l6", "欸這個好好玩喔。", "開心", G),
 ("d5-l7", "食譜還在桌子的另一邊，連翻都沒有翻開。", "平常", "旁白"),
])
b.chat("d5-c1", ["小夜：你手法也太熟", "阿明：這個是新手？？", "路人：你常烤喔"])
b.link(b.prev, "d5-c1"); b.prev = "d5-c1"
b.chain([
 ("d5-l8", "沒有啊，第一次。", "開心", G),
 ("d5-l9", "麵團進烤箱。她坐在旁邊等。", "平常", "旁白"),
 ("d5-l10", "這個要等三十五分鐘。", "平常", G),
 ("d5-l11", "她說得很快，像在報一個自己背過很多次的數字。", "平常", "旁白"),
])
b.chat("d5-c2", ["小夜：你怎麼知道", "阿明：三十五分鐘欸", "路人B：好準"])
b.link(b.prev, "d5-c2"); b.prev = "d5-c2"
b.chain([
 ("d5-l12", "欸？\n……不知道耶。\n反正就是三十五分鐘。", "發呆", G),
])


def keep(key, label, note, y=-700):
    """這一天玩家插不上手，可是事情照樣發生。她記住的東西是被動進來的。"""
    p = b.setvar(f"{key}-set", [{"variable": "pending", "kind": "set", "value": label}],
                 text="", title="記下來")
    b.link(b.prev, p)
    g, outs = b.store(f"{key}-m", note, x=b.col(), y=y)
    b.link(p, g)
    j = b.setvar(f"{key}-j", [], text="", title="接回主線", x=b.col(), y=0)
    for o in outs: b.link(o, j)
    b.prev = j
    return j


keep("d5-k1", "我今天烤了麵包",
     "「等一下。」她低頭，然後抬頭，然後放棄。最舊的那一格自己掉出去了。")

b.chain([
 ("d5-l13", "三十五分鐘之後，麵包出爐了。烤得剛剛好。", "平常", "旁白"),
 ("d5-l14", "麵包放涼。保鮮膜包起來，邊角收進去，折得很仔細。", "平常", "旁白"),
 ("d5-l15", "然後她拿了一張紙條，寫字。", "平常", "旁白"),
 ("d5-l16", "鏡頭拍到那張紙條。", "平常", "旁白"),
 ("d5-l17", "上面寫著五個字：給黑洞先生。", "平常", "旁白"),
])
b.chat("d5-c3", ["小夜：黑洞先生是誰", "阿明：等等你有室友？？",
                 "路人B：他長什麼樣子", "小夜：黑洞先生是誰！！"])
b.link(b.prev, "d5-c3"); b.prev = "d5-c3"
b.chain([
 ("d5-l18", "喔，我室友啊。", "平常", G),
 ("d5-l19", "好啦下一個環節——", "開心", G),
 ("d5-l20", "她跳過去了。留言區還在刷。", "平常", "旁白"),
])

keep("d5-k2", "我在紙條上寫了給黑洞先生",
     "「等一下。」有一格自己掉出去了，她沒有發現。")

# 唯一的一個選擇
b.chain([
 ("d5-t1", "你的輸入框亮了。", "平常", "旁白"),
 ("d5-t2", "今天你只能做這一件事。", "平常", "旁白"),
 ("d5-t3", "幾千個人在猜他是誰。你是唯一知道的人。", "平常", "旁白"),
 ("d5-t4", "你知道他幾點回來。你知道他的外套內側是黑的。", "平常", "旁白"),
 ("d5-t5", "你知道她每天半夜都在烤。", "平常", "旁白"),
])
c = b.choice("d5-tell", "……", ["講出去", "不講"])
b.link(b.prev, c)
x = b.col()
tell = b.setvar("d5-told", [{"variable": "told", "kind": "set", "value": 1}],
                text="你的留言跳出來。", title="講出去", x=x, y=-250)
b.link(c, tell, "choice-0")
t2 = b.chat("d5-told-chat", ["阿明：等等這是真的嗎", "小夜：他每天半夜？？",
                            "路人：格莉奇你回答一下"], x=x + 300, y=-250)
b.link(tell, t2)
t3 = b.say("d5-told-2", "欸？\n哈哈哈哈哈這什麼啦。\n好啦我們來看麵包！麵包！",
           face="當機", x=x + 600, y=-250)
b.link(t2, t3)
t4 = b.say("d5-told-3", "她笑了很久。笑得比平常久。", who="旁白", x=x + 900, y=-250)
b.link(t3, t4)
q1 = b.say("d5-quiet", "你沒有送出去。\n留言區自己吵了一陣子，然後被別的話題蓋過去。\n"
                       "這件事還是只有你知道。", who="旁白", x=x, y=250)
b.link(c, q1, "choice-1")
j = b.setvar("d5-tj", [], text="", title="接回主線", x=x + 1200, y=0)
b.link(t4, j); b.link(q1, j)
b.prev = j

b.chat("d5-c4", ["小夜：你什麼時候烤的"])
b.link(b.prev, "d5-c4"); b.prev = "d5-c4"
b.chain([
 ("d5-l21", "剛剛啊。\n你們不是都看到了。", "平常", G),
])
b.chat("d5-c5", ["小夜：我是說以前啦", "阿明：他問的是以前"])
b.link(b.prev, "d5-c5"); b.prev = "d5-c5"
b.chain([
 ("d5-l22", "她低頭看著自己手上那塊還冒著熱氣的麵包。", "平常", "旁白"),
 ("d5-l23", "停了三秒。", "平常", "旁白"),
 ("d5-l24", "……我是不是也烤過別次？", "發呆", G),
 ("d5-l25", "沒有人回答得出來。", "平常", "旁白"),
])

keep("d5-k3", "我可能烤過很多次",
     "「等一下。」有一格自己掉出去了。這一次她盯著空的地方看了很久。")

b.chain([
 ("d5-e1", "好啦！今天就到這裡！掰掰！", "開心", G),
 ("d5-e2", "她下播下得比平常快。", "平常", "旁白"),
])

sc2 = b.scene("d5-off", "第五天・下播後", "鏡頭朝著天花板。麥克風還開著。", "下播後")
b.link(b.prev, sc2); b.prev = sc2
b.voiceonly = True   # 鏡頭朝天花板，看不到人
b.chain([
 ("d5-o1", "門開了。外套被掛起來。", "平常", "旁白"),
 ("d5-o2", "你回來啦。這個給你。", "開心", G),
 ("d5-o3", "保鮮膜的聲音。", "平常", "旁白"),
 ("d5-o4", "嗯。", "餓", HOLE),
 ("d5-o5", "外套被打開又合上。", "平常", "旁白"),
 ("d5-o6", "欸。\n我是不是常常給你這個？", "發呆", G),
 ("d5-o7", "嗯。", "飽", HOLE),
 ("d5-o8", "……常常是多常？", "發呆", G),
 ("d5-o9", "很常。", "飽", HOLE),
 ("d5-o10", "天花板亮了一下。", "平常", "旁白"),
])

# 講出去的人今天晚上會多聽到一句
g2 = b.setvar("d5-tg", [], text="", title="今天有人講出去了嗎")
b.link(b.prev, g2)
gx = b.col()
lk = b.chain([
 ("d5-o11", "今天有人知道得比妳多。", "飽", HOLE),
 ("d5-o12", "欸？誰？", "發呆", G),
 ("d5-o13", "不知道。", "飽", HOLE),
 ("d5-o14", "喔。", "平常", G),
 ("d5-o15", "她就忘了。", "平常", "旁白"),
], y=-250, x=gx, link_prev=False)
b.link(g2, lk[0], "right", cond={"variable": "told", "op": "eq", "value": 1})
jj = b.setvar("d5-tj2", [], text="", title="接回主線", x=gx + 1600, y=0)
b.link(g2, jj); b.link(lk[-1], jj)
b.prev = jj

before = b.prev
s_in, s_out = b.settle("d5-set", x=b.col(), y=-400)
b.link(before, s_in); b.prev = s_out

rv = b.setvar("d5-rv", [{"variable": "ruleVersion", "kind": "set", "value": 5}],
              text="守則本翻開。", title="守則本第五版")
b.link(b.prev, rv)
ri = b.add("d5-rule", {"type": "input", "title": "今天要留什麼給明天的她？",
                       "text": "明天早上她會翻開守則本，唸出這一句，然後照做。",
                       "inputVariable": "ruleLine5",
                       "inputPlaceholder": "寫一句給明天的她"})
b.link(rv, ri); b.prev = ri
b.chain([
 ("d5-r1", "{{name}}，記得存檔喔。", "平常", G),
 ("d5-r2", "燈關了。", "平常", "旁白"),
 ("d5-r3", "天花板亮了一下。", "平常", "旁白"),
 ("d5-r4", "又亮了一下。", "平常", "旁白"),
])
b.link(b.prev, b.jump("d5-fin", "board-v2-day6", "d6-open", text="天亮了。"))

b.push("新一・第五天（VTuber 前提）")
