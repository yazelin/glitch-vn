#!/usr/bin/env python3
"""把「整份一次唸完」的配音檔切回一句一個檔。

外部配音服務常常只給你一個長檔（諾亞那支 144 秒、26 句）。VN 是每張卡片掛
自己的 voiceUrl，所以一定要切開。

**不要只靠靜音判斷句子。** 那支 144 秒的檔裡超過 0.6 秒的停頓只有 11 個，
句子有 26 句，數量對不上；短句之間根本沒有停頓，句子中間反而有。

做法是對齊：台詞原文我們有，whisper 給每個字的時間點，用原文去比對辨識結果
就知道每一句落在哪一段。靜音只用來微調切點，把切點推到最近的停頓上。

用法：
    python3 tools/split_take.py 諾亞 take.mp3 -o art/voice/noah/
"""
import argparse, pathlib, re, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))


def norm(s):
    """只留下可以拿來比對的字元。標點、空白、全半形差異全部拿掉。"""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[^\w]", "", s)


def align(chars, times, want):
    """把每一句原文對到字元流上，回傳每一句的 (起, 迄) 秒。

    用 difflib 找最長相符片段當錨點——辨識一定有錯字，硬比對會整句對不上。
    """
    import difflib
    spans, cur = [], 0
    for w in want:
        m = difflib.SequenceMatcher(None, chars[cur:], w, autojunk=False)
        blocks = [b for b in m.get_matching_blocks() if b.size]
        if not blocks:
            spans.append(None)
            continue
        a0 = cur + blocks[0].a
        a1 = cur + blocks[-1].a + blocks[-1].size
        spans.append((times[a0][0], times[min(a1, len(times)) - 1][1]))
        cur = a1
    return spans


def snap(t, quiet, limit=0.45):
    """把切點推到最近的靜音中心，推不動就原地不動。"""
    best, bd = t, limit
    for a, b in quiet:
        c = (a + b) / 2
        if abs(c - t) < bd:
            best, bd = c, abs(c - t)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("who")
    ap.add_argument("take")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    import gen_voice as gv, voice as V
    rows = [(t, e, k) for w, t, e, k in gv.utterances() if w == a.who]
    if not rows:
        sys.exit(f"找不到 {a.who} 的台詞")
    out = pathlib.Path(a.out or ROOT / "art/voice")
    out.mkdir(parents=True, exist_ok=True)

    import numpy as np, soundfile as sf, librosa, whisper
    y, sr = librosa.load(a.take, sr=16000, mono=True)
    quiet = []
    iv = librosa.effects.split(y, top_db=32)
    for i in range(len(iv) - 1):
        g0, g1 = iv[i][1] / sr, iv[i + 1][0] / sr
        if g1 - g0 > 0.18:
            quiet.append((g0, g1))

    m = whisper.load_model("large-v3-turbo", device="cuda")
    # **一定要給 initial_prompt 逼它出正體。** 不給的話 whisper 吐簡體，
    # 拿去跟正體原文比字元會全部不像，驗收就會謊報一堆失敗。
    ZH = "以下是正體中文的台灣用語對白。"
    r = m.transcribe(a.take, language="zh", word_timestamps=True, initial_prompt=ZH)
    chars, times = "", []
    for s in r["segments"]:
        for w in s.get("words", []):
            c = norm(w["word"])
            if not c:
                continue
            step = (w["end"] - w["start"]) / len(c)
            for i, ch in enumerate(c):
                chars += ch
                times.append((w["start"] + i * step, w["start"] + (i + 1) * step))

    spans = align(chars, times, [norm(t) for t, _, _ in rows])
    miss = [i for i, s in enumerate(spans) if s is None]
    print(f"辨識 {len(chars)} 字，對上 {len(spans)-len(miss)}/{len(rows)} 句")

    # **只信起點，不信終點。** 終點常常抓歪：同一批裡出現過零長度、
    # 只有 0.4 秒、以及前後兩句時間重疊。每一句唸到下一句的起點為止，
    # 天然單調遞增又不重疊，最後一句才用它自己的終點。
    starts = []
    last = 0.0
    for sp in spans:
        t = last if sp is None else max(sp[0], last)
        starts.append(t)
        last = t
    tail = max((sp[1] for sp in spans if sp), default=len(y) / sr)

    cuts = []
    for i, ((text, emo, key), sp) in enumerate(zip(rows, spans)):
        if sp is None:
            print(f"  ✗ {i+1:2d} 對不上：{text[:20]}")
            continue
        s0 = snap(starts[i] - 0.12, quiet)
        nxt = starts[i + 1] if i + 1 < len(starts) else tail + 0.25
        # 終點取「自己唸完」與「下一句開始」兩者較早的那個。只用下一句開始的話，
        # 尾巴會黏上服務唸出來的編號跟情緒（「嗯。」會變成三點八秒）。
        s1 = snap(min(sp[1] + 0.15, nxt - 0.12), quiet)
        if s1 - s0 < 0.2:                       # 對齊失手，退回下一句的起點
            s1 = max(nxt - 0.12, s0 + 0.35)
        seg = y[int(max(0, s0) * sr):int(s1 * sr)]
        sf.write(str(out / f"{key}.wav"), seg, sr)
        flag = "  ★短" if len(seg) / sr < 0.3 else ""
        print(f"  {i+1:2d} {s0:6.2f}→{s1:6.2f} ({len(seg)/sr:4.1f}s){flag} {text[:18]}")
        cuts.append((key, text))

    # **切完一定要驗。** 逐段重新辨識，跟原文比字元重疊率——切歪、黏到下一句的
    # 編號、或整段抓錯位置，用聽的要聽二十六遍，用這個一次就點名。
    import difflib
    print("\n驗收（重新辨識每一段，比對原文）：")
    bad = 0
    for key, text in cuts:
        f = out / f"{key}.wav"
        got = norm(m.transcribe(str(f), language="zh", initial_prompt=ZH)["text"])
        want = norm(text)
        r = difflib.SequenceMatcher(None, got, want, autojunk=False).ratio()
        if r < 0.7:
            bad += 1
            print(f"  ✗ {r:.2f} 想要「{text[:16]}」聽到「{got[:16]}」")
    print(f"  {len(cuts)-bad}/{len(cuts)} 段通過（相似度 0.7 以上）")


if __name__ == "__main__":
    main()
