"""Day 6・提示詞掛掉。全劇最高點。

她問的五個洞都是只有下播之後才知道的事，幾千個粉絲答不出來。
你答得出來——而這個節目只有一種救法：她會把你打的字唸出來。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from daykit import Board, G, HOLE

b = Board("board-v2-day6", "新一・第六天：提示詞掛掉", "五個洞，三次搶答。每救一個，就是她親口把下播後的事播出去。")

b.scene("d6-open", "第六天・開播前", "直播室的倒數顯示 05:00。提示欄跑得好好的。", "開播前", start=True)
b.prev = "d6-open"
w = b.wake("d6", day=6, prefill=["今天就聊聊天"])
b.link("d6-open", w); b.prev = w
b.addops(w, [{"variable": "savesLeft", "kind": "set", "value": 3},
             {"variable": "savedCount", "kind": "set", "value": 0},
             {"variable": "settleAt", "kind": "set", "value": 0},
             {"variable": "leaked", "kind": "set", "value": 0}])

b.chain([
 ("d6-p1", "她翻開守則本，唸出昨天那一句：「{{ruleLine5}}」", "平常", "旁白"),
 ("d6-p2", "喔。好喔。", "開心", G),
 ("d6-p3", "今天的流程、今天的梗、常客的名字，全部都在提示欄上面。", "平常", "旁白"),
 ("d6-p4", "今天沒什麼特別的。就聊聊天。", "平常", G),
 ("d6-p5", "這種最輕鬆了。", "開心", G),
])

sc = b.scene("d6-live", "第六天・直播中", "留言區開了。", "直播中")
b.link(b.prev, sc); b.prev = sc
b.chain([
 ("d6-l1", "逼——嗶！大家好，我是格莉奇！", "當機", G),
 ("d6-l2", "她講了二十分鐘。講得很順。", "平常", "旁白"),
 ("d6-l3", "常客的名字一個都沒有叫錯。上禮拜的梗接得剛剛好。", "平常", "旁白"),
 ("d6-l4", "然後提示欄變成空白。", "平常", "旁白"),
 ("d6-l5", "她沒有停。", "平常", "旁白"),
 ("d6-l6", "對啊，然後那個——\n那個誰，就是常常來的那個。\n阿明！", "平常", G),
])
b.chat("d6-c1", ["阿明：？", "小夜：那是我"])
b.link(b.prev, "d6-c1"); b.prev = "d6-c1"
b.chain([
 ("d6-l7", "喔喔喔對不起小夜！哈哈我今天眼睛壞掉。", "當機", G),
 ("d6-l8", "她笑得跟平常一樣。", "平常", "旁白"),
 ("d6-l9", "接下來十分鐘，她叫錯了四個人的名字。", "平常", "旁白"),
 ("d6-l10", "欸，我問一下喔。\n這個有點奇怪，你們不要笑我。", "發呆", G),
])


def mem(key, gate_, outs, end):
    b.unlink(f"{key}-after-hit", f"{key}-end")
    b.link(f"{key}-after-hit", gate_)
    for o in outs: b.link(o, end)


HOLES = [
 ("d6-h1", "我是不是每天半夜都在做什麼事？",
  ["阿明：睡覺？", "小夜：打遊戲", "路人：不知道欸"],
  "你每天半夜都在烤麵包",
  "喔——{{name}} 說我每天半夜都在烤麵包！\n對耶！我好像真的有！",
  "算了，可能沒有吧。好啦下一個。", "我每天半夜都在烤麵包"),
 ("d6-h2", "我有一首歌，我一直會唱。\n那首歌叫什麼？",
  ["阿明：你唱過的太多了", "小夜：哪一首", "路人B：查不到"],
  "《{{oldSong}}》，你兩年前寫的",
  "《{{oldSong}}》。\n{{name}} 說是我兩年前寫的。\n我會寫歌喔？",
  "沒有人答得出來。她笑著跳過去。", "我兩年前寫過一首歌"),
 ("d6-h3", "我每天晚上……\n是不是都會跟誰講話？",
  ["路人：跟我們啊", "小夜：下播之後你不是就睡了嗎", "阿明：？？"],
  "你每天下播之後都跟我講話",
  "欸？\n{{name}} 說我每天下播之後都跟他講話。\n"
  "有嗎？我不記得欸。\n不過既然你這樣說，那應該就有吧。",
  "她想了很久，然後說「應該沒有吧」。", "下播之後有人在跟我講話"),
 ("d6-h4", "那個麵包。\n我為什麼要留一個給他？",
  ["小夜：留給誰", "阿明：他是誰啦", "路人B：不知道"],
  "因為你們是好朋友",
  "因為我們是好朋友。\n喔。\n那我就繼續留給他好了。",
  "她自己想了一個理由，說完自己也不太信。", "我留麵包給他是因為我們是好朋友"),
 ("d6-h5", "最後一個。\n我室友為什麼要跟我住？",
  ["小夜：房租便宜？", "阿明：？？", "路人B：這什麼問題"],
  "因為你總是有東西可以忘掉",
  "因為我……總是有東西可以忘掉。\n\n"
  "（她唸完了。她唸的時候沒有停頓，像在唸一句別人寫的句子。）\n"
  "（她沒有懂。）\n（留言區懂了。留言區停住了。）\n"
  "哈哈。\n這不是 Bug，這是 Feature！",
  "算了。反正他就是住在這裡。\n他住這裡很好啊。\n\n（她說得很開心。）",
  "他為什麼跟我住"),
]
for key, ask, comments, ans, hit_t, miss_t, label in HOLES:
    end, hit = b.hole(key, ask, comments, ans, hit_t, miss_t,
                      ops_hit=[{"variable": "pending", "kind": "set", "value": label},
                               {"variable": "leaked", "kind": "add", "value": 1}])
    g, outs = b.store(f"{key}-m", "「等一下。」有一格自己掉出去了，她沒有發現。",
                      x=b.col(), y=-700)
    mem(key, g, outs, end)
    b.prev = end

# 撐過去要救到兩個以上
gate = b.setvar("d6-judge", [], text="", title="今天撐過去了嗎")
b.link(b.prev, gate)
gx = b.col()
ok = b.chain([
 ("d6-e1", "好，今天雖然怪怪的，但是還可以嘛。", "開心", G),
 ("d6-e2", "今天記住的東西——{{slot1}}、{{slot2}}、{{slot3}}、{{slot4}}。", "平常", G),
 ("d6-e3", "掰掰！", "開心", G),
], y=-250, x=gx, link_prev=False)
b.link(gate, ok[0], "right", cond={"variable": "savedCount", "op": "gte", "value": 2})
bad = b.chain([
 ("d6-b1", "那個……", "當機", G),
 ("d6-b2", "對不起喔大家，我今天狀況不太好。", "當機", G),
 ("d6-b3", "我先下播了。\n對不起。", "當機", G),
 ("d6-b4", "她提早下播了四十分鐘。", "平常", "旁白"),
], y=250, x=gx, link_prev=False)
b.link(gate, bad[0])
clr = b.setvar("d6-clear",
               [{"variable": "slot1", "kind": "set", "value": ""},
                {"variable": "slot2", "kind": "set", "value": ""},
                {"variable": "slot3", "kind": "set", "value": ""},
                {"variable": "slot4", "kind": "set", "value": ""},
                {"variable": "slotUsed", "kind": "set", "value": 0}],
               text="四個格子是空的。", title="沒撐過去：四格清空", x=gx + 1200, y=250)
b.link(bad[-1], clr)

sc2 = b.scene("d6-off", "第六天・下播後", "鏡頭朝著天花板。麥克風還開著。很久都沒有聲音。", "下播後")
b.link(ok[-1], sc2); b.link(clr, sc2); b.prev = sc2
b.voiceonly = True   # 鏡頭朝天花板，看不到人
b.chain([
 ("d6-o1", "門開了。外套被掛起來。", "平常", "旁白"),
 ("d6-o2", "怎麼了。", "餓", HOLE),
 ("d6-o3", "沒有啊。", "平常", G),
 ("d6-o4", "嗯。", "飽", HOLE),
 ("d6-o5", "天花板亮了一下。又亮了一下。", "平常", "旁白"),
 ("d6-o6", "今天亮得比平常多。", "平常", "旁白"),
 ("d6-o7", "你的私訊還通。", "平常", "旁白"),
])

g2 = b.setvar("d6-judge2", [], text="", title="撐過去的人才聽得到那半句")
b.link(b.prev, g2)
hx = b.col()
half = b.chain([
 ("d6-h-1", "「你今天很棒。」", "平常", G),
 ("d6-h-2", "……", "發呆", G),
 ("d6-h-3", "{{name}}。", "平常", G),
 ("d6-h-4", "你今天一直在。", "平常", G),
 ("d6-h-5", "我想跟你說，我其實一直都——", "平常", G),
 ("d6-h-6", "ERROR", "當機", "旁白"),
 ("d6-h-7", "聲音硬生生斷掉。", "平常", "旁白"),
 ("d6-h-8", "兩秒。", "平常", "旁白"),
 ("d6-h-9", "咦，我剛剛講到哪？", "發呆", G),
 ("d6-h-10", "她不會再講第二次。", "平常", "旁白"),
 ("d6-h-11", "只有你聽到那半句。", "平常", "旁白"),
], y=-250, x=hx, link_prev=False)
b.link(g2, half[0], "right", cond={"variable": "savedCount", "op": "gte", "value": 2})
quiet = b.chain([
 ("d6-q-1", "你打了字。", "平常", "旁白"),
 ("d6-q-2", "她沒有唸出來。", "平常", "旁白"),
 ("d6-q-3", "……嗯。\n謝謝。", "發呆", G),
 ("d6-q-4", "天花板亮了一下。", "平常", "旁白"),
], y=250, x=hx, link_prev=False)
b.link(g2, quiet[0])

join = b.setvar("d6-join", [], text="", title="接回主線", x=hx + 3600, y=0)
b.link(half[-1], join); b.link(quiet[-1], join)
b.prev = join

before = b.prev
s_in, s_out = b.settle("d6-set", x=b.col(), y=-400)
b.link(before, s_in); b.prev = s_out

rv = b.setvar("d6-rv", [{"variable": "ruleVersion", "kind": "set", "value": 6}],
              text="守則本翻開。", title="守則本第六版")
b.link(b.prev, rv)
ri = b.add("d6-rule", {"type": "input", "title": "今天要留什麼給明天的她？",
                       "text": "明天是兩週年。",
                       "inputVariable": "ruleLine6",
                       "inputPlaceholder": "寫一句給明天的她"})
b.link(rv, ri); b.prev = ri
b.chain([
 ("d6-r1", "{{name}}，記得存檔喔。", "平常", G),
 ("d6-r2", "燈關了。", "平常", "旁白"),
])
b.link(b.prev, b.jump("d6-fin", "board-v2-day7", "d7-open", text="天亮了。"))

b.push("新一・第六天（VTuber 前提）")
