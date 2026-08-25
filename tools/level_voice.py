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
import hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"
BACK = OUT / "pre-level"
# 壓過的檔記在這裡（檔名 → 壓完的雜湊）。有些很短或很輕的句子受真峰值限制，
# 壓到底也搆不到目標，只靠「離目標多遠」判斷的話它們每一次重跑都會再壓一遍，
# 每一遍多一代 mp3 轉檔損失。
LEDGER = OUT / "levelled.json"
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


def sha(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default=None)
    ap.add_argument("--intro", action="store_true",
                    help="改壓角色頁那批（自介與別人怎麼說）")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    if a.intro:
        # **角色頁那批也要壓，而且要壓同一個目標。** clone 會把參考音的音量
        # 一起複製過去，實測 15 支從 -11.5 到 -24.8，差 13.2 dB（四倍以上）。
        # 讀者是在同一頁上一顆一顆按過去的，落差比書裡更明顯。
        # **指名保留的那一份也要壓**（art/voice/intro/picked/），
        # 不然下次 gen_intro 會把沒壓過的那一份複製回 docs/。
        D = ROOT / "docs/voice"
        files = [("角色頁", f) for f in
                 sorted(D.glob("intro-*.mp3")) + sorted(D.glob("view-*.mp3"))]
        files += [("指名保留", f) for f in
                  sorted((ROOT / "art/voice/intro/picked").glob("*.mp3"))]
    else:
        import gen_voice as gv
        rows = [(w, k) for w, t, e, k in gv.utterances()
                if not a.who or w == a.who]
        files = [(w, OUT / f"{k}.mp3") for w, k in rows if (OUT / f"{k}.mp3").exists()]
    print(f"{len(files)} 個檔")
    if a.dry:
        return
    BACK.mkdir(parents=True, exist_ok=True)

    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}

    done = 0
    for w, f in files:
        # **備份一定要用現在的檔覆蓋。** 原本寫成「沒有才備份」，於是重跑時
        # 會從舊備份處理，把後來換上去的新版本蓋回去（實際發生過：剛裝好的
        # 三句被舊版洗掉）。備份的語意是「這次處理前的樣子」，不是「最初的」。
        if led.get(f.name) == sha(f):
            continue
        m = measure(f)
        if not m:
            print("量不到", f.name)
            continue
        # **已經在目標範圍內的就跳過。** 每壓一次多一代 mp3 轉檔損失，
        # 全批重跑幾次就聽得出來。容差開 1 dB：loudnorm 的 linear 模式固定
        # 會低目標約 0.5 dB，容差設 0.5 的話每一次重跑都會全部再壓一遍。
        if abs(float(m["input_i"]) - TARGET_I) <= 1.0:
            continue
        b = (BACK / ("intro-" + f.parent.name + "-" + f.name)
             if a.intro else BACK / f.name)
        b.write_bytes(f.read_bytes())
        # 兩段式：把第一段量到的值餵回去，loudnorm 才知道要怎麼壓
        af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
              f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
              f"offset={m['target_offset']}:linear=true:print_format=summary")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(b), "-af", af,
                        "-ar", "16000", "-ac", "1", "-b:a", "64k", str(f)],
                       capture_output=True)
        led[f.name] = sha(f)
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(files)}", flush=True)
    LEDGER.write_text(json.dumps(led, indent=0), encoding="utf-8")
    print(f"統一了 {done} 個（原檔在 {BACK}）")


if __name__ == "__main__":
    main()


# 背景樂也要壓，而且**要整批一起壓**。
# 只壓換上去的那幾支、留著沒換的那幾支不動，同一個專案裡就會有兩種響度標準：
# 實際發生過——換了五支壓到 -18，剩下六支還在 -13.4～-16，
# 再把全域音量從 0.22 拉到 0.32，落差就爆出來（聯動直播室那場特別吵）。
#     python3 tools/level_bgm.py
