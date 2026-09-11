#!/usr/bin/env python3
"""把一個角色要唸的話串成一份稿，貼去測試專案讓 Larch 一次配完。

**為什麼要串成一份。** Larch 的 `POST /voice/generate` 是一行一次，一千多行
就是一千多次呼叫，而且每一次都可能逾時。外部配音的做法是反過來：
一個角色的台詞接成一張卡（或幾張），配出一個長檔，抓下來用
`tools/split_take.py` 切回一句一個檔，再把網址寫回真正的卡片。
正篇的諾亞、鐵塔、黑洞先生都是這樣做的。

    python3 tools/take_script.py --list                 # 誰有幾句、幾個字
    python3 tools/take_script.py 發傳單的                 # 印出稿子
    python3 tools/take_script.py 發傳單的 -o out.txt      # 存檔
    python3 tools/take_script.py 發傳單的 --limit 3000    # 換成三千字一塊

一句一行，前面帶編號。編號是給對齊用的錨點（見 split_take 的排卡註三：
編號只在附近找不到的時候才回頭問它），**不要唸出來**——貼進卡片的時候
把編號那一欄拿掉，或是在指示裡講明編號不唸。
"""
import argparse
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))

LIMIT = 4000        # 一塊的上限字數。Larch 那邊一張卡吃得下的量，保守抓


def rows(who=None):
    import gen_voice as G
    out = []
    for sp, tx, emo, k in G.utterances():
        if who and sp != who:
            continue
        out.append((sp, tx, emo, k, G.BOARD_OF.get(k, "")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("who", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--limit", type=int, default=LIMIT)
    ap.add_argument("--board", default="", help="只取某一塊板子的（inv＝調查篇）")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    all_rows = rows()
    if a.board:
        all_rows = [r for r in all_rows if r[4] == a.board]

    if a.list or not a.who:
        by = collections.Counter()
        ch = collections.Counter()
        for sp, tx, _e, _k, _b in all_rows:
            by[sp] += 1
            ch[sp] += len(tx)
        print(f"{'講者':<12}{'句':>6}{'字':>7}{'幾塊':>6}")
        for sp, n in by.most_common():
            print(f"{sp:<12}{n:>6}{ch[sp]:>7}{-(-ch[sp] // a.limit):>6}")
        return 0

    mine = [r for r in all_rows if r[0] == a.who]
    if not mine:
        print(f"找不到「{a.who}」。跑 --list 看有誰。")
        return 1

    # 照 limit 切塊。**不從句子中間切**，一句是一個單位。
    blocks, cur, n = [], [], 0
    for sp, tx, _e, k, _b in mine:
        if cur and n + len(tx) > a.limit:
            blocks.append(cur)
            cur, n = [], 0
        cur.append((len(sum(blocks, [])) + len(cur) + 1, tx, k))
        n += len(tx)
    if cur:
        blocks.append(cur)

    lines = []
    for i, blk in enumerate(blocks, 1):
        lines.append(f"# {a.who}　第 {i}/{len(blocks)} 塊　{len(blk)} 句　"
                     f"{sum(len(t) for _, t, _ in blk)} 字")
        for num, tx, _k in blk:
            lines.append(f"{num:>4}. {tx}")
        lines.append("")
    text = "\n".join(lines)

    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
        print(f"寫出 {a.out}：{len(mine)} 句、{sum(len(t) for _, t, _e, _k, _b in mine)} 字、{len(blocks)} 塊")
    else:
        print(text)
    return 0


def demo():
    """自檢：切塊不可以切在句子中間，也不可以漏句"""
    say = ["一" * 30] * 10
    limit = 100
    blocks, cur, n = [], [], 0
    for tx in say:
        if cur and n + len(tx) > limit:
            blocks.append(cur); cur, n = [], 0
        cur.append(tx); n += len(tx)
    if cur:
        blocks.append(cur)
    assert sum(len(b) for b in blocks) == len(say), blocks
    assert all(sum(len(t) for t in b) <= limit + 30 for b in blocks), blocks
    print("demo ok")


if __name__ == "__main__":
    sys.exit(demo() if "demo" in sys.argv else main())
