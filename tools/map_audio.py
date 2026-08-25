#!/usr/bin/env python3
"""把小說站的段落對回配音檔，產生 design/audiobook.json。

小說正文跟 VN 台詞幾乎逐字相同，差別在分段與標點：小說用「」包對白、
留言寫成 `> **貓草**：…`，而 VN 把同一段話拆成幾個參數、把講者另外存。
所以**不能直接字串相等**，要正規化之後照順序對齊。

一對多與多對一都要處理：
  一張留言卡三則訊息 → 小說是三段（一個音檔配三段）
  小說一段長旁白     → VN 拆成兩個參數但仍是一張卡（一個音檔配一段）

輸出是每章一串「步驟」，每一步 = 要一起反白的段落編號 + 要播的網址。

用法：python3 tools/map_audio.py
"""
import json, pathlib, re, runpy, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[^\w]", "", s)


def paragraphs(md):
    """小說的段落。標題不算，引用與粗體記號拿掉，留言的講者前綴也拿掉。"""
    out = []
    for p in md.split("\n\n"):
        p = p.strip()
        if not p or p.startswith("#"):
            continue
        out.append(p)
    return out


def bare(p):
    """段落拿去比對用的形態。

    **小說的對白帶著說話者標記，VN 沒有。** 小說寫「少來。」她說。「那時候你連
    抖內按鈕在哪都找不到。」，VN 是兩句台詞，中間那個「她說」把字串接不起來
    ——第七章有四十一段就是這樣漏掉的。有引號的段落只取引號裡的內容。
    """
    t = re.sub(r"^>\s*", "", p, flags=re.M)
    t = t.replace("**", "")
    # 留言的「貓草：」講者前綴。VN 把講者另外存，文字裡沒有它。
    t = re.sub(r"^[^：\n]{1,6}：", "", t, flags=re.M)
    # **只有整段以「開頭才算對白。** 敘述裡引用一句話（理由是「兩邊的粉絲都
    # 可以參與」）也含引號，把它當對白處理會只剩引號內容，整段就對不上了
    # ——第三章有十五段是這樣壞掉的。
    if t.lstrip().startswith("「"):
        inner = re.findall(r"「([^」]*)」", t)
        if inner:
            return norm("".join(inner))
    return norm(t)


def vn_lines():
    """VN 那一側，照章、照卡片順序。"""
    import novelkit as nk, voice as V
    built = {}
    nk.Chapter.push = lambda self, s: built.setdefault(self.bid, self.nodes)
    nk.ensure_characters = lambda: {n: f"c-{n}" for n in list(nk.SPRITE) + ["旁白"]}

    class _A(dict):
        def __missing__(self, k): return f"x/{k}"
    nk.A = _A(nk.A)
    nk.VOICE_URLS = {}

    per = {}
    for f in sorted((ROOT / "larch").glob("build_ch0*.py")):
        ch = int(f.stem[-2:])
        before = set(built)
        runpy.run_path(str(f), run_name="__main__")
        rows = []
        for bid in [b for b in built if b not in before]:
            for n in built[bid]:
                d = n["data"]
                if (d.get("type") or "dialogue") != "dialogue":
                    continue
                # **算鍵要用 speakText，跟 gen_voice 一致。** 畫面上顯示的跟
                # 要唸的不一定一樣（「貓草已離線。」畫面要有、聲音不要），
                # 用 text 算出來的鍵會對到「會把系統訊息唸出來」的那一版舊檔。
                items = ([(l.get("speaker"), l.get("text"), l.get("emotion"))
                          for l in d.get("dialogueLines") or []]
                         or [(d.get("speaker"),
                              d.get("speakText") or d.get("text"),
                              d.get("emotion"))])
                for sp, tx, em in items:
                    if sp and tx and tx.strip():
                        rows.append((norm(tx), V.key(sp, tx, em or None), tx))
        per[ch] = rows
    return per


def align(paras, lines):
    """照順序對齊。回傳 [(段落編號們, 代號)]。

    **不可以一路線性掃下去。** 那樣一旦錯位就再也接不回來（實測只對上 4%，
    比不對齊還糟）。改成在往前一小段的範圍內找錨點：對不上就跳過這一段，
    下一段還有機會重新咬住。
    """
    W = 12                       # 往前找幾句
    steps, j = [], 0
    i = 0
    while i < len(paras):
        a = bare(paras[i])
        if not a:
            i += 1
            continue
        hit = None
        for d in range(min(W, len(lines) - j)):
            b = lines[j + d][0]
            if a == b:
                hit = ("eq", d); break
            if b and a.startswith(b):
                hit = ("many_lines", d); break
            if a and b.startswith(a):
                hit = ("many_paras", d); break
        if hit is None:
            i += 1
            continue
        kind, d = hit
        j += d                                   # 跳過中間對不上的 VN 句子
        if kind == "eq":
            steps.append(([i], lines[j][1])); i += 1; j += 1
        elif kind == "many_lines":               # 一段小說 = 好幾句 VN
            got = ""
            while j < len(lines) and len(got) < len(a) and a.startswith(got + lines[j][0]):
                got += lines[j][0]
                steps.append(([i], lines[j][1])); j += 1
            i += 1
        else:                                    # 一句 VN = 好幾段小說
            b = lines[j][0]
            got, idx = "", []
            while i < len(paras) and len(got) < len(b) and b.startswith(got + bare(paras[i])):
                got += bare(paras[i]); idx.append(i); i += 1
            steps.append((idx or [i], lines[j][1])); j += 1
    return steps


def main():
    urls = json.loads((ROOT / "art/voice/urls.json").read_text(encoding="utf-8"))
    per = vn_lines()
    out, tot_p, tot_s = {}, 0, 0
    for ch in sorted(per):
        # **第八章是片尾，沒有小說正文。** 不跳過的話這裡會 FileNotFoundError，
        # 而且整支腳本從此跑不完 —— 對應表就再也沒有重生過，
        # 有聲書會一直指著舊的音檔（2026-08 抓到 44 步是舊的）。
        src = ROOT / f"novel/ch{ch:02d}.md"
        if not src.exists():
            print(f"第{ch}章　沒有小說正文（片尾），跳過")
            continue
        md = src.read_text(encoding="utf-8")
        paras = paragraphs(md)
        steps = align(paras, per[ch])
        rows = [{"paras": ps, "url": urls[k]} for ps, k in steps if k in urls]
        out[str(ch)] = rows
        covered = len({p for r in rows for p in r["paras"]})
        tot_p += len(paras); tot_s += covered
        print(f"第{ch}章　段落 {len(paras):3d}　配到音的 {covered:3d}"
              f"　({covered/len(paras)*100:.0f}%)　步驟 {len(rows)}")
    p = ROOT / "design/audiobook.json"
    p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"\n{p}　全書 {tot_s}/{tot_p} 段有聲音（{tot_s/tot_p*100:.0f}%）")


if __name__ == "__main__":
    main()
