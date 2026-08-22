"""小說版的白板建構器。

跟舊版那支 daykit 完全不同：這裡沒有變數、沒有條件邊、沒有記憶格。
小說是線性的，所以骨架只有「場景 → 一連串卡片 → 下一章」。

用得到的兩個平台功能（2026-08-22 從前端 bundle 挖出來的）：
  characterLayers  一張卡可以站好幾個人，各自有位置、縮放、翻轉
  dialogueLines    一張卡可以裝一整段來回對話，不必一句一張卡

這兩個加起來，散文式的對話段落才排得出來。
"""
import json, pathlib, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
BASE = f"https://larch.yapiflow.com/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
A = json.loads((ROOT / "larch/assets.json").read_text())

G, HOLE, NARRATOR = "格莉奇", "黑洞先生", "旁白"
SPRITE = {G: "sprite-glitch", HOLE: "sprite-blackhole", "貓草": "sprite-catgrass",
          "鐵塔": "sprite-tower", "0x": "sprite-zerox", "斑比": "sprite-bambi",
          "諾亞": "sprite-noah"}
# 立繪原檔高度差很多（0x 站得直、諾亞佝僂），縮放各自調過才會站得一樣高
SCALE = {G: .82, HOLE: .86, "貓草": .84, "鐵塔": .90, "0x": .80, "斑比": .78, "諾亞": .84}
AVATAR = {G: "avatar-glitch", HOLE: "avatar-blackhole", "貓草": "avatar-catgrass",
          "鐵塔": "avatar-tower", "0x": "avatar-zerox", "斑比": "avatar-bambi",
          "諾亞": "avatar-noah"}


def api(data=None, method="GET", path="", tries=4):
    body = json.dumps(data).encode() if data is not None else None
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(BASE + path, body, H, method=method), timeout=240))
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == tries - 1:
                raise
            print(f"  Larch 回 {e.code}，{2**i*5} 秒後重試")
            time.sleep(2 ** i * 5)


def ensure_characters():
    """讀角色清單。**建立與維護在 setup_characters.py**，這裡只負責拿 id。

    角色不是只有名字：平台的角色有 portraitUrl 跟 expressions，
    卡片上的 emotion 要對得到 expressions 裡的情緒名，編輯器才顯示得出來。
    """
    proj = api()
    have = {c["name"]: c["id"] for c in proj.get("characters", [])}
    missing = [n for n in list(SPRITE) + [NARRATOR] if n not in have]
    assert not missing, f"角色還沒建：{missing}　先跑 setup_characters.py"
    return have


class Chapter:
    def __init__(self, bid, name, desc, cids):
        self.bid, self.name, self.desc, self.cids = bid, name, desc, cids
        self.nodes, self.edges, self.prev, self._x, self._n = [], [], None, 0, 0
        self.cast = []          # 目前站在台上的人 [(名字, 位置)]

    # ── 內部 ────────────────────────────────────────────
    def _add(self, data):
        self._n += 1
        nid = f"{self.bid}-{self._n:03d}"
        self._x += 300
        self.nodes.append({"id": nid, "type": "story",
                           "position": {"x": self._x, "y": 0}, "data": data})
        if self.prev:
            self.edges.append({"id": f"e{self._n}", "source": self.prev,
                               "target": nid, "sourceHandle": "right", "animated": True})
        self.prev = nid
        return nid

    def _layers(self, speaking=None):
        out = []
        for name, pos in self.cast:
            key = SPRITE[name]
            out.append({"id": f"layer-{name}-{pos}", "url": A[key], "position": pos,
                        "x": 0, "y": 0, "scale": SCALE[name],
                        # 沒在講話的人壓暗，一眼看得出誰在說
                        "opacity": 1 if (speaking is None or name == speaking) else .55,
                        # 不要翻轉：0x 耳邊的標籤、貓草胸前的徽章都是不對稱的，
                        # 鏡射過去記號會跑到另一邊。
                        "flipX": False})
        return out

    # ── 對外 ────────────────────────────────────────────
    # 場景卡吃得下的畫面特效。這幾個是從官方範例專案裡確認出來的，
    # 其他值沒驗過，不要亂填。
    EFFECTS = ("rain", "snow", "embers", "flash", "stars3d")

    def scene(self, title, text, bg, start=False, effect=None,
              bgm=None, volume=.22):
        d = {"type": "scene", "title": title, "text": text, "background": A[bg]}
        if effect:
            assert effect in self.EFFECTS, f"沒驗過的特效：{effect}"
            d["visualEffect"] = effect
        if bgm:
            d.update(bgm=A[bgm], bgmVolume=volume, bgmLoop=True)
        if start:
            d["start"] = True
        return self._add(d)

    def stage(self, *who):
        """設定台上有誰。('格莉奇','left') 或直接給名字（自動排位）。"""
        slots = ["center"] if len(who) == 1 else ["left", "right"] if len(who) == 2 \
            else ["left", "center", "right"]
        self.cast = [w if isinstance(w, tuple) else (w, slots[i])
                     for i, w in enumerate(who)]
        return self.cast

    def narrate(self, *paras):
        """旁白。沒有名字，可是**台上的人要留著**。

        旁白時把立繪清掉的話，人會一直消失又出現，讀起來是閃的。
        要讓畫面沒有人，就明講 stage() 清空。
        """
        # **旁白是一個角色。** 平台一定要有 speaker，留白會變成沒有名牌的怪狀態，
        # 在編輯器裡看起來也像沒填完。做成沒有立繪的角色最乾淨。
        return self._add({"type": "dialogue", "title": paras[0][:14],
                          "text": "\n".join(paras), "speaker": NARRATOR,
                          "characterId": self.cids.get(NARRATOR),
                          "characterLayers": self._layers()})

    def say(self, who, *lines):
        """一個人講一段。"""
        return self._add({"type": "dialogue", "title": f"{who}：{lines[0][:12]}",
                          "text": "\n".join(lines), "speaker": who,
                          "characterId": self.cids.get(who),
                          "characterLayers": self._layers(who)})

    def talk(self, *pairs):
        """一來一往裝在同一張卡。pairs = (講者, 台詞) 一串。

        一句一張卡的話，兩個人鬥嘴會變成點十次滑鼠。dialogueLines 就是為這個存在的。
        """
        lines = [{"id": f"l{i}", "speaker": w, "text": t,
                  "emotion": ""} for i, (w, t) in enumerate(pairs)]
        return self._add({"type": "dialogue", "title": f"{pairs[0][0]}：{pairs[0][1][:10]}",
                          "text": pairs[0][1], "speaker": pairs[0][0],
                          "characterId": self.cids.get(pairs[0][0]),
                          "characterLayers": self._layers(),
                          "dialogueLines": lines})

    def chat(self, *msgs, who=None):
        """留言區／訊息。

        **播放器沒有大頭照這個東西**（bundle 裡 avatar 出現零次），
        可是立繪圖層有 scale 跟 x/y，所以把切好的圓形頭像縮小擺在左下角，
        效果就是聊天軟體的大頭貼。貓草人不在那個房間裡，用小頭像剛好把
        「他在另一個空間」講清楚，比讓他站進客廳合理。

        全部訊息都同一個人講的話（"貓草：…"），就掛他的頭像、掛他的名字。
        """
        if who is None:
            who = None
            names = {m.split("：", 1)[0] for m in msgs if "：" in m}
            if len(names) == 1 and next(iter(names)) in AVATAR:
                who = next(iter(names))
        body = [m.split("：", 1)[1] if who and m.startswith(who + "：") else m
                for m in msgs]
        layers = self._layers()
        if who:
            layers = layers + [{"id": f"avatar-{who}", "url": A[AVATAR[who]],
                                "position": "left", "x": -40, "y": 300,
                                "scale": .22, "opacity": 1, "flipX": False}]
        return self._add({"type": "dialogue", "title": f"{who or '留言區'}：{body[0][:12]}",
                          "text": "\n".join(body), "speaker": who or "留言區",
                          "characterId": self.cids.get(who) if who else None,
                          "characterLayers": layers})

    def end(self, text="（第一章結束）"):
        """章末。**要標出來**，不然檢查工具分不出「刻意的終點」跟「接漏了」。"""
        return self._add({"type": "dialogue", "title": "章末", "text": text,
                          "speaker": NARRATOR, "characterId": self.cids.get(NARRATOR),
                          "chapterEnd": True})

    def jump(self, board_id, node_id, text="（下一章）"):
        return self._add({"type": "boardJump", "title": "下一章", "text": text,
                          "jumpBoardId": board_id, "jumpNodeId": node_id})

    def push(self, summary):
        proj = api()
        proj["boards"] = [b for b in proj.get("boards", []) if b["id"] != self.bid]
        proj["boards"].append({"id": self.bid, "kind": "story", "mode": "story",
                               "name": self.name, "description": self.desc,
                               "nodes": self.nodes, "edges": self.edges})
        proj.setdefault("activeBoardId", self.bid)
        r = api({"project": proj, "summary": summary}, "PUT")
        b = [x for x in r["boards"] if x["id"] == self.bid][0]
        print(f"{self.name}：卡片 {len(b['nodes'])}　邊 {len(b['edges'])}")
        return r
