#!/usr/bin/env python3
"""把一個角色的短句組成長段一次生成，再切回一句一個檔。

**短句各自生會不穩。** 一句一句丟進去，每一句的語調都是重新擲一次骰子，
格莉奇前幾章都是短的鬥嘴句，聽起來就一句比一句兇。旁白同一套設定卻很穩，
差別在他的句子長。組成長段再切，整段的語調是連貫的。

只組**指示相同**的連續句子（多數是沒標情緒與標平靜的那批，走同一個底色）。
標了情緒的句子單獨生，那是刻意要不一樣的。

切割沿用 split_take 的做法：whisper 給每個字的時間點，拿原文對齊找出每一句，
切完**逐段重新辨識比對原文**——切歪、黏到隔壁句，用聽的要聽一百多遍。
沒通過驗收的那幾段不覆蓋，保留原本的檔。

用法：
    ~/CosyVoice/.venv/bin/python tools/batch_voice.py 格莉奇
    ~/CosyVoice/.venv/bin/python tools/batch_voice.py 格莉奇 --max 200 --dry
"""
import argparse, difflib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"


def groups(rows, max_chars, max_n):
    """連續、同指示的句子併成一段。"""
    out, cur, ins = [], [], None
    for r in rows:
        if r[4] != ins or len(cur) >= max_n or \
                sum(len(x[1]) for x in cur) + len(r[1]) > max_chars:
            if cur:
                out.append(cur)
            cur, ins = [], r[4]
        cur.append(r)
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("who")
    ap.add_argument("--max", type=int, default=180)
    ap.add_argument("--n", type=int, default=9)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    import gen_voice as gv, voice as V
    import split_take as ST
    rows = [(w, t.replace("\n", ""), e, k, V.instruct(w, e))
            for w, t, e, k in gv.utterances() if w == a.who]
    if not rows:
        sys.exit(f"找不到 {a.who}")
    gs = [g for g in groups(rows, a.max, a.n) if len(g) > 1]
    solo = sum(1 for g in groups(rows, a.max, a.n) if len(g) == 1)
    print(f"{a.who} 共 {len(rows)} 句 → {len(gs)} 段（另有 {solo} 句單獨，不動）")
    for g in gs[:3]:
        print(f"  {len(g)} 句 {sum(len(x[1]) for x in g)} 字："
              + "".join(x[1] for x in g)[:44])
    if a.dry:
        return

    ref, ptext, speed = V.VOICE[a.who]
    ref = ref if ref.startswith("/") else str(ROOT / ref)
    tmp = ROOT / "art/voice/batch"
    tmp.mkdir(parents=True, exist_ok=True)
    jobs = [{"out": str(tmp / f"g{i:03d}.wav"),
             "text": V.to_speech("".join(x[1] for x in g)),
             "prompt_wav": ref, "prompt_text": ptext, "speed": speed,
             "instruct": g[0][4]} for i, g in enumerate(gs)]
    jf = tmp / "jobs.json"
    jf.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    py = pathlib.Path.home() / "CosyVoice/.venv/bin/python"
    env = dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1")
    subprocess.check_call([str(py), "-u", str(ROOT / "tools/voice_batch.py"),
                           "--jobs", str(jf)], env=env)

    import numpy as np, soundfile as sf, librosa, whisper
    m = whisper.load_model("large-v3-turbo", device="cuda")
    ZH = "以下是正體中文的台灣用語對白。"
    ok = fail = 0
    for i, g in enumerate(gs):
        f = tmp / f"g{i:03d}.wav"
        if not f.exists():
            continue
        y, sr = librosa.load(str(f), sr=16000, mono=True)
        quiet = []
        iv = librosa.effects.split(y, top_db=32)
        for j in range(len(iv) - 1):
            g0, g1 = iv[j][1] / sr, iv[j + 1][0] / sr
            if g1 - g0 > 0.15:
                quiet.append((g0, g1))
        r = m.transcribe(str(f), language="zh", word_timestamps=True,
                         initial_prompt=ZH)
        chars, times = "", []
        for s in r["segments"]:
            for w in s.get("words", []):
                c = ST.norm(w["word"])
                if not c:
                    continue
                step = (w["end"] - w["start"]) / len(c)
                for n2, ch in enumerate(c):
                    chars += ch
                    times.append((w["start"] + n2 * step,
                                  w["start"] + (n2 + 1) * step))
        spans = ST.align(chars, times, [ST.norm(V.to_speech(x[1])) for x in g])
        starts, last = [], 0.0
        for sp in spans:
            t0 = last if sp is None else max(sp[0], last)
            starts.append(t0); last = t0
        tail = max((sp[1] for sp in spans if sp), default=len(y) / sr)
        for j, (row, sp) in enumerate(zip(g, spans)):
            if sp is None:
                fail += 1
                continue
            s0 = ST.snap(starts[j] - 0.10, quiet)
            nxt = starts[j + 1] if j + 1 < len(starts) else tail + 0.2
            s1 = ST.snap(min(sp[1] + 0.14, nxt - 0.10), quiet)
            if s1 - s0 < 0.2:
                s1 = max(nxt - 0.10, s0 + 0.35)
            seg = y[int(max(0, s0) * sr):int(s1 * sr)]
            p = tmp / f"{row[3]}.wav"
            sf.write(str(p), seg, sr)
            got = ST.norm(m.transcribe(str(p), language="zh",
                                       initial_prompt=ZH)["text"])
            want = ST.norm(V.to_speech(row[1]))
            ratio = difflib.SequenceMatcher(None, got, want,
                                            autojunk=False).ratio()
            if ratio < 0.7:
                fail += 1
                print(f"  ✗{ratio:.2f} 想要「{row[1][:16]}」聽到「{got[:16]}」")
                p.unlink()
                continue
            ok += 1
            for d in (OUT, ROOT / "docs/voice"):
                subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(p),
                                       "-ac", "1", "-b:a", "64k",
                                       str(d / f"{row[3]}.mp3")])
            p.unlink()
    print(f"\n換掉 {ok} 句，{fail} 句沒通過驗收（保留原本的檔）")


if __name__ == "__main__":
    main()
