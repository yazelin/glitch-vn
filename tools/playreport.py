#!/usr/bin/env python3
"""把一批自動玩家的紀錄整理成難度數字。用法：python3 tools/playreport.py <批次目錄>

每一輪抓：走到哪個結局、幾天、出門幾次、幾條線打開了、名單上有幾條註解。
輸出一張每輪的表加一張彙總表，最後印出五個軸的分數（見 design/調查篇-難度.md）。
"""
import sys, re, json, pathlib, statistics, collections

BASE = pathlib.Path(sys.argv[1])
# 里程碑：字串出現在紀錄裡就算走到
MILE = [
    ("店員信任", "選「問店員一件事」"),
    ("洗衣店開", ("選「問店員這條街深夜還有什麼開著」", "選「問管理員這附近晚上還有什麼開著」")),
    ("洗衣店第一晚", "選「坐著等烘乾」"),
    ("工作室開", "選「問她桌上那幾張」"),
    ("斑比信任三", "選「問斑比守則本是不是她畫的」"),
    ("那面牆", "那面牆從天花板下面排到腰"),
    ("十四樓開", "→ 去 十四樓大廳"),
    ("見到 0x", "你來過六次"),
    ("貓草信任一", "貓草：三次了。"),
    ("深夜的鐵塔", "跟靠窗那個人講話"),
]
ANNOT = [("貓草家", "等級八十，他說那是看時數"), ("鐵塔", "三包喉糖，他說兩天"),
         ("0x", "兩分鐘。她記得我來過幾次"), ("斑比", "第四行是她自己"),
         ("諾亞", "我問過他。他不知道"), ("考完就刪", "帳號兩年前刪掉的")]

rows = []
for d in sorted(BASE.glob("*/")):
    t = d / "transcript.txt"
    if not t.exists():
        continue
    s = t.read_text(encoding="utf-8", errors="replace")
    pol, seed = d.name.rsplit("-", 1)
    days = [int(x) for x in re.findall(r"=== 板 第 (\d+) 天", s)]
    r = {"走法": pol, "種子": seed,
         # 收尾固定在最後一天之後，結局好壞看名單那一頁出不出來（clue_list＝看過斑比那面牆）
         "結局": "有名單" if "@Bambi_Draft3" in s else "空的最後一頁",
         "最後一天": max(days) if days else 0,
         "出門": int(m.group(1)) if (m := re.search(r"出門 (\d+) 次", s)) else 0,
         "不出門": s.count("這個深夜不出門"),
         "選過": int(m2.group(1)) if (m2 := re.search(r"選過 (\d+) 格", s)) else 0}
    for name, pat in MILE:
        pats = pat if isinstance(pat, tuple) else (pat,)
        r[name] = "○" if any(p in s for p in pats) else "—"
    r["註解"] = sum(1 for _, pat in ANNOT if pat in s)
    r["看到牆"] = r["那面牆"]
    rows.append(r)

if not rows:
    sys.exit("沒有紀錄")

cols = ["走法", "種子", "結局", "最後一天", "出門", "選過", "註解"] + [m[0] for m in MILE]
print("\t".join(cols))
for r in rows:
    print("\t".join(str(r.get(c, "")) for c in cols))

print("\n=== 彙總")
by = collections.defaultdict(list)
for r in rows:
    by[r["走法"]].append(r)
print("走法\t輪數\t有名單\t看到牆\t見到0x\t註解中位數\t出門中位數")
for pol, rs in sorted(by.items()):
    print(f"{pol}\t{len(rs)}\t{sum(1 for r in rs if r['結局']=='有名單')}"
          f"\t{sum(1 for r in rs if r['那面牆']=='○')}\t{sum(1 for r in rs if r['見到 0x']=='○')}"
          f"\t{statistics.median(r['註解'] for r in rs)}\t{statistics.median(r['出門'] for r in rs)}")

print("\n=== 每一條線有幾成的輪次走到")
for name, _ in MILE:
    n = sum(1 for r in rows if r[name] == "○")
    print(f"{name}\t{n}/{len(rows)}\t{round(100*n/len(rows))}%")
