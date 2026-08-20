#!/usr/bin/env python3
"""Day 4・數靴子 —— 事件池日。

Day 4 的功能不是推主線,是讓玩家看見前三天的選擇累積成什麼。門邊的靴子高度、
她的口袋空不空、黑洞先生回來時腳的數量 —— 前三天是背景,今天推到前景。
她今天第一次數靴子。

中午改用 pool():六個事件抽一個,抽到用過的就往下掉。六個裡有兩個(收據、
水槽的麵粉痕跡)是麵包前史的碎片,不點破,留給玩家自己拼。

台詞從 llmshare 六家的稿子逐事件挑,不整篇照抄:minimax 的語氣最像格莉奇,
glm 的「4KB 擠掉別的東西」邏輯最扎實,kimi 的地圖那段意象最好。
qwen 那份混了簡體(無意义/存档),沒用。

代名詞規則:妳=格莉奇／你=玩家／中午段黑洞先生不在畫面上,一律用全名。
改動寫在這裡,不要只改線上版 —— 重建會蓋回去。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE, A

b = Board("board-day4", "Day 4・數靴子",
          "早：從一句夢話開始，她第一次數門邊的靴子　中：六選一的事件池　晚：依中午的去處演三個版本")

# ══════════ 早 ══════════
b.prev = b.scene("d4m-scene", "第四天・清晨", "天還沒亮。她躺著，眼睛沒睜開，嘴巴在動。",
                 "早", bgm=A["bgm-theme"], start=True)
b.prev = b.wake("d4m", prefill=["昨天守則上那句話", "門邊有 {{holeFeet}} 隻腳的靴子"])
b.link(b.find("d4m-scene")["id"], b.prev)
b.chain([
    ("d4m-dream", "……不是那邊，是這邊。", "發呆", G),   # speak-tw-ok：夢話,不是修辭
    ("d4m-boot",  "逼——嗶！", "當機", G),
    ("d4m-up",    "她彈起來。房間裡只有她一個人。她完全不記得自己剛剛說了什麼。", "平常", None),
    ("d4m-heard", "我剛剛有講話嗎？我覺得有人在聽。", "發呆", G),
    ("d4m-gone",  "黑洞先生的外套不在。門是關好的。他已經出去了。", "平常", None),
    ("d4m-rule",  "她翻開守則本。昨天最後一行是昨天的自己寫的。", "平常", None),
    ("d4m-quote", "「{{ruleLine3}}」", "平常", None),
    ("d4m-obey",  "我不記得為什麼要寫這個。可是既然是我寫的，那就照做。", "平常", G),
    ("d4m-boots", "門邊那疊短靴。今天她第一次停下來數。", "平常", None),
    ("d4m-count", "一、二、三……{{holeFeet}}。", "平常", G),
    ("d4m-few",   "我不知道昨天有幾雙。我沒有昨天。可是這個數字，感覺不太對。", "發呆", G),
])
cur = b.setvar("d4m-counted", [{"variable": "countedFeet", "kind": "set", "value": 1},
                               {"variable": "dejaVu", "kind": "add", "value": 1}],
               text="她把這個數字記下來。", title="第一次數")
b.link(b.prev, cur); b.prev = cur

# ── 這一天的核心矛盾：數字對不上，而你是唯一知道為什麼的人 ──
# 六家一致說 Day 4 沒有當天的矛盾。這裡用遊戲本來就有的累積：門邊那疊靴子
# 是你這禮拜餵他的次數堆出來的——那疊就是她忘掉的東西的數量。
b.chain([
    ("d4m-askyou", "你記得昨天有幾雙嗎？", "平常", G),
    ("d4m-only",   "你是這個房子裡唯一有昨天的人。我沒有，黑洞先生不講。", "平常", G),
])
tq = b.choice("d4m-tellq", "她問你昨天門邊有幾雙靴子。你知道答案。",
              ["告訴她真的數字", "跟她說跟昨天一樣", "不回答"])
b.link(b.prev, tq)
tx = b.col()
t_truth = b.setvar("d4m-t-truth", [{"variable": "toldFeet", "kind": "set", "value": "truth"}],
    text="你把真的數字給她。\n"
         "「所以多了。」她說。「多了幾雙我不知道，可是多了。」\n"
         "她蹲回門邊，開始把靴子一雙一雙排開。",
    title="說真話", x=tx, y=-200)
t_same = b.setvar("d4m-t-same", [{"variable": "toldFeet", "kind": "set", "value": "same"}],
    text="你跟她說跟昨天一樣。\n"
         "「喔，那就好。」她鬆了一口氣，站起來拍拍膝蓋。\n"
         "她一整天都不會再看那疊靴子。這件事現在只有你揹著。",
    title="說一樣", x=tx, y=0)
t_none = b.setvar("d4m-t-silent", [{"variable": "toldFeet", "kind": "set", "value": "silent"}],
    text="你沒有回答。\n"
         "「……好吧。」她看著螢幕看了一會兒。「你也不知道，還是你不想講？」\n"
         "「算了。反正我等一下也會忘記我問過。」",
    title="不回答", x=tx, y=200)
b.link(tq, t_truth, "choice-0"); b.link(tq, t_same, "choice-1"); b.link(tq, t_none, "choice-2")
join_t = b.say("d4m-t-join", "她把手插進口袋。", who=None, title="接著", x=tx + 400, y=0)
for n in (t_truth, t_same, t_none): b.link(n, join_t)
b.prev = join_t
b.chain([
    ("d4m-empty",  "口袋是空的。空得很具體，像是本來有東西，剛剛才被拿走。", "發呆", G),
])

# ══════════ 中 ══════════
cur = b.scene("d4n-scene", "第四天・中午", "太陽正上方。房間安靜得能聽見冰箱在運轉。", "中")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d4n-alone", "又剩我們兩個了。我是說我跟你。黑洞先生不算，黑洞先生去上班了。", "平常", G),
    ("d4n-hunt",  "她在房間裡繞。她說她在找東西，但她不知道要找什麼。", "平常", None),
])

EVENTS = [
    ("plant", "usedPlant",
     "欸，窗台上這盆是什麼時候冒出來的？葉子怎麼全歪那邊——那是黑洞先生常坐的位置。是誰種的啊，歪成這樣也不扶一下。", "平常",
     "她把花盆擺正了一點。葉子明天還會記得那個方向，她不會。明天她再看見它，只會當作是風吹的。",
     "黑洞先生把那盆植物連同它歪的方向一起吃掉了。黃昏黑洞先生回來時，窗台上只剩一個空盆，那叢觸手裡多出一根還不知道該往哪邊長的。",
     "「你幫我記一下嘛。」她語氣很輕，像在借一件外套。窗台上還歪著一叢綠，可是明天的她不會記得自己看過——要等你回來告訴她，她才會第二次認出這盆東西。",
     "窗台那盆歪的植物"),

    ("receipt", "usedReceipt",
     "桌上這張收據哪來的？麵粉、酵母……我半夜三點去超市買過這些？我連揉麵糰的步驟都背不起來啊。", "發呆",
     "她把收據夾在冰箱門上。明天它還在，但她不會記得自己為什麼三點去買酵母——那個「為什麼」會跟著收據一起，結成一塊她翻不到的硬塊。",
     "黑洞先生把凌晨三點的那趟超市嚼了下去。黃昏黑洞先生回來時，那叢觸手比早上飽滿，連短靴的皮面都撐出了一點光澤。",
     "那行凌晨三點的時間戳被你保住了，但她的口袋空空的。明天醒來，她不會知道自己曾經在深夜裡醒來過一次。",
     "凌晨三點的收據"),

    ("button", "usedButton",
     "我口袋裡怎麼會有鈕扣——等一下，這是西裝的。這附近穿西裝的只有黑洞先生吧？", "平常",
     "她把鈕扣放在床頭櫃上，用杯子壓住。明天醒來她會盯著它發呆：一顆她不認識的西裝鈕扣，乾乾淨淨躺在那裡，像一句被吞回去的問句。",
     "黑洞先生把這顆鈕扣連同它的來歷一起嚥了下去。黃昏黑洞先生回來時，西裝下擺多出一個針孔，卻沒有對應的扣子。她看了一眼，只覺得那件西裝哪裡怪怪的。",
     "「你拿著，」她把鈕扣放進你手心，「搞不好哪天要還人。」明天她摸遍口袋也找不到它——而你的口袋裡多了一顆跟她無關、屬於黑洞先生的東西。",
     "口袋裡的鈕扣"),

    ("flour", "usedFlour",
     "水槽怎麼白白的……麵粉？有人半夜在這裡揉過麵糰嗎？我揉的？我什麼時候會揉麵糰了？", "發呆",
     "她拿抹布把水槽擦乾淨，指縫間留著一點滑滑的觸感。明天她會記得水槽髒過，卻不會記得是誰弄髒的——甚至不會想到，那雙手可能是自己的。",
     "黑洞先生把水槽邊緣的麵粉印子舔得乾乾淨淨，水槽恢復成從來沒有人用過的樣子。黃昏黑洞先生回來時袖口沾了一點澱粉的白，她沒看見，因為她連有這件事都不記得了。",
     "「這個畫面你收著，」她朝水槽比了比，「我懷疑我半夜幹過什麼好事。」明天水槽會亮得像新的一樣，連那雙手都沒存在過。",
     "水槽的麵粉痕跡"),

    ("doornote", "usedDoorNote",
     "「今天早點回來」……這是我寫的嗎？寫給誰啊？黑洞先生剛剛還踩過去耶，眼睛都不看一下。", "平常",
     "她把紙條撿起來，攤平，貼回門口。明天她出門會看見它，讀一遍，皺眉——又是自己寫的，又是沒人理，又是早點回來。",
     "黑洞先生把紙條嚼了，連同那六個字的筆跡一起。黃昏黑洞先生回來時腳步比平常重一點，像是真的早了一點——但她不知道那跟紙條有任何關係。",
     "「這我自己寫的喔，」她有點不好意思，「幫我收著，別弄丟。」明天她會在門口找那張紙，發現沒有，然後懷疑自己是不是記錯了。",
     "門墊上的紙條"),

    ("map", "usedMap",
     "牆上這張地圖是哪來的？有人圈了一個地方，旁邊寫「黑洞先生在這裡上班」。等等，我怎麼會不知道黑洞先生在哪上班？", "發呆",
     "她盯著地圖上那個圈看了很久。明天她會忘記那個圈是誰畫的，但會記得一件事——她不知道黑洞先生每天去哪裡。這個「不知道」會跟著她。",
     "黑洞先生把地圖連同膠帶一起嚼了，牆上留下一塊乾淨的長方形，周圍是發黃的舊漆。她之後每次看到那塊乾淨，都覺得那裡本來就該空著。",
     "「你幫我查一下這是哪，」她指了指那個圈，「搞不好我畫錯了。」地圖到了你手上，牆上的膠帶痕跡慢慢捲起來。她不再追問黑洞先生的去向。",
     "牆上的地圖"),
]
# 「交給你保管」本來只是換一種不見。四家會審都指同一件事,所以在開池之前先讓
# 玩家有機會把存貨還回去 —— 這樣 give 才是迴圈的一半,不是丟掉。
hb_gate = b.prev
hx = b.col()
hb_ask = b.say("d4n-hb", "對了。我好像有東西寄在你那邊。你手上現在有 {{givenCount}} 件。",
               face="平常", who=G, x=hx, y=-160)
b.link(hb_gate, hb_ask, "right", cond={"variable": "givenCount", "op": "gte", "value": 1})
hb_q = b.choice("d4n-hb-q", "要還一件給她嗎？\n" + "（她的記憶體 {{slotUsed}}／4）",
                ["還給她（她今天會記得，明天照樣忘）", "先留著（等更值得的時候）"],
                x=hx + 300, y=-160)
b.link(hb_ask, hb_q)
hb_yes = b.setvar("d4n-hb-yes",
                  [{"variable": "givenCount", "kind": "add", "value": -1},
                   {"variable": "slotUsed", "kind": "add", "value": 1}],
                  text="你把它拿出來還給她。她接過去，看了很久，然後笑了一下。"
                       "那個表情像是在看別人做的一件好事，而那個人剛好是她自己。",
                  title="還她", x=hx + 620, y=-220)
hb_no = b.say("d4n-hb-no", "「那你先收著。」她說得很輕鬆，因為她根本不知道自己寄放了什麼。",
              who=None, x=hx + 620, y=-100)
b.link(hb_q, hb_yes, "choice-0"); b.link(hb_q, hb_no, "choice-1")
hb_join = b.say("d4n-hb-join", "她繼續在房間裡繞。", who=None, x=hx + 940, y=-160)
b.link(hb_yes, hb_join); b.link(hb_no, hb_join)
b.link(hb_gate, hb_join)   # 手上沒東西就直接跳過整段
b.prev = hb_join

b.pool("d4n", EVENTS, after_text="好。收工。")

# 餵他之後，門邊當場多一雙。這是整個遊戲裡「餵他」第一次有看得見的代價——
# 而如果早上你說了真話，她會把兩件事連起來：那疊靴子就是她忘掉的東西的數量。
after_pool = b.prev
sx = b.col()
saw = b.setvar("d4n-saw", [{"variable": "sawBoot", "kind": "set", "value": 1}],
    text="門邊有東西輕輕落下的聲音。\n"
         "那疊短靴上面多了一雙。剛剛還沒有的。",
    title="門邊多了一雙", x=sx, y=-200)
b.link(after_pool, saw, "right", cond={"variable": "todayRoute", "op": "eq", "value": "feed"})

conn = b.setvar("d4n-connect", [{"variable": "connected", "kind": "set", "value": 1}],
    text="", title="她連起來了", x=sx + 300, y=-300)
b.link(saw, conn, "right", cond={"variable": "toldFeet", "op": "eq", "value": "truth"})
b.chain([
    ("d4n-c1", "等一下。", "當機", G),
    ("d4n-c2", "早上你說多了。剛剛又多了一雙。而我剛剛才決定要把一件事交給黑洞先生。", "發呆", G),
    ("d4n-c3", "她走到門邊，蹲下來，手放在最上面那雙靴子上。那雙是新的，鞋底沒有磨過。", "平常", None),
    ("d4n-c4", "這疊短靴不是誰的鞋子。這疊是我忘掉的東西。", "發呆", G),
    ("d4n-c5", "一雙就是一件。門邊有 {{holeFeet}} 隻腳的高度，就是我忘了 {{fedCount}} 件事。", "發呆", G),
    ("d4n-c6", "她坐在門邊，很久沒有站起來。", "平常", None),
    ("d4n-c7", "……可是我不知道那 {{fedCount}} 件是什麼。我連自己丟過什麼都不知道。", "發呆", G),
], x=sx + 600, y=-300, link_prev=False)
b.link(conn, b.find("d4n-c1")["id"])
conn_end = b.prev

noconn = b.say("d4n-noconn", "她看了那雙新靴子一眼，然後轉開。今天沒有人告訴她該數什麼。",
               who=None, title="她沒連起來", x=sx + 600, y=-100)
b.link(saw, noconn)

join_n = b.say("d4n-join", "好。我們等黑洞先生回來。", who=G, face="平常",
               title="收工", x=sx + 3400, y=0)
b.link(after_pool, join_n)
b.link(conn_end, join_n); b.link(noconn, join_n)
b.prev = join_n

# ══════════ 晚 ══════════
cur = b.scene("d4e-scene", "第四天・傍晚", "門口有腳步聲。不只一組。", "晚")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d4e-back", "黑洞先生回來了。她走到門邊，這次她沒有看臉，她先看腳。", "平常", None),
])
back = b.prev
ex = b.col()
r_feed = b.say("d4e-r-feed", "{{holeFeet}} 隻。比早上多一隻。她說不出哪裡不一樣，但她整個下午都在等這個。", who=None, title="他吃掉了", x=ex, y=-260)
r_keep = b.say("d4e-r-keep", "{{holeFeet}} 隻。跟早上一樣。她有點失望，然後她忘了自己在失望什麼。", who=None, title="她留著", x=ex, y=0)
r_give = b.say("d4e-r-give", "{{holeFeet}} 隻。跟早上一樣。她的口袋也還是空的。今天她把東西放到了一個她走不到的地方。", who=None, title="交給你了", x=ex, y=260)
b.link(back, r_feed, "right", cond={"variable": "todayRoute", "op": "eq", "value": "feed"})
b.link(back, r_keep, "right", cond={"variable": "todayRoute", "op": "eq", "value": "keep"})
b.link(back, r_give)

# 餵了哪一件,他身上就帶回哪一件的痕跡。glm 指出中午的選擇要直接決定晚上的
# 懸念,不能只對靴子數量有反應。六條各自對應 EVENTS 的順序。
TRACE = [
    "他身上有一點土味。她湊近聞了一下，說不上來像什麼，只覺得自己應該要認得。",
    "他脫西裝的時候，口袋裡掉出一小捲收銀機的紙。上面沒有印任何字。他撿起來，收好。",
    "他今天的西裝下擺整整齊齊，沒有針孔。她記得今天好像有什麼東西是有洞的，但想不起來是什麼。",
    "他洗手洗了很久。水聲停了以後，他站在水槽前面又看了三秒。",
    "他進門的時候低頭看了一眼門墊。墊子上什麼都沒有。他還是看了。",
    "他經過那面牆的時候慢下來。牆上那塊乾淨的長方形，他看了很久，比看她還久。",
]
tx = ex + 320
traces = []
for i, t in enumerate(TRACE):
    n = b.say(f"d4e-trace{i+1}", t, who=None, title=f"痕跡{i+1}", x=tx, y=(i - 3) * 130 - 260)
    b.link(r_feed, n, "right", cond={"variable": "todayEvent", "op": "eq", "value": i + 1})
    traces.append(n)

# 她今天把靴子跟遺忘連起來的話，他不會裝作沒發生。
cn = b.say("d4e-conn", "妳今天數到了。", who=HOLE, face="預設", title="他說（她連起來了）",
           x=tx + 340, y=-620)
cn2 = b.say("d4e-conn2", "數到了。門邊那疊是我丟掉的東西。是不是？", who=G, face="發呆",
            title="她問", x=tx + 640, y=-620)
cn3 = b.say("d4e-conn3", "是。", who=HOLE, face="預設", title="他承認", x=tx + 940, y=-620)
cn4 = b.say("d4e-conn4", "他第一次直接回答一個問題。她愣了兩秒，然後低頭看自己的手。",
            who=None, title="他第一次直接回答", x=tx + 1240, y=-620)
cn5 = b.say("d4e-conn5", "那你為什麼要留著？丟掉的東西你留著幹嘛？", who=G, face="發呆",
            title="她追問", x=tx + 1540, y=-620)
cn6 = b.say("d4e-conn6", "他沒有回答這一句。他走去角落坐下，那疊靴子在他背後。",
            who=None, title="他不答", x=tx + 1840, y=-620)
for a, bb in ((cn, cn2), (cn2, cn3), (cn3, cn4), (cn4, cn5), (cn5, cn6)): b.link(a, bb)

merge = b.say("d4e-merge", "妳今天在數什麼。", who=HOLE, face="預設", title="他問了", x=tx + 340, y=0)
for r in (r_keep, r_give, *traces): b.link(r, merge)
b.link(r_feed, merge)   # 保底:抽到的事件不在表上時不會斷線
# 所有原本指向 merge 的線先改指向閘門,閘門再判斷她有沒有連起來。
# 直接對來源加一條有條件的線是沒用的——那些來源已經有「痕跡」那組有條件的線,
# 而且一定會有一條命中,新加的永遠輪不到。
gate4 = b.setvar("d4e-gate", [], text="", title="她連起來了嗎", x=tx + 300, y=-300)
b.redirect(merge, gate4, keep=(cn6,))
b.link(gate4, cn, "right", cond={"variable": "connected", "op": "eq", "value": 1})
b.link(gate4, merge)
b.link(cn6, merge)
b.prev = merge
b.chain([
    ("d4e-admit", "靴子。門邊那疊。我今天第一次數。", "平常", G),
    ("d4e-why",   "為什麼今天數。", "預設", HOLE),
    ("d4e-dunno", "不知道。就是覺得應該要數。像是有人叫我數。", "發呆", G),
    ("d4e-stop",  "黑洞先生把外套掛好，動作停了一下，比平常久。", "平常", None),
    ("d4e-dont",  "不要數。", "預設", HOLE),
    ("d4e-huh",   "為什麼？", "平常", G),
    ("d4e-none",  "黑洞先生沒有回答。他從來不解釋自己說的話。", "平常", None),
    ("d4e-rule",  "……好吧。填守則。第 {{ruleVersion}} 版。", "平常", G),
])
cur = b.add("d4e-rulein", {"type": "input", "title": "填空位",
    "text": "空位在這裡。今天要留什麼給明天的我？",
    "inputVariable": "ruleLine4", "inputPlaceholder": "寫一句話…",
    "inputSuggestions": ["數門邊的靴子。", "不要數靴子。", "我的口袋本來應該有東西。"]})
b.link(b.prev, cur); b.prev = cur
cur = b.setvar("d4e-rulever", [{"variable": "ruleVersion", "kind": "add", "value": 1},
                               {"variable": "dayCount", "kind": "set", "value": 4}],
               text="她寫上去。第 {{ruleVersion}} 版，完成。", title="守則 +1")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d4e-save",  "記得存檔。今天這個數字，我自己留不住。", "平常", G),
    ("d4e-sleep", "她躺回床上。門邊那疊短靴在黑暗裡看不出高度。", "平常", None),
])
b.link(b.prev, b.jump("d4e-jump", "board-day5", "d5m-scene"))
b.push("Day 4 事件池日:六選一,晚上依中午的去處分三個版本,她第一次數靴子")
