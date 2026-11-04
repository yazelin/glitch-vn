#!/usr/bin/env python3
"""把 larch/ui/<main|inv>/ 的介面 Skills 逐部位推上 Larch（PUT /interface，一次一個部位，不動專案其他地方）。

每個部位帶 expectedHtml（線上現在的內容，沒有就空字串），別人在編輯器改過就會被擋下來，不會蓋掉。
Larch 寫入前會自己留一份完整專案的復原副本。

    python3 larch/ui/push_ui.py main      正篇（title、dialogue、choices、menu、gallery）
    python3 larch/ui/push_ui.py inv       調查篇（再加 inventory）
    加 --dry 只列出會推哪些部位
"""
import json, pathlib, sys, time, urllib.error, urllib.request

HERE = pathlib.Path(__file__).parent
KEY = pathlib.Path.home().joinpath('.config/larch/key').read_text().strip()
PROJ = {'main': 'project-bec1644c-0dfe-4447-86c0-0c592e2f939f', 'inv': 'project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4'}
NAME = {'main': '格莉奇OS（正篇）', 'inv': '守則本（調查篇）'}
ORDER = ['title', 'dialogue', 'choices', 'menu', 'inventory', 'gallery']


def call(method, path, body=None, etag=None):
    h = {'User-Agent': 'glitch-vn/1.0', 'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}
    if etag: h['If-Match'] = etag
    req = urllib.request.Request(f'https://larch.ink/api/agent/projects/{path}', data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r: return r.status, json.loads(r.read() or b'{}'), r.headers.get('ETag')
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b'')[:400].decode('utf-8', 'replace'), None


def main():
    work = sys.argv[1]; pid = PROJ[work]
    files = {f.stem: f for f in (HERE / work).iterdir() if f.stem in ORDER and f.suffix in ('.html', '.css')}
    st, proj, etag = call('GET', pid)
    proj = proj.get('project', proj)
    ci = (proj.get('settings') or {}).get('customInterfaces') or {}
    for part in [p for p in ORDER if p in files]:
        html = files[part].read_text(encoding='utf-8')
        expected = (ci.get(part) or {}).get('html', '')
        if '--dry' in sys.argv: print(part, len(html), '字', '（線上已有）' if expected else '（線上沒有）'); continue
        body = {'surface': part, 'html': html, 'enabled': True, 'expectedHtml': expected,
                'summary': f'翻新：{NAME[work]}的{part}（作者 2026-11-04 在比較頁看過）'}
        for attempt in range(3):
            st, res, et = call('PUT', f'{pid}/interface', body, etag)
            if st == 409 or st == 428:
                _, _, etag = call('GET', pid); continue
            break
        if et: etag = et
        print(part, st, '' if st < 300 else res)
        time.sleep(1)
    if '--dry' in sys.argv: return
    _, back, _ = call('GET', pid); back = back.get('project', back)
    ci = (back.get('settings') or {}).get('customInterfaces') or {}
    for part in [p for p in ORDER if p in files]:
        same = (ci.get(part) or {}).get('html') == files[part].read_text(encoding='utf-8')
        print('讀回', part, '一致' if same else '不一致或沒寫進去', '啟用' if (ci.get(part) or {}).get('enabled') else '')


if __name__ == '__main__':
    main()
