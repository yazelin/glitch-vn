#!/usr/bin/env python3
"""從 project.json 生機制文件。

手寫的機制表一定會過期 —— 劇本每改一次就要記得回來改文件,不可能記得住。
所以直接從專案本身長出來:哪張卡設了什麼變數、哪條邊看什麼條件,都是讀出來的。
之後 GitHub Pages 的攻略站也吃這份輸出。
"""
import json, pathlib, collections

P = json.load(open(pathlib.Path.home() / "glitch-vn/backup/project.json"))
BOARDS = [b for b in P["boards"] if b["id"].startswith("board-day")]
BOARDS.sort(key=lambda b: int(b["id"].replace("board-day", "")))
N = {n["id"]: (b, n) for b in P["boards"] for n in b["nodes"]}

OPTXT = {"eq": "＝", "neq": "≠", "gt": "＞", "gte": "≥", "lt": "＜", "lte": "≤"}
KIND = {"set": "設為", "add": "加", "toggle": "翻轉", "random": "隨機"}

out = ["# 《格莉奇與黑洞先生》機制表", "",
       "這份文件是 `tools/gen_docs.py` 從 Larch 專案讀出來生的，不要手改。",
       "改完劇本跑 `python3 tools/pull.py && python3 tools/gen_docs.py`。", ""]

out += ["## 一、規模", "",
        f"- 天數：{len(BOARDS)}", 
        f"- 卡片：{sum(len(b['nodes']) for b in P['boards'])}（其中素材庫 {len(next(b for b in P['boards'] if not b['id'].startswith('board-day'))['nodes'])} 張不在遊玩路徑上）",
        f"- 連線：{sum(len(b['edges']) for b in P['boards'])}",
        f"- 變數：{len(P['variables'])}", ""]

# 誰動了哪個變數
writers = collections.defaultdict(list)
for b in BOARDS:
    for n in b["nodes"]:
        for op in n["data"].get("variableOps") or []:
            writers[op["variable"]].append((b, n, op))
        iv = n["data"].get("inputVariable")
        if iv: writers[iv].append((b, n, {"kind": "input"}))

out += ["## 二、變數", "", "| 變數 | 說明 | 預設 | 誰會動它 |", "|---|---|---|---|"]
for v in P["variables"]:
    who = "、".join(sorted({w[0]["name"].split("・")[0] for w in writers[v["name"]]})) or "（沒有卡片會動）"
    out.append(f"| `{v['name']}` | {v.get('label') or ''}{('：' + v['description']) if v.get('description') else ''} "
               f"| `{v.get('defaultValue')}` | {who} |")
out.append("")

out += ["## 三、每天的選擇與後果", ""]
for b in BOARDS:
    out += [f"### {b['name']}", ""]
    seg = None
    for n in b["nodes"]:
        d = n["data"]
        if d.get("type") == "scene":
            seg = d.get("title", "")
        if d.get("type") == "choice":
            out.append(f"**{seg}｜{d.get('text','').splitlines()[0]}**")
            out.append("")
            for i, c in enumerate(d.get("choices") or []):
                label = c if isinstance(c, str) else c.get("text", "")
                # 這個選項往下會設什麼
                effs = []
                for e in b["edges"]:
                    if e["source"] == n["id"] and e.get("sourceHandle") == f"choice-{i}":
                        tgt = next((m for m in b["nodes"] if m["id"] == e["target"]), None)
                        cond = (e.get("data") or {}).get("condition")
                        pre = (f"（條件：`{cond['variable']}` {OPTXT.get(cond['op'], cond['op'])} `{cond['value']}`）"
                               if cond else "")
                        if tgt:
                            for op in tgt["data"].get("variableOps") or []:
                                effs.append(f"{pre}`{op['variable']}` {KIND.get(op['kind'], op['kind'])} `{op.get('value', '')}`")
                            if not (tgt["data"].get("variableOps")):
                                effs.append(f"{pre}（不動變數）")
                out.append(f"- {i+1}. {label}")
                for e in effs: out.append(f"    - {e}")
            out.append("")
        if d.get("type") == "input":
            out += [f"**{seg}｜填空 → `{d.get('inputVariable')}`**：{d.get('text','').splitlines()[0]}", ""]
    # 這板上有條件的邊
    conds = [(e, (e.get("data") or {}).get("condition")) for e in b["edges"] if (e.get("data") or {}).get("condition")]
    conds = [(e, c) for e, c in conds if not (e.get("sourceHandle") or "").startswith("choice-")]
    if conds:
        out += ["**這天會依狀態分岔的地方**", ""]
        for e, c in conds:
            tgt = next((m for m in b["nodes"] if m["id"] == e["target"]), None)
            title = (tgt["data"].get("title") or tgt["id"]) if tgt else e["target"]
            out.append(f"- `{c['variable']}` {OPTXT.get(c['op'], c['op'])} `{c['value']}` → {title}")
        out.append("")

# 結局
end_board = next((b for b in BOARDS if b["id"] == "board-day7"), None)
if end_board:
    out += ["## 四、結局", "",
            "最後一天的結局由兩件事決定：中午把麵包放到哪裡，以及**這一週餵過黑洞先生幾次**。", ""]
    for n in end_board["nodes"]:
        for op in n["data"].get("variableOps") or []:
            if op["variable"] == "ending":
                out.append(f"- **{n['data'].get('title')}**（`ending` = `{op.get('value')}`）")
    out += ["",
            "「留給黑洞先生」這條路再分兩種：`fedCount` ≥ 1 時他吃不下（那塊麵包會一直放在桌上），",
            "`fedCount` = 0 時他吃得下。前六天每一次「餵他」都在花掉他的胃，帳單開在最後一天。", ""]

p = pathlib.Path.home() / "glitch-vn/docs/mechanics.md"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(out), encoding="utf-8")
print(f"寫好 {p}（{len(out)} 行）")
