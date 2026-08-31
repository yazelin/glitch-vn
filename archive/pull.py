#!/usr/bin/env python3
"""把 Larch 上的專案整包抓下來存檔。Larch 是唯一一份,本機要留副本。"""
import pathlib, json, pathlib, re, sys, urllib.request
K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
d = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://larch.ink/api/agent/projects/{P}",
    headers={"Authorization": f"Bearer {K}"}), timeout=120))
root = pathlib.Path(__file__).resolve().parent.parent / "backup"
root.mkdir(parents=True, exist_ok=True)
(root / "project.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
# 素材 key 去掉副檔名與 -v2 這類版號尾碼;同一個 key 有多筆時取最後上傳的那筆,
# 免得重出一版之後 daykit 找不到(bg-night-v2 vs bg-night 就踩過一次)。
assets = {}
for m in d["media"]:
    key = re.sub(r"-v\d+$", "", m["name"].rsplit(".", 1)[0])
    assets[key] = m["url"]
(root / "assets.json").write_text(json.dumps(assets, ensure_ascii=False, indent=2), encoding="utf-8")
print("板:", [(b["name"], len(b["nodes"]), len(b["edges"])) for b in d["boards"]])
print("變數", len(d["variables"]), "個　素材", len(d["media"]), "個")
