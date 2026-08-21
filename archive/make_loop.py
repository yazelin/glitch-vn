#!/usr/bin/env python3
"""把 Suno 出來的曲子做成 VN 能用的背景音樂。

Suno 反覆給不出來的三件事,後製都修得掉:
  太亮      → 高頻 shelf 衰減
  動態太大  → 壓縮打平,再整體降到背景音量
  有淡出    → 挑一段乾淨的,用交叉淡化自己接自己,做成真的無縫 loop

用法: python3 make_loop.py <輸入> <輸出> --start 30 --len 72 --xfade 4 --tilt -6
"""
import argparse, subprocess, sys
import numpy as np

SR = 44100

def load(path):
    raw = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","2","-ar",str(SR),"-f","f32le","-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)

def seamless(y, start, length, xfade):
    """取一段,把它後面那 xfade 秒交叉淡化回開頭 → 尾接頭不會有斷點"""
    s, L, X = int(start*SR), int(length*SR), int(xfade*SR)
    need = s + L + X
    if need > len(y):
        raise SystemExit(f"素材只有 {len(y)/SR:.0f} 秒,要不到 {need/SR:.0f} 秒")
    seg = y[s:need]
    loop = seg[:L].copy()
    w = np.linspace(0, 1, X)[:, None]
    loop[:X] = seg[L:L+X]*(1-w) + seg[:X]*w
    return loop

def estimate_bpm(y):
    """從 onset 包絡的自相關估拍速。只是估,拿來對齊小節夠用。"""
    mono = y.mean(1) if y.ndim > 1 else y
    hop, win = 512, 2048
    n = (len(mono) - win) // hop
    frames = np.stack([mono[i*hop:i*hop+win] * np.hanning(win) for i in range(min(n, 4000))])
    S = np.abs(np.fft.rfft(frames, axis=1))
    d = np.diff(S, axis=0); d[d < 0] = 0
    env = d.sum(1); env -= env.mean()
    ac = np.correlate(env, env, "full")[len(env)-1:]
    fps = SR / hop
    lo, hi = int(fps*60/180), int(fps*60/60)
    return 60 * fps / (lo + int(np.argmax(ac[lo:hi])))


def snap_to_bars(length, bpm, beats_per_bar=4):
    """把 loop 長度收到最接近的整數小節。

    取樣層面接得再準,樂句在半小節處重新開始,聽起來還是斷的——實測就是
    這樣被聽出「非常明顯的斷點」。鋼琴那種長衰減的曲子比較不明顯,有鼓的
    一定要對齊。
    """
    bar = beats_per_bar * 60.0 / bpm
    bars = max(1, round(length / bar))
    return bars * bar, bars, bar


def process(src, tilt, target, comp_ratio=3.0):
    """先把整首做完 EQ + 壓縮 + 響度,再回傳取樣。

    順序很重要:acompressor 與 loudnorm 都是有狀態的,單趟處理時開頭沒有歷史、
    結尾有,增益曲線兩端不一樣。先裁 loop 再處理的話,numpy 裡接得好好的接縫
    會被動態處理拉開——實測就是這樣被聽出「非常明顯的斷點」。
    """
    # 壓縮會把埋著的東西挖出來。實測:原曲的鼓低到 Gemini 聽不見,ratio=3 壓過
    # 之後它就聽出「低音鼓與踏拔」了。動態本來就平的曲子不要壓,--comp 1 關掉。
    chain = [f"highshelf=f=6000:g={tilt}", f"highshelf=f=10000:g={tilt}"]
    if comp_ratio > 1.01:
        chain.append(f"acompressor=threshold=-20dB:ratio={comp_ratio}:attack=50:release=400")
    chain.append(f"loudnorm=I={target}:TP=-2:LRA=7")
    af = ",".join(chain)
    raw = subprocess.run(["ffmpeg","-v","error","-i",src,"-af",af,
                          "-ac","2","-ar",str(SR),"-f","f32le","-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--start", type=float, default=30)
    ap.add_argument("--len", type=float, default=72)
    ap.add_argument("--xfade", type=float, default=4)
    ap.add_argument("--tilt", type=float, default=-6, help="6kHz 以上衰減幾 dB")
    ap.add_argument("--target", type=float, default=-24, help="目標 LUFS,背景音樂要低")
    ap.add_argument("--bpm", type=float, default=0, help="指定拍速;留空就自己估")
    ap.add_argument("--comp", type=float, default=3.0, help="壓縮比;1 = 不壓")
    a = ap.parse_args()

    y = process(a.src, a.tilt, a.target, a.comp)
    bpm = a.bpm or estimate_bpm(y)
    length, bars, bar = snap_to_bars(a.len, bpm)
    print(f"   拍速約 {bpm:.1f} BPM,一小節 {bar:.3f} 秒 → loop 收到 {bars} 小節 = {length:.2f} 秒")
    loop = seamless(y, a.start, length, a.xfade)
    a.len = length

    import wave
    tmp = "/tmp/_loop_done.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(loop, -1, 1)*32767).astype("<i2").tobytes())
    # 這一趟只做編碼,不再碰動態,接縫才保得住
    subprocess.run(["ffmpeg","-v","error","-y","-i",tmp,"-c:a","libmp3lame","-b:a","192k",a.out],
                   check=True)
    print(f"-> {a.out}  {a.len:.0f} 秒無縫 loop,高頻 {a.tilt}dB,{a.target} LUFS")


if __name__ == "__main__":
    main()
