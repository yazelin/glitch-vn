"""Day 2・遊戲實況。玩家做的事是指路，不是補記憶。

守則本在這一天第一次真的執行：她翻開，唸出玩家昨天寫的那句，然後照做。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from daykit import Board, G, HOLE

b = Board("board-v2-day2", "新一・第二天：遊戲實況", "指路。指錯她會死，而她不知道自己死過幾次。")

b.scene("d2-open", "第二天・開播前", "直播室的倒數顯示 12:00。桌上攤著守則本。", "早", start=True)
b.prev = "d2-open"
# 這一天的玩法是指路，搶答只給一次——洞也只有一個。
w = b.wake("d2", day=2)
b.link("d2-open", w); b.prev = w
b.addops(w, [{"variable": "savesLeft", "kind": "set", "value": 1},
             {"variable": "savedCount", "kind": "set", "value": 0},
             {"variable": "settleAt", "kind": "set", "value": 0},
             {"variable": "deaths", "kind": "set", "value": 0}])

b.chain([
 ("d2-p1", "唔……早。", "睡著", G),
 ("d2-p2", "我今天要做什麼來著。", "發呆", G),
 ("d2-p3", "她翻開守則本，翻到最新的那一頁。", "平常", "旁白"),
 ("d2-p4", "「{{ruleLine1}}」", "平常", G),
 ("d2-p5", "喔。好喔。", "開心", G),
 ("d2-p6", "她沒有問為什麼。她照著做了。", "平常", "旁白"),
])

sc = b.scene("d2-live", "第二天・直播中", "留言區開了。", "中")
b.link(b.prev, sc); b.prev = sc
b.chain([
 ("d2-l1", "逼——嗶！大家好，我是格莉奇！", "當機", G),
 ("d2-l2", "今天要玩遊戲！超老的那種！", "開心", G),
 ("d2-l3", "我先說喔，我很會玩。", "開心", G),
 ("d2-l4", "她死了。開場十四秒。", "平常", "旁白"),
 ("d2-l5", "……剛剛那個不算。", "當機", G),
])


def fork(key, ask, right, wrong_text, right_text, quiet_text, y=0):
    """一個岔路。指對走出去，指錯她掉下去，不出聲她自己選。"""
    a = b.say(f"{key}-ask", ask, face="平常")
    b.link(b.prev, a)
    c = b.choice(f"{key}-q", "你要指哪一邊？", ["左邊", "右邊", "不出聲"])
    b.link(a, c)
    x = b.col()
    ok = b.say(f"{key}-ok", right_text, face="開心", x=x, y=y - 200)
    bad = b.setvar(f"{key}-bad", [{"variable": "deaths", "kind": "add", "value": 1}],
                   text=wrong_text, title="她死了", x=x, y=y)
    qt = b.say(f"{key}-quiet", quiet_text, who="旁白", x=x, y=y + 200)
    b.link(c, ok if right == 0 else bad, "choice-0")
    b.link(c, bad if right == 0 else ok, "choice-1")
    b.link(c, qt, "choice-2")
    end = b.setvar(f"{key}-end", [], text="", title="接回主線", x=x + 300, y=y)
    for n in (ok, bad, qt): b.link(n, end)
    b.prev = end
    return end


fork("d2-f1", "畫面上是一個岔路。左邊和右邊看起來一模一樣。\n"
              "欸，左邊還右邊？大家幫我決定，我照做。", 0,
     "走右邊！\n\n（地板不見了。）\n哇啊啊啊——",
     "走左邊！\n\n（她走出去了。）\n欸嘿，我就說我很會玩吧。",
     "她自己選了一邊。這一次她運氣不錯。")

b.chain([
 ("d2-s1", "畫面跳回存檔點。她坐在同一塊石頭上，跟三分鐘前一模一樣。", "平常", "旁白"),
 ("d2-s2", "咦。\n我剛剛是不是死過？", "發呆", G),
])
b.chat("d2-s3", ["小夜：你死了 {{deaths}} 次", "阿明：你死超慘", "路人：哈哈哈哈哈"])
b.link(b.prev, "d2-s3"); b.prev = "d2-s3"
b.chain([
 ("d2-s4", "{{deaths}} 次？不可能，我明明只死一次。", "當機", G),
 ("d2-s5", "她笑著站起來，往同一個岔路走過去。", "平常", "旁白"),
 ("d2-s6", "走得比上一次還開心。", "平常", "旁白"),
])

fork("d2-f2", "欸，左邊還右邊？", 1,
     "走左邊！\n\n（地板不見了。）\n哇啊啊啊——",
     "走右邊！\n\n（她走出去了。）\n你看吧，我第一次就過了。",
     "她自己選了一邊。這一次沒有那麼好運。")

# 這一天她真正卡住的只有一次，可是一天不會只留下一件事。
# 沒有這兩個，晚上四格只填得到一格，結算就變成點空白。
p1 = b.setvar("d2-k1", [{"variable": "pending", "kind": "set", "value": "我今天死了好幾次"}],
              text="", title="記下來")
b.link(b.prev, p1)
g1, o1 = b.store("d2-mk1", "有一格自己掉出去了，她沒有發現。", x=b.col(), y=-700)
b.link(p1, g1)
j1 = b.setvar("d2-k1-end", [], text="", title="接回主線", x=b.col(), y=0)
for o in o1: b.link(o, j1)
b.prev = j1

b.chain([
 ("d2-u1", "欸，這個東西是什麼？", "發呆", G),
 ("d2-u2", "畫面上跳出遊戲的存檔介面。上面有一整排格子，每一格寫著時間。", "平常", "旁白"),
 ("d2-u3", "喔——這個是存檔喔。", "平常", G),
 ("d2-u4", "這個好方便喔。", "開心", G),
 ("d2-u5", "我也想要一個。", "開心", G),
 ("d2-u6", "留言區安靜了兩秒，然後開始刷「你有啊」。", "平常", "旁白"),
 ("d2-u7", "我有嗎？", "發呆", G),
])
p2 = b.setvar("d2-k2", [{"variable": "pending", "kind": "set", "value": "遊戲會幫你記住走到哪裡"}],
              text="", title="記下來")
b.link(b.prev, p2)
g2, o2 = b.store("d2-mk2", "有一格自己掉出去了，她沒有發現。", x=b.col(), y=-700)
b.link(p2, g2)
j2 = b.setvar("d2-k2-end", [], text="", title="接回主線", x=b.col(), y=0)
for o in o2: b.link(o, j2)
b.prev = j2


def mem(key, gate, outs, end):
    b.unlink(f"{key}-after-hit", f"{key}-end")
    b.link(f"{key}-after-hit", gate)
    for o in outs: b.link(o, end)


end1, hit1 = b.hole(
 "d2-h1", "大魔王站在畫面中間。她打了三分鐘，血條沒有動。\n"
          "打不過欸。這個到底要怎麼打。\n系統讀取中……",
 ["小夜：打頭", "阿明：打腳", "路人B：不要打，用跑的"],
 "打腳",
 "{{name}} 說要打腳！\n腳？好喔。\n\n（血條掉了一整條。）\n"
 "欸欸欸真的耶！{{name}} 你怎麼知道！",
 "她照著留言區試了七種打法。七種都不對。\n"
 "算了，這個王我們下次再打。反正下次我也不會記得打過。\n"
 "（她說完自己笑了。留言區沒有人笑。）",
 ops_hit=[{"variable": "pending", "kind": "set", "value": "打那個王要打腳"}])
st1, outs1 = b.store("d2-m1", "她說到一半停住了。有一格自己掉出去了，她沒有發現。",
                     x=b.col(), y=-700)
mem("d2-h1", st1, outs1, end1)
b.prev = end1

b.chain([
 ("d2-e1", "好啦今天就到這裡！", "開心", G),
 ("d2-e2", "今天我學到——{{slot1}}、{{slot2}}、{{slot3}}、{{slot4}}。", "平常", G),
 ("d2-e3", "掰掰！", "開心", G),
])

sc2 = b.scene("d2-off", "第二天・下播後", "鏡頭朝著天花板。留言區關了。麥克風還開著。", "晚")
b.link(b.prev, sc2); b.prev = sc2
b.chain([
 ("d2-o1", "門開了。外套被掛起來。", "平常", "旁白"),
 ("d2-o2", "今天玩什麼？", "餓", HOLE),
 ("d2-o3", "玩遊戲啊！超好玩的！", "開心", G),
 ("d2-o4", "哪一個？", "餓", HOLE),
 ("d2-o5", "就……那個啊。\n那個有大魔王的。", "發呆", G),
 ("d2-o6", "妳昨天也玩那個。", "餓", HOLE),
 ("d2-o7", "安靜了三秒。", "平常", "旁白"),
 ("d2-o8", "……喔。", "發呆", G),
 ("d2-o9", "天花板亮了一下。", "平常", "旁白"),
 ("d2-o10", "你的私訊還通。", "平常", "旁白"),
 ("d2-o11", "「你今天死了 {{deaths}} 次。」", "平常", G),
 ("d2-o12", "欸！{{deaths}} 次！\n我怎麼都不記得。", "當機", G),
 ("d2-o13", "那不重要。", "飽", HOLE),
 ("d2-o14", "……也是啦。", "平常", G),
])

before = b.prev
s_in, s_out = b.settle("d2-set", x=b.col(), y=-400)
b.link(before, s_in); b.prev = s_out

rv = b.setvar("d2-rv", [{"variable": "ruleVersion", "kind": "set", "value": 2}],
              text="守則本翻開。", title="守則本第二版")
b.link(b.prev, rv)
ri = b.add("d2-rule", {"type": "input", "title": "今天要留什麼給明天的她？",
                       "text": "明天早上她會翻開守則本，唸出這一句，然後照做。",
                       "inputVariable": "ruleLine2",
                       "inputPlaceholder": "寫一句給明天的她"})
b.link(rv, ri); b.prev = ri
b.chain([
 ("d2-r1", "{{name}}，記得存檔喔。", "平常", G),
 ("d2-r2", "……", "發呆", G),
 ("d2-r3", "欸，我的存檔在哪裡啊？", "發呆", G),
 ("d2-r4", "燈關了。", "平常", "旁白"),
 ("d2-r5", "天花板亮了一下。", "平常", "旁白"),
])
b.link(b.prev, b.jump("d2-fin", "board-v2-day3", "d3-open", text="天亮了。"))

b.push("新一・第二天（VTuber 前提）")
