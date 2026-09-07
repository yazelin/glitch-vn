#!/usr/bin/env python3
"""格莉奇只在螢幕上（design/調查篇.md 四「看得到，見不到」）。這支把她的立繪合成到五種螢幕道具上，
推送層在她講話（remote）的卡把對應的道具掛上舞台：
  notice   一樓公告螢幕        standee  便利商店／手辦店的紙板立牌
  billboard 車站前看板、燈箱   tv       材料行的舊電視
  phone    手機直播畫面
立繪從正文專案的網址抓（larch/assets.json），不進 repo；產出 art/screens/screen-*.png（透明）。
"""
import json, pathlib, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art/screens"; OUT.mkdir(exist_ok=True)
A = json.load(open(ROOT / "larch/assets.json"))
CACHE = pathlib.Path("/tmp/glitch-sprites"); CACHE.mkdir(exist_ok=True)
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def sprite(key):
    p = CACHE / f"{key}.bin"
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(A[key], headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
    im = Image.open(p).convert("RGBA")
    return im.crop(im.getbbox())


def fit(im, w, h, top=0.0):
    """把立繪放進 w×h 的框，寬度優先貼滿，超出的往下裁（螢幕只看得到上半身）。"""
    s = w / im.width
    r = im.resize((w, int(im.height * s)), Image.LANCZOS)
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    box.paste(r, (0, int(-r.height * top)), r)
    return box


def rounded(w, h, r, fill):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill)
    return im


def scanlines(w, h, alpha=28):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in range(0, h, 4):
        d.line((0, y, w, y), fill=(0, 0, 0, alpha))
    return im


def screen_panel(w, h, bezel, radius, body, glass, who, top, tint):
    """通用：機身 → 玻璃 → 立繪 → 掃描線 → 反光"""
    im = rounded(w, h, radius, body)
    g = rounded(w - 2 * bezel, h - 2 * bezel, max(2, radius // 2), glass)
    im.paste(g, (bezel, bezel), g)
    pic = fit(who, w - 2 * bezel, h - 2 * bezel, top)
    im.paste(pic, (bezel, bezel), pic)
    t = Image.new("RGBA", (w - 2 * bezel, h - 2 * bezel), tint); im.paste(t, (bezel, bezel), t)
    im.paste(scanlines(w - 2 * bezel, h - 2 * bezel), (bezel, bezel), scanlines(w - 2 * bezel, h - 2 * bezel))
    hl = Image.new("RGBA", (w - 2 * bezel, h - 2 * bezel), (0, 0, 0, 0))
    ImageDraw.Draw(hl).polygon([(0, 0), (int(w * .45), 0), (0, int(h * .5))], fill=(255, 255, 255, 22))
    im.paste(hl, (bezel, bezel), hl)
    return im


def text_line(w, txt, size, color):
    f = ImageFont.truetype(FONT, size)
    im = Image.new("RGBA", (w, int(size * 1.6)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    tw = d.textlength(txt, font=f)
    d.text(((w - tw) / 2, size * .2), txt, font=f, fill=color)
    return im


happy, plain = sprite("glitch-happy"), sprite("glitch-plain")

# 1. 公告螢幕（一樓）：橫的壁掛 LCD，暗色機身，藍一點
im = screen_panel(900, 560, 22, 18, (28, 30, 34, 255), (12, 18, 28, 255), happy, .04, (40, 90, 140, 40))
im.save(OUT / "screen-notice.png")

# 2. 紙板立牌（便利商店、手辦店）：全身，白邊，底下一個紙板腳
w = 520; s = w / happy.width; body = happy.resize((w, int(happy.height * s)), Image.LANCZOS)
pad = 26; card = Image.new("RGBA", (w + 2 * pad, body.height + 2 * pad + 40), (0, 0, 0, 0))
edge = Image.new("RGBA", body.size, (0, 0, 0, 0)); edge.paste((246, 244, 238, 255), None, body.split()[3])
edge = edge.filter(ImageFilter.MaxFilter(21))          # 白色刀模邊
card.paste(edge, (pad, pad), edge); card.paste(body, (pad, pad), body)
d = ImageDraw.Draw(card)
d.polygon([(w * .3, body.height + pad - 30), (w * .78, body.height + pad - 30), (w * .9, body.height + pad + 36), (w * .18, body.height + pad + 36)],
          fill=(150, 118, 78, 255))
card.save(OUT / "screen-standee.png")

# 3. 看板／燈箱（車站前、公車站、捷運出口）：寬幅，字幕「我會記得你們的」，暖白邊光
im = screen_panel(1200, 560, 14, 8, (60, 60, 64, 255), (18, 16, 30, 255), happy, .06, (120, 60, 160, 36))
cap = text_line(1200, "我會記得你們的", 56, (240, 240, 245, 235))
im.paste(cap, (0, 560 - 14 - cap.height - 10), cap)
im.save(OUT / "screen-billboard.png")

# 4. 舊電視（材料行）：厚機身、圓角大、偏灰綠、掃描線重
im = screen_panel(760, 620, 46, 60, (70, 66, 60, 255), (22, 26, 22, 255), plain, .05, (60, 90, 60, 60))
big = scanlines(760 - 92, 620 - 92, 55); im.paste(big, (46, 46), big)
im.save(OUT / "screen-tv.png")

# 5. 手機（直播）：直的，圓角大，右上角紅點 LIVE
im = screen_panel(520, 1060, 18, 70, (20, 20, 22, 255), (14, 14, 20, 255), happy, .0, (30, 60, 110, 30))
d = ImageDraw.Draw(im)
d.rounded_rectangle((40, 44, 150, 84), 20, fill=(200, 30, 40, 235)); d.ellipse((54, 56, 70, 72), fill=(255, 255, 255, 255))
f = ImageFont.truetype(FONT, 26); d.text((80, 50), "LIVE", font=f, fill=(255, 255, 255, 255))
im.save(OUT / "screen-phone.png")
# 舞台上的演員以圖的底邊落地。壁掛的螢幕、看板、電視、手機底下補一段透明，畫面才會掛在牆的高度，不是放在地上
PAD = {"screen-notice.png": 560, "screen-billboard.png": 520, "screen-tv.png": 420, "screen-phone.png": 220}
for name, pad in PAD.items():
    im = Image.open(OUT / name).convert("RGBA")
    out = Image.new("RGBA", (im.width, im.height + pad), (0, 0, 0, 0)); out.paste(im, (0, 0), im); out.save(OUT / name)
for f_ in sorted(OUT.glob("screen-*.png")):
    print(f_.name, Image.open(f_).size)
