#!/usr/bin/env python3
"""排出「該聽哪幾句」，把 1900 句收到一個人坐一次就能聽完的量。

**收斂的方法是按詞不按句。** 破音字是字的問題不是句的問題：「摺」唸錯，
它出現的 14 句一定全錯，聽一句就夠判。所以讀音那一類每個可疑詞只留一句代表，
275 句收成 52 句。

**排序是證據強度。** 依序是：
  一、同一個詞在好幾句裡都被聽錯   → 最像真的唸錯（一次性的多半是 ASR 抖動）
  二、秒數跟字數對不上            → 跳針或被切掉，跟唸什麼無關
  三、瑕疵掃描標到的              → 頻譜異常
  四、逐句情緒例外                → 我們手動改過指令，值得抽聽

**不列進來的**：機器判得出來的那幾類（重複、亂掉、少唸）已經直接重生了，
不佔人的時間；@handle 那類 ASR 本來就聽不出來，不是缺陷。

    python3 tools/listen_list.py     # 寫出 art/voice/listen.json
"""
import collections, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    tri = json.loads((ROOT / "art/voice/triage.json").read_text(encoding="utf-8"))
    # **本人聽過說沒問題的就不要再排上來。** 沒有這一份的話，每次重跑
    # 同一批句子又會回到清單最前面，聽過的人看不出自己聽到哪裡了。
    hp = ROOT / "art/voice/heard.json"
    heard = set(json.loads(hp.read_text(encoding="utf-8"))) if hp.exists() else set()
    # 已經修掉並複驗過的也不排（修好的紀錄在 paren-check / len-scan 跑完之後）
    fixed = set()
    fp = ROOT / "art/voice/fixed.json"
    if fp.exists():
        fixed = set(json.loads(fp.read_text(encoding="utf-8")))
    skip = heard | fixed
    out = {}

    # 一、讀音：按詞聚合，每個出現兩次以上的詞留一句代表（挑差最多的那句）
    by_word = collections.defaultdict(list)
    for r in tri:
        if r["kind"] != "讀音":
            continue
        for s in r["segs"][:3]:
            by_word[s].append(r)
    # **一個詞判過就整組退場。** 聽過的那一句如果是某個詞的代表，代表這個詞
    # 已經有答案了；再換另一句上來問同一個詞，等於同一題問第二次。
    # 2026-09-15 踩到：本人說「逼」那兩句都 OK，清單卻又換一句「逼」上來。
    settled = {w for w, rs in by_word.items() if any(x["key"] in skip for x in rs)}
    for w, rs in sorted(by_word.items(), key=lambda x: -len(x[1])):
        if len(rs) < 2 or w in settled:
            continue
        rs = [x for x in rs if x["key"] not in skip]
        if len(rs) < 2:
            continue
        r = max(rs, key=lambda x: x["diff"])
        out.setdefault(r["key"], {
            "rank": 1, "why": f"「{w}」在 {len(rs)} 句裡都被聽錯，聽這一句就能判",
            "got": r["got"][:40]})

    # 二、秒數對不上
    lp = ROOT / "art/voice/len-scan.json"
    if lp.exists():
        for r in json.loads(lp.read_text(encoding="utf-8")):
            if r["key"] in skip:
                continue
            out.setdefault(r["key"], {
                "rank": 2, "why": f"{r['n']} 個字唸了 {r['sec']} 秒，長度不對",
                "got": ""})

    # 三、瑕疵掃描
    fp = ROOT / "art/voice/flagged.json"
    if fp.exists():
        for k in json.loads(fp.read_text(encoding="utf-8")):
            if k in skip:
                continue
            out.setdefault(k, {"rank": 3, "why": "瑕疵掃描標到（頻譜異常）", "got": ""})

    # 四、逐句情緒例外
    sys.path.insert(0, str(ROOT / "larch"))
    import voice as V
    for (sp, tx) in getattr(V, "LINE_EMO", {}):
        if V.key(sp, tx) in skip:
            continue
        out.setdefault(V.key(sp, tx), {"rank": 4, "why": "這一句的語氣指令是手動改的", "got": ""})

    p = ROOT / "art/voice/listen.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = collections.Counter(v["rank"] for v in out.values())
    print(f"建議先聽 {len(out)} 句（排掉聽過的 {len(heard)} 句、修好的 {len(fixed)} 句）：")
    for r, lab in ((1, "讀音（每個可疑詞一句）"), (2, "長度不對"),
                   (3, "瑕疵掃描"), (4, "語氣例外")):
        print(f"  {n[r]:>3} 句　{lab}")
    print(f"寫出 {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
