#!/usr/bin/env python3
"""把《調查篇》設計文件裡的台詞解析成卡片結構。**這一支不碰 Larch。**

為什麼要解析而不是手抄：定稿散在六份檔案、三百多張卡，
手抄一次要好幾天，而且設計文件還在改，抄完隔天就過期。
設計文件是事實來源，這支負責把它讀成資料。

    python3 larch/inv/parse.py              # 印摘要
    python3 larch/inv/parse.py --json out.json
    python3 larch/inv/parse.py --file 調查篇-橋段2   # 只看一份
    python3 larch/inv/parse.py --show 3             # 印前三張卡的內容

**認得的格式**（照既有定稿寫出來的，不是我發明的）：

    **旁白**（`scene: store`，深夜）      ← 旁白卡，可帶場景與時段
    > 兩點十分。
    > 冰櫃的壓縮機還在響。

    ──                                   ← 換卡

    **talk**（貓草／玩家）                 ← 多講者裝同一張
    > *他先開口。*                        ← 斜體＝舞台指示，不進配音
    > **貓草**：站前那家在出清。

    **玩家**（筆記）                       ← 筆記卡
    > 深夜的便利商店。

    **→ `open_figure` ← true**            ← 變數寫入，掛在前一張卡上
"""
import argparse, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
# 作廢與非台詞的檔案不解析。第一天的初稿已被定稿取代（定稿檔開頭寫明），
# 兩份都讀會把同一場算兩次。
OBSOLETE = {"調查篇-第一天"}
DOCS = [d for d in sorted(ROOT.glob("design/調查篇*.md"))
        if d.stem not in OBSOLETE]

# 卡頭：**旁白**（`scene: store`，深夜） / **talk**（貓草／玩家） / **玩家**（筆記）
HEAD = re.compile(r"^\*\*(旁白|talk|玩家|特寫卡)\*\*(?:（(.*?)）)?\s*$")
SCENE = re.compile(r"`scene:\s*([a-z_0-9]+)`")
SLOT = re.compile(r"(上午|下午|晚上|深夜)")
BREAK = re.compile(r"^──+\s*$")
# > **貓草**：台詞
LINE_SPK = re.compile(r"^>\s*\*\*(.+?)\*\*[：:]\s*(.*)$")
# > *舞台指示*
LINE_DIR = re.compile(r"^>\s*\*(.+)\*\s*$")
LINE_ANY = re.compile(r"^>\s?(.*)$")
# **→ `var` ← true** 或 **→ `met_貓草` ＋1**
VAR = re.compile(r"\*\*→\s*`([^`]+)`\s*(?:←\s*(\S+)|＋\s*(\d+))")


def parse_file(path):
    cards, cur, problems = [], None, []
    lines = path.read_text(encoding="utf-8").split("\n")
    scene = slot = None

    def flush():
        nonlocal cur
        if cur and cur["lines"]:
            cards.append(cur)
        cur = None

    for i, ln in enumerate(lines, 1):
        m = HEAD.match(ln)
        if m:
            flush()
            kind, meta = m.group(1), m.group(2) or ""
            if s := SCENE.search(meta):
                scene = s.group(1)
            if t := SLOT.search(meta):
                slot = t.group(1)
            cur = {"kind": {"旁白": "narrate", "talk": "talk",
                            "玩家": "note", "特寫卡": "plate"}[kind],
                   "scene": scene, "slot": slot, "meta": meta,
                   "lines": [], "vars": [], "file": path.stem, "line": i}
            continue
        if BREAK.match(ln):
            flush()
            continue
        if v := VAR.search(ln):
            tgt = cards[-1] if cards else None
            if tgt is None:
                problems.append(f"{path.stem}:{i} 變數寫入前面沒有卡片")
            else:
                tgt["vars"].append({"name": v.group(1),
                                    "set": v.group(2), "add": v.group(3)})
            continue
        if cur is None:
            continue
        if not ln.startswith(">"):
            # 引言區塊結束
            if ln.strip() == "":
                continue
            flush()
            continue
        if (s := LINE_SPK.match(ln)):
            cur["lines"].append({"speaker": s.group(1), "text": s.group(2)})
        elif (d := LINE_DIR.match(ln)):
            cur["lines"].append({"speaker": None, "text": d.group(1),
                                 "direction": True})
        else:
            t = LINE_ANY.match(ln).group(1).strip()
            if t:
                cur["lines"].append({"speaker": None, "text": t})
    flush()
    return cards, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--file")
    ap.add_argument("--show", type=int, default=0)
    a = ap.parse_args()

    docs = [d for d in DOCS if not a.file or a.file in d.stem]
    allc, allp = [], []
    print(f"{'檔案':30s} {'卡':>5} {'旁白':>5} {'對話':>5} {'筆記':>5} {'變數':>5}")
    for d in docs:
        cards, probs = parse_file(d)
        allc += cards
        allp += probs
        k = lambda t: sum(1 for c in cards if c["kind"] == t)
        nv = sum(len(c["vars"]) for c in cards)
        print(f"{d.stem:30s} {len(cards):5d} {k('narrate'):5d} {k('talk'):5d} "
              f"{k('note'):5d} {nv:5d}")
    print(f"{'合計':30s} {len(allc):5d}")

    spk = {}
    for c in allc:
        for l in c["lines"]:
            if l.get("speaker"):
                spk[l["speaker"]] = spk.get(l["speaker"], 0) + 1
    print("\n講者（前十）：", "、".join(
        f"{w} {n}" for w, n in sorted(spk.items(), key=lambda x: -x[1])[:10]))
    scenes = sorted({c["scene"] for c in allc if c["scene"]})
    print("抓到的場景代號：", "、".join(scenes) or "（無）")

    if a.show:
        for c in allc[:a.show]:
            print(f"\n--- {c['file']}:{c['line']} {c['kind']} "
                  f"scene={c['scene']} slot={c['slot']}")
            for l in c["lines"]:
                pre = f"{l['speaker']}：" if l.get("speaker") else (
                    "（指示）" if l.get("direction") else "")
                print("   ", pre + l["text"][:60])
            for v in c["vars"]:
                print("    →", v)

    if allp:
        print(f"\n解析問題 {len(allp)} 條：")
        for p in allp[:20]:
            print("  ・", p)
    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps(allc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n寫出 {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
