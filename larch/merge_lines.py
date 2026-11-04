"""正篇「一句一卡」合併成多句卡（2026-11-04 作者在翻新比較頁選「合併成多句卡」）。

同一塊白板上，一路單線相連的對話卡（中間沒有分岔、沒有條件線、下一張只有一條入線）
併成一張卡：第一張卡的 id 留著，每一句的字、講者、表情、配音照原樣，
原本那張卡的立繪（stage）掛到那一句上（Larch 一張卡可以每句換立繪）。

立繪一句一句照原樣，包括留言頭像在貓草講話時出現、格莉奇回話時收掉
（作者 2026-11-04：「他能出現消失這樣對於他講話反而是比較好的事，一句一句的感覺比較強」）。
唯一會不見的是串裡的卡片轉場：正篇 20 張帶轉場的對話卡全是聊天室留言，
每一句讓整個畫面淡一次（220ms）；轉場只能掛在卡片上，併進同一張卡就沒有了。
`--keep-avatars` 可以讓留言頭像在同一張卡裡一直留在場上（第一版的做法，作者沒採用）。

用法：
    python3 larch/merge_lines.py            讀線上、合併、寫到 larch/merge/（不推）
    python3 larch/merge_lines.py --check    同上，另外核對合併前後每一條路線展開成一句一句完全相同
    python3 larch/merge_lines.py --push     備份到 larch/backups/ 後逐塊 PUT，推完讀回再核對一次
    加 --cdn：同時把圖與配音換成 jsDelivr 網址（larch/main_cdn.json，main_cdn.py 產的），謝幕 ch08 只換網址不合併
"""
import copy, json, pathlib, re, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import config

ROOT = config.ROOT
OUT = ROOT / 'larch/merge'
BOARDS = ['ch01', 'ch02', 'ch03', 'ch04', 'ch05', 'ch06', 'ch07']   # ch08 謝幕不動
SPECIAL = ('chapterEnd', 'cgOps', 'variableOps', 'start', 'speakText')   # 有這些欄位的卡不併進前一張
MAX_LINES = 40   # 調查篇用過一張 44 句，Larch 播得動；超過就在立繪不變的地方切開


def lines_of(d):
    """一張對話卡展開成句子；原本就是多句卡的照用，單句卡做成一句。每句都帶這張卡的立繪。"""
    stage = copy.deepcopy(d.get('stage') or {})
    if d.get('dialogueLines'):
        out = []
        for l in d['dialogueLines']:
            l = copy.deepcopy(l)
            l.setdefault('stage', copy.deepcopy(stage))
            out.append(l)
        return out
    l = {'text': d.get('text', ''), 'emotion': d.get('emotion', ''), 'speaker': d.get('speaker', '')}
    if d.get('voiceUrl'): l['voiceUrl'] = d['voiceUrl']
    l['stage'] = stage
    return [l]


def actor_ids(stage):
    return tuple(sorted(a.get('id', '') for a in (stage or {}).get('actors', [])))


def keep_avatars(lines):
    """留言頭像在同一張卡裡留在場上，直到清場或同一個位置換人。"""
    held = {}   # slot -> actor
    for l in lines:
        acts = (l.get('stage') or {}).get('actors', [])
        if any(a.get('id') == 'actor-none' for a in acts):
            held.clear(); continue
        for a in acts:
            if str(a.get('id', '')).startswith('avatar-'):
                held[a.get('slot')] = a
        have = {a.get('slot') for a in acts if str(a.get('id', '')).startswith('avatar-')}
        for slot, a in held.items():
            if slot not in have:
                acts.append(copy.deepcopy(a))
        l['stage'] = {**(l.get('stage') or {}), 'actors': acts}
    return lines


def chains(board):
    nodes = {n['id']: n for n in board['nodes']}
    out, inn = {}, {}
    for e in board['edges']:
        out.setdefault(e['source'], []).append(e); inn.setdefault(e['target'], []).append(e)
    is_dlg = lambda i: nodes[i]['data'].get('type') == 'dialogue'

    def nxt(a):
        o = out.get(a, [])
        if len(o) != 1 or (o[0].get('data') or {}).get('condition'): return None
        t = o[0]['target']
        if t not in nodes or not is_dlg(t) or len(inn.get(t, [])) != 1: return None
        if any(nodes[t]['data'].get(k) for k in SPECIAL): return None
        return t

    linked = {nxt(a) for a in nodes if is_dlg(a)} - {None}
    result = []
    for h in nodes:
        if not is_dlg(h) or h in linked: continue
        c = [h]
        while True:
            t = nxt(c[-1])
            if not t or t in c: break
            c.append(t)
        result.append(c)
    return result, nodes, out


def split_long(cards, nodes):
    """一串展開超過 MAX_LINES 句就切開；切在前後兩張卡立繪一樣的地方，播起來看不出切口。"""
    groups, cur, n = [], [], 0
    for cid in cards:
        k = len(lines_of(nodes[cid]['data']))
        if cur and n + k > MAX_LINES:
            # 往回找一個立繪不變的切口
            cut = len(cur)
            for j in range(len(cur) - 1, 0, -1):
                if actor_ids(nodes[cur[j - 1]]['data'].get('stage')) == actor_ids(nodes[cur[j]]['data'].get('stage')):
                    cut = j; break
            groups.append(cur[:cut]); cur = cur[cut:]; n = sum(len(lines_of(nodes[c]['data'])) for c in cur)
        cur.append(cid); n += k
    if cur: groups.append(cur)
    return groups


def merge_board(board):
    board = copy.deepcopy(board)
    cs, nodes, out = chains(board)
    drop, new_edges_from = set(), {}
    merged_cards = 0
    for c in cs:
        for g in split_long(c, nodes):
            if len(g) < 2: continue
            head = nodes[g[0]]
            lines = []
            for cid in g: lines += lines_of(nodes[cid]['data'])
            for i, l in enumerate(lines): l['id'] = f'l{i}'
            if '--keep-avatars' in sys.argv: keep_avatars(lines)
            d = head['data']
            d['dialogueLines'] = lines
            d['text'] = lines[0]['text']
            d['speaker'] = lines[0].get('speaker', d.get('speaker', ''))
            d['emotion'] = lines[0].get('emotion', '')
            if lines[0].get('voiceUrl'): d['voiceUrl'] = lines[0]['voiceUrl']
            d['stage'] = copy.deepcopy(lines[0]['stage'])
            drop.update(g[1:])
            tail_edges = out.get(g[-1], [])
            new_edges_from[g[0]] = tail_edges
            merged_cards += len(g) - 1
    keep_edges = []
    for e in board['edges']:
        if e['source'] in drop or e['target'] in drop:
            continue
        if e['source'] in new_edges_from:
            continue   # 頭卡原本連到第二張的線換掉
        keep_edges.append(e)
    for head, tails in new_edges_from.items():
        for e in tails:
            e2 = copy.deepcopy(e); e2['source'] = head
            e2['id'] = f"{e['id']}" if e['id'] not in {x['id'] for x in keep_edges} else f"{e['id']}-m"
            keep_edges.append(e2)
    board['nodes'] = [n for n in board['nodes'] if n['id'] not in drop]
    board['edges'] = keep_edges
    return board, merged_cards


def script(board):
    """從起點照線走，展開成「句子與非對話卡」的序列；選項的每一條分支各走一遍。合併前後必須完全相同。"""
    nodes = {n['id']: n for n in board['nodes']}
    out = {}
    for e in board['edges']: out.setdefault(e['source'], []).append(e)
    for v in out.values(): v.sort(key=lambda e: str(e.get('sourceHandle')))
    start = [n['id'] for n in board['nodes'] if n['data'].get('start')] or [board['nodes'][0]['id']]
    seqs, stack = [], [(start[0], ())]
    seen = set()
    while stack:
        cur, path = stack.pop()
        seq = []
        while cur and (cur, len(path)) not in seen:
            seen.add((cur, len(path)))
            d = nodes[cur]['data']
            if d.get('type') == 'dialogue':
                for l in lines_of(d): seq.append(('L', l.get('speaker', ''), l.get('text', ''), l.get('voiceUrl', '')))
            else:
                seq.append(('N', d.get('type'), cur))
            o = out.get(cur, [])
            if len(o) == 1: cur = o[0]['target']
            else:
                for e in o: stack.append((e['target'], path + (cur,)))
                cur = None
        seqs.append(tuple(seq))
    return sorted(seqs)


def swapper(on=None):
    """--cdn（或 on=True）：舊網址 → jsDelivr 網址（只換整串網址，比對前後兩邊都先換，路線展開才比得起來）"""
    if not (('--cdn' in sys.argv) if on is None else on): return lambda o: o
    mapping = json.loads((ROOT / 'larch/main_cdn.json').read_text(encoding='utf-8'))
    def swap(o):
        t = json.dumps(o, ensure_ascii=False)
        for a, b in mapping.items(): t = t.replace(a, b)
        return json.loads(t)
    return swap


def main():
    proj = config.api(); proj = proj.get('project', proj)
    OUT.mkdir(parents=True, exist_ok=True)
    report, merged = [], {}
    swap = swapper()
    targets = BOARDS + (['ch08'] if '--cdn' in sys.argv else [])
    for b in proj['boards']:
        if b['id'] not in targets: continue
        if b['id'] in BOARDS: nb, k = merge_board(b)
        else: nb, k = copy.deepcopy(b), 0
        nb = swap(nb); b = swap(b)
        merged[b['id']] = nb
        before = sum(1 for n in b['nodes'] if n['data'].get('type') == 'dialogue')
        after = sum(1 for n in nb['nodes'] if n['data'].get('type') == 'dialogue')
        lines_b = sum(len(lines_of(n['data'])) for n in b['nodes'] if n['data'].get('type') == 'dialogue')
        lines_a = sum(len(lines_of(n['data'])) for n in nb['nodes'] if n['data'].get('type') == 'dialogue')
        same = script(b) == script(nb) if '--check' in sys.argv or '--push' in sys.argv else None
        report.append(f"{b['id']}: 對話卡 {before} → {after}（併掉 {k}），句子 {lines_b} → {lines_a}，卡 {len(b['nodes'])} → {len(nb['nodes'])}，線 {len(b['edges'])} → {len(nb['edges'])}" + ('' if same is None else f"，路線展開{'一致' if same else '不一致！'}"))
        if same is False: print('\n'.join(report)); sys.exit('路線展開對不上，停下來')
        (OUT / f"{b['id']}.json").write_text(json.dumps(nb, ensure_ascii=False), encoding='utf-8')
    print('\n'.join(report))
    if '--push' not in sys.argv: return
    ts = time.strftime('%Y%m%d-%H%M')
    bk = ROOT / f'larch/backups/main-{ts}-before-merge.json'; bk.parent.mkdir(exist_ok=True)
    bk.write_text(json.dumps(proj, ensure_ascii=False), encoding='utf-8'); print('備份', bk)
    # ch01 最後推：Larch 把最後一次 PUT 的白板當主線
    for bid in [x for x in targets if x != 'ch01'] + ['ch01']:
        nb = merged[bid]
        body = {k: nb[k] for k in ('id', 'kind', 'mode', 'name', 'nodes', 'edges') if k in nb}
        body['summary'] = '一句一卡合併成多句卡（作者 2026-11-04 拍板；字、配音照原樣）' + ('；圖與配音改走 jsDelivr' if '--cdn' in sys.argv else '')
        config.api(body, 'PUT', f'/boards/{bid}')
        print('推了', bid)
    back = config.api(); back = back.get('project', back)
    for b in back['boards']:
        if b['id'] in merged:
            ok = len(b['nodes']) == len(merged[b['id']]['nodes']) and len(b['edges']) == len(merged[b['id']]['edges']) and script(b) == script(merged[b['id']])
            left = len(re.findall(r'yazelin\.github\.io/glitch-vn/voice|r2\.dev/[^"]+\.(?:png|jpe?g)', json.dumps(b))) if '--cdn' in sys.argv else 0
            if left: ok = False; print(b['id'], f'還有 {left} 個舊網址')
            print(b['id'], '讀回核對', '通過' if ok else '不一致！')


if __name__ == '__main__':
    main()
