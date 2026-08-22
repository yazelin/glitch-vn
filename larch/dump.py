#!/usr/bin/env python3
"""把板子印成可讀的樣子。線上要登入才玩得到，這是我自己驗節奏用的。"""
import json, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import PROJ, BASE, H, ROOT, STORE, api  # noqa: E402

p = api()
want = sys.argv[1] if len(sys.argv) > 1 else None
for b in p["boards"]:
    if want and b["id"] != want:
        continue
    print(f"\n{'='*54}\n{b['name']}\n{'='*54}")
    for n in b["nodes"]:
        d = n["data"]
        t = d.get("type") or "dialogue"
        cast = "／".join(f'{L["id"].split("-")[1]}@{L["position"]}'
                         for L in (d.get("characterLayers") or []))
        if t == "scene":
            print(f"\n── {d['title']} ──　{d.get('text','')}")
            print(f"   〔背景 {d.get('background','').rsplit('_',1)[-1]}〕")
            continue
        if t == "boardJump":
            print(f"→ {d.get('jumpBoardId')}"); continue
        head = f"[{cast}] " if cast else ""
        if d.get("dialogueLines"):
            print(f"  {head}")
            for L in d["dialogueLines"]:
                print(f"    {L['speaker']}：{L['text']}")
            continue
        sp = d.get("speaker")
        for i, line in enumerate((d.get("text") or "").split("\n")):
            tag = (f"{sp}：" if sp else "") if i == 0 else ("　" * (len(sp) + 1) if sp else "")
            print(f"  {head if i == 0 else ''}{tag}{line}")
