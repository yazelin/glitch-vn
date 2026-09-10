#!/usr/bin/env python3
"""白板上選擇卡的去向表。跑：python3 tools/choicemap.py

白板把卡片排成一格一格的網格，格距 360、卡片寬 306，所以跨超過一格的連接線
會從中間那張卡的背面穿過去，肉眼找不到。要知道某個選項接去哪，用這支查。

  python3 tools/choicemap.py            線上那份板子（push.py 推上去的）
  python3 tools/choicemap.py --local    本機 larch/inv/out/board.json（還沒推的）
  python3 tools/choicemap.py 鞋盒        只看標題或內文含這兩個字的選擇卡

每個選項印出直接接到的卡；那張卡如果是匯流、設變數、回板這種沒有台詞的，
會再往下走幾步，找到第一句真的講話為止（→ 前面的箭頭數＝走了幾步）。
"""
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "larch/inv/state.json"
LOCAL = ROOT / "larch/inv/out/board.json"
QUIET = ("setVariable", "boardJump", "interrupt")   # 沒有台詞、只是過路的卡


def live_board():
    key = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
    st = json.loads(STATE.read_text())
    url = f"https://larch.ink/api/agent/projects/{st['projectId']}/boards/{st['boardId']}"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return d.get("board") or d


def load(local: bool):
    if local:
        d = json.loads(LOCAL.read_text())
        return d if "nodes" in d else d["boards"][0]
    return live_board()


def blurb(node, width=42):
    """一張卡拿來認人的那一句"""
    d = node.get("data") or {}
    t = (d.get("text") or d.get("title") or "").replace("\n", " ").strip()
    return t[:width] or f"（{d.get('type')}）"


def walk(nid, by_id, out_edges, hops=5):
    """從一張卡往下走，停在第一張有台詞的卡上；回傳（走了幾步, 那張卡）"""
    n = by_id.get(nid)
    for step in range(hops):
        if not n:
            return step, None
        if (n.get("data") or {}).get("type") not in QUIET:
            return step, n
        nxt = out_edges.get(n["id"]) or []
        if len(nxt) != 1:          # 分岔或走到底就停在這裡
            return step, n
        n = by_id.get(nxt[0]["target"])
    return hops, n


def main(argv):
    local = "--local" in argv
    needle = next((a for a in argv[1:] if not a.startswith("--")), "")
    b = load(local)
    nodes, edges = b.get("nodes", []), b.get("edges", [])
    by_id = {n["id"]: n for n in nodes}
    out_edges = {}
    for e in edges:
        out_edges.setdefault(e["source"], []).append(e)
    groups = {n["id"]: (n["data"] or {}).get("title", n["id"])
              for n in nodes if (n.get("data") or {}).get("type") == "group"}

    def where(n):
        """這張卡在白板哪裡：群組名 + 座標"""
        p = n.get("position") or {}
        g = groups.get(n.get("parentId"), "")
        return f"{g} ({p.get('x')}, {p.get('y')})" if g else f"({p.get('x')}, {p.get('y')})"

    picked = [n for n in nodes if (n.get("data") or {}).get("type") == "choice"
              and (not needle or needle in json.dumps(n["data"], ensure_ascii=False))]
    print(f"{'本機' if local else '線上'}板子：卡片 {len(nodes)}、選擇卡 {len(picked)}"
          + (f"（篩「{needle}」）" if needle else ""))

    missing = 0
    for n in sorted(picked, key=lambda x: (x.get("parentId") or "", x["position"]["x"])):
        d = n["data"]
        print(f"\n■ {d.get('title') or blurb(n)}   [{n['id']}]  {where(n)}")
        wired = {e.get("sourceHandle"): e for e in out_edges.get(n["id"], [])}
        for i, label in enumerate(d.get("choices") or []):
            e = wired.get(f"choice-{i}")
            if not e:
                print(f"   {i+1}. {label}　★ 沒有接線")
                missing += 1
                continue
            tgt = by_id.get(e["target"])
            if not tgt:
                print(f"   {i+1}. {label}　★ 接到不存在的卡 {e['target']}")
                missing += 1
                continue
            print(f"   {i+1}. {label}")
            print(f"        → [{tgt['id']}] {where(tgt)}  {blurb(tgt)}")
            step, land = walk(tgt["id"], by_id, out_edges)
            if land is not None and land["id"] != tgt["id"]:
                print(f"        {'→' * (step + 1)} [{land['id']}] {where(land)}  {blurb(land)}")

    print(f"\n沒接好的選項：{missing}")
    return 1 if missing else 0


def demo():
    """自檢：假板子，第二個選項故意不接線"""
    b = {"nodes": [
        {"id": "g", "data": {"type": "group", "title": "測試群組"}, "position": {"x": 0, "y": 0}},
        {"id": "c", "parentId": "g", "position": {"x": 0, "y": 0},
         "data": {"type": "choice", "title": "選擇", "choices": ["甲", "乙"]}},
        {"id": "v", "parentId": "g", "position": {"x": 360, "y": 0}, "data": {"type": "setVariable"}},
        {"id": "d", "parentId": "g", "position": {"x": 720, "y": 0},
         "data": {"type": "dialogue", "text": "真正的下一句"}}],
        "edges": [{"source": "c", "target": "v", "sourceHandle": "choice-0"},
                  {"source": "v", "target": "d"}]}
    by_id = {n["id"]: n for n in b["nodes"]}
    oe = {}
    for e in b["edges"]:
        oe.setdefault(e["source"], []).append(e)
    step, land = walk("v", by_id, oe)
    assert land["id"] == "d" and step == 1, (step, land)
    assert walk("d", by_id, oe) == (0, by_id["d"])
    print("demo ok")


if __name__ == "__main__":
    sys.exit(demo() if "demo" in sys.argv else main(sys.argv))
