#!/usr/bin/env python3
"""把配音裡可疑的句子挑出來，集中成一個資料夾讓人一次聽完。

**六百多句不可能一句一句聽。** 音高守門會在生成時擋掉明顯失手的，但門檻
（跟參考音比 0.87）是用少數幾句標記過的樣本校出來的，落在門檻附近的那一批
其實是「不知道」而不是「壞」。這支工具就是把那一批撈出來給人判。

**音高不是「兇」的代理指標。** 試過把「高於中位 12%」的三十八句挑出來重做，
結果平均升高 14 Hz——因為短句音調高本來就是自然的（「欸。」「妳好。」
「恭喜。」本來就上揚），那是語調不是缺陷。真正有效的每一次都是人指名某一句，
去看那一句的上下文，然後改**表演指示**。這支工具只負責找出「可能壞掉」的，
不負責判斷「聽起來如何」。

挑三種：
  一、音高偏離參考音（預設 0.90 以下或 1.25 以上）
  二、長度跟字數對不上——太短通常是整句沒唸完，太長通常是黏到別的東西
  三、完全沒有聲音

檔名會加上偏離程度與台詞開頭，照可疑程度排序，聽到不可疑就可以停。

用法：
    python3 tools/voice_review.py                # → art/voice/review/
    python3 tools/voice_review.py --lo 0.85
"""
import argparse, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=float, default=0.90)
    ap.add_argument("--hi", type=float, default=1.25)
    ap.add_argument("--who", default=None)
    a = ap.parse_args()

    import gen_voice as gv, voice as V
    sys.path.insert(0, str(ROOT / "tools"))
    from voice_batch import _f0

    rows = [(w, t, e, k) for w, t, e, k in gv.utterances()
            if (not a.who or w == a.who) and V.VOICE.get(w)]
    review = OUT / "review"
    if review.exists():
        shutil.rmtree(review)
    review.mkdir(parents=True)

    import soundfile as sf, statistics

    # **基準要用這個角色自己所有句子的中位音高，不可以用 VOICE 裡的參考音。**
    # 走外部配音的角色（鐵塔、諾亞、黑洞先生）在 VOICE 裡登記的是備援的
    # CosyVoice 聲源，跟實際用的 MiniMax 差了好幾個半音，拿它當基準會把
    # 那三個人整批誤判成有問題。用自己的中位數，兩種來源都適用。
    have = []
    for w, t, e, k in rows:
        f = next((OUT / f"{k}{x}" for x in (".wav", ".mp3")
                  if (OUT / f"{k}{x}").exists()), None)
        if f:
            have.append([w, t, e, k, f, _f0(f), sf.info(str(f)).duration])
    ref = {}
    for w in {x[0] for x in have}:
        vals = [x[5] for x in have if x[0] == w and x[5] > 0]
        ref[w] = statistics.median(vals) if vals else 0

    # **第二遍要限制搜尋範圍。** pyin 會八度誤判：諾亞那句長台詞在上限 520 時
    # 報 201Hz（他的中位是 109），限制到 200 就變 140——聽起來完全正常，
    # 是被加倍了。用角色自己的中位數框住範圍，假警報就消失。
    for x in have:
        r = ref[x[0]]
        if not r:
            continue
        v = _f0(x[4], fmin=max(60, r * 0.5), fmax=r * 1.8)
        # **量不到就沿用第一遍的值，不要當成沒有聲音。** 收窄範圍會讓
        # 短句一個有聲幀都抓不到，那是量測的限制，不是檔案壞掉。
        if v:
            x[5] = v
    print("各角色的中位音高：",
          {w: round(v) for w, v in sorted(ref.items(), key=lambda x: -x[1])})

    bad = []
    for w, t, e, k, f, got, dur in have:
        # 字數對長度：正常大約每秒四點三個字。差太多就是沒唸完或黏到別的。
        r = got / ref[w] if ref[w] else 1.0
        # **要把角色的語速算進去。** 旁白跑 1.15 倍速，不除掉的話他每一句
        # 都會被判「太短」——那批二十八句的旗標有一大半是這樣來的。
        want = max(len(t.replace("\n", "")) / 4.3 / V.VOICE[w][2], 0.35)
        why = []
        # **一秒以下不檢查音高。** pyin 在短音檔上常常一個有聲幀都抓不到，
        # 那不代表沒有聲音——「雪。」0.77 秒、RMS 0.05，pyin 給零幀，
        # yin 量得到 103Hz，是黑洞先生的正常音域。門檻設 0.55 太低，
        # 單字句本來就落在 0.7～0.9 秒。這種句子只看長度。
        if dur < 1.0:
            pass
        elif got == 0:
            why.append("沒有聲音")
        elif not (a.lo <= r <= a.hi):
            why.append(f"音高{r:.2f}")
        if dur < want * 0.55:
            why.append(f"太短{dur:.1f}秒")
        elif dur > want * 2.2 + 1.0:
            why.append(f"太長{dur:.1f}秒")
        if why:
            bad.append((abs(r - 1), w, t, k, f, "＋".join(why)))

    bad.sort(reverse=True)
    for i, (_, w, t, k, f, why) in enumerate(bad, 1):
        head = t.replace("\n", "")[:16]
        shutil.copy(f, review / f"{i:03d}-{w}-{why}-{head}{f.suffix}")
    print(f"檢查 {len(rows)} 句，挑出 {len(bad)} 句 → {review}")
    for _, w, t, k, f, why in bad[:15]:
        print(f"  {w:<5}{why:<14}{t.replace(chr(10),'')[:28]}")


if __name__ == "__main__":
    main()
