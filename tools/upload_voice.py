#!/usr/bin/env python3
"""把 art/voice 裡的配音上傳成專案媒體，網址寫進 art/voice/urls.json。

**跟平台的即時生成完全分開。** 我們自己生、自己傳，卡片只填 voiceUrl，
不碰 voiceMode="realtime"，所以那 280 次額度一次都不會用到。

category 要填 voice（實測平台記成 category=voice、type=audio）。早期註解寫
「只有 scene／character／prop」是舊的。

檔名就是台詞的代號（voice.key），所以 urls.json 是 代號 → 網址，
build_ch0*.py 直接查表掛上去，不用再對一次。

用法：
    python3 tools/upload_voice.py          # 只傳還沒傳過的
    python3 tools/upload_voice.py --redo   # 全部重傳
"""
import json, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"
# **不要寫 urls.json。** 那份是建置實際在查的表，Pages 那條路也在寫它，
# 兩支程式同時跑就會互相覆蓋（實測 Pages 的 677 筆被蓋成 105 筆，
# 有聲書的對應率因此從七成掉到一成七，而且不會報錯）。
# 這裡只記自己傳上去的，要切換過去再合併。
MAP = OUT / "urls-larch.json"
# 八條會撞 429（伺服器有速率限制），被擋掉的那些等於白跑，所以並行度拉高
# 反而沒有更快。三條加上退讓重試比八條硬衝穩。
WORKERS = 3


def main():
    from setup import upload
    from config import api
    urls = {}
    if MAP.exists() and "--redo" not in sys.argv:
        urls = json.loads(MAP.read_text(encoding="utf-8"))
    # **以平台為準，不要只信本地的 urls.json。** 上傳到一半中斷的話，檔案已經
    # 在平台上了但本地沒記錄，再跑一次會傳出一堆重複的媒體。檔名就是代號，
    # 直接對得回來。
    if "--redo" not in sys.argv:
        n0 = len(urls)
        for m in api().get("media", []):
            if m.get("category") == "voice" and (m.get("name") or "").endswith(".mp3"):
                urls.setdefault(m["name"][:-4], m["url"])
        if len(urls) > n0:
            print(f"平台上已經有 {len(urls)-n0} 個沒記錄到的，收回來")
    files = sorted(OUT.glob("*.mp3"))
    todo = [f for f in files if f.stem not in urls]
    print(f"{len(files)} 個音檔，已傳 {len(files)-len(todo)}，這次傳 {len(todo)}")
    # **一定要並行。** 單筆上傳實測二十四秒，而且跟檔案大小無關（13KB 也是
    # 二十四秒），瓶頸在伺服器端延遲不在頻寬。六百多個檔照順序傳要十三小時。
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    lock = threading.Lock()

    def one(f):
        raw = f.read_bytes()
        for i in range(6):
            try:
                return f.stem, upload(f.name, raw, "voice", "audio/mpeg")
            except Exception as e:
                if "429" not in str(e) or i == 5:
                    raise
                time.sleep(4 * 2 ** i)      # 4、8、16、32、64 秒
        raise RuntimeError("重試用完")

    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, f): f for f in todo}
        for fu in as_completed(futs):
            k, u = fu.result()
            with lock:
                urls[k] = u
                done += 1
                if done % 20 == 0 or done == len(todo):
                    MAP.write_text(json.dumps(urls, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
                    print(f"  {done}/{len(todo)}", flush=True)
    MAP.write_text(json.dumps(urls, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"寫好 {MAP}（{len(urls)} 筆）")


if __name__ == "__main__":
    main()
