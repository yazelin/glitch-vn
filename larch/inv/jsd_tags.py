#!/usr/bin/env python3
"""《調查篇》的配音、圖、配樂改走 jsDelivr 的孤兒 tag（作者 2026-10-07）。

為什麼：jsDelivr 的 gh 路由照「repo＋版本」整包算大小，超過 50 MB 就回 403。glitch-vn 在 main 是 747 MB、
在 8b099dd 是 686 MB，所以 @main 跟釘 commit 都一樣會掛（抽 200 個網址 3 個 403）。
Larch 媒體庫（r2.dev）會限流、沒有 CDN 快取；GitHub Pages 從這邊只有 50–170 KB/s。

做法：調查篇實際用到的檔案（約 118 MB）照類型分組，每組 40 MB 以內，各打一個孤兒 tag
（沒有上一層、只放這組檔案的 commit，用 repo 裡現成的 blob，repo 不會變大）：
  inv-voice-N 配音（docs/voice、art/voice-larch）、inv-art 圖、inv-bgm-N 配樂與音效。
網址對應：jsDelivr 的直接換 @tag；r2 與 Pages 上的下載下來算 blob hash，跟 main 上的檔案比對內容一模一樣才換。
Larch AI 語音 91 句本機原本沒有，已下載到 art/voice-larch/（檔名照媒體庫）。樂園主題曲在 glitch-park-gacha（2 MB），直接走它的 @main。
tag 打了就不改；內容變了就打下一版 <tag>-r2。

    python3 larch/inv/jsd_tags.py            乾跑：讀線上版子，印分組表與會換幾個網址（不寫任何東西）
    python3 larch/inv/jsd_tags.py --push     打 tag、推 tag、寫 jsd_manifest.json、每個新網址實際 GET
之後換線上網址用現成的 swap_urls.py（讀下來→改→PUT→對卡數線數，先備份到 backups/）：
    python3 larch/inv/swap_urls.py larch/inv/jsd_manifest.json --project --dry
    python3 larch/inv/swap_urls.py larch/inv/jsd_manifest.json --project
"""
import hashlib, json, os, pathlib, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import patch_live as L   # request()、BOARDS（主版最後推）沿用同一套

MANIFEST = HERE / "jsd_manifest.json"
CDN = "https://cdn.jsdelivr.net/gh/yazelin/glitch-vn@"
PARK_OLD = "https://yazelin.github.io/glitch-park-gacha/assets/audio/glitch-park-theme.mp3"
PARK_NEW = "https://cdn.jsdelivr.net/gh/yazelin/glitch-park-gacha@main/assets/audio/glitch-park-theme.mp3"
LIMIT = 40e6   # jsDelivr 上限 50 MB，留空間
MEDIA = r'https?://[^"\'\s\\<>)]+\.(?:webp|png|jpe?g|avif|gif|mp3|ogg|wav|m4a|mp4|webm)'
UA = {"User-Agent": "Mozilla/5.0"}


def git(*a, inp=None, env=None):
    return subprocess.run(["git", *a], cwd=ROOT, input=inp, env=env, check=True, capture_output=True, text=True).stdout


def tree(ref):
    out = {}
    for line in git("-c", "core.quotePath=false", "ls-tree", "-r", "-l", "-z", ref).split("\0"):
        if line:
            meta, path = line.split("\t", 1); _, _, blob, size = meta.split(); out[path] = (blob, int(size))
    return out


def live_texts():
    """線上會用到素材的地方：每塊版子，加上專案層的 settings／variables（背包按鈕圖、道具圖）→ {名稱: 文字}"""
    proj = L.request("")[0]; proj = proj.get("project", proj)
    out = {b["id"]: json.dumps(L.request(f"/boards/{b['id']}")[0], ensure_ascii=False) for b in proj["boards"]}
    out["（專案層 settings／variables）"] = json.dumps({"settings": proj.get("settings"), "variables": proj.get("variables")}, ensure_ascii=False)
    return out


def blob_of(url):
    for i in range(4):
        try:
            d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
            return hashlib.sha1(b"blob %d\0" % len(d) + d).hexdigest()
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def category(path):
    if path.startswith(("docs/voice/", "art/voice-larch/")): return "inv-voice"
    if path.endswith((".mp3", ".ogg", ".wav", ".m4a")): return "inv-bgm"
    return "inv-art"


def plan(texts):
    """→ (src: {舊網址: (ref, path)}, 找不到原檔的網址)"""
    main = tree("main"); by_blob = {}
    for p, (b, _) in main.items(): by_blob.setdefault(b, p)
    urls = sorted({u for t in texts for u in re.findall(MEDIA, t, re.I)})
    src, todo, missing = {}, [], []
    for u in urls:
        m = re.match(re.escape(CDN) + r"([^/]+)/(.+)$", u)
        if m: src[u] = (m[1], urllib.parse.unquote(m[2])); continue
        if "r2.dev" in u or "yazelin.github.io/glitch-vn/" in u: todo.append(u)
    larch = {f: f"art/voice-larch/{f}" for f in os.listdir(ROOT / "art/voice-larch") if f.endswith(".mp3")}
    with ThreadPoolExecutor(4) as ex:
        for u, b in zip(todo, ex.map(blob_of, todo)):
            name = urllib.parse.unquote(u.rsplit("/", 1)[1])
            p = by_blob.get(b) or (larch.get(name) if b and main.get(larch.get(name, ""), ("",))[0] == b else None)
            if p: src[u] = ("main", p)
            else: missing.append(u)
    return src, missing


def groups(src):
    trees = {}
    files = {}
    for ref, path in src.values():
        t = trees.setdefault(ref, tree(ref))
        blob, size = t[path]
        if path in files and files[path][0] != blob: sys.exit(f"{path} 在兩個版本內容不同，不能放同一個 tag")
        files[path] = (blob, size)
    cats = {}
    for p in sorted(files): cats.setdefault(category(p), []).append(p)
    out = {}
    for c, paths in cats.items():
        chunks, cur, tot = [], [], 0
        for p in paths:
            if cur and tot + files[p][1] > LIMIT: chunks.append(cur); cur, tot = [], 0
            cur.append(p); tot += files[p][1]
        chunks.append(cur)
        for i, ch in enumerate(chunks): out[c if len(chunks) == 1 else f"{c}-{i + 1}"] = ch
    assert not any(re.match(r"v\d", t) for t in out), "tag 不可以 v＋數字開頭（jsDelivr 會當版本號）"
    return out, files


def tree_from(paths, files):
    idx = tempfile.mktemp()
    env = {**os.environ, "GIT_INDEX_FILE": idx}
    try:
        git("update-index", "--add", "--index-info", inp="".join(f"100644 {files[p][0]}\t{p}\n" for p in paths), env=env)
        return git("write-tree", env=env).strip()
    finally:
        if os.path.exists(idx): os.unlink(idx)


def assign(gs, files, create):
    names, new = {}, []
    have = set(git("tag", "-l").split())
    for g, paths in gs.items():
        t = tree_from(paths, files)
        vs = ([g] if g in have else []) + sorted((x for x in have if re.fullmatch(re.escape(g) + r"-r\d+", x)), key=lambda x: int(x.rsplit("-r", 1)[1]))
        if vs and git("rev-parse", vs[-1] + "^{tree}").strip() == t:
            names[g] = vs[-1]; continue
        name = g if not vs else f"{g}-r{len(vs) + 1}"
        names[g] = name; new.append(name)
        if create: git("tag", name, git("commit-tree", t, "-m", f"jsDelivr：調查篇 {g}（只放這組用到的檔案）").strip())
    return names, new


def check(urls):
    def get(u):
        for i in range(3):
            try:
                urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read(); return None
            except Exception as e:
                err = f"{getattr(e, 'code', e)}"; time.sleep(5 * (i + 1))
        return f"{err} {urllib.parse.unquote(u)}"
    with ThreadPoolExecutor(8) as ex: return [r for r in ex.map(get, sorted(urls)) if r]


def main():
    push = "--push" in sys.argv
    git("fetch", "-q", "--tags", "origin")
    live = live_texts()
    for k, t in live.items(): print(f"{k}：{len(re.findall(MEDIA, t, re.I))} 處素材網址")
    texts = list(live.values())
    src, missing = plan(texts)
    gs, files = groups(src)
    names, new = assign(gs, files, create=push)
    for g, paths in gs.items():
        print(f"{'新' if names[g] in new else '  '} {names[g]:14} {len(paths):5} 個 {sum(files[p][1] for p in paths) / 1e6:5.1f} MB")
    where = {p: names[g] for g, ps in gs.items() for p in ps}
    m = {u: CDN + where[p] + "/" + urllib.parse.quote(p) for u, (_, p) in src.items()}
    if PARK_OLD in "".join(texts): m[PARK_OLD] = PARK_NEW
    left = [u for u in missing if u != PARK_OLD]
    print(f"會換的網址 {len(m)} 個；找不到原檔、維持原樣的 {len(left)} 個", left[:3])
    if not push:
        print("（乾跑：沒有打 tag、沒有寫任何東西）"); return
    if new: git("push", "-q", "origin", *new)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    bad = check(set(m.values()))
    print(f"驗收：{len(set(m.values()))} 個新網址，失敗 {len(bad)} 個")
    for b in bad: print("  ", b)
    if bad: sys.exit(1)
    print("下一步：python3 larch/inv/swap_urls.py larch/inv/jsd_manifest.json --project --dry")


if __name__ == "__main__":
    main()
