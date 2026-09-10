#!/usr/bin/env python3
"""把調查篇的美術轉成網頁用的 webp。跑：python3 tools/gen_inv_art.py

`art/` 裡是工作檔：背景 1920×1080 的 jpg、立繪 1024×1536 的 png，四個資料夾加起來三十 MB。
**那些不能直接放上網**。正篇站的 `docs/img/` 是二十四張 webp、三點八 MB，
這一支照同一個標準產調查篇那一份。

  背景     長邊 1600、webp q80
  立繪     長邊 900、webp q82、留透明
  螢幕道具 長邊 700
  背包道具 長邊 500
  縮圖     長邊 480，畫廊列表用（檔名加 -t）

輸出到 docs/img/inv/（跟正篇的 docs/img/ 收在一起）。**原圖不進 docs**，也不要在網頁上連 art/。
"""
import pathlib
import sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/img/inv"
# 來源資料夾 → （長邊, 品質, 要不要另外產縮圖）
JOBS = [("art/bg-investigation", 1600, 80, True),
        ("art/inv-cast", 900, 82, True),
        ("art/screens", 700, 82, False),
        ("art/items", 500, 82, False)]
THUMB = 480


def convert(src: pathlib.Path, dst: pathlib.Path, long_edge: int, q: int):
    im = Image.open(src)
    # 立繪要留透明，背景不用。轉 RGB 會把透明壓成黑。
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
    else:
        im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > long_edge:
        s = long_edge / max(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=q, method=6)
    return dst.stat().st_size


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = n = 0
    for folder, long_edge, q, thumb in JOBS:
        src_dir = ROOT / folder
        if not src_dir.exists():
            print(f"  跳過（沒有這個資料夾）{folder}")
            continue
        for p in sorted(src_dir.iterdir()):
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                continue
            # 綠幕／洋紅幕的原圖是去背用的中間產物，不上網
            if "-on-magenta" in p.stem or "-on-green" in p.stem or p.stem.endswith("-raw"):
                continue
            total += convert(p, OUT / f"{p.stem}.webp", long_edge, q)
            n += 1
            if thumb:
                total += convert(p, OUT / f"{p.stem}-t.webp", THUMB, 78)
                n += 1
    print(f"寫出 {n} 個檔到 {OUT.relative_to(ROOT)}／共 {total/1024/1024:.1f} MB")
    src_mb = sum(f.stat().st_size for folder, *_ in JOBS
                 for f in (ROOT / folder).glob("*") if f.is_file()) / 1024 / 1024
    print(f"原始 {src_mb:.1f} MB → 網頁用 {total/1024/1024:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
