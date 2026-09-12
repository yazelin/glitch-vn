"""調查篇缺的那幾首 BGM。一次一首，不要把 .11 的四個 worker 塞滿（別條線也在用）。

風格錨定在正篇既有的九支：安靜、不搶戲、可循環、沒有人聲。
這一款整整十四天都在同一批地點來回，**配樂要耐聽到玩家忘記它在播**。
"""
import base64, json, os, pathlib, sys, time, urllib.request

OUT = pathlib.Path(__file__).parent
KEY = os.environ["GEMINI_IMAGE_KEY"]
API = "http://192.168.11.11:8070/api/music"

JOBS = {
 "bgm-store": "便利商店的深夜。冷氣與冰櫃壓縮機的低頻嗡鳴當底，上面一層很輕的電鋼琴，"
              "四到五個音反覆，沒有旋律高潮。日光燈的白。安靜，不搶戲，可以無縫循環，"
              "沒有人聲，沒有鼓組，沒有漸強。三十秒以上。",
 "bgm-parts":  "老電子材料行的午後。木頭抽屜、真空管、積灰的零件。指彈尼龍弦吉他，"
              "慢，帶一點懷舊但不煽情，偶爾一聲很輕的顫音琴。安靜，不搶戲，可以循環，"
              "沒有人聲，沒有鼓組。三十秒以上。",
 "bgm-transit": "台北近郊車站前的站牌與捷運出口。城市環境的白噪當底，上面疏落的馬林巴與"
              "合成器長音，節奏鬆散像等車。不悲傷也不明亮，就是在等。安靜，可以循環，"
              "沒有人聲，沒有明顯鼓點。三十秒以上。",
}

JOBS_B = {
 "bgm-store-b": "便利商店的深夜。極簡：一台冰櫃的低頻嗡鳴，加上非常稀疏的合成器長音，"
              "兩三個音就好，音與音之間留很長的空白。不要旋律。像店裡沒有人的時候。"
              "可以無縫循環，沒有人聲，沒有鼓組。三十秒以上。",
 "bgm-parts-b": "老電子材料行的午後。老式電子琴的單音旋律，帶一點失真與磁帶感，"
              "速度很慢，像店裡那台收音機在放很舊的曲子。安靜，可以循環，"
              "沒有人聲，沒有鼓組。三十秒以上。",
 "bgm-transit-b": "台北近郊車站前。只有一把電鋼琴，慢速，和弦之間留白很久，"
              "沒有環境音也沒有其他樂器。空曠，像月台上只剩你一個人。"
              "可以循環，沒有人聲，沒有鼓點。三十秒以上。",
}
JOBS = {**JOBS, **JOBS_B}

for name, prompt in JOBS.items():
    p = OUT / f"{name}.mp3"
    if p.exists():
        print(f"  {name} 已經有了，跳過"); continue
    body = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(API, body, {"Content-Type": "application/json",
                                             "x-goog-api-key": KEY})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            d = json.loads(r.read().decode())
    except Exception as e:
        print(f"  ★ {name} 失敗：{str(e)[:120]}"); continue
    if not d.get("success") or not d.get("audio"):
        print(f"  ★ {name} 回了但沒有音檔：{json.dumps(d, ensure_ascii=False)[:160]}"); continue
    p.write_bytes(base64.b64decode(d["audio"]))
    print(f"  {name}.mp3  {p.stat().st_size//1024} KB  {time.time()-t0:.0f}s  mime={d.get('mime')}")
