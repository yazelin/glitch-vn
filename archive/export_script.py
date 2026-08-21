#!/usr/bin/env python3
"""把整個遊戲匯出成一份看得懂的純文字劇本。

dump_board.py 是把節點圖照順序印出來，分支會被攤平成一條直線——拿去給人審
會誤判（會以為玩家一次要讀完全部分支）。這一支照圖的結構走，分支標出來、
縮排開，讀的人看得出「這裡岔開了，玩家只走一條」。

走圖的邏輯在 script_walk.py（HTML 版共用同一支，只能有一份）。

用法：python3 export_script.py > docs/script.txt
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from script_walk import DAYS, board_events

out = []
for b in DAYS:
    out.append(f"\n\n{'═' * 56}\n{b['name']}\n{b.get('description','')}\n{'═' * 56}")
    for e in board_events(b):
        pad = "　" * e["depth"]
        k = e["kind"]
        if k == "scene":
            out.append(f"\n{pad}── {e['title']} ──　{e['text']}")
        elif k == "choice":
            out.append(f"{pad}【選擇】{e['text']}")
        elif k == "input":
            out.append(f"{pad}【玩家打字 → {e['var']}】{e['text']}")
        elif k == "jump":
            out.append(f"{pad}→ 接到 {e['to']}")
        elif k == "vars":
            tail = f"　〔{e['ops']}〕" if e["ops"] else ""
            out.append(f"{pad}{e['text']}{tail}" if e["text"] else f"{pad}〔{e['ops']}〕")
        elif k == "loop":
            out.append(f"{pad}↩︎（回到前面的「{e['text']}」）")
        elif k == "branch":
            if e["label"] is not None:
                out.append(f"{pad}　◆ 選「{e['label']}」"
                           + (f"（{e['cond']} 才走這條）" if e["cond"] else ""))
            else:
                out.append(f"{pad}　◆ " + (f"{e['cond']} 的話" if e["cond"] else "其他情況"))
        else:
            who = e["who"]
            for line in e["lines"]:
                out.append(f"{pad}{who + '：' if who and who != '旁白' else ''}{line}")

print("\n".join(out))
