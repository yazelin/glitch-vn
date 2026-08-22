#!/usr/bin/env python3
"""把某個角色的台詞匯出成純文字，餵給外部配音服務。

**檔案裡不可以有標頭、編號、情緒欄。** 那些服務是把整份文件唸出來的：
第一次匯出帶了說明跟「編號｜情緒｜台詞」，生出來的 144 秒有一大半在唸
「諾亞台詞表，共26句，格式，編號，情緒，台詞……一，笑，又鎖起來了」。
要它唸什麼就只放什麼。

**輸出放 design/台詞/，不要放 docs/。** 那是 GitHub Pages 的根目錄，
放進去等於把工作檔公開發佈出去，而且會被搜尋引擎收錄。

用法：
    python3 tools/dump_lines.py 鐵塔              # → design/台詞/鐵塔.txt（純台詞）
    python3 tools/dump_lines.py 鐵塔 --numbered   # 每句前面加「第N句。」
    python3 tools/dump_lines.py 鐵塔 --notes      # 另存一份帶情緒的給人看

純台詞版優先。編號版的用處是**保證句與句之間有停頓**：連續幾句都很短的話，
服務可能一口氣唸完，中間沒有空隙，切割就只能硬切。編號唸出來會被
tools/split_take.py 從尾巴剪掉，不會留在成品裡。
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))


def main():
    who = sys.argv[1]
    import gen_voice as gv
    rows = [(w, t, e) for w, t, e, _ in gv.utterances() if w == who]
    if not rows:
        sys.exit(f"找不到 {who} 的台詞")

    # 純台詞：一句一段，句內的換行拉平成一行，免得被當成新的一句。
    # **換行要變成句號，不可以直接拿掉。** 貓草的卡片是聊天訊息，一則一行，
    # 拿掉換行會黏成「本來就是你今天發了三則預告」，唸起來是另一句話。
    def flatten(t):
        out = ""
        for line in t.split("\n"):
            line = line.strip()
            if not line:
                continue
            if out and out[-1] not in "。！？，、…":
                out += "。"
            out += line
        return out

    flat = [flatten(t) for _, t, _ in rows]
    if "--numbered" in sys.argv:
        flat = [f"第{i}句。{t}" for i, t in enumerate(flat, 1)]
    body = "\n\n".join(flat)
    tag = "-編號" if "--numbered" in sys.argv else ""
    p = ROOT / f"design/台詞/{who}{tag}.txt"
    p.write_text(body + "\n", encoding="utf-8")
    print(f"{p}　{len(rows)} 句　{len(body)} 字")

    if "--notes" in sys.argv:
        q = ROOT / f"design/台詞/{who}-對照.txt"
        q.write_text("\n".join(
            f"{i:2d}｜{e or '—'}｜" + t.replace("\n", " ")
            for i, (_, t, e) in enumerate(rows, 1)) + "\n", encoding="utf-8")
        print(f"{q}　（這份給人看，不要餵給配音服務）")


if __name__ == "__main__":
    main()
