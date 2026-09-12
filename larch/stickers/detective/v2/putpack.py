"""整包覆蓋：27 張 v2 表情 + 保留原本那張 cover 素材。PUT 是整包覆蓋，沒送到的等同被刪。"""
import json, os, time, urllib.request

K = open(os.path.expanduser("~/.config/larch/key")).read().strip()
PACK = "pack-5bb678c9-a6bc-4d19-8680-219d9bf842ed"
URL = "https://larch.ink/api/agent/asset-packs/" + PACK
D = "/home/ct/glitch-vn/larch/stickers/detective/v2/"

def get():
    r = urllib.request.Request(URL, headers={"Authorization": "Bearer " + K})
    with urllib.request.urlopen(r, timeout=300) as f:
        d = json.load(f)
    return d.get("pack", d)

before = get()
json.dump(before, open(D + "pack-before-v2.json", "w"), ensure_ascii=False, indent=1)
ups = json.load(open(D + "uploaded-v2.json"))
assert len(ups) == 27, len(ups)

emoji = [{
    "id": u["id"], "url": u["url"], "name": u["label"], "type": "image", "remote": True,
    "source": "AI Agent upload", "category": "emoji", "character": "格莉奇",
    "variant": "偵探腔" if int(u["num"]) <= 18 else "創作現場",
    "emojiShortcode": u["short"], "emojiName": u["label"],
} for u in sorted(ups.values(), key=lambda x: x["num"])]

keep = [a for a in before["assets"] if a["category"] != "emoji"]   # 原本那張 cover 素材
assets = emoji + keep
order = [a["id"] for a in assets]
assert len(order) == len(set(order))
assert len({e["emojiShortcode"] for e in emoji}) == 27
assert all(e["url"].endswith(".webp") for e in emoji)

body = {
    "name": before["name"], "description": before["description"],
    "cover": before["cover"], "creator": before["creator"],
    "category": "emoji", "categories": ["emoji", "scene"],
    "assets": assets, "assetOrder": order,
    "summary": "27 張表情換成 v2：重畫解決 v1 頭頂天線被切掉的問題，仍為 370×320 無損 WebP",
}

for attempt in range(4):
    req = urllib.request.Request(URL, data=json.dumps(body, ensure_ascii=False).encode(),
        method="PUT", headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as f:
            json.load(f)
        print("PUT ok")
        break
    except Exception as e:
        print("第", attempt + 1, "次失敗", repr(e)[:160])
        time.sleep(20)
else:
    raise SystemExit("PUT 四次都失敗，素材包沒有改動")

after = get()
json.dump(after, open(D + "pack-after-v2.json", "w"), ensure_ascii=False, indent=1)
e = [a for a in after["assets"] if a["category"] == "emoji"]
print("素材", len(after["assets"]), "| emoji", len(e), "| 全 webp",
      all(a["url"].endswith(".webp") for a in e),
      "| 名稱全中文", not any(a["name"].isascii() for a in e),
      "| shortcode 不重複", len({a["emojiShortcode"] for a in e}) == 27,
      "| cover", after["cover"] == before["cover"])
