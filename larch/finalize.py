"""建置推上線之前的最後一步：build 完推上去的就是線上現在的版本。

2026-11-04 正篇有三件事是直接改線上做的。同一套轉換接在 novelkit.push() 裡，
建置腳本照舊寫「一句一張卡」，推之前在這裡變成新版本：
1. 好幾句併成一張卡（merge_lines.merge_board，ch01–ch07；ch08 謝幕不併）
2. 圖與配音換成 jsDelivr 孤兒 tag 的網址（main_cdn.json）。build 產的配音是 `@main` 網址，
   那條會 403（repo 超過 jsDelivr 的 50 MB），一樣照檔名換成 tag 裡同一個檔
3. 格莉奇的新姿勢與表情（art/main-poses/table.py 的規則；table.tsv 決定欄有填的照決定）
"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'larch')); sys.path.insert(0, str(ROOT / 'art/main-poses'))
import merge_lines
import lines as L, table as T, apply as A


MAIN = re.compile(r'https://cdn\.jsdelivr\.net/gh/yazelin/glitch-vn@main/[^"\s]+')


def retag(b):
    """@main 網址 → tag 裡同一個檔（檔名是雜湊或時間戳，不會撞名）。tag 裡沒有的留著並列出來。"""
    tagged = {u.rsplit('/', 1)[1]: u for u in json.loads((ROOT / 'larch/main_cdn.json').read_text(encoding='utf-8')).values()}
    left = set()
    def sub(m):
        u = tagged.get(m.group(0).rsplit('/', 1)[1])
        if not u: left.add(m.group(0))
        return u or m.group(0)
    b = json.loads(MAIN.sub(sub, json.dumps(b, ensure_ascii=False)))
    if left: print(f'  ★ {b["id"]} 有 {len(left)} 個檔還不在 jsDelivr tag 裡（@main 會 403），先跑 main_cdn.py 打新 tag：', sorted(left)[:3])
    return b


def finalize(bid, nodes, edges):
    b = {'id': bid, 'nodes': nodes, 'edges': edges}
    if bid in merge_lines.BOARDS: b, _ = merge_lines.merge_board(b)
    b = retag(merge_lines.swapper(True)(b))
    rows = L.table({'boards': [b]})
    keep = A.decided()
    want = {}
    for r, k in zip(rows, T.propose(rows)):
        k = keep.get((r['ch'], r['card'], r['i'])) or k
        if k and k != 'wave': want[(r['ch'], r['card'], r['i'])] = k
    A.apply({'boards': [b]}, want, A.urls())
    return b['nodes'], b['edges']
