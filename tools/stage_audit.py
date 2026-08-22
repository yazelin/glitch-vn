#!/usr/bin/env python3
"""一場一場列出「台上有誰、誰講過話」，用來抓角色跨場景沒退場。

播放器會保留上一張卡的立繪，所以場景換了、cast 沒重下，人就跟著走進下一場。
    python3 tools/stage_audit.py            # 全部七章
    python3 tools/stage_audit.py ch03
    python3 tools/stage_audit.py --quiet    # 只印有人整場沒開口的場
"""
import pathlib, runpy, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))


def build():
    import novelkit as nk
    built = {}
    nk.Chapter.push = lambda self, s: built.setdefault(self.bid, self.nodes) or {}
    nk.ensure_characters = lambda: {n: f"c-{n}" for n in list(nk.SPRITE) + ["旁白"]}
    class _A(dict):
        def __missing__(self, k): return f"x/{k}"
    nk.A = _A(nk.A)
    for f in sorted((ROOT / "larch").glob("build_ch0*.py")):
        runpy.run_path(str(f), run_name="__main__")
    return built


def scenes(nodes):
    """依場景卡切段。回傳 [(起, 場景標題, 背景, [每張的台上], [開口過的])]。"""
    out, cur = [], None
    for i, n in enumerate(nodes):
        d = n["data"]
        if (d.get("type") or "dialogue") != "dialogue":
            if cur:
                out.append(cur)
            cur = [i, d.get("title", "")[:22],
                   (d.get("background") or "").rsplit("/", 1)[-1], [], set()]
            if not (d.get("stage") or {}).get("actors"):
                cur[1] += "（場景卡沒清台）" if "stage" not in d else "（清台）"
        if cur is None:
            cur = [i, "（章首）", "", [], set()]
        actors = [a.get("name") or a.get("id")
                  for a in (d.get("stage") or {}).get("actors") or []]
        cur[3].append([a for a in actors if not str(a).startswith("avatar-")])
        lines = d.get("dialogueLines") or []
        for s in ([l.get("speaker") for l in lines] if lines else [d.get("speaker")]):
            if s and s != "旁白":
                cur[4].add(s)
    if cur:
        out.append(cur)
    return out


def main():
    args = sys.argv[1:]
    only = [a for a in args if a.startswith("ch")]
    quiet = "--quiet" in args
    for bid, nodes in sorted(build().items()):
        if only and bid not in only:
            continue
        print(f"\n=== {bid} ===")
        for start, title, bg, per_card, spoke in scenes(nodes):
            cast = {a for row in per_card for a in row}
            mute = sorted(cast - spoke)
            if quiet and not mute:
                continue
            tag = "　← 整場沒開口：" + "、".join(mute) if mute else ""
            print(f"{start:3d} {title:<26} [{bg:<22}] 台上:{'、'.join(sorted(cast)) or '空'}{tag}")


if __name__ == "__main__":
    main()
