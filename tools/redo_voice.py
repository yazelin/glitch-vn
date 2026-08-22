#!/usr/bin/env python3
"""重做指定的句子，用比較嚴的音高標準挑最好的一版。

平常那條產線的守門是「跟參考音比，0.87～1.25」，寬到足以放行偶爾一次的失手
——第二章「這是假的。周邊。」就是這樣過關的，聽起來太激動，量出來 1.32
（相對她自己的中位），但相對參考音只有 1.18。

這支專門用來收尾：生好幾版，挑**最接近該角色中位音高**的那一版。
角色的中位是從已經生好的檔算的，比參考音準——那才是實際的聲線。

**要用 CosyVoice 的 venv 跑**，系統 python 沒有 librosa（挑選那一步要量音高）。

用法：
    ~/CosyVoice/.venv/bin/python tools/redo_voice.py 這是假的   # 用台詞的一部分找
    ~/CosyVoice/.venv/bin/python tools/redo_voice.py v-1234abcd  # 或直接給代號
    ~/CosyVoice/.venv/bin/python tools/redo_voice.py 這是假的 -n 6  # 生幾版（預設 5）
"""
import argparse, json, pathlib, statistics, subprocess, sys, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="+")
    ap.add_argument("-n", type=int, default=5)
    a = ap.parse_args()

    import gen_voice as gv, voice as V
    from voice_batch import _f0
    rows = gv.utterances()

    picked = []
    for q in a.what:
        for w, t, e, k in rows:
            if q == k or q in t.replace("\n", ""):
                picked.append((w, t, e, k))
    if not picked:
        sys.exit(f"找不到：{a.what}")

    # 角色的中位音高：從已經生好的檔算，那才是實際聲線
    med = {}
    for w in {x[0] for x in picked}:
        vals = []
        for w2, t2, e2, k2 in rows:
            if w2 != w:
                continue
            f = OUT / f"{k2}.mp3"
            if f.exists():
                v = _f0(f)
                if v:
                    vals.append(v)
        med[w] = statistics.median(vals) if vals else 0
        print(f"{w} 的中位音高 {med[w]:.0f} Hz")

    tmp = ROOT / "art/voice/redo"
    tmp.mkdir(parents=True, exist_ok=True)
    jobs = []
    for w, t, e, k in picked:
        ref, ptext, speed = V.VOICE[w]
        ref = ref if ref.startswith("/") else str(ROOT / ref)
        for i in range(a.n):
            jobs.append({"out": str(tmp / f"{k}__{i}.wav"), "text": V.to_speech(t),
                         "prompt_wav": ref, "prompt_text": ptext, "speed": speed,
                         "instruct": V.instruct(w, e)})
    jf = tmp / "jobs.json"
    jf.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    py = pathlib.Path.home() / "CosyVoice/.venv/bin/python"
    env = dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1")
    subprocess.check_call([str(py), "-u", str(ROOT / "tools/voice_batch.py"),
                           "--jobs", str(jf)], env=env)

    import soundfile as sf
    for w, t, e, k in picked:
        m = med[w] or 0
        # 期望長度：實測語速約每秒 4.3 個字。**長度也要看**，只挑音高的話，
        # 唸得突然很快的那一版照樣會被選上（旁白「那不是這首歌的和弦。」
        # 就是這樣：音高沒問題，語速突變）。
        want = max(len(t.replace("\n", "")) / 4.3, 0.4)
        best, bd = None, 9e9
        cands = sorted(tmp.glob(f"{k}__*.wav"))
        for c in cands:
            v = _f0(c, fmin=max(60, m * 0.5), fmax=m * 1.8) if m else 0
            dur = sf.info(str(c)).duration
            dp = abs(v / m - 1) if (m and v) else 9
            dd = abs(dur / want - 1)
            d = dp + dd * 0.6            # 音高為主，長度為輔
            print(f"  {c.name}  {v:5.0f} Hz  {dur:4.1f}s（期望 {want:.1f}）"
                  f"  音高偏離 {dp:.2f} 長度偏離 {dd:.2f}")
            if d < bd:
                best, bd = c, d
        if best:
            subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(best),
                                   "-ac", "1", "-b:a", "64k", str(OUT / f"{k}.mp3")])
            (ROOT / "docs/voice" / f"{k}.mp3").write_bytes((OUT / f"{k}.mp3").read_bytes())
            print(f"★ {t[:20]} → 用 {best.name}（偏離 {bd:.2f}）")
            for c in cands:
                c.unlink()


if __name__ == "__main__":
    main()
