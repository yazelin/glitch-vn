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

# 配音網址表：代號 → 網址（tools/upload_voice.py 產生）。還沒生配音就是空的，
# 建置照樣跑得動——沒有網址的句子單純沒有聲音，不會壞。
_VU = ROOT / "art/voice/urls.json"
VOICE_URLS = json.loads(_VU.read_text(encoding="utf-8")) if _VU.exists() else {}


def _voice(d):
    """把 voiceUrl 掛上卡片。**多人卡片一定要掛在行上**，卡片層只吃得下一個聲音。

    查表的鍵一定要跟 tools/gen_voice.py 收句子時算的一模一樣：
    單人卡用卡片的 speaker/text/emotion，多人卡用每一行自己的三個欄位。
    差一個欄位就全部對不上，而且不會報錯，只會安靜地沒有聲音。
    """
    if not VOICE_URLS:
        return d
    import voice as V
    lines = d.get("dialogueLines")
    if lines:
        for l in lines:
            u = VOICE_URLS.get(V.key(l.get("speaker"), l.get("text"),
                                     l.get("emotion") or None))
            if u:
                l["voiceUrl"] = u
    else:
        u = VOICE_URLS.get(V.key(d.get("speaker"), d.get("text"),
                                 d.get("emotion") or None))
        if u:
            d["voiceUrl"] = u
    return d

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
        "難過": "face-glitch-sad", "笑": "face-glitch-laugh", "在算": "face-glitch-count"},
    # **不要用 blackhole-full／hungry。** 那是舊版七天記憶遊戲的素材，
    # 「吃飽」是當時的機制，所以美術畫的是**身形**變化（肩膀變寬、軀幹變厚），
    # 不是表情差分。沿用舊素材要看圖，不能只看檔名。
    HOLE: {"平靜": "blackhole-idle", "轉頭": "face-blackhole-turn",
           "看著她": "face-blackhole-look", "拉開外套": "face-blackhole-coat",
           "不回答": "face-blackhole-still", "點頭": "face-blackhole-nod"},
    "鐵塔": {"公事": "face-tower-brief", "疲憊": "face-tower-tired",
           "難得的溫柔": "face-tower-warm", "掛掉": "face-tower-leave"},
    "0x": {"意外": "face-zerox-startled", "壓著": "face-zerox-held",
           "要走": "face-zerox-leaving", "唱歌": "face-zerox-sing",
           "完全的平": "face-zerox-flat"},
    "斑比": {"不安": "face-bambi-anxious", "被說中": "face-bambi-moved",
           "專注": "face-bambi-focus", "累": "face-bambi-tired"},
    "諾亞": {"想事情": "face-noah-puzzle", "笑": "face-noah-smile",
           "在修東西": "face-noah-work", "和藹": "face-noah-warm"},
    "貓草": {"發酸": "face-catgrass-sour", "彆扭": "face-catgrass-sulky"},
}


# 背景配哪一首 BGM。寫成表而不是散在各章，是因為同一個場景在七章裡出現很多次，
# 靠人記會漂。要換的地方（第七章的客廳與茶几是全書的轉折）在 build 腳本裡明寫 bgm=。
BGM_FOR = {
    "title-cover": "bgm-title",
    "bg-studio-2am": "bgm-studio", "bg-studio-day": "bgm-studio",
    "bg-collab-studio": "bgm-collab",
    "bg-living-night": "bgm-living", "bg-table-lamp": "bgm-notebook",
    "bg-booth": "bgm-work", "bg-greenroom": "bgm-cold", "bg-corridor": "bgm-cold",
    "bg-office-14f": "bgm-cold", "bg-bambi-studio": "bgm-studio",
    "bg-apartment-hall": "bgm-living", "bg-noah-shop": "bgm-shop",
    "bg-stairs": "bgm-shop", "bg-street-day": "bgm-street",
    "bg-kitchen-morning": "bgm-morning",
}


def prop(key, slot="center", scale=1.0, enter="fade"):
    """把一樣東西擺進畫面。角色在講某個東西的時候，那個東西應該看得到。

    平台沒有「道具」這種卡，可是 stage.actors 吃任何一張圖——
    留言區的大頭貼就是這樣做的。這裡同一招用在本子、收據上。

    **scale 用 1.0，位置烤在圖裡。** 立繪貼齊畫面底部，所以小圖會沉到腳邊
    再被對話框蓋掉（本子掉在地上、收據只露一個角，兩個都發生過）。
    `offsetY` 也救不了，那個欄位是小數不是像素。見 tools/make_prop_card.py。
    """
    return {"id": f"prop-{key}-{slot}", "url": A[key], "name": "",
            "slot": slot, "scale": scale, "offsetX": 0, "offsetY": 0,
            "enter": enter, "loop": "none"}


def _emo(name, speaking, emotion, face):
    """這個角色這一張要用哪個表情。

    **旁白卡也要能換表情。** 「他轉過頭來」「他看了很久」「0x 唱得很好」
    這些最好的節拍全部寫在旁白裡，只換「正在講話的人」的話一張都用不到。
    所以 face=(角色, 表情) 是獨立於 speaking 的一條路，而且不會把別人調暗。
    """
    if face and name == face[0]:
        return face[1]
    return emotion if name == speaking else None


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
        self._bgm = None        # 現在在播哪一首，一樣就不重下（會從頭重播）
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

    def _stage(self, speaking=None, extra=(), emotion=None, face=None):
        """舞台。**用 stage.actors，不要只用 characterLayers。**

        actors 多了兩個 characterLayers 沒有的東西：`enter` 進場動畫、
        `loop` 待機動畫。沒有 loop 的立繪就是一張不會動的貼圖。
        `breathe` 是呼吸，市集上的作品幾乎每個角色都掛這個。
        """
        actors = []
        for name, pos in self.cast:
            actors.append({"id": f"actor-{name}-{pos}",
                           "url": art(name, _emo(name, speaking, emotion, face)),
                           "name": name, "slot": pos, "scale": SCALE[name],
                           "offsetX": 0, "offsetY": 0,
                           "enter": "fade", "loop": "breathe",
                           "loopSpeed": 1, "loopStrength": 1})
        actors += list(extra)
        return actors

    def _layers(self, speaking=None, extra=(), emotion=None, face=None):
        """舊的 characterLayers。編輯器某些地方還在讀它，所以兩個都寫。"""
        out = []
        for name, pos in self.cast:
            out.append({"id": f"layer-{name}-{pos}",
                        "url": art(name, _emo(name, speaking, emotion, face)),
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
        # 沒指定就照背景查表。**同一首不要重下**，重下等於從頭重播，
        # 連著三場都是茶几的話音樂會一直跳回開頭。
        bgm = bgm or BGM_FOR.get(bg)
        if bgm and bgm in A and bgm != self._bgm:
            d.update(bgm=A[bgm], bgmVolume=volume, bgmLoop=True)
            self._bgm = bgm
        if start:
            d["start"] = True
        # **場景卡也要寫 stage。** 沒寫的話播放器保留上一張的人；章與章之間就會
        # 把上一章最後站著的人帶進來（第二章結尾黑洞先生還在，第三章開頭他就出現了）。
        # 市集的場景卡要嘛沒有 stage、要嘛帶一個演員數為零的 stage——後者才是清台。
        return self._card(d)

    def stage(self, *who):
        """設定台上有誰。('格莉奇','left') 或直接給名字（自動排位）。"""
        # 站位有五個：farLeft left center right farRight
        slots = (["center"], ["left", "right"], ["left", "center", "right"],
                 ["farLeft", "left", "right", "farRight"],
                 ["farLeft", "left", "center", "right", "farRight"])[len(who) - 1]
        self.cast = [w if isinstance(w, tuple) else (w, slots[i])
                     for i, w in enumerate(who)]
        return self.cast

    def _card(self, d, speaking=None, extra=(), emotion=None, face=None):
        if (d.get("type") or "dialogue") == "dialogue":
            _voice(d)
        d["characterLayers"] = self._layers(speaking, extra, emotion, face)
        d["stage"] = {"actors": self._stage(speaking, extra, emotion, face)}
        return self._add(d)

    def narrate(self, *paras, face=None, props=()):
        """旁白。沒有名字，可是**台上的人要留著**。

        旁白時把立繪清掉的話，人會一直消失又出現，讀起來是閃的。
        要讓畫面沒有人，就明講 stage() 清空。
        """
        # **旁白是一個角色。** 平台一定要有 speaker，留白會變成沒有名牌的怪狀態，
        # 在編輯器裡看起來也像沒填完。做成沒有立繪的角色最乾淨。
        return self._card({"type": "dialogue", "title": paras[0][:14],
                           "text": "\n".join(paras), "speaker": NARRATOR,
                           "characterId": self.cids.get(NARRATOR)},
                          face=face, extra=tuple(props))

    def _avatar(self, who):
        """只以訊號存在的人用大頭貼：貓草在留言區、鐵塔在耳機裡，兩個都不在這個房間。
        （視訊會議看得到本人，那裡用全身立繪——看得到跟聽得到不一樣。）"""
        return ({"id": f"avatar-{who}", "url": A[AVATAR[who]], "name": who,
                 "slot": "left", "scale": 1.0, "offsetX": 0, "offsetY": 0,
                 "enter": "slideLeft", "loop": "none"},)

    def say(self, who, *lines, emotion="平靜", remote=False):
        """一個人講一段。emotion 要對得到角色的 expressions，播放器才換得了臉。

        remote=True：他不在這個房間，只有聲音（耳機、電話）。掛大頭貼。
        """
        if remote:
            return self._card({"type": "dialogue", "title": f"{who}：{lines[0][:12]}",
                               "text": "\n".join(lines), "speaker": who,
                               "characterId": self.cids.get(who)},
                              extra=self._avatar(who))
        return self._card({"type": "dialogue", "title": f"{who}：{lines[0][:12]}",
                           "text": "\n".join(lines), "speaker": who,
                           "emotion": emotion,
                           "characterId": self.cids.get(who)},
                          speaking=who, emotion=emotion)

    def talk(self, *pairs, emotion=None, who=None, remote=None):
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
        # remote=名字：那個人不在房間裡，只有聲音。掛他的大頭貼。
        extra = self._avatar(remote) if remote else ()
        return self._card(d, speaking=face, emotion=emotion, extra=extra)

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
        self.cast = []
        return self._card({"type": "dialogue", "title": "章末", "text": text,
                           "speaker": NARRATOR, "characterId": self.cids.get(NARRATOR),
                           "chapterEnd": True})

    def jump(self, board_id, node_id, text="（下一章）"):
        # **跳下一章之前把台上清空。** 不清的話下一章開頭會出現上一章最後站著的人。
        self.cast = []
        return self._card({"type": "boardJump", "title": "下一章", "text": text,
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
