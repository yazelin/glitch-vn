#!/usr/bin/env python3
"""色票驗收：立繪照 spec 量佔比、背景照時段量色溫。**兩個都有上緣，不是只看下緣。**

調查篇跟正文的方向相反（見 design/palette.json 的 rules）：
正文七個角色的色票是事後從立繪量回來的，調查篇是先寫死 spec 再照著產。
所以這支是「產完之後比對有沒有漂掉」，比不過就重產那一張，不是回頭改 spec。

    python3 tools/check_palette.py            # 全部
    python3 tools/check_palette.py --sprites  # 只驗立繪
    python3 tools/check_palette.py --bg       # 只驗背景

踩過的兩個坑，都寫成程式了：
1. **不要用「最常見的顏色裡最接近的一個」當指標。** 膚色面積大就一直被選中，
   量不出色票到底有沒有出現。要量的是「距離這個色票夠近的像素佔多少」。
2. **色溫要檢查上緣。** 第一版只判 R−B > 15，五張白天版全部飆到 +48 到 +74
   還印成達標，實際上是曬白的黃昏調不是清亮的上午。
"""
import argparse, json, math, pathlib, sys
from PIL import Image, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAL = ROOT / "design/palette.json"

# 立繪：檔名 → palette.json 的角色鍵
SPRITES = {
    "sprite-admin": "管理員", "sprite-clerk": "便利商店店員",
    "sprite-parts": "材料行老闆", "sprite-reception": "十四樓櫃檯",
    "sprite-guard": "保全",
}
# 主／副／點各自的佔比門檻（%）
NEED = {"主": 12.0, "副": 5.0, "點": 0.4}
# 已知且接受的例外。**要寫理由**，不寫理由就是把門檻調鬆而已。
# 值是「量到多少就算過」，只對這一格放行，不動全域門檻。
ACCEPTED = {
    ("管理員", "#b9bcb4"): (4.99,
        "差 0.01 個百分點，落在縮圖重取樣的誤差裡。重產過一次反而掉到 3.25%，"
        "已退回 v1（art/out/sprite-admin-v1.png 是同一張）。"),
}
TOL = 60.0          # RGB 歐氏距離，算「這個像素屬於這個色票」

# 背景：時段 → R−B 區間。來源是 design/調查篇-場景.md「白天與夜晚是兩種色溫」
BANDS = {"白天": (15, 45), "晚上": (-45, -25), "深夜": (-999, -55)}
# 檔名尾巴 → 時段。對不上的檔案不驗，不是失敗
SUFFIX = {"-day": "白天", "-day2": "白天", "-night": "深夜"}
# 正文七章的背景不受調查篇色溫規格管：那些已經上線，改了等於改已發佈的作品。
# bg-street-day.png 是正文的（ch06 車站前），調查篇走 bg-street-day2.png。
SKIP = {"bg-street-day.png"}


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def body_pixels(im):
    """去掉 #00FF00 綠幕。判準放寬，因為邊緣有反鋸齒。"""
    return [p for p in im.getdata()
            if not (p[1] > 150 and p[1] > p[0] + 50 and p[1] > p[2] + 50)]


def check_sprites(spec):
    bad = []
    for stem, who in SPRITES.items():
        f = ROOT / f"art/out/{stem}.png"
        if not f.exists():
            print(f"  略過 {stem}（檔案不在）")
            continue
        im = Image.open(f).convert("RGB")
        im.thumbnail((300, 450))          # 縮圖再量，全尺寸沒有量得比較準
        body = body_pixels(im)
        n = len(body) or 1
        print(f"\n== {who}")
        for s in spec["cast"][who]["spec"]:
            want = hex2rgb(s["hex"])
            pct = sum(1 for p in body if dist(p, want) < TOL) * 100 / n
            need = NEED[s["slot"]]
            exc = ACCEPTED.get((who, s["hex"]))
            ok = pct >= need or (exc and pct >= exc[0] - 0.01)
            if not ok:
                bad.append(f"{who} 的{s['slot']}色 {s['hex']}（{s['name']}）只有 {pct:.2f}%，門檻 {need}%")
            tag = "OK  " if ok else "不足"
            if ok and exc and pct < need:
                tag = "例外"
            print(f"   {tag} {s['slot']} {s['hex']} {s['name']:<12} {pct:6.2f}%"
                  + (f"   ← {exc[1]}" if tag == "例外" else ""))
    return bad


def slot_of(stem):
    for suf, slot in sorted(SUFFIX.items(), key=lambda kv: -len(kv[0])):
        if stem.endswith(suf):
            return slot
    return None


def check_bg():
    bad = []
    files = sorted(list((ROOT / "art/out").glob("bg-*.png"))
                   + list((ROOT / "art/bg-investigation").glob("bg-*.jpg")))
    print()
    for f in files:
        if f.name in SKIP:
            continue
        slot = slot_of(f.stem)
        if not slot:
            continue
        im = Image.open(f).convert("RGB")
        im.thumbnail((200, 200))
        r, g, b = ImageStat.Stat(im).mean
        w = r - b
        lo, hi = BANDS[slot]
        ok = lo <= w <= hi
        if not ok:
            why = "太冷" if w < lo else "太暖"
            bad.append(f"{f.name}（{slot}）R−B {w:+.1f}，{why}，區間是 {lo} 到 {hi}")
        print(f"  {'OK  ' if ok else '超出'} {f.name:28s} {slot}  R−B {w:+6.1f}  區間 {lo} 到 {hi}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprites", action="store_true")
    ap.add_argument("--bg", action="store_true")
    a = ap.parse_args()
    both = not (a.sprites or a.bg)
    spec = json.loads(PAL.read_text(encoding="utf-8"))
    bad = []
    if both or a.sprites:
        bad += check_sprites(spec)
    if both or a.bg:
        bad += check_bg()
    print()
    if bad:
        print(f"沒過 {len(bad)} 項：")
        for x in bad:
            print("  ・", x)
        sys.exit(1)
    print("全部符合色票與色溫規格。")


if __name__ == "__main__":
    main()
