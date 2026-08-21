#!/usr/bin/env python3
"""從 backup/project.json 反推出一支建置腳本。

Day 1 與 Day 2 的建置腳本在一次暫存目錄被清空時弄丟了,那兩天只存在線上版,
改不動 —— 只能像 patch_day2_jump.py 那樣就地補,很難改台詞。這支把板子的
節點與邊原樣印成 Python,讓那兩天回到跟其他天一樣可以重建。

刻意印成 b.add / b.link 的原樣,不去猜哪張該還原成 say() 或 chain():
猜錯會靜默改掉內容,而原樣印出來的台詞照樣可以直接編輯。

用法:python3 reverse_board.py board-day1 > build_day1.py
"""
import json, pathlib, sys

BID = sys.argv[1]
P = json.load(open(pathlib.Path.home() / "glitch-vn/backup/project.json"))
B = next(b for b in P["boards"] if b["id"] == BID)
# 印成 Python 字面值,不是 JSON —— JSON 的 true/false/null 在 Python 裡跑不動
J = repr

print('#!/usr/bin/env python3')
print(f'"""{B["name"]} —— 這支是 reverse_board.py 從線上版反推出來的。')
print()
print('原本的建置腳本弄丟了(暫存目錄被清空),所以卡片是原樣印出來的,沒有還原成')
print('say()／chain()。台詞照樣直接改這裡,改完跑這支重建,不要只改線上版。')
print('"""')
print('import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")')
print('from daykit import Board')
print()
print(f'b = Board({J(B["id"])}, {J(B["name"])}, {J(B.get("description") or "")})')
print()
for n in B["nodes"]:
    p = n.get("position") or {}
    print(f'b.add({J(n["id"])}, {J(n["data"])}, x={p.get("x", 0)}, y={p.get("y", 0)})')
print()
for e in B["edges"]:
    c = (e.get("data") or {}).get("condition")
    args = f'{J(e["source"])}, {J(e["target"])}, {J(e.get("sourceHandle") or "right")}'
    if c:
        args += ', cond=' + J({k: v for k, v in c.items() if k != "kind"})
    print(f'b.link({args})')
print()
print(f'b.push({J(B["name"] + "：從線上版反推重建")})')
