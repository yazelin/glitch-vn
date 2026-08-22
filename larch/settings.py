#!/usr/bin/env python3
"""專案設定：標題畫面、對話框樣式、游標、封面。

**這些不是裝飾。** 市集上那兩個作品跟我第一版最大的差別，一半在這裡：
沒有 titleScreen 就沒有開始畫面，沒有 dialogueUi 就是預設的灰盒子。

欄位是從市集的專案 JSON 挖出來的（GET /api/marketplace/{id}?play=1，不用登入）。
"""
import base64, json, pathlib, urllib.request

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import PROJ, BASE, H, ROOT, STORE, api  # noqa: E402




def main():
    assets = json.loads((ROOT / "larch/assets.json").read_text())
    # **標題畫面吃的是第一張卡的背景**，不是這裡。這個是市集與列表的縮圖，
    # 所以用有標題燒在上面的 OG 圖才對。
    # 第一張卡的背景是 title-cover（乾淨的，文字交給 titleScreen 的 layer 畫）。
    for key, f in (("title-cover", "title-cover.jpg"), ("cover", "og.jpg")):
        if key not in assets:
            raw = (ROOT / "docs/img" / f).read_bytes()
            assets[key] = api({"name": f, "mimeType": "image/jpeg", "category": "scene",
                               "base64": base64.b64encode(raw).decode()},
                              "POST", "/media")["asset"]["url"]
            print(f"  上傳 {f}")
    cover = assets["cover"]
    (ROOT / "larch/assets.json").write_text(
        json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")

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
        # **按鈕是 layer，不會自己出現。** kind:"button" 配 action:start/continue/gallery，
        # 語言選單是 kind:"language"。只放文字層的話畫面上一個按鈕都沒有。
        # 兩個角色站在左右，所以文字與按鈕全部排在中間那一欄。
        # **文字三層的 x/y 是使用者在平台上調過的，讀回來寫進這裡。**
        # 這一支會整包覆蓋 titleScreen，所以在平台上調完要記得回寫，不然下次跑就洗掉。
        "titleScreen": {"frame": "none", "bgmVolume": 0.4, "layers": [
            {"id": "eyebrow", "kind": "text", "role": "eyebrow",
             "x": 43.87, "y": 16.29, "size": 1, "align": "center", "width": 34},
            {"id": "name", "kind": "text", "role": "title",
             "x": 45.41, "y": 22.66, "size": 5.4, "align": "center", "width": 40},
            {"id": "description", "kind": "text", "role": "description",
             "x": 45.48, "y": 32.45, "size": 1.2, "align": "center", "width": 36},
            {"id": "action-start", "kind": "button", "action": "start",
             "icon": True, "x": 37, "y": 50, "size": 1.35, "width": 26},
            {"id": "action-continue", "kind": "button", "action": "continue",
             "icon": True, "x": 37, "y": 60, "size": 1.35, "width": 26},
            {"id": "action-gallery", "kind": "button", "action": "gallery",
             "icon": True, "x": 37, "y": 70, "size": 1.35, "width": 26},
            {"id": "languages", "kind": "language", "x": 37, "y": 82, "size": 1.1},
        ]},
        # 配色跟小說站同一套（ai-brain-site 的 --bg #04080c、--cy #25c2e8、--mint #7cf3c0）
        # fontFamily 使用者在平台上改成 sans，讀回來收進這裡
        "dialogueUi": {"preset": "custom", "presentation": "gradient",
                       "fontFamily": "sans", "fontSize": 25, "nameFontSize": 18,
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
            ("bg-table-lamp", "守則本・第一千零四版"),
            ("bg-booth", "錄音間・第十一次"),
            ("bg-greenroom", "休息室・兩點五十分"),
            ("bg-studio-day", "聯動・猜歌"),
            ("bg-corridor", "後台走廊・燈一段一段熄"),
            ("bg-bambi-studio", "斑比的工作室・七個馬克杯"),
            ("bg-apartment-hall", "門口・凌晨一點"),
            ("bg-noah-shop", "諾亞的店・沒有一台是好的"),
            ("bg-stairs", "樓梯口・兩個人點了一下頭"),
            ("bg-street-day", "車站前・你最近忘記過什麼"),
            ("bg-office-14f", "十四樓・一盆真的植物"),
            ("bg-kitchen-morning", "廚房・她開始找麵粉"))],
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
