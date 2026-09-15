#!/usr/bin/env python3
"""抓「秒數跟字數對不上」的音檔——太長的多半在跳針，太短的是被切掉。

**這一類靠聽寫抓不到。** 一兩個字的句子，ASR 的輸出本來就不可信
（「喔。」被聽成一串俄文），所以 asr_audit 把短句整批濾掉了。
但「兩個字唸了六秒」是算得出來的，不需要知道它唸了什麼。

每個字大約 0.22 到 0.30 秒（本書 2020 句量出來的中位數）。門檻取得寬，
因為句號、破折號、情緒停頓都會拉長，抓的是離譜的那些。

**ffprobe 不可以用管線餵。** 餵 stdin 的話它回 N/A，浮點轉換會炸或變成 0，
於是「每一個檔都超短」——那是假的。一定要給檔案路徑。

    python3 tools/len_scan.py
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "larch"))
import re


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    t = r.stdout.strip()
    return float(t) if t and t != "N/A" else None


def main():
    import gen_voice as G, voice as V
    rows = []
    for who, text, emo, k in G.utterances():
        said = V.to_speech(text)
        n = len(re.sub(r"[^\w一-鿿]+", "", said))
        if not n:
            continue
        p = ROOT / "docs/voice" / f"{k}.mp3"
        if not p.exists():
            p = ROOT / "art/voice" / f"{k}.mp3"
        if not p.exists():
            continue
        d = dur(p)
        if d is None:
            print(f"★ 量不到秒數：{p}")
            continue
        rows.append({"key": k, "who": who, "text": text, "n": n, "sec": round(d, 2),
                     "per": round(d / n, 3)})
    rows.sort(key=lambda r: -r["per"])
    # 門檻：每字 0.9 秒以上算太長（中位數約 0.27，四倍以上）；0.12 以下算太短。
    long_ = [r for r in rows if r["per"] > 0.9]
    short = [r for r in rows if r["per"] < 0.12]
    mid = sorted(r["per"] for r in rows)[len(rows) // 2]
    print(f"{len(rows)} 句。每字秒數中位數 {mid:.3f}")
    print(f"  太長（>0.9，疑似跳針）：{len(long_)} 句")
    print(f"  太短（<0.12，疑似被切掉）：{len(short)} 句\n")
    for r in long_[:25]:
        print(f"  {r['sec']:>6.2f}秒 / {r['n']:>2}字 = {r['per']:.2f}　{r['who']}｜{r['text'][:22]}".replace("\n", "／"))
    if short:
        print()
        for r in short[:10]:
            print(f"  {r['sec']:>6.2f}秒 / {r['n']:>2}字 = {r['per']:.2f}　{r['who']}｜{r['text'][:22]}".replace("\n", "／"))
    (ROOT / "art/voice/len-scan.json").write_text(
        json.dumps(long_ + short, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
