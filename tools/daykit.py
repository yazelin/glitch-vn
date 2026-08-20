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
BG = {"早": A["bg-morning"], "中": A["bg-noon"], "晚": A["bg-night"]}

# 三個去處的選項字面,五天共用同一組,玩家才學得起來
ROUTES = ["留在我這裡（明天睡醒就忘了）",
          "給黑洞先生吃（他會長回一隻腳）",
          "交給你保管（留得住，但你要回來）"]
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
                     emotion=face if who == G else ("飽" if face == "飽" else "餓"),
                     character=FACE[face] if who == G else
                               (A["blackhole-full"] if face == "飽" else A["blackhole-hungry"]))
        else:
            d["speaker"] = "旁白"; d["title"] = title or "旁白"
        return self.add(nid, d, x, y)

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
        e = {"id": f"e-{a}-{handle}-{b}", "source": a, "target": b,
             "sourceHandle": handle, "animated": True}
        if cond: e["data"] = {"condition": {"kind": "variable", **cond}}
        self.edges.append(e)

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

        events = [(短名, 去重變數, 介紹文, 表情, 留著文, 餵他文, 交給你文)]

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
        gates, tails = [], []
        for i, (name, used, intro, face, t_keep, t_feed, t_give) in enumerate(events):
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
                            [{"variable": "slotUsed", "kind": "add", "value": 1},
                             {"variable": "todayRoute", "kind": "set", "value": "keep"},
                             {"variable": used, "kind": "set", "value": 1}],
                            text=t_keep, title="留著", x=gx + 600, y=y - 150)
            kf = self.setvar(f"{key}-{name}-full",
                             [{"variable": "overwroteCount", "kind": "add", "value": 1},
                              {"variable": "todayRoute", "kind": "set", "value": "keep"},
                              {"variable": used, "kind": "set", "value": 1}],
                             text="她硬塞進去。4KB 滿了，某個舊的東西被擠出來——"
                                  "她不知道被擠掉的是什麼，因為被擠掉的東西連同「它存在過」一起沒了。",
                             title="留著（滿了）", x=gx + 600, y=y - 60)
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
            self.link(c, kf, "choice-0",
                      cond={"variable": "slotUsed", "op": "gte", "value": 4})
            self.link(c, k, "choice-0")
            self.link(c, f, "choice-1"); self.link(c, gg, "choice-2")
            tails += [k, kf, f, gg]
        # 抽到用過的就掉到下一個;最後一個當保底
        for i in range(len(gates) - 1):
            self.link(gates[i], gates[i + 1], "right",
                      cond={"variable": events[i][1], "op": "eq", "value": 1})
        self.link(roll, gates[-1])
        aft = self.say(f"{key}-after", after_text, x=gx + 1000, y=0)
        for t in tails: self.link(t, aft)
        self.prev = aft
        return aft

    def push(self, summary):
        proj = _get()
        boards = [b for b in proj["boards"] if b["id"] != self.bid]
        boards.append({"id": self.bid, "kind": "story", "mode": "story",
                       "name": self.name, "description": self.desc,
                       "nodes": self.nodes, "edges": self.edges})
        proj["boards"] = boards
        r = _put({"project": proj, "summary": summary})
        b = [x for x in r["boards"] if x["id"] == self.bid][0]
        print(f"{self.name}：卡片 {len(b['nodes'])}  邊 {len(b['edges'])}")
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
