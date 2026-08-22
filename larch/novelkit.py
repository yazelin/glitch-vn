"""小說版的白板建構器。

跟舊版那支 daykit 完全不同：這裡沒有變數、沒有條件邊、沒有記憶格。
小說是線性的，所以骨架只有「場景 → 一連串卡片 → 下一章」。

用得到的兩個平台功能（2026-08-22 從前端 bundle 挖出來的）：
  characterLayers  一張卡可以站好幾個人，各自有位置、縮放、翻轉
  dialogueLines    一張卡可以裝一整段來回對話，不必一句一張卡

這兩個加起來，散文式的對話段落才排得出來。
"""
import json, pathlib, time, urllib.error, urllib.request

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import PROJ, BASE, H, ROOT, STORE, api  # noqa: E402

A = json.loads((ROOT / "larch/assets.json").read_text())

G, HOLE, NARRATOR = "格莉奇", "黑洞先生", "旁白"
SPRITE = {G: "sprite-glitch", HOLE: "sprite-blackhole", "貓草": "sprite-catgrass",
          "鐵塔": "sprite-tower", "0x": "sprite-zerox", "斑比": "sprite-bambi",
          "諾亞": "sprite-noah"}
# 立繪原檔高度差很多（0x 站得直、諾亞佝僂），縮放各自調過才會站得一樣高
# 市集專案的 scale 實測都在 0.90～1.04，我原本 0.78～0.90 整組偏小。
# 每個人的立繪原檔高度不一樣，所以各自微調，讓他們站起來差不多高。
SCALE = {G: .96, HOLE: 1.0, "貓草": .98, "鐵塔": 1.04, "0x": .94,
         "斑比": .92, "諾亞": .98}
# 演出詞彙表。全部從市集上別人發佈的專案裡挖出來的（GET /api/marketplace/{id}?play=1，
# 不用登入），不是猜的。
ENTER = ("fade", "zoom", "spring", "bounce", "blur", "glide", "riseUp", "swoopIn",
         "walkInLeft", "arcLeft", "arcRight", "slideLeft", "slideRight", "slideDown")
LOOP = ("breathe", "nod", "sway", "shiver", "hop", "pulse", "none")
TRANSITION = ("fade", "wipeLeft", "wipeRight", "blurCut", "flash", "irisIn",
              "fadeBlack", "none")
EFFECT = ("rain", "snow", "embers", "flash", "stars3d", "petals", "vignette",
          "speedLines", "fog", "shake", "none")
SLOT = ("farLeft", "left", "center", "right", "farRight")

# 聊天頭像：跟立繪同尺寸的透明畫布，圓形放在左下角。
# **定位做在圖裡，不要用 offsetX/offsetY**——那兩個的單位是小數不是像素。
AVATAR = {G: "chat-glitch", HOLE: "chat-blackhole", "貓草": "chat-catgrass",
          "鐵塔": "chat-tower", "0x": "chat-zerox", "斑比": "chat-bambi",
          "諾亞": "chat-noah"}

# 表情差分。**卡片填 emotion 還不夠**——市集上的作品是把舞台那個角色的 url
# 一起換成差分圖，兩個都寫播放器才換得了臉。只填 emotion 的話畫面不會動。
EXPR = {
    G: {"平靜": "glitch-plain", "開心": "glitch-happy", "發呆": "glitch-thinking",
        "驚訝": "glitch-idle", "當機": "glitch-error", "想睡": "glitch-sleep",
        "難過": "face-glitch-sad"},
    HOLE: {"平靜": "blackhole-idle", "飽": "blackhole-full", "餓": "blackhole-hungry"},
    "鐵塔": {"公事": "face-tower-brief", "疲憊": "face-tower-tired",
           "難得的溫柔": "face-tower-warm"},
    "0x": {"意外": "face-zerox-startled", "壓著": "face-zerox-held",
           "要走": "face-zerox-leaving"},
    "斑比": {"不安": "face-bambi-anxious", "被說中": "face-bambi-moved",
           "專注": "face-bambi-focus"},
    "諾亞": {"想事情": "face-noah-puzzle", "笑": "face-noah-smile"},
    "貓草": {"發酸": "face-catgrass-sour", "彆扭": "face-catgrass-sulky"},
}


def art(name, emotion=None):
    """這個角色現在該用哪一張圖。沒有對應的差分就回基礎立繪。"""
    key = EXPR.get(name, {}).get(emotion or "")
    return A[key] if key and key in A else A[SPRITE[name]]



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
        self.pending = []       # 支線走完等著接回主線的那幾張
        self.cast = []          # 目前站在台上的人 [(名字, 位置)]

    # ── 內部 ────────────────────────────────────────────
    def _add(self, data):
        self._n += 1
        nid = f"{self.bid}-{self._n:03d}"
        self._x += 300
        self.nodes.append({"id": nid, "type": "story",
                           "position": {"x": self._x, "y": 0}, "data": data})
        # 支線的每一條末端都接到下一張主線卡，這就是匯流點
        srcs = self.pending or ([self.prev] if self.prev else [])
        for k, s0 in enumerate(srcs):
            self.edges.append({"id": f"e{self._n}-{k}", "source": s0,
                               "target": nid, "sourceHandle": "right", "animated": True})
        self.pending = []
        self.prev = nid
        return nid

    def _stage(self, speaking=None, extra=(), emotion=None):
        """舞台。**用 stage.actors，不要只用 characterLayers。**

        actors 多了兩個 characterLayers 沒有的東西：`enter` 進場動畫、
        `loop` 待機動畫。沒有 loop 的立繪就是一張不會動的貼圖。
        `breathe` 是呼吸，市集上的作品幾乎每個角色都掛這個。
        """
        actors = []
        for name, pos in self.cast:
            actors.append({"id": f"actor-{name}-{pos}",
                           "url": art(name, emotion if name == speaking else None),
                           "name": name, "slot": pos, "scale": SCALE[name],
                           "offsetX": 0, "offsetY": 0,
                           "enter": "fade", "loop": "breathe",
                           "loopSpeed": 1, "loopStrength": 1})
        actors += list(extra)
        return actors

    def _layers(self, speaking=None, extra=(), emotion=None):
        """舊的 characterLayers。編輯器某些地方還在讀它，所以兩個都寫。"""
        out = []
        for name, pos in self.cast:
            out.append({"id": f"layer-{name}-{pos}",
                        "url": art(name, emotion if name == speaking else None),
                        "position": pos, "x": 0, "y": 0, "scale": SCALE[name],
                        "opacity": 1 if (speaking is None or name == speaking) else .55,
                        # 不要翻轉：0x 耳邊的標籤、貓草胸前的徽章都是不對稱的。
                        "flipX": False})
        return out + [{"id": e["id"], "url": e["url"], "position": e["slot"],
                       "x": e["offsetX"], "y": e["offsetY"], "scale": e["scale"],
                       "opacity": 1, "flipX": False} for e in extra]

    # ── 對外 ────────────────────────────────────────────
    def scene(self, title, text, bg, start=False, effect=None,
              bgm=None, volume=.22, transition="fade", ms=340):
        d = {"type": "scene", "title": title, "text": text, "background": A[bg],
             "transition": transition, "transitionMs": ms}
        assert transition in TRANSITION, f"沒有這個轉場：{transition}"
        if effect:
            assert effect in EFFECT, f"沒有這個特效：{effect}"
            d["visualEffect"] = effect
        if bgm:
            d.update(bgm=A[bgm], bgmVolume=volume, bgmLoop=True)
        if start:
            d["start"] = True
        return self._add(d)

    def stage(self, *who):
        """設定台上有誰。('格莉奇','left') 或直接給名字（自動排位）。"""
        # 站位有五個：farLeft left center right farRight
        slots = (["center"], ["left", "right"], ["left", "center", "right"],
                 ["farLeft", "left", "right", "farRight"],
                 ["farLeft", "left", "center", "right", "farRight"])[len(who) - 1]
        self.cast = [w if isinstance(w, tuple) else (w, slots[i])
                     for i, w in enumerate(who)]
        return self.cast

    def _card(self, d, speaking=None, extra=(), emotion=None):
        d["characterLayers"] = self._layers(speaking, extra, emotion)
        d["stage"] = {"actors": self._stage(speaking, extra, emotion)}
        return self._add(d)

    def narrate(self, *paras):
        """旁白。沒有名字，可是**台上的人要留著**。

        旁白時把立繪清掉的話，人會一直消失又出現，讀起來是閃的。
        要讓畫面沒有人，就明講 stage() 清空。
        """
        # **旁白是一個角色。** 平台一定要有 speaker，留白會變成沒有名牌的怪狀態，
        # 在編輯器裡看起來也像沒填完。做成沒有立繪的角色最乾淨。
        return self._card({"type": "dialogue", "title": paras[0][:14],
                           "text": "\n".join(paras), "speaker": NARRATOR,
                           "characterId": self.cids.get(NARRATOR)})

    def say(self, who, *lines, emotion="平靜"):
        """一個人講一段。emotion 要對得到角色的 expressions，播放器才換得了臉。"""
        return self._card({"type": "dialogue", "title": f"{who}：{lines[0][:12]}",
                           "text": "\n".join(lines), "speaker": who,
                           "emotion": emotion,
                           "characterId": self.cids.get(who)},
                          speaking=who, emotion=emotion)

    def talk(self, *pairs, emotion=None, who=None):
        """一來一往裝在同一張卡。pairs = (講者, 台詞) 一串。

        一句一張卡的話，兩個人鬥嘴會變成點十次滑鼠。dialogueLines 就是為這個存在的。
        """
        # 一張卡只有一個舞台，所以差分掛在 who（預設第一個講話的人）身上。
        face = who or pairs[0][0]
        lines = [{"id": f"l{i}", "speaker": w, "text": t,
                  "emotion": emotion if (emotion and w == face) else ""}
                 for i, (w, t) in enumerate(pairs)]
        d = {"type": "dialogue", "title": f"{pairs[0][0]}：{pairs[0][1][:10]}",
             "text": pairs[0][1], "speaker": pairs[0][0],
             "characterId": self.cids.get(pairs[0][0]),
             "dialogueLines": lines}
        if emotion:
            d["emotion"] = emotion
        return self._card(d, speaking=face, emotion=emotion)

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
        extra = ()
        if who:
            extra = ({"id": f"avatar-{who}", "url": A[AVATAR[who]], "name": who,
                      "slot": "left", "scale": 1.0, "offsetX": 0, "offsetY": 0,
                      "enter": "slideLeft", "loop": "none"},)
        return self._card({"type": "dialogue", "title": f"{who or '留言區'}：{body[0][:12]}",
                           "text": "\n".join(body), "speaker": who or "留言區",
                           "characterId": self.cids.get(who) if who else None,
                           # 頭像用 slideLeft 滑進來，像訊息跳出來
                           "transition": "fade", "transitionMs": 220},
                          extra=extra)

    def branch(self, prompt, *arms, title="鏡頭"):
        """支線。**讀者不在這個世界裡**，他只是決定鏡頭要停在哪一樣東西上。

        所以選項寫的是房間裡的東西，不是「你要做什麼」；旁白也不對讀者說話。
        每一條走完都接回主線的下一張卡，主線一個字都不會變。

            c.branch("客廳裡還有三樣東西。",
                     ("門邊那疊短靴", ("……", "……")),
                     ("桌上冷掉的披薩", ("……",)))
        """
        assert 2 <= len(arms) <= 4, "選項給兩到四個"
        # **選項卡也要帶立繪。** 用 _add 的話台上的人會在這一張消失、選完又出現，
        # 跟旁白清掉立繪是同一個坑。
        cid = self._card({"type": "choice", "title": title, "text": prompt,
                          "choices": [a[0] for a in arms],
                          "choiceMode": "branch", "choicePlacement": "center"})
        ends = []
        for i, (label, paras) in enumerate(arms):
            self.prev = None            # 這一條的第一張由 choice 的 handle 接
            first = None
            for para in paras:
                nid = self._card({"type": "dialogue", "title": f"{label}：{para[:10]}",
                                  "text": para, "speaker": NARRATOR,
                                  "characterId": self.cids.get(NARRATOR)})
                first = first or nid
            self.edges.append({"id": f"ec{self._n}-{i}", "source": cid, "target": first,
                               "sourceHandle": f"choice-{i}", "targetHandle": "top",
                               "label": label, "animated": True})
            ends.append(self.prev)
        self.prev, self.pending = None, ends
        return cid

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
