#!/usr/bin/env python3
"""量每個配音檔的頭尾靜音有多少秒。只量，不改檔案。

作法：`silenceremove` 前後各跑一次（中間 `areverse` 把音檔倒過來），
門檻 -50dB、`detection=peak`，比對修前修後的時長差。

**不可以用管線接 ffprobe 量時長。** 管線出來的 wav 沒有時長標頭，
ffprobe 回 `N/A`，於是每個檔都算成「沒有靜音」——一個假的零，
而且它長得跟「這批檔案很乾淨」一模一樣。要寫成真的檔案再量。
（這一條是 yazelin 2026-09-13 踩到並且靠負控制抓回來的。）

    python3 tools/silence_scan.py                # 全部，寫進 art/voice/silence.json
    python3 tools/silence_scan.py --limit 40     # 只量前 40 個（對數字用）

中斷可續：已經量過的代號會跳過。
"""
import argparse, json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art/voice/silence.json"
TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:detection=peak,"
        "areverse")


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def head_tail(p, tmpdir):
    """回 (原長, 修完的長, 差)。量不到回 None，不要回 0。"""
    d0 = dur(p)
    if d0 is None:
        return None
    out = pathlib.Path(tmpdir) / "t.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-af", TRIM, str(out)],
                   capture_output=True)
    d1 = dur(out)
    if d1 is None:
        return None
    return (d0, d1, round(d0 - d1, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dir", default="docs/voice")
    a = ap.parse_args()
    files = sorted((ROOT / a.dir).glob("*.mp3"))
    if a.limit:
        files = files[:a.limit]
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [f for f in files if f.stem not in have]
    print(f"{len(files)} 個檔，已經量過 {len(files) - len(todo)} 個，這次量 {len(todo)} 個")
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for i, f in enumerate(todo, 1):
            r = head_tail(f, td)
            if r is None:
                bad += 1
                continue
            have[f.stem] = {"dur": round(r[0], 3), "trimmed": round(r[1], 3), "silence": r[2]}
            if i % 200 == 0:
                OUT.write_text(json.dumps(have, ensure_ascii=False), encoding="utf-8")
                print(f"  {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have, ensure_ascii=False), encoding="utf-8")
    vals = [v["silence"] for v in have.values()]
    vals.sort()
    if vals:
        print(f"量到 {len(vals)} 個：平均 {sum(vals)/len(vals):.3f} 秒、"
              f"中位 {vals[len(vals)//2]:.3f}、最多 {vals[-1]:.3f}、"
              f"超過 0.5 秒的 {sum(1 for v in vals if v > 0.5)} 個")
    if bad:
        print(f"★ 量不到的 {bad} 個（沒有算成 0）")


if __name__ == "__main__":
    sys.exit(main())
