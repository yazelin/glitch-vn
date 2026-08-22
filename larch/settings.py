#!/usr/bin/env python3
"""專案設定：標題畫面、對話框樣式、游標、封面。

**這些不是裝飾。** 市集上那兩個作品跟我第一版最大的差別，一半在這裡：
沒有 titleScreen 就沒有開始畫面，沒有 dialogueUi 就是預設的灰盒子。

欄位是從市集的專案 JSON 挖出來的（GET /api/marketplace/{id}?play=1，不用登入）。
"""
import base64, json, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
B = f"https://larch.yapiflow.com/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def api(d=None, m="GET", path=""):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        B + path, json.dumps(d).encode() if d else None, H, method=m), timeout=300))


def main():
    assets = json.loads((ROOT / "larch/assets.json").read_text())
    cover = assets.get("cover")
    if not cover:
        raw = (ROOT / "docs/img/og.jpg").read_bytes()
        cover = api({"name": "cover.jpg", "mimeType": "image/jpeg", "category": "scene",
                     "base64": base64.b64encode(raw).decode()}, "POST", "/media")["asset"]["url"]
        assets["cover"] = cover
        (ROOT / "larch/assets.json").write_text(
            json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
        print("  封面上傳完成")

    p = api()
    s = dict(p.get("settings") or {})
    s.update({
        "resolution": {"width": 1920, "height": 1080},
        "stageFit": "auto",
        "keepActorsInFrame": False,
        "textSpeed": 30,
        "typingEffect": True,
        "autoAdvanceDelay": 1800,
        "showVersionBadge": True,
        "showRpgHud": False,
        "projectThumbnail": cover,
        "titleScreenEnabled": True,
        "titleCoverShade": 0.62,
        "titleCoverPositionX": 50,
        "titleCoverPositionY": 46,
        "titleScreen": {"frame": "none", "layers": [
            {"id": "eyebrow", "kind": "text", "role": "eyebrow",
             "x": 6, "y": 16, "size": 1, "align": "left", "width": 40},
            {"id": "name", "kind": "text", "role": "title",
             "x": 6, "y": 24, "size": 6, "align": "left", "width": 70},
            {"id": "description", "kind": "text", "role": "description",
             "x": 6, "y": 42, "size": 1.15, "align": "left", "width": 44},
        ]},
        # 配色跟小說站同一套（ai-brain-site 的 --bg #04080c、--cy #25c2e8、--mint #7cf3c0）
        "dialogueUi": {"preset": "custom", "presentation": "gradient",
                       "fontFamily": "serif", "fontSize": 25, "nameFontSize": 18,
                       "textColor": "#dfe8ec", "speakerColor": "#25c2e8",
                       "accentColor": "#7cf3c0", "borderColor": "#25c2e8",
                       "panelColor": "#04080c", "panelOpacity": 0.82,
                       "panelWidth": 100, "panelPadding": 30, "panelOffset": 0,
                       "borderRadius": 0, "backdropBlur": 0},
        "cgGalleryEnabled": True,
        "cgGallerySource": "picked",
        "cgGalleryItems": [{"url": assets[k], "title": t} for k, t in (
            ("bg-studio-2am", "直播室・凌晨兩點"),
            ("bg-living-night", "客廳・電視播的是雪"),
            ("bg-table-lamp", "守則本・第一千零四版"))],
    })
    p["settings"] = s
    r = api({"project": p, "summary": "標題畫面、對話框樣式、封面、CG 收藏"}, "PUT")
    got = r["settings"]
    for k in ("titleScreenEnabled", "projectThumbnail", "cgGalleryEnabled", "stageFit"):
        v = got.get(k)
        print(f"  {k:20s} {str(v)[:56]}")
    print(f"  dialogueUi           {got['dialogueUi']['panelColor']} / "
          f"{got['dialogueUi']['speakerColor']}")
    print(f"  cgGalleryItems       {len(got.get('cgGalleryItems') or [])} 張")


if __name__ == "__main__":
    main()
