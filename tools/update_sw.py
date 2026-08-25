#!/usr/bin/env python3
"""用內容 hash 產 sw.js 的快取版號。**不要手動 bump，遲早會忘。**

兩層各自算自己的 hash：
  SHELL  五個頁面 + manifest + icon，改一行字就換版
  ASSET  img/ 與 voice/ 的檔名清單，只有增刪或改名才換版

ASSET 用「檔名 + 大小」而不是完整內容雜湊，因為七百多個音檔全讀一次太慢，
而這個站的音檔名是內容雜湊（見 larch/voice.py 的 key），改內容一定改檔名。

    python3 tools/update_sw.py
"""
import hashlib, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SW = DOCS / "sw.js"

SHELL = ["index.html", "novel.html", "characters.html", "timeline.html",
         "extras.html", "vn.html", "credits.html", "manifest.webmanifest"]


def shell_hash():
    h = hashlib.sha256()
    for n in SHELL:
        f = DOCS / n
        h.update(f.read_bytes() if f.exists() else b"")
    for p in sorted(DOCS.glob("img/icon-*.png")):
        h.update(p.read_bytes())
    # 字型也在 SHELL_FILES 裡。**加了新文字要重切字型**，而重切之後如果版號沒動，
    # 舊使用者拿到的還是舊子集，新字會掉到系統字型——同一行兩種臉，而且不會報錯。
    for p in sorted(DOCS.glob("fonts/*.woff2")):
        h.update(p.read_bytes())
    return h.hexdigest()[:10]


def asset_hash():
    h = hashlib.sha256()
    for d in ("img", "voice"):
        for p in sorted((DOCS / d).glob("*")):
            h.update(f"{p.name}:{p.stat().st_size}".encode())
    return h.hexdigest()[:10]


def main():
    s = SW.read_text(encoding="utf-8")
    sh, ah = shell_hash(), asset_hash()
    new = (f"/* cache:start — tools/update_sw.py 產生，勿手改 */\n"
           f"const SHELL_CACHE = 'gvn-shell-{sh}';\n"
           f"const ASSET_CACHE = 'gvn-assets-{ah}';\n"
           f"/* cache:end */")
    s2 = re.sub(r"/\* cache:start.*?/\* cache:end \*/", new, s, flags=re.S)
    if s2 == s:
        print("版號沒變")
        return
    SW.write_text(s2, encoding="utf-8")
    print(f"  shell  = gvn-shell-{sh}\n  assets = gvn-assets-{ah}")


if __name__ == "__main__":
    main()
