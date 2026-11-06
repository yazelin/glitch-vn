"""推薦改法的機械檢查：抓第一批推錯的三種樣子（人稱換掉、多出前後文沒有的名詞、刪成空的），
加上評審分歧、只有 speak-tw 抓到。只標出來給人讀，不判對錯。用法：BATCH=-2 python3 tools/line_review_check.py <work> -2，結果寫到 design/台詞審查-2026-11/<work>/check<B>.json。
2026-11-06 第二批複查：評審一次只看得到前後幾行，看不出全書反覆出現的詞句（「外套的內側」「紙板人形」「聯動」），所以加了「斷了重複詞句」。"""
import json, re, sys, collections, logging
import jieba, jieba.posseg as pseg
jieba.setLogLevel(logging.WARNING)
sys.path.insert(0, '/home/ct/glitch-vn/tools'); import line_review as lr
work, B = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
D = lr.OUT / work
rows = json.loads((D / 'lines.json').read_text(encoding='utf-8')); pos = {r['id']: k for k, r in enumerate(rows)}
flags = {f['id']: f for f in json.loads((D / f'flags{B}.json').read_text(encoding='utf-8'))}
cands = json.loads((D / f'candidates{B}.json').read_text(encoding='utf-8')); picks = json.loads((D / f'picks{B}.json').read_text(encoding='utf-8'))
PRON = ['我們', '你們', '妳們', '她們', '他們', '我', '你', '妳', '她', '他', '它', '牠']
NEG = ['沒有', '不', '沒', '別', '未', '無']
NUM = re.compile(r'[0-9０-９]+(?:\.[0-9]+)?|[零〇一二三四五六七八九十百千萬兩]{2,}|[一二三四五六七八九十兩](?=[點年月日天個次秒分週人頁版號樓句張台])')
def count(s, words):
    c = collections.Counter()
    for w in words:   # 長的先數，數過就挖掉，「我們」不會再算成「我」
        c[w] += s.count(w); s = s.replace(w, '\0')
    return +c
def nouns(s): return {w for w, f in pseg.cut(s) if f.startswith('n') and len(w) >= 2}
ALL = ' '.join(r['text'] for r in rows)
LABELS = {r['who'] for r in rows}
def refrains(i, old, new):
    """原句裡在全書別處還出現兩次以上、改法卻拿掉的詞句（四到八個字），挑最長的不重疊幾個。"""
    rest = ALL.replace(old, '', 1); got = []
    for n in range(8, 3, -1):
        for k in range(len(old) - n + 1):
            g = old[k:k + n]
            if re.search(r'[\s，。、！？「」／/]', g) or g in new or any(g in x for x in got): continue
            if rest.count(g) >= 2: got.append(g)
    return [f'{g}（別處 {rest.count(g)} 次）' for g in got[:3]]
def check(i, old, new):
    p = picks[i]; f = flags[i]; out = []
    if not new.strip(): return ['刪成空的']
    if count(old, PRON) != count(new, PRON): out.append(f'人稱 {dict(count(old, PRON))}→{dict(count(new, PRON))}')
    if count(old, NEG) != count(new, NEG): out.append('否定詞數量變了')
    if sorted(NUM.findall(old)) != sorted(NUM.findall(new)): out.append(f'數字 {NUM.findall(old)}→{NUM.findall(new)}')
    ctx = ' '.join(r['text'] for r in lr.context(rows, [pos[i]], before=4, after=3)) + old
    extra = sorted(w for w in nouns(new) if w not in ctx)
    if extra: out.append('多出名詞 ' + '、'.join(extra))
    rf = refrains(i, old, new)
    if rf: out.append('斷了重複詞句 ' + '、'.join(rf))
    lab = lambda t: {w for x in t.split('\n') for w in LABELS if w and x.startswith(w + '：')}
    if lab(new) - lab(old): out.append('混進講者標籤 ' + '、'.join(sorted(lab(new) - lab(old))))
    if old.count('\n') != new.count('\n'): out.append('段數變了')
    tops = collections.Counter(j['top'] for j in p['judges'])
    if p['score'][p['best']] - p['score']['原'] <= 1 or tops[p['best']] < 2: out.append(f"評審分歧 {p['score']}")
    if len(f.get('votes') or []) < 2: out.append('只有 speak-tw 抓到')
    return out
res = {}
for i, old, new in lr.final_changes(work):
    if i in flags: res[i] = {'old': old, 'new': new, 'who': flags[i]['who'], 'hits': check(i, old, new)}
hit = {i: v for i, v in res.items() if v['hits']}
print(work, B or '第一批', '推薦改寫', len(res), '句；有標記', len(hit), '句')
print('  ', collections.Counter(h.split(' ')[0] for v in hit.values() for h in v['hits']).most_common())
(D / f'check{B}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
