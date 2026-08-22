#!/usr/bin/env python3
"""把所有配音統一到同一個響度。

**每個角色的音量差很多**：實測格莉奇 -13.3 dB、旁白 -19.1、黑洞先生 -25.0，
最大差到 11.7 dB（將近四倍音量）。原因是 clone 會把參考音的音量一起複製過去，
而外部配音又是另一套。聽起來就像格莉奇在吼、黑洞在喃喃自語。

用 ffmpeg 的 loudnorm（EBU R128）做兩段式正規化：先量再套，比單純調峰值準，
因為它量的是人耳感受到的響度，不是最大振幅。

**不重生任何一句**，只改音量。原檔備份在 art/voice/pre-level/。

用法：
    python3 tools/level_voice.py            # 全部
    python3 tools/level_voice.py --who 格莉奇
    python3 tools/level_voice.py --dry      # 只量不改
"""
import argparse, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"
BACK = OUT / "pre-level"
TARGET_I, TARGET_TP, TARGET_LRA = -18.0, -2.0, 9.0


def measure(p):
    # **不可以加 -v error。** loudnorm 的 JSON 是走 stderr 的 info 訊息，
    # 壓掉輸出等級就一起壓掉了，量到的永遠是 None。
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-af",
         f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    s = r.stderr
    i = s.rfind("{")
    return json.loads(s[i:]) if i >= 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default=None)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    import gen_voice as gv
    rows = [(w, k) for w, t, e, k in gv.utterances()
            if not a.who or w == a.who]
    files = [(w, OUT / f"{k}.mp3") for w, k in rows if (OUT / f"{k}.mp3").exists()]
    print(f"{len(files)} 個檔")
    if a.dry:
        return
    BACK.mkdir(parents=True, exist_ok=True)

    done = 0
    for w, f in files:
        b = BACK / f.name
        if not b.exists():
            b.write_bytes(f.read_bytes())
        m = measure(b)
        if not m:
            print("量不到", f.name)
            continue
        # 兩段式：把第一段量到的值餵回去，loudnorm 才知道要怎麼壓
        af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
              f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
              f"offset={m['target_offset']}:linear=true:print_format=summary")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(b), "-af", af,
                        "-ar", "16000", "-ac", "1", "-b:a", "64k", str(f)],
                       capture_output=True)
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(files)}", flush=True)
    print(f"統一了 {done} 個（原檔在 {BACK}）")


if __name__ == "__main__":
    main()
