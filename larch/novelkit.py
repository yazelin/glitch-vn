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
    got = False
    lines = d.get("dialogueLines")
    if lines:
        for l in lines:
            u = VOICE_URLS.get(V.key(l.get("speaker"), l.get("text"),
                                     l.get("emotion") or None))
            if u:
                l["voiceUrl"] = u
                got = True
    else:
        # speakText：畫面上的字跟要唸的字不一樣時用它（系統訊息不唸，見 chat）
        u = VOICE_URLS.get(V.key(d.get("speaker"),
                                 d.get("speakText") or d.get("text"),
                                 d.get("emotion") or None))
        if u:
            d["voiceUrl"] = u
            got = True
    # **真正讓匯出版有聲音的開關在 project.languages，不在這裡。**
    # 匯出的播放器有一道閘：
    #     if (d.voiceMode && d.voiceMode!=='off' && d.voiceMode!=='realtime') playVoice(...)
    # 它讀卡片層的 d.voiceMode。可是**卡片上自己寫的 voiceMode 會被匯出程序丟掉**
    # （雲端存得下、匯出的 JSON 裡是 0 個），匯出時是從
    # `project.languages[].voiceMode` 複製到每張卡的。所以那個欄位要設在語言上，
    # 見 larch/setup_language.py。實測：語言加上去之後匯出的 JSON 立刻有 145 個。
    # 這裡照樣標一份當備援——線上播放器不看它，也不會壞事。
    if got:
        d["voiceMode"] = "shared"
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
        "難過": "face-glitch-sad", "笑": "face-glitch-laugh", "在算": "face-glitch-count",
        # 洩氣跟難過共用同一張臉。第七章那句「……喔。」用它，
        # 語氣另外在 voice.EMO 分開（配音要洩氣，不要吃驚）。
        "洩氣": "face-glitch-sad",
        # 深夜家常只改配音的唸法，臉沿用平靜那張。**一定要對到，**
        # 不然新情緒查不到差分會退回預設立繪，畫面跟著變。
        "深夜家常": "glitch-plain"},
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
           "在修東西": "face-noah-work", "撬鎖": "face-noah-pick", "和藹": "face-noah-warm"},
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


# 清台用的透明演員。名字留空，stage_audit 這類工具靠 id 認得出「這張其實是空台」。
GHOST = {"id": "actor-none", "url": A["sprite-none"], "name": "", "slot": "center",
         "scale": 0.01, "offsetX": 0, "offsetY": 0, "enter": "fade", "loop": "none"}


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
        self._cg = 0            # CG 解鎖卡自己一組流水號，不佔劇情卡的號碼
        self.pending = []       # 支線走完等著接回主線的那幾張
        self._bgm = None        # 現在在播哪一首，一樣就不重下（會從頭重播）
        self.cast = []          # 目前站在台上的人 [(名字, 位置)]

    # ── 內部 ────────────────────────────────────────────
    def _add(self, data, nid=None, eid=None):
        # nid 給了就不動流水號。**在中間插卡不可以把後面的卡片 id 全部往後推**——
        # 讀者的存檔記的是卡片 id，整章重編等於把所有進度打散（CG 解鎖卡就是這樣插的）。
        if nid is None:
            self._n += 1
            nid = f"{self.bid}-{self._n:03d}"
            eid = f"e{self._n}"
        # 蛇行排版。**不要排成一條橫線**：正篇本來是 y 全部 0、x 間距 300，
        # 而卡片本身寬 306，所以每一張都疊在前一張上面六個像素，連接線全部藏在
        # 卡片底下，整塊版子在編輯器裡看起來像一條沒有線的長條（2026-09-12）。
        #
        # 一列 WRAP 張，從左到右；下一列反過來從右到左。**折行那條線因此是短短
        # 一段垂直的**，不會像從左到右排那樣往回穿過整列卡片的背面。
        # CW 留 154px 的縫（460 − 306）讓相鄰的線看得見。
        CW, CH, WRAP = 460, 320, 12
        i = len(self.nodes)
        row, col = divmod(i, WRAP)
        if row % 2:
            col = WRAP - 1 - col
        self.nodes.append({"id": nid, "type": "story",
                           "position": {"x": col * CW, "y": row * CH}, "data": data})
        # 支線的每一條末端都接到下一張主線卡，這就是匯流點
        srcs = self.pending or ([self.prev] if self.prev else [])
        for k, s0 in enumerate(srcs):
            self.edges.append({"id": f"{eid}-{k}", "source": s0,
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
        # **台上沒人的時候要放一個看不見的演員。**
        # 播放器是「有新的才換，沒有就留著」：actors 給空陣列它不會清台，
        # 會把上一張的人留到下一張。實測過五種給空值的寫法（空陣列、
        # 連欄位都不給、加 props、character:null、clearStage:true）全部無效，
        # 換成「給一個透明的演員」四種寫法全部有效。
        # 所以清台的做法是換人，不是不給人。sprite-none 是一張 8×8 全透明圖。
        return actors or [GHOST]

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
        out += [{"id": e["id"], "url": e["url"], "position": e["slot"],
                 "x": e["offsetX"], "y": e["offsetY"], "scale": e["scale"],
                 "opacity": 1, "flipX": False} for e in extra]
        # 同上：空的話留著上一張的人，所以放透明的那一張。
        return out or [{"id": "layer-none", "url": A["sprite-none"],
                        "position": "center", "x": 0, "y": 0, "scale": 0.01,
                        "opacity": 1, "flipX": False}]

    # ── 對外 ────────────────────────────────────────────
    def scene(self, title, text, bg, start=False, effect=None,
              bgm=None, volume=.32, transition="fade", ms=340):
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
        # **空陣列不是清台。** 播放器是「有新的才換」，給空陣列它會把上一張的人留著。
        # 清台靠一個透明的演員（見 GHOST 與 _stage），這是實測出來的。
        return self._card(d)

    def cg(self, key, title):
        """把一張背景收進 CG 收藏。放在那張背景真正出現的那一場。

        **畫廊清單與解鎖動作是兩份資料。** `settings.cgGalleryItems` 的
        `locked: True` 決定它一開始是不是問號（見 larch/settings.py），
        這裡的卡決定什麼時候解開。只做一邊就會變成「畫廊有這張但永遠解不開」
        或「解鎖了但畫廊沒有」。

        **只有 `setVariable` 這個型別的卡吃 `cgOps`**，搬不到對話卡或場景卡上。
        播放器認的是 `url`（`cgGalleryItems[i].url` 與 `cgOps[i].url` 要是同一個字串），
        `id` 只是這個動作自己的名字。

        **`text` 不可以留空。** 播放器的自動前進條件是
        `!(mode === "card" || text.trim())`，空白的話卡片模式就是一張點不動的
        空白卡，標題還寫著「設定變量」，玩家直接卡在那裡。

        卡片 id 是 `chNN-cgN`，不佔劇情卡的流水號：在中間插卡不可以把後面
        整章的 id 往後推，讀者的存檔記的就是那些 id。
        """
        assert key in A, f"沒有這張圖：{key}"
        self._cg += 1
        return self._add({"type": "setVariable", "title": "CG 收藏",
                          "text": f"記住這個畫面。\n「{title}」收進了 CG 收藏。",
                          "cgOps": [{"id": f"cg-{key}", "url": A[key],
                                     "mode": "unlock"}]},
                         nid=f"{self.bid}-cg{self._cg}", eid=f"ecg{self._cg}")

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

    def narrate(self, *paras, face=None, props=(), emotion=None):
        """旁白。沒有名字，可是**台上的人要留著**。

        旁白時把立繪清掉的話，人會一直消失又出現，讀起來是閃的。
        要讓畫面沒有人，就明講 stage() 清空。
        """
        # **旁白是一個角色。** 平台一定要有 speaker，留白會變成沒有名牌的怪狀態，
        # 在編輯器裡看起來也像沒填完。做成沒有立繪的角色最乾淨。
        # emotion 在旁白身上不是表情，是**唸法**：唸紙上的字跟描述動作要不一樣。
        # 見 voice.EMO 的「唸紙上的字」。旁白沒有立繪，所以不影響畫面。
        d = {"type": "dialogue", "title": paras[0][:14],
             "text": "\n".join(paras), "speaker": NARRATOR,
             "characterId": self.cids.get(NARRATOR)}
        if emotion:
            d["emotion"] = emotion
        return self._card(d, face=face, extra=tuple(props))

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

        **全書只有 11% 是多行卡，這是刻意的，不要「順手優化」。** 掃過一遍：
        有 24 串連著出現、中間沒有旁白的單行角色卡（共 74 張，最長 7 張），
        技術上都可以合成一張。作者決定不合——一句一張的節奏是想要的。

        真的要合的話先改這裡：現在非 who 的那幾行 emotion 是空字串，而配音的
        檔名是 sha1(講者|文字|情緒)，所以合併會讓那 54 句的鍵變掉、音檔對不上，
        **而且不會報錯，只會安靜地沒有聲音**。

        **pairs 可以是二元組也可以是三元組**：`("諾亞", "有啊。")` 沿用整張卡的
        emotion（只掛在 who 身上，其餘行是空的），`("諾亞", "有啊。", "笑")`
        則是那一行自己的情緒。混用沒問題。

        **有了三元組才寫得出多句卡。** 配音的鍵是 sha1(講者|文字|情緒)，
        非主講者那幾行如果只能是空情緒，同一句話放進多句卡跟放進單句卡
        就會算出不同的鍵，音檔對不上，而且不會報錯，只會安靜地沒有聲音。
        """
        # 一張卡只有一個舞台，所以差分掛在 who（預設第一個講話的人）身上。
        face = who or pairs[0][0]
        norm = [(p + ("",))[:3] if len(p) == 2 else p for p in pairs]
        lines = [{"id": f"l{i}", "speaker": w, "text": t,
                  # 逐行情緒優先；沒填的才沿用整張卡的（而且只有 who 沿用，
                  # 這是既有行為，改掉會讓已經生好的 54 句鍵變掉）
                  "emotion": e or (emotion if (emotion and w == face) else "")}
                 for i, (w, t, e) in enumerate(norm)]
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
        # **系統訊息不配音。** 「貓草已離線。」是介面吐出來的狀態，不是有人在
        # 講話，唸出來很怪。它跟前面幾則留言黏在同一張卡上，所以整張一起被唸了。
        # 這裡把它從要唸的文字裡拿掉，畫面上照舊顯示。
        SPEAK_SKIP = ("已離線", "已上線", "已加入", "已退出")
        say_body = [m for m in body if not any(x in m for x in SPEAK_SKIP)]
        extra = ()
        if who:
            extra = ({"id": f"avatar-{who}", "url": A[AVATAR[who]], "name": who,
                      "slot": "left", "scale": 1.0, "offsetX": 0, "offsetY": 0,
                      "enter": "slideLeft", "loop": "none"},)
        d = {"type": "dialogue", "title": f"{who or '留言區'}：{body[0][:12]}",
             "text": "\n".join(body), "speaker": who or "留言區",
             "characterId": self.cids.get(who) if who else None,
             # 頭像用 slideLeft 滑進來，像訊息跳出來
             "transition": "fade", "transitionMs": 220}
        # 配音查表用的是要唸的文字，跟畫面上的不一樣時另外記，見 _voice。
        if say_body != body:
            d["speakText"] = "\n".join(say_body)
        return self._card(d, extra=extra)

    def branch(self, prompt, *arms, title="鏡頭", emotion=None):
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
                # 支線裡的旁白也要能給唸法（描述動作、唸紙上的字……）
                pd = {"type": "dialogue", "title": f"{label}：{para[:10]}",
                      "text": para, "speaker": NARRATOR,
                      "characterId": self.cids.get(NARRATOR)}
                if emotion:
                    pd["emotion"] = emotion
                nid = self._card(pd)
                first = first or nid
            self.edges.append({"id": f"ec{self._n}-{i}", "source": cid, "target": first,
                               "sourceHandle": f"choice-{i}", "targetHandle": "top",
                               "label": label, "animated": True})
            ends.append(self.prev)
        self.prev, self.pending = None, ends
        return cid

    def end(self, text="（第一章結束）", who=None, emotion=None):
        """章末。**要標出來**，不然檢查工具分不出「刻意的終點」跟「接漏了」。

        who 給名字的話換那個人講（謝幕那句是格莉奇說的，不是旁白）。
        """
        self.cast = []
        d = {"type": "dialogue", "title": "章末", "text": text,
             "speaker": who or NARRATOR,
             "characterId": self.cids.get(who or NARRATOR), "chapterEnd": True}
        if emotion:
            d["emotion"] = emotion
        return self._card(d)

    def credits(self, url, title="片尾謝幕", text=""):
        """片尾字卷。**用 miniGame 卡片，不是自己畫。**

        Larch 的 miniGame 卡片會拿 miniGameHtml 開一個 iframe，靠 postMessage
        溝通（larch:ready 開場、larch:set 寫變數、larch:complete 結束往下走）。
        這裡塞的只是一層薄殼：載入 Pages 上的殺青頁，再把那一頁的「播完了」
        轉成 larch:complete。內容留在 Pages，改字改圖不用動 Larch。
        """
        self.cast = []
        shell = (
            '<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
            # 薄殼背景一定要透明：Larch 2026-09-04 起 miniGame 層可以透明，這一層是唯一
            # 擋住放映廳場景的東西。credits.html?bg=none 那邊本來就是 transparent。
            '<style>html,body{margin:0;height:100%;background:transparent}'
            'iframe{width:100%;height:100%;border:0;display:block}</style>'
            f'<iframe src="{url}" allow="fullscreen"></iframe><script>'
            "parent.postMessage({type:'larch:ready'},'*');"
            "addEventListener('message',function(e){var d=e.data;"
            "if(!d||d.from!=='glitch-credits')return;"
            "if(d.done)parent.postMessage({type:'larch:complete',result:'complete',"
            "eventName:'Glitch.CreditsDone',payload:{}},'*');});"
            '</script></html>')
        return self._add({"type": "miniGame", "title": title, "text": text,
                          "miniGameHtml": shell, "miniGamePresentation": "fullscreen",
                          "miniGameSkippable": True,
                          "miniGameReadVars": [], "miniGameWriteVars": [],
                          "miniGameNote": f"薄殼而已，內容在 {url}"})

    def jump(self, board_id, node_id, text="（下一章）"):
        # **跳下一章之前把台上清空。** 不清的話下一章開頭會出現上一章最後站著的人。
        self.cast = []
        return self._card({"type": "boardJump", "title": "下一章", "text": text,
                           "jumpBoardId": board_id, "jumpNodeId": node_id})

    def push(self, summary):
        # **一次只推自己這一塊版子。** 以前這裡走 `PUT /projects`，要把整包
        # 一點四 MB（八塊版子）送上去，2026-09-11 開始伺服器吃不下，連著回
        # 502（重試第三次才過）。`PUT /boards/:id` 只送這一章，幾十 KB，
        # 而且碰不到 settings／characters／media，`PUT /projects` 那條
        # 「只留你送的」的坑也一起避開。
        # 板子順序與 activeBoardId 不用在這裡管：兩個都已經在專案上了，
        # 這支端點是就地更新，不會把版子搬到陣列最後。
        path = f"/boards/{self.bid}"
        old = {n["id"]: n for n in ((api(path=path).get("board") or {})
                                    .get("nodes") or [])}
        # **重建一章會把線上的翻譯整批刪掉，而且不會報錯。** 平台的翻譯功能把譯文寫在
        # 每張卡的 `data.localizations` 裡，建置腳本產不出那個欄位，所以照原樣推上去
        # 就是「我這一份沒有」＝刪掉。下一個專案要是有翻譯要保，就在這裡照卡片 id
        # 把線上那一份接回來（`n["data"]["localizations"] = o["data"]["localizations"]`），
        # 2026-09-11 第一章的八十一張日文就是這樣救回來的。
        #
        # **這個專案刻意不留翻譯。** 那批 ja-JP 是平台上跑過一次翻譯留下的，只翻了第一章，
        # 作者決定拿掉，所以這裡不接回來——推一次就清掉了。專案層的語言清單是另一份資料，
        # 在 larch/setup_language.py 清；只清一邊會留下殘骸。
        #
        # `measured` 是編輯器量出來的尺寸，平台寫的，那個要留著。
        drop = 0
        for n in self.nodes:
            o = old.get(n["id"])
            if not o:
                continue
            if (o.get("data") or {}).get("localizations"):
                drop += 1
            if o.get("measured"):
                n["measured"] = o["measured"]
        r = api({"name": self.name, "kind": "story", "mode": "story",
                 "description": self.desc, "nodes": self.nodes,
                 "edges": self.edges, "summary": summary}, "PUT", path)
        # **PUT 的回應沒有 nodes／edges**（只回 `{projectId, board:{id,name,…}}`），
        # 所以要驗有沒有推上去只能再讀一次。
        b = api(path=path).get("board") or {}
        back = sum(1 for n in b["nodes"] if (n["data"].get("localizations") or []))
        print(f"{self.name}：卡片 {len(b['nodes'])}／{len(self.nodes)}　"
              f"邊 {len(b['edges'])}／{len(self.edges)}　"
              f"翻譯 清掉 {drop} 張，剩 {back} 張")
        assert len(b["nodes"]) == len(self.nodes), f"{self.bid}：卡片回讀對不上"
        assert len(b["edges"]) == len(self.edges), f"{self.bid}：邊回讀對不上"
        return r
