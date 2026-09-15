#!/usr/bin/env python3
"""哪幾句的配音過期了——**把「沒有紀錄」跟「紀錄不符」分開**。

2026-09-15 踩到：判準寫成 `spoken.get(k) != to_speech(text)`，
而 `spoken.json` 裡沒有紀錄的句子 `spoken.get()` 回 `None`，
一律不等於任何字串，於是**早期生的那批全部被判定要重生**——
700 句裡大部分音檔是好的，而當時有人正在聽那個頁面。

    python3 tools/stale_check.py            # 只報告
    python3 tools/stale_check.py --delete   # 真的刪（刪之前先確認沒有人在聽）
"""
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delete", action="store_true")
    a = ap.parse_args()
    import gen_voice as G, voice as V
    from voice import LARCH_VOICE as LV
    spoken = json.loads((ROOT / "art/voice/spoken.json").read_text(encoding="utf-8"))
    pk = ROOT / "art/voice/picked.json"
    picked = set(json.loads(pk.read_text(encoding="utf-8"))) if pk.exists() else set()

    mismatch, norec, fine = [], [], 0
    for who, text, emo, k in G.utterances():
        if who in LV or k in picked:
            continue
        said = V.to_speech(text)
        if k in spoken:
            if spoken[k] != said:
                mismatch.append((who, text, spoken[k], said))
            else:
                fine += 1
        elif said != text:
            # 沒有紀錄，而且這一句有套替身——**可能**過期，但也可能它本來就是
            # 照替身版生的、只是沒有登記。要靠聽或 ASR 才判得了。
            norec.append((who, text, said))
        else:
            fine += 1
    print(f"紀錄不符（**一定要重生**）：{len(mismatch)} 句")
    for w, t, was, now in mismatch[:8]:
        print(f"  {w}｜{t[:20]}".replace("\n", "／"))
        print(f"      當初唸 {was[:24]}".replace("\n", "／"))
        print(f"      現在要 {now[:24]}".replace("\n", "／"))
    print(f"沒有紀錄、而且有套替身（**不確定**，不要一律重生）：{len(norec)} 句")
    print(f"對得上或沒套替身：{fine} 句")
    if a.delete:
        n = 0
        for w, t, was, now in mismatch:
            k = V.key(w, t, None)
            for d in ("art/voice", "docs/voice"):
                for e in (".mp3", ".wav"):
                    p = ROOT / d / (k + e)
                    if p.exists():
                        p.unlink(); n += 1
        print(f"只刪了「紀錄不符」那 {len(mismatch)} 句的 {n} 個檔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
