#!/usr/bin/env python3
"""把 pick_takes 生的某一版裝成正式的。

用法：
    python3 tools/install_take.py art/voice/takes-ch02/01-2-*.wav ...
    python3 tools/install_take.py --ch 2 01-2 02-2 03-1

序號對代號查同資料夾的 keys.tsv（pick_takes 產生的）。裝完會自動統一響度
並同步到 docs/voice。
"""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    args = [a for a in sys.argv[1:] if a != "--ch"]
    ch = None
    if "--ch" in sys.argv:
        ch = int(sys.argv[sys.argv.index("--ch") + 1])
        args = [a for a in args if a != str(ch)]

    picks = []
    for a in args:
        p = pathlib.Path(a)
        if p.exists():
            picks.append(p)
            continue
        m = re.match(r"^(\d+)-(\d+)$", a)
        if m and ch:
            d = ROOT / f"art/voice/takes-ch{ch:02d}"
            hit = list(d.glob(f"{m.group(1)}-{m.group(2)}-*.wav"))
            if hit:
                picks.append(hit[0])
                continue
        sys.exit(f"找不到：{a}")

    done = 0
    for p in picks:
        keys = p.parent / "keys.tsv"
        if not keys.exists():
            sys.exit(f"{keys} 不在，沒有代號表")
        num = p.name.split("-")[0]
        row = [l for l in keys.read_text(encoding="utf-8").splitlines()
               if l.startswith(num + "\t")]
        if not row:
            print("代號表裡沒有", num)
            continue
        _, key, text = row[0].split("\t", 2)
        for d in ("art/voice", "docs/voice"):
            subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(p),
                                   "-ac", "1", "-b:a", "64k",
                                   str(ROOT / d / f"{key}.mp3")])
        done += 1
        print(f"  {p.name} → {text[:24]}")
    print(f"裝上 {done} 句")


if __name__ == "__main__":
    main()
