#!/usr/bin/env python3
"""逐段問「這段音訊有沒有人聲」，用來掃背景樂。

**whisper 不能拿來驗人聲。** 純音樂會讓它產生幻覺，十一支背景樂裡有十支
被轉成整排的「Thank you.」。這支改用 gemini-web 的 chat-file，問封閉選項。

**要逐段掃，不能只聽開頭。** 這批背景樂是生成的，模型很容易在中段塞進
人聲：bgm-living 的 135～210 秒有人在說話，而挑選時只聽了前 30 秒。

    python3 tools/scan_bgm_vocal.py art/bgm/*.mp3        # 每支切三段
    python3 tools/scan_bgm_vocal.py /tmp/一段.mp3         # 直接問某一段
需要環境變數 GEMINI_IMAGE_KEY。
"""
import base64, json, pathlib, sys, urllib.request, os, concurrent.futures as cf
Q = ("這段音訊裡有沒有「人聲」？只回答下面其中一項，再加一句話說明：\n"
     "A 完全沒有人聲，純樂器\n"
     "B 有人聲，但只是無意義的哼唱或和聲墊底\n"
     "C 有人在唱有歌詞的歌\n"
     "D 有人在說話")
def ask(p):
    p = pathlib.Path(p)
    body = json.dumps({"prompt": Q, "file": base64.b64encode(p.read_bytes()).decode(),
                       "filename": "clip.mp3", "timeout": 240}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        "http://192.168.11.11:8070/api/chat-file", body,
        {"Content-Type": "application/json",
         "x-goog-api-key": os.environ["GEMINI_IMAGE_KEY"]}), timeout=300)
    return p.stem, json.loads(r.read()).get("text","").strip()[:180]
import subprocess, tempfile
def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",str(p)],capture_output=True,text=True).stdout or 0)

files=[]
tmp=tempfile.mkdtemp()
for x in sys.argv[1:]:
    p=pathlib.Path(x); d=dur(p)
    if d <= 60:                      # 已經是切好的片段
        files.append(p); continue
    for i in (1,2,3):                # 整支的話取四分之一、二分之一、四分之三
        s0=int(d*i/4)
        out=pathlib.Path(tmp)/f"{p.stem}-{s0}.mp3"
        subprocess.run(["ffmpeg","-v","error","-y","-ss",str(s0),"-t","35",
                        "-i",str(p),"-b:a","128k",str(out)],capture_output=True)
        files.append(out)
with cf.ThreadPoolExecutor(3) as ex:
    for n,t in ex.map(ask, files):
        print(f"\n【{n}】{t}")
