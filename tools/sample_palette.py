#!/usr/bin/env python3
"""從立繪取樣每個角色的固有色，產生 design/palette.json 的候選。

**顏色的正典是圖，不是文字。** 只有格莉奇與黑洞先生有寫死的 hex
（ai-brain-site/persona.json 的 characters.*.identity），其餘五個人的顏色
只存在 art/sprite-*.png 裡。所以這裡直接量圖。

做法：丟掉透明與接近透明的像素（立繪是去背的，背景會把平均值拉走），
其餘量化成 N 色，照佔比排序。**佔比要一起輸出**：模型平均出來的假色佔比
都很低，看得出來。

**面積跟彩度要一起看。** 只照面積排，格莉奇的髮色會被淺色帽 T 吃掉；
只照彩度排，一兩個像素的雜點會排第一。所以兩份都取，合起來去重。

用法：
    python3 tools/sample_palette.py            # 全部角色，只印不寫
    python3 tools/sample_palette.py --write    # 寫進 design/palette.json 的 cast.*.art
    python3 tools/sample_palette.py --who 格莉奇
"""
import argparse, colorsys, json, pathlib, re, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPRITE = {"格莉奇": "sprite-glitch.png", "黑洞先生": "sprite-blackhole.png",
          "貓草": "sprite-catgrass.png", "鐵塔": "sprite-tower.png",
          "0x": "sprite-zerox.png", "斑比": "sprite-bambi.png",
          "諾亞": "sprite-noah.png"}


# 佔比低於這個的顏色不收：那多半是量化平均出來的、圖上找不到的假色。
MIN_SHARE = 0.005


def head(path, alpha_min=200, top=0.20, n=2):
    """只取非透明區塊上緣 20% 的顏色。**站姿立繪的髮色量全身量不到**：
    頭佔的面積小，格莉奇的薄荷髮色會被淺色帽 T 蓋過去，面積與彩度都排不進去。"""
    im = Image.open(path).convert("RGBA")
    bbox = im.getchannel("A").point(lambda v: 255 if v >= alpha_min else 0).getbbox()
    if not bbox:
        return []
    x0, y0, x1, y1 = bbox
    crop = im.crop((x0, y0, x1, y0 + max(1, int((y1 - y0) * top))))
    tmp = pathlib.Path("/tmp/_head.png")
    crop.save(tmp)
    return sample(tmp, n=n, alpha_min=alpha_min, buckets=16)


def sample(path, n=6, alpha_min=200, buckets=48):
    """回傳 [(hex, 佔比, 彩度)]，面積前 n 與彩度前 n 合併去重。"""
    im = Image.open(path).convert("RGBA")
    px = [(r, g, b) for r, g, b, a in im.getdata() if a >= alpha_min]
    if not px:
        return []
    flat = Image.new("RGB", (len(px), 1))
    flat.putdata(px)
    q = flat.quantize(colors=buckets, method=Image.MEDIANCUT)
    pal, total, cols = q.getpalette(), len(px), []
    for count, idx in q.getcolors():
        r, g, b = pal[idx * 3:idx * 3 + 3]
        s = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[1]
        cols.append({"hex": f"#{r:02x}{g:02x}{b:02x}",
                     "share": round(count / total, 4), "sat": round(s, 2)})
    keep = [c for c in cols if c["share"] >= MIN_SHARE]
    by_area = sorted(keep, key=lambda c: -c["share"])[:n]
    by_sat = sorted(keep, key=lambda c: -c["sat"])[:n]
    out, seen = [], set()
    for c in by_area + by_sat:
        if c["hex"] not in seen:
            seen.add(c["hex"]); out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--who")
    ap.add_argument("--write", action="store_true",
                    help="寫回 design/palette.json 的 cast.*.art（其餘欄位不動）")
    a = ap.parse_args()
    PAL = ROOT / "design/palette.json"
    doc = json.loads(PAL.read_text(encoding="utf-8")) if PAL.exists() else {"cast": {}}
    for who, f in SPRITE.items():
        if a.who and who != a.who:
            continue
        p = ROOT / "art" / f
        if not p.exists():
            print(f"{who}：找不到 {p}", file=sys.stderr)
            continue
        rows = sample(p, a.n)
        hd = head(p)
        for c in hd:
            c["region"] = "頭部"
        seen = {c["hex"] for c in rows}
        rows += [c for c in hd if c["hex"] not in seen]
        # 一個角色八色是上限。再多就不是色卡了，看的人挑不出主色。
        rows = rows[:8]
        print(f"\n{who}　{f}")
        for c in rows:
            print(f"  {c['hex']}  佔比 {c['share']*100:5.1f}%  彩度 {c['sat']:.2f}")
        if a.write:
            doc.setdefault("cast", {}).setdefault(who, {})["sprite"] = f"art/{f}"
            doc["cast"][who]["art"] = rows
    if a.write:
        PAL.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n寫好 {PAL}")


if __name__ == "__main__":
    main()
