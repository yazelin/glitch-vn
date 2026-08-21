#!/usr/bin/env python3
"""一個指令跑完所有檢查。改完劇本跑這支就好。

檢查:
  1. 每塊板子走遍所有玩法 —— 抓斷線、環、只有條件出線沒有預設的卡
  2. 跨板跳躍的目標板與目標卡都存在
  3. 代名詞規則
  4. 有沒有卡片在動不存在的變數,或動錯型別(文字變數做加法)

離開碼非 0 代表有問題。
"""
import json, pathlib, subprocess, sys

T = pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable, str(T / "pull.py")], check=True, stdout=subprocess.DEVNULL)
P = json.load(open(T.parent / "backup/project.json"))
# 舊版（board-dayN）跟新前提版（board-v2-dayN）兩條線都要驗。
# 線上跑的是 activeBoardId 那一條，另一條先建好放著對照。
DAYS = sorted([b for b in P["boards"] if "day" in b["id"] and b["id"].startswith("board-")],
              key=lambda b: (1 if "v2" in b["id"] else 0, int(b["id"].split("day")[-1])))
bad = []

print("── 玩法模擬 ──")
for b in DAYS:
    r = subprocess.run([sys.executable, str(T / "sim_board.py"), b["id"]],
                       capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if "模擬玩法" in l]
    prob = [l for l in r.stdout.splitlines() if "問題" in l]
    print(f"  {b['name']:22}{line[0].strip() if line else '沒有輸出'}")
    for p_ in prob:
        print(f"      ★ {p_.strip()}"); bad.append(f"{b['id']}: {p_.strip()}")

print("── 接線 ──")
# 模擬器只驗「從起點走得到」。斷頭的邊、指向不存在的卡、孤島、沒有保底的出口
# 它都看不見——因為那些東西本來就走不到,不會出現在「走過的卡」裡。
r = subprocess.run([sys.executable, str(T / "check_wiring.py")],
                   capture_output=True, text=True)
for line in r.stdout.strip().splitlines():
    print("  " + line)
if r.returncode:
    bad.append("接線有問題")

print("── 跨板跳躍 ──")
ids = {x["id"] for x in P["boards"]}
for b in P["boards"]:
    for n in b["nodes"]:
        d = n["data"]
        if d.get("type") != "boardJump": continue
        tb, tn = d.get("jumpBoardId"), d.get("jumpNodeId")
        ok = tb in ids and any(m["id"] == tn for x in P["boards"] if x["id"] == tb for m in x["nodes"])
        print(f"  {b['id']:14} -> {tb}/{tn} {'' if ok else '★ 斷了'}")
        if not ok: bad.append(f"{b['id']} 的跳躍接到不存在的 {tb}/{tn}")

print("── 變數 ──")
V = {v["name"]: v for v in P["variables"]}
for b in P["boards"]:
    for n in b["nodes"]:
        for op in n["data"].get("variableOps") or []:
            v = op["variable"]
            if v not in V:
                bad.append(f"{n['id']} 動了不存在的變數 {v}"); print(f"  ★ {bad[-1]}")
            elif op["kind"] in ("add",) and V[v]["type"] not in ("number", "int", "float"):
                bad.append(f"{n['id']} 對文字變數 {v} 做加法"); print(f"  ★ {bad[-1]}")
        iv = n["data"].get("inputVariable")
        if iv and iv not in V:
            bad.append(f"{n['id']} 寫進不存在的變數 {iv}"); print(f"  ★ {bad[-1]}")
# 用到 = 被寫、被填、被邊條件讀、或被台詞用 {{}} 引用。前兩項算漏了會誤判成死變數,
# 差點害我刪掉 11 個還活著的。
written, read = set(), set()
for b in P["boards"]:
    for n in b["nodes"]:
        for op in n["data"].get("variableOps") or []: written.add(op["variable"])
        if n["data"].get("inputVariable"): written.add(n["data"]["inputVariable"])
        txt = json.dumps(n["data"], ensure_ascii=False)
        for v in V:
            if "{{" + v + "}}" in txt: read.add(v)
    for e in b["edges"]:
        c = (e.get("data") or {}).get("condition")
        if c: read.add(c["variable"])
ghost = sorted(read - written)      # 讀得到但沒人寫 —— 那條分支永遠不會成立
dead = sorted(set(V) - written - read)
for v in ghost:
    bad.append(f"變數 {v} 有人讀卻沒人寫，靠它的分支永遠不會成立"); print(f"  ★ {bad[-1]}")
print(f"  沒人用的變數 {len(dead)} 個：{'、'.join(dead) or '無'}")

print("── 空卡片 ──")
# 空 text 的對話卡在播放器裡是一個空的對話框,玩家要點過去。用空卡當匯流點很順手,
# 但玩起來是一格莫名其妙的停頓。Day 3 改成探索日的時候踩過。
blanks = []
for b in DAYS:
    for n in b["nodes"]:
        d = n["data"]
        if d.get("type") in (None, "dialogue") and not (d.get("text") or "").strip():
            blanks.append(f'{b["id"]}／{n["id"]}')
for x in blanks[:8]:
    print(f"  ★ 空的對話卡：{x}")
if blanks:
    bad.append(f"{len(blanks)} 張空的對話卡")
else:
    print("  沒有空的對話卡")

print("── 中文寫作（speak-tw）──")
# 刻意保留的句子。speak-tw 的 speak-tw-ok 標記加不到 Larch 卡片上,所以放這裡,
# 每一條都要寫清楚為什麼 —— 不寫理由的例外一律不收。
ALLOW = {
    "這不是 Bug，是 Feature":
        "設定裡明列的口頭禪（persona.json 的 Catchphrases），不是修辭。"
        "仿造的變體（「這可不是系統故障，是…」那種）不在例外內",
    "……不是那邊，是這邊":
        "Day 5 開場的夢話。這是劇情碎片(她夢裡在指某個方向),不是拿來製造洞見感的修辭",
}
dump = T.parent / "docs/script.txt"
with open(dump, "w") as f:
    for b in DAYS:
        f.write(subprocess.run([sys.executable, str(T / "dump_board.py"), b["id"]],
                               capture_output=True, text=True).stdout)
r = subprocess.run(["speak-tw", str(dump)], capture_output=True, text=True)
hits = [l.strip() for l in r.stdout.splitlines() if ":" in l and l.startswith("    ")]
real = [h for h in hits if not any(a in h for a in ALLOW)]
for h in real: print(f"  ★ {h}")
if real: bad.append(f"speak-tw {len(real)} 處")
print(f"  {len(hits)} 處命中，{len(hits) - len(real)} 處是登記過的例外，剩 {len(real)} 處要改")

print("── 代名詞 ──")
r = subprocess.run([sys.executable, str(T / "check_pronouns.py")], capture_output=True, text=True)
print("  " + r.stdout.strip().replace("\n", "\n  "))
if r.returncode: bad.append("代名詞有問題")

print()
if bad:
    print(f"★ {len(bad)} 個問題"); sys.exit(1)
print("全部通過。")
