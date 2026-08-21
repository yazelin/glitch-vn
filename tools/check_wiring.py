#!/usr/bin/env python3
"""接線檢查。模擬器只驗「從起點走得到」，這一支驗圖本身有沒有壞。

sim_board 走得到 ≠ 線接好了。走不到的東西它會報，但底下這些它看不見：
  * 邊指向不存在的卡（斷頭）
  * 邊的來源不存在
  * 沒有任何入邊的卡（孤島）——不在起點上就永遠不會出現
  * 沒有任何出邊的卡（死路）——玩家點下去之後畫面就停在那裡
  * 選擇卡的某個選項沒有出線——玩家點了沒反應
  * 邊的 sourceHandle 指到不存在的選項
  * 重複的邊 id
  * 同一個出口全部都有條件、沒有預設線——條件都不成立就卡住

素材庫那塊板也一起檢查（它不是入口，但它還在專案裡）。
"""
import collections, json, pathlib, sys, urllib.request

K = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
P = "project-e14f9260-e4c0-4ce7-9d2d-70203cdec591"
d = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://larch.yapiflow.com/api/agent/projects/{P}",
    headers={"Authorization": f"Bearer {K}"}), timeout=120))

ENDS = ("boardJump",)          # 這些型別本來就不用出邊
# 刻意的終點。新增的死路一律報錯——這裡沒登記就是接漏了。
TERMINALS = {"d7-fin", "end-common-3", "d7-f9"}
bad = []
for b in d["boards"]:
    ids = {n["id"] for n in b["nodes"]}
    N = {n["id"]: n for n in b["nodes"]}
    out = collections.defaultdict(list)
    inc = collections.Counter()
    eids = collections.Counter()
    for e in b["edges"]:
        eids[e.get("id")] += 1
        if e["source"] not in ids:
            bad.append((b["id"], f'邊的來源不存在：{e["source"]} → {e["target"]}'))
            continue
        if e["target"] not in ids:
            bad.append((b["id"], f'邊指向不存在的卡：{e["source"]} → {e["target"]}'))
            continue
        out[e["source"]].append(e)
        inc[e["target"]] += 1
    for eid, c in eids.items():
        if c > 1:
            bad.append((b["id"], f"重複的邊 id：{eid} ×{c}"))

    starts = [n["id"] for n in b["nodes"] if n["data"].get("start")]
    for n in b["nodes"]:
        nid, dd = n["id"], n["data"]
        t = dd.get("type")
        if not inc[nid] and nid not in starts:
            bad.append((b["id"], f"孤島（沒有入邊）：{nid}"))
        es = out[nid]
        if not es and t not in ENDS and nid not in TERMINALS:
            bad.append((b["id"], f"死路（沒有出邊）：{nid}"))
        if t == "choice":
            n_opt = len(dd.get("choices") or [])
            shared = dd.get("choiceMode") == "shared"
            handles = {e.get("sourceHandle") for e in es}
            for i in range(n_opt):
                h = "choice-all" if shared else f"choice-{i}"
                if h not in handles:
                    bad.append((b["id"], f"選項沒有出線：{nid} 的第 {i+1} 項"))
            for h in handles:
                if h and h.startswith("choice-") and h != "choice-all":
                    if not h[7:].isdigit() or int(h[7:]) >= n_opt:
                        bad.append((b["id"], f"出口指到不存在的選項：{nid} 的 {h}"))
        # 同一個出口全部有條件、沒有保底
        by_h = collections.defaultdict(list)
        for e in es:
            by_h[e.get("sourceHandle") or "right"].append(e)
        for h, group in by_h.items():
            if group and all((e.get("data") or {}).get("condition") for e in group):
                bad.append((b["id"], f"沒有保底：{nid} 的 {h} 全部都有條件，"
                                     f"條件都不成立就卡住"))

print(f"檢查 {len(d['boards'])} 塊板、"
      f"{sum(len(b['nodes']) for b in d['boards'])} 張卡、"
      f"{sum(len(b['edges']) for b in d['boards'])} 條邊")
by_board = collections.Counter(x[0] for x in bad)
if not bad:
    print("接線全部正常。")
for bid, msg in bad:
    print(f"  ★ [{bid.replace("board-","")}] {msg}")
if bad:
    print("\n" + "　".join(f"{k[-12:]} {v}" for k, v in by_board.items()))
sys.exit(1 if bad else 0)
