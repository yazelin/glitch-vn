#!/usr/bin/env python3
"""產「立繪姿勢表」design/調查篇-立繪姿勢.tsv：程式規則（larch/inv/poses.py）只負責提案，人看表決定。

    python3 tools/pose_table.py --board <線上版子快照 或 專案備份 json>

欄位：卡、段落、誰、提案、觸發、審閱、決定、全文。
- 提案：規則算出來的；"base" 是基本立繪。
- 共用卡（同一張卡被好幾個段落走到）只能一種姿勢：取各段落提案裡最多的非基本姿勢，審閱欄標出各段落的提案。
- 審閱／決定：重跑會**保留舊表裡已填的決定**（用「卡＋誰」對），審閱欄若舊表有字也保留。
apply_poses.py 讀這份表：決定欄有值用決定，沒有用提案。
"""
import argparse, csv, json, pathlib, sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "larch/inv")); sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "larch"))
import poses as P
OUT = ROOT / "design/調查篇-立繪姿勢.tsv"
FIELDS = ["卡", "段落", "誰", "提案", "觸發", "審閱", "決定", "全文"]


def load_board(path):
    j = json.loads(pathlib.Path(path).read_text(encoding="utf-8")); j = j.get("project", j)
    return next(b for b in j["boards"] if b["id"] == "board-main") if "boards" in j else j.get("board", j)


def build(board):
    import sim as S
    import apply_poses as A
    seg_label = {r["segment"]: (r.get("label") or r["section"]) for r in S.rules}
    lab_of = {}
    for e in board["edges"]:
        v = (e.get("data", {}).get("condition") or {}).get("value")
        if v in seg_label:
            lab_of[e["target"]] = seg_label[v]
    for n in board["nodes"]:
        if n["data"].get("type") == "interrupt":
            lab_of[n["id"]] = n["data"].get("title")
    votes = defaultdict(list); info = {}
    for cards in A.segments_of(board):
        label = lab_of.get(cards[0]["id"], "?"); cur = {}
        for n in cards:
            d = n["data"]
            if d.get("type") != "dialogue":
                continue
            why = {}; cur = P.pose_of_card(d, cur, why)
            for a in (d.get("stage") or {}).get("actors") or []:
                who = P.who_of_name(a.get("name"))
                if not who:
                    continue
                pose = cur.get(who) if (who, cur.get(who)) in P.FILES else "base"
                votes[(n["id"], who)].append((label, pose, why.get(who)))
                if (n["id"], who) not in info:
                    lines = d.get("dialogueLines") or [{"speaker": d.get("speaker"), "text": d.get("text")}]
                    info[(n["id"], who)] = " ／ ".join(f"{L.get('speaker') or '旁白'}：{(L.get('text') or '').replace(chr(10), ' ')}" for L in lines)
    rows = []
    for (cid, who), vs in votes.items():
        poses = [p for _, p, _ in vs]
        non_base = [p for p in poses if p != "base"]
        pick = Counter(non_base).most_common(1)[0][0] if non_base else "base"
        if pick == "base" and len(set(poses)) == 1:
            continue                       # 從頭到尾都是基本立繪的不列
        trig = next((w for l, p, w in vs if p == pick and w), None) or ("（沿用前一張）" if pick != "base" else "（基本）")
        note = ""
        if len(vs) > 1 and len(set(poses)) > 1:
            note = "共用卡：" + "、".join(f"{l}→{p}" for l, p, _ in vs)
        rows.append({"卡": cid, "段落": vs[0][0], "誰": who, "提案": pick, "觸發": trig, "審閱": note, "決定": "", "全文": info[(cid, who)]})
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--board", required=True); a = ap.parse_args()
    old = {}
    if OUT.exists():
        for r in csv.DictReader(open(OUT, encoding="utf-8"), delimiter="\t"):
            old[(r["卡"], r["誰"])] = r
    rows = build(load_board(a.board))
    for r in rows:
        o = old.get((r["卡"], r["誰"]))
        if o:
            r["決定"] = o.get("決定", "")
            if o.get("審閱") and o["審閱"] != "OK" and not r["審閱"]:
                r["審閱"] = o["審閱"]
        r["審閱"] = r["審閱"] or "OK"
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t"); w.writeheader(); w.writerows(rows)
    c = Counter(r["決定"] or r["提案"] for r in rows)
    print(f"{len(rows)} 列 → {OUT.relative_to(ROOT)}；最終（決定優先）", dict(c))
    for r in rows:
        if r["審閱"] != "OK" or r["決定"]:
            print(f"  {r['卡']:<9}{r['誰']:<4}提 {r['提案']:<7}決定 {r['決定'] or '-':<7}{r['審閱'][:60]}")


if __name__ == "__main__":
    main()
