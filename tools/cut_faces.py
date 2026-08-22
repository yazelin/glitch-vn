#!/usr/bin/env python3
"""表情差分去背：綠幕 key → 清內部殘留 → 負控制驗收。

三步一定要照順序，而且**驗收要貼洋紅**：貼白底或棋盤格看不出「整片被吃掉」。
cutout skill 只清碰得到畫面邊界的連通區域（這是對的，眼白才留得住），
髮絲之間那種被主體圍起來的綠它到不了，所以要補 interior.py 那一道。

用法：python3 tools/cut_faces.py [名字...]      不給名字就處理 art/out/face-*.png
"""
import pathlib, subprocess, sys
from PIL import Image
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
CUT = pathlib.Path.home() / ".claude/skills/cutout/cutout.py"
OUT = ROOT / "art/face"; OUT.mkdir(parents=True, exist_ok=True)
TMP = pathlib.Path("/tmp/_face.png")


def run(*a):
    r = subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(f"失敗：{a}")
    return r.stdout


def audit(p):
    """負控制：貼洋紅之後量不透明像素與殘留綠。指標會說謊，所以兩個都看。"""
    im = Image.open(p).convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    al = a[..., 3]
    opaque = int((al > 200).sum())
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = int((((g - np.maximum(r, b)) > 30) & (al > 40)).sum())
    corners = [int(al[y, x]) for y in (0, im.height - 1) for x in (0, im.width - 1)]
    return opaque, green, corners


def main(names):
    src = ROOT / "art/out"
    files = [src / f"{n}.png" for n in names] if names else sorted(src.glob("face-*.png"))
    for f in files:
        if not f.exists():
            print(f"  ★ 沒有 {f.name}"); continue
        run(CUT, "key", f, "-o", TMP)
        run(ROOT / "tools/interior.py", TMP, OUT / f.name)
        opaque, green, corners = audit(OUT / f.name)
        flag = "" if green < opaque * 0.004 and max(corners) == 0 else "  ★ 要看一下"
        print(f"  {f.stem:22s} 不透明 {opaque:7d}　殘留綠 {green:5d}　四角 {corners}{flag}")


if __name__ == "__main__":
    main(sys.argv[1:])
