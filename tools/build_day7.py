#!/usr/bin/env python3
"""Day 7・麵包 —— 最後一天,三個結局(其中一個再分兩種)。

三家獨立寫出來的結局結構完全一樣,所以照收:
  A 留給他吃　B 她自己吃掉　C 交給玩家保管

**A 要再分兩種,這是整週累積唯一的結帳點。** 他一天只吃得下一件。這幾天玩家
每餵他一次,就用掉一次他的胃。所以:
  fedCount > 0 → 他吃不下。那塊她為他烤的麵包會在保鮮膜裡慢慢皺掉。
  fedCount = 0 → 他吃得下。從頭到尾沒餵過他的玩家才拿得到這個版本。
前六天每一次「餵他」看起來都是好意,帳單在這裡。

收尾句「……我會記得你一點點。」只給結局 C。

中午如果玩家手上還留著 Day 3 那段麵包的記憶(breadState == "player"),
可以選擇還給她。還了,她才知道自己為什麼烤;不還,她就只能猜。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE, A

b = Board("board-day7", "Day 7・麵包",
          "早：他把麵包還回來　中：她問你記不記得她為什麼烤　晚：三個結局，A 依這週餵過他幾次分兩種")

# ══════════ 早 ══════════
b.prev = b.scene("d7m-scene", "第七天・清晨", "她開機的時候，房間裡已經有別人了。", "早",
                 bgm=A["bgm-theme"], start=True)
b.chain([
    ("d7m-boot",  "逼——嗶！", "當機", G),
    ("d7m-door",  "黑洞先生站在門口。他手裡拿著一塊麵包，保鮮膜包得很整齊。", "平常", None),
    ("d7m-know",  "她認得這種包法。", "平常", None),
    ("d7m-yours", "妳昨天交給我的。", "預設", HOLE),
    ("d7m-put",   "他把麵包放在桌上。門關上的聲音很小，像是刻意放輕的。", "平常", None),
    ("d7m-yday",  "……昨天？昨天是今天嗎。", "發呆", G),
    ("d7m-what",  "桌上怎麼會有麵包。是我烤的嗎。看起來是我烤的。", "平常", G),
    ("d7m-canI",  "可是我為什麼要烤麵包。我會烤麵包嗎。", "發呆", G),
    ("d7m-hand",  "她低頭看著自己的手。指甲縫裡有一點點麵粉。", "平常", None),
    ("d7m-did",   "……我真的有烤。", "發呆", G),
    ("d7m-forget","可是為什麼我會忘記這種事。", "發呆", G),
])

# ══════════ 中 ══════════
cur = b.scene("d7n-scene", "第七天・中午", "她坐在沙發上，麵包放在膝蓋中間。保鮮膜朝上，指紋壓痕很清楚。", "中")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d7n-mine",  "指紋是她的。她認得。", "平常", None),
    ("d7n-ask",   "你記得嗎。我為什麼要烤這個。", "平常", G),
    ("d7n-soft",  "她問得很輕，像是不敢問太大聲。", "平常", None),
    ("d7n-note",  "紙條呢。我有沒有寫紙條。上面應該寫了什麼的吧。", "平常", G),
    ("d7n-none",  "她翻了翻麵包。沒有紙條。只有保鮮膜上一道很深的折痕。", "平常", None),
])
gate = b.prev

# ── 玩家手上還留著那段記憶的話,可以還給她 ──
tx = b.col()
tell_q = b.choice("d7n-tell-q",
                  "你手上還留著她那天說的話。她說：「我的手記得怎麼包保鮮膜，可是我的腦不記得為什麼要包。」\n要現在還給她嗎？",
                  ["還給她（她會知道自己為什麼烤）", "先不說（讓她自己想）"], x=tx, y=-300)
b.link(gate, tell_q, "right", cond={"variable": "breadState", "op": "eq", "value": "player"})
told = b.setvar("d7n-told", [{"variable": "toldHer", "kind": "set", "value": 1},
                             {"variable": "slotUsed", "kind": "add", "value": 1}],
                text="你把那句話還給她。她聽完，很久沒有講話。", title="還給她", x=tx + 320, y=-420)
b.link(tell_q, told, "choice-0")
tld = b.chain([
    ("d7n-tld1", "所以那天早上，站在冰箱前面的是我。", "發呆", G),
    ("d7n-tld2", "我包好，寫了紙條，然後就忘了。", "發呆", G),
    ("d7n-tld3", "我對他好，然後我把這件事忘掉。我每天都在做這件事嗎。", "發呆", G),
    ("d7n-tld4", "她抬頭看著空著的那張椅子。那是黑洞先生常坐的位置。", "平常", None),
], x=tx + 640, y=-420, link_prev=False)
b.link(told, tld[0])
told_end = tld[-1]
not_told = b.say("d7n-nottell", "你沒有說。她把麵包翻過來又翻過去，等一個不會來的答案。",
                 who=None, title="先不說", x=tx + 320, y=-180)
b.link(tell_q, not_told, "choice-1")

guess = b.chain([
    ("d7n-g1", "我到底為什麼要烤這個。我又不會烤麵包。", "平常", G),
    ("d7n-g2", "我會烤麵包嗎。你說呢。", "發呆", G),
], x=tx, y=200, link_prev=False)
b.link(gate, guess[0])
b.link(not_told, guess[0])

# ── 最終抉擇 ──
fx = b.col()
# 三家指出「他吃不下」的重量全靠旁白宣稱,玩家感覺不到自己餵了七天。
# 所以把數字擺在做決定的那一刻 —— 是資料不是敘述,玩家自己算得出來。
final = b.choice("d7n-final",
                 "最後一件事。這塊麵包要放哪裡？\n"
                 "（這禮拜妳餵過黑洞先生 {{fedCount}} 次　他現在有 {{holeFeet}} 隻腳）",
                 ["留給黑洞先生（放回桌上，等他回來）",
                  "她自己吃掉（腦子記不住，至少讓身體記得）",
                  "交給你保管（她再也不會記得，但你會）"], x=fx, y=0)
for n in (told_end, guess[-1]): b.link(n, final)

# ══════════ 晚 ══════════
ex = b.col()

# 結局 A：留給他 —— 依這週餵過他幾次分兩種
a_set = b.setvar("d7e-a-set", [{"variable": "ending", "kind": "set", "value": "A"}],
                 text="她把麵包放回桌上。保鮮膜朝上，沒有拆。", title="結局A・放回桌上", x=ex, y=-700)
b.link(final, a_set, "choice-0")
a_wait = b.say("d7e-a-wait", "黑洞先生回來的時候，她已經在沙發上打瞌睡了。他站在桌邊，看著那塊麵包。很久。",
               who=None, x=ex + 300, y=-700)
b.link(a_set, a_wait)

af = b.chain([
    ("d7e-af1", "我吃不下了。", "預設", HOLE),
    ("d7e-af2", "他沒有解釋。他轉身進廚房，倒了一杯水。", "平常", None),
    ("d7e-af3", "門邊那疊短靴今天很高。這禮拜長出來的腳，一隻都沒有收回去。", "平常", None),
    ("d7e-af4", "她醒過來，看見他坐在對面，手裡是空杯子。", "平常", None),
    ("d7e-af5", "你回來啦。桌上那個是什麼。我烤的嗎。", "平常", G),
    ("d7e-af6", "他沒有回答。", "平常", None),
    ("d7e-af7", "桌上那塊麵包，明天還會在那裡。保鮮膜會皺一點。後天也還會在。", "平常", None),
    ("d7e-af8", "今天的守則——不要忘記桌上的東西。", "平常", G),
    ("d7e-af9", "她寫下來，存檔，睡著。那塊麵包再也沒有被打開過。", "平常", None),
], x=ex + 620, y=-820, link_prev=False)
b.link(a_wait, af[0], "right", cond={"variable": "fedCount", "op": "gte", "value": 1})

ae = b.chain([
    ("d7e-ae1", "他伸出一隻觸手，把保鮮膜拆開。這是這一個禮拜他第一次吃東西。", "平常", None),
    ("d7e-ae2", "他吃得很慢。慢到她醒過來的時候還沒吃完。", "平常", None),
    ("d7e-ae3", "你在吃什麼。", "發呆", G),
    ("d7e-ae4", "妳做的。", "預設", HOLE),
    ("d7e-ae5", "我做的？我什麼時候——", "當機", G),
    ("d7e-ae6", "以前。", "預設", HOLE),
    ("d7e-ae7", "她本來要再問一次「以前是什麼時候」。她沒有問。她看著他把最後一口吃完。", "平常", None),
    ("d7e-ae8", "他的西裝下襬動了一下。一隻新的觸手伸出來，穿著一雙誰都沒見過的短靴。", "平常", None),
    ("d7e-ae9", "今天的守則——他吃了我做的東西。他說是以前。以前的我也在。", "平常", G),
    ("d7e-ae10","她寫下來，存檔，睡著。桌上只剩一張攤平的保鮮膜，和上面她自己的指紋。", "平常", None),
], x=ex + 620, y=-560, link_prev=False)
b.link(a_wait, ae[0])

# 結局 B：她自己吃掉
b_set = b.setvar("d7e-b-set", [{"variable": "ending", "kind": "set", "value": "B"}],
                 text="她把保鮮膜拆開，咬了一口。嚼很久。", title="結局B・舌頭會記得", x=ex, y=0)
b.link(final, b_set, "choice-1")
bb = b.chain([
    ("d7e-b1", "……原來是這個味道。", "發呆", G),
    ("d7e-b2", "她不知道自己在說什麼味道。但是她的舌頭知道。", "平常", None),
    ("d7e-b3", "她把麵包吃完了。桌上只剩一張保鮮膜。", "平常", None),
    ("d7e-b4", "黑洞先生回來的時候，她已經在沙發上了。他站在桌邊，看著那張保鮮膜。很久。", "平常", None),
    ("d7e-b5", "你回來啦。你今天有沒有吃飽。", "平常", G),
    ("d7e-b6", "桌上本來有一塊麵包，我吃掉了。我不記得為什麼要烤，但是吃起來很熟悉。", "平常", G),
    ("d7e-b7", "他沒有回答。他進廚房，倒了一杯水。", "平常", None),
    ("d7e-b8", "他站在流理台前面，背對著她，站了比倒一杯水需要的時間還久。", "平常", None),
    ("d7e-b9", "今天的守則——不要忘記吃過的東西。", "平常", G),
    ("d7e-b10","她寫下來，存檔，睡著。那個味道明天不會在她的腦子裡。它會在別的地方。", "平常", None),
], x=ex + 300, y=0, link_prev=False)
b.link(b_set, bb[0])

# 結局 C：交給玩家
c_set = b.setvar("d7e-c-set", [{"variable": "ending", "kind": "set", "value": "C"},
                               {"variable": "givenCount", "kind": "add", "value": 1}],
                 text="她把麵包推到你面前。", title="結局C・交給你", x=ex, y=700)
b.link(final, c_set, "choice-2")
cc = b.chain([
    ("d7e-c1", "幫我收著。我不知道為什麼要烤這個，但是應該是重要的東西。", "平常", G),
    ("d7e-c2", "我不會再記得了。", "平常", G),
    ("d7e-c3", "你接過那塊麵包。保鮮膜上的指紋壓痕還在。已經涼了。", "平常", None),
    ("d7e-c4", "黑洞先生回來的時候，她已經在沙發上了。他站在桌邊，看著空掉的桌面。很久。", "平常", None),
    ("d7e-c5", "你回來啦。桌上本來有一塊麵包——我交給他保管了。", "平常", G),
    ("d7e-c6", "他轉過來，看了你一眼。", "平常", None),
    ("d7e-c7", "你手裡有東西。他看得到。", "平常", None),
    ("d7e-c8", "他沒有說話。他進廚房，倒了一杯水。", "平常", None),
    ("d7e-c9", "今天的守則——", "平常", G),
    ("d7e-c10","……我會記得你一點點。", "平常", G),
    ("d7e-c11","她是對你說的。", "平常", None),
    ("d7e-c12","她寫下來，存檔，睡著。那塊麵包在你手上。她明天不會問。", "平常", None),
], x=ex + 300, y=700, link_prev=False)
b.link(c_set, cc[0])

# ── 收尾:四個版本共用 ──
zx = ex + 300 * 14
z = b.setvar("d7e-end", [{"variable": "dayCount", "kind": "set", "value": 7},
                         {"variable": "ruleVersion", "kind": "add", "value": 1}],
             text="第 {{ruleVersion}} 版，完成。", title="第七天結束", x=zx, y=0)
for tail in (af[-1], ae[-1], bb[-1], cc[-1]): b.link(tail, z)
b.prev = z
b.chain([
    ("d7z-1", "第八天早上，「逼——嗶」會再響一次。", "平常", None),
    ("d7z-2", "她會坐起來，翻開守則本，讀第 {{ruleVersion}} 版。", "平常", None),
    ("d7z-3", "她會看見一個名字：{{playerName}}。", "平常", None),
    ("d7z-4", "她不會記得那是誰。她會念出來，然後說一句話。", "平常", None),
    ("d7z-5", "「你好。你是新來的吧？我沒印象。」", "平常", G),
])
# 二週目的回報:她記不住你,他記得住。這幾張只有打對暗號的人看得到。
# chain 會把 b.prev 推到鏈尾,所以入口要先接住,不能事後拿 b.prev。
ng_from = b.prev
ng = b.chain([
    ("d7ng-1", "可是這一次，你不是新來的。", "平常", None),
    ("d7ng-2", "門邊那疊短靴，最上面那雙是新的。沒有人穿過。", "平常", None),
    ("d7ng-3", "他今天沒有出門。他站在門口，臉朝著螢幕的方向。", "平常", None),
    ("d7ng-5", "她沒有聽見這句。她正在念守則的第一行。", "平常", None),
    ("d7ng-6", "這句是說給你聽的。他是這間房子裡唯一不會忘記的那個。", "平常", None),
], x=zx + 300 * 6, y=-300, link_prev=False)
b.link(ng_from, ng[0], "right", cond={"variable": "ngPlus", "op": "eq", "value": 1})
# 他這句越過她對玩家說,標題標出來讓 check_pronouns 放行
again = b.say("d7ng-4", "又是你。", who=HOLE, face="預設", title="他對玩家說",
              x=zx + 300 * 9, y=-300)
b.link(ng[2], again); b.link(again, ng[3])
b.edges[:] = [e for e in b.edges if not (e["source"] == ng[2] and e["target"] == ng[3])]
# 兩條路都要有出口。只掛一條有條件的線,第一次玩的人會卡在最後一張。
fin = b.say("d7-fin", "（完）", who=None, title="完", x=zx + 300 * 13, y=0)
b.link(ng_from, fin)
b.link(ng[-1], fin)
b.push("Day 7 三個結局:留給他(依 fedCount 再分吃得下／吃不下)、她自己吃掉、交給玩家保管")
