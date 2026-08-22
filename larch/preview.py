#!/usr/bin/env python3
"""本地預覽：把一張卡合成成播放器大概會長的樣子。

**播放器要 Google 登入才玩得到，所以我看不到自己做的東西。**
與其一直猜位置與大小，不如在本機照同一組數字合成一張 1920x1080，
自己看過再推上去。這不是像素級精準，可是「頭貼太低」「立繪太小」這種
問題一眼就看得出來。

用法：python3 larch/preview.py <章 id> <卡片index> [out.jpg]
      python3 larch/preview.py <卡片index> [out.jpg]      （預設第一章）
"""
import json, pathlib, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import PROJ, BASE, H, ROOT, STORE, api  # noqa: E402

K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
W, H = 1920, 1080
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
TC = 3
# slot 對應到畫面的水平位置（五個站位）
SLOT_X = {"farLeft": .12, "left": .28, "center": .5, "right": .72, "farRight": .88}
CACHE = ROOT / "larch/.cache"; CACHE.mkdir(exist_ok=True)


def grab(url):
    f = CACHE / url.rsplit("/", 1)[-1]
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
    return Image.open(f)


def main():
    argv = sys.argv[1:]
    bid = argv.pop(0) if argv and not argv[0].isdigit() else None
    idx = int(argv[0]) if argv else 8
    out = argv[1] if len(argv) > 1 else "/tmp/preview.jpg"
    p = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://larch.yapiflow.com/api/agent/projects/{PROJ}",
        headers={"Authorization": f"Bearer {K}"}), timeout=180))
    board = next((b for b in p["boards"] if b["id"] == bid), None) if bid \
        else p["boards"][0]
    assert board, f"沒有這一章：{bid}　有的是 {[b['id'] for b in p['boards']]}"
    nodes = board["nodes"]
    d = nodes[idx]["data"]
    # 背景取最近一張場景卡的
    bgurl = next((n["data"]["background"] for n in reversed(nodes[:idx + 1])
                  if n["data"].get("background")), None)
    canvas = grab(bgurl).convert("RGB").resize((W, H), Image.LANCZOS) if bgurl \
        else Image.new("RGB", (W, H), (4, 8, 12))

    for a in (d.get("stage") or {}).get("actors", []):
        im = grab(a["url"]).convert("RGBA")
        h = int(H * a.get("scale", 1))
        im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        x = int(W * SLOT_X.get(a.get("slot", "center"), .5) - im.width / 2)
        canvas.paste(im.convert("RGB"), (x, H - im.height), im)

    # 對話框（照 settings.dialogueUi 的值畫）
    ui = p["settings"]["dialogueUi"]
    # **對話框要抓高一點。** presentation:"gradient" 會往上暈開，
    # 實際遮到的範圍比面板本身高很多；我抓 30% 的時候誤判過一次。
    panel_h = int(H * .45)
    ov = Image.new("RGBA", (W, panel_h), (4, 8, 12, int(255 * ui["panelOpacity"])))
    canvas.paste(Image.alpha_composite(
        canvas.crop((0, H - panel_h, W, H)).convert("RGBA"), ov).convert("RGB"),
        (0, H - panel_h))
    dr = ImageDraw.Draw(canvas)
    dr.line([(0, H - panel_h), (W, H - panel_h)], fill=ui["borderColor"], width=2)
    y = H - panel_h + 34
    sp = d.get("speaker")
    if sp:
        dr.text((120, y), sp, font=ImageFont.truetype(SERIF_B, ui["nameFontSize"] * 2, index=TC),
                fill=ui["speakerColor"])
        y += 54
    lines = [l["text"] for l in d.get("dialogueLines", [])] or (d.get("text") or "").split("\n")
    f = ImageFont.truetype(SERIF, int(ui["fontSize"] * 1.75), index=TC)
    for t in lines[:4]:
        dr.text((120, y), t[:38], font=f, fill=ui["textColor"])
        y += 60
    canvas.save(out, quality=86)
    print(f"卡 {idx}　{d.get('type','dialogue')}　speaker={sp!r}　"
          f"actors={[a['name'] for a in (d.get('stage') or {}).get('actors', [])]}")
    print(f"→ {out}")


if __name__ == "__main__":
    main()
