#!/usr/bin/env python3
"""調查板拍立得縮圖的 atlas：12 個地點 × 白天／晚上／深夜，一張 webp 拼版＋座標表。

原本每格拍立得直接載整張 1920×1080 的場景圖（三十幾張、每張幾百 KB）只為了顯示一張 4:3 的小縮圖，
開板要等很久（2026-09-17 作者要求改 atlas）。這裡切成 240×180（4:3，中央裁切）拼成一張。

    python3 tools/make_board_atlas.py     → art/board-atlas.webp、art/board-atlas.json

json：{"cols": n, "rows": m, "w": 240, "h": 180, "map": {loc: {"day": [col,row], "evening": [...], "night": [...]}}}
board.html 用 background-size/position 取格；push.py 灌網址（/*@@ATLAS@@*/）；patch_live 換線上。
時段的代替順序跟 push.py pick_bg 一樣：晚上沒圖用白天，深夜沒圖用晚上（再沒有用白天）。
"""
import json, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "art/bg-investigation"
W, H = 240, 180
# 地點代號跟 board.html SPOTS 的 id 一致；檔名主幹照 build.py 的 BG 表
LOCS = ["lobby", "roof", "street", "studio", "booth", "tower14", "store", "parts", "busstop", "metro", "laundry", "figure"]
DAY = {"lobby": "bg-lobby-day", "roof": "bg-roof-day", "street": "bg-street-day2", "studio": "bg-bambi-studio-day",
       "booth": "bg-booth-hall", "tower14": "bg-tower14-day", "store": "bg-store-day", "parts": "bg-parts-day",
       "busstop": "bg-busstop-day", "metro": "bg-metro-day", "laundry": "bg-laundry-day", "figure": "bg-figure-day"}
EVE = {loc: f"bg-{loc}-evening" for loc in LOCS} | {"studio": "bg-studio-evening", "booth": "bg-booth-hall"}
NIGHT = {loc: f"bg-{loc}-night" for loc in LOCS} | {"lobby": "bg-lobby-evening", "roof": "bg-roof-evening", "studio": "bg-studio-evening",
                                                    "booth": "bg-booth-hall", "parts": "bg-parts", "busstop": "bg-busstop",
                                                    "metro": "bg-metro", "laundry": "bg-laundry", "figure": "bg-figure"}


def find(stem):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = SRC / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def thumb(p):
    im = Image.open(p).convert("RGB"); w, h = im.size
    s = max(W / w, H / h); im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    x = (im.width - W) // 2; y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def main():
    cells = {}          # 檔案 → 格子（同一張圖只放一格）
    order = []
    m = {}
    for loc in LOCS:
        d = find(DAY[loc]); e = find(EVE[loc]) or d; n = find(NIGHT[loc]) or e or d
        m[loc] = {}
        for k, p in (("day", d), ("evening", e), ("night", n)):
            if p is None:
                print("  ★ 沒圖：", loc, k); continue
            if p not in cells:
                cells[p] = len(order); order.append(p)
            m[loc][k] = cells[p]
    cols = 6; rows = (len(order) + cols - 1) // cols
    atlas = Image.new("RGB", (cols * W, rows * H), (17, 17, 17))
    for i, p in enumerate(order):
        atlas.paste(thumb(p), ((i % cols) * W, (i // cols) * H))
    out = ROOT / "art/board-atlas.webp"; atlas.save(out, "WEBP", quality=80)
    for loc in m:
        for k, i in m[loc].items():
            m[loc][k] = [i % cols, i // cols]
    (ROOT / "art/board-atlas.json").write_text(json.dumps({"cols": cols, "rows": rows, "w": W, "h": H, "map": m}, ensure_ascii=False), encoding="utf-8")
    print(f"{len(order)} 張縮圖 → {out.relative_to(ROOT)} {atlas.size} {out.stat().st_size // 1024} KB；座標表 art/board-atlas.json")


if __name__ == "__main__":
    main()
