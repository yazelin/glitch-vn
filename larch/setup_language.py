#!/usr/bin/env python3
"""把 voiceMode 設在專案的語言上。**匯出的單檔 HTML 有沒有聲音靠這個。**

匯出的播放器那道閘讀的是卡片層的 `d.voiceMode`，可是卡片上自己寫的那個
會被匯出程序丟掉：雲端存得下、`larch_export_project` 出來的 JSON 裡是 0 個。
匯出時是從 `project.languages[].voiceMode` 複製到每張卡的。

所以「匯出版沒聲音」不是卡片的問題，是專案設定少一個欄位。實測：
語言加上 voiceMode 之後，同一章匯出的 JSON 從 0 個變成 145 個。

    python3 larch/setup_language.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import api

MODE = "shared"
# **這個作品只有正體中文一種語言。** 2026-09-11 讀回來的清單裡多了一筆 ja-JP，
# 是平台上跑過一次翻譯功能留下的（只翻了第一章的八十一張卡），作者決定拿掉。
# 語言清單與卡片上的譯文是兩份資料，只清一邊會留下殘骸：譯文在版子那一邊清
# （見 novelkit.Chapter.push），這裡清清單。
KEEP = "zh-Hant"


def main():
    p = api()
    langs = p.get("languages") or []
    drop = [l for l in langs if l.get("code") != KEEP]
    todo = [l for l in langs if l.get("code") == KEEP and l.get("voiceMode") != MODE]
    if not drop and not todo:
        print(f"語言已經只有 {KEEP} 而且 voiceMode={MODE}，不用動")
        return
    # **`zh-Hant` 那一筆整個保留，`voiceMode` 一個字都不要動。**
    # 匯出的單檔播放器只看 project.languages[].voiceMode，動到它語音整個不響。
    keep = [l for l in langs if l.get("code") == KEEP]
    for l in keep:
        l["voiceMode"] = MODE
    p["languages"] = keep
    if drop:
        print("要拿掉的語言：", [(l.get("code"), l.get("label")) for l in drop])
    # **整包 PUT 才留得住其他欄位**（PUT 只留你送的），所以 p 是整包讀回來的，
    # boards 也在裡面一起送回去。推完一定要回讀比對卡數與邊數。
    r = api({"project": p, "summary": f"語言只留 {KEEP}，voiceMode={MODE}"}, "PUT")
    print("設好了：", [(l.get("code"), l.get("voiceMode")) for l in r.get("languages", [])])
    print("版子：", [(b["id"], len(b["nodes"]), len(b["edges"])) for b in r.get("boards", [])])


if __name__ == "__main__":
    main()
