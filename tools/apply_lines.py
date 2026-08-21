#!/usr/bin/env python3
"""把「卡片編號 → 新台詞」套回建置腳本。

反推回來的腳本裡，同一句話可能長成三種樣子：
  b.add('id', {'text': '單引號…'})        ← reverse_board 產生的
  ("id", "雙引號…", "表情", G)              ← chain 寫的
  b.settext("id", "…")                    ← 打磨區塊寫的
**而且同一張卡可能被設定兩次**（b.add 一次、settext 再一次），後者贏。
所以要全部換掉，只換一處等於沒換——這個虧吃過。

用法：python3 apply_lines.py <對照表.json> [--write]
"""
import json, pathlib, re, sys

new = json.load(open(sys.argv[1]))
T = pathlib.Path(__file__).resolve().parent
files = {f.name: f.read_text() for f in T.glob("build_day*.py")}
hits, miss = {}, []

for nid, text in new.items():
    n = 0
    for fn, src in files.items():
        # b.add('id', {'text': '...'}) / {"text": "..."}
        for q1, q2 in (("'", "'"), ('"', '"')):
            pat = re.compile(rf"({q1}{re.escape(nid)}{q2},\s*\{{[^}}]*?{q1}text{q2}:\s*)"
                             rf"({q1}(?:[^{q1}\\]|\\.)*{q2})")
            src, k = pat.subn(lambda m: m.group(1) + q1 + text + q1, src)
            n += k
        # ("id", "...", 表情, 說話者) —— chain 的元組。
        # **要排除接線的函式**:b.link("a","b") 的第一個參數也是編號,
        # 直接比對會把「目標卡片」換成台詞。踩過一次,而且是 build 掛掉才發現。
        pat2 = re.compile(rf'(?<!link\()(?<!unlink\()(?<!redirect\()'
                          rf'(\(\s*"{re.escape(nid)}"\s*,\s*)("(?:[^"\\]|\\.)*")'
                          rf'(?=\s*,\s*")')
        src, k = pat2.subn(lambda m: m.group(1) + '"' + text + '"', src)
        n += k
        # b.settext("id", "...") —— 可能跨行相接
        pat3 = re.compile(rf'(b\.settext\(\s*"{re.escape(nid)}"\s*,\s*)'
                          rf'((?:"(?:[^"\\]|\\.)*"\s*\n?\s*)+)')
        src, k = pat3.subn(lambda m: m.group(1) + '"' + text + '"', src)
        n += k
        files[fn] = src
    if n:
        hits[nid] = n
    else:
        miss.append(nid)

if "--write" in sys.argv:
    for fn, src in files.items():
        (T / fn).write_text(src)
print(f"套用 {len(hits)} 句（共改到 {sum(hits.values())} 處）")
multi = {k: v for k, v in hits.items() if v > 1}
if multi:
    print(f"  同一張卡被設定多次的 {len(multi)} 張：{', '.join(list(multi)[:6])}")
if miss:
    print(f"★ 找不到 {len(miss)} 句：{', '.join(miss)}")
sys.exit(1 if miss else 0)
