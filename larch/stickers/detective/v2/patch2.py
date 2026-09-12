"""只換 23 與 24 兩張：上傳新檔 → 單次 PUT 換掉那兩筆 → 驗 → 刪舊的兩筆孤兒。"""
import base64, io, json, os, time, urllib.request
import numpy as np
from PIL import Image

K = open(os.path.expanduser("~/.config/larch/key")).read().strip()
PROJ = "project-bec1644c-0dfe-4447-86c0-0c592e2f939f"
MEDIA = f"https://larch.ink/api/agent/projects/{PROJ}/media"
PACK = "https://larch.ink/api/agent/asset-packs/pack-5bb678c9-a6bc-4d19-8680-219d9bf842ed"
D = "/home/ct/glitch-vn/larch/stickers/detective/"
UA = {"User-Agent": "Mozilla/5.0"}
JOBS = [("23", "分歧選項怎麼選"), ("24", "今晚一定要完稿")]

def call(url, method="GET", body=None, tries=5):
    for i in range(tries):
        r = urllib.request.Request(url, method=method,
            data=json.dumps(body, ensure_ascii=False).encode() if body else None,
            headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=300) as f:
                return json.load(f)
        except Exception as e:
            print(" ", method, "第", i+1, "次失敗", repr(e)[:110], flush=True)
            time.sleep(20)
    raise SystemExit(method + " 全部失敗")

def strays(url):
    from scipy import ndimage
    b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    al = np.asarray(Image.open(io.BytesIO(b)).convert("RGBA"))[..., 3]
    op = al > 24
    lab, k = ndimage.label(op)
    sz = ndimage.sum(op, lab, range(1, k+1))
    m = int(np.argmax(sz)) + 1
    top = np.nonzero((lab == m).any(1))[0].min()
    return [int(sz[i-1]) for i in range(1, k+1) if i != m
            and np.nonzero((lab == i).any(1))[0].max() < top-2], int(op[0].sum()), int(np.nonzero(op)[0].min())

pack = call(PACK); pack = pack.get("pack", pack)
assert len(pack["assets"]) == 28, len(pack["assets"])
old = {a["name"]: a for a in pack["assets"] if a["category"] == "emoji"}
assert all(cap in old for _, cap in JOBS)

fresh = {}
for num, cap in JOBS:
    b64 = base64.b64encode(open(f"{D}{num}-{cap}.webp", "rb").read()).decode()
    a = call(MEDIA, "POST", {"name": f"glitch-detective-v2b-{num}.webp",
                             "mimeType": "image/webp", "base64": b64, "category": "prop"})["asset"]
    fresh[cap] = a
    print(num, cap, "上傳 ok", a["url"][-28:], flush=True)

# 新 id 等於新增、舊 id 沒送到等於移除，一次 PUT 就夠（PUT 只有對「同一個 id」才會不更新）
assets = []
for a in pack["assets"]:
    cap = a.get("name")
    if a["category"] == "emoji" and cap in fresh:
        assets.append({**a, "id": fresh[cap]["id"], "url": fresh[cap]["url"],
                       "source": fresh[cap].get("source", a.get("source"))})
    else:
        assets.append(a)
call(PACK, "PUT", {"name": pack["name"], "description": pack["description"],
                   "cover": pack["cover"], "creator": pack["creator"],
                   "category": pack["category"], "categories": pack["categories"],
                   "assets": assets, "assetOrder": [a["id"] for a in assets],
                   "summary": "換掉 23、24 兩張：清掉切格殘留在頭頂上方的離群碎片"})

after = call(PACK); after = after.get("pack", after)
e = [a for a in after["assets"] if a["category"] == "emoji"]
print("素材", len(after["assets"]), "| emoji", len(e), "| cover 未動", after["cover"] == pack["cover"])
for num, cap in JOBS:
    live = [a for a in e if a["name"] == cap]
    assert len(live) == 1, (cap, len(live))
    s, touch, top = strays(live[0]["url"])
    print(f"  {cap}: 線上網址已換 {live[0]['url'] == fresh[cap]['url']} | 離群碎片 {s or '無'} "
          f"| 觸及上緣 {touch} | 頭頂留白 {top}")
    assert live[0]["url"] == fresh[cap]["url"] and not s and touch == 0

# 舊的兩筆變孤兒,確認沒人引用再刪
proj = call(f"https://larch.ink/api/agent/projects/{PROJ}")
proj = proj.get("project", proj)
urls = {a["url"] for a in after["assets"]}
blob = json.dumps({k: v for k, v in proj.items() if k != "media"}, ensure_ascii=False)
dead = [old[cap]["id"] for _, cap in JOBS]
bad = [a for a in proj["media"] if a["id"] in dead and (a["url"] in urls or a["url"] in blob)]
print("舊兩筆仍被引用:", len(bad))
assert not bad
call(MEDIA, "DELETE", {"assetIds": dead})
print("已刪掉舊的兩筆孤兒")
