#!/usr/bin/env python3
"""把「整份一次唸完」的配音檔切回一句一個檔。

外部配音服務常常只給你一個長檔（諾亞那支 144 秒、26 句）。VN 是每張卡片掛
自己的 voiceUrl，所以一定要切開。

**不要只靠靜音判斷句子。** 那支 144 秒的檔裡超過 0.6 秒的停頓只有 11 個，
句子有 26 句，數量對不上；短句之間根本沒有停頓，句子中間反而有。

做法是對齊：台詞原文我們有，whisper 給每個字的時間點，用原文去比對辨識結果
就知道每一句落在哪一段。靜音只用來微調切點，把切點推到最近的停頓上。

**規模會決定難度。** 十句到五十句的檔一次到位（10/10、18/18、26/26、50/50），
一百五十二句那份試了五次才成，過程中學到的三件事都是反直覺的：

  一、**對齊只能在附近找。** 拿每一句去比對「剩下的全部字元」，短句（「欸。」
      「喔。」）會在幾百字外找到假匹配，一跳過去後面全錯——152 句只對上 36 句。
  二、**長檔要分段辨識**，八分鐘一次丟進去 whisper 會整段漏掉（1943 字只吐
      1286 字）。但分段單獨做反而更糟（95 → 40），因為對齊本身就不穩，
      分段又給它更多噪音。三件事要一起做才有用。
  三、**編號是求助用的，不是指揮用的。** 服務唸出來的「第N句」是很好的錨點，
      但直接把指標推到編號之後會從 130 掉到 61：辨識出來的編號本身會錯，
      推到錯的位置後面就全歪。只在附近找不到的時候才回頭問它。

最後那一版：146/152 對上。

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


def _cn2int(s):
    """把「第37句」裡的數字轉成整數。whisper 有時吐阿拉伯數字有時吐國字。"""
    if s.isdigit():
        return int(s)
    D = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
         "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if "百" in s or len(s) > 4:
        return None
    if "十" in s:
        a, _, b = s.partition("十")
        return (D.get(a, 1) if a else 1) * 10 + (D.get(b, 0) if b else 0)
    return D.get(s)


def align(chars, times, want, numbered=False):
    """把每一句原文對到字元流上，回傳每一句的 (起, 迄) 秒。

    **只在附近找，而且要求匹配比例。** 早期版本拿每一句去跟「剩下的全部字元」
    比對，短句（「欸。」「喔。」）很容易在幾百字之外找到假的匹配點，一旦跳過去
    後面就全錯——一百五十二句的長檔只對上三十幾句就是這樣。
    """
    import difflib
    # **有編號就用編號當錨點。** 服務唸出來的「第N句」比台詞本身可靠得多：
    # 台詞可能只有兩三個字（「你要嗎。」「黑洞先生。」），比例門檻一嚴就對不上，
    # 連續十二句一起漏掉；編號永遠是完整的一串，而且唯一。
    marks = {}
    if numbered:
        import re as _re
        for m2 in _re.finditer(r"第([0-9零一二三四五六七八九十百]+)句", chars):
            n = _cn2int(m2.group(1))
            if n and n not in marks:
                marks[n] = m2.end()

    spans, pos = [], 0
    for idx, w in enumerate(want, 1):
        if not w:
            spans.append(None)
            continue
        # 往前看的範圍：這一句的長度乘三再加緩衝。中間夾雜的東西（服務唸出來的
        # 「第N句」、辨識錯的字）都在這個範圍內，跳得過去。
        def find(start):
            wn = chars[start:start + len(w) * 3 + 120]
            if not wn:
                return None
            b = difflib.SequenceMatcher(None, wn, w, autojunk=False) \
                .find_longest_match(0, len(wn), 0, len(w))
            need = 1 if (numbered and len(w) <= 4) else max(2, int(len(w) * 0.45))
            return b if b.size >= need else None

        blk = find(pos)
        base = pos
        # **編號是求助用的，不是指揮用的。** 直接把指標推到編號之後會更糟
        # （130 → 61）：辨識出來的編號本身會錯，一推到錯的位置後面就全歪。
        # 只有在附近找不到的時候才回頭問編號。
        if blk is None and idx in marks:
            base = marks[idx]
            blk = find(base)
        if blk is None:
            spans.append(None)
            continue
        a0 = base + max(0, blk.a - blk.b)                 # 把匹配段往回推到句首
        a1 = min(len(times), a0 + len(w))
        if a1 <= a0:
            spans.append(None)
            continue
        spans.append((times[a0][0], times[a1 - 1][1]))
        pos = a1
    return spans



def vad_chars(y, sr, m, ZH, top_db=32, gap=0.30):
    """用靜音切段，逐段辨識，回傳字元流與每個字的時間。

    **這比整檔辨識準得多。** 長檔一次丟給 whisper 會漏字（八分鐘的檔
    原文 1943 字只吐 1286 字），時間戳也飄。切成一句上下的短段之後，
    每一段幾乎不會漏，時間就用該段的起迄平均分配給它的字。

    段落跟句子不是一對一：MiniMax 會把幾句短的連著唸成一段，
    長句子中間停頓又會被切成兩段。所以這裡只負責產生準確的字元流，
    對齊仍然交給 align()。
    """
    import tempfile, pathlib
    import soundfile as sf, librosa

    iv = librosa.effects.split(y, top_db=top_db)
    segs, cur = [], [iv[0]]
    for i in range(len(iv) - 1):
        if (iv[i + 1][0] - iv[i][1]) / sr > gap:
            segs.append((cur[0][0], cur[-1][1])); cur = []
        cur.append(iv[i + 1])
    segs.append((cur[0][0], cur[-1][1]))
    print(f"VAD 切出 {len(segs)} 段，逐段辨識")

    chars, times = "", []
    for a0, b0 in segs:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            sf.write(tf.name, y[a0:b0], sr)
            t = norm(m.transcribe(tf.name, language="zh", initial_prompt=ZH)["text"])
        pathlib.Path(tf.name).unlink(missing_ok=True)
        if not t:
            continue
        t0, t1 = a0 / sr, b0 / sr
        step = (t1 - t0) / len(t)
        for i, ch in enumerate(t):
            chars += ch
            times.append((t0 + i * step, t0 + (i + 1) * step))
    return chars, times


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

    # **先切段再逐段辨識**（見 vad_chars），字元流才準；對齊仍然用 align()。
    chars, times = vad_chars(y, sr, m, ZH)
    numbered = chars.count("句") >= len(rows) * 0.5
    if numbered:
        print("偵測到編號，用編號當錨點")
    # **要拿替身版的文字去對齊。** 錄音是照 design/台詞/*.txt 唸的，那份已經
    # 套過 voice.SUB（闔→合、行→航……）。拿原文去比，長句會整句對不上。
    spans = align(chars, times, [norm(V.to_speech(t)) for t, _, _ in rows], numbered)
    miss = [i for i, x in enumerate(spans) if x is None]
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
        want = norm(V.to_speech(text))
        r = difflib.SequenceMatcher(None, got, want, autojunk=False).ratio()
        if r < 0.7:
            bad += 1
            print(f"  ✗ {r:.2f} 想要「{text[:16]}」聽到「{got[:16]}」")
    print(f"  {len(cuts)-bad}/{len(cuts)} 段通過（相似度 0.7 以上）")


if __name__ == "__main__":
    main()
