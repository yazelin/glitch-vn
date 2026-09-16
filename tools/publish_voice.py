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
    if "--purge" in sys.argv:
        # 手動 commit＋push 之後用：把最後一個 commit 動到的音檔從 jsDelivr 快取踢掉
        out = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD",
                                       "--", "docs/voice"], cwd=ROOT, text=True)
        purge([pathlib.Path(p).name for p in out.split() if p.endswith(".mp3")])
        return
    DST.mkdir(parents=True, exist_ok=True)
    urls = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    changed = []
    for f in sorted(SRC.glob("*.mp3")):
        d = DST / f.name
        # **要比內容，不可以只比大小。** 統一響度之後有些檔大小剛好一樣，
        # 用大小判斷就整批跳過，線上還是舊的聲音（實際發生過）。
        if not d.exists() or d.read_bytes() != f.read_bytes():
            shutil.copy(f, d)
            changed.append(f.name)
        # **這一份一律是 Pages 的網址，不要跟 Larch 的混在一起。**
        # 混著用的話，哪天 Larch 專案刪掉，小說站就有一百多句會壞。
        # Larch 的網址記在 urls-larch.json，要切換過去再整份換。
        urls[f.stem] = f"{SITE}/{f.name}"
    n = len(changed)
    MAP.write_text(json.dumps(urls, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"複製 {n} 個 → {DST}，網址表 {len(urls)} 筆")

    if "--push" in sys.argv:
        subprocess.check_call(["git", "add", "docs/voice", "art/voice/urls.json"],
                              cwd=ROOT)
        subprocess.check_call(["git", "commit", "-m",
                               "配音上 Pages（Larch 上傳每分鐘只跑得動兩個）"], cwd=ROOT)
        subprocess.check_call(["git", "push"], cwd=ROOT)
        print("推出去了。Pages 佈署要等一兩分鐘。")
        purge(changed)
    elif changed:
        print("卡片上播的是 jsDelivr（@main 快取十二小時）。commit、push 之後跑 --purge 讓新檔立刻生效。")


# 卡片上掛的是 jsDelivr 的網址（larch/novelkit.py 的 cdn()），@main 那一層快取十二小時。
# 改過的檔要打 purge，不然玩家聽到的還是舊音檔——跟「沒 push」的失敗長相一模一樣。
# 要在 git push 之後打：purge 只是丟掉快取，下一次抓的是 GitHub 上現在的檔。
CDN = "https://purge.jsdelivr.net/gh/yazelin/glitch-vn@main/docs/voice"


def purge(names):
    import urllib.request
    bad = 0
    for name in names:
        try:
            urllib.request.urlopen(f"{CDN}/{name}", timeout=30).read()
        except Exception as e:   # purge 失敗只是快取晚十二小時更新，不擋發佈
            bad += 1
            print(f"  purge 失敗 {name}: {e}")
    print(f"purge jsDelivr：{len(names) - bad}/{len(names)}")


if __name__ == "__main__":
    main()
