#!/usr/bin/env python3
"""把配音放上 GitHub Pages，網址寫進 art/voice/urls.json。

**voiceUrl 只是一個網址，不一定要放在 Larch。** 平台的上傳實測每分鐘只傳得動
兩個（單筆二十五秒，跟檔案大小無關，八條並行會撞 429），六百多個要五小時。
這個專案的 Pages 來源就是 docs/，把檔案放進去就有網址，免上傳免額度。

代價是那些檔會進 git 歷史（約 27MB，跟 art/bgm 同級），而且要等 Pages 佈署。

用法：
    python3 tools/publish_voice.py          # 複製進 docs/voice/ 並寫網址表
    python3 tools/publish_voice.py --push   # 順便 commit 與 push
"""
import json, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "art/voice"
DST = ROOT / "docs/voice"
MAP = SRC / "urls.json"
SITE = "https://yazelin.github.io/glitch-vn/voice"


def main():
    DST.mkdir(parents=True, exist_ok=True)
    urls = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    n = 0
    for f in sorted(SRC.glob("*.mp3")):
        d = DST / f.name
        if not d.exists() or d.stat().st_size != f.stat().st_size:
            shutil.copy(f, d)
            n += 1
        # **這一份一律是 Pages 的網址，不要跟 Larch 的混在一起。**
        # 混著用的話，哪天 Larch 專案刪掉，小說站就有一百多句會壞。
        # Larch 的網址記在 urls-larch.json，要切換過去再整份換。
        urls[f.stem] = f"{SITE}/{f.name}"
    MAP.write_text(json.dumps(urls, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"複製 {n} 個 → {DST}，網址表 {len(urls)} 筆")

    if "--push" in sys.argv:
        subprocess.check_call(["git", "add", "docs/voice", "art/voice/urls.json"],
                              cwd=ROOT)
        subprocess.check_call(["git", "commit", "-m",
                               "配音上 Pages（Larch 上傳每分鐘只跑得動兩個）"], cwd=ROOT)
        subprocess.check_call(["git", "push"], cwd=ROOT)
        print("推出去了。Pages 佈署要等一兩分鐘。")


if __name__ == "__main__":
    main()
