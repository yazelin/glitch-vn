#!/usr/bin/env python3
"""掃出《調查篇》設計文件裡所有的變數，列成一張帳，並抓出命名衝突。

**為什麼要工具不要手寫清單**：變數散在六份以上的設計文件裡，
而且每寫一批橋段就會多幾個。手寫的那份第二天就過期了。

抓兩類問題：
  一、同一個東西兩種寫法（see_noah 與 clue_see_noah）
  二、只出現一次的（很可能是打錯字，或者是誰隨手發明沒有登記的）

    python3 tools/vars.py            # 印帳
    python3 tools/vars.py --check    # 只有衝突才印，有衝突就 exit 1（給 CI 用）
    python3 tools/vars.py --cards    # 比對兩張插件卡跟設計文件有沒有走鐘

--cards 抓的是**實作跟設計慢慢分家**這件事：卡片裡的地點代號、線索代號
是寫死在 HTML 裡的，設計文件改了不會有人記得回去改卡片，而且不會報錯。
"""
import collections, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = sorted(ROOT.glob("design/調查篇*.md"))

# 反引號裡的識別字。範本（met_<誰>）與純中文不算。
PAT = re.compile(r"`([a-z][a-z0-9_]*(?:_[一-鿿0-9x]+)?)`")

# 地點代號不是變數（它們是 dest 的值）。單獨列一組，不進「其他旗標」。
# 板上的十二個目的地。**貓草家不在裡面**：trust 3 那五個私人地方是
# 「場景不是地點」（設計文件一之三），在原本那個地點裡多開一段。
LOC = {"lobby", "roof", "street", "busstop", "metro", "store", "parts",
       "laundry", "figure", "studio", "booth", "tower14"}
# 程式識別字與 Larch 的欄位名，掃到了也不是這款的狀態。
IGNORE = {"novelkit", "to_speech", "values", "variables", "who", "face", "speaker",
          "remote", "choices", "cids", "branch", "emotion", "scene", "talk", "narrate",
          "say", "boardJump", "miniGame", "trust", "clue_", "met_", "trust_", "see_",
          "deadend_", "note_", "weather", "breakfast"}

GROUPS = [
    ("地點", re.compile("^(" + "|".join(sorted(LOC)) + ")$")),
    ("核心狀態", re.compile(r"^(day|slot|dest|here|unlocked|met)$")),
    ("關係",     re.compile(r"^(trust_|met_|noah_stage$)")),
    ("線索",     re.compile(r"^(clue_|see_)")),
    ("筆記",     re.compile(r"^(notes|note_)")),
    ("死路",     re.compile(r"^deadend_")),
    ("其他旗標", re.compile(r".")),
]


def group_of(name):
    for label, pat in GROUPS:
        if pat.search(name):
            return label
    return "其他旗標"


def scan():
    hits = collections.defaultdict(list)
    for f in DOCS:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in PAT.finditer(line):
                n = m.group(1)
                if n in IGNORE or n.endswith("_") or len(n) < 3:
                    continue
                hits[n].append((f.name, i))
    return hits


def conflicts(hits):
    """同一個東西兩種寫法。目前只抓 clue_see_x 對 see_x 這一類前綴重複。"""
    out = []
    for n in hits:
        if n.startswith("clue_see_") and n[5:] in hits:
            out.append((n, n[5:]))
        if n.startswith("clue_") and ("see_" + n[5:]) in hits and not n.startswith("clue_see_"):
            out.append((n, "see_" + n[5:]))
    return out


def cards():
    """比對 larch/cards 裡兩張卡的硬編碼跟設計文件。"""
    docs = "\n".join(f.read_text(encoding="utf-8") for f in DOCS)
    bad = 0

    board = (ROOT / "larch/cards/board.html").read_text(encoding="utf-8")
    ids = set(re.findall(r"\{id:'([a-z0-9_]+)'", board))
    print(f"調查板：{len(ids)} 個地點")
    for i in sorted(ids - LOC):
        print(f"  ★ 卡片有、LOC 沒登記：{i}"); bad += 1
    for i in sorted(LOC - ids):
        print(f"  ★ LOC 有、卡片沒畫：{i}"); bad += 1
    gates = set(re.findall(r"gate:'([a-z0-9_]+)'", board))
    for g in sorted(gates):
        if f"`{g}`" not in docs:
            print(f"  ★ 閘沒寫進設計文件：{g}"); bad += 1

    notes = (ROOT / "larch/cards/notes.html").read_text(encoding="utf-8")
    codes = set(re.findall(r"\['((?:clue|see|name)_[a-z0-9]+)'", notes))
    print(f"調查筆記：{len(codes)} 個代號")
    for c in sorted(codes):
        if c.startswith("name_"):
            continue          # 六個 ID 的代號是卡片自己的，設計文件不列
        if f"`{c}`" not in docs:
            print(f"  ★ 代號沒寫進設計文件：{c}"); bad += 1
    # 反向：設計文件有的 see_* 卡片要畫得出來，不然玩家永遠看不到那一份目擊
    for c in sorted(set(re.findall(r"`(see_[a-z]+)`", docs))):
        if c not in codes and c != "see_zero":   # see_zero 是拒答，本來就沒有內容
            print(f"  ★ 設計文件有、筆記卡沒畫：{c}"); bad += 1

    print("\n卡片跟設計對得起來" if not bad else f"\n★ {bad} 處對不起來")
    sys.exit(1 if bad else 0)


def main():
    check = "--check" in sys.argv
    hits = scan()
    bad = conflicts(hits)
    lonely = sorted(n for n, v in hits.items() if len(v) == 1)

    if not check:
        by = collections.defaultdict(list)
        for n, v in hits.items():
            by[group_of(n)].append((n, v))
        print(f"掃了 {len(DOCS)} 份設計文件，{len(hits)} 個變數\n")
        for label, _ in GROUPS:
            rows = sorted(by.get(label, []))
            if not rows:
                continue
            print(f"── {label}（{len(rows)}）")
            for n, v in rows:
                where = ", ".join(sorted({f.replace("調查篇", "").replace(".md", "").strip("-") or "本篇"
                                          for f, _ in v}))
                print(f"  {n:24s} {len(v):3d} 次　{where}")
            print()

    if bad:
        print("★ 命名衝突（同一個東西兩種寫法）")
        for a, b in bad:
            print(f"   {a}　與　{b}")
    lonely = [n for n in lonely if n not in LOC]
    if lonely and not check:
        print(f"只出現一次的（{len(lonely)} 個，可能是打錯字或沒登記的）")
        print("   " + "　".join(lonely))
    if check:
        print("沒有命名衝突" if not bad else "")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if "--cards" in sys.argv:
        cards()
    else:
        main()
