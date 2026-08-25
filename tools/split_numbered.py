#!/usr/bin/env python3
"""把「第N句。台詞。」格式的長檔切成一句一個檔。

外部配音服務給的是一個長檔。**編號比台詞可靠**：服務唸出來的「第N句」
是很好的錨點，短台詞（「等一下。」）拿去對齊會在幾百字外找到假匹配。

**切點只能往後吸，不能往回。** 往回吸會吸到錨點前面那個停頓，
於是「第三句」被切進台詞裡，而 ASR 驗收只會說相似度掉了一點，
不會告訴你原因（實際發生過：12 句裡有 3 句開頭多唸了編號）。

    python3 tools/split_numbered.py <長檔> <輸出目錄> [--lines 逐字稿.txt]
"""
import re, sys, pathlib


def main():
    import librosa, numpy as np, soundfile as sf, whisper, difflib
    src = sys.argv[1]
    out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    want = []
    if "--lines" in sys.argv:
        want = [l.strip() for l in
                pathlib.Path(sys.argv[sys.argv.index("--lines") + 1]
                             ).read_text(encoding="utf-8").splitlines() if l.strip()]

    y, sr = librosa.load(src, sr=24000, mono=True)
    m = whisper.load_model("large-v3-turbo", device="cuda")
    r = m.transcribe(src, language="zh", initial_prompt="繁體中文", word_timestamps=True)
    words = [w for s in r["segments"] for w in s.get("words", [])]
    txt = "".join(w["word"] for w in words)

    def at(i):
        n = 0
        for w in words:
            if n + len(w["word"]) > i:
                return w["start"], w["end"]
            n += len(w["word"])
        return words[-1]["end"], words[-1]["end"]

    marks = [(mm.start(), mm.end()) for mm in
             re.finditer(r"第([0-9零一二三四五六七八九十]{1,3})[句局]", txt)]
    iv = librosa.effects.split(y, top_db=32)
    gaps = [(iv[k][1] / sr, iv[k + 1][0] / sr) for k in range(len(iv) - 1)]

    def snap(t, lo, hi, lim=0.6):
        """把切點推到最近的停頓，**但不准跑出 [lo, hi]**。"""
        best, bd = t, lim
        for a, b in gaps:
            c = (a + b) / 2
            if lo <= c <= hi and abs(c - t) < bd:
                best, bd = c, abs(c - t)
        return best

    cjk = lambda s: re.sub(r"[^一-鿿]", "", s)
    ok = 0
    for i, (ms, me) in enumerate(marks):
        anchor_end = at(me)[0]
        nxt = at(marks[i + 1][0])[0] if i + 1 < len(marks) else len(y) / sr
        st = snap(anchor_end, anchor_end, nxt)          # 只能往後
        en = snap(nxt, st, nxt)
        seg = y[int(st * sr):int(en * sr)]
        f = out / f"{i + 1:02d}.wav"
        sf.write(f, seg, sr)
        t = m.transcribe(str(f), language="zh", initial_prompt="繁體中文")["text"].strip()
        bleed = bool(re.match(r"第[0-9零一二三四五六七八九十]{1,3}[句局]", t))
        sim = (difflib.SequenceMatcher(None, cjk(want[i]), cjk(t)).ratio()
               if i < len(want) else 1.0)
        good = sim >= 0.6 and not bleed
        ok += good
        tag = "★編號切進去" if bleed else ("★對不上" if sim < 0.6 else "ok ")
        print(f"  {tag:12s}{i+1:2d} {len(seg)/sr:5.2f}s  {t[:38]}")
    print(f"\n=== {ok}/{len(marks)} ===")
    sys.exit(0 if ok == len(marks) else 1)


if __name__ == "__main__":
    main()
