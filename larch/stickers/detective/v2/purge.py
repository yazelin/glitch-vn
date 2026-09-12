"""刪掉專案素材庫裡的孤兒：v1 的 27 張 + 我中斷的 6 張 v2。刪之前先證明沒人引用。"""
import json, os, re, sys, time, urllib.request

K = open(os.path.expanduser("~/.config/larch/key")).read().strip()
PROJ = "project-bec1644c-0dfe-4447-86c0-0c592e2f939f"
PURL = f"https://larch.ink/api/agent/projects/{PROJ}"
MURL = PURL + "/media"
PACK = "https://larch.ink/api/agent/asset-packs/pack-5bb678c9-a6bc-4d19-8680-219d9bf842ed"
PAT = re.compile(r"^glitch-detective-(v2-)?\d{2}\.webp$")

def call(url, method="GET", body=None):
    r = urllib.request.Request(url, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    for i in range(4):
        try:
            with urllib.request.urlopen(r, timeout=300) as f:
                return json.load(f)
        except Exception as e:
            print(" ", method, "第", i+1, "次失敗", repr(e)[:120], flush=True)
            time.sleep(20)
    raise SystemExit(method + " 四次都失敗")

proj = call(PURL); proj = proj.get("project", proj)
pack = call(PACK); pack = pack.get("pack", pack)

targets = [a for a in proj["media"] if PAT.match(a.get("name", ""))]
print("比對到的孤兒:", len(targets))
print("  v1:", sum(1 for a in targets if "-v2-" not in a["name"]),
      " v2 中斷那批:", sum(1 for a in targets if "-v2-" in a["name"]))

# 三道安全檢查
pack_urls = {a["url"] for a in pack["assets"]}
blob = json.dumps({k: v for k, v in proj.items() if k != "media"}, ensure_ascii=False)
bad = [a for a in targets if a["url"] in pack_urls or a["url"] in blob]
kept = [a for a in proj["media"] if not PAT.match(a.get("name", ""))]
print("  仍被素材包或專案卡片引用的:", len(bad))
print("  誤中你手動上傳的檔:", sum(1 for a in targets if re.match(r"^\d{2}-", a.get("name", ""))))
print("  刪完專案素材會從", len(proj["media"]), "剩", len(kept))
if bad:
    raise SystemExit("有東西還在引用，不刪")
if len(targets) != 33:
    print("注意：預期 33 筆，實際", len(targets))
if "--go" not in sys.argv:
    raise SystemExit("(乾跑，沒有刪)")

call(MURL, "DELETE", {"assetIds": [a["id"] for a in targets]})
proj2 = call(PURL); proj2 = proj2.get("project", proj2)
left = [a for a in proj2["media"] if PAT.match(a.get("name", ""))]
print("刪除後仍殘留:", len(left), "| 專案素材總數", len(proj2["media"]))
pack2 = call(PACK); pack2 = pack2.get("pack", pack2)
print("素材包仍是", len(pack2["assets"]), "筆，emoji",
      sum(1 for a in pack2["assets"] if a["category"] == "emoji"))
