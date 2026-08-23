#!/usr/bin/env python3
"""把 art/bgm 底下每一支背景樂壓到同一個響度。

**整批一起壓。** 只壓新換上去的那幾支會留下兩種標準，混在一起聽就是
有幾場特別吵。實際發生過：換了五支壓到 -18，沒換的六支還在 -13.4～-16。

壓完要重新上傳（網址會變）並重建所有章節，卡片才吃得到新的那一份。
    python3 tools/level_bgm.py            # 只看現在差多少
    python3 tools/level_bgm.py --fix      # 真的壓
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BGM = ROOT / "art/bgm"
TARGET, TOL = -18.0, 1.0


def measure(p):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-af",
         f"loudnorm=I={TARGET}:TP=-2:LRA=9:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    i = r.stderr.rfind("{")
    return json.loads(r.stderr[i:]) if i >= 0 else None


def main():
    fix = "--fix" in sys.argv
    off = []
    for f in sorted(BGM.glob("*.mp3")):
        m = measure(f)
        if not m:
            print("量不到", f.name)
            continue
        cur = float(m["input_i"])
        mark = "" if abs(cur - TARGET) <= TOL else "　← 要壓"
        print(f"  {f.stem:<16}{cur:7.2f} LUFS{mark}")
        if mark:
            off.append((f, m))
    if not off:
        return print(f"\n全部在 {TARGET}±{TOL} dB 內。")
    if not fix:
        return print(f"\n{len(off)} 支不在範圍內。加 --fix 才會真的壓。")
    for f, m in off:
        af = (f"loudnorm=I={TARGET}:TP=-2:LRA=9:measured_I={m['input_i']}:"
              f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
              f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        tmp = f.with_suffix(".tmp.mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-af", af,
                        "-ar", "48000", "-ac", "2", "-b:a", "180k", str(tmp)],
                       capture_output=True)
        tmp.replace(f)
        print("  壓好", f.stem)
    print("\n記得重新上傳（larch/setup.py）並重建所有章節——網址變了。")


if __name__ == "__main__":
    main()
