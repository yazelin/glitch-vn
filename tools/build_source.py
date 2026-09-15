#!/usr/bin/env python3
"""逐句記下「這個音檔是哪一條線產生的」。

**不要從角色反推。** 保全與店員中途換過音色、有些句子走逐句有些走長檔，
角色層看不見那種例外；而頁面上要回答的是「這一句用哪條線」。

判定依據（照可靠度排序，先中的贏）：

  一、`art/voice/takes/<角色>.mp3` 存在，而且那一句的 mp3 **比長檔新**
      → Larch 長檔切分。長檔是一次唸完再切，切出來的檔一定晚於長檔本身。
  二、角色在 `LARCH_VOICE` 裡但檔案比長檔舊（或沒有長檔）
      → Larch 逐句（`POST /voice/generate` 一行一次）。
  三、角色在 `voice.EXTERNAL` 裡（黑洞先生、諾亞、鐵塔）
      → 正篇那幾句是 MiniMax／Larch 長檔切分的；
        **調查篇那 107 句是本機克隆**（`gen_voice` 的 EXTERNAL 閘只擋正篇）。
  四、其餘 → 本機 CosyVoice3 克隆。

判不出來的寫「不確定」並附理由，**不要猜一個**。

    python3 tools/build_source.py        # 寫出 art/voice/source.json
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice/source.json"


def main():
    import gen_voice as G
    from voice import LARCH_VOICE as LV, EXTERNAL
    import voice as V
    labels = json.loads((ROOT / "art/voice/larch-labels.json").read_text(encoding="utf-8"))
    takes = {p.stem: p.stat().st_mtime for p in (ROOT / "art/voice/takes").glob("*.mp3")}
    src = {}
    for who, text, emo, k in G.utterances():
        f = ROOT / "docs/voice" / f"{k}.mp3"
        if not f.exists():
            f = ROOT / "art/voice" / f"{k}.mp3"
        if not f.exists():
            src[k] = {"line": "沒有音檔", "why": "兩個目錄都找不到這個代號"}
            continue
        mt = f.stat().st_mtime
        if who in LV:
            lab = labels.get(who, ["", who])[1]
            # **用「有沒有 wav」分，不要用時間戳。** split_take 切出來的是 wav
            # （之後才轉 mp3），逐句下載的只有 mp3。時間戳分不出來——
            # 逐句補的那批晚於長檔，用時間比會全部被算成長檔（2026-09-14 中過）。
            wav = (ROOT / "art/voice" / f"{k}.wav").exists()
            if wav and who in takes:
                src[k] = {"line": f"Larch 長檔・{lab}", "why": "有 wav，是從該角色的長檔切出來的"}
            elif wav:
                src[k] = {"line": "不確定", "why": f"有 wav 但找不到 {who} 的長檔，來歷判不出來"}
            else:
                src[k] = {"line": f"Larch 逐句・{lab}",
                          "why": "只有 mp3 沒有 wav，是逐句呼叫下載的"}
        elif who in EXTERNAL:
            if G.BOARD_OF.get(k) == "inv":
                src[k] = {"line": "本機 CosyVoice3（克隆外部聲音）",
                          "why": "調查篇那批走本機，參考音是從他自己的外部長檔切下來的"}
            else:
                src[k] = {"line": "Larch／MiniMax 長檔切分", "why": "正篇的外部配音角色"}
        else:
            src[k] = {"line": "本機 CosyVoice3 克隆", "why": f"參考音 {V.VOICE.get(who, ('?',))[0]}"}
    OUT.write_text(json.dumps(src, ensure_ascii=False, indent=0), encoding="utf-8")
    import collections
    c = collections.Counter(v["line"] for v in src.values())
    print(f"寫出 {OUT}　{len(src)} 句")
    for k, n in c.most_common():
        print(f"  {n:5d}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
