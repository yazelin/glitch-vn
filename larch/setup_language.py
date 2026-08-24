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


def main():
    p = api()
    langs = p.get("languages") or []
    todo = [l for l in langs if l.get("voiceMode") != MODE]
    if not todo:
        print(f"語言已經是 voiceMode={MODE}，不用動")
        return
    for l in todo:
        l["voiceMode"] = MODE
    r = api({"project": p, "summary": f"語言設定 voiceMode={MODE}"}, "PUT")
    print("設好了：", [(l.get("code"), l.get("voiceMode")) for l in r.get("languages", [])])


if __name__ == "__main__":
    main()
