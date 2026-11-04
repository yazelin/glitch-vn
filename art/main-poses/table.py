"""正篇「這一句格莉奇用哪張」的規則（2026-11-04 作者拍板：五個姿勢都用、茶几那幾幕不放立繪、黑洞先生不改）。

姿勢看場景與台詞（新姿勢候選比較頁第三版寫的那些場景），表情照線上現在那一句用的臉（配音是照那個情緒錄的，臉跟著聲音走）。
產出 table.tsv：每一句一列，提案欄是規則算的，決定欄留給作者改（空的就用提案）。
用法：python3 art/main-poses/table.py     先跑 lines.py 產 lines.json
"""
import collections, csv, json, pathlib
HERE = pathlib.Path(__file__).parent

# 場景的預設姿勢；沒列的都是「站著說話」
SCENE = {('ch01', 'bg-studio-2am'): 'stream', ('ch06', 'bg-studio-2am'): 'stream',
         ('ch03', 'bg-collab-studio'): 'stream', 'bg-table-lamp': 'none', 'bg-kitchen-morning': 'baking'}
# 場景裡的一段改用別的姿勢：(章, 起句開頭, 迄句開頭, 姿勢)，兩句都算在內
SPANS = [
    ('ch02', '樣品是隔天寄到的', '她翻到第一頁', 'rulebook'),
    ('ch02', '她說給自己聽的', '錄音間裡沒有人', 'rulebook'),
    ('ch02', '那天晚上她把樣品帶回家', '你要嗎', 'rulebook'),          # 拿給黑洞先生看，他收進外套之後手上就空了
    ('ch02', '書籤上印著她的簽名', '標籤底下壓著', 'rulebook'),
    ('ch06', '她做了她每次都會做的事', '欸，同學', 'wave'),           # 街訪打招呼，揮手只留給這裡
    ('ch07', '她在他旁邊坐下', '0x 說，兩年前', 'hands'),            # 「發現自己的手在抖」
    ('ch07', '有五百次', '然後妳每天早上讀到那一句', 'hands'),         # 「格莉奇低頭看著自己的手。她的手還在抖。」前後
]
FACE = {'sprite-glitch': 'plain', 'glitch-plain': 'plain', 'glitch-happy': 'happy', 'glitch-thinking': 'thinking',
        'glitch-idle': 'surprised', 'glitch-error': 'error', 'glitch-sleep': 'sleep',
        'face-glitch-sad': 'sad', 'face-glitch-laugh': 'laugh', 'face-glitch-count': 'count'}
ONE_FACE = {'hands', 'baking'}   # 這兩個姿勢只有一張，臉已經畫在姿勢裡（低頭難過、早晨的微笑）


def propose(rows):
    pose = []
    for r in rows:
        p = SCENE.get((r['ch'], r['bg'])) or SCENE.get(r['bg']) or 'talk'
        pose.append(p)
    for ch, a, b, p in SPANS:
        ks = [k for k, r in enumerate(rows) if r['ch'] == ch]
        start = next(k for k in ks if rows[k]['text'].startswith(a))
        end = next(k for k in ks if k >= start and rows[k]['text'].startswith(b))
        for k in range(start, end + 1): pose[k] = p
    out = []
    for r, p in zip(rows, pose):
        if not r['glitch']: out.append(''); continue          # 她本來就不在台上
        f = FACE[r['glitch']]
        if p in ('none', 'wave'): out.append(p)               # wave＝照舊（現在那張揮手的）
        elif p in ONE_FACE or f == 'plain': out.append(p)
        else: out.append(f'{p}-{f}')
    return out


if __name__ == '__main__':
    rows = json.loads((HERE / 'lines.json').read_text(encoding='utf-8'))
    prop = propose(rows)
    with open(HERE / 'table.tsv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['章', '卡', '句', '背景', '誰', '情緒', '台詞', '現在', '提案', '決定'])
        for r, p in zip(rows, prop):
            w.writerow([r['ch'], r['card'], r['i'], r['bg'], r['who'], r['emo'], r['text'].replace('\n', ' / '), r['glitch'], p, ''])
    c = collections.Counter(p for p in prop if p)
    print(len(rows), '句；', sorted(c.items(), key=lambda x: -x[1]))
