"""把 table.tsv 的立繪換進線上正篇。只動舞台上格莉奇那一個演員：換圖片網址，茶几那幾幕換成空白演員。

    python3 art/main-poses/apply.py --dry           只印每章改幾張卡、幾句，換成哪些圖
    python3 art/main-poses/apply.py --push          先存備份 → 改 → 逐章 PUT（ch01 最後）→ 讀回驗
保證：卡數、邊數、台詞、配音、其他角色不變；改完逐卡把舞台拿掉後比對，有任何不同就停，不送出。
圖片網址在 sprites.json（代號 → 網址）。決定欄有值用決定，空的用提案；wave／空白＝不動。
"""
import copy, csv, json, pathlib, sys, time
HERE = pathlib.Path(__file__).parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'larch')); sys.path.insert(0, str(HERE))
import config
from lines import walk

G = '格莉奇'


def plan():
    want = {}
    for r in csv.DictReader(open(HERE / 'table.tsv', encoding='utf-8'), delimiter='\t'):
        k = (r['決定'] or r['提案']).strip()
        if r['現在'] and k and k != 'wave': want[(r['章'], r['卡'], int(r['句']))] = k
    return want


def urls():
    return json.loads((HERE / 'sprites.json').read_text(encoding='utf-8'))


def decided():
    """table.tsv 決定欄有填的句子（作者改過的）。build 時（larch/finalize.py）蓋過規則算出來的提案。"""
    return {(r['章'], r['卡'], int(r['句'])): r['決定'].strip()
            for r in csv.DictReader(open(HERE / 'table.tsv', encoding='utf-8'), delimiter='\t') if r['決定'].strip()}


def ghosts(p):
    for b in p['boards']:
        for n in b['nodes']:
            d = n['data']
            a = next((x for x in (d.get('stage') or {}).get('actors', []) if x.get('id') == 'actor-none'), None)
            l = next((x for x in d.get('characterLayers') or [] if x.get('id') == 'layer-none'), None)
            if a and l: return a, l
    return None, None   # 這一塊版子沒有空白演員；真的要用到時 fix_* 會報錯


def fix_actors(actors, key, url, ghost):
    out = []
    for a in actors:
        if a.get('name') != G: out.append(a); continue
        if key == 'none': continue
        a = dict(a); a['url'] = url; out.append(a)
    if not out and ghost is None: raise ValueError('台上要換成空白演員，可是這一塊版子找不到 actor-none')
    return out or [copy.deepcopy(ghost)]


def fix_layers(layers, key, url, ghost):
    out = []
    for l in layers:
        if not str(l.get('id', '')).startswith(f'layer-{G}'): out.append(l); continue
        if key == 'none': continue
        l = dict(l); l['url'] = url; out.append(l)
    if not out and ghost is None: raise ValueError('台上要換成空白演員，可是這一塊版子找不到 layer-none')
    return out or [copy.deepcopy(ghost)]


def strip(d):
    d = copy.deepcopy(d); d.pop('stage', None); d.pop('characterLayers', None)
    for l in d.get('dialogueLines') or []: l.pop('stage', None)
    return d


def others(stage):
    return [a for a in (stage or {}).get('actors', []) if a.get('name') != G and a.get('id') != 'actor-none']


def apply(p, want, urls):
    ga, gl = ghosts(p); changed = {}
    for b in p['boards']:
        rows = {(cid, i) for cid, i, _, _ in walk(b)}
        nodes = {n['id']: n for n in b['nodes']}; nb = 0; nl = 0
        for cid in {c for c, _ in rows}:
            d = nodes[cid]['data']; before = copy.deepcopy(d)
            lines = d.get('dialogueLines')
            keys = {i: want.get((b['id'], cid, i)) for i in ([-1] if not lines and (b['id'], cid, -1) in want else range(len(lines or [None])))}
            if not any(keys.values()): continue
            for i, k in keys.items():
                if not k: continue
                if lines: lines[i]['stage'] = dict(lines[i].get('stage') or {}, actors=fix_actors(lines[i]['stage'].get('actors', []), k, urls.get(k), ga)); nl += 1
            k0 = keys.get(0) if lines else (keys.get(-1) or keys.get(0))
            if k0:
                d['stage'] = dict(d.get('stage') or {}, actors=fix_actors((d.get('stage') or {}).get('actors', []), k0, urls.get(k0), ga))
                if d.get('characterLayers'): d['characterLayers'] = fix_layers(d['characterLayers'], k0, urls.get(k0), gl)
                if not lines: nl += 1
            if d == before: continue   # 已經是新圖（推過一次之後讀回再套就該全部落在這裡）
            # 驗：舞台以外不變、其他角色不變
            assert strip(before) == strip(d), cid
            for s0, s1 in [(before.get('stage'), d.get('stage'))] + [(l0.get('stage'), l1.get('stage')) for l0, l1 in zip(before.get('dialogueLines') or [], d.get('dialogueLines') or [])]:
                assert others(s0) == others(s1), cid
            nb += 1
        if nb: changed[b['id']] = (nb, nl)
    return changed


def main():
    urls = json.loads((HERE / 'sprites.json').read_text()) if (HERE / 'sprites.json').exists() else {}
    want = plan()
    missing = sorted({k for k in want.values() if k != 'none' and k not in urls})
    if missing and '--dry' not in sys.argv: raise SystemExit(f'sprites.json 沒有這些圖的網址：{missing}')
    p = config.api(); p = p.get('project', p); orig = copy.deepcopy(p)
    n0 = {b['id']: (len(b['nodes']), len(b['edges'])) for b in p['boards']}
    changed = apply(p, want, urls or {k: f'<{k}>' for k in set(want.values())})
    for bid, (nb, nl) in changed.items(): print(f'{bid}：{nb} 張卡、{nl} 句')
    assert {b['id']: (len(b['nodes']), len(b['edges'])) for b in p['boards']} == n0
    if '--push' not in sys.argv: return
    ts = time.strftime('%Y%m%d-%H%M')
    bk = ROOT / f'larch/backups/main-{ts}-before-poses.json'; bk.write_text(json.dumps(orig, ensure_ascii=False))
    print('備份', bk.relative_to(ROOT))
    order = sorted(changed, key=lambda b: (b == 'ch01', b))   # ch01 最後推：Larch 把最後一次 PUT 的白板當主線
    for bid in order:
        board = next(b for b in p['boards'] if b['id'] == bid)
        config.api(board, 'PUT', f'/boards/{bid}'); print('推了', bid); time.sleep(1)
    back = config.api(); back = back.get('project', back)
    got = apply(copy.deepcopy(back), want, urls)
    print('讀回：再套一次還要改的卡', got or '沒有（全部已經是新圖）')
    for b0, b1 in zip(sorted(orig['boards'], key=lambda b: b['id']), sorted(back['boards'], key=lambda b: b['id'])):
        assert (len(b0['nodes']), len(b0['edges'])) == (len(b1['nodes']), len(b1['edges'])), b0['id']
        s0 = {n['id']: strip(n['data']) for n in b0['nodes']}; s1 = {n['id']: strip(n['data']) for n in b1['nodes']}
        assert s0 == s1, f'{b0["id"]} 舞台以外有變動'
    print('讀回驗過：卡數、邊數、台詞與配音都沒變')


if __name__ == '__main__':
    main()
