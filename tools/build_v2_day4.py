"""Day 4・讀粉絲來信。玩家做的事是真的打一封信。

記憶考在這一天：她唸到你保管的那件事，然後問你那是什麼時候的事。
答錯她照樣相信——從今天起那件事在她那裡就是錯的那一天。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from daykit import Board, G, HOLE

b = Board("board-v2-day4", "新一・第四天：讀粉絲來信", "寫信。她唸出你寫的，可是不記得那件事。")

b.scene("d4-open", "第四天・開播前", "直播室的倒數顯示 20:00。桌上堆著一疊信。", "早", start=True)
b.prev = "d4-open"
w = b.wake("d4", day=4, prefill=["今天要讀大家的信"])
b.link("d4-open", w); b.prev = w
b.addops(w, [{"variable": "savesLeft", "kind": "set", "value": 2},
             {"variable": "savedCount", "kind": "set", "value": 0},
             {"variable": "settleAt", "kind": "set", "value": 0}])

b.chain([
 ("d4-p1", "她翻開守則本，唸出昨天那一句：「{{ruleLine3}}」", "平常", "旁白"),
 ("d4-p2", "喔。好喔。", "開心", G),
 ("d4-p3", "哇，好多喔。", "開心", G),
 ("d4-p4", "這些都是寫給我的？", "開心", G),
 ("d4-p5", "她拿起最上面那一封，看了三秒，放回去。", "平常", "旁白"),
 ("d4-p6", "等一下再看。等一下比較有感覺。", "平常", G),
])

sc = b.scene("d4-live", "第四天・直播中", "留言區開了。", "中")
b.link(b.prev, sc); b.prev = sc
b.chain([
 ("d4-l1", "逼——嗶！大家好，我是格莉奇！", "當機", G),
 ("d4-l2", "今天讀信！大家寫給我的信！", "開心", G),
 ("d4-l3", "現在寫也來得及喔，我等你們。", "開心", G),
])
inp = b.add("d4-letter", {"type": "input", "title": "你要寫什麼給她？",
                          "text": "她在等。如果你有幫她記著什麼，可以寫那一件。",
                          "inputVariable": "letter",
                          "inputPlaceholder": "寫一封信給她"})
b.link(b.prev, inp); b.prev = inp

b.chain([
 ("d4-r1", "第一封。小夜寫的。", "平常", G),
 ("d4-r2", "「格莉奇你昨天唱歌很好聽，可是你音準有一段掉了。」", "平常", G),
 ("d4-r3", "欸——！小夜你不要講出來啦！", "當機", G),
 ("d4-r4", "下一封！", "開心", G),
 ("d4-r5", "喔，這一封是 {{name}} 寫的。", "開心", G),
 ("d4-r6", "{{name}} 我認識！每天都在！", "開心", G),
 ("d4-r7", "她的天線轉了一圈。", "平常", "旁白"),
 ("d4-r8", "「{{letter}}」", "平常", G),
])

# 有沒有保管過東西，這一段完全不一樣
gate = b.setvar("d4-gate", [], text="", title="她有沒有東西可以被提醒")
b.link(b.prev, gate)
x = b.col()

# 有保管
q1 = b.say("d4-k1", "她停住了。", who="旁白", x=x, y=-400)
b.link(gate, q1, "right", cond={"variable": "keptCount", "op": "gte", "value": 1})
k = b.chain([
 ("d4-k2", "{{kept1}}……", "發呆", G),
 ("d4-k3", "這個我完全沒印象欸。", "發呆", G),
 ("d4-k4", "可是你寫得好詳細喔。", "平常", G),
 ("d4-k5", "連我那天穿什麼都寫了。", "平常", G),
 ("d4-k6", "{{name}}，你可以告訴我這是什麼時候的事嗎？", "平常", G),
], y=-400, x=x + 300, link_prev=False)
b.link(q1, k[0])

quiz = b.choice("d4-quiz", "你要說哪一天？",
                ["第一天", "第二天", "第三天", "我也不記得了"], x=x + 2200, y=-400)
b.link(k[-1], quiz)
qx = x + 2500
ok = b.setvar("d4-ok", [{"variable": "pending", "kind": "set", "valueFrom": "kept1"}],
              text="那我那天就是有做這件事囉？\n好，那我記回來。\n"
                   "欸嘿，我的記憶體真的很好用。",
              title="答對", x=qx, y=-700)
no = b.setvar("d4-no", [{"variable": "pending", "kind": "set", "valueFrom": "kept1"}],
              text="喔——原來是那天。\n好，那我記回來。\n\n"
                   "（她沒有懷疑。她一點懷疑都沒有。）\n"
                   "（從今天起，這件事在她那裡就是那一天發生的。）",
              title="答錯", x=qx, y=-450)
dunno = b.say("d4-dunno", "喔……那就算了。\n反正我也不記得。\n\n"
                          "（她把信折起來，放到旁邊那一疊。）",
              face="平常", x=qx, y=-200)
for i in range(3):
    b.link(quiz, ok, f"choice-{i}",
           cond={"variable": "keptFrom1", "op": "eq", "value": i + 1})
    b.link(quiz, no, f"choice-{i}")
b.link(quiz, dunno, "choice-3")
g1, o1 = b.store("d4-m1", "有一格自己掉出去了，她沒有發現。", x=qx + 400, y=-1100)
b.link(ok, g1); b.link(no, g1)

# 沒保管過
q2 = b.chain([
 ("d4-z1", "喔喔喔謝謝！", "開心", G),
 ("d4-z2", "不過你都不跟我講以前的事欸。", "平常", G),
 ("d4-z3", "別人的信裡面都會寫「你上次怎樣怎樣」。", "平常", G),
 ("d4-z4", "你的信裡面只有今天。", "發呆", G),
 ("d4-z5", "她說完就唸下一封了。", "平常", "旁白"),
], y=400, x=x, link_prev=False)
b.link(gate, q2[0])

join = b.setvar("d4-join", [], text="", title="接回主線", x=qx + 900, y=0)
for o in o1: b.link(o, join)
b.link(dunno, join)
b.link(q2[-1], join)
b.prev = join


def mem(key, gate_, outs, end):
    b.unlink(f"{key}-after-hit", f"{key}-end")
    b.link(f"{key}-after-hit", gate_)
    for o in outs: b.link(o, end)


end1, hit1 = b.hole(
 "d4-h1", "欸，我是不是應該要回信？\n我有回過嗎？",
 ["小夜：你上禮拜回過我", "阿明：沒有", "路人B：你說要回，然後就沒了"],
 "你說要回，然後就沒了",
 "……有人說我說要回，然後就沒了。\n"
 "那我今天回一封好了。\n\n（她回了一封。回給誰她沒有講。）",
 "留言區三種說法都有，她笑著說「那應該有吧」。",
 ops_hit=[{"variable": "pending", "kind": "set", "value": "我今天回了一封信"}])
g2, o2 = b.store("d4-m2", "有一格自己掉出去了，她沒有發現。", x=b.col(), y=-700)
mem("d4-h1", g2, o2, end1)
b.prev = end1

end2, hit2 = b.hole(
 "d4-h2", "還有一件事我想問。\n寫信給我的人，我是不是應該要記得他們？",
 ["小夜：你記得我就好", "阿明：不用啦", "路人B：你有記得啊"],
 "你記得他們寫過什麼就好",
 "記得他們寫過什麼就好。\n喔。那我可以。\n……應該可以。",
 "她想了很久，然後說「我盡量」。",
 ops_hit=[{"variable": "pending", "kind": "set", "value": "我要記得大家寫過什麼"}])
g3, o3 = b.store("d4-m3", "有一格自己掉出去了，她沒有發現。", x=b.col(), y=-700)
mem("d4-h2", g3, o3, end2)
b.prev = end2

b.chain([
 ("d4-e1", "好啦，今天的信讀完了。", "平常", G),
 ("d4-e2", "今天記住的東西——{{slot1}}、{{slot2}}、{{slot3}}、{{slot4}}。", "平常", G),
 ("d4-e3", "掰掰！明天要做菜喔！", "開心", G),
])

sc2 = b.scene("d4-off", "第四天・下播後", "鏡頭朝著天花板。麥克風還開著。", "晚")
b.link(b.prev, sc2); b.prev = sc2
b.chain([
 ("d4-o1", "門開了。外套被掛起來。", "平常", "旁白"),
 ("d4-o2", "今天呢？", "餓", HOLE),
 ("d4-o3", "今天讀信。", "平常", G),
 ("d4-o4", "有一個人……\n他記得我不記得的事。", "平常", G),
 ("d4-o5", "嗯。", "餓", HOLE),
 ("d4-o6", "你不覺得很奇怪嗎？", "發呆", G),
 ("d4-o7", "不會。", "飽", HOLE),
 ("d4-o8", "天花板亮了一下。", "平常", "旁白"),
 ("d4-o9", "你的私訊還通。", "平常", "旁白"),
 ("d4-o10", "「我一直都在。」", "平常", G),
 ("d4-o11", "……", "發呆", G),
 ("d4-o12", "黑洞先生，他說他一直都在。", "平常", G),
 ("d4-o13", "嗯。", "飽", HOLE),
 ("d4-o14", "那我怎麼會不記得。", "發呆", G),
 ("d4-o15", "沒有人回答。", "平常", "旁白"),
])

before = b.prev
s_in, s_out = b.settle("d4-set", x=b.col(), y=-400)
b.link(before, s_in); b.prev = s_out

rv = b.setvar("d4-rv", [{"variable": "ruleVersion", "kind": "set", "value": 4}],
              text="守則本翻開。", title="守則本第四版")
b.link(b.prev, rv)
ri = b.add("d4-rule", {"type": "input", "title": "今天要留什麼給明天的她？",
                       "text": "明天早上她會翻開守則本，唸出這一句，然後照做。",
                       "inputVariable": "ruleLine4",
                       "inputPlaceholder": "寫一句給明天的她"})
b.link(rv, ri); b.prev = ri
b.chain([
 ("d4-r9", "{{name}}，記得存檔喔。", "平常", G),
 ("d4-r10", "燈關了。", "平常", "旁白"),
 ("d4-r11", "天花板亮了一下。", "平常", "旁白"),
])
b.link(b.prev, b.jump("d4-fin", "board-v2-day5", "d5-open", text="天亮了。"))

b.push("新一・第四天（VTuber 前提）")
