"""新立繪上線前的放檔：播放走 jsDelivr 孤兒 tag（跟 main-art-1 同一套），專案素材庫也傳一份（AGENTS.md：圖要在專案內有一份）。
寫 sprites.json（table.tsv 的代號 → jsDelivr 網址），apply.py 照它換。

    python3 art/main-poses/host.py --dry       列出要放哪些檔
    python3 art/main-poses/host.py --push      打 tag、推 tag、逐一 GET 驗大小、傳素材庫、寫 sprites.json
"""
import base64, csv, json, pathlib, subprocess, sys, time, urllib.request
HERE = pathlib.Path(__file__).parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'larch'))
import config
from main_cdn import orphan, CDN

TAG = 'main-art-2'


def keys():
    ks = set()
    for r in csv.DictReader(open(HERE / 'table.tsv', encoding='utf-8'), delimiter='\t'):
        k = (r['決定'] or r['提案']).strip()
        if r['現在'] and k not in ('', 'none', 'wave'): ks.add(k)
    return sorted(ks)


def main():
    files = {k: HERE / f'sprite/glitch-{k}.webp' for k in keys()}
    miss = [k for k, f in files.items() if not f.exists()]
    if miss: raise SystemExit(f'還沒有圖：{miss}')
    for k, f in files.items(): print(k, f.relative_to(ROOT), f.stat().st_size // 1024, 'KB')
    if '--push' not in sys.argv: return
    blobs = {str(f.relative_to(ROOT)): subprocess.run(['git', 'hash-object', '-w', str(f)], cwd=ROOT, capture_output=True, check=True, text=True).stdout.strip() for f in files.values()}
    orphan(TAG, blobs, '正篇新立繪：五個姿勢與七張表情（2026-11-04 作者拍板）')
    subprocess.run(['git', 'push', 'origin', TAG], cwd=ROOT, check=True)
    urls = {}
    for k, f in files.items():
        u = f'{CDN}{TAG}/{f.relative_to(ROOT)}'
        for i in range(6):   # 新 tag 剛推上去，jsDelivr 第一次抓可能還沒準備好
            try: n = len(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'glitch-vn/1.0'}), timeout=60).read()); break
            except Exception as e:
                if i == 5: raise
                print('  jsDelivr 還沒好，等一下再試', e); time.sleep(10)
        assert n == f.stat().st_size, (u, n)
        urls[k] = u
        config.api({'name': f.name, 'mimeType': 'image/webp', 'category': 'character', 'base64': base64.b64encode(f.read_bytes()).decode()}, 'POST', '/media')
        print('好了', k)
    (HERE / 'sprites.json').write_text(json.dumps(urls, ensure_ascii=False, indent=1))
    print('寫好 sprites.json，', len(urls), '張')


if __name__ == '__main__':
    main()
