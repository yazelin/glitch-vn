#!/usr/bin/env python3
"""排出「該聽哪幾句」，讓人不用聽一千九百句。

**排序的是證據強度，不是句子順序。** 每一層都有一個獨立的訊號：

  一、兩輪 ASR 都對不上，而且差很多  → 最可能真的唸錯
  二、這一輪變差了（上一輪對得上）    → 這次重生引入的
  三、瑕疵掃描標到的                → 頻譜異常（相位檢驗沒過，多半是誤報）
  四、替身改過內容的                → 我們動過它唸什麼，值得抽聽
  五、走 Larch 逐句的例外            → 那批沒有套替身

**排掉的噪音**（跟 auto_fix_pron 同一組，2026-09-14 量出來的）：
數字寫法、他／她、的／地／得、著／着、語助詞、三個字以內的短句。
不排掉的話前十名有七個是「十」「百」「千」「點」。

    python3 tools/triage.py              # 印清單
    python3 tools/triage.py --json out.json
"""
import argparse, collections, difflib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
CN = "零一二三四五六七八九"
NOISE = set("他她你妳它牠的地得著着了嗎呢吧呀哦哈欸誒喔噢嗯唔啊阿")


def norm(s):
    s = re.sub(r"\d", lambda m: CN[int(m.group())], s or "")
    return re.sub(r"[^\w一-鿿]+", "", s)


def diff_of(want, got, orig=None):
    """回 (差幾個音, 對不上的那幾段)。拿替身前後兩種寫法比，取比較像的。"""
    from pypinyin import lazy_pinyin
    best = None
    for cand in [x for x in (want, orig) if x]:
        a, b = lazy_pinyin(norm(cand)), lazy_pinyin(norm(got))
        sm = difflib.SequenceMatcher(None, a, b)
        same = sum(x.size for x in sm.get_matching_blocks())
        d = max(len(a), len(b)) - same
        if best is None or d < best[0]:
            best = (d, cand, sm)
    d, cand, sm = best
    segs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        seg = norm(cand)[i1:i2]
        if not seg or len(seg) > 4:
            continue
        if not re.sub(r"[零一二三四五六七八九十百千萬點分秒0-9x]", "", seg):
            continue
        if all(ch in NOISE for ch in seg):
            continue
        segs.append(seg)
    return d, segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=60)
    a = ap.parse_args()
    import gen_voice as G, voice as V
    from voice import LARCH_VOICE as LV
    cur = json.loads((ROOT / "art/voice/asr-audit.json").read_text(encoding="utf-8"))
    prevp = pathlib.Path("/tmp/claude-1000/-home-ct/7955990f-7a10-435a-ab8b-923901aff325/scratchpad/audit-prev.json")
    prev = json.loads(prevp.read_text(encoding="utf-8")) if prevp.exists() else {}
    flagged = set(json.loads((ROOT / "art/voice/flagged.json").read_text(encoding="utf-8")))
    src = json.loads((ROOT / "art/voice/source.json").read_text(encoding="utf-8"))
    info = {k: (w, t) for w, t, e, k in G.utterances()}

    rows = []
    for k, v in cur.items():
        if v.get("score") is None or k not in info:
            continue
        who, text = info[k]
        said = V.to_speech(text)
        if len(norm(said)) <= 3:
            continue
        d, segs = diff_of(said, v["got"], text)
        if not segs:
            continue
        pd = None
        if k in prev and prev[k].get("score") is not None:
            pd, _ = diff_of(prev[k]["want"], prev[k]["got"], text)
        worse = pd is not None and pd == 0 and d >= 2
        rows.append({
            "key": k, "who": who, "text": text, "said": said, "got": v["got"],
            "diff": d, "segs": segs, "prev_diff": pd, "worse": worse,
            "flag": k in flagged, "line": src.get(k, {}).get("line", ""),
            "score": (3 if worse else 0) + min(d, 8) + (2 if k in flagged else 0)
                     + (1 if said != text else 0),
        })
    rows.sort(key=lambda r: -r["score"])
    print(f"有證據要聽的：{len(rows)} 句（總共 {len(cur)} 句聽寫過）")
    print(f"  這一輪變差的：{sum(1 for r in rows if r['worse'])}")
    print(f"  瑕疵掃描也標到的：{sum(1 for r in rows if r['flag'])}\n")
    for r in rows[:a.top]:
        tag = ("★變差 " if r["worse"] else "") + ("◆瑕疵 " if r["flag"] else "")
        print(f"  差{r['diff']:>2} {tag}{r['who']}｜{r['text'][:26]}".replace("\n", "／"))
        print(f"         聽成 {r['got'][:26]}｜可疑：{'、'.join(r['segs'][:4])}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n寫出 {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
