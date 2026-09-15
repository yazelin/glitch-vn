#!/usr/bin/env python3
"""把 triage.json 按「壞法」分類，因為不同壞法要用不同方法處理。

**重點不是排序，是分流。** 有三種壞法機器自己判得出來，不必人耳：

  重複   ASR 把同一句抄兩遍 → 音檔真的唸了兩次（CosyVoice 已知的迴圈）
  亂掉   ASR 吐出英文或無關字串 → 音檔是雜訊或整段跑掉
  多唸    ASR 比原文長很多 → 長檔切分時把隔壁句的頭尾切進來

剩下的才是破音字，而破音字**按詞聚合**之後只剩幾十個詞，
一個詞聽一句就能判，不必逐句聽。

    python3 tools/triage_kind.py
"""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LATIN = re.compile(r"[A-Za-z]{4,}")
HANDLE = re.compile(r"[@＠][A-Za-z0-9_]")


def norm(s):
    return re.sub(r"[^\w一-鿿]+", "", s or "")


def repeated(got):
    """ASR 抄兩遍：把字串對半切，前半在後半裡找得到。"""
    g = norm(got)
    if len(g) < 16:
        return False
    h = len(g) // 2
    return g[:h] in g[h:] or g[h:] in g[:h]


def kind_of(r):
    said, got = norm(r["said"]), norm(r["got"])
    if HANDLE.search(r["text"]):
        return "帳號"                      # ASR 聽不出 @handle，不是缺陷
    if repeated(r["got"]):
        return "重複"
    if LATIN.search(r["got"]) and not LATIN.search(r["text"]):
        return "亂掉"
    if len(got) > len(said) * 1.35 + 4:
        return "多唸"
    if len(got) < len(said) * 0.65 - 2:
        return "少唸"
    return "讀音"


def main():
    rows = json.loads((ROOT / "art/voice/triage.json").read_text(encoding="utf-8"))
    for r in rows:
        r["kind"] = kind_of(r)
    by = collections.Counter(r["kind"] for r in rows)
    order = ["重複", "亂掉", "多唸", "少唸", "讀音", "帳號"]
    how = {"重複": "直接重生，不用聽", "亂掉": "直接重生，不用聽",
           "多唸": "重切或重生，不用聽", "少唸": "重生，不用聽",
           "讀音": "**要你的耳朵**，但按詞聽", "帳號": "不是缺陷，忽略"}
    print("290 句按壞法分流：\n")
    for k in order:
        print(f"  {k}　{by[k]:>3} 句　{how[k]}")
    auto = sum(by[k] for k in ("重複", "亂掉", "多唸", "少唸"))
    print(f"\n  機器自己能處理：{auto} 句　要人耳：{by['讀音']} 句　可忽略：{by['帳號']} 句")

    words = collections.Counter()
    where = collections.defaultdict(list)
    for r in rows:
        if r["kind"] != "讀音":
            continue
        for s in r["segs"][:3]:
            words[s] += 1
            where[s].append(r)
    print(f"\n讀音那 {by['讀音']} 句聚成 {len(words)} 個詞。出現兩次以上的：\n")
    for w, n in words.most_common():
        if n < 2:
            continue
        r = where[w][0]
        print(f"  {n}× {w}　例：{r['who']}｜{r['text'][:20]}".replace("\n", "／"))
        print(f"         聽成 {r['got'][:20]}")
    solo = [w for w, n in words.items() if n == 1]
    print(f"\n  只出現一次的詞：{len(solo)} 個 → {'、'.join(solo[:40])}")
    (ROOT / "art/voice/triage.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
