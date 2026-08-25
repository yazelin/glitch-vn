#!/usr/bin/env python3
"""角色頁的自我介紹配音：一個角色一段，讀者按下去就聽得到那個人的聲音。

用意是**在讀之前先認識聲音**。所以這七段一律不碰第七章的答案，
也不講守則本後來怎麼了——只講這個人自己是誰。

聲線跟全書共用同一組參考音（larch/voice.py 的 VOICE），**不可以另外選角**：
角色頁聽到的聲音跟書裡不是同一個人的話，這個功能就是反效果。

諾亞與鐵塔走的是外部配音（Larch 的 MiniMax），他們的參考音是從**自己的成品**
切下來的，逐字稿一個字都沒改（見 voice-ref/noah.wav、tower.wav 與下面的 REF）。
不用 scratchpad 那批試驗檔：那個目錄會隨 session 消失，聲線就重建不出來。

    python3 tools/gen_intro.py           # 生 wav 再轉 mp3 進 docs/voice/
    python3 tools/gen_intro.py --dry     # 只寫 jobs.json，不跑模型
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
    "格莉奇": ("glitch", None,
             "大家好，我是格莉奇。虛擬主播，頻道第二年。"
             "我的記憶體只有四KB。這是我的口頭禪，也是實話。"
             "放不下的東西會被擠掉，所以我每天晚上都會抄一次守則本。"
             "第一頁有七行，上面有六個名字。"
             "我知道有第七個。我只是叫不出來。"),
    "黑洞先生": ("blackhole", None,
              "我住在她家。沙發那一邊。"
              "我吃被忘掉的事。吃進去的永遠在我裡面，可是拿不出來。"
              "她從來沒有為這件事跟我道過歉。這樣很好。"),
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
    "諾亞": ("noah", None,
           "我姓諾亞。修收音機的。"
           "店在頂樓，招牌是從樓下騎樓搬上來的，字看不清楚了沒關係，要找的人找得到。"
           "樓下那個小姑娘常常把自己鎖在門外。"
           "她一個禮拜來問我三次同一件事。我每次都回答。"
           "因為她每次都是第一次問啊。"),
}

# 外部配音的兩位：參考音從他們**自己的成品**切下來，逐字稿是那句話的原文。
# 這樣聲線跟書裡是同一個人，也不必再等平台額度。
REF = {
    "諾亞": ("voice-ref/noah.wav",
           "一九六四年的。真空管的。這種東西現在沒有人修了，因為零件停產四十年了。", 0.9),
    "鐵塔": ("voice-ref/tower.wav",
           "內頁是空白的。附一張書籤，上面印妳的簽名。定價一千二，首批三千本，毛利四成三。", 1.0),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, meta = [], {}
    for who, (slug, emo, text) in INTRO.items():
        ref, ptext, speed = REF.get(who) or V.VOICE[who]
        ref = str(ROOT / ref) if not ref.startswith("/") else ref
        jobs.append({"out": str(OUT / f"{slug}.wav"),
                     "text": V.to_speech(text),   # 讀音替身，見 voice.SUB
                     "prompt_wav": ref, "prompt_text": ptext, "speed": speed,
                     "instruct": V.instruct(who, emo)})
        meta[slug] = {"who": who, "text": text}
        print(f"  {who:5s} → {slug:10s} {len(text):3d} 字　{pathlib.Path(ref).name}")
    (ROOT / "art/voice/intro-jobs.json").write_text(
        json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "art/voice/intro.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    if "--dry" in sys.argv:
        return

    # **一定要用 CosyVoice 的 venv 跑**，系統 python 沒有 torchaudio。
    py = pathlib.Path.home() / "CosyVoice/.venv/bin/python"
    env = dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1")
    rc = subprocess.call([str(py), "-u", str(ROOT / "tools/voice_batch.py"),
                          "--jobs", str(ROOT / "art/voice/intro-jobs.json")], env=env)
    if rc:
        sys.exit(rc)

    DOCS.mkdir(parents=True, exist_ok=True)
    for w in sorted(OUT.glob("*.wav")):
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(w),
                               "-ac", "1", "-b:a", "64k",
                               str(DOCS / f"intro-{w.stem}.mp3")])
    print(f"\n完成：{len(list(DOCS.glob('intro-*.mp3')))} 段自介")


if __name__ == "__main__":
    main()
