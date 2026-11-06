#!/usr/bin/env python3
"""台詞審查（2026-11-04 作者：「尋找台詞語句不通順的部份出來，並每句提供修改建議後評選出適合的語句」「以前的作品就是很多 AI 味」）。

    python3 tools/line_review.py export main|inv     線上專案攤成逐句（含配音網址）→ design/台詞審查-2026-11/<作品>/lines.json
    python3 tools/line_review.py detect main|inv     speak-tw ＋三個模型各讀一遍，兩票以上或 speak-tw 抓到才算 → flags.json
    python3 tools/line_review.py suggest main|inv    每句三個改法 → candidates.json
    python3 tools/line_review.py judge main|inv      三個模型把「原句＋三個改法」排名次，算總分 → picks.json

判準見 CRITERIA；角色的聲音照 larch/setup.py 的 PROFILE。這支只產建議，不改線上、不重配。
"""
import concurrent.futures as cf, json, os, pathlib, random, re, subprocess, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/台詞審查-2026-11'
B = os.environ.get('BATCH', '')   # 第二批起：BATCH=-2 讀寫 flags-2.json、candidates-2.json、picks-2.json
PROJ = {'main': 'project-bec1644c-0dfe-4447-86c0-0c592e2f939f', 'inv': 'project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4'}
# 作者 2026-11-04：「是不是用了太多其他模型，你只使用 deepseek 4.1 flash 就好」——llmshare 預設只開這一個，其他模型要 LLMSHARE_ALLOW_ANY。
# 第一批與正篇第二批是 deepseek-v4-pro、kimi-k3、qwen3.5:397b 三個評的；之後偵測、改寫、評審都只用這一個。
MODELS = ['deepseek-v4.1-flash:1017']
# 作者：評比時用 deepseek-v4.1-flash:1017 評三次當三個評審（每次洗不同的順序）。kimi-k3 這類貴的模型不用（推理模型，想的部分也算錢）。
JUDGES = [(MODELS[0], n) for n in (1, 2, 3)]
BASE = os.environ.get('LLMSHARE_BASE_URL', 'https://llm-share.duotify.com/v1')

STORY = {'main': """《格莉奇與黑洞先生》七章視覺小說。AI 虛擬主播格莉奇只有 4KB 的記憶，每晚睡前抄守則本第一頁：六個名字，加上第七行她自己寫的「還有一個。不要問他是誰。」
室友黑洞先生話很少，吃被忘掉的事。旁白冷靜、短句、散文，看到什麼寫什麼。聊天室的字是觀眾打的。""",
         'inv': """《格莉奇與黑洞先生・調查篇》。主角（旁白稱「她」，講者名「玩家」）在格莉奇住的那棟樓與附近調查「不該存在的東西」，
一天一天跟住戶、店員、配角打聽。格莉奇只隔著螢幕講話（廣告、直播）。主角的筆記平穩，像在唸自己的筆記。"""}

CRITERIA = """要找的：
1. 不通順：讀起來卡、語序怪、主詞或指代不清、前後接不上、翻譯腔（「進行」「被……所」「對於……來說」「一個……的存在」）。
2. 不像台灣人會講的話：口語台詞寫得太書面，或用到中國用語。
3. AI 味：格言式或金句式的收尾、「不是 X，是 Y」的假對比、三段排比、旁白直接替人物下情緒結論、空泛或硬湊的比喻、
   同一種句型一直重複（「像……一樣」「那種……的」）、為了好聽犧牲意思。
不要抓的（這部作品刻意的風格）：旁白的冷靜短句；反覆出現的意象（電視上的雪、第七行、守則本）；格莉奇講精準的數字（她是 AI）；
0x 極簡；貓草在聊天室不打標點、用刪節號；黑洞先生一兩句就講完、問句不用問號的語氣；角色的口頭禪。"""


# 調查篇的講者名跟正篇不同；聲音照 design/調查篇-台詞審查-2026-10-01.md 第一節那張表
INV = {'管理員': '公事公辦，講到自己的地盤就停不下來', '修收音機的': '諾亞。不問、溫和、每次都重新回答一遍', '畫她的人': '斑比。猶豫、焦慮、話講出口又收回',
       '斑比': '猶豫、焦慮、話講出口又收回', '客人': '貓草。隨便、頂嘴、怕頻道變紅', '經紀人': '鐵塔。俐落，沒有多餘情緒',
       '0x': '精準，把最重要的那件留在嘴裡', '店員': '有點累，可是客氣', '材料行老闆': '短、直接，記得問題不記得臉', '櫃檯': '標準話術，一句都不多',
       '保全': '慢、話長，一個人守久了', '黑洞先生': '沉穩、話少、脾氣好', '住戶': '沉穩、話少、脾氣好', '格莉奇': '只隔著螢幕講話（廣告、直播）',
       '玩家': '主角。平穩，像在唸自己的筆記', '旁白': '冷靜，指主角一律用「她」'}


def profiles(work='main'):
    if work == 'inv': return INV
    src = (ROOT / 'larch/setup.py').read_text(encoding='utf-8')
    i = src.index('PROFILE = {'); j = src.index('\n}\n', i) + 3; ns = {}; exec(src[i:j], ns)
    return {k: ' / '.join(x for x in v[1:4] if x) for k, v in ns['PROFILE'].items()}


RPM_FILE = pathlib.Path.home() / '.cache/llmshare-rpm'


def rpm_slot(limit=13):
    """llmshare 這把金鑰每分鐘 15 次；本機所有呼叫共用這份時間戳（同 xu/審稿/scene_review.py 的 rpm_slot）。
    批次派工上限 13，留 2 個給閘門讀稿人（feedback_llmshare_cheap_labor）。2026-11-04 這支一開始沒走限速，一直撞 429。"""
    import fcntl
    RPM_FILE.parent.mkdir(exist_ok=True)
    while True:
        with open(RPM_FILE, 'a+') as f:
            fcntl.flock(f, fcntl.LOCK_EX); f.seek(0); now = time.time()
            ts = [float(x) for x in f.read().split() if now - float(x) < 60]
            if len(ts) < limit:
                f.seek(0); f.truncate(); f.write(' '.join(map(str, ts + [now]))); return
            wait = 60.5 - (now - min(ts))
        time.sleep(wait)


def api(model, prompt, max_tokens=8000, tries=3):
    body = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': 0.2}
    for i in range(tries):
        rpm_slot()
        try:
            r = urllib.request.Request(BASE + '/chat/completions', json.dumps(body).encode(),
                                       {'Authorization': f"Bearer {os.environ['LLMSHARE_API_KEY']}", 'Content-Type': 'application/json', 'User-Agent': 'glitch-vn/1.0'})
            ch = json.load(urllib.request.urlopen(r, timeout=900))['choices'][0]
            if not (ch['message'].get('content') or '').strip() and ch.get('finish_reason') == 'length':
                print(f'  {model} 想太久，輸出額度用完還沒給答案（max_tokens={max_tokens}）', flush=True)
            return ch['message'].get('content') or ''
        except Exception as e:
            if i == tries - 1: print(f'  {model} 失敗：{str(e)[:120]}'); return ''
            time.sleep((30 if '429' in str(e) else 10) * (i + 1))


def json_in(text):
    m = re.search(r'\[.*\]', text, re.S)
    try: return json.loads(m.group(0)) if m else []
    except Exception: return []


def export(work):
    sys.path.insert(0, str(ROOT / 'larch')); sys.path.insert(0, str(ROOT / 'art/main-poses'))
    from lines import walk
    req = urllib.request.Request(f'https://larch.ink/api/agent/projects/{PROJ[work]}', headers={
        'User-Agent': 'glitch-vn/1.0', 'Authorization': 'Bearer ' + pathlib.Path.home().joinpath('.config/larch/key').read_text().strip()})
    p = json.load(urllib.request.urlopen(req, timeout=300)); p = p.get('project', p)
    rows = []
    from merge_lines import lines_of
    def every(b):   # 調查篇靠調查板分流，從起點沿線走只走得到開場；改成照版子上的卡片順序全部攤開
        for n in b['nodes']:
            d = n['data']
            if d.get('type') == 'dialogue':
                for i, l in enumerate(lines_of(d)): yield n['id'], i, l, d.get('background') or ''
            elif d.get('type') in ('choice', 'scene') and d.get('text'):
                yield n['id'], -1, {'text': d['text'], 'speaker': ''}, d.get('background') or ''
    for b in p['boards']:
        for cid, i, l, bg in (walk(b) if work == 'main' else every(b)):
            t = (l.get('text') or '').strip()
            if not t: continue
            rows.append({'id': f"{b['id']}/{cid}/{i}", 'board': b['id'], 'card': cid, 'i': i, 'bg': bg.rsplit('/', 1)[-1][:60],
                         'who': l.get('speaker') or '旁白', 'emo': l.get('emotion') or '', 'text': t, 'voice': l.get('voiceUrl') or ''})
    d = OUT / work; d.mkdir(parents=True, exist_ok=True)
    (d / 'lines.json').write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding='utf-8')
    print(work, len(rows), '句，有配音', sum(1 for r in rows if r['voice']))


def detect(work):
    d = OUT / work; rows = json.loads((d / 'lines.json').read_text(encoding='utf-8'))
    # speak-tw：一句一行
    txt = d / '_speak.txt'; txt.write_text('\n'.join(f"{r['id']}｜{r['who']}｜{r['text'].replace(chr(10), ' / ')}" for r in rows) + '\n', encoding='utf-8')
    out = subprocess.run(['speak-tw', str(txt)], capture_output=True, text=True).stdout
    rule, st = '', {}
    for line in out.splitlines():
        if line and not line.startswith(' ') and '（' in line: rule = line.split('　')[0].strip()
        m = re.search(r'_speak\.txt:(\d+)\s', line)
        if m: st.setdefault(rows[int(m.group(1)) - 1]['id'], []).append(rule)
    txt.unlink()
    print('speak-tw 抓到', len(st), '句')
    prof = profiles(work)
    chunks, cur = [], []
    for r in rows:
        if cur and (len(cur) >= 45 or cur[-1]['board'] != r['board']): chunks.append(cur); cur = []
        cur.append(r)
    if cur: chunks.append(cur)
    def ask(model, ch):
        who = sorted({r['who'] for r in ch})
        prompt = f"""你是台灣的小說編輯，替這部作品抓台詞與旁白的問題。

{STORY[work]}

這一段出現的人物與聲音：
""" + '\n'.join(f'- {w}：{prof.get(w, "（配角）")}' for w in who) + f"""

{CRITERIA}

下面是這一段的每一句，格式是「編號｜講者｜內容」（內容裡的 / 是換行）。只列出有問題的句子。
輸出 JSON 陣列，每一項：{{"id": "編號", "type": "不通順|不像台灣口語|AI味|接不上", "why": "一句話說哪裡有問題", "level": 1 到 3}}
level 3＝一定要改，2＝建議改，1＝小地方。沒有問題就回 []。只回 JSON。

""" + '\n'.join(f"{r['id']}｜{r['who']}｜{r['text'].replace(chr(10), ' / ')}" for r in ch)
        return model, [x for x in json_in(api(model, prompt, max_tokens=64000)) if isinstance(x, dict) and x.get('id')]   # 推理模型想的也算額度，8000 會被想完
    votes = {}
    with cf.ThreadPoolExecutor(6) as ex:
        futs = [ex.submit(ask, m, ch) for ch in chunks for m in MODELS]
        for n, f in enumerate(cf.as_completed(futs), 1):
            model, items = f.result()
            for x in items: votes.setdefault(x['id'], []).append({'model': model, 'type': x.get('type', ''), 'why': x.get('why', ''), 'level': x.get('level', 1)})
            if n % 10 == 0: print(f'  {n}/{len(futs)}', flush=True)
    ids = {r['id'] for r in rows}
    flags = []
    for r in rows:
        v = [x for x in votes.get(r['id'], []) if r['id'] in ids]
        models = {x['model'] for x in v}
        if len(models) >= 2 or r['id'] in st:
            flags.append({**r, 'votes': v, 'speak_tw': st.get(r['id'], []), 'n': len(models), 'level': max([int(x.get('level') or 1) for x in v] or [2])})
    tag = os.environ.get('DETECT_TAG', '')   # 重跑時另存，不蓋掉已經做完改法與評審的那一份
    (d / f'votes{tag}.json').write_text(json.dumps(votes, ensure_ascii=False, indent=1), encoding='utf-8')
    (d / f'flags{tag}.json').write_text(json.dumps(flags, ensure_ascii=False, indent=1), encoding='utf-8')
    print(work, '抓到', len(flags), '句（兩票以上或 speak-tw）；一票的', sum(1 for k, v in votes.items() if len({x["model"] for x in v}) == 1))


def context(rows, idx, before=3, after=2):
    i = idx[0]
    return [rows[k] for k in range(max(0, i - before), min(len(rows), i + after + 1))]


def suggest(work):
    """每句三個改法。劇本改稿照作者的習慣派 codex -m gpt-6.1-sol（feedback_codex_model_choice），一章一次。"""
    d = OUT / work; rows = json.loads((d / 'lines.json').read_text(encoding='utf-8'))
    flags = json.loads((d / f'flags{B}.json').read_text(encoding='utf-8')); pos = {r['id']: k for k, r in enumerate(rows)}
    prof = profiles(work); groups = {}
    for f in flags:
        g = groups.setdefault(f['board'], [[]])
        if len(g[-1]) >= 25: g.append([])
        g[-1].append(f)
    groups = {f'{b}-{n}': fs for b, gs in groups.items() for n, fs in enumerate(gs)}
    def run(board, fs):
        blocks = []
        for f in fs:
            ctx = context(rows, [pos[f['id']]])
            why = '；'.join(sorted({v['why'] for v in f['votes'] if v.get('why')})[:3] + f['speak_tw'])
            blocks.append(f"【{f['id']}】講者：{f['who']}（{prof.get(f['who'], '配角')}）\n被指出的問題：{why}\n前後文：\n" +
                          '\n'.join(('→ ' if c['id'] == f['id'] else '  ') + f"{c['who']}：{c['text'].replace(chr(10), ' / ')}" for c in ctx))
        prompt = f"""你是台灣的小說編輯。{STORY[work]}

下面每一句都被抓出有問題（「→」那一行是要改的句子）。每句給三個改法：
- 意思、資訊、角色的聲音都不變，不加新的情節或設定，前後文接得上
- 長度跟原句差不多（這句要重新配音，差太多會改掉節奏）；原句裡的「 / 」是換行，改法也可以用
- 改掉被指出的問題，也不要帶進新的 AI 味：不要「不是 X，是 Y」、不要金句收尾、不要三段排比、不要替人物下情緒結論
- 三個改法要真的不一樣：a 最小改動、b 重組句子、c 更口語或更簡潔
- 正體中文、台灣用語、全形標點
只輸出 JSON 陣列：[{{"id": "編號", "a": "…", "b": "…", "c": "…", "note": "一句話說改了什麼"}}]

""" + '\n\n'.join(blocks)
        out = d / f'_suggest-{board}{B}.txt'
        if out.exists() and json_in(out.read_text(encoding='utf-8')):   # 已經有答案的組不重跑（可以中斷續跑）
            got = json_in(out.read_text(encoding='utf-8')); print(board, len(fs), '句 → 沿用', len(got), flush=True); return got
        if os.environ.get('CODEX_OFF'):   # codex 額度用完時：把同一份提示詞寫成檔，交給別的寫手照答，答案寫回 out
            (d / f'_prompt-{board}{B}.txt').write_text(prompt, encoding='utf-8'); print(board, len(fs), '句 → 寫成提示詞檔', flush=True); return []
        if os.environ.get('WRITER', 'deepseek') == 'deepseek':   # 同上：改寫也只用 deepseek-v4.1-flash
            out.write_text(api(MODELS[0], prompt, max_tokens=64000), encoding='utf-8')
            got = json_in(out.read_text(encoding='utf-8')); print(board, len(fs), '句 → 拿到', len(got), flush=True); return got
        r = subprocess.run(['codex', 'exec', '-m', 'gpt-6.1-sol', '-s', 'read-only', '--skip-git-repo-check', '-o', str(out), prompt],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, cwd=str(d))
        if not out.exists(): (d / f'_suggest-{board}.log').write_text((r.stdout or '')[-3000:] + '\n----\n' + (r.stderr or '')[-3000:], encoding='utf-8')   # 2026-11-04 調查篇第二批整批沒拿到，留下錯誤訊息
        got = json_in(out.read_text(encoding='utf-8')) if out.exists() else []
        print(board, len(fs), '句 → 拿到', len(got), flush=True)
        return got
    who = {f['id']: f['who'] for f in flags}; orig = {f['id']: f['text'] for f in flags}
    def unlabel(i, t):   # 2026-11-06：deepseek 照前後文「講者：台詞」的格式把講者抄進改法（調查篇 180 個），原句開頭沒有的就拿掉
        p = f"{who.get(i, '')}："
        return ' / '.join(x[len(p):] if x.startswith(p) and not orig.get(i, '').startswith(p) else x for x in t.split(' / '))
    cands = {}
    with cf.ThreadPoolExecutor(4) as ex:
        for got in ex.map(lambda kv: run(*kv), groups.items()):
            for x in got:
                if isinstance(x, dict) and x.get('id'):
                    for k in 'abc':
                        if isinstance(x.get(k), str): x[k] = unlabel(x['id'], x[k])
                    cands[x['id']] = x
    (d / f'candidates{B}.json').write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding='utf-8')
    print(work, '有改法的', len(cands), '／', len(flags))


def judge(work):
    """三個模型把「原句＋a、b、c」排名次（每個評審看到的順序都洗過，看不到哪一個是原句），照名次給 3/2/1/0 分加總。"""
    d = OUT / work; rows = json.loads((d / 'lines.json').read_text(encoding='utf-8')); pos = {r['id']: k for k, r in enumerate(rows)}
    flags = {f['id']: f for f in json.loads((d / f'flags{B}.json').read_text(encoding='utf-8'))}
    cands = json.loads((d / f'candidates{B}.json').read_text(encoding='utf-8')); prof = profiles(work)
    ids = [i for i in flags if i in cands]
    old = json.loads((d / f'picks{B}.json').read_text(encoding='utf-8')) if os.environ.get('REDO_SHORT') else {}
    if old: ids = [i for i in ids if len(old.get(i, {}).get('judges', [])) < len(JUDGES)]   # 中途撞到預算上限：只重評評審不滿三位的句子，評滿的沿用
    batches = [ids[k:k + 8] for k in range(0, len(ids), 8)]   # 推理模型想的部分也算在 max_tokens 裡，一批太多會想到額度用完、答案是空的
    def ask(model, batch, seed):
        rnd = random.Random(seed); order = {}; blocks = []
        for i in batch:
            opts = [('原', flags[i]['text']), ('a', cands[i]['a']), ('b', cands[i]['b']), ('c', cands[i]['c'])]; rnd.shuffle(opts)
            order[i] = {str(n + 1): k for n, (k, _) in enumerate(opts)}
            ctx = context(rows, [pos[i]])
            blocks.append(f"【{i}】講者：{flags[i]['who']}（{prof.get(flags[i]['who'], '配角')}）\n前後文：\n" +
                          '\n'.join(('→ ' if c['id'] == i else '  ') + f"{c['who']}：{c['text'].replace(chr(10), ' / ')}" for c in ctx) + '\n候選：\n' +
                          '\n'.join(f"{n + 1}. {t.replace(chr(10), ' / ')}" for n, (_, t) in enumerate(opts)))
        prompt = f"""你是台灣的小說編輯，替這部作品選台詞。{STORY[work]}

{CRITERIA}

每一題有四個候選，替「→」那一句選。好的標準：通順、像這個人會講的話、沒有 AI 味、跟前後文接得上、意思沒走掉。
把四個候選從好到壞排名次。只輸出 JSON 陣列：[{{"id": "編號", "rank": ["最好的號碼", "…", "…", "最差的號碼"], "why": "一句話說第一名為什麼好"}}]

""" + '\n\n'.join(blocks)
        res = {}
        for x in json_in(api(model.split('#')[0], prompt, max_tokens=64000)):
            if isinstance(x, dict) and x.get('id') in order and isinstance(x.get('rank'), list):
                res[x['id']] = {'rank': [order[x['id']].get(str(r)) for r in x['rank']], 'why': x.get('why', '')}
        return model, res
    score = {i: {'原': 0, 'a': 0, 'b': 0, 'c': 0} for i in ids}; why = {i: [] for i in ids}
    with cf.ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(ask, f'{m}#{n}', b, n * 7 + k) for k, b in enumerate(batches) for m, n in JUDGES]
        for f in cf.as_completed(futs):
            model, res = f.result()
            for i, v in res.items():
                for pts, k in zip((3, 2, 1, 0), v['rank']):
                    if k in score[i]: score[i][k] += pts
                why[i].append({'model': model, 'top': v['rank'][0] if v['rank'] else None, 'why': v['why']})
    picks = {**old, **{i: {'score': score[i], 'best': max(score[i], key=lambda k: (score[i][k], k == '原')), 'judges': why[i]} for i in ids}}
    (d / f'picks{B}.json').write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding='utf-8')
    import collections
    print(work, '評完', len(picks), '句；勝出', collections.Counter(p['best'] for p in picks.values()))


def final_changes(work, overrides=None):
    """評審推薦（或作者在頁面上改的）＝要換成的字。回傳 [(id, 原句, 新句)]，選原句的不列。"""
    d = OUT / work
    flags = {f['id']: f for f in json.loads((d / f'flags{B}.json').read_text(encoding='utf-8'))}
    cands = json.loads((d / f'candidates{B}.json').read_text(encoding='utf-8')); picks = json.loads((d / f'picks{B}.json').read_text(encoding='utf-8'))
    ov = d / 'overrides.json'   # 作者在頁面上改的，或審查時發現評審選錯的（附理由）
    overrides = {**(json.loads(ov.read_text(encoding='utf-8')) if ov.exists() else {}), **(overrides or {})}
    out = []
    for i, p in picks.items():
        o = overrides.get(i) or {}
        if (o.get('note') or '').strip(): new = o['note'].strip()
        else:
            k = o.get('choice') or p['best']
            if k == '原': continue
            new = cands[i][k]
        new = new.replace(' / ', '\n')
        old = flags[i]['text']
        if old.count('\n') != new.count('\n'): new = new.replace('\n', '')   # 段數不同就併成一段，build 的呼叫形狀不變
        if not new.strip():   # 2026-11-06：第一批 ch05-052 刪成空字串，場景卡變成一個空白框。刪整句要改卡片結構，不能換成空字串
            print(f'  {i}：改法是整句刪掉，build 不能放空字串，先留原句（要刪得手動改卡片）'); continue
        if new != old: out.append((i, old, new))
    return out


def apply_main(dry):
    """正篇：改 larch/build_chNN.py 裡的字串。用 AST 找字串（相鄰字串在 AST 裡是一個值），整句對得上就換整個，
    不然照換行拆開一段一段對（narrate 的每個參數是一段）。每一段要剛好出現一次，不然停下來。"""
    import ast
    changes = final_changes('main')
    by_file = {}
    for i, old, new in changes: by_file.setdefault(ROOT / f"larch/build_{i.split('/')[0]}.py", []).append((i, old, new))
    for path, items in by_file.items():
        src = path.read_text(encoding='utf-8'); lines = src.splitlines(keepends=True)
        offs = [0]
        for l in lines: offs.append(offs[-1] + len(l))
        consts = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        def pos(n):   # col_offset 是 UTF-8 位元組數，要換成字元位置
            a = offs[n.lineno - 1] + len(lines[n.lineno - 1].encode('utf-8')[:n.col_offset].decode('utf-8'))
            b = offs[n.end_lineno - 1] + len(lines[n.end_lineno - 1].encode('utf-8')[:n.end_col_offset].decode('utf-8'))
            return a, b
        edits = []
        for i, old, new in items:
            whole = [n for n in consts if n.value == old]
            if not whole and sum(1 for n in consts if n.value == new) == 1: continue   # 整句已經換過
            if len(whole) != 1 and old.count('\n') != new.count('\n'):   # 2026-11-06：段數不同時 zip 會把多的那段配錯、重複一段
                raise SystemExit(f'{path.name} {i}：原句 {old.count(chr(10)) + 1} 段、新句 {new.count(chr(10)) + 1} 段，要手動改卡片')
            pairs = [(old, new)] if len(whole) == 1 else list(zip(old.split('\n'), new.split('\n')))
            find = lambda v: [n for n in consts if n.value == v or (n.value.endswith('：' + v) and '：' not in n.value[:-len(v) - 1])]   # 聊天卡的字串是「講者：內容」
            for o, nw in pairs:
                if o == nw: continue   # 沒改的那一段不用找
                hit = find(o)
                if not hit and len(find(nw)) == 1: continue   # 已經換過（可以重跑）
                if len(hit) != 1: raise SystemExit(f'{path.name} {i}：「{o[:20]}」找到 {len(hit)} 處，停下來')
                edits.append((*pos(hit[0]), json.dumps(hit[0].value[:len(hit[0].value) - len(o)] + nw, ensure_ascii=False), i))
        for a, b, lit, i in sorted(edits, reverse=True): src = src[:a] + lit + src[b:]
        ast.parse(src)
        print(path.name, len(items), '句', len(edits), '個字串', '（試算）' if dry else '')
        if not dry: path.write_text(src, encoding='utf-8')
    return changes


def larch_voice_main():
    """正篇改到的句子裡，講者走 Larch 音色的（鐵塔、諾亞、黑洞先生，voice.EXTERNAL）要請平台照板上的字重唸。
    做法跟 tools/gen_larch_voice.py 一樣：帶 boardId、nodeId、lineIndex，回傳的字要跟我們要的一樣才收。"""
    sys.path.insert(0, str(ROOT / 'larch')); import config, voice as V
    UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
    spoken_p = ROOT / 'art/voice/spoken.json'; spoken = json.loads(spoken_p.read_text(encoding='utf-8'))
    flags = {f['id']: f for f in json.loads((OUT / f'main/flags{B}.json').read_text(encoding='utf-8'))}   # 第二批讀 flags-2.json
    done = []
    for i, old, new in final_changes('main'):
        f = flags[i]
        if f['who'] not in V.EXTERNAL or not f['voice']: continue
        board, card, idx = i.split('/'); k = V.key(f['who'], new, f['emo'] or None)
        body = {'nodeId': card, 'boardId': board, 'lineIndex': int(idx), 'voiceId': V.LARCH_VOICE[f['who']][0], 'emotion': f['emo'] or ''}
        r = config.api(body, 'POST', '/voice/generate')
        got = (r.get('text') or '').strip(); url = (r.get('asset') or {}).get('url')
        if got != new.strip() or not url: print('  ★', i, '平台唸的不是新字或沒有網址：', got[:20]); continue
        data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120).read()
        (ROOT / f'art/voice/{k}.mp3').write_bytes(data); spoken[k] = new; done.append(k)
        print(' ', f['who'], k, len(data), 'bytes', new[:20].replace(chr(10), '/'), flush=True); time.sleep(0.5)
    spoken_p.write_text(json.dumps(spoken, ensure_ascii=False, indent=0), encoding='utf-8')
    print('平台重唸', len(done), '句')


# 調查篇：板上存的是顯示名（larch/inv/push.py 的 DISPLAY、names.PROSE），配音照本名
INV_SRC = {'修收音機的': '諾亞', '客人': '貓草', '經紀人': '鐵塔', '畫她的人': '斑比'}
INV_PROJ = PROJ['inv']


def inv_plan():
    """調查篇要改的每一句。kind：A＝不用重配（本來就沒聲音，或只改括號裡的舞台指示，配音管線會濾掉括號）、
    L＝本機重配（voice.VOICE）、X＝Larch 音色重配（voice.LARCH_VOICE，平台照板上的字唸）。"""
    sys.path.insert(0, str(ROOT / 'larch')); import voice as V
    flags = {f['id']: f for f in json.loads((OUT / 'inv' / f'flags{B}.json').read_text(encoding='utf-8'))}
    strip = lambda t: re.sub(r'（[^）]*）', '', t)
    out = []
    for i, old, new in final_changes('inv'):
        f = flags[i]; board, card, idx = i.rsplit('/', 2); src = INV_SRC.get(f['who'], f['who'])
        if not f['voice'] or strip(old) == strip(new): kind = 'A'
        elif src in V.LARCH_VOICE: kind = 'X'
        elif V.VOICE.get(src): kind = 'L'
        else: kind = 'A'; print('  ★ 有配音但找不到聲音：', i, f['who'])
        out.append({'id': i, 'board': board, 'card': card, 'idx': int(idx), 'who': f['who'], 'src': src, 'emo': f['emo'] or '',
                    'old': old, 'new': new, 'kind': kind, 'key': V.key(src, new, f['emo'] or None)})
    return out


def _tool_on(items, tool, args=()):
    """壓響度、ASR 這兩支照 gen_voice.utterances() 挑檔；調查篇改過的字不在那裡面，所以塞一份清單給它們。"""
    sys.path.insert(0, str(ROOT / 'tools')); import gen_voice as G
    one = [(x['src'], x['new'], x['emo'] or None, x['key']) for x in items]
    code = (f"import sys; sys.path[:0]=[{str(ROOT / 'tools')!r},{str(ROOT / 'larch')!r}]; import gen_voice as G; "
            f"G.utterances=lambda: {one!r}; import runpy; sys.argv=[{tool!r}]+{list(args)!r}; runpy.run_path({str(ROOT / f'tools/{tool}.py')!r}, run_name='__main__')")
    py = str(pathlib.Path.home() / 'voice-venv/bin/python') if tool == 'asr_audit' else sys.executable
    return subprocess.run([py, '-c', code], capture_output=True, text=True, cwd=str(ROOT))


def inv_gen_local(items):
    sys.path.insert(0, str(ROOT / 'larch')); import voice as V
    jobs = [{'out': str(ROOT / f"art/voice/{x['key']}.wav"), 'text': V.to_speech(x['new']), 'prompt_wav': str(ROOT / V.VOICE[x['src']][0]),
             'prompt_text': V.VOICE[x['src']][1], 'speed': V.VOICE[x['src']][2], 'instruct': V.instruct_for(x['src'], x['emo'] or None, x['new'])} for x in items]
    jf = ROOT / 'art/voice/jobs-review.json'; jf.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding='utf-8')
    env = dict(os.environ, MODELSCOPE_OFFLINE='1', HF_HUB_OFFLINE='1')
    subprocess.run([str(pathlib.Path.home() / 'voice-venv/bin/python'), '-u', str(ROOT / 'tools/voice_batch.py'), '--jobs', str(jf), '--force'], env=env, capture_output=True)
    for x in items:
        w = ROOT / f"art/voice/{x['key']}.wav"
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', str(w), '-ac', '1', '-b:a', '64k', str(w.with_suffix('.mp3'))])
    jf.unlink()


def inv_boards():
    sys.path.insert(0, str(ROOT / 'larch/inv')); from patch_live import request
    return request


def inv_patch(items, field):
    """field='text'：換字（先比對原文，對不上就停）；field='voice'：換成 tag 上的新配音網址。讀線上→改→PUT→讀回對卡數線數。"""
    request = inv_boards()
    for board in sorted({x['board'] for x in items}):
        payload, etag = request(f'/boards/{board}'); b = payload.get('board', payload); by = {n['id']: n for n in b['nodes']}
        before = (len(b['nodes']), len(b['edges'])); n = 0
        for x in [x for x in items if x['board'] == board]:
            d = by[x['card']]['data']; lines = d.get('dialogueLines')
            tgt = lines[x['idx']] if lines else d
            if field == 'text':
                if tgt.get('text') == x['new']: continue
                if tgt.get('text') != x['old']: raise SystemExit(f"{x['id']}：線上的字跟審查時不一樣，停下來：{tgt.get('text', '')[:30]!r}")
                tgt['text'] = x['new']
                if lines and x['idx'] == 0 and d.get('text') == x['old']: d['text'] = x['new']
            else:
                url = x['url']
                if tgt.get('voiceUrl') == url: continue
                tgt['voiceUrl'] = url
                if lines and x['idx'] == 0 and d.get('voiceUrl'): d['voiceUrl'] = url
            n += 1
        if not n: print(board, '已經是新的'); continue
        bk = ROOT / f"larch/inv/backups/{board}-{time.strftime('%Y%m%d-%H%M')}-before-review-{field}.json"; bk.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        request(f'/boards/{board}', 'PUT', {'name': b.get('name', board), 'kind': b.get('kind', 'story'), 'mode': b.get('mode', 'story'), 'nodes': b['nodes'], 'edges': b['edges'],
                                            'summary': f'台詞審查（2026-11）：{"換字" if field == "text" else "換新配音"} {n} 句'}, etag)
        back, _ = request(f'/boards/{board}'); back = back.get('board', back)
        assert (len(back['nodes']), len(back['edges'])) == before, board
        print(board, f'改了 {n} 句', '讀回卡數線數一致', before)


def inv_larch_voice(items):
    sys.path.insert(0, str(ROOT / 'larch')); import voice as V
    request = inv_boards()
    UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
    spoken_p = ROOT / 'art/voice/spoken.json'; spoken = json.loads(spoken_p.read_text(encoding='utf-8'))
    payload, _ = request('/boards/board-main'); by = {n['id']: n for n in payload.get('board', payload)['nodes']}
    for x in items:
        body = {'nodeId': x['card'], 'boardId': x['board'], 'voiceId': V.LARCH_VOICE[x['src']][0], 'emotion': x['emo']}
        if by[x['card']]['data'].get('dialogueLines'): body['lineIndex'] = x['idx']
        r, _ = request('/voice/generate', 'POST', body)
        got = (r.get('text') or '').strip(); url = (r.get('asset') or {}).get('url')
        if got != x['new'].strip() or not url: raise SystemExit(f"{x['id']}：平台唸的不是新字：{got[:24]!r}")
        (ROOT / f"art/voice/{x['key']}.mp3").write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120).read())
        spoken[x['key']] = x['new']; print(' ', x['who'], x['key']); time.sleep(0.5)
    spoken_p.write_text(json.dumps(spoken, ensure_ascii=False, indent=0), encoding='utf-8')


def inv_publish(items, tag):
    """新音檔放 docs/voice、urls.json，打 jsDelivr 孤兒 tag，逐一 GET 對大小。回傳每句的新網址。"""
    import shutil
    sys.path.insert(0, str(ROOT / 'larch')); from main_cdn import orphan, CDN
    MAP = ROOT / 'art/voice/urls.json'; urls = json.loads(MAP.read_text(encoding='utf-8')); files = {}
    for x in items:
        shutil.copy(ROOT / f"art/voice/{x['key']}.mp3", ROOT / f"docs/voice/{x['key']}.mp3")
        urls[x['key']] = f"https://yazelin.github.io/glitch-vn/voice/{x['key']}.mp3"
        path = f"docs/voice/{x['key']}.mp3"
        files[path] = subprocess.run(['git', 'hash-object', '-w', path], capture_output=True, text=True, check=True, cwd=str(ROOT)).stdout.strip()
    MAP.write_text(json.dumps(urls, ensure_ascii=False, indent=1), encoding='utf-8')
    orphan(tag, files, f'台詞審查（2026-11）：調查篇改字的 {len(files)} 句重配')
    subprocess.run(['git', 'push', 'origin', tag], check=True, capture_output=True, cwd=str(ROOT))
    for x in items:
        x['url'] = f"{CDN}{tag}/docs/voice/{x['key']}.mp3"
        for k in range(6):
            try: n = len(urllib.request.urlopen(urllib.request.Request(x['url'], headers={'User-Agent': 'glitch-vn/1.0'}), timeout=60).read()); break
            except Exception:
                if k == 5: raise
                time.sleep(10)
        assert n == (ROOT / f"docs/voice/{x['key']}.mp3").stat().st_size, x['url']
    print(tag, len(items), '個檔，jsDelivr 逐一對過大小')
    return items


if __name__ == '__main__':
    cmd, work = sys.argv[1], sys.argv[2]
    if cmd == 'larch-voice': larch_voice_main(); raise SystemExit
    if cmd == 'inv-plan':
        import collections; pl = inv_plan(); print(collections.Counter(x['kind'] for x in pl)); raise SystemExit
    if cmd == 'apply':
        apply_main('--dry' in sys.argv) if work == 'main' else None; raise SystemExit
    {'export': export, 'detect': detect, 'suggest': suggest, 'judge': judge}[cmd](work)
