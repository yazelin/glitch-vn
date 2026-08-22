#!/usr/bin/env python3
"""道具卡：把物件放進一張跟立繪等高的透明畫布，位置烤進圖裡。

**立繪是貼齊畫面底部的**，所以直接把一張小圖當 actor 擺進去，它會沉到腳邊，
然後被對話框蓋掉——本子掉在地上、收據只露一個角，兩個都發生過。
`offsetY` 也救不了：那個欄位的單位是小數不是像素（市集實測 ±9）。

作法跟聊天頭貼一樣：畫布跟立繪同尺寸，物件擺在上半部，用 scale 1.0 送出去。

用法：python3 tools/make_prop_card.py [物件高度佔畫布幾成] [上緣在幾成高]
"""
import pathlib, sys
from PIL import Image

# 疊過字的版本優先（art/face-text），沒有才用純去背的（art/face）
SRC = pathlib.Path("art/face")
TEXTED = pathlib.Path("art/face-text")
OUT = pathlib.Path("art/prop"); OUT.mkdir(exist_ok=True)
W, H = 900, 1600                        # 跟立繪等高，寬一點好放橫的東西
SIZE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.30   # 物件高度佔畫布幾成
TOP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.16    # 上緣在畫布的幾成高

for p in sorted(SRC.glob("prop-*.png")):
    t = TEXTED / p.name
    im = Image.open(t if t.exists() else p).convert("RGBA")
    bbox = im.getbbox()                 # 先裁掉四周的透明邊，不然大小不一致
    if bbox:
        im = im.crop(bbox)
    h = int(H * SIZE)
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card.alpha_composite(im, ((W - im.width) // 2, int(H * TOP)))
    card.save(OUT / f"{p.stem}.png")
    print(f"  {p.stem:20s} 物件 {im.width}x{im.height}　上緣 {int(H*TOP)}／{H}")
