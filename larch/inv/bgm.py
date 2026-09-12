"""背景代號 → BGM。**一張表，兩個掛載入口都讀它。**

調查篇的背景有兩個地方會寫：`build.py` 的場景卡，以及 `push.py` 段落中途換場景
（`sceneCode`，BG_MAP 那一段）。2026-09-12 只掛在 build 那一邊的時候，
有 9 張卡是真的換了地點、畫面也換了，音樂卻還停在上一個地點——**而且板上
看起來完全正常，storylint 的 S2 是綠的**，因為它只數有幾張卡宣告了 bgm。

規格第三節三條規矩：只在換曲點寫、空字串等於沒設（前一首會繼續播）、
有配音的段落音量 0.24–0.32。
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BGM_PAGES = "https://yazelin.github.io/glitch-vn/bgm"
_A = json.loads((ROOT / "larch/assets.json").read_text(encoding="utf-8"))

BGM_FOR = {
    # 調查篇自己的五支（2026-09-12 定案，證據強度見 art/bgm/inv-candidates/README.md）
    "bg-store-day": "inv-store", "bg-store-evening": "inv-store", "bg-store-night": "inv-store",
    "bg-parts-day": "inv-parts", "bg-parts-evening": "inv-parts", "bg-parts": "inv-parts",
    "bg-figure-day": "inv-figure", "bg-figure-evening": "inv-figure", "bg-figure": "inv-figure",
    "bg-laundry-day": "inv-laundry", "bg-laundry-evening": "inv-laundry", "bg-laundry": "inv-laundry",
    # 站牌與捷運口共用一首：兩個地點，同一種「在路上等」
    "bg-busstop-day": "inv-transit", "bg-busstop-evening": "inv-transit", "bg-busstop": "inv-transit",
    "bg-metro-day": "inv-transit", "bg-metro-evening": "inv-transit", "bg-metro": "inv-transit",
    # 沿用正篇的六個
    "bg-lobby-day": "bgm-living", "bg-lobby-evening": "bgm-living", "bg-apartment-hall": "bgm-living",
    "bg-roof-day": "bgm-shop", "bg-roof-evening": "bgm-shop", "bg-noah-shop": "bgm-shop",
    "bg-bambi-studio-day": "bgm-studio", "bg-studio-evening": "bgm-studio", "bg-bambi-studio": "bgm-studio",
    "bg-tower14-day": "bgm-cold", "bg-tower14-evening": "bgm-cold", "bg-tower14-night": "bgm-cold",
    "bg-street-day2": "bgm-street", "bg-street-evening": "bgm-street", "bg-street-night": "bgm-street",
    "bg-desk-night": "bgm-notebook",
    # **錄音間門口（booth）故意留白。** 十二個地點裡只有它沒有拍板要哪一首，
    # 沒寫就是延續前一首（規格第三節第一條），那是平台行為不是漏掉。
    # 正篇最接近的是 bg-corridor → bgm-cold，但那是我推的，不是拍板過的，所以不寫。
    "bg-booth-hall": None, "bg-booth-evening": None,
    # 貓草家門口與家裡也沒有拍板（不在那十二個地點的清單裡）。寫成 None 是為了
    # 讓「不在表上」那個警告留給**真的新出現的背景**，不要被這兩個長期留白的蓋掉。
    "bg-catgrass-door": None, "bg-catgrass-home": None,
}
# 有配音的段落音量壓在 0.24–0.32，再高會蓋掉台詞（規格第三節第三條）。
# 取中間值：調查篇幾乎每一句都有聲音。
BGM_VOLUME = 0.28
# 有配音的段落音量壓在 0.24–0.32，再高會蓋掉台詞（規格第三節第三條）。
# 取中間值：調查篇幾乎每一句都有聲音。
VOLUME = 0.28
STAT = {"set": 0, "blank": [], "unknown": []}


def url(track):
    if track.startswith("inv-"):
        return f"{BGM_PAGES}/bgm-{track}.mp3"
    return _A[track]          # 正篇那六支在 assets.json（Larch 的 R2）


def apply(d, code):
    """照背景代號把 bgm 寫上去。code 不帶 @@。回傳有沒有寫。"""
    if code not in BGM_FOR:
        STAT["unknown"].append(code)     # 新背景沒進表要看得見，不能安靜沿用前一首
        return False
    track = BGM_FOR[code]
    if track is None:
        STAT["blank"].append(code)
        return False
    # **不要寫空字串。** 空字串在平台上等於沒設，前一首會繼續播，
    # 而它看起來像「這裡設過了」。storylint 的 S2 就是在抓這個。
    d["bgm"] = url(track)
    d["bgmVolume"] = VOLUME
    d["bgmLoop"] = True
    STAT["set"] += 1
    return True


def report(where):
    import collections
    u = collections.Counter(STAT["unknown"]); b = collections.Counter(STAT["blank"])
    print(f"BGM（{where}）：掛上 {STAT['set']} 張卡　故意留白 {sum(b.values())} 張　"
          f"不在表上 {sum(u.values())} 張")
    if b:
        print(f"  留白的背景：{dict(b)}")
    if u:
        print(f"  ★ 不在對照表上的背景：{dict(u)}　（會安靜地沿用前一首，去補表）")


def dedupe(nodes, edges):
    """拿掉「同一首再宣告一次」的那些。

    **板子是圖，不是直線。** 同一張卡可能從好幾條路進來，所以「前一首是什麼」
    要沿著邊往回找最近的宣告卡，不能照卡片順序。平台的行為是同一首再下一次會
    從頭重播，所以一段連續的同地點卡片只能有第一張帶 bgm。

    拿掉一張會改變別張的「最近祖先」，所以要跑到不再變動為止。
    """
    import collections, re
    rev = collections.defaultdict(list)
    for e in edges:
        rev[e["target"]].append(e["source"])
    data = {n["id"]: n["data"] for n in nodes}

    def track(i):
        u = data[i].get("bgm")
        if not u:
            return None
        m = re.search(r"_?((?:bgm-inv|bgm)-[a-z0-9-]+)\.mp3$", u)
        return m.group(1) if m else u

    removed = 0
    while True:
        cur = {i: track(i) for i in data if track(i)}
        drop = []
        for i, t in cur.items():
            seen, q, found = set(), list(rev.get(i, [])), set()
            while q:
                x = q.pop()
                if x in seen:
                    continue
                seen.add(x)
                if x in cur:
                    found.add(cur[x])
                else:
                    q.extend(rev.get(x, []))
            if found == {t}:          # 前面每一條路都已經在播這一首
                drop.append(i)
        if not drop:
            break
        for i in drop:
            for k in ("bgm", "bgmVolume", "bgmLoop"):
                data[i].pop(k, None)
        removed += len(drop)
    if removed:
        print(f"BGM：拿掉 {removed} 張「同一首再宣告一次」的（會從頭重播）")
    return removed
