#!/usr/bin/env python3
"""正篇的圖改 webp、配音與圖改走 jsDelivr 孤兒 tag（作者 2026-11-04 在翻新比較頁選「圖和配音都做」）。

跟調查篇 larch/inv/jsd_tags.py 同一套想法：jsDelivr 的 gh 路由照「repo＋版本」整包算大小，超過 50 MB 回 403，
所以每組素材各打一個只放那組檔案的孤兒 tag（沒有上一層的 commit）。
  main-voice-1   正篇配音（docs/voice/v-*.mp3，22 MB）。其中 6 句現在 Pages 是 404（9/16 進過 37f5b95、後來被刪），
                 從 git 歷史把同一個 blob 放進 tag，聲音一個字都沒動。
  main-art-1     正篇用到的圖，從 Larch 素材庫（r2.dev）下載後轉 webp（art/main-webp/）。新的 webp 直接寫成 git 物件，
                 不 commit 到 main（main 常有別條線沒提交的改動）。
Larch 素材庫的原圖都還在，沒有刪任何東西。介面 Skills 裡的網址只收 r2.dev（見 reference_larch_ui_skill_url_allowlist），
所以介面用到的頭像、立繪、軟木板維持 r2，不在這裡換。

    python3 larch/main_cdn.py            乾跑：列出要換的網址與大小，轉好的 webp 寫到 art/main-webp/（不打 tag、不推）
    python3 larch/main_cdn.py --push     打 tag、推 tag、每個新網址實際 GET、寫 larch/main_cdn.json（舊網址 → 新網址）
套到白板是 merge_lines.py --cdn 那一步（合併與換網址一起推，白板只改一次）。
"""
import hashlib, io, json, pathlib, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import config
from PIL import Image

ROOT = config.ROOT
OUT_IMG = ROOT / 'art/main-webp'
MANIFEST = ROOT / 'larch/main_cdn.json'
CDN = 'https://cdn.jsdelivr.net/gh/yazelin/glitch-vn@'
UA = {'User-Agent': 'glitch-vn/1.0'}
IMG = re.compile(r'https://pub-[0-9a-f]+\.r2\.dev/[^"\'\s\\<>)]+\.(?:png|jpe?g)')
VOICE = re.compile(r'https://yazelin\.github\.io/glitch-vn/voice/(v-[0-9a-f]+\.mp3)')
BOARDS = ['ch01', 'ch02', 'ch03', 'ch04', 'ch05', 'ch06', 'ch07', 'ch08']


def git(*a, inp=None):
    r = subprocess.run(['git', *a], cwd=ROOT, input=inp, capture_output=True, check=True)
    return r.stdout


def fetch(u):
    for i in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
        except Exception:
            if i == 3: raise
            time.sleep(2 + i * 2)


def voice_blob(name):
    """docs/voice/<name> 的 blob：main 上有就用 main 的，沒有就從最後一個有它的 commit 拿。"""
    path = f'docs/voice/{name}'
    try: return git('rev-parse', f'HEAD:{path}').decode().strip()
    except subprocess.CalledProcessError: pass
    log = git('log', '--all', '--format=%H', '--', path).decode().split()
    for c in log:
        try: return git('rev-parse', f'{c}:{path}').decode().strip()
        except subprocess.CalledProcessError: continue
    return None


def webp_bytes(raw):
    im = Image.open(io.BytesIO(raw))
    alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    buf = io.BytesIO()
    (im.convert('RGBA') if alpha else im.convert('RGB')).save(buf, 'WEBP', quality=86, method=6)
    return buf.getvalue()


def orphan(tag, files, msg):
    """files: {repo 路徑: blob}。做一棵只有這些檔案的樹、一個沒有上一層的 commit，打成 tag。"""
    idx = ROOT / '.git' / f'tmp-index-{tag}'
    env_idx = {'GIT_INDEX_FILE': str(idx)}
    import os
    env = {**os.environ, **env_idx}
    if idx.exists(): idx.unlink()
    lines = ''.join(f'100644 {b}\t{p}\n' for p, b in sorted(files.items()))
    subprocess.run(['git', 'update-index', '--add', '--index-info'], cwd=ROOT, input=lines.encode(), env=env, check=True)
    t = subprocess.run(['git', 'write-tree'], cwd=ROOT, env=env, capture_output=True, check=True).stdout.decode().strip()
    idx.unlink()
    c = git('commit-tree', t, '-m', msg).decode().strip()
    git('tag', tag, c)
    return c


def main():
    push = '--push' in sys.argv
    proj = config.api(); proj = proj.get('project', proj)
    text = json.dumps([b for b in proj['boards'] if b['id'] in BOARDS], ensure_ascii=False) + json.dumps(proj['settings'], ensure_ascii=False)
    imgs = sorted(set(IMG.findall(text)))
    voices = sorted(set(VOICE.findall(text)))
    print(f'圖 {len(imgs)} 張、配音 {len(voices)} 個')

    # 配音：每個檔名找 blob
    vfiles, missing = {}, []
    for name in voices:
        b = voice_blob(name)
        if b: vfiles[f'docs/voice/{name}'] = b
        else: missing.append(name)
    if missing: sys.exit(f'這些配音在 git 裡找不到，不能搬：{missing}')
    from_history = [p for p in vfiles if not (ROOT / p).exists()]
    print('配音從 git 歷史救回：', [p.rsplit('/', 1)[-1] for p in from_history])

    # 圖：下載、轉 webp、寫成 git 物件
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    def conv(u):
        raw = fetch(u)
        name = u.rsplit('/', 1)[-1].rsplit('.', 1)[0] + '.webp'   # 保留素材庫的時間戳前綴，名字不會撞
        data = webp_bytes(raw)
        (OUT_IMG / name).write_bytes(data)
        return u, name, len(raw), len(data)
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(conv, imgs))
    ifiles, mapping = {}, {}
    for u, name, a, b in rows:
        blob = git('hash-object', '-w', str(OUT_IMG / name)).decode().strip()
        ifiles[f'art/main-webp/{name}'] = blob
        mapping[u] = f'{CDN}main-art-1/art/main-webp/{name}'
    print(f"圖 {sum(r[2] for r in rows) / 1e6:.1f} MB → webp {sum(r[3] for r in rows) / 1e6:.1f} MB")
    for name in voices:
        mapping[f'https://yazelin.github.io/glitch-vn/voice/{name}'] = f'{CDN}main-voice-1/docs/voice/{name}'
    vsize = sum(int(git('cat-file', '-s', b).decode()) for b in vfiles.values())
    isize = sum(int(git('cat-file', '-s', b).decode()) for b in ifiles.values())
    print(f'tag 大小：main-voice-1 {vsize / 1e6:.1f} MB、main-art-1 {isize / 1e6:.1f} MB（上限 50 MB）')
    assert vsize < 45e6 and isize < 45e6
    if not push:
        print('（乾跑：沒有打 tag、沒有推）'); return

    have = set(git('tag', '-l').decode().split())
    for tag, files, msg in [('main-voice-1', vfiles, 'jsDelivr：正篇配音（只放正篇用到的檔案）'), ('main-art-1', ifiles, 'jsDelivr：正篇的圖（webp）')]:
        if tag in have: sys.exit(f'{tag} 已經存在，內容變了要打下一版（-r2）')
        orphan(tag, files, msg)
    git('push', '-q', 'origin', 'main-voice-1', 'main-art-1')
    print('推了 tag')
    # 每個新網址實際 GET，大小對得上才算數
    sizes = {**{mapping[f'https://yazelin.github.io/glitch-vn/voice/{p.rsplit("/", 1)[-1]}']: int(git('cat-file', '-s', b).decode()) for p, b in vfiles.items()},
             **{mapping[u]: b for u, _, _, b in rows}}
    def check(u):
        try: return u, len(fetch(u)) == sizes[u]
        except Exception: return u, False
    with ThreadPoolExecutor(8) as ex: bad = [u for u, ok in ex.map(check, list(sizes)) if not ok]
    if bad: sys.exit(f'{len(bad)} 個新網址抓不到或大小不對，先不要套用：{bad[:5]}')
    MANIFEST.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(mapping)} 個新網址全部 GET 通過，寫了 {MANIFEST.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
