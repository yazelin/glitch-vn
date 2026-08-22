#!/usr/bin/env python3
"""小說版的檢查。線性的東西要驗的東西少，可是還是不能靠眼睛。"""
import json, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import PROJ, BASE, H, ROOT, STORE, api  # noqa: E402

p = api()
bad, warn = [], []
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
# ── 站位的兩個常見錯 ─────────────────────────────────
# 一、旁白講到某個人在場，可是台上沒有他
# 二、某個人站在台上很久，中間沒有講話也沒有被提到
# 兩個都是「站位綁在段落邊界、不是綁在劇情上」的症狀，第一章都犯過。
CAST = ["格莉奇", "黑洞先生", "貓草", "鐵塔", "0x", "斑比", "諾亞"]
QUIET = 6
for b in p["boards"]:
    on = {}
    for i, n in enumerate(b["nodes"]):
        d = n["data"]
        names = {a["name"] for a in (d.get("stage") or {}).get("actors", [])}
        txt = (d.get("text") or "") + " ".join(
            l.get("text", "") for l in (d.get("dialogueLines") or []))
        speak = {d.get("speaker")} | {l.get("speaker") for l in (d.get("dialogueLines") or [])}
        # 只抓「旁白用某人當句首描述他在場」——「黑洞先生坐在沙發上」要抓，
        # 「第三則是斑比自己轉的」不要抓（那只是提到名字）。
        heads = {l.strip()[:6] for l in (d.get("text") or "").split("\n")}
        for who in CAST:
            present = (d.get("speaker") == "旁白"
                       and any(h.startswith(who) for h in heads))
            if present and who not in names:
                warn.append(f"{b['id']}：{n['id']} 旁白說「{who}」在場，可是台上沒有他")
            if who in names:
                if who in speak or who in txt:
                    on[who] = i
                elif i - on.get(who, i) >= QUIET:
                    warn.append(f"{b['id']}：{n['id']} 「{who}」已經站了 {i - on[who]} 張卡"
                                f"沒講話也沒被提到，要不要讓他退場")
                    on[who] = i
            else:
                on.pop(who, None)

print()
for x in bad: print("  ★", x)
for x in warn: print("  ・", x)
print("全部通過。" if not bad else f"★ {len(bad)} 個問題")
sys.exit(1 if bad else 0)
