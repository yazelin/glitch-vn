#!/usr/bin/env python3
"""清掉沒有任何一張卡在用的配音檔。

檔名是 sha1(講者|文字|情緒)，所以**改一個字舊檔就變成孤兒**。累積下來
docs/voice 會塞一堆沒人用的檔，還會一起推進 git。

預設只列出來，加 --fix 才真的刪。挑選過的錄音（art/voice/picked.json）
一律不刪——那些是使用者聽過指名要用的，就算暫時沒卡片在用也留著。

    python3 tools/prune_voice.py          # 只看有幾個
    python3 tools/prune_voice.py --fix    # 真的刪
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
sys.path.insert(0, str(ROOT / "tools"))


def main():
    from gen_voice import utterances
    used = {k for _, _, _, k in utterances()}
    pk = ROOT / "art/voice/picked.json"
    keep = used | (set(json.loads(pk.read_text())) if pk.exists() else set())
    # **小說站的有聲書也在用這些檔，而且它的鍵是從小說原文算的**，
    # 跟卡片上的字不見得一樣。只看卡片的話會刪掉有聲書還在用的檔，
    # 而且不會報錯——那一句就是安靜地沒有聲音。實際差一個檔就中過。
    site = ROOT / "docs/novel.html"
    if site.exists():
        keep |= set(re.findall(r"voice/(v-[0-9a-f]+)\.mp3", site.read_text()))
    fix = "--fix" in sys.argv
    total = 0
    for d in (ROOT / "art/voice", ROOT / "docs/voice"):
        orphans = [p for p in sorted(d.glob("*.mp3")) if p.stem not in keep]
        print(f"{d.relative_to(ROOT)}：{len(orphans)} 個孤兒")
        total += len(orphans)
        if fix:
            for p in orphans:
                p.unlink()
                b = ROOT / "art/voice/pre-level" / p.name
                if b.exists():
                    b.unlink()
    print(f"\n{'刪掉' if fix else '可以刪'} {total} 個。"
          + ("" if fix else "　加 --fix 才會真的刪。"))
    if fix:
        print("記得跑 python3 tools/publish_voice.py 讓網址表跟上。")


if __name__ == "__main__":
    main()
