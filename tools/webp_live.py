#!/usr/bin/env python3
"""把線上專案卡片還在用的 PNG／JPG 圖抓下來轉成 webp（去背立繪保留透明），寫到 art/live-webp/，
並產 art/live-webp-pending.json（舊網址→本機 webp 檔）。上傳與換網址是另外兩步：

    python3 tools/webp_live.py <GET /projects 快照.json>      # 轉檔
    python3 tools/webp_live.py <快照> --upload                 # 逐檔 POST /media，把新網址寫進 art/bg-investigation/webp/live-map.json
    python3 larch/inv/swap_urls.py art/bg-investigation/webp/live-map.json   # 換卡片上的網址（版子）

live-map.json 是 patch_live.py 會讀的那份對照表，整包重建後跑 patch_live 就會再換一次。
"""
import base64, io, json, pathlib, re, sys, time, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "art/live-webp"
MAP = ROOT / "art/bg-investigation/webp/live-map.json"
Q_ALPHA, Q_PHOTO = 90, 85
UA = {"User-Agent": "Mozilla/5.0"}


def used_images(project):
    blob = json.dumps({k: v for k, v in project.items() if k != "media"}, ensure_ascii=False)
    return sorted(set(re.findall(r'https?://[^\s"\'\)\\]+?\.(?:png|jpe?g)', blob, re.I)))


def convert(url):
    name = re.sub(r"^\d+_", "", url.rsplit("/", 1)[-1])
    dst = OUT / (name.rsplit(".", 1)[0] + ".webp")
    if dst.exists():
        return dst
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
    im = Image.open(io.BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P") and (im.mode != "P" or "transparency" in im.info):
        im = im.convert("RGBA"); im.save(dst, "WEBP", quality=Q_ALPHA, method=6)
    else:
        im = im.convert("RGB"); im.save(dst, "WEBP", quality=Q_PHOTO, method=6)
    print(f"{name:40} {len(raw)//1024:6} KB -> {dst.stat().st_size//1024:5} KB {im.mode}", flush=True)
    return dst


def upload(url, dst, key, base):
    body = {"base64": base64.b64encode(dst.read_bytes()).decode(), "name": dst.name, "mimeType": "image/webp"}
    req = urllib.request.Request(base + "/media", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                a = json.load(r); a = a.get("asset", a); return a["url"]
        except Exception as e:
            print("  失敗", i + 1, repr(e)[:100], flush=True); time.sleep(15)
    raise SystemExit("上傳放棄 " + dst.name)


def main():
    snap = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    project = snap.get("project", snap)
    OUT.mkdir(exist_ok=True)
    urls = used_images(project)
    files = {u: convert(u) for u in urls}
    pending = {u: str(d.relative_to(ROOT)) for u, d in files.items()}
    (OUT.parent / "live-webp-pending.json").write_text(json.dumps(pending, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(files), "張，合計", sum(d.stat().st_size for d in files.values()) // 1024, "KB")
    if "--upload" not in sys.argv:
        return
    key = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
    state = json.loads((ROOT / "larch/inv/state.json").read_text(encoding="utf-8"))
    base = f"https://larch.ink/api/agent/projects/{state['projectId']}"
    table = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    for u, d in files.items():
        if u in table:
            continue
        t = time.time(); table[u] = upload(u, d, key, base)
        MAP.write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"上傳 {d.name:36} {round(time.time()-t)} s -> {table[u].rsplit('/',1)[-1]}", flush=True)
    print("對照表", len(table), "筆 ->", MAP)


if __name__ == "__main__":
    main()
