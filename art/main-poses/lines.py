"""把線上正篇攤成「每一句」的清單：章、卡、句、背景、誰在講、emotion、台詞、格莉奇台上用哪張圖。
給 table.py 排「這一句換哪個姿勢」用。只讀，不寫。
用法：python3 art/main-poses/lines.py [live.json]    不給檔就 GET 線上
"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'larch'))
from merge_lines import lines_of

NAME = re.compile(r'\d+_([a-z0-9-]+)\.(?:png|webp|jpe?g)$')
stem = lambda u: (NAME.search(u or '') or [None, ''])[1]


def walk(board):
    """照線走（選項各分支依序走一遍、走過的卡不重走），回傳 [(卡, 句索引, 句, 背景)]。"""
    nodes = {n['id']: n for n in board['nodes']}; out = {}
    for e in board['edges']: out.setdefault(e['source'], []).append(e)
    for v in out.values(): v.sort(key=lambda e: str(e.get('sourceHandle')))
    start = next((n['id'] for n in board['nodes'] if n['data'].get('start')), board['nodes'][0]['id'])
    rows, seen, stack = [], set(), [(start, '')]
    while stack:
        cur, bg = stack.pop()
        while cur and cur not in seen and cur in nodes:
            seen.add(cur); d = nodes[cur]['data']
            if d.get('background'): bg = d['background']
            if d.get('type') == 'dialogue':
                for i, l in enumerate(lines_of(d)): rows.append((cur, i, l, bg))
            elif (d.get('stage') or {}).get('actors'):   # 場景卡、選項卡也帶立繪（選項卡沒帶的話人會在那一張消失）
                rows.append((cur, -1, {'text': d.get('text') or d.get('title') or '', 'speaker': '', 'stage': d['stage']}, bg))
            o = out.get(cur, [])
            if len(o) == 1: cur = o[0]['target']
            else:
                stack += [(e['target'], bg) for e in reversed(o)]; cur = None
    return rows


def table(p):
    res = []
    for b in p['boards']:
        for cid, i, l, bg in walk(b):
            g = [a for a in (l.get('stage') or {}).get('actors', []) if a.get('name') == '格莉奇']
            res.append({'ch': b['id'], 'card': cid, 'i': i, 'bg': stem(bg), 'who': l.get('speaker', ''),
                        'emo': l.get('emotion', ''), 'text': l.get('text', ''), 'glitch': stem(g[0]['url']) if g else ''})
    return res


if __name__ == '__main__':
    import config
    p = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else config.api()
    p = p.get('project', p)
    rows = table(p)
    out = ROOT / 'art/main-poses/lines.json'
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding='utf-8')
    import collections
    print(len(rows), '句；格莉奇在台上', sum(1 for r in rows if r['glitch']), '句')
    print(collections.Counter(r['glitch'] for r in rows if r['glitch']).most_common())
