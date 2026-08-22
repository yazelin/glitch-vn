"""補一道：清掉被主體圍住、flood-fill 到不了的綠色區塊。

cutout.py 只清「碰得到畫面邊界」的連通區域，這是對的——眼白、瞳孔反光、
主體內部同色的小物才留得住。可是髮絲之間、手臂內側那種被圍起來的背景
它也到不了，成品貼上洋紅一看就是一圈綠。

這一支只在「角色身上本來就沒有任何綠色」的前提下能用。用之前先確認。
"""
import sys, numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA")
a = np.asarray(im).astype(np.int16)
r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
# 綠佔壓倒性優勢才算背景。門檻寬一點沒關係，因為角色身上沒有綠。
green = (g - np.maximum(r, b) > 45) & (g > 90) & (al > 0)
before = int((al > 0).sum())
a[..., 3] = np.where(green, 0, al)
# 邊緣再 despill 一次：g 壓回 r/b 的水準，不然剩下的輪廓會泛青
edge = (a[..., 3] > 0) & (np.asarray(Image.fromarray(
    (a[..., 3] > 0).astype(np.uint8) * 255).filter(
    __import__("PIL.ImageFilter", fromlist=["x"]).MinFilter(5))) == 0)
gg = np.minimum(a[..., 1], np.maximum(a[..., 0], a[..., 2]))
a[..., 1] = np.where(edge, gg, a[..., 1])
after = int((a[..., 3] > 0).sum())
Image.fromarray(a.astype(np.uint8)).save(dst)
print(f"{dst}  不透明 {before} -> {after}  清掉 {before-after}")
