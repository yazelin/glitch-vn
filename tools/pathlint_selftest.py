#!/usr/bin/env python3
"""pathlint 的負控制。跑：python3 tools/pathlint_selftest.py

檢查器最常見的壞法是**安靜地不再檢查**：規則寫錯、欄位改名、資料結構變了，
它照樣印「沒有問題」。所以七項每一項都在這裡注一個故障進板子的副本，
確認那一項真的會叫；注入前的乾淨板子則必須是綠的。

每一項只注一個故障，跑完就丟。原始的 board.json 不會被動到
（走 PATHLINT_BOARD 指到暫存目錄的副本）。

改 pathlint 的規則要順手改這裡，不然那一項等於沒在驗。
"""
import copy
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "larch/inv/out/board.json"


def run(board_path):
    """跑一次 pathlint，回傳（有幾件問題, 整段輸出）"""
    env = dict(os.environ, PATHLINT_BOARD=str(board_path))
    r = subprocess.run([sys.executable, str(ROOT / "tools/pathlint.py")],
                       capture_output=True, text=True, env=env, cwd=ROOT)
    m = re.search(r"問題 (\d+) 件", r.stdout)
    return (int(m.group(1)) if m else -1), r.stdout


# ── 七個注入。每一支收一份板子（可以改），回傳這一項預期會出現的字串 ──────


def inject_dup_label(b):
    """一、同一個地點同一個時段兩格標籤一樣，而且條件不互斥"""
    src = next(r for r in b["rules"] if r.get("label") and r.get("slots"))
    twin = copy.deepcopy(src)
    twin["section"] = "注入・複製的那一格"
    b["rules"].append(twin)          # 條件一模一樣＝不互斥
    return "重複標籤"


def inject_unreachable_value(b):
    """二、條件比對的值沒有任何一張卡設得到

    要挑一個**用 set 寫、而且不是板上累加**的變數，不然 pathlint 會在算得出上限之前
    就 continue 掉（那些是故意放過的，靜態算不出來）。
    """
    sets, adds, card_writes = set(), set(), set()
    for n in b["nodes"]:
        card_writes.update((n.get("data") or {}).get("miniGameWriteVars") or [])
        for o in ((n.get("data") or {}).get("variableOps") or []):
            (sets if o.get("kind") == "set" else adds).add(o.get("variable"))
    FREE = {"day", "slot", "inventory", "here", "met", "visited", "tries", "任一"}
    for r in b["rules"]:
        for c in r["conds"]:
            v = c["variable"]
            if c["op"] != "eq" or v in FREE or v in adds or v in card_writes:
                continue
            if v in sets:
                c["value"] = "注入・不可能的值"
                return "值對不到"
    raise SystemExit("找不到可以注入的 eq 條件")


def inject_unwritten_var(b):
    """三、條件讀的變數沒有任何地方會寫"""
    b["rules"][0]["conds"] = b["rules"][0]["conds"] + [
        {"variable": "注入_沒有人寫的變數", "op": "eq", "value": True}]
    return "沒有人寫"


def inject_edge_id_clash(b):
    """四、兩條邊撞同一個 id"""
    b["edges"][1]["id"] = b["edges"][0]["id"]
    return "邊撞 id"


def inject_missing_choice_edge(b):
    """五、選擇卡的選項數跟接出去的 choice-N 邊數對不上"""
    for i, e in enumerate(b["edges"]):
        if str(e.get("sourceHandle", "")).startswith("choice-"):
            del b["edges"][i]
            return "選項沒接好"
    raise SystemExit("板上沒有選項邊")


def inject_dropped_direction(b):
    """六、舞台指示沒進到卡上

    要挑一句**只出現在一個地方**的指示，不然刪掉一張卡上的，
    另一張還留著同一句，檢查器就抓不到（有幾場是逐字重複的）。
    """
    blob = json.dumps(b["nodes"], ensure_ascii=False)
    for n in b["nodes"]:
        dl = (n.get("data") or {}).get("dialogueLines") or []
        for i, l in enumerate(dl):
            if l.get("emotion") != "描述動作":
                continue
            key = l["text"][:14]
            if blob.count(key) != 1:
                continue
            del dl[i]
            return "指示沒進卡"
    raise SystemExit("找不到只出現一次的舞台指示")


def inject_empty_speaker(b):
    """七、講者留空字串的台詞行"""
    for n in b["nodes"]:
        dl = (n.get("data") or {}).get("dialogueLines") or []
        if dl:
            dl[0]["speaker"] = ""
            return "講者留空"
    raise SystemExit("板上沒有 dialogueLines")


def inject_bad_var_name(b):
    """八、variableOps 的名字長得不像變數

    設計稿把箭頭寫進反引號裡（`trust_斑比 ← 3`）或是註解裡引到檔名，
    解析器會把整串當變數名，那張卡真正要設的值就沒設到。
    """
    for n in b["nodes"]:
        ops = (n.get("data") or {}).get("variableOps") or []
        if ops:
            ops[0]["variable"] = ops[0]["variable"] + " ← 3"
            return "變數名怪"
    raise SystemExit("板上沒有 variableOps")


CASES = [("一、重複標籤", inject_dup_label),
         ("二、值對不到", inject_unreachable_value),
         ("三、沒有人寫", inject_unwritten_var),
         ("四、邊撞 id", inject_edge_id_clash),
         ("五、選項沒接好", inject_missing_choice_edge),
         ("六、指示沒進卡", inject_dropped_direction),
         ("七、講者留空", inject_empty_speaker),
         ("八、變數名怪", inject_bad_var_name)]


def main():
    if not SRC.exists():
        print("先跑 python3 larch/inv/build.py --out larch/inv/out/board.json")
        return 1
    clean = json.loads(SRC.read_text(encoding="utf-8"))
    fails = []
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)

        # 先確認乾淨的板子是綠的。這一關不過的話底下每一項都不算數。
        base = td / "clean.json"
        base.write_text(json.dumps(clean, ensure_ascii=False), encoding="utf-8")
        n, out = run(base)
        if n != 0:
            print(f"★ 乾淨的板子就有 {n} 件問題，先把它修綠再跑這一支：\n{out}")
            return 1
        print("乾淨的板子：0 件　○")

        for name, fn in CASES:
            b = copy.deepcopy(clean)
            want = fn(b)
            p = td / "hurt.json"
            p.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
            n, out = run(p)
            hit = [l for l in out.splitlines() if l.startswith(want)]
            ok = bool(hit)
            print(f"{name:<14} 注入後 {n:>2} 件　{'○' if ok else '★ 沒抓到'}"
                  + (f"　{hit[0][:48]}" if ok else ""))
            if not ok:
                fails.append(name)

        # 還原：同一份乾淨的板子再跑一次，確認上面那些注入沒有留下副作用
        n, _ = run(base)
        print(f"還原後：{n} 件　{'○' if n == 0 else '★'}")
        if n != 0:
            fails.append("還原")

    print(f"\n八項負控制：{len(CASES) - len([f for f in fails if f != '還原'])}/{len(CASES)} 會叫"
          + ("" if not fails else "　★ 沒過：" + "、".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
