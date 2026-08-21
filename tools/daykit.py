"""建每日白板的共用零件。五天各自的內容寫在 build_dayN.py,骨架都在這裡。

腳本掉過一次(放在 session 暫存目錄被清掉),所以這些檔案一律放 ~/glitch-vn/tools/。
"""
import pathlib, json, pathlib, urllib.request

KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
PROJ = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
BASE = f"https://larch.yapiflow.com/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
A = json.loads((pathlib.Path(__file__).resolve().parent.parent / "backup" / "assets.json").read_text())

G, HOLE = "格莉奇", "黑洞先生"
CID = {G: "character-15c41e1f-ca37-424f-8c49-ac1031a42928",
       HOLE: "character-25c9632f-cd67-49d0-a4bd-2757b51127e7"}
FACE = {"平常": A["glitch-plain"], "預設": A["glitch-idle"], "開心": A["glitch-happy"],
        "發呆": A["glitch-thinking"], "當機": A["glitch-error"], "睡著": A["glitch-sleep"]}
BG = {"早": A["bg-morning"], "中": A["bg-noon"], "晚": A["bg-night"],
      # 新前提（VTuber 版）的三段。下播後那張是天花板——鏡頭倒在桌上忘了關。
      "開播前": A["bg-pre"], "直播中": A["bg-live"], "下播後": A["bg-ceiling"]}

# 三個去處的選項字面,五天共用同一組,玩家才學得起來
ROUTES = ["留在我這裡（明天睡醒就忘了）",
          "給黑洞先生吃（他會長回一隻腳）",
          "交給你保管（留得住，但你要回來）"]
# 新前提（VTuber 版）。她睡前做的三個動作，不是「決定要忘掉什麼」。
NIGHT = ["她自己複誦一遍", "講給你聽，講兩次", "什麼都不做"]
STATUS = "（記憶體 {{slotUsed}}／4　黑洞先生今天吃了 {{fedToday}}／1）"


def _api(data=None, method="GET", tries=4):
    """Larch 偶爾回 502,不是我們的問題,但每次手動重跑很煩。退避重試。"""
    import time
    body = json.dumps(data).encode() if data is not None else None
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(
                BASE, body, H, method=method), timeout=180))
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == tries - 1: raise
            print(f"  Larch 回 {e.code}，{2 ** i * 5} 秒後重試（第 {i + 1} 次）")
            time.sleep(2 ** i * 5)


def _get(): return _api()
def _put(payload): return _api(payload, "PUT")


class Board:
    def __init__(self, bid, name, desc):
        self.bid, self.name, self.desc = bid, name, desc
        self.nodes, self.edges, self.prev, self._x = [], [], None, 0
        # 下播之後鏡頭朝著天花板，玩家看不到她。這個旗標一開，台詞就不帶立繪。
        self.voiceonly = False

    def col(self, step=1):
        self._x += 300 * step
        return self._x

    def add(self, nid, data, x=None, y=0):
        # id 撞名不會報錯,只會讓 link 接到錯的那張,在圖上變成環。Day 6 踩過一次。
        assert not any(n["id"] == nid for n in self.nodes), f"卡片 id 重複：{nid}"
        self.nodes.append({"id": nid, "type": "story",
                           "position": {"x": self.col() if x is None else x, "y": y}, "data": data})
        return nid

    def say(self, nid, text, who=G, face="平常", title="", x=None, y=0):
        d = {"type": "dialogue", "title": title or text[:16], "text": text, "characterPosition": "center"}
        if who in (G, HOLE):
            d.update(speaker=who, characterId=CID[who],
                     emotion=face if who == G else ("飽" if face == "飽" else "餓"))
            if not self.voiceonly:
                d["character"] = (FACE[face] if who == G else
                                  (A["blackhole-full"] if face == "飽" else A["blackhole-hungry"]))
        else:
            d["speaker"] = "旁白"; d["title"] = title or "旁白"
        return self.add(nid, d, x, y)

    def chat(self, nid, lines, title="留言區", x=None, y=0):
        """留言區。玩家的留言只是幾千則裡的一則，所以假留言要真的長得像留言。

        lines = ["小夜：你昨天說要開新企劃", ...]
        """
        return self.add(nid, {"type": "dialogue", "title": title,
                              "text": "\n".join(lines), "speaker": "留言區"}, x, y)

    def hole(self, key, ask, comments, answer, after_hit, after_miss,
             ops_hit=(), x=None, y=0):
        """她卡住的一個洞。玩家一天只有三次搶答，用在哪幾次是玩家的選擇。

        搶答用次數不用亂數：`savesLeft` 用完之後那條路走不進去，
        走進去的會扣一次。沒搶的洞由別的粉絲補，她照樣唸，有時候唸到錯的。
        """
        a = self.say(f"{key}-ask", ask, face="發呆")
        if self.prev: self.link(self.prev, a)
        c = self.chat(f"{key}-chat", comments)
        self.link(a, c)
        q = self.choice(f"{key}-q", f"要搶這一題嗎？（今天還剩 {{{{savesLeft}}}} 次）",
                        [f"打字：「{answer}」", "這一題放著"])
        self.link(c, q)
        bx = self.col()
        used = self.say(f"{key}-used", "你的搶答今天用完了。你看著別人搶。",
                        who="旁白", x=bx, y=-240)
        hit = self.setvar(f"{key}-hit",
                          [{"variable": "savesLeft", "kind": "add", "value": -1},
                           {"variable": "savedCount", "kind": "add", "value": 1}, *ops_hit],
                          text="", title="搶到了", x=bx, y=0)
        # 空的對話卡在播放器上是一張要點掉的空白框，所以用 setVariable 當中繼。
        miss = self.setvar(f"{key}-miss", [], text="", title="放著", x=bx, y=240)
        # 次數用完就走不進搶答那條
        self.link(q, used, "choice-0",
                  cond={"variable": "savesLeft", "op": "lte", "value": 0})
        self.link(q, hit, "choice-0")
        self.link(q, miss, "choice-1")
        h = self.say(f"{key}-after-hit", after_hit, face="開心", x=bx + 300, y=0)
        self.link(hit, h)
        m = self.say(f"{key}-after-miss", after_miss, face="平常", x=bx + 300, y=240)
        self.link(miss, m); self.link(used, m)
        end = self.setvar(f"{key}-end", [], text="", title="接回主線", x=bx + 600, y=0)
        self.link(h, end); self.link(m, end)
        self.prev = end
        return end, hit

    def scene(self, nid, title, text, seg, bgm=None, start=False, x=None, y=0):
        d = {"type": "scene", "title": title, "text": text, "background": BG[seg]}
        if bgm: d.update(bgm=bgm, bgmVolume=0.3, bgmLoop=True)
        if start: d["start"] = True
        return self.add(nid, d, x, y)

    def choice(self, nid, text, opts, title="選擇", x=None, y=0):
        return self.add(nid, {"type": "choice", "title": title, "text": text,
                              "choices": opts, "choiceMode": "branch"}, x, y)

    def setvar(self, nid, ops, text="", title="記錄", x=None, y=0):
        return self.add(nid, {"type": "setVariable", "title": title, "text": text,
                              "variableOps": [{"id": f"op-{i}", **o} for i, o in enumerate(ops)]}, x, y)

    def jump(self, nid, board_id, node_id, text="天亮了。", title="下一天", x=None, y=0):
        return self.add(nid, {"type": "boardJump", "title": title, "text": text,
                              "jumpBoardId": board_id, "jumpNodeId": node_id}, x, y)

    def link(self, a, b, handle="right", cond=None):
        # id 要唯一。用「來源＋出口＋目標」當 id 的話,同一組多條件的線會全部撞在
        # 一起(二週目八個暗號都是 hub→yes)。功能上 Larch 照單全收,可是編輯器的
        # 圖用 id 當 key,而且下次誰去重就會被吃掉。加序號。
        self._eid = getattr(self, "_eid", 0) + 1
        e = {"id": f"e{self._eid}-{a}-{handle}-{b}", "source": a, "target": b,
             "sourceHandle": handle, "animated": True}
        if cond: e["data"] = {"condition": {"kind": "variable", **cond}}
        self.edges.append(e)

    def find(self, nid):
        return next(n for n in self.nodes if n["id"] == nid)

    def settext(self, nid, text):
        """改一張已經存在的卡的台詞。反推回來的板子用這個打磨,比重寫整張安全。"""
        self.find(nid)["data"]["text"] = text

    def redirect(self, old_target, new_target, keep=()):
        """把所有指向 old_target 的線改指向 new_target。

        要在既有的匯流點前面插一個閘門的時候用。直接對來源加一條有條件的線是
        沒用的——那些來源可能已經有別的有條件的線,而且一定會有一條命中,
        新加的永遠輪不到。Day 4 晚上踩過。
        """
        n = 0
        for e in self.edges:
            if e["target"] == old_target and e["source"] not in keep:
                e["target"] = new_target
                self._eid = getattr(self, "_eid", 0) + 1
                e["id"] = (f"e{self._eid}-{e['source']}-"
                           f"{e.get('sourceHandle','right')}-{new_target}")
                n += 1
        assert n, f"沒有線指向 {old_target}"
        return n

    def dropop(self, nid, variable):
        """拿掉某張卡對某個變數的操作。

        反推回來的卡片自己會加 slotUsed,而共用的記憶格零件也會加——重複計數,
        結果是還沒滿就被當成滿了。這種錯只有模擬器抓得到:
        「該走到的存放分支一個都沒走到,而溢位那條走到了」。
        """
        d = self.find(nid)["data"]
        d["variableOps"] = [o for o in d.get("variableOps", [])
                            if o.get("variable") != variable]

    def addops(self, nid, ops):
        d = self.find(nid)["data"]
        base = d.setdefault("variableOps", [])
        base += [{"id": f"op-{len(base) + i}", **o} for i, o in enumerate(ops)]

    def remove(self, nid):
        """刪掉一張卡連同它的線。搬走內容之後原卡要刪,不然會變成走不到的孤兒。"""
        n = len(self.nodes)
        self.nodes[:] = [x for x in self.nodes if x["id"] != nid]
        assert len(self.nodes) < n, f"本來就沒有這張卡：{nid}"
        self.edges[:] = [e for e in self.edges
                         if e["source"] != nid and e["target"] != nid]

    def unlink(self, a, b):
        n = len(self.edges)
        self.edges[:] = [e for e in self.edges if not (e["source"] == a and e["target"] == b)]
        assert len(self.edges) < n, f"本來就沒有這條線：{a} -> {b}"

    def chain(self, items, y=0, x=None, link_prev=True):
        """[(id, 文字, 表情, 說話者)] 串成一直線,自動接上前一張。

        分支用 x=起點、link_prev=False:這樣不會接到 self.prev,回傳的
        list 可以拿 [0] 當入口、[-1] 當出口自己接線。
        """
        made = []
        for i, (nid, text, face, who) in enumerate(items):
            cur = self.say(nid, text, who=who, face=face, y=y,
                           x=None if x is None else x + 300 * i)
            if made:
                self.link(made[-1], cur)
            elif link_prev and self.prev:
                self.link(self.prev, cur)
            made.append(cur)
            self.prev = cur
        return made

    def route(self, key, var, intro, intro_face, question, t_keep, t_feed, t_give,
              after, after_face="平常", extra_keep=(), extra_feed=(), extra_give=()):
        """一件事的三去處分流。留著佔格、餵他長腳、交給玩家累加。"""
        a = self.say(f"{key}-intro", intro, face=intro_face)
        self.link(self.prev, a)
        c = self.choice(f"{key}-q", question + "\n" + STATUS, ROUTES)
        self.link(a, c)
        bx = self.col()
        k = self.setvar(f"{key}-keep", [{"variable": "slotUsed", "kind": "add", "value": 1},
                                        *extra_keep, *([{"variable": var, "kind": "set", "value": 1}] if var else [])],
                        text=t_keep, title="留著", x=bx, y=-240)
        f = self.setvar(f"{key}-feed", [{"variable": "fedToday", "kind": "add", "value": 1},
                                        {"variable": "fedCount", "kind": "add", "value": 1},
                                        {"variable": "holeFeet", "kind": "add", "value": 1},
                                        *extra_feed, *([{"variable": var, "kind": "set", "value": 1}] if var else [])],
                        text=t_feed, title="餵他", x=bx, y=0)
        g = self.setvar(f"{key}-give", [{"variable": "givenCount", "kind": "add", "value": 1},
                                        *extra_give, *([{"variable": var, "kind": "set", "value": 1}] if var else [])],
                        text=t_give, title="交給你", x=bx, y=240)
        self.link(c, k, "choice-0"); self.link(c, f, "choice-1"); self.link(c, g, "choice-2")
        aft = self.say(f"{key}-after", after, face=after_face)
        for b in (k, f, g): self.link(b, aft)
        self.prev = aft
        return aft

    def pool(self, key, events, roll_var="todayEvent", after_text="好。那我們等黑洞先生回來。"):
        """隨機事件池。

        events = [(短名, 去重變數, 介紹文, 表情, 留著文, 餵他文, 交給你文, 記憶格標籤)]

        每個事件要有自己的三去處結果——共用一張選擇卡做不到,因為 choice 的
        handle 只有一組。所以每個事件各配一張選擇卡。

        去重用「閘門往下掉」:抽到用過的就接到下一個事件的閘門,最後一個當保底。
        不用重抽迴圈,因為那在圖上會變成環,而且理論上可能一直抽到用過的。
        """
        roll = self.setvar(f"{key}-roll",
                           [{"variable": roll_var, "kind": "random", "min": 1, "max": len(events)}],
                           text="", title="抽今天的事件")
        self.link(self.prev, roll)
        gx = self.col()
        gates, tails, keeps = [], [], []
        for i, (name, used, intro, face, t_keep, t_feed, t_give, label) in enumerate(events):
            y = (i - len(events) / 2) * 300
            g = self.say(f"{key}-{name}", intro, face=face, title=f"事件{i+1}", x=gx, y=y)
            gates.append(g)
            self.link(roll, g, "right", cond={"variable": roll_var, "op": "eq", "value": i + 1})
            c = self.choice(f"{key}-{name}-q", "這件事要放哪裡？\n" + STATUS, ROUTES,
                            x=gx + 300, y=y)
            self.link(g, c)
            # 記憶體滿了要有代價,不然「留著」跟「交給你」在故事層都只是東西不見了。
            # 四家會審都點這一項:第 4 格之後再留,就會擠掉一件她不知道是什麼的舊事。
            k = self.setvar(f"{key}-{name}-keep",
                            [{"variable": "pending", "kind": "set", "value": label or name},
                             {"variable": "todayRoute", "kind": "set", "value": "keep"},
                             {"variable": used, "kind": "set", "value": 1}],
                            text=t_keep, title="留著", x=gx + 600, y=y - 150)
            f = self.setvar(f"{key}-{name}-feed",
                            [{"variable": "fedToday", "kind": "add", "value": 1},
                             {"variable": "fedCount", "kind": "add", "value": 1},
                             {"variable": "holeFeet", "kind": "add", "value": 1},
                             {"variable": "todayRoute", "kind": "set", "value": "feed"},
                             {"variable": used, "kind": "set", "value": 1}],
                            text=t_feed, title="餵他", x=gx + 600, y=y)
            gg = self.setvar(f"{key}-{name}-give",
                             [{"variable": "givenCount", "kind": "add", "value": 1},
                              {"variable": "todayRoute", "kind": "set", "value": "give"},
                              {"variable": used, "kind": "set", "value": 1}],
                             text=t_give, title="交給你", x=gx + 600, y=y + 90)
            self.link(c, k, "choice-0")
            self.link(c, f, "choice-1"); self.link(c, gg, "choice-2")
            keeps.append(k)
            tails += [f, gg]
        # 抽到用過的就掉到下一個;最後一個當保底
        for i in range(len(gates) - 1):
            self.link(gates[i], gates[i + 1], "right",
                      cond={"variable": events[i][1], "op": "eq", "value": 1})
        self.link(roll, gates[-1])
        # 所有「留著」都走同一組記憶格:滿了最舊的自己掉出去,她沒得挑。
        store_gate, store_outs = self.store(
            f"{key}-mem",
            "她說到一半停住了。「等一下。我剛剛腦子裡有一個東西，它剛剛還在的。」\n"
            "她低頭，然後抬頭，然後放棄。最舊的那一格自己掉出去了，"
            "她連它存在過都不知道。",
            x=gx + 900, y=-700)
        for k_ in keeps: self.link(k_, store_gate)
        tails += store_outs
        aft = self.say(f"{key}-after", after_text, x=gx + 1400, y=0)
        for t in tails: self.link(t, aft)
        self.prev = aft
        return aft

    def recall(self, key, question, items, x=0, y=0):
        """昨天你替她保管的東西，今天她問你那是什麼。答對她才拿得回去。

        這是整個遊戲的論點做成玩法：你是她的記憶，所以被考的是**你的**記憶。
        原型裡本來就有（「我今天好像學過一種貓叫。你還記得怎麼叫嗎？」），
        做成七天迴圈的時候掉了，現在接回來。

        items = [(標籤, 答對的話她說什麼, 答錯的話她說什麼)]
        選項固定，正確答案靠 heldItem 比對——所以同一張選擇卡可以考任何一件。
        """
        q = self.choice(f"{key}-q", question, [it[0] for it in items], x=x, y=y)
        outs = []
        for i, (label, ok_text, no_text) in enumerate(items):
            ok = self.setvar(
                f"{key}-ok{i}",
                [{"variable": "recallOk", "kind": "set", "value": 1},
                 {"variable": "pending", "kind": "set", "value": label},
                 {"variable": "givenCount", "kind": "add", "value": -1},
                 {"variable": "heldItem", "kind": "set", "value": ""}],
                text=ok_text, title=f"答對：{label}", x=x + 400, y=y + (i - 2) * 130)
            self.link(q, ok, f"choice-{i}",
                      cond={"variable": "heldItem", "op": "eq", "value": label})
            no = self.setvar(
                f"{key}-no{i}",
                [{"variable": "recallOk", "kind": "set", "value": 2},
                 {"variable": "heldItem", "kind": "set", "value": ""}],
                text=no_text, title=f"答錯：{label}", x=x + 400, y=y + (i - 2) * 130 + 60)
            self.link(q, no, f"choice-{i}")
            outs.append((ok, no))
        return q, outs

    def wake(self, key, prefill=(), looks=0, day=0, x=None, y=0):
        """開機：清空記憶格。她每天睡醒清空，所以每一天都要走這一步。

        prefill = 醒來就已經佔掉的格子（例如 Day 3 手裡那塊麵包）。
        沒有這個的話，一整天都填不滿四格，「滿了會掉出去」就永遠不會發生。
        """
        ops = [{"variable": "slotUsed", "kind": "set", "value": len(prefill)},
               {"variable": "fedToday", "kind": "set", "value": 0},
               {"variable": "figured", "kind": "set", "value": ""},
               {"variable": "lostBread", "kind": "set", "value": 0},
               {"variable": "pending", "kind": "set", "value": ""}]
        for i in range(4):
            ops.append({"variable": f"slot{i+1}", "kind": "set",
                        "value": prefill[i] if i < len(prefill) else ""})
        if looks:
            ops.append({"variable": "looksLeft", "kind": "set", "value": looks})
        if day:
            ops.append({"variable": "dayNow", "kind": "set", "value": day})
        return self.setvar(f"{key}-wake", ops, text="", title="開機：記憶體清空", x=x, y=y)

    # ── 探索日用的零件 ────────────────────────────────────
    def store(self, key, overflow_text, overflow_ops=(), x=0, y=0):
        """把 pending 存進記憶格。滿了就先進先出——最舊的自己掉出去。

        **不讓玩家挑要丟哪一格。** 五家會審都說強制刪除玩起來像資源管理作業,
        而且那不符合她:她記不住的東西是自己掉出去的,她沒得挑。玩家只能看著
        最早的那件掉出去,擋不住。這樣痛的方向才對。

        先進先出用 valueFrom 一路往前搬(slot1←slot2←slot3←slot4←pending)。
        因為順序是固定的,掉出去的是哪一件可以事先算得出來,所以掉出去那張卡
        可以寫成真正的台詞,不是泛泛的「你忘記了某個東西」。
        """
        gate = self.setvar(f"{key}-gate", [], text="", title="放進記憶體", x=x, y=y)
        outs = []
        for i in range(4):
            n = self.setvar(
                f"{key}-s{i+1}",
                [{"variable": f"slot{i+1}", "kind": "set", "valueFrom": "pending"},
                 {"variable": "slotUsed", "kind": "add", "value": 1}],
                text="", title=f"存進第 {i+1} 格", x=x + 300, y=y + (i - 2) * 110)
            self.link(gate, n, "right",
                      cond={"variable": "slotUsed", "op": "eq", "value": i})
            outs.append(n)
        # 滿了:最舊的自己掉出去,往前推一格
        shift = self.setvar(
            f"{key}-shift",
            [{"variable": "slot1", "kind": "set", "valueFrom": "slot2"},
             {"variable": "slot2", "kind": "set", "valueFrom": "slot3"},
             {"variable": "slot3", "kind": "set", "valueFrom": "slot4"},
             {"variable": "slot4", "kind": "set", "valueFrom": "pending"},
             {"variable": "overwroteCount", "kind": "add", "value": 1},
             *overflow_ops],
            text=overflow_text, title="最舊的掉出去了", x=x + 300, y=y + 300)
        self.link(gate, shift)
        outs.append(shift)
        return gate, outs

    def keepstore(self, key, x=0, y=0, n=6):
        """玩家保管的東西存進 kept1…keptN。

        跟 store() 不一樣的地方：**玩家不會忘記**，所以滿了不往前推，
        多的那件只加計數不佔名額（第七天挑得出來的就是有名字的那幾件）。
        """
        gate = self.setvar(f"{key}-gate", [], text="", title="交給玩家保管", x=x, y=y)
        outs = []
        for i in range(n):
            c = self.setvar(
                f"{key}-k{i+1}",
                [{"variable": f"kept{i+1}", "kind": "set", "valueFrom": "pending"},
                 {"variable": "keptCount", "kind": "add", "value": 1},
                 # 第四天的記憶考只考第一件，所以只有第一件要記是哪一天的。
                 *([{"variable": "keptFrom1", "kind": "set", "valueFrom": "dayNow"}]
                   if i == 0 else [])],
                text="", title=f"第 {i+1} 件", x=x + 300, y=y + (i - n / 2) * 110)
            self.link(gate, c, "right",
                      cond={"variable": "keptCount", "op": "eq", "value": i})
            outs.append(c)
        over = self.setvar(f"{key}-over", [{"variable": "keptCount", "kind": "add", "value": 1}],
                           text="", title="超過六件", x=x + 300, y=y + n * 60)
        self.link(gate, over)
        outs.append(over)
        return gate, outs

    def settle(self, key, x=0, y=0):
        """下播後的四格結算。她睡前對還在手上的四件做三個動作之一。

        空的格子跳過——空的格子沒有東西可以處置，硬演會變成點空白卡。

        「交給你保管」要走共用的 keepstore，可是那個區塊不知道自己是從第幾格
        進來的。用 `settleAt` 記現在做到第幾格，保管完再照這個數字回到下一格。
        """
        ks_gate, ks_outs = self.keepstore(f"{key}-ks", x=x + 1500, y=y - 500)
        hub = self.setvar(f"{key}-kshub", [], text="", title="保管完", x=x + 1900, y=y - 500)
        for o in ks_outs: self.link(o, hub)
        after = self.setvar(f"{key}-done", [], text="", title="結算完", x=x + 2300, y=y + 1050)
        gates, nexts = [], []
        for i in range(4):
            sy = y + i * 700
            g = self.setvar(f"{key}-g{i+1}",
                            [{"variable": "settleAt", "kind": "set", "value": i + 1}],
                            text="", title=f"第 {i+1} 格", x=x, y=sy)
            gates.append(g)
        for i in range(4):
            sy = y + i * 700
            nxt = gates[i + 1] if i + 1 < 4 else after
            nexts.append(nxt)
            g = gates[i]
            say = self.say(f"{key}-say{i+1}", f"第 {i+1} 件，{{{{slot{i+1}}}}}。",
                           face="平常", x=x + 300, y=sy)
            # 空格跳過（有條件的先判，所以這條要在無條件那條之前加）
            self.link(g, nxt, "right", cond={"variable": f"slot{i+1}", "op": "eq", "value": ""})
            self.link(g, say)
            c = self.choice(f"{key}-q{i+1}", "這一件怎麼辦？", NIGHT, x=x + 600, y=sy)
            self.link(say, c)
            keep = self.say(f"{key}-keep{i+1}",
                            f"{{{{slot{i+1}}}}}。{{{{slot{i+1}}}}}。好，記起來了。",
                            face="開心", x=x + 900, y=sy - 200)
            give = self.setvar(f"{key}-give{i+1}",
                               [{"variable": "pending", "kind": "set", "valueFrom": f"slot{i+1}"}],
                               text=f"{{{{name}}}}，你幫我記著喔。{{{{slot{i+1}}}}}。\n"
                                    f"我再講一次，{{{{slot{i+1}}}}}。你記住了嗎？",
                               title="交給你", x=x + 900, y=sy)
            let = self.setvar(f"{key}-let{i+1}",
                              [{"variable": "fedCount", "kind": "add", "value": 1},
                               {"variable": "holeFeet", "kind": "add", "value": 1}],
                              text="這件……算了。", title="讓它去", x=x + 900, y=sy + 200)
            self.link(c, keep, "choice-0")
            self.link(c, give, "choice-1")
            self.link(c, let, "choice-2")
            self.link(give, ks_gate)
            self.link(keep, nxt); self.link(let, nxt)
        # 保管完照 settleAt 回到下一格
        for i in range(3):
            self.link(hub, nexts[i], "right",
                      cond={"variable": "settleAt", "op": "eq", "value": i + 1})
        self.link(hub, after)
        self.prev = after
        return gates[0], after

    def andlink(self, src, conds, target, fallthrough, x=0, y=0, key=None):
        """條件的 AND。邊的條件一次只能比一個變數,所以串起來走。

        src --(A)--> 中繼 --(B)--> target
         └--(預設)--> fallthrough      中繼 --(預設)--> fallthrough
        """
        prev = src
        for i, c in enumerate(conds[:-1]):
            mid = self.setvar(f"{key}-and{i}", [], text="", title="檢查",
                              x=x + i * 200, y=y)
            self.link(prev, mid, "right", cond=c)
            self.link(prev, fallthrough)
            prev = mid
        self.link(prev, target, "right", cond=conds[-1])
        self.link(prev, fallthrough)

    def split_narration(self):
        """把混在台詞裡的括號旁白拆成獨立的旁白卡。

        「（她走出去了。）」寫在格莉奇的對話卡裡，播放器會讓她**把括號唸出來**，
        而且立繪還掛在旁邊。寫劇本的時候很自然就會這樣寫，所以靠自動拆，不靠記性。

        原卡留第一段，後面每一段各長一張卡，原本的出線接到最後一張。
        """
        for n in list(self.nodes):
            d = n["data"]
            if d.get("type") != "dialogue" or d.get("speaker") not in (G, HOLE):
                continue
            lines = [l for l in (d.get("text") or "").split("\n") if l.strip()]
            if not any(l.strip().startswith("（") and l.strip().endswith("）") for l in lines):
                continue
            runs = []
            for l in lines:
                nar = l.strip().startswith("（") and l.strip().endswith("）")
                if runs and runs[-1][0] == nar:
                    runs[-1][1].append(l)
                else:
                    runs.append((nar, [l]))
            nid, x, y = n["id"], n["position"]["x"], n["position"]["y"]
            outs = [e for e in self.edges if e["source"] == nid]
            first_nar, first_lines = runs[0]
            d["text"] = "\n".join(l.strip("（）") if first_nar else l for l in first_lines)
            if first_nar:
                d["speaker"] = "旁白"
                for k in ("character", "characterId", "emotion"):
                    d.pop(k, None)
            d["title"] = d["text"][:16]
            prev = nid
            for i, (nar, ls) in enumerate(runs[1:], 1):
                txt = "\n".join(l.strip("（）") if nar else l for l in ls)
                cur = self.say(f"{nid}-n{i}", txt,
                               who="旁白" if nar else d.get("speaker", G),
                               face=d.get("emotion") or "平常",
                               x=x + 40 * i, y=y + 70 * i)
                self.link(prev, cur)
                prev = cur
            for e in outs:
                e["source"] = prev
                self._eid = getattr(self, "_eid", 0) + 1
                e["id"] = f"e{self._eid}-{prev}-{e.get('sourceHandle','right')}-{e['target']}"

    def push(self, summary):
        self.split_narration()
        proj = _get()
        boards = [b for b in proj["boards"] if b["id"] != self.bid]
        boards.append({"id": self.bid, "kind": "story", "mode": "story",
                       "name": self.name, "description": self.desc,
                       "nodes": self.nodes, "edges": self.edges})
        proj["boards"] = boards
        r = _put({"project": proj, "summary": summary})
        b = [x for x in r["boards"] if x["id"] == self.bid][0]
        # 這塊板用到的變數，推完之後確認還在。
        # 平台不穩的時候整包 PUT 有可能把變數蓋掉，而卡片照樣存進去——
        # 症狀是「動了不存在的變數」，但要跑 verify 才看得到,推的當下沒有任何徵兆。
        have = {v["name"] for v in r.get("variables", [])}
        used = {op["variable"] for n in self.nodes
                for op in (n["data"].get("variableOps") or [])}
        used |= {n["data"]["inputVariable"] for n in self.nodes
                 if n["data"].get("inputVariable")}
        used |= {e["data"]["condition"]["variable"] for e in self.edges
                 if (e.get("data") or {}).get("condition")}
        lost = sorted(used - have)
        print(f"{self.name}：卡片 {len(b['nodes'])}  邊 {len(b['edges'])}"
              + (f"　★ 變數不見了：{'、'.join(lost)}" if lost else ""))
        return r


def add_variables(new):
    """new = [(name, type, label, desc, default)]，已存在的跳過"""
    proj = json.load(urllib.request.urlopen(urllib.request.Request(BASE, headers=H), timeout=120))
    have = {v["name"] for v in proj["variables"]}
    added = []
    for n, t, label, desc, dv in new:
        if n not in have:
            proj["variables"].append({"id": n, "name": n, "type": t,
                                      "label": label, "description": desc, "defaultValue": dv})
            added.append(n)
    if added:
        json.load(urllib.request.urlopen(urllib.request.Request(
            BASE, json.dumps({"project": proj, "summary": f"加變數：{'、'.join(added)}"}).encode(),
            H, method="PUT"), timeout=180))
    print("新增變數:", added or "無")
