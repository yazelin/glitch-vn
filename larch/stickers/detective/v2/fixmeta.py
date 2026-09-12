"""把手動上傳的 27 張改成 emoji 並補齊欄位，順便清掉 v1 舊表情。
PUT 對既有 id 只認不改，所以要兩次：先移除、再用同一批 id 重加。"""
import json, os, re, time, urllib.request

K = open(os.path.expanduser("~/.config/larch/key")).read().strip()
PACK = "pack-5bb678c9-a6bc-4d19-8680-219d9bf842ed"
URL = "https://larch.ink/api/agent/asset-packs/" + PACK
D = "/home/ct/glitch-vn/larch/stickers/detective/v2/"

SHORT = {"01":"fishy","02":"motive","03":"nocoincidence","04":"blocked","05":"itsme",
 "06":"cantwrite","07":"illogical","08":"deadtalk","09":"onetruth","10":"onetruthyell",
 "11":"unusual","12":"amongus","13":"boldguess","14":"dyingmessage","15":"timeline",
 "16":"nohiding","17":"tipoficeberg","18":"casesolved","19":"tenrevisions","20":"ideastruck",
 "21":"greatart","22":"giveup","23":"whichbranch","24":"finishtonight","25":"perfectbgm",
 "26":"wheresbug","27":"needidea"}

def req(method, body=None):
    r = urllib.request.Request(URL, method=method,
        data=json.dumps(body, ensure_ascii=False).encode() if body else None,
        headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    for i in range(4):
        try:
            with urllib.request.urlopen(r, timeout=300) as f:
                return json.load(f)
        except Exception as e:
            print(" ", method, "第", i+1, "次失敗", repr(e)[:120], flush=True)
            time.sleep(20)
    raise SystemExit(method + " 四次都失敗")

def get():
    d = req("GET")
    return d.get("pack", d)

before = get()
json.dump(before, open(D + "pack-before-fixmeta.json", "w"), ensure_ascii=False, indent=1)

new, cover = [], []
for a in before["assets"]:
    m = re.match(r"^(\d{2})-(.+)$", a.get("name") or "")
    if m and a["category"] == "scene":
        new.append((m.group(1), m.group(2), a))
    elif a["category"] != "emoji":
        cover.append(a)                      # 保留那張 cover 素材，id 與 url 不動
new.sort()
assert len(new) == 27 and {n for n, _, _ in new} == set(SHORT), len(new)
assert len(cover) == 1, cover

base = {"name": before["name"], "description": before["description"],
        "cover": before["cover"], "creator": before["creator"]}

# 第一次：只留 cover，把 24 筆 v1 舊表情與那 27 筆 scene 全部移出
print("PUT 1：清成只剩 cover")
req("PUT", {**base, "category": "scene", "categories": ["scene"],
            "assets": cover, "assetOrder": [a["id"] for a in cover],
            "summary": "清掉 v1 舊表情，並把手動上傳的 27 張暫時移出以便改欄位"})
mid = get()
print("  現在", len(mid["assets"]), "筆")
assert len(mid["assets"]) == 1

# 第二次：用同一批 id 重加，這次帶齊 emoji 欄位
emoji = [{
    "id": a["id"], "url": a["url"], "name": cap, "type": a.get("type", "image"),
    "remote": True, "source": a.get("source", "upload"), "category": "emoji",
    "character": "格莉奇", "variant": "偵探腔" if int(n) <= 18 else "創作現場",
    "emojiShortcode": SHORT[n], "emojiName": cap,
} for n, cap, a in new]
assets = emoji + cover
print("PUT 2：重加 27 筆 emoji")
req("PUT", {**base, "category": "emoji", "categories": ["emoji", "scene"],
            "assets": assets, "assetOrder": [a["id"] for a in assets],
            "summary": "27 張 v2 表情改歸 emoji，補上中文名稱、emojiName、英文 shortcode 與角色分組"})

after = get()
json.dump(after, open(D + "pack-after-fixmeta.json", "w"), ensure_ascii=False, indent=1)
e = [a for a in after["assets"] if a["category"] == "emoji"]
print("素材", len(after["assets"]), "| emoji", len(e),
      "| 全 webp", all(a["url"].endswith(".webp") for a in e),
      "| 名稱全中文", not any(a["name"].isascii() for a in e),
      "| 名稱無編號前綴", not any(re.match(r"^\d{2}-", a["name"]) for a in e),
      "| shortcode 不重複", len({a["emojiShortcode"] for a in e}) == 27,
      "| emojiName 齊全", all(a.get("emojiName") for a in e),
      "| cover 未動", after["cover"] == before["cover"],
      "| categories", after["categories"])
