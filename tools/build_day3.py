#!/usr/bin/env python3
"""Day 3・麵包 —— 探索日（v2 重做）。

玩家實測的兩句話直接決定了這次重做：

  「一天過得好快，才幾句話就沒了，完全沒經歷過的感覺」
  「不知道自己在記什麼」

原本這天只有 50 張卡、中午只有一個選擇。現在中午是探索：房間裡有五個地方
可以看，黑洞先生傍晚就回來，玩家只陪得了三個。看到的東西要決定去處，而
4KB 真的會滿——滿了必須丟一格，丟掉的那件黑洞先生會吃掉，玩家擋不住。

**四格的內容看得見**（選項與台詞用 {{slot1}}…{{slot4}}）。這是「不知道自己在
記什麼」的直接解法：你不可能管理一個看不見的東西。驗過播放器會對選項文字
做變數插值（`re(e)` 有套在選項的 span 上）。

晚上她只講得出還留在格子裡的東西。清空之後就沒了——所以留著的意義是
「今天晚上她講得出來」，那是這一天唯一的出口。

台詞來源：五家平行寫，逐段挑。冰箱／守則本／角落取 kimi，窗台取 glm 與
minimax（他們獨立寫出同一個東西：碗底大小的圓形灰塵印。那指向麵包，
不會像 kimi 的金髮那樣引進第三個角色）。「再去一次」五句原稿是同一個笑話
結構，重寫過。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE, A

b = Board("board-day3", "Day 3・麵包",
          "早：從冰箱開始　中：五個地方只看得了三個，4KB 真的會滿　晚：她只講得出還留在格子裡的")

MEM = "（記憶體 {{slotUsed}}／4　今天還能看 {{looksLeft}} 個地方）"

# ══════════════════ 早 ══════════════════
b.prev = b.scene("d3m-scene", "第三天・清晨", "冰箱門沒關緊，透出一條光。",
                 "早", bgm=A["bgm-theme"], start=True)
b.chain([
    ("d3m-stand", "她站在冰箱前面，手裡拿著一塊用保鮮膜包好的麵包。她不記得自己是怎麼走過來的。", "平常", None),
    ("d3m-boot",  "……逼——嗶！", "當機", G),
    ("d3m-late",  "喔。我開機了。剛剛那是誰在動？", "發呆", G),
    ("d3m-note",  "保鮮膜上貼著一張紙條。字跡歪歪的，寫著「給黑洞先生」。這是我寫的字。", "平常", G),
    ("d3m-again", "這真的是我寫的字。", "發呆", G),
    ("d3m-hands", "我的手記得怎麼包保鮮膜，可是我的腦不記得為什麼要包。", "發呆", G),
    ("d3m-boots", "黑洞先生正在門邊穿靴子，觸手一根一根塞進短靴裡。他停了一下。", "平常", None),
    ("d3m-ask",   "黑洞先生，這什麼時候做的？我真的完全不記得。", "平常", G),
    ("d3m-reply", "妳以前烤過。", "預設", HOLE),
    ("d3m-when",  "以前是什麼時候？", "平常", G),
    ("d3m-silent","黑洞先生把最後一根觸手塞進靴子。\n門開了又關上。", "平常", None),
    ("d3m-cold",  "她還站在冰箱前面，手裡的麵包漸漸退冰。", "平常", None),
])

# 記憶體檢視：她把四格唸出來。第一次玩四格是空的——那個空白就是這天的起點。
cur = b.setvar("d3m-reset",
               [{"variable": "slotUsed", "kind": "set", "value": 2},
                {"variable": "slot1", "kind": "set", "value": "手裡這塊麵包"},
                {"variable": "slot2", "kind": "set", "value": "紙條上是我自己的字"},
                {"variable": "slot3", "kind": "set", "value": ""},
                {"variable": "slot4", "kind": "set", "value": ""},
                {"variable": "looksLeft", "kind": "set", "value": 3},
                {"variable": "fedToday", "kind": "set", "value": 0},
                {"variable": "seenFridge", "kind": "set", "value": 0},
                {"variable": "seenWindow", "kind": "set", "value": 0},
                {"variable": "seenBoots", "kind": "set", "value": 0},
                {"variable": "seenRules", "kind": "set", "value": 0},
                {"variable": "seenCorner", "kind": "set", "value": 0}],
               text="", title="今天的記憶體，清空")
b.link(b.prev, cur); b.prev = cur
b.chain([
    ("d3m-check", "她敲了敲自己的側面，像在確認裡面還剩多少位置。", "平常", None),
    ("d3m-two",   "四格。已經用掉兩格了——「{{slot1}}」跟「{{slot2}}」。今天才剛開始耶。", "發呆", G),
    ("d3m-plan",  "黑洞先生要傍晚才回來。\n在那之前我想在房間裡看幾個地方。\n可是我只剩兩格。\n而且我走到一半就會忘記自己在找什麼。", "平常", G),
    ("d3m-warn",  "如果滿了我還硬要記，最舊的那一格就會自己掉出去。我攔不住，也不會知道掉的是什麼。", "平常", G),
    ("d3m-pair",  "還有一件事。有時候兩件東西同時擺在我腦子裡，我會突然看懂一點什麼。"
                  "一件一件分開看就沒有。", "平常", G),
    ("d3m-pair2", "所以你挑的時候，順便想一下哪兩件放在一起會有意思。", "平常", G),
    ("d3m-you",   "所以你帶路。你說去哪，我就去哪。", "平常", G),
])

# ══════════════════ 中：探索 ══════════════════
cur = b.scene("d3n-scene", "第三天・中午", "太陽爬到窗戶正上方。房間安靜得聽得見冰箱在運轉。", "中")
b.link(b.prev, cur); b.prev = cur


# 每一筆最後一欄是「搭檔」:(對方的旗標, 拼出來的代號, 她當場說的話)
# 只要對方已經在記憶格裡,留下這一件的當下就會接起來。
# 一件線索單獨看不出東西，兩件放在一起才有意思。
# 最後一欄是搭檔：(對方的旗標, 拼出來的代號, 她當場說的話)。
# **合併發生在留下第二件的當下，不是等到晚上。** 五家會審指出等到晚上的話，
# 玩家探索前不知道哪兩個能拼，變成盲賭；而且「啊原來如此」那一下應該在現場。
PLACES = [
    ("fridge", "seenFridge", "keptFridge", "冰箱",
     "她走到冰箱前面。金屬門面還留著清晨開關時的餘溫。",
     ["麵包還在裡面。是我早上看到的那塊，還是另一塊？",
      "保鮮膜折得很仔細，邊角收進去，像我在包禮物的時候會做的事。",
      "但是我現在的包裝技術明明很爛。"],
     "冰箱的門我剛剛才關上。再開一次，裡面也不會多長出東西。",
     "冰箱繼續運轉。沒有人去確認那塊麵包的保鮮膜還是不是原來的樣子。",
     "保鮮膜的折法",
     [("keptRules", 'hand', '她把保鮮膜攤開，又摺回去。\n「守則本上的字比我現在寫的穩。這個保鮮膜也折得比我會做的仔細。」\n「有一個比我穩的人，用我的字跡寫東西，用我的手折保鮮膜。」\n「那個人是我嗎？還是我是那個人剩下來的部分？」\n她低頭看自己的手，翻過來，又翻回去。\n「這雙手好像替誰做過什麼很認真的事。」\n「而且做完就忘了，所以那個人到現在都還沒有被謝過。」')]),

    ("window", "seenWindow", "keptWindow", "窗台",
     "她走到窗邊。陽光從左邊斜斜照進來，在窗台上畫出一條很亮的線。",
     ["這裡有東西被移動過。陽光直射的那個位置，灰塵的形狀是圓的。",
      "圓的，大小跟一個碗底差不多。印子很深，表示那個東西在這裡放了很久很久。",
      "可是現在什麼都沒有。有人把一個放在這裡很久的東西拿走了。"],
     "窗台就長那樣。灰塵不會自己演一次給我看。",
     "下午的陽光從窗台慢慢退開。那個圓形的灰塵印還留在那裡，等著被誰注意到。",
     "窗台上的圓印",
     [("keptRules", 'dough', '格莉奇突然不講話了。\n「守則上寫『不要半夜開烤箱』、『麵粉要收在櫃子裡』。」\n而窗台上有一個碗底的印子。\n印子很深，表示那個碗在那裡放了很久很久。\n「碗放在有太陽的地方是為了發酵。」\n她停住了。\n這句話她說得太順了，順到不像是第一次說。')]),

    ("boots", "seenBoots", "keptBoots", "門邊那疊短靴",
     "她蹲到門邊，手指撥過那疊沒人穿的短靴，揚起很薄的灰。",
     ["這麼多雙，全部一樣的款式，像某種儀式用的陳列。",
      "有一雙的鞋面裂開了，從鞋尖裂到鞋帶孔中間。",
      "沒有腳卻有這麼多靴子。黑洞先生的觸手會換鞋嗎？還是觸手也會長大，舊的皮撐破了？"],
     "我剛剛數過了。再數一次，數字也不會變得比較好懂。",
     "門邊的短靴維持著原來的堆疊角度。裂痕在陰影裡繼續裂。",
     "裂開的那雙靴子",
     [("keptCorner", 'feet', '「靴子是裝腳的東西。」\n「可是角落地板上那些刮痕，是觸手磨出來的。細細的，一道一道。」\n「坐在那裡的人沒有腳。可是門邊那疊靴子，每一雙都是照著腳的形狀做的。」\n她抬起頭。\n「黑洞先生以前有腳嗎？」')]),

    ("rules", "seenRules", "keptRules", "守則本",
     "她翻開桌上的守則本。紙頁因為太常被翻動而捲起邊角。",
     ["這些字我看得懂。「不要半夜開烤箱」、「麵粉要收在櫃子裡」。",
      "可是筆跡跟我現在寫的不一樣。比較穩，比較不抖。",
      "最後一頁有我的簽名，還畫了一個笑臉。我不記得我有這麼開朗過。"],
     "同一頁我剛看完。那些字不會因為我多看一次就換一種說法。",
     "守則本攤在桌上，捲起的紙頁慢慢恢復原本翹起的弧度。前幾天的筆跡繼續等。",
     "守則上的那兩條",
     [("keptWindow", 'dough', '格莉奇突然不講話了。\n「守則上寫『不要半夜開烤箱』、『麵粉要收在櫃子裡』。」\n而窗台上有一個碗底的印子。\n印子很深，表示那個碗在那裡放了很久很久。\n「碗放在有太陽的地方是為了發酵。」\n她停住了。\n這句話她說得太順了，順到不像是第一次說。'), ("keptFridge", 'hand', '她把保鮮膜攤開，又摺回去。\n「守則本上的字比我現在寫的穩。這個保鮮膜也折得比我會做的仔細。」\n「有一個比我穩的人，用我的字跡寫東西，用我的手折保鮮膜。」\n「那個人是我嗎？還是我是那個人剩下來的部分？」\n她低頭看自己的手，翻過來，又翻回去。\n「這雙手好像替誰做過什麼很認真的事。」\n「而且做完就忘了，所以那個人到現在都還沒有被謝過。」')]),

    ("corner", "seenCorner", "keptCorner", "黑洞先生坐的那個角落",
     "她走到房間最裡面的角落。那裡的地板顏色比周圍淺了一圈。",
     ["地板的磨損是一個很規則的圓，大小剛好塞得下一團觸手。",
      "圓圈裡有幾道刮痕，很細，像硬殼反覆摩擦留下的。",
      "我從來沒有在這裡坐過。這不是我的尺寸。",
      "黑洞先生每天回來都窩在這裡。不餓的時候也窩著。"],
     "那個圓我已經量過了。地板不會在十分鐘裡改變形狀。",
     "角落的陰影隨著日落變濃。地板上那個淺色的圓被黑暗慢慢填滿。",
     "角落地板上的圓",
     [("keptBoots", 'feet', '「靴子是裝腳的東西。」\n「可是角落地板上那些刮痕，是觸手磨出來的。細細的，一道一道。」\n「坐在那裡的人沒有腳。可是門邊那疊靴子，每一雙都是照著腳的形狀做的。」\n她抬起頭。\n「黑洞先生以前有腳嗎？」')]),
]

# 他吃的是「她知道這件事」，不是東西本身。東西都還在原地，只是她不會再停下來看。
FEED = {
 "fridge": "東西還在冰箱裡，保鮮膜也還是那個折法。\n"
           "只是她今天想了一下午的那件事，晚上就沒有再想起來了。\n"
           "沒有人通知她那件事要走。",
 "window": "圓印還在窗台上，一點都沒有變淡。\n"
           "只是她以後走過去不會再停下來了。\n"
           "那個印子會一直在那裡，等一個不會再問的人。",
 "boots":  "裂痕還在。它今天晚上還會再裂長一點點。\n"
           "只是她明天看到，會覺得那本來就是裂的。",
 "rules":  "那兩行字還印在紙上，一個筆畫都沒有掉。\n"
           "只是她明天翻到那一頁，會覺得那是別人寫的。",
 "corner": "地板上那個圓還在，而且會愈來愈深。\n"
           "只是不會再有人問它是怎麼來的了。",
}

q = b.choice("d3n-q", "今天要陪她去看哪裡？\n" + MEM,
             [p[2] for p in PLACES])
b.link(b.prev, q)
hub = q          # 選擇卡本身就是 hub,不用另外一張

# 存進記憶體的共用零件（五個地點共用）
# 她早上就佔掉兩格(麵包、字跡),所以第三次留東西一定會擠掉最舊的那一格 ——
# 也就是「手裡這塊麵包」。順序固定,所以掉出去的是什麼算得出來,
# 可以寫成真正的台詞而不是泛泛的「你忘記了某個東西」。
store_gate, store_outs = b.store(
    "d3n-mem",
    "格莉奇說到一半停住了。\n「等一下。」\n她把手舉到眼前。\n翻過來，又翻回去。\n手心有一道很淺的壓痕。\n像剛剛握過有重量的東西。\n「我這隻手剛剛拿過東西。是什麼形狀的來著。」\n她握起來，鬆開，再握起來。\n想用手的形狀把那個東西想回來。\n想不回來。\n「……算了。應該不重要。」\n格莉奇把手放下。\n口袋裡有一張折得很整齊的保鮮膜。\n她沒有摸到，也不會知道那是誰折的。",
    overflow_ops=[{"variable": "lostBread", "kind": "set", "value": 1}],
    x=b.col(3), y=-700)

after = []          # 每個地點結束之後匯到這裡，接時間流逝
for i, (key, seen, kept, name, go, finds, again, missed, label, combos) in enumerate(PLACES):
    y = (i - 2) * 420
    x0 = b.col() if i == 0 else x0
    gx = 3000 + i * 0     # 位置只影響編輯畫面的可讀性
    # 已經看過了 → 不消耗次數，直接回 hub
    rep = b.say(f"d3n-{key}-again", again, face="平常", title=f"{name}（看過了）",
                x=1500, y=y - 130)
    b.link(q, rep, f"choice-{i}", cond={"variable": seen, "op": "eq", "value": 1})
    b.link(rep, hub)
    # 第一次去
    n_go = b.say(f"d3n-{key}-go", go, who=None, title=name, x=1500, y=y)
    b.link(q, n_go, f"choice-{i}")
    prev = n_go
    for j, line in enumerate(finds):
        n = b.say(f"d3n-{key}-f{j}", line, face="平常" if j < len(finds) - 1 else "發呆",
                  title=name, x=1800 + j * 300, y=y)
        b.link(prev, n); prev = n
    mark = b.setvar(f"d3n-{key}-mark",
                    [{"variable": seen, "kind": "set", "value": 1},
                     {"variable": "pending", "kind": "set", "value": label}],
                    text="", title=f"發現：{label}", x=1800 + len(finds) * 300, y=y)
    b.link(prev, mark)
    rq = b.choice(f"d3n-{key}-route", f"「{label}」這件事要放哪裡？\n" + MEM,
                  ["留在我這裡（今天晚上我還講得出來）",
                   "給黑洞先生吃（他會長回一隻腳）",
                   "交給你保管（留得住，但你要回來）"],
                  x=2100 + len(finds) * 300, y=y)
    b.link(mark, rq)
    keep_mark = b.setvar(f"d3n-{key}-keep", [{"variable": kept, "kind": "set", "value": 1}],
                         text="", title=f"留著：{label}",
                         x=2400 + len(finds) * 300, y=y)
    b.link(rq, keep_mark, "choice-0")
    # 搭檔已經在記憶格裡的話,當場接起來。走到這裡代表這一件一定留著了,
    # 所以只要比對方一個變數,不需要 AND。
    for ci, (partner, tag, text) in enumerate(combos):
        n = b.setvar(f"d3n-{key}-c{ci}",
                     [{"variable": "figured", "kind": "set", "value": tag}],
                     text=text, title=f"拼起來了：{tag}",
                     x=2700 + len(finds) * 300 + ci * 300, y=y - 150)
        b.link(keep_mark, n, "right", cond={"variable": partner, "op": "eq", "value": 1})
        b.link(n, store_gate)
    b.link(keep_mark, store_gate)      # 搭檔都不在就直接收進記憶格
    n_feed = b.setvar(f"d3n-{key}-feed",
                      [{"variable": "fedToday", "kind": "add", "value": 1},
                       {"variable": "fedCount", "kind": "add", "value": 1},
                       {"variable": "holeFeet", "kind": "add", "value": 1}],
                      text=FEED[key],
                      title="餵他", x=2400 + len(finds) * 300, y=y + 90)
    n_give = b.setvar(f"d3n-{key}-give",
                      [{"variable": "givenCount", "kind": "add", "value": 1},
                       {"variable": "heldItem", "kind": "set", "value": label}],
                      text="她講給你聽，講了兩次。\n"
                           "「你要記住喔。明天我會問你。」\n"
                           "她自己不會記得講過這句話。",
                      title="交給你", x=2400 + len(finds) * 300, y=y + 180)
    b.link(rq, n_feed, "choice-1"); b.link(rq, n_give, "choice-2")
    after += [n_feed, n_give]

after += store_outs

# ── 時間流逝 → 次數 -1 → 回 hub 或去晚上 ──
tick = b.setvar("d3n-tick", [{"variable": "looksLeft", "kind": "add", "value": -1}],
                text="", title="時間走了一段", x=4600, y=0)
for n in after:
    b.link(n, tick)

TIME = [
    ("d3n-t2", "陽光從窗框左側移到了中央。她的散熱風扇跟著降了一檔轉速。", 2),
    ("d3n-t1", "遠處傳來列車壓過鐵軌的悶響。她站在房間中央，還沒決定往哪裡走。", 1),
]
for nid, text, left in TIME:
    n = b.say(nid, text, who=None, title="時間", x=4900, y=(left - 1) * 200)
    b.link(tick, n, "right", cond={"variable": "looksLeft", "op": "eq", "value": left})
    b.link(n, hub)

dusk = b.say("d3n-dusk", "牆上的影子折到第三道彎。她講話開始重複同一個字，卡住，然後跳過去。",
             who=None, title="傍晚要到了", x=4900, y=-400)
b.link(tick, dusk)

# 沒去過的地方，在這裡各補一句。
# 用串接式:每一張都直接連到「後面所有還沒檢查的地點」,最後一條無條件的接晚上。
# 不用空白卡當匯流點——空 text 的對話卡在播放器裡是一個空的對話框,玩家要點過去。
missed_nodes = []
for i, (key, seen, kept, name, go, finds, again, missed, label, combos) in enumerate(PLACES):
    missed_nodes.append((seen, b.say(f"d3n-{key}-missed", missed, who=None,
                                     title=f"沒去{name}", x=5300 + i * 300, y=-420)))

# ══════════════════ 晚 ══════════════════
ev = b.scene("d3e-scene", "第三天・傍晚", "門口有腳步聲。天已經暗了。", "晚", x=7000, y=0)
for i, src in enumerate([dusk] + [n for _, n in missed_nodes]):
    for seen, tgt in missed_nodes[i:]:
        b.link(src, tgt, "right", cond={"variable": seen, "op": "eq", "value": 0})
    b.link(src, ev)
b.prev = ev
b.chain([
    ("d3e-in",    "門開了。黑洞先生滑進來，西裝下襬擦過地板。", "平常", None),
    ("d3e-first", "今天沒有麵包。", "預設", HOLE),
    ("d3e-huh",   "……你怎麼知道我今天有沒有麵包？", "發呆", G),
    ("d3e-none",  "黑洞先生沒有回答。\n他走向房間最裡面那個角落。", "平常", None),
    ("d3e-report","我今天記了一些東西。趁我還記得，現在報告一下。", "平常", G),
    ("d3e-list",  "我記得「{{slot1}}」、「{{slot2}}」、「{{slot3}}」、「{{slot4}}」。", "平常", G),
    ("d3e-gap",   "……有幾格是空的。空的那幾格我沒有辦法告訴你裡面本來有什麼，因為空的就是空的。", "發呆", G),
])

# 合併已經在中午發生過了（留下第二件的當下）。晚上只負責反應。
report = b.prev
cx = b.col(2)

# ══ 他的反應:依她拼出了什麼 ══
hx = cx + 1600
# 她今天拼出了什麼，他就回哪一句。這是他一天裡唯一會多說一句話的地方。
REACT = [
    ("dough", "妳每次都停在同一句。", "他說（發酵）"),
    ("hand",  "妳沒有剩下來。妳一直都在。", "他說（那個人是我嗎）"),
    ("feet",  "有過。", "他說（他以前有腳嗎）"),
]
react_join = b.say("d3e-react-join", "她等了一下，等到確定他不會再說第二句。",
                   who=None, title="等他", x=hx + 400, y=0)
for k, (tag, line, title) in enumerate(REACT):
    n = b.say(f"d3e-react-{tag}", line, who=HOLE, face="預設", title=title,
              x=hx, y=(k - 1) * 200)
    for src in [report]:
        b.link(src, n, "right", cond={"variable": "figured", "op": "eq", "value": tag})
    b.link(n, react_join)
quiet = b.say("d3e-react-none", "黑洞先生把外套掛好，坐進角落。\n今天的報告他沒有接。",
              who=None, title="他沒接", x=hx, y=400)
for src in [report]:
    b.link(src, quiet)
b.link(quiet, react_join)
b.prev = react_join

# ══ 麵包的去處 ══
# 她如果連麵包都忘了(記憶體滿了擠掉最舊的那一格),就沒得選——他自己去拿。
bx = b.col()
forgot = b.setvar("d3e-bread-forgot",
                  [{"variable": "breadState", "kind": "set", "value": "hole"},
                   {"variable": "fedToday", "kind": "add", "value": 1},
                   {"variable": "fedCount", "kind": "add", "value": 1},
                   {"variable": "holeFeet", "kind": "add", "value": 1}],
                  text="黑洞先生站起來，走到冰箱前面。\n打開，拿出那塊用保鮮膜包好的麵包。\n「那是什麼？」格莉奇問。\n他沒有回答。\n他把麵包收進西裝內袋。\n他不吃這種東西。從來沒有吃過。\n他吃掉的是「格莉奇烤過這塊麵包」這件事。\n那件事她今天弄丟了。\n她看著他收好。那個包裝手法有點眼熟。\n可是她想不起來在哪裡看過。",
                  title="她忘了麵包這件事", x=bx, y=-400)
b.link(react_join, forgot, "right", cond={"variable": "lostBread", "op": "eq", "value": 1})

b.chain([
    ("d3e-bread1", "還有一件事。冰箱裡那塊麵包。", "平常", G),
    ("d3e-bread2", "我今天一整天都沒有動它。它上面寫著給你，可是我不知道為什麼。", "平常", G),
    ("d3e-bread3", "黑洞先生沒有看冰箱的方向。他在等她自己決定。", "平常", None),
], x=bx, y=0, link_prev=False)
b.link(react_join, b.find("d3e-bread1")["id"])
bq = b.choice("d3e-breadq", "那塊麵包要怎麼辦？",
              ["拿給黑洞先生（他今天還沒吃東西）",
               "放回冰箱（明天她不會記得它在那裡）",
               "交給你保管（她再也不會知道自己烤過麵包）"],
              x=bx + 900, y=0)
b.link(b.prev, bq)
b_hole = b.setvar("d3e-bread-hole",
                  [{"variable": "breadState", "kind": "set", "value": "hole"},
                   {"variable": "fedToday", "kind": "add", "value": 1},
                   {"variable": "fedCount", "kind": "add", "value": 1},
                   {"variable": "holeFeet", "kind": "add", "value": 1}],
                  text="黑洞先生接過去。\n連紙條一起收進西裝內袋。\n他不吃麵包。\n他吃的是格莉奇本來要對他說的那句謝謝。\n那句話她今天沒有說出口。\n所以那句話成了他的。\n格莉奇覺得好像應該難過。\n可是想不起來為什麼。",
                  title="給他吃了", x=bx + 1200, y=-160)
b_self = b.setvar("d3e-bread-self",
                  [{"variable": "breadState", "kind": "set", "value": "self"}],
                  text="她把麵包放回冰箱，關門的時候特別輕。\n"
                       "門合上的那一刻，她已經在想別的事了。",
                  title="放回冰箱", x=bx + 1200, y=0)
b_play = b.setvar("d3e-bread-player",
                  [{"variable": "breadState", "kind": "set", "value": "player"},
                   {"variable": "givenCount", "kind": "add", "value": 1}],
                  text="她把保鮮膜的折法又演了一遍給你看。先對折兩次，再從中間往外壓。\n"
                       "像是在確認你真的記住了。",
                  title="交給你了", x=bx + 1200, y=160)
b.link(bq, b_hole, "choice-0"); b.link(bq, b_self, "choice-1"); b.link(bq, b_play, "choice-2")

rule_in = b.say("d3e-rule", "好吧。填守則。第 {{ruleVersion}} 版。", face="平常", who=G,
                x=bx + 1600, y=0)
for n in (forgot, b_hole, b_self, b_play): b.link(n, rule_in)
b.prev = rule_in

# 她今天拼出來的東西，只有寫進守則才活得過今晚。所以建議句依 figured 不同——
# 五家會審說上一版「拼出來只多幾句獨白，不改變任何事」，這裡是那句話的出口。
rx = b.col()
RULEIN = [
    ("dough", "我今天差點想起一件事。趁還沒忘，我要把它寫下來。",
     ["我以前會烤麵包。", "窗台上那個碗是拿來發酵的。", "「不要半夜開烤箱」是我自己寫的。"]),
    ("hand", "有一個比我穩的人用過我的手。我要把這件事留給明天的我。",
     ["守則本上的字是我寫的，只是比較早以前的我。",
      "我的手會做一些我的腦不知道的事。", "去比對筆跡。"]),
    ("feet", "我今天問了一個問題，他回答了。這種事不常發生。",
     ["黑洞先生以前有腳。他說有過。", "門邊的靴子是他的，不是別人的。",
      "問他腳是怎麼不見的。"]),
    ("none", "今天沒有拼出什麼。可是我還是得寫一句。",
     ["去看窗台。", "翻守則本，看前面幾天寫了什麼。",
      "問黑洞先生「以前」是什麼時候。"]),
]
rule_nodes = []
for k, (tag, lead, sug) in enumerate(RULEIN):
    n1 = b.say(f"d3e-lead-{tag}", lead, who=G, face="平常",
               title=f"守則引子（{tag}）", x=rx, y=(k - 1) * 260)
    n2 = b.add(f"d3e-in-{tag}", {"type": "input", "title": f"填空位（{tag}）",
        "text": "空位在這裡。今天要留什麼給明天的我？\n"
                "（明天早上的她會照著這句話做。她不會問為什麼。）",
        "inputVariable": "ruleLine3", "inputPlaceholder": sug[0],
        "inputSuggestions": sug}, x=rx + 320, y=(k - 1) * 260)
    b.link(n1, n2)
    if tag != "none":
        b.link(b.prev, n1, "right", cond={"variable": "figured", "op": "eq", "value": tag})
    else:
        b.link(b.prev, n1)
    rule_nodes.append(n2)
cur = b.setvar("d3e-rulever", [{"variable": "ruleVersion", "kind": "add", "value": 1},
                               {"variable": "dayCount", "kind": "set", "value": 3}],
               text="她一筆一畫寫上去。第 {{ruleVersion}} 版，完成。", title="守則 +1",
               x=rx + 700, y=0)
for n in rule_nodes: b.link(n, cur)
b.prev = cur
# 寫完唸一次給他聽。迴路要在今天閉合——五家裡有兩家說「明天才看得到後果，
# 本日不閉合」。他聽完的那句話，就是玩家今天寫的字第一次產生後果。
b.chain([
    ("d3e-read",  "我唸一次給你聽，確認我明天看得懂。", "平常", G),
    ("d3e-quote", "「{{ruleLine3}}」", "平常", G),
    ("d3e-hear",  "黑洞先生在角落，沒有轉頭。可是他的觸手停了一下，才繼續動。", "平常", None),
    ("d3e-ok",    "明天的我會照著這句做。她不會問為什麼，因為問了也沒有人會回答。", "平常", G),
    ("d3e-hm",    "嗯。", "預設", HOLE),
    ("d3e-save",  "記得存檔。今天這幾格，我自己留不住。", "平常", G),
    ("d3e-sleep", "她躺下的時候，把口袋裡的保鮮膜摺成更小的方塊。", "平常", None),
    ("d3e-hook1", "對了。今天交給你的那件事。", "平常", G),
    ("d3e-hook2", "明天早上我會問你那是什麼。我一定會忘記，所以我一定會問。", "平常", G),
    ("d3e-hook3", "你要想清楚再回答。答錯的話，那件事就真的沒有了。", "平常", G),
    ("d3e-crack", "而在她看不見的黑暗裡，門邊那雙裂開的短靴。\n裂痕又往鞋帶孔的方向裂了一點。", "平常", None),
])
b.link(b.prev, b.jump("d3e-jump", "board-day4", "d4m-scene"))
b.push("Day 3 改成探索日:五個地方只看得了三個,4KB 真的會滿,晚上她只講得出還在格子裡的")
