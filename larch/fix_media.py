#!/usr/bin/env python3
"""把素材分到正確的類別。

**上傳的時候要帶 `category`**（`{name, mimeType, base64, category}`），
沒帶的話全部掉進「道具」。這是 Larch 自己的角色工坊提示詞裡寫的，
skill 文件沒提，我第一次上傳時漏了。

紀錄本來就在 project.media 裡，所以改分類直接改欄位，不用重傳一次。

    場景 scene      背景圖
    立繪 character  角色的全身圖與表情差分
    道具 prop       頭像那種可以獨立擺上場的東西
"""
import json, pathlib, urllib.request

P = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
B = f"https://larch.yapiflow.com/api/agent/projects/{P}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def api(data=None, method="GET", path=""):
    body = json.dumps(data).encode() if data is not None else None
    return json.load(urllib.request.urlopen(
        urllib.request.Request(B + path, body, H, method=method), timeout=240))


def cat(name):
    if name.startswith("bg-"):
        return "scene"
    if name.startswith("avatar-"):
        return "prop"
    if name.startswith(("sprite-", "glitch-", "blackhole-")):
        return "character"
    return None


p = api()
n = 0
keep = []
for m in p.get("media", []):
    if m["name"] == "test-cat.png":          # 剛才試 category 用的，丟掉
        continue
    c = cat(m["name"])
    if c and m.get("category") != c:
        m["category"] = c
        n += 1
    keep.append(m)
p["media"] = keep
r = api({"project": p, "summary": "素材補上分類"}, "PUT")
from collections import Counter
print(f"改了 {n} 筆")
print(Counter(m.get("category") or "（沒有分類）" for m in r["media"]))
