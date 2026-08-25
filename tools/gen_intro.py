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
import json, os, pathlib, subprocess, sys

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
             "我的記憶體只有四KB。這句話我每天都要講一次，而且它是真的。"
             "放不下的東西會被擠掉，所以我每天晚上都會抄一次守則本。"
             "第一頁有七行，上面有六個名字。"
             "我知道有第七個。我只是叫不出來。"),
    # **不可以寫成他睡在她家沙發。** 那讓他看起來像寄住，而正典是
    # 「一段互相剛好的關係」：他有正職，她是他唯一吃得飽的地方，兩邊都不吃虧。
    # 也不要寫成可憐或委屈，他的底色是沉穩、脾氣好、半闔眼的溫和微笑。
    "黑洞先生": ("blackhole", None,
              "我是她的室友。"
              "我有正職，早上出門，晚上回來。"
              "我吃被忘掉的事。別人掉的都是碎的，她掉的是一整件，有頭有尾。"
              "所以我在這裡。這樣對我們兩個都剛好。"),
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
     "我們在樓梯口點過頭很多次了，沒講過話。"
     "有些人不用講話，你看他站在那裡就知道他不會走。"),
    ("黑洞先生", "noah",
     "頂樓那位。他把別人掉的東西收著，等人來拿。"
     "我也收東西。可是我這裡沒有人來拿，也拿不走。"),
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
     "他發現她的毛病能賣。"
     "我沒有意見。我只是不會做那件事。"),
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
    "諾亞": ("voice-ref/noah.wav",
           "一九六四年的。真空管的。這種東西現在沒有人修了，因為零件停產四十年了。", 0.9),
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
             + [(w, f"view-{SLUG[w]}-{ab}", None, t, ab) for w, ab, t in VIEWS])
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
        sig = f"{job['text']}|{job['instruct']}|{job['speed']}|{ref}"
        fresh[slug] = sig
        stale = took.get(slug) != sig or not pathlib.Path(job["out"]).exists()
        want = (only is None and stale) or ("--all" in sys.argv) or (only and who in only)
        print(f"  {who:5s} → {slug:22s} {len(text):3d} 字　{pathlib.Path(ref).name}"
              f"　{'重生' if want else '沒變，跳過'}")
        if want:
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
