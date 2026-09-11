#!/usr/bin/env python3
"""劇情模式那一輪有沒有真的照軌道走。跑：

    python3 tools/railcheck.py <逐字稿…>

軌道是 `design/調查篇-通關路線.txt`（一輪完美通關的逐字稿），逐字稿是
`MODE=story node tools/autoplay.mjs` 跑出來的那一份。這一支把兩邊**逐步**比：
第 N 天第幾個時段去了哪裡、在選單上選了哪一格，一步一行。

**為什麼要有這一支**：2026-09-11 退回過一次。當時 build.py 只報「軌道對上 10/11 張」，
看起來沒事，可是那一輪在第 2 天晚上就選了別的一格，後面每一格的前提都接不上，
貓草那條線整條斷掉，結局名單只有 4/6。**走得完不等於走對**，差別只有逐步比才看得出來。

名單那一頁幾分之六是另一支（scratchpad 的 score.py）在算，這一支只管路線。
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROUTE = ROOT / "design/調查篇-通關路線.txt"
SLOT = {"上午": 0, "下午": 1, "晚上": 2, "深夜": 3}


def steps(path):
    """逐字稿 → [(天, 時段, 地名, 選單標籤)]，順序照走過的樣子。"""
    out, cur = [], None
    for ln in pathlib.Path(path).read_text(encoding="utf-8", errors="replace").split("\n"):
        if m := re.match(r"^=== 板 第 (\d+) 天 ・ (上午|下午|晚上|深夜)", ln):
            cur = [int(m.group(1)), SLOT[m.group(2)], "", ""]
            out.append(cur)
            continue
        if cur is None:
            continue
        if m := re.match(r"^→ 去 (\S+)", ln):
            cur[2] = m.group(1)
        elif m := re.search(r"→ 選「(.+?)」", ln):
            if not cur[3]:
                cur[3] = m.group(1)
    return out


def main():
    if not sys.argv[1:]:
        print(__doc__)
        return 2
    want = {(d, s): (p, l) for d, s, p, l in steps(ROUTE)}
    rc = 0
    for f in sys.argv[1:]:
        got = steps(f)
        bad = []
        print(f"\n== {f}　出門 {len(got)} 次（軌道 {len(want)} 步）")
        for d, s, p, l in got:
            w = want.get((d, s))
            if w is None:
                bad.append((d, s, "軌道上沒有這一步", f"{p}／{l}"))
                continue
            if p != w[0]:
                bad.append((d, s, f"地點該是 {w[0]}", p or "（沒去）"))
            elif w[1] and l != w[1]:
                bad.append((d, s, f"選單該選「{w[1]}」", f"選了「{l}」" if l else "（沒選）"))
        for d, s in sorted(set(want) - {(d, s) for d, s, _, _ in got}):
            bad.append((d, s, f"這一步沒走到：{want[(d, s)][0]}／{want[(d, s)][1]}", ""))
        if bad:
            rc = 1
            for d, s, why, gotv in bad:
                print(f"  ★ 第 {d:>2} 天 時段{s}　{why}　{gotv}")   # speak-tw-ok：★ 是這一批工具共用的紅字記號
        print(f"  對上 {len(got) - len([x for x in bad if x[3] != ''])}／{len(want)}，"
              f"{'沒有差異' if not bad else f'★ 差 {len(bad)} 步'}")   # speak-tw-ok
    return rc


if __name__ == "__main__":
    sys.exit(main())
