#!/usr/bin/env python3
"""把七章裡的每一句話生成語音。

**不用平台的即時生成。** 播放器吃 `voiceUrl`（卡片層與每一行對話都有），
所以自己生、自己上傳，額度無關，而且聲線控制得住——同一個角色不可以有兩種聲音。

引擎是 CosyVoice3 zero-shot clone：給一段參考音加那段話的逐字稿，就能用那個
聲音唸任何文字，不用訓練。參考音的對應寫在 larch/voice.py 的 VOICE。

檔名用內容雜湊（見 voice.key），所以卡片搬家不用重生，改字才重生那一句。

用法：
    python3 tools/gen_voice.py --list          # 只列出要生幾句、每個角色幾句
    python3 tools/gen_voice.py --who 格莉奇     # 只生某個角色
    python3 tools/gen_voice.py                 # 生全部缺的
"""
import collections, json, os, pathlib, runpy, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"


def utterances():
    """空跑七章，收集每一句要唸的話。回傳 [(講者, 台詞, 情緒, 代號)]。"""
    import novelkit as nk
    import voice as V
    built = {}
    nk.Chapter.push = lambda self, s: built.setdefault(self.bid, self.nodes) or {}
    nk.ensure_characters = lambda: {n: f"c-{n}" for n in list(nk.SPRITE) + ["旁白"]}
    # 素材網址在這一步用不到，缺鍵時給個假的，免得 A[...] 爆掉
    class _A(dict):
        def __missing__(self, k): return f"x/{k}"
    nk.A = _A(nk.A)
    for f in sorted((ROOT / "larch").glob("build_ch0*.py")):
        runpy.run_path(str(f), run_name="__main__")

    out, seen = [], set()
    for bid in sorted(built):
        for n in built[bid]:
            d = n["data"]
            if (d.get("type") or "dialogue") != "dialogue":
                continue
            lines = d.get("dialogueLines") or []
            # emotion 一併收走：表演指示是用它決定的（見 voice.instruct）。
            # 多人卡片上，emotion 只掛在「臉有換」的那個人身上（novelkit.talk），
            # 其他行是空字串，剛好就是我們要的分辨方式。
            if lines:
                items = [(l.get("speaker"), l.get("text"), l.get("emotion"))
                         for l in lines]
            else:
                items = [(d.get("speaker"), d.get("text"), d.get("emotion"))]
            for sp, tx, emo in items:
                if not sp or not tx or not tx.strip():
                    continue
                k = V.key(sp, tx, emo)
                if k in seen:            # 同一句話只生一次
                    continue
                seen.add(k)
                out.append((sp, tx, emo or None, k))
    return out


def main():
    args = sys.argv[1:]
    import voice as V
    us = utterances()
    by = collections.Counter(s for s, _, _, _ in us)
    OUT.mkdir(parents=True, exist_ok=True)
    # docs/voice 也要算進來——進 git 的是那一份，art/voice 只是工作區。
    # 少了它，重新 clone 之後會把六百多句全部重生一次。
    have = ({p.stem for p in OUT.glob("*.wav")} | {p.stem for p in OUT.glob("*.mp3")}
            | {p.stem for p in (ROOT / "docs/voice").glob("*.mp3")})
    todo = [u for u in us if u[3] not in have]
    if "--who" in args:
        who = args[args.index("--who") + 1]
        todo = [u for u in todo if u[0] == who]

    print(f"全書 {len(us)} 句（去重後），已生 {len(us) - len(todo)}，這次要生 {len(todo)}")
    print("\n各角色：")
    for k, v in by.most_common():
        print(f"  {k:8s} {v:4d} 句  {'' if V.VOICE.get(k) else '★ 還沒選參考音'}")
    if "--list" in args:
        return

    # 沒有參考音的角色直接跳過，不要擋住其他人。貓草只打字不出聲，
    # 本來就可能整個不配——那不是缺漏，是設計。
    # 外部配音的角色缺檔就是缺檔，不可以拿本機的聲音補（見 voice.EXTERNAL）
    ext = sorted({s for s, _, _, _ in todo if s in getattr(V, "EXTERNAL", ())})
    if ext:
        n = len([1 for s, _, _, _ in todo if s in ext])
        print(f"\n★ 跳過外部配音角色的 {n} 句：{ext}")
        print("  那些要回頭從長檔補切，不可以就地生，不然會變成另一個人的聲音")
        todo = [u for u in todo if u[0] not in ext]
    skip = sorted({s for s, _, _, _ in todo if not V.VOICE.get(s)})
    if skip:
        print(f"\n跳過（還沒選參考音）：{skip}")
        todo = [u for u in todo if V.VOICE.get(u[0])]
    if not todo:
        print("沒有要生的。")
        return

    jobs = []
    for who, text, emo, k in todo:
        ref, ptext, speed = V.VOICE[who]
        jobs.append({"out": str(OUT / f"{k}.wav"),
                     "text": V.to_speech(text),          # 讀音替身，見 voice.SUB
                     "prompt_wav": str(ROOT / ref) if not ref.startswith("/") else ref,
                     "prompt_text": ptext, "speed": speed,
                     "instruct": V.instruct(who, emo)})
    jf = ROOT / "art/voice/jobs.json"
    jf.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n寫好 {len(jobs)} 個工作 → {jf}")
    if "--dry" in args:
        return

    # **一定要用 CosyVoice 的 venv 跑**，系統 python 沒有 torchaudio。
    # 離線旗標也不能省：modelscope 會去抓 FST 檔然後卡住。
    py = pathlib.Path.home() / "CosyVoice/.venv/bin/python"
    env = dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1")
    rc = subprocess.call([str(py), "-u", str(ROOT / "tools/voice_batch.py"),
                          "--jobs", str(jf)], env=env)
    if rc:
        sys.exit(rc)
    print("\n轉 mp3（wav 進不了 git，見 .gitignore）")
    for w in sorted(OUT.glob("*.wav")):
        m = w.with_suffix(".mp3")
        if m.exists():
            continue
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(w),
                               "-ac", "1", "-b:a", "64k", str(m)])
    print(f"完成：{len(list(OUT.glob('*.mp3')))} 個 mp3")


if __name__ == "__main__":
    main()
