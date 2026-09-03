#!/usr/bin/env python3
"""量每個角色所有配音的基頻，抓出「被換成別人聲音」的句子。

**這是靜默故障，用聽的很難發現。** 全書七百句，某一句忽然變成另一個人的聲音，
除非剛好聽到那一句，不然它會一路上線。而它真的發生過：

  諾亞 第 7、16 句是 210 Hz，他其他 17 句的中位數是 111 Hz。
  那兩句不是 MiniMax 那個老人，是 gen_voice 看到缺檔就用本機補的
  （見 voice.EXTERNAL 的警告）。更糟的是我後來還拿第 7 句去切 zero-shot
  的參考音，於是自介整段變成年輕人的聲音。

用法：

    python3 tools/scan_voice_f0.py            # 全部角色
    python3 tools/scan_voice_f0.py 諾亞 鐵塔

**短句量不準**。1 到 2 秒、有聲比例低的句子（「嗯。」「我說好。」）pyin 會貼著
下限回 60 Hz，看起來像大暴走其實只是量不到。所以短句另外標「量不準」，
不列進判定，也不要拿它去嚇人。

要 librosa，跑在 CosyVoice 的 venv：

    ~/voice-venv/bin/python tools/scan_voice_f0.py
"""
import io, pathlib, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
import voice as V  # noqa: E402

MIN_SEC = 2.5       # 比這短的不判定，只標「量不準」
TOL = 0.25          # 偏離中位數這個比例就點名


def main():
    import librosa, numpy as np

    def f0(p):
        y, sr = librosa.load(str(p), sr=16000)
        f, _, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr)
        f = f[~np.isnan(f)]
        return (float(np.median(f)) if len(f) else float("nan"),
                librosa.get_duration(y=y, sr=sr))

    who_list = [a for a in sys.argv[1:] if not a.startswith("-")] or [
        p.stem.replace("-對照", "")
        for p in (ROOT / "design/台詞").glob("*-對照.txt")]
    bad = 0
    for who in who_list:
        f = ROOT / f"design/台詞/{who}-對照.txt"
        if not f.exists():
            continue
        rows = []
        for ln in f.read_text(encoding="utf-8").splitlines():
            if "｜" not in ln:
                continue
            n, emo, txt = [x.strip() for x in ln.split("｜", 2)]
            k = V.key(who, txt, None if emo == "—" else emo)
            p = ROOT / f"art/voice/{k}.mp3"
            if p.exists():
                hz, sec = f0(p)
                rows.append((n, k, hz, sec, txt))
        long = [r for r in rows if r[3] >= MIN_SEC and r[2] == r[2]]
        if len(long) < 3:
            print(f"{who:6s} 可判定的句子太少（{len(long)} 句），跳過")
            continue
        med = statistics.median(r[2] for r in long)
        off = [r for r in long if abs(r[2] - med) / med > TOL]
        bad += len(off)
        print(f"\n{who}　中位數 {med:.0f} Hz　可判定 {len(long)} 句"
              f"　（另有 {len(rows) - len(long)} 句太短，量不準）")
        for n, k, hz, sec, txt in off:
            print(f"  ★ 第{n:>3}句 {hz:6.1f} Hz  {sec:4.1f}s  {k}")
            print(f"     「{txt[:38]}」")
        if not off:
            print("  都在範圍內")
    print(f"\n=== 點名 {bad} 句 ===")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
