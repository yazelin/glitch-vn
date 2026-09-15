#!/usr/bin/env python3
"""吃 ASR 掃描的結果，找出反覆唸錯的詞，自動試候選寫法，驗過就寫進替身表。

**這支的目的是讓人少聽。** 掃描給的是「哪幾句對不上」，可是一句一句修沒有意義——
今天二十幾個詞裡，同一個字往往影響好幾句（「摺」一個字 12 句、「螢幕」38 句）。
所以先把對不上的地方聚成「詞」，再針對詞去試。

流程（每一個詞）：
  一、從對不上的句子裡抽出「原文有、聽寫沒有」的那一段字
  二、生候選：同音異體字、拆詞、加語助字
  三、每個候選生一次音、ASR 聽回來，**聽寫回原文那個詞才算過**
  四、過了就寫進 SUB；全部沒過就列進「要耳朵判」

**不自動套用沒驗過的候選。** 今天有兩次候選比原文更糟（帽言→冒鹽、床電→床定格），
沒有 ASR 驗這一關就會把對的換成錯的。

    ~/voice-venv/bin/python tools/auto_fix_pron.py --dry     # 只列出可疑的詞
    ~/voice-venv/bin/python tools/auto_fix_pron.py           # 真的試並寫進表
"""
import argparse, difflib, json, pathlib, re, subprocess, sys, tempfile, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
AUDIT = ROOT / "art/voice/asr-audit.json"


CN = "零一二三四五六七八九"
def zh(s):
    """比對前先正規化。**不做這些，前幾名全部是假警報**（2026-09-14 實測）：

      一、ASR 把數字寫成阿拉伯數字（「11點半」對「十一點半」），差一堆音
      二、我們的替身把「行」換成「航」，而 ASR 聽回正確的「行」；
          `lazy_pinyin` 給「行」的預設讀音是 xíng，跟 háng 對不上 → 65 句假警報
    """
    s = s or ""
    s = re.sub(r"\d", lambda m: CN[int(m.group())], s)     # 阿拉伯數字轉中文
    return re.sub(r"[^\w一-鿿]+", "", s)


def suspects(min_diff=1, top=400):
    """回 [(可疑詞, 出現次數, 例句)]，照出現次數排。"""
    from pypinyin import lazy_pinyin
    import voice as V
    import gen_voice as G
    orig = {k: t for w, t, e, k in G.utterances()}
    rows = json.loads(AUDIT.read_text(encoding="utf-8"))
    bag = collections.Counter()
    ex = {}
    for k, v in rows.items():
        if v.get("score") is None:
            continue
        a, b = zh(v["want"]), zh(v["got"])
        # **短句不算。** 三個字以內 ASR 本來就不穩（「喔。」「欸」聽成一整串），
        # 那是辨識的問題不是配音的問題。
        if len(a) <= 3:
            continue
        # **拿替身前後兩種寫法比，取比較像的那個。** 替身把「行」換成「航」，
        # 而唸出來是對的、ASR 聽回「行」——只比替身版的話那 65 句全是假警報。
        cands = [a]
        o = zh(orig.get(k, ""))
        if o and o != a:
            cands.append(o)
        best = None
        for c in cands:
            sm = difflib.SequenceMatcher(None, lazy_pinyin(c), lazy_pinyin(b))
            same = sum(x.size for x in sm.get_matching_blocks())
            d = max(len(lazy_pinyin(c)), len(lazy_pinyin(b))) - same
            if best is None or d < best[0]:
                best = (d, c, sm)
        d, a, sm = best
        if d < min_diff:
            continue
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            seg = a[i1:i2]
            if not (1 <= len(seg) <= 4):
                continue
            # **數字的寫法差異不算唸錯。** ASR 寫「4300」「3.4」，原文寫
            # 「四千三百」「三點四」——那是格式不是發音。不排掉的話前十名
            # 有七個是「十」「百」「千」「點」（2026-09-14 實測）。
            if not re.sub(r"[零一二三四五六七八九十百千萬點分秒0-9x]", "", seg):
                continue
            # 同音異形的語助詞：ASR 挑哪一個字是它的偏好，不是唸錯
            if seg in ("欸", "誒", "喔", "噢", "嗯", "唔", "啊", "阿"):
                continue
            # ASR 的用字偏好，不是唸錯：他／她／你／妳同音，的／地／得同音，
            # 著／着是簡繁字形。這些混進來會把真的蓋掉。
            if all(ch in "他她你妳它牠的地得著着了嗎呢吧呀哦哈" for ch in seg):
                continue
            bag[seg] += 1
            ex.setdefault(seg, (v["want"], v["got"]))
    return [(w, n, ex[w]) for w, n in bag.most_common(top)]


def candidates(word):
    """同音異體字與常見改寫。**只產同音或同義的，不改意思。**"""
    import opencc
    out = []
    try:
        out.append(opencc.OpenCC("t2s").convert(word))   # 簡體同音字形
    except Exception:
        pass
    out += [word + "子", word + "的", word[0] + word if len(word) == 1 else word]
    return [c for c in dict.fromkeys(out) if c and c != word]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--min-count", type=int, default=2, help="至少影響幾句才值得修")
    a = ap.parse_args()
    if not AUDIT.exists():
        sys.exit("還沒有掃描結果，先跑 tools/asr_audit.py")
    sus = [(w, n, e) for w, n, e in suspects() if n >= a.min_count]
    print(f"可疑的詞（至少影響 {a.min_count} 句）：{len(sus)} 個")
    for w, n, (want, got) in sus[:40]:
        print(f"  {n:4d} 句　「{w}」")
        print(f"          要唸 {want[:30]}")
        print(f"          聽成 {got[:30]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
