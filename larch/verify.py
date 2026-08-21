#!/usr/bin/env python3
"""小說版的檢查。線性的東西要驗的東西少，可是還是不能靠眼睛。"""
import json, pathlib, sys, urllib.request

PROJ = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
p = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://larch.yapiflow.com/api/agent/projects/{PROJ}",
    headers={"Authorization": f"Bearer {KEY}"}), timeout=180))
bad = []
cids = {c["id"] for c in p.get("characters", [])}
for b in p["boards"]:
    N = {n["id"]: n for n in b["nodes"]}
    out = {}
    for e in b["edges"]:
        if e["source"] not in N: bad.append(f"{b['id']}：邊的來源不存在 {e['source']}")
        if e["target"] not in N: bad.append(f"{b['id']}：邊的目標不存在 {e['target']}")
        out.setdefault(e["source"], []).append(e["target"])
    tgt = {t for v in out.values() for t in v}
    start = [n["id"] for n in b["nodes"] if n["data"].get("start")]
    for n in b["nodes"]:
        d, nid = n["data"], n["id"]
        if nid not in tgt and nid not in start:
            bad.append(f"{b['id']}：{nid} 沒有入邊（走不到）")
        if nid not in out and d.get("type") != "boardJump" and not d.get("chapterEnd"):
            bad.append(f"{b['id']}：{nid} 沒有出邊（點下去就停住）")
        if d.get("type") in (None, "dialogue") and not (d.get("text") or "").strip():
            bad.append(f"{b['id']}：{nid} 是空的對話卡")
        if d.get("characterId") and d["characterId"] not in cids:
            bad.append(f"{b['id']}：{nid} 的 characterId 對不到角色")
        for L in (d.get("characterLayers") or []):
            if not L.get("url"): bad.append(f"{b['id']}：{nid} 有立繪圖層沒有圖")
        if d.get("type") == "scene" and not d.get("background"):
            bad.append(f"{b['id']}：{nid} 場景卡沒有背景")
    # 線性檢查：分岔在小說版是不該出現的
    for s, t in out.items():
        if len(t) > 1: bad.append(f"{b['id']}：{s} 有 {len(t)} 條出邊，小說版應該是線性的")
    kinds = {}
    for n in b["nodes"]:
        k = n["data"].get("type") or "dialogue"
        kinds[k] = kinds.get(k, 0) + 1
    lines = sum(len(n["data"].get("dialogueLines") or []) for n in b["nodes"])
    print(f"{b['name']}：{len(b['nodes'])} 卡　{kinds}　多句對話 {lines} 句")
    print(f"  起點 {start or '★ 沒有起點卡'}")
print()
for x in bad: print("  ★", x)
print("全部通過。" if not bad else f"★ {len(bad)} 個問題")
sys.exit(1 if bad else 0)
