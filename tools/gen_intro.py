#!/usr/bin/env python3
"""角色頁的自我介紹配音：一個角色一段，讀者按下去就聽得到那個人的聲音。

用意是**在讀之前先認識聲音**。所以這七段一律不碰第七章的答案，
也不講守則本後來怎麼了——只講這個人自己是誰。

聲線跟全書共用同一組參考音（larch/voice.py 的 VOICE），**不可以另外選角**：
角色頁聽到的聲音跟書裡不是同一個人的話，這個功能就是反效果。

諾亞與鐵塔走的是外部配音（Larch 的 MiniMax），他們的參考音是從**自己的成品**
切下來的，逐字稿一個字都沒改（見 voice-ref/noah.wav、tower.wav 與下面的 REF）。
不用 scratchpad 那批試驗檔：那個目錄會隨 session 消失，聲線就重建不出來。

    python3 tools/gen_intro.py           # 只重生「唸出來的字或表演指示變了」的
    python3 tools/gen_intro.py --all     # 全部重生（手氣不好想重擲的時候）
    python3 tools/gen_intro.py --only 格莉奇 黑洞先生
    python3 tools/gen_intro.py --dry     # 只寫 jobs.json，不跑模型

**voice_batch 看到 wav 已存在就跳過**，所以改了文字直接跑會得到「要生 0」，
而它不會報錯——檔案還是舊的，驗收也就驗到舊的那一份。這裡自己記帳（intro-take.json）
比對送進模型的字與指示，變了就把舊 wav 刪掉再跑。
"""
import hashlib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
import voice as V  # noqa: E402

OUT = ROOT / "art/voice/intro"
DOCS = ROOT / "docs/voice"

# 講者 → (角色頁上的 slug, 自介, 表演指示要用的 emotion)
# emotion 填 None 就用 voice.BASE 那個角色的底色。
INTRO = {
    # emotion 用「開心」：底色那版聽起來悶，可是她是**開台第一天就答應要記住
    # 每一個人**的那種人，自介不該像在道歉。
    # **「口頭禪」拿掉了。** 那個 chán 音模型唸不出來，六版全錯（腦／糖／蹭／襯／槍／掐），
    # 同音替身也救不了。改成把那件事講出來，本來就比貼一個標籤好。
    "格莉奇": ("glitch", "開心",
             "大家好，我是格莉奇。虛擬主播，頻道第二年。"
             # **4KB 是她的哏，不是規格**（design/novel.md 之十一、persona 的 taskNote）。
             # 真要當字面值她連一句話都跑不完。原本寫「也是實話」、改寫時又寫成
             # 「而且它是真的」，兩次都把哏講成規格。正典的寫法是
             # 「手邊放不下」「滿了就把最舊的一整件擠掉」，不要拿數字算。
             "我的記憶體只有四KB。這句話我每天都要講一次。"
             "真的沒有那麼少啦。可是我手邊確實放不下，滿了就把最舊的一整件擠掉。"
             "所以我每天晚上都會抄一次守則本。"
             "第一頁有七行，上面有六個名字。"
             "我知道有第七個。我只是叫不出來。"),
    # **他不解釋自己。** 正典寫得很清楚：話極少，溫和，從不解釋自己，不會追問。
    # 第一版寫他睡在沙發那一邊，看起來像寄住；第二版補「我有正職，早上出門」
    # 想澄清，可是**替自己辯解正好是他不會做的事**。
    # 他是什麼、吃什麼，卡片上那段介紹已經寫了，自介不必再解釋一次，
    # 這裡只留他的聲音。溫柔要從「她不必抱歉」看出來，不是講出來。
    "黑洞先生": ("blackhole", "溫和",
              "我是她的室友。"
              "她忘掉的事我收著。收得很好，不會弄丟。"
              "她不必為那個跟我抱歉。她也沒有抱歉過。這樣很好。"
              "其他的我沒有要講。"),
    "貓草": ("catgrass", None,
           "我？貓草。等級八十，全勤。"
           "開台第一天我就在了，那天總共七個人，你自己去算。"
           "我不是什麼老粉……我只是剛好每天都有空。"
           "你不要跟她講我這樣說。"),
    "鐵塔": ("tower", None,
           "她的經紀人。"
           "訂閱數我背得出來，周邊庫存我也背得出來，她昨天講了幾次同一句話我也數過。"
           "她的毛病現在是賣點。這句話我只講一次。"
           "還有問題嗎。"),
    "0x": ("zerox", None,
           "0x。企業勢，跟她同期出道，同一天。"
           "零失誤。寫在規格書上的那一種。"
           "她的數字我不看。"
           "沒了。"),
    "斑比": ("bambi", None,
           "啊、我是斑比。接案的，畫她的立繪。"
           "現在是第七版。不對，第七版是上禮拜……"
           "我知道我改太多次了，我知道。"
           "可是她的瀏海分線在右邊數過來第三根，那個位置錯一格整張就不對。"
           "……你覺得現在這版可以嗎。"),
    # **他不報自己的名字。** 「諾亞」在他那支克隆聲線裡一直糊成「作呀」，
    # 三種寫法、五次以上重擲都一樣，是系統性的。卡片上本來就寫著他的名字，
    # 而且不自我介紹本來就比較像他講話的樣子。
    "諾亞": ("noah", None,
           "修收音機的。"
           "店在頂樓，招牌是從樓下騎樓搬上來的，字看不清楚了沒關係，要找的人找得到。"
           "樓下那個小姑娘常常把自己鎖在門外。"
           "她一個禮拜來問我三次同一件事。我每次都回答。"
           "因為她每次都是第一次問啊。"),
}

# ── 別人怎麼說 ──────────────────────────────────────────
# 一個角色對另一個角色的看法。**只寫書裡真的有交集的組合**，
# 不要因為好玩就讓兩個沒碰過面的人互相評論：
#   諾亞 ↔ 黑洞先生  第五章之五，晚上七點多在樓梯口交會，點過頭，沒講過話
#   鐵塔 ↔ 斑比      第二章，《守則本》周邊是鐵塔請斑比重畫的
#   鐵塔 ↔ 0x        第三章，聯動企劃是兩邊的經紀人一起談的
#   貓草 → 0x        他在聊天室裡，看得到同業
#   格莉奇 → 貓草    全勤兩年
#
# **不可以寫出新的劇情。** 這裡只放觀察，不放事件：寫「我看他每天七點回來」
# 可以，寫「他跟我說過他為什麼留下來」不行，那等於在正文之外偷加一場戲。
# 也一律避開第七章的答案。
VIEWS = [
    ("諾亞", "blackhole",
     "樓下那位先生。每天七點過後回來，西裝、帽子，短靴擦得很亮。"
     "我們在樓梯口點過頭很多次了，話沒講過幾句。"
     "有些人不用講話，你看他站在那裡就知道他不會走。"),
    # **不要把他寫成缺了什麼。** 他不是可憐的那一個：吃進去的永遠在他裡面，
    # 他跟她是互相剛好。原本寫「我這裡沒有人來拿，也拿不走」，
    # 那是從缺口的角度寫他，跟正典的底色相反。
    ("黑洞先生", "noah",
     "頂樓那位。他收著她掉的東西，等她自己上去拿。"
     "她每次都當第一次問，他每次都當第一次答。"
     "我看過很多人。做得到這個的不多。"),
    ("鐵塔", "bambi",
     "斑比。她很慢，一張圖可以改到第四十版。"
     "可是她畫的東西我一張都沒有退過。慢得有道理的我不催。"),
    ("斑比", "tower",
     "那個經紀人……他每次都只回「可以」或「再看看」，一個字都不多。"
     "我以為他覺得我很煩。"
     "……後來我才發現，他從來沒有退過我的稿。"),
    ("鐵塔", "zerox",
     "0x。那邊團隊三十幾個人，法務兩個。"
     "她的數字乾淨到不像真的。我查過，是真的。"
     "開會提到她的名字的時候，我不接話。"),
    ("0x", "tower",
     "她的經紀人。他算得很準，只算今天。"
     "他發現她的毛病能賣，然後把它做成了周邊。"
     "我沒有意見。我只是不會賣那個。"),
    ("貓草", "zerox",
     "0x 喔……她那種的我看不下去，全部都對，一次都不會出錯。"
     "出錯才好看啊。"
     "……我不是說格莉奇出錯好看，我不是那個意思。"),
    ("格莉奇", "catgrass",
     "貓草是全勤喔！等級八十！"
     "他每次都說他只是剛好有空。"
     "可是「剛好有空」兩年欸。這個我有記起來。"),
]

# 外部配音的兩位：參考音從他們**自己的成品**切下來，逐字稿是那句話的原文。
# 這樣聲線跟書裡是同一個人，也不必再等平台額度。
REF = {
    # **參考音一定要先量 F0 再用。** 本來是從第 7 句切的，而那一句是 210 Hz——
    # 它根本不是 MiniMax 那個老人，是被本機用別人的聲音靜默補過的
    # （見 voice.EXTERNAL 的警告，全書中位數 111 Hz，只有第 7、16 句是兩百多）。
    # 拿它當參考音的下場是整個聲線變成年輕人，而且聽起來完全不像同一個角色。
    "諾亞": ("voice-ref/noah.wav",
           "本來就壞掉了。我這裡沒有一台是好的。我是把很多台壞的，湊成一台會響的。", 0.9),
    "鐵塔": ("voice-ref/tower.wav",
           "內頁是空白的。附一張書籤，上面印妳的簽名。定價一千二，首批三千本，毛利四成三。", 1.0),
}


TAKE = ROOT / "art/voice/intro-take.json"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else None
    took = json.loads(TAKE.read_text(encoding="utf-8")) if TAKE.exists() else {}
    jobs, meta, fresh, views = [], {}, {}, []
    SLUG = {w: v[0] for w, v in INTRO.items()}
    # 自介與「別人怎麼說」走同一條管線：同一個角色不可以有兩種聲音。
    items = ([(w, v[0], v[1], v[2], None) for w, v in INTRO.items()]
             # 「別人怎麼說」沿用該角色自介的表演指示：同一個人在講話，
             # 沒有理由自介溫和、講別人的時候忽然變冷。
             + [(w, f"view-{SLUG[w]}-{ab}", INTRO[w][1], t, ab) for w, ab, t in VIEWS])
    for who, slug, emo, text, about in items:
        ref, ptext, speed = REF.get(who) or V.VOICE[who]
        ref = str(ROOT / ref) if not ref.startswith("/") else ref
        job = {"out": str(OUT / f"{slug}.wav"),
               "text": V.to_speech(text),        # 讀音替身，見 voice.SUB
               "prompt_wav": ref, "prompt_text": ptext, "speed": speed,
               "instruct": V.instruct(who, emo)}
        if about is None:
            meta[slug] = {"who": who, "text": text}
        else:
            views.append({"who": who, "about": about, "text": text, "slug": slug})
        # **參考音要記內容不是記路徑。** 只記路徑的話，把 voice-ref/noah.wav 換成
        # 另一段錄音（路徑一樣、內容不同）會被判定「沒變」直接跳過，而且不報錯——
        # 聲線根本沒換，驗收卻以為換過了。逐字稿也要記，它跟參考音是一組的。
        sig = (f"{job['text']}|{job['instruct']}|{job['speed']}|{ref}"
               f"|{ptext}|{hashlib.sha256(pathlib.Path(ref).read_bytes()).hexdigest()[:12]}")
        fresh[slug] = sig
        stale = took.get(slug) != sig or not pathlib.Path(job["out"]).exists()
        want = (only is None and stale) or ("--all" in sys.argv) or (only and who in only)
        print(f"  {who:5s} → {slug:22s} {len(text):3d} 字　{pathlib.Path(ref).name}"
              f"　{'重生' if want else '沒變，跳過'}")
        if want:
            # **--dry 不可以刪檔。** 乾跑是「看它打算做什麼」，
            # 之前把 unlink 寫在這裡，跑一次 --dry 就把舊音檔清掉了，
            # 而且畫面上只印「重生」，看不出檔案已經不見。
            if "--dry" not in sys.argv:
                pathlib.Path(job["out"]).unlink(missing_ok=True)
            jobs.append(job)
    def save():
        (ROOT / "art/voice/intro.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        (ROOT / "art/voice/views.json").write_text(
            json.dumps(views, ensure_ascii=False, indent=1), encoding="utf-8")

    if not jobs:
        print("\n沒有要重生的。要重擲手氣用 --all 或 --only <角色>")
        save()
        return
    (ROOT / "art/voice/intro-jobs.json").write_text(
        json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    save()
    if "--dry" in sys.argv:
        return

    # **一定要用 CosyVoice 的 venv 跑**，系統 python 沒有 torchaudio。
    py = pathlib.Path.home() / "CosyVoice/.venv/bin/python"
    env = dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1")
    rc = subprocess.call([str(py), "-u", str(ROOT / "tools/voice_batch.py"),
                          "--jobs", str(ROOT / "art/voice/intro-jobs.json")], env=env)
    if rc:
        sys.exit(rc)

    TAKE.write_text(json.dumps(fresh, ensure_ascii=False, indent=1), encoding="utf-8")
    DOCS.mkdir(parents=True, exist_ok=True)
    for w in sorted(OUT.glob("*.wav")):
        # 自介是 intro-<角色>.mp3，看法是 view-<誰>-<講誰>.mp3。
        # 檔名本身就說得出那是什麼，前端不必再組前綴。
        name = w.stem if w.stem.startswith("view-") else f"intro-{w.stem}"
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(w),
                               "-ac", "1", "-b:a", "64k", str(DOCS / f"{name}.mp3")])
    print(f"\n完成：{len(list(DOCS.glob('intro-*.mp3')))} 段自介、"
          f"{len(list(DOCS.glob('view-*.mp3')))} 段別人怎麼說")


if __name__ == "__main__":
    main()
