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
DAYS = sorted([b for b in P["boards"] if b["id"].startswith("board-day")],
              key=lambda b: int(b["id"].replace("board-day", "")))
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
unused = [v for v in V if not any(
    op["variable"] == v for b in DAYS for n in b["nodes"] for op in (n["data"].get("variableOps") or []))
    and not any(n["data"].get("inputVariable") == v for b in DAYS for n in b["nodes"])]
print(f"  七天用不到的變數 {len(unused)} 個（素材庫版留下來的）：{'、'.join(unused) or '無'}")

print("── 代名詞 ──")
r = subprocess.run([sys.executable, str(T / "check_pronouns.py")], capture_output=True, text=True)
print("  " + r.stdout.strip().replace("\n", "\n  "))
if r.returncode: bad.append("代名詞有問題")

print()
if bad:
    print(f"★ {len(bad)} 個問題"); sys.exit(1)
print("全部通過。")
