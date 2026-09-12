#!/usr/bin/env python3
"""把 A/B 代聽用的節錄做成等長、等響度。**兩次通過**。

用法：python3 tools/level_ab.py art/bgm/inv-candidates --seconds 60

**為什麼一定要兩次通過。** ffmpeg 的 `loudnorm` 單次通過是**估的**，不是量的。
2026-09-12 w1V 實測我單次通過交出去的三對：store 差 0.9 LU、parts 差 0.8 LU、
transit 差 1.4 LU，而且 transit 的 A 是 −16.1，比目標 −18 高了 1.9。
**「比較安靜不搶戲」這條判準對 1.4 LU 是敏感的**——那個差聽得出來，
答案有可能是音量給的，跟長度會帶著答案跑是同一件事，只是變因換成音量。

做法：第一次通過量出 `measured_I／TP／LRA／thresh／offset`，
第二次把那五個值帶回去，加 `linear=true`。

**一律從全長原檔開始**，不要拿已經正規化過的節錄再跑一次——那是二次處理，
量到的是上一次的結果。
"""
import argparse, json, pathlib, subprocess, sys

TARGET = "I=-18:TP=-2:LRA=9"


def measure(src, seconds):
    """第一次通過：量這一段的實際響度。"""
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(src), "-t", str(seconds),
         "-af", f"loudnorm={TARGET}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = r.stderr
    i = txt.rfind("{")
    if i < 0:
        raise SystemExit(f"量不到 {src}")
    return json.loads(txt[i:txt.rfind("}") + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir"); ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--out", default="ab-60s")
    a = ap.parse_args()
    d = pathlib.Path(a.dir); out = d / a.out; out.mkdir(exist_ok=True)
    bad, level = [], {}
    for src in sorted(d.glob("*.mp3")):
        m = measure(src, a.seconds)
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-t", str(a.seconds),
             "-af", f"loudnorm={TARGET}:measured_I={m['input_i']}:"
                    f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                    f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true",
             "-ac", "2", "-b:a", "128k", str(out / src.name)], check=True)
        chk = measure(out / src.name, a.seconds)
        got = float(chk["input_i"])
        print(f"  {src.name:<20}{float(m['input_i']):>7.1f} → {got:>6.1f} LU")
        level[src.stem] = got

    # **要驗的是同一對之間的差，不是離 -18 多遠。**
    # 會讓代聽答錯的是「這半邊比較大聲」，不是「兩邊都比目標小 0.6」。
    # 2026-09-12 第一版的門檻寫成絕對值，結果 parts 那一對兩支都是 -18.6、
    # 彼此差 0.0 LU（完美），卻被判失敗——驗錯了東西。
    print()
    for stem in sorted(k for k in level if not k.endswith("-b")):
        b = stem + "-b"
        if b not in level:
            continue
        d = abs(level[stem] - level[b])
        ok = d <= 0.3
        print(f"  {stem:<16}A {level[stem]:>6.1f}  B {level[b]:>6.1f}  差 {d:.1f} LU  "
              f"{'○' if ok else '★ 差太多，代聽可能是音量給的答案'}")
        if not ok:
            bad.append(stem)
    _odd = [k for k, v in level.items() if abs(v + 18) > 1.5]
    if _odd:
        print(f"\n（理智檢查：{_odd} 離 -18 超過 1.5 LU，值得看一眼，但不影響對內比較）")
    if bad:
        print(f"\n★ {len(bad)} 對的音量差超過 0.3 LU：{bad}"); return 1
    print("\n每一對的音量差都在 0.3 LU 以內")
    return 0


if __name__ == "__main__":
    sys.exit(main())
