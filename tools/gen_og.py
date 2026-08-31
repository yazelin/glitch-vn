#!/usr/bin/env python3
"""生分享用的 OG 圖（1200x630）、寬幅橫幅（1600x520）與 favicon。

不用生成模型畫：這張圖的內容是既有的立繪加標題，用合成的比較準、字比較利，
而且改標題重跑就好。字型用系統的 Noto Serif CJK TC。
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path.home() / "glitch-vn"
IMG = ROOT / "docs/img"
BG, CY, MINT, TEXT, MUTED = "#04080c", "#25c2e8", "#7cf3c0", "#dfe8ec", "#93a3ac"
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIF_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
MONO = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
# .ttc 裡面 TC 不是第 0 個字面，挑錯會拿到日文字形
TC = 3


def f(path, size, idx=TC):
    return ImageFont.truetype(path, size, index=idx)


def sprite(name, h):
    im = Image.open(ROOT / f"art/sprite-{name}.png").convert("RGBA")
    im = im.crop(im.getchannel("A").getbbox())
    im.thumbnail((900, h), Image.LANCZOS)
    return im


W, H = 1200, 630
c = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(c)

# 底部一條 cy→mint 的漸層，跟站上章名那條線同一個手法
for x in range(W):
    t = x / W
    d.line([(x, H - 6), (x, H)], fill=(int(0x25 + (0x7c - 0x25) * t),
                                       int(0xc2 + (0xf3 - 0xc2) * t),
                                       int(0xe8 + (0xc0 - 0xe8) * t)))

g, b = sprite("glitch", 560), sprite("blackhole", 580)
c.paste(g, (36, H - 6 - g.height), g)
c.paste(b, (W - b.width - 30, H - 6 - b.height), b)

cx = W // 2
d.text((cx, 132), "繁體中文小說・全七章", font=f(MONO, 25), fill=CY, anchor="mm")
d.text((cx, 226), "格莉奇與黑洞先生", font=f(SERIF, 76), fill=TEXT, anchor="mm")
d.text((cx, 320), "兩年前開台第一天來了七個人。", font=f(SERIF_R, 30), fill=MUTED, anchor="mm")
d.text((cx, 366), "她說，我要記住每一個來的人，我保證。", font=f(SERIF_R, 30), fill=MUTED, anchor="mm")
d.text((cx, 452), "她記得六個。", font=f(SERIF, 44), fill=MINT, anchor="mm")

c.save(IMG / "og.jpg", quality=88, optimize=True)
print(f"  og.jpg 1200x630  {(IMG / 'og.jpg').stat().st_size // 1024} KB")

# ── 寬幅橫幅 1600x520 ──────────────────────────────────
# 給 Larch 個人頁那種寬版頭圖用。**不要拿 og.jpg 去裁**：3.08:1 太扁，
# 全身立繪塞進去只剩一條，字也會被壓到沒有空間。改成只留上半身、字橫排。
def bust(name, h, keep=0.52):
    """上半身：從去背後的 bbox 取上面 keep 的比例，再縮到高度 h。"""
    im = Image.open(ROOT / f"art/sprite-{name}.png").convert("RGBA")
    im = im.crop(im.getchannel("A").getbbox())
    im = im.crop((0, 0, im.width, int(im.height * keep)))
    im.thumbnail((900, h), Image.LANCZOS)
    return im


W2, H2 = 1600, 520
w = Image.new("RGB", (W2, H2), BG)
d2 = ImageDraw.Draw(w)
for x in range(W2):
    tt = x / W2
    d2.line([(x, H2 - 5), (x, H2)], fill=(int(0x25 + (0x7c - 0x25) * tt),
                                          int(0xc2 + (0xf3 - 0xc2) * tt),
                                          int(0xe8 + (0xc0 - 0xe8) * tt)))

gb, bb = bust("glitch", 500), bust("blackhole", 520)
w.paste(gb, (24, H2 - 5 - gb.height), gb)
w.paste(bb, (W2 - bb.width - 16, H2 - 5 - bb.height), bb)

cx2 = W2 // 2
d2.text((cx2, 132), "繁體中文小說・全七章", font=f(MONO, 24), fill=CY, anchor="mm")
d2.text((cx2, 214), "格莉奇與黑洞先生", font=f(SERIF, 72), fill=TEXT, anchor="mm")
d2.text((cx2, 296), "她說，我要記住每一個來的人，我保證。", font=f(SERIF_R, 27), fill=MUTED, anchor="mm")
d2.text((cx2, 370), "她記得六個。", font=f(SERIF, 40), fill=MINT, anchor="mm")

w.save(IMG / "og-wide.jpg", quality=88, optimize=True)
print(f"  og-wide.jpg 1600x520  {(IMG / 'og-wide.jpg').stat().st_size // 1024} KB")

# favicon：格莉奇的頭，方形去背 PNG
gg = Image.open(ROOT / "art/sprite-glitch.png").convert("RGBA")
gg = gg.crop(gg.getchannel("A").getbbox())
head = gg.crop((0, 0, gg.width, int(gg.width * 0.92)))
for size in (32, 180):
    o = head.resize((size, size), Image.LANCZOS)
    o.save(IMG / f"icon-{size}.png")
print("  icon-32.png / icon-180.png")
