#!/usr/bin/env python3
"""把配音聽寫回來，跟「應該唸的字」比對讀音，挑出唸錯的。

**為什麼比音不比字。** whisper 聽寫出來的同音字跟原文一定不同
（襪子↔袜子、機器↔机器、三坪↔三瓶），那些不是錯。所以兩邊都轉成拼音再比，
**而且不帶聲調**——whisper 分不出聲調，帶聲調比會整批假警報。

代價是**只有聲調錯的抓不到**（翹 qiáo／qiào 那一類）。那種目前只能靠耳朵。
這支工具抓的是「唸成完全不同的音」：誇→禍、摺→器、螢幕→由沐、〇→整個沒唸。

    ~/voice-venv/bin/python tools/asr_audit.py            # 全部
    ~/voice-venv/bin/python tools/asr_audit.py --limit 50 # 先跑 50 個看看
    ~/voice-venv/bin/python tools/asr_audit.py --self-test # 負控制

輸出 art/voice/asr-audit.json，並印出最可疑的前 40 句。
中斷可續：已經聽寫過的代號會跳過。
"""
import argparse, json, pathlib, sys, difflib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice/asr-audit.json"


def say(text):
    """一句話的音（不帶聲調的拼音串）。標點與空白不算。"""
    from pypinyin import lazy_pinyin
    import re
    t = re.sub(r"[^\w一-鿿]+", "", text)
    return lazy_pinyin(t)


def score(want, got):
    """回 (相似度, 對不上的音節數)。相似度 1.0 代表讀音完全一樣。"""
    a, b = say(want), say(got)
    if not a:
        return 1.0, 0
    sm = difflib.SequenceMatcher(None, a, b)
    same = sum(bl.size for bl in sm.get_matching_blocks())
    return same / max(len(a), len(b)), max(len(a), len(b)) - same


def rows():
    import gen_voice as G, voice as V
    from voice import LARCH_VOICE as LV
    out = []
    for who, text, emo, k in G.utterances():
        said = V.to_speech(text)
        if not said.strip():
            continue
        p = ROOT / "docs/voice" / f"{k}.mp3"
        if not p.exists():
            p = ROOT / "art/voice" / f"{k}.mp3"
        if not p.exists():
            continue
        out.append((k, who, said, str(p), who in LV))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        # 負控制：已知該抓的要抓到，已知不該抓的不可以抓到。
        # 正確答案是今天用同一套方法一句一句量出來的，不是猜的。
        bad = [("你不要以為我在夸你。", "你不要以為我在禍你,你是第二個。"),
               ("螢幕上看不出來。", "由沐上看不出來。"),
               ("她把傳單摺起來。", "她把傳單器起來。")]
        ok = [("有人留了一隻袜子。", "有人留了一隻襪子。"),
              ("三坪多。", "三瓶多。"),
              ("六台機器，一台在轉。", "六台機器,一台再轉。")]
        print("該抓到的（相似度要低）：")
        for w, g in bad:
            s, n = score(w, g)
            print(f"  {s:.2f}  差 {n} 音　{w[:16]}")
        print("不該抓到的（相似度要高）：")
        for w, g in ok:
            s, n = score(w, g)
            print(f"  {s:.2f}  差 {n} 音　{w[:16]}")
        return 0

    import whisper
    rs = rows()
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [r for r in rs if r[0] not in have]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{len(rs)} 句有檔，已經聽過 {len(rs)-len([r for r in rs if r[0] not in have])} 句，這次聽 {len(todo)} 句")
    m = whisper.load_model(a.model, device="cuda")
    for i, (k, who, said, path, is_larch) in enumerate(todo, 1):
        try:
            r = m.transcribe(path, language="zh", initial_prompt="繁體中文對話。")
            got = (r.get("text") or "").strip()
            s, n = score(said, got)
            have[k] = {"who": who, "want": said, "got": got, "score": round(s, 3),
                       "diff": n, "larch": is_larch}
        except Exception as e:
            have[k] = {"who": who, "want": said, "got": "", "score": None, "err": str(e)[:80]}
        if i % 50 == 0:
            OUT.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"  {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")

    # **判準是「差幾個音」，不是相似度。** 負控制量出來：同音字換過之後，
    # 唸對的句子差 0 個音（袜子↔襪子、三坪↔三瓶都是 0）。所以差 >= 1 就值得看。
    # 相似度在長句上會被稀釋——一句四十個音只錯一個，相似度 0.97 卻是真的錯。
    vals = [v for v in have.values() if v.get("score") is not None]
    import collections
    hist = collections.Counter(min(v["diff"], 6) for v in vals)
    print(f"\n聽過 {len(have)} 句。差幾個音的分布："
          + "　".join(f"{k}{'+' if k==6 else ''}：{hist[k]}" for k in sorted(hist)))
    sus = sorted([v for v in vals if v["diff"] >= 1],
                 key=lambda v: (-v["diff"], v["score"]))
    print(f"差 >= 1 個音的共 {len(sus)} 句。最可疑的前 40：")
    for v in sus[:40]:
        print(f"  {v['score']:.2f} 差{v['diff']:>2}  {v['who']:<6}｜要唸 {v['want'][:26]}")
        print(f"                    ｜聽成 {v['got'][:26]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
