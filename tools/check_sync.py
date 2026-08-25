#!/usr/bin/env python3
"""確認三個站的角色自介是同一份。

**自介的唯一事實來源在這個 repo**（tools/gen_intro.py），格莉奇OS 與部落格
各複製一份過去。而複製是靠人記得——2026-08-25 就漏過一次：改寫了黑洞先生的
自介、推了小說站，另外兩個站停在舊版，是使用者聽出來的（他一直聽到
「我有正職」那一句）。音檔跟逐字稿都要比，只比其中一邊會漏。

    python3 tools/check_sync.py

有不一致就 exit 1，並印出要跑哪一支同步腳本。
"""
import hashlib, io, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOME = pathlib.Path.home()
INTRO = json.loads((ROOT / "art/voice/intro.json").read_text(encoding="utf-8"))
WHO = ("glitch", "blackhole")   # 另外兩個站只放這兩位

SITES = [
    ("格莉奇OS", HOME / "ai-brain-site", "audio/intro-{k}.mp3",
     "python3 scripts/sync_intro.py && python3 scripts/update_sw_hashes.py"),
    ("部落格", HOME / "yazelin.github.io", "assets/audio/intro-{k}.mp3",
     "手動複製，這個站沒有同步腳本"),
]


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    total = 0
    for name, base, pat, how in SITES:
        bad = 0   # 每個站各自算，不然第一個站壞掉會害第二個站也印修法
        if not base.exists():
            print(f"{name:8s} 找不到 {base}，跳過")
            continue
        for k in WHO:
            src = ROOT / f"docs/voice/intro-{k}.mp3"
            dst = base / pat.format(k=k)
            if md5(src) != md5(dst):
                print(f"FAIL  {name} 的 {k} 音檔跟這裡不一樣")
                bad += 1
        # 逐字稿：兩個站放的位置不一樣，各自找
        want = {k: INTRO[k]["text"] for k in WHO}
        if "ai-brain-site" in str(base):
            s = (base / "index.html").read_text(encoding="utf-8")
        else:
            s = "".join((base / f"characters/{k}.md").read_text(encoding="utf-8")
                        for k in WHO)
        for k, t in want.items():
            if t not in s:
                print(f"FAIL  {name} 的 {k} 逐字稿是舊的")
                bad += 1
        if not bad:
            print(f"ok    {name} 跟這裡一致")
        if bad:
            print(f"      修法：cd {base} && {how}")
        total += bad
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
