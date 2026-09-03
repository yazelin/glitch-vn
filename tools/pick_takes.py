#!/usr/bin/env python3
"""一句生好幾版，全部留著讓人挑。

**同一組指示既生得出兇的也生得出好的。** 試過調指示、調音高，都沒有用——
兇是每次生成擲骰子的結果。所以與其猜，不如一句多生幾版讓耳朵挑。

輸出的檔名帶序號與台詞開頭，同一句的幾個版本排在一起，聽完把選中的
檔名回報，用 tools/install_take.py 裝上去。

用法：
    ~/voice-venv/bin/python tools/pick_takes.py 格莉奇 --ch 2 -n 3
"""
import argparse, json, os, pathlib, re, runpy, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))


def chapter_rows(ch, who):
    import novelkit as nk, voice as V
    built = {}
    nk.Chapter.push = lambda self, s: built.setdefault(self.bid, self.nodes)
    nk.ensure_characters = lambda: {n: f"c-{n}" for n in list(nk.SPRITE) + ["旁白"]}

    class _A(dict):
        def __missing__(self, k): return f"x/{k}"
    nk.A = _A(nk.A)
    nk.VOICE_URLS = {}
    runpy.run_path(str(ROOT / f"larch/build_ch{ch:02d}.py"), run_name="__main__")
    out = []
    for bid in built:
        for n in built[bid]:
            d = n["data"]
            if (d.get("type") or "dialogue") != "dialogue":
                continue
            items = ([(l.get("speaker"), l.get("text"), l.get("emotion"))
                      for l in d.get("dialogueLines") or []]
                     or [(d.get("speaker"), d.get("text"), d.get("emotion"))])
            for sp, tx, em in items:
                if sp == who and tx and tx.strip():
                    out.append((tx, em or None, V.key(sp, tx, em or None)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("who")
    ap.add_argument("--ch", type=int, required=True)
    ap.add_argument("-n", type=int, default=3)
    ap.add_argument("-o", default=None)
    a = ap.parse_args()

    import voice as V
    rows = chapter_rows(a.ch, a.who)
    print(f"第{a.ch}章 {a.who} {len(rows)} 句 × {a.n} 版 = {len(rows)*a.n} 支")
    out = pathlib.Path(a.o or ROOT / f"art/voice/takes-ch{a.ch:02d}")
    out.mkdir(parents=True, exist_ok=True)
    ref, ptext, speed = V.VOICE[a.who]
    ref = ref if ref.startswith("/") else str(ROOT / ref)

    jobs = []
    for i, (t, e, k) in enumerate(rows, 1):
        head = re.sub(r'[^\w一-鿿]', '', t.replace("\n", ""))[:12]
        for j in range(1, a.n + 1):
            jobs.append({"out": str(out / f"{i:02d}-{j}-{head}.wav"),
                         "text": V.to_speech(t), "prompt_wav": ref,
                         "prompt_text": ptext, "speed": speed,
                         "instruct": V.instruct(a.who, e)})
    jf = out / "jobs.json"
    jf.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    # 代號表：裝上去的時候要用
    (out / "keys.tsv").write_text(
        "\n".join(f"{i:02d}\t{k}\t{t.replace(chr(10),' ')}"
                  for i, (t, e, k) in enumerate(rows, 1)), encoding="utf-8")
    py = pathlib.Path.home() / "voice-venv/bin/python"
    env = dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1")
    subprocess.check_call([str(py), "-u", str(ROOT / "tools/voice_batch.py"),
                           "--jobs", str(jf)], env=env)
    print(f"\n聽 {out}，把選中的檔名回報")


if __name__ == "__main__":
    main()
