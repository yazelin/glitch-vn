#!/usr/bin/env python3
"""聊天頭像：跟立繪同尺寸的透明畫布，圓形擺在左側。

**定位做在圖裡，不要用 offsetX/offsetY。** 那兩個的單位是小數（市集實測
offsetX ±11、offsetY ±9），不是像素；填 300 會直接把圖推出畫面。

要調高低就改 TOP（畫布高度的百分比）。畫布底部會被對話框蓋住，所以不能太低。
"""
import pathlib, sys
from PIL import Image

AV = pathlib.Path("art/avatar")
OUT = pathlib.Path("art/chat"); OUT.mkdir(exist_ok=True)
W, H = 640, 1600          # 跟立繪同尺寸
D = 330                    # 圓形直徑
TOP = float(sys.argv[1]) if len(sys.argv) > 1 else 0.40   # 圓形上緣在畫布的幾成高
LEFT = 34
for p in sorted(AV.glob("avatar-*.png")):
    head = Image.open(p).convert("RGBA").resize((D, D), Image.LANCZOS)
    # **不要鏡射。** 立繪原本就畫成臉略朝右（朝畫面內），擺左邊剛好。
    # 我鏡射過一次，結果眼睛跑到圓的左邊變成朝外，比原本糟。
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(head, (LEFT, int(H * TOP)))
    canvas.save(OUT / p.name.replace("avatar-", "chat-"))
print(f"  圓形上緣 {TOP:.0%}　下緣 {(H*TOP+D)/H:.0%}　直徑 {D}px　共 "
      f"{len(list(OUT.glob('chat-*.png')))} 張")
