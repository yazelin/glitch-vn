#!/usr/bin/env python3
"""產 PWA 圖示。**換內容一定要換檔名**（icon-v2-… ），不要用 ?v=。

瀏覽器的 favicon 資料庫很頑固、常無視快取標頭；SW 是 cache-first；
已安裝的 PWA 圖示更是安裝當下就烤進去。改名是唯一可靠的作法。

三種輸出：
  一般圖示    內容鋪滿，四周留一點邊
  maskable   安全區是中央 80%，內容寬控在 72–76%，外面會被系統套遮罩
  favicon    32px，另外拉對比（縮到那麼小細節會糊掉）

底色用站上的 --bg #04080c。透明底在深色桌面看起來會像破圖，
在淺色桌面又變成白塊。
"""
import pathlib
from PIL import Image
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "art/sprite-glitch.png"
OUT = ROOT / "docs/img"
BG = (4, 8, 12, 255)
VER = "v2"


def head_square():
    """從立繪切出頭肩方框。**用實際 ink 邊界算，不要目測。**"""
    im = Image.open(SRC).convert("RGBA")
    a = np.asarray(im)
    top = a[: int(im.height * 0.40), ..., 3]
    ys, xs = np.where(top > 16)
    cx = (xs.min() + xs.max()) // 2
    y0, y1 = ys.min(), ys.max()
    side = int((y1 - y0) * 1.06)
    x0 = max(0, cx - side // 2)
    return im.crop((x0, y0, x0 + side, y0 + side))


def compose(head, size, inner):
    """把頭放進正方形底片。inner 是內容佔畫布的比例。"""
    canvas = Image.new("RGBA", (size, size), BG)
    w = int(size * inner)
    h = head.resize((w, w), Image.LANCZOS)
    canvas.alpha_composite(h, ((size - w) // 2, (size - w) // 2))
    return canvas


def main():
    head = head_square()
    made = []
    for size, inner, name in ((192, 0.90, f"icon-{VER}-192.png"),
                              (512, 0.90, f"icon-{VER}-512.png"),
                              (512, 0.74, f"icon-{VER}-maskable-512.png"),
                              (180, 0.90, f"icon-{VER}-180.png")):
        compose(head, size, inner).save(OUT / name)
        made.append(name)
    # favicon 32：縮到這麼小要另外拉對比，不然只剩一團藍
    small = compose(head, 128, 0.96).convert("RGB")
    from PIL import ImageEnhance
    small = ImageEnhance.Contrast(small).enhance(1.9)
    small.resize((32, 32), Image.LANCZOS).save(OUT / f"icon-{VER}-32.png")
    made.append(f"icon-{VER}-32.png")
    for n in made:
        im = Image.open(OUT / n)
        print(f"  {n:<28} {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
