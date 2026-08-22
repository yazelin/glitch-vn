#!/usr/bin/env python3
"""把劇情裡的字疊到空白的本子／螢幕底圖上。

**不要叫生圖模型寫這些字。** 守則本第一頁是全書的核心畫面，上面是六個 @ID
加一句中文，模型寫出來一定是亂碼，而且改一個字就要重生一張。
所以底圖只生「完全空白的本子」，字在這裡用 PIL 疊——字對得上劇情，之後要改也免費。

**版面用偵測的，不要寫死座標。** 四張底圖的構圖都不一樣（本子的位置、螢幕的角度），
寫死的結果是最後一行衝出頁面右緣被切掉。這裡找出畫面裡最大的那塊平坦亮區
（＝紙頁或螢幕），再把字排進去，字級自動縮到最長的一行放得下為止。

手寫感用楷書（AR PL UKai TW）加每一行的微小旋轉與位移。整齊的字看起來像印刷。

用法：python3 tools/gen_page.py
"""
import pathlib, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art/page"; OUT.mkdir(parents=True, exist_ok=True)
KAI = "/usr/share/fonts/truetype/arphic/ukai.ttc"

IDS = ["@CatGrass_80", "@Tower_Manager", "@Null_0x99",
       "@Bambi_Draft3", "@Radio_Noah", "@考完就刪"]
PAGES = {
    # (底圖, 行, 墨色, 只用亮區的右半邊, 模糊)
    "page-rulebook-1004": ("plate-rulebook", ["八月二十二日"] + IDS +
                           ["還有一個。不要問他是誰。"], (34, 30, 46), True, 0),
    "page-rulebook-final": ("plate-rulebook", ["八月二十三日"] + IDS +
                            ["還有一個。他就在客廳。", "去問他今天累不累。"],
                            (34, 30, 46), True, 0),
    "page-sample": ("plate-sample", ["@Lorem_Ipsum", "@Sample_User", "@Demo_Name",
                                     "@Your_Name_Here", "@Placeholder", "@Example_01",
                                     "@Text_Goes_Here"], (52, 48, 64), True, 0),
    # 兩年前的串流截圖：三百六十的畫質。先疊字，再降採樣、再模糊——
    # 要的效果是「數得出七行、可是第七行讀不出來」，那是第四章的關鍵。
    # **這張是劇透的關鍵。** 第四章的重點是「數得出七行、第七行讀不出來，
    # 只看得出開頭像一個 @」。糊得不夠就等於直接把 @Zero_Point 寫在螢幕上，
    # 第四章到第七章之間的懸念全部作廢。
    "page-day5": ("plate-screen", ["開台第五天"] + IDS + ["@Zero_Point"],
                  (232, 238, 248), False, 7.0),
}


def bright_box(img, screen=False):
    """找出畫面裡最大的一塊平坦亮區＝紙頁或螢幕。回傳它的外接框。

    **螢幕要另外判。** 亮的藍色螢幕飽和度很高，會被「低飽和」那個條件排除掉，
    結果框到檯燈或桌面，字級被壓到看不見。
    """
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    if screen:
        m = (a[..., 2] - a[..., 0] > 18) & (lum > 55)
    else:
        m = (lum > lum.max() * 0.62) & (sat < 90)
    m = ndimage.binary_opening(m, np.ones((9, 9)))
    lab, n = ndimage.label(m)
    if not n:
        h, w = lum.shape
        return int(w * .5), int(h * .2), int(w * .9), int(h * .8)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    ys, xs = np.where(lab == int(np.argmax(sizes)) + 1)
    return xs.min(), ys.min(), xs.max(), ys.max()


def render(name, plate, lines, ink, right_half, blur):  # right_half 已停用
    src = ROOT / "art/out" / f"{plate}.png"
    if not src.exists():
        print(f"  ★ 缺底圖 {plate}"); return
    img = Image.open(src).convert("RGB")
    x0, y0, x1, y1 = bright_box(img, screen=(plate == "plate-screen"))
    # **用整個攤開的寬度，不要只用右半頁。** 只用右頁的話欄寬剩一半，
    # 字級被寬度卡死，讀不出來就白做了。
    pad = int((x1 - x0) * 0.13)
    x0, x1 = x0 + pad, x1 - pad
    y0, y1 = y0 + int((y1 - y0) * 0.06), y1 - int((y1 - y0) * 0.08)
    # **文字要留在畫面上半部。** 對話框的漸層會蓋掉下面將近一半，
    # 而這幾張的重點就是最後一行——被蓋住等於這張圖白做。
    y1 = min(y1, int(img.height * 0.46))
    colw, colh = x1 - x0, y1 - y0
    step = colh / len(lines)

    # 字級自動縮到最長的一行放得下，而且不超過行高
    size = int(step * 0.78)   # 行距吃緊，字級盡量吃滿一行
    while size > 8:
        f = ImageFont.truetype(KAI, size, index=0)
        if max(f.getbbox(t)[2] for t in lines) <= colw:
            break
        size -= 2
    f = ImageFont.truetype(KAI, size, index=0)

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rnd = random.Random(name)           # 固定亂數，重跑結果一樣
    for i, t in enumerate(lines):
        dx, dy = rnd.uniform(-5, 5), rnd.uniform(-3, 3)
        tile = Image.new("RGBA", (colw + 120, int(step) + 60), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((30, 12), t, font=f, fill=ink + (240,))
        tile = tile.rotate(rnd.uniform(-1.0, 1.0), resample=Image.BICUBIC,
                           center=(0, tile.height // 2))
        layer.alpha_composite(tile, (int(x0 + dx - 30), int(y0 + i * step + dy - 12)))
    if blur:
        # 先降採樣再放回來，才像低碼率的串流截圖；只糊不降採樣看起來只是失焦
        w, h = layer.size
        layer = layer.resize((w // 10, h // 10), Image.BILINEAR).resize((w, h), Image.BILINEAR)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    p = OUT / f"{name}.png"; img.save(p)
    print(f"  {name:22s} {len(lines)} 行　字級 {size}　欄寬 {colw}　→ {p.name}")


# 道具上的字。**這條路跟本子那條不一樣**：道具要保留透明背景（render 會轉成
# 不透明），而且範圍要用物件本身的外框，不是畫面裡的亮區。
PROPS = {
    # 旁白唸「品項那一欄寫著：天線用同軸線 3M」，紙上空白的話畫面在跟台詞打架
    "prop-receipt": ["電子材料行", "————", "天線用同軸線 3M",
                     "$180", "————", "謝謝惠顧"],
}


def render_prop(name, lines, ink=(74, 66, 80)):
    src = ROOT / "art/face" / f"{name}.png"
    if not src.exists():
        print(f"  ★ 缺去背圖 {name}"); return
    im = Image.open(src).convert("RGBA")
    x0, y0, x1, y1 = im.getbbox()               # 用物件本身的外框
    pad_x = int((x1 - x0) * 0.16)
    pad_y = int((y1 - y0) * 0.14)
    x0, x1 = x0 + pad_x, x1 - pad_x
    y0, y1 = y0 + pad_y, y1 - pad_y
    colw, colh = x1 - x0, y1 - y0
    step = colh / len(lines)
    size = int(step * 0.66)
    while size > 8:
        f = ImageFont.truetype(KAI, size, index=0)
        if max(f.getbbox(t)[2] for t in lines) <= colw:
            break
        size -= 2
    f = ImageFont.truetype(KAI, size, index=0)
    d = ImageDraw.Draw(im)
    rnd = random.Random(name)
    for i, t in enumerate(lines):
        w = f.getbbox(t)[2]
        d.text((x0 + (colw - w) / 2 + rnd.uniform(-3, 3),
                y0 + i * step + rnd.uniform(-2, 2)), t, font=f, fill=ink + (232,))
    out = ROOT / "art/face-text"; out.mkdir(exist_ok=True)
    im.save(out / f"{name}.png")
    print(f"  {name:22s} {len(lines)} 行　字級 {size}　寬 {colw}　→ art/face-text/")


def main():
    for name, (plate, lines, ink, rh, blur) in PAGES.items():
        render(name, plate, lines, ink, rh, blur)
    for name, lines in PROPS.items():
        render_prop(name, lines)


if __name__ == "__main__":
    main()
