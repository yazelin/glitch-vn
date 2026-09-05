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
# 卡頭有兩類：固定的四種，以及**單一講者用自己的名字當卡頭**
# （格莉奇全作都是這種，她只在螢幕與喇叭上出現，括號裡帶 `remote`）。
GENERIC_HEADS = {"台詞", "排卡註", "配音", "接線", "變數"}
# 錄音／背包是建置巨集，不是台詞卡（見 design/調查篇-背包與謎題.md 三之三、三之四）：
#   **錄音**（保全）            → 有 rec_ok 才出現的選擇卡「開錄音機／不開」＋取得道具卡。
#                                引言裡帶講者的行是他對錄音機的反應，沒講者的一行是錄到的那一句（道具備註）。
#   **背包**（錄音・保全）       → 打開背包卡；挑中括號裡那一件才接下一張，否則直接回調查板。
FIXED = ["旁白", "talk", "玩家", "特寫卡", "錄音", "背包"]
CAST = ["格莉奇", "黑洞先生", "貓草", "鐵塔", "0x", "斑比", "諾亞",
        "管理員", "店員", "保全", "材料行老闆", "櫃檯", "住戶",
        "路人", "路人乙", "高中生", "阿姨", "送貨的", "發傳單的", "上班族"]
HEAD = re.compile(r"^\*\*(" + "|".join(FIXED + CAST) + r")\*\*(?:（(.*?)）)?\s*$")
SCENE = re.compile(r"`scene:\s*([a-z_0-9]+)`")
SLOT = re.compile(r"(上午|下午|晚上|深夜)")
BREAK = re.compile(r"^──+\s*$")
# > **貓草**：台詞
LINE_SPK = re.compile(r"^>\s*\*\*(.+?)\*\*[：:]\s*(.*)$")
# > *舞台指示*
LINE_DIR = re.compile(r"^>\s*\*(.+)\*\s*$")
LINE_ANY = re.compile(r"^>\s?(.*)$")
# **→ `var` ← true** 或 **→ `met_貓草` ＋1**
# 段落層的 metadata。這些不是卡片，是**建置真正需要的東西**：
# 觸發決定這一段什麼時候播（＝邊的條件），變數決定它寫什麼。
# 只抓文字，判讀留給下一層，因為寫法還沒統一（「`day >= 4`」與「第四天以後」並存）。
META = re.compile(r"^\*\*(觸發|變數|線索|問誰|地點・時段|給什麼|新資訊)\*\*[：:]?\s*(.*)$")
PERSONS = ["管理員", "諾亞", "斑比", "鐵塔", "0x", "貓草", "便利商店店員", "材料行老闆"]
# 含 L1：橋段的每一場都是 L1，而且標題就帶地點代號與時段（`# 五、深夜的鐵塔（`store`・深夜）`）。
SECTION = re.compile(r"^(#{1,5})\s+(.*?)\s*$")
# 這些節不是台詞，是給人看的註解，可是裡面常有 `>` 引用（範例、對照），
# 不跳過的話會被當成卡片。標題含任一關鍵字就整節跳過（直到下一個同級或更高的標題）。
SKIP = ["排卡註", "觸發條件一覽", "格式", "配音", "讀音", "待拍板", "總表", "評審",
        "刪除線", "情緒", "規矩", "哪裡不可以", "這一列", "信任怎麼升", "照改的",
        "問題成立", "只接受一半", "沒抓到", "驗過的", "兩個敘述聲音", "節奏",
        "在整篇的位置", "拼起來之後", "沒有寫的", "判決", "連帶要改", "走不走得到",
        "走得到嗎", "變數", "機制", "丟掉的", "自我約束", "收尾門檻", "跟結局的接口",
        "落差", "為什麼是這一行", "缺的格子", "他在這一款裡", "他現在是誰",
        "表上那一列", "各補什麼", "我自己抓到", "判決怎麼處理", "卡數", "標點",
        "共用音檔", "為什麼一張", "不可以做的事", "自己驗過"]

VAR = re.compile(r"\*\*→\s*(?:解鎖\s*)?`([^`]+)`\s*(?:←\\s*(\\S+)|＋\\s*(\\d+))?")


def parse_file(path):
    cards, cur, problems = [], None, []
    lines = path.read_text(encoding="utf-8").split("\n")
    scene = slot = None

    def flush():
        nonlocal cur
        if cur and (cur["lines"] or cur["kind"] == "bag"):
            cards.append(cur)
        cur = None

    stack, meta_now, skip_lvl = [], {}, None   # stack = [(level, text)]
    for i, ln in enumerate(lines, 1):
        if h := SECTION.match(ln):
            flush()
            lvl, text = len(h.group(1)), h.group(2)
            stack = [(l, t) for l, t in stack if l < lvl] + [(lvl, text)]
            meta_now = {}
            # scene/slot 只在同一節內黏著。換到 L2/L3 就重設，不然 0x 那張卡
            # 會繼承上一節鐵塔的 `booth`（2026-09-05 抓到的 bug）。
            # 兩份文件的 L2 意思不同：問答矩陣的 L2 是「人」（換人＝換地點，要重設），
            # 橋段的 L2 是「同一場裡的子卡」（要繼承第一張卡頭的 scene）。
            # 所以只在 L2 標題是人名時重設。
            # L1＝橋段換場（一定換地點）；問答矩陣的 L2 是人名（換人＝換地點）。
            if lvl == 1 or (lvl == 2 and any(w in text for w in PERSONS)):
                scene = slot = None
            if skip_lvl is not None and lvl <= skip_lvl:
                skip_lvl = None
            if skip_lvl is None and any(k in text for k in SKIP):
                skip_lvl = lvl
            continue
        if skip_lvl is not None:
            continue
        if mm := META.match(ln):
            key, val = mm.group(1), mm.group(2).strip()
            meta_now[key] = (meta_now.get(key, "") + " " + val).strip()
            continue
        m = HEAD.match(ln)
        if m:
            flush()
            kind, meta = m.group(1), m.group(2) or ""
            if s := SCENE.search(meta):
                scene = s.group(1)
            if t := SLOT.search(meta):
                slot = t.group(1)
            kmap = {"旁白": "narrate", "talk": "talk",
                    "玩家": "note", "特寫卡": "plate", "錄音": "rec", "背包": "bag"}
            cur = {"kind": kmap.get(kind, "say"),
                   "speaker": None if kind in FIXED else kind,
                   # remote＝他不在這個房間，只有訊號（螢幕、喇叭、耳機）。
                   # novelkit 的 say(remote=True) 就是這個，掛大頭貼不掛立繪。
                   "remote": "remote" in meta,
                   "scene": scene, "slot": slot, "meta": meta,
                   # 段落鍵取最深一層**有意義的**標題。「台詞」「排卡註」這種每一格底下都有的
                   # 通用標題要跳過，不然 Ａ一、Ａ二、Ｃ 全被合成一段、觸發條件一起丟掉（2026-09-06 抓到）。
                   "section": next((t for _, t in reversed(stack) if t.strip() not in GENERIC_HEADS), None),
                   "headings": [t for _, t in stack],      # 由外到內
                   "trigger": dict(meta_now),
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
    print(f"{'檔案':30s} {'卡':>5} {'旁白':>5} {'對話':>5} {'獨白':>5} {'筆記':>5} {'變數':>5}")
    for d in docs:
        cards, probs = parse_file(d)
        allc += cards
        allp += probs
        k = lambda t: sum(1 for c in cards if c["kind"] == t)
        nv = sum(len(c["vars"]) for c in cards)
        print(f"{d.stem:30s} {len(cards):5d} {k('narrate'):5d} {k('talk'):5d} "
              f"{k('say'):5d} {k('note'):5d} {nv:5d}")
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
    rem = sum(1 for c in allc if c.get("remote"))
    print(f"remote 卡（只有訊號、不掛立繪）：{rem} 張")
    trig = sum(1 for c in allc if c.get("trigger", {}).get("觸發"))
    secs = len({(c["file"], c["section"]) for c in allc if c.get("section")})
    print(f"帶觸發條件的卡：{trig} 張，分佈在 {secs} 個段落")

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
