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
FLIP = {"catgrass"}        # 臉朝畫面外的，只有這一個
for p in sorted(AV.glob("avatar-*.png")):
    head = Image.open(p).convert("RGBA").resize((D, D), Image.LANCZOS)
    # 頭貼永遠擺畫面左側，所以臉要朝右（朝畫面內）。
    # **逐個看過才決定要不要鏡射**：七個裡只有貓草是真的朝外（臉在圓的左半、
    # 視線往左下），其他六個都接近正面，鏡了反而破壞。
    # 判斷方法：把頭貼放大、畫一條中線，看臉偏哪一邊。縮圖看不出來，我看錯過一次。
    # 只鏡射頭部特寫是安全的——貓草的貓徽章在胸前，不在這個範圍內。
    if p.stem.split("-", 1)[1] in FLIP:
        head = head.transpose(Image.FLIP_LEFT_RIGHT)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(head, (LEFT, int(H * TOP)))
    canvas.save(OUT / p.name.replace("avatar-", "chat-"))
print(f"  圓形上緣 {TOP:.0%}　下緣 {(H*TOP+D)/H:.0%}　直徑 {D}px　共 "
      f"{len(list(OUT.glob('chat-*.png')))} 張")
