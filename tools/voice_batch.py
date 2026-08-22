#!/usr/bin/env python3
"""這個作品的配音批次工具。跟 cosy-narrator 的差別有三：

一、**整句一次合成，不要自己按句號拆。** 試過把長句切成四十字以內再接，比整段
    丟進去差：每一段各自合成，指示會重新擲一次骰子，段與段的情緒對不起來。
    CosyVoice 內部本來就會在 60～80 個 token 分段，這裡把它吐的段落接起來就好。
二、**可以調語速**（CosyVoice 的 inference_zero_shot 吃 speed）。
三、**模型只載入一次**，然後把一整批句子跑完。載入要三十幾秒，一句一句跑會被它吃掉。

用法：
  python3 tools/voice_batch.py --jobs jobs.json
  jobs.json = [{"out": "路徑.wav", "text": "要唸的話",
                "prompt_wav": "參考音", "prompt_text": "參考音的逐字稿",
                "speed": 1.0, "instruct": "冷淡，沒有起伏"}, ...]

**有 instruct 就走 inference_instruct2。** zero-shot 會把參考音的語氣一起複製過去，
而 Common Voice 那些參考音是照稿唸的、平的，所以生出來也是平的——沒有語氣不是模型不會，
是我們沒有給指示。instruct2 用參考音複製音色，語氣照指示走。
"""
import argparse, json, pathlib, sys, time

# 音高守門的容許範圍（跟參考音的比值）。低於下限就是**失手**：
# 同一句話、同一個指示連生兩次，音高可以差到 -27%，聽起來像換了一個人
# ——格莉奇會變成小男生。其他角色正常都落在 0.97～1.12。
F0_LO, F0_HI, TRIES = 0.87, 1.25, 4


def _f0(path):
    """中位基頻。取不到就回 0（當作通過，不要因為量不到而卡住）。"""
    import numpy as np, librosa
    y, sr = librosa.load(str(path), sr=16000, mono=True)
    if len(y) < sr * 0.15:
        return 0.0
    # **用 pyin 不要用 yin。** yin 快，但把好的（0.98）跟失手的（0.92）擠在一起
    # 分不開；pyin 量同一批是 0.90～0.95 對 0.74～0.83，中間有乾淨的空隙。
    f, _, _ = librosa.pyin(y, fmin=60, fmax=520, sr=sr)
    f = f[~np.isnan(f)]
    return float(np.median(f)) if len(f) else 0.0

COSY = pathlib.Path.home() / "CosyVoice"
MODEL = COSY / "pretrained_models/Fun-CosyVoice3-0.5B"


def _synth(cv, j, ptext):
    if j.get("instruct"):
        ins = f"You are a helpful assistant. {j['instruct']}<|endofprompt|>"
        return cv.inference_instruct2(j["text"], ins, j["prompt_wav"],
                                      stream=False, speed=j.get("speed", 1.0))
    return cv.inference_zero_shot(j["text"], ptext, j["prompt_wav"],
                                  stream=False, speed=j.get("speed", 1.0))


def _guard(cv, j, ptext, out, ref, torch, torchaudio):
    """音高守門：偏離參考音太多就重生，留最接近的那一版。

    模型是隨機的——同一句話同一個指示生兩次結果不一樣，所以「生一次就收工」
    對六百多句來說一定會漏掉幾十句失手的。這裡用數字擋掉，不用人耳一句一句聽。
    """
    if not ref:
        return ""
    best, best_d = _f0(out), None
    if best and F0_LO <= best / ref <= F0_HI:
        return ""
    best_d = abs(best / ref - 1) if best else 9
    tmp = out.with_suffix(".try.wav")
    for k in range(TRIES - 1):
        wav = torch.cat([r["tts_speech"] for r in _synth(cv, j, ptext)], dim=1)
        torchaudio.save(str(tmp), wav, cv.sample_rate)
        got = _f0(tmp)
        d = abs(got / ref - 1) if got else 9
        if d < best_d:
            best, best_d = got, d
            tmp.replace(out)
        else:
            tmp.unlink(missing_ok=True)
        if F0_LO <= best / ref <= F0_HI:
            return f"  ↻{k+1} {best:.0f}Hz"
    return f"  ↻{TRIES-1} {best:.0f}Hz ★仍偏離"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    a = ap.parse_args()
    jobs = json.loads(pathlib.Path(a.jobs).read_text(encoding="utf-8"))
    todo = [j for j in jobs if not pathlib.Path(j["out"]).exists()]
    print(f"{len(jobs)} 句，要生 {len(todo)}", flush=True)
    if not todo:
        return

    sys.path.append(str(COSY / "third_party/Matcha-TTS"))
    sys.path.append(str(COSY))
    import torch, torchaudio
    from cosyvoice.cli.cosyvoice import AutoModel

    t0 = time.time()
    cv = AutoModel(model_dir=str(MODEL))
    print(f"模型載入 {time.time()-t0:.0f}s", flush=True)

    ref_f0, skipped = {}, []
    for n, j in enumerate(todo, 1):
        out = pathlib.Path(j["out"]); out.parent.mkdir(parents=True, exist_ok=True)
        if j["prompt_wav"] not in ref_f0:
            ref_f0[j["prompt_wav"]] = _f0(j["prompt_wav"])
        # CosyVoice 的 prompt 要這個前綴，narrate.py 也是這樣寫的
        ptext = f"You are a helpful assistant.<|endofprompt|>{j['prompt_text']}"
        t1 = time.time()
        if j.get("instruct"):
            # **指示也要帶 <|endofprompt|>**，官方 example.py 就是這樣寫的。
            # 少了它會先丟 AssertionError，然後炸在卷積層（Kernel size 那個錯訊很誤導）。
            ins = f"You are a helpful assistant. {j['instruct']}<|endofprompt|>"
            gen = cv.inference_instruct2(j["text"], ins, j["prompt_wav"],
                                         stream=False, speed=j.get("speed", 1.0))
        else:
            gen = cv.inference_zero_shot(j["text"], ptext, j["prompt_wav"],
                                         stream=False, speed=j.get("speed", 1.0))
        pieces = [r["tts_speech"] for r in gen]
        if not pieces:
            # 只有標點的句子（貓草那句「…………」）正規化之後什麼都不剩，
            # 模型吐空的。那種句子畫面上有意義，但沒有聲音可配——記下來跳過，
            # **不可以讓它把整批倒掉**：第一次跑就是死在第十六句。
            skipped.append(j["text"][:20])
            print(f"[{n}/{len(todo)}]  跳過（沒有可唸的內容）  {j['text'][:20]}",
                  flush=True)
            continue
        torchaudio.save(str(out), torch.cat(pieces, dim=1), cv.sample_rate)
        note = _guard(cv, j, ptext, out, ref_f0[j["prompt_wav"]], torch, torchaudio)
        print(f"[{n}/{len(todo)}] {time.time()-t1:4.1f}s  {out.name}{note}  "
              f"{j['text'][:26]}", flush=True)
    if skipped:
        print(f"跳過 {len(skipped)} 句沒有可唸內容的：{skipped}", flush=True)
    print(f"完成，總共 {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
