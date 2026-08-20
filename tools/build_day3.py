#!/usr/bin/env python3
"""Day 3・麵包 —— 高潮物件登場。

開場刻意打斷開機流程:她已經站在冰箱前拿著麵包了,「逼——嗶」在看到麵包之後
才響。前兩天都是「開機→自我介紹→他出門」,第三天起每天要用不同方式進場。

**晚上會依中午的選擇分三個版本演。** 五家會審裡有四家指出原本的版本「晚上對
中午的選擇零反應」——不管餵了、留了、還是交出去,他回來都是同一套台詞,中午
那個三選一在當天完全沒有迴響,玩家會覺得選了也沒用。

台詞已套代名詞規則(妳=格莉奇／你=玩家／中午段他不在畫面上一律用全名),
改動直接寫在這裡,不要只改線上版——重建會蓋回去,這個虧吃過兩次。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE, A

b = Board("board-day3", "Day 3・麵包",
          "早：從冰箱開始，開機聲在看到麵包之後才響　中：她研究保鮮膜　晚：依中午的選擇演三個版本")

# ══════════ 早 ══════════
b.prev = b.scene("d3m-scene", "第三天・清晨", "冰箱門沒關緊，透出一條光。",
                 "早", bgm=A["bgm-theme"], start=True)
b.chain([
    ("d3m-stand", "她站在冰箱前面，手裡拿著一塊用保鮮膜包好的麵包。她不記得自己是怎麼走過來的。", "平常", None),
    ("d3m-boot",  "……逼——嗶！", "當機", G),
    ("d3m-late",  "喔。我開機了。剛剛那是誰在動？", "發呆", G),
    ("d3m-note",  "保鮮膜上貼著一張紙條。「給黑洞先生。」是我的字。", "平常", G),
    ("d3m-hands", "我的手記得怎麼包保鮮膜，可是我的腦不記得為什麼要包。", "發呆", G),
    ("d3m-ask",   "黑洞先生，這是我做的嗎？", "平常", G),
    ("d3m-reply", "是妳的字。", "預設", HOLE),
    ("d3m-when",  "那什麼時候做的？", "平常", G),
    ("d3m-silent","黑洞先生沒有回答。他把西裝拉平，出門了。", "平常", None),
    ("d3m-feet",  "門邊那疊沒人穿的短靴，今天的高度對得上他身上 {{holeFeet}} 隻腳。她沒有數，她從來不數。", "平常", None),
])

# ══════════ 中 ══════════
cur = b.scene("d3n-scene", "第三天・中午", "太陽爬到窗戶正上方。麵包放在桌子中間，保鮮膜反著光。", "中")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d3n-look",  "我把它翻來翻去看了很久。保鮮膜包得很仔細——先對折兩次，再從中間往外壓。那是我會做的方式。", "平常", G),
    ("d3n-smell", "我聞了一下。身體有反應。像是很久沒做，可是手還記得。", "發呆", G),
    ("d3n-logic", "問題來了。如果我忘了它在哪，黑洞先生就會把它當成沒人要的東西吃掉，然後長回一隻腳。", "平常", G),
    ("d3n-logic2","可是如果我記得——那這塊麵包到底是要給誰的？", "發呆", G),
])
b.route("d3n-bread", None,
        "「冰箱裡有麵包」這件事，你幫我決定。", "平常",
        "「冰箱裡有一塊我做的麵包」這件事，要放哪裡？",
        "她把麵包放回冰箱，把「它在那裡」記在自己的記憶體裡。明天她會忘，然後它就變成一塊沒有人記得的麵包。",
        "她把「冰箱裡有麵包」這件事交給黑洞先生。麵包本身還在冰箱，可是明天沒有人會想起去開那扇門。",
        "她把麵包舉起來給你看，讓你看清楚保鮮膜的折法。「你幫我記著它在冰箱。明天問我。」",
        "好。那我們等黑洞先生回來。",
        extra_keep=[{"variable": "breadState", "kind": "set", "value": "self"}],
        extra_feed=[{"variable": "breadState", "kind": "set", "value": "hole"}],
        extra_give=[{"variable": "breadState", "kind": "set", "value": "player"}])

# ══════════ 晚:依中午的選擇分三個版本 ══════════
cur = b.scene("d3e-scene", "第三天・深夜", "城市的燈熄了大半。螢幕和桌燈是房間裡僅剩的光。", "晚")
b.link(b.prev, cur); b.prev = cur
back = b.say("d3e-back", "我回來了。", who=HOLE, face="預設")
b.link(b.prev, back)

# 三條支線各自演一個「當晚就看得到」的細節,讓中午的選擇當天結清
ex = b.col()
r_hole = b.say("d3e-r-hole",
    "黑洞先生掛外套的時候，她發現他少穿了一隻短靴。門邊那疊今天多出一雙。她沒有數，她從來不數。",
    who=None, title="他吃掉了", x=ex, y=-260)
r_self = b.say("d3e-r-self",
    "她經過冰箱的時候停了三秒，盯著門把看。她自己也不知道在看什麼。明天她不會記得這個動作。",
    who=None, title="她留著", x=ex, y=0)
r_play = b.say("d3e-r-player",
    "她把保鮮膜的折法又演了一遍給你看。先對折兩次，再從中間往外壓。像是在確認你真的記住了。",
    who=None, title="交給你了", x=ex, y=260)
b.link(back, r_hole, "right", cond={"variable": "breadState", "op": "eq", "value": "hole"})
b.link(back, r_self, "right", cond={"variable": "breadState", "op": "eq", "value": "self"})
b.link(back, r_play)
join = b.say("d3e-join", "……", who=None, title="匯合", x=ex + 300, y=0)
for r in (r_hole, r_self, r_play): b.link(r, join)
b.prev = join

b.chain([
    ("d3e-push",  "黑洞先生。那塊麵包。知道我什麼時候做的吧。", "平常", G),
    ("d3e-past",  "妳以前烤過。", "預設", HOLE),
    ("d3e-push2", "「以前」是什麼時候？", "平常", G),
    ("d3e-quiet", "黑洞先生把外套掛好。這個問題他沒有接。", "平常", None),
    ("d3e-you",   "黑洞先生每次都說「以前」。到底知道多少我不記得的事？", "發呆", G),
    ("d3e-none",  "他還是沒有回答。", "平常", None),
    ("d3e-rule",  "算了。填守則。第 {{ruleVersion}} 版。", "平常", G),
])
cur = b.add("d3e-rulein", {"type": "input", "title": "填空位",
    "text": "空位在這裡。今天要留什麼給明天的我？",
    "inputVariable": "ruleLine3", "inputPlaceholder": "寫一句話…",
    "inputSuggestions": ["冰箱裡有東西。", "問黑洞先生「以前」是什麼時候。", "我的手比我的腦記得多。"]})
b.link(b.prev, cur); b.prev = cur
cur = b.setvar("d3e-rulever", [{"variable": "ruleVersion", "kind": "add", "value": 1},
                               {"variable": "dayCount", "kind": "set", "value": 3}],
               text="她寫上去。第 {{ruleVersion}} 版，完成。", title="守則 +1")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d3e-save",  "記得存檔。不然明天我又要重新認識你。", "平常", G),
    ("d3e-sleep", "她躺回床上。螢幕的光慢慢暗下去。", "平常", None),
])
b.link(b.prev, b.jump("d3e-jump", "board-day4", "d4m-scene"))
b.push("Day 3 晚上依中午的選擇分三個版本演,中午的三選一當天就結清")
