#!/usr/bin/env python3
"""把改寫套回建置腳本。

**改腳本，不改線上版。** 直接用 API 改台詞的話，下一次重建整天就全部蓋回去，
這個虧吃過兩次。所以這支是找到腳本裡的那串原文，換成新的。

換不到的會列出來，不會靜默跳過——靜默跳過等於改了一半。
"""
import json, pathlib, re, sys

TOOLS = pathlib.Path(__file__).resolve().parent
new = json.load(open("/tmp/rewrites.json"))
old = {x["id"]: x["text"] for x in json.load(open("/tmp/plain.json"))}

def esc(t):
    """腳本裡的字串是 Python 字面值：真換行寫成 \\n，而且可能被拆成多段相接。"""
    return t.replace("\n", "\\n")

done, miss = [], []
files = {f.name: f.read_text() for f in TOOLS.glob("build_day*.py")}
for nid, newtext in new.items():
    o, n = esc(old[nid]), newtext.replace("\\n", "\\n")
    hit = False
    for fn, src in files.items():
        if o in src:
            files[fn] = src.replace(o, n)
            done.append((fn, nid)); hit = True; break
    if not hit:
        miss.append(nid)
if "--write" in sys.argv:
    for fn, src in files.items():
        (TOOLS / fn).write_text(src)
print(f"套用 {len(done)} 張，找不到原文 {len(miss)} 張")
for m in miss: print("  ★", m)
