#!/usr/bin/env python3
"""把每個配音檔的頭尾靜音修掉。**只修頭尾，中間的停頓不動。**

    ~/voice-venv/bin/python tools/trim_silence.py --self-test   # 負控制，先跑這個
    python3 tools/trim_silence.py --dry                          # 只看會修幾個
    python3 tools/trim_silence.py                                # 真的修

**量法會靜默失敗，所以先跑負控制。** 用管線接 ffprobe 量時長，管線出來的 wav
沒有時長標頭，ffprobe 回 `N/A`，於是每個檔都算成「沒有靜音」——一個假的零，
而且它長得跟「這批檔案很乾淨」一模一樣。`--self-test` 拿一個**已知加了靜音**
的檔去跑，確認修法真的會動、而且量得到差值。

**先寫暫存再原子換過去**：跑到一半被中斷不會留下半寫的檔。
帳本記在 art/voice/trimmed.json，可以中斷續跑。
"""
import argparse, json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art/voice"
LEDGER = OUT / "trimmed.json"
TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:detection=peak,"
        "areverse")
KEEP = 0.05      # 頭尾各留一點點，不要切到氣音


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def trim_to(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    f"{TRIM},adelay={int(KEEP*1000)}|{int(KEEP*1000)},"
                    f"areverse,adelay={int(KEEP*1000)}|{int(KEEP*1000)},areverse",
                    "-ac", "1", "-b:a", "64k", str(dst)], capture_output=True)
    return dur(dst)


def self_test():
    print("負控制：拿一個檔，前後各加 0.8 秒靜音，看修得掉嗎")
    src = next(OUT.glob("v-*.mp3"))
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        padded = td / "padded.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                        "adelay=800|800,areverse,adelay=800|800,areverse",
                        "-ac", "1", "-b:a", "64k", str(padded)], capture_output=True)
        d0, d1 = dur(src), dur(padded)
        if d1 is None:
            print("✘ 量不到加料之後的時長——量法就是壞的，不要往下做"); return 1
        print(f"  原檔 {d0:.2f} 秒 → 加料後 {d1:.2f} 秒（多了 {d1-d0:.2f}，預期約 1.6）")
        out = td / "trimmed.mp3"
        d2 = trim_to(padded, out)
        if d2 is None:
            print("✘ 量不到修完的時長"); return 1
        print(f"  修完 {d2:.2f} 秒（跟原檔差 {d2-d0:+.2f}）")
        ok = abs(d2 - d0 - 2 * KEEP) < 0.25
        print(("  ✔ 修法有效" if ok else "  ✘ 修法沒把加的靜音拿掉")
              + f"　（判準：修完要回到原檔 ±0.25 秒，含刻意保留的 {KEEP*2:.2f} 秒）")
        # 反向：拿一個沒加料的檔再跑一次，時長不該掉太多
        out2 = td / "again.mp3"
        d3 = trim_to(src, out2)
        print(f"  對照：原檔直接修 {d0:.2f} → {d3:.2f}（掉 {d0-d3:.2f} 秒，那是它本來就有的頭尾靜音）")
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--min", type=float, default=0.08, help="小於這個秒數就不值得修")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    files = sorted(OUT.glob("v-*.mp3"))
    todo = [f for f in files if led.get(f.name) != int(f.stat().st_mtime)]
    print(f"{len(files)} 個檔，這次看 {len(todo)} 個")
    cut = kept = bad = 0
    total = 0.0
    with tempfile.TemporaryDirectory() as td:
        for i, f in enumerate(todo, 1):
            d0 = dur(f)
            if d0 is None:
                bad += 1; continue
            tmp = pathlib.Path(td) / "t.mp3"
            d1 = trim_to(f, tmp)
            if d1 is None or d1 < 0.15:      # 修完幾乎沒東西：不要動它
                kept += 1; continue
            if d0 - d1 < a.min:
                kept += 1
                led[f.name] = int(f.stat().st_mtime)
                continue
            if not a.dry:
                tmp.replace(f)
                led[f.name] = int(f.stat().st_mtime)
            cut += 1; total += d0 - d1
            if i % 200 == 0:
                if not a.dry:
                    LEDGER.write_text(json.dumps(led), encoding="utf-8")
                print(f"  {i}/{len(todo)}　修了 {cut}", flush=True)
    if not a.dry:
        LEDGER.write_text(json.dumps(led), encoding="utf-8")
    print(f"修了 {cut} 個（共去掉 {total:.1f} 秒，平均 {total/max(cut,1):.3f}）、"
          f"不用修 {kept} 個、量不到 {bad} 個")
    return 0


if __name__ == "__main__":
    sys.exit(main())
