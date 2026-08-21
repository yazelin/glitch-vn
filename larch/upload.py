#!/usr/bin/env python3
"""把素材上傳到小說版專案，並回寫 larch/assets.json。

背景轉成 1920x1080 的 JPEG（原檔 1536x1024 是 3:2，播放器是 16:9，要裁）。
立繪維持透明 PNG。
"""
import base64, json, pathlib, sys, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
BASE = f"https://larch.yapiflow.com/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
STORE = ROOT / "larch/assets.json"


def put_media(name, raw, mime):
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        BASE + "/media",
        json.dumps({"base64": base64.b64encode(raw).decode(),
                    "name": name, "mimeType": mime}).encode(),
        H, method="POST"), timeout=240))
    return r["asset"]["url"]


def bg(path, key, tmp):
    """3:2 的原圖裁成 16:9。裁上下不裁左右——構圖的重點都在中間帶。"""
    im = Image.open(path).convert("RGB")
    w = im.width
    h = int(w * 9 / 16)
    top = (im.height - h) // 2
    im = im.crop((0, top, w, top + h)).resize((1920, 1080), Image.LANCZOS)
    im.save(tmp, quality=88, optimize=True)
    return put_media(f"{key}.jpg", pathlib.Path(tmp).read_bytes(), "image/jpeg")


def main():
    assets = json.loads(STORE.read_text()) if STORE.exists() else {}
    tmp = "/tmp/_bg.jpg"
    for p in sorted((ROOT / "art/out").glob("bg-*.png")):
        k = p.stem
        if k in assets and "--force" not in sys.argv:
            print(f"  跳過 {k}（已上傳）"); continue
        assets[k] = bg(p, k, tmp)
        print(f"  背景 {k}")
    for p in sorted((ROOT / "art/avatar").glob("avatar-*.png")):
        k = p.stem
        if k in assets and "--force" not in sys.argv:
            print(f"  跳過 {k}"); continue
        assets[k] = put_media(f"{k}.png", p.read_bytes(), "image/png")
        print(f"  頭像 {k}")
    for p in sorted((ROOT / "art").glob("sprite-*.png")):
        k = p.stem
        if k in assets:
            print(f"  跳過 {k}（已上傳）"); continue
        assets[k] = put_media(f"{k}.png", p.read_bytes(), "image/png")
        print(f"  立繪 {k}")
    STORE.write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(assets)} 個素材 → {STORE}")


if __name__ == "__main__":
    main()
