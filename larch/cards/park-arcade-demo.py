#!/usr/bin/env python3
"""建一個乾淨的示範專案，給 arcade-hub 插件當說明書。

跑一次會建新專案；之後再跑帶 --project <id> 就是重推那個專案的版子。

    python3 larch/cards/park-arcade-demo.py              # 建新專案
    python3 larch/cards/park-arcade-demo.py --project project-xxxx   # 重推

示範的重點是**接線**不是美術：兩款遊戲各自接「收齊／未集齊」兩條邊，
另外三格留空示範停用，最後一條無條件邊當保底。CG 怎麼接寫在卡片台詞裡。
"""
import argparse, json, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
API = "https://larch.ink/api/agent"
MANIFEST = ROOT / "larch/cards/park-arcade.larch-plugin.json"
BG = ("https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/"
      "larch/project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4/1789499006706_bg-park-lobby-v1.webp")
BGM = "https://yazelin.github.io/glitch-park-gacha/assets/audio/glitch-park-theme.mp3"

GAMES = [("gacha", "◉ 扭蛋機", "https://yazelin.github.io/glitch-park-gacha/"),
         ("claw", "◇ 夾娃娃機", "https://yazelin.github.io/glitch-park-claw/")]

VARS = ["demo_gacha_state", "demo_cg_gacha", "demo_cg_gacha_no",
        "demo_claw_state", "demo_cg_claw", "demo_cg_claw_no", "demo_leave"]


def call(path, method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        h["If-Match"] = etag
    req = urllib.request.Request(API + path, data, h, method=method)
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
        return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def variables():
    out = []
    for n in VARS:
        kind = "string" if n.endswith("_state") else "boolean"
        out.append({"name": n, "type": kind, "defaultValue": "" if kind == "string" else False,
                    "description": "這一款的存檔（卡片只負責轉交）" if kind == "string" else "離開那一款時卡片寫的值"})
    return out


def plugin_node():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    card = m["cards"][0]
    values = {"subtitle": "玩哪一台？（示範只開了兩款，其餘三格留空＝停用）",
              "background": BG, "bgmUrl": BGM, "bgmVolume": 0.27,
              "leaveLabel": "← 離開（示範結束）", "leaveResultVar": "demo_leave"}
    for i, (key, label, url) in enumerate(GAMES, 1):
        values[f"game{i}"] = " | ".join([label, url, key, f"demo_{key}_state",
                                         f"demo_cg_{key}", f"demo_cg_{key}_no"])
    return {"type": "plugin", "pluginId": m["id"], "pluginCardId": card["id"],
            "pluginName": m["name"], "pluginCardName": card["name"],
            "pluginIcon": card.get("icon", "dices"), "pluginColor": card.get("color", "#6b2d8f"),
            "pluginVersion": m["version"], "pluginHtml": card["html"],
            "pluginPresentation": "fullscreen", "pluginSkippable": True,
            "pluginFrame": {"showTitle": False, "showButton": False, "backgroundOpacity": 0},
            "pluginAssets": [], "platforms": ["web"], "voiceMode": "off",
            "pluginValues": values,
            "pluginReadVars": [f"demo_{k}_state" for k, _, _ in GAMES],
            "pluginWriteVars": [f"demo_{k}_state" for k, _, _ in GAMES]
                               + [f"demo_cg_{k}" for k, _, _ in GAMES]
                               + [f"demo_cg_{k}_no" for k, _, _ in GAMES] + ["demo_leave"],
            "title": "小遊戲集合（arcade-hub）", "text": ""}


def say(title, lines, **extra):
    d = {"type": "dialogue", "title": title, "speaker": "說明",
         "text": lines[0], "dialogueLines": [{"id": f"l{i}", "speaker": "說明", "text": t}
                                             for i, t in enumerate(lines)],
         "stage": {"actors": []}, "characterLayers": []}
    d.update(extra)
    return d


def cond(var):
    """條件邊一律問 ==true：沒玩過的那幾款兩個變量都是預設的 false，不會被別款的離開事件掃到。"""
    return {"op": "eq", "kind": "variable", "variable": var, "value": True, "variableLabel": var}


def board():
    nodes, edges = [], []
    def node(nid, data, x, y):
        nodes.append({"id": nid, "type": "story", "position": {"x": x, "y": y}, "data": data})
    def edge(src, dst, condition=None, handle="right"):
        e = {"id": f"e-{src}-{dst}", "source": src, "target": dst, "sourceHandle": handle}
        if condition:
            e["data"] = {"condition": condition}
        edges.append(e)

    node("demo-intro", {"type": "scene", "title": "這是什麼", "start": True, "background": BG,
                        "text": "arcade-hub 插件示範。\n下一張就是那張卡：一個選單、兩款外部小遊戲，"
                                "離開時把「收齊／沒收齊」寫進變量。\n玩完會回到這裡，畫面上會告訴你剛才寫了什麼。",
                        "transition": "fade", "transitionMs": 360,
                        "autoAdvance": {"enabled": False}}, 0, 0)
    node("demo-park", plugin_node(), 360, 0)
    node("demo-end", say("示範結束", [
        "你按了離開，所以卡片寫了 demo_leave = true，這條邊就是判它。",
        "整張版子只有六條邊從那張卡出去：兩款各兩條（收齊／未集齊）、一條離開、一條無條件的保底。",
        "保底那條指回卡片自己——沒有任何新東西要演的時候，玩家就是重新看到選單。"]), 720, 320)

    for i, (key, label, _) in enumerate(GAMES):
        y = -260 + i * 200
        win, lose = f"demo-{key}-win", f"demo-{key}-lose"
        node(win, say(f"{label}：收齊", [
            f"卡片寫了 demo_cg_{key} = true、demo_cg_{key}_no = false。",
            f"這條邊的條件就是 demo_cg_{key} == true。",
            "正式專案在這裡接 CG 對話卡，後面再接一張 setVariable 卡把 CG 解鎖；"
            "想讓它只播一次，條件再加一個 Larch 的 CG 收藏判斷。"]), 720, y)
        node(lose, say(f"{label}：還沒收齊", [
            f"卡片寫了 demo_cg_{key}_no = true、demo_cg_{key} = false。",
            "兩個變量永遠一真一假，所以這兩條邊不會同時成立。",
            "為什麼不共用一個變量問 ==false：沒玩過的那幾款預設就是 false，"
            "那樣接的話你玩完任何一款，其他款的「未集齊」都會跟著成立。"]), 720, y + 100)
        edge("demo-park", win, cond(f"demo_cg_{key}"))
        edge("demo-park", lose, cond(f"demo_cg_{key}_no"))
        edge(win, "demo-park")
        edge(lose, "demo-park")

    edge("demo-intro", "demo-park")
    edge("demo-park", "demo-end", cond("demo_leave"))
    edge("demo-park", "demo-park")        # 保底，要排最後
    return nodes, edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    a = ap.parse_args()

    pid = a.project
    if not pid:
        created, _ = call("/projects", "POST", {
            "name": "arcade-hub 插件示範",
            "description": "「小遊戲集合」插件卡怎麼用：一張卡接兩款外部小遊戲，"
                           "離開時把收齊／未集齊寫進兩個一真一假的變量，下游六條邊怎麼分。"})
        pid = (created.get("project") or created).get("id")
        print("建好新專案", pid)

    snap, etag = call(f"/projects/{pid}")
    p = snap.get("project", snap)
    p["variables"] = variables()
    st = p.setdefault("settings", {})
    st.setdefault("plugins", {})["arcade-hub"] = {"enabled": True}
    st["stageFit"] = "auto"           # 不設的話手機直式會把立繪壓成一條
    st["cgGalleryEnabled"] = False    # 沒有 CG，開著標題畫面會多一顆空按鈕
    p["languages"] = [{"code": "zh-Hant", "label": "繁體中文", "voiceMode": "off"}]
    _, etag = call(f"/projects/{pid}", "PUT", {"project": p, "summary": "示範專案的變數與插件開關"}, etag)
    print("變數", len(p["variables"]), "個｜插件開關寫好")

    nodes, edges = board()
    _, _ = call(f"/projects/{pid}/boards/board-main", "PUT",
                {"name": "示範", "nodes": nodes, "edges": edges,
                 "summary": "arcade-hub 示範：插件卡＋兩款遊戲的收齊/未集齊分岔"}, etag)

    back, _ = call(f"/projects/{pid}/boards/board-main")
    b = back.get("board", back)
    got = [n for n in b["nodes"] if n["id"] == "demo-park"][0]["data"]
    outs = [e for e in b["edges"] if e["source"] == "demo-park"]
    ok = (len(b["nodes"]) == len(nodes) and len(b["edges"]) == len(edges)
          and got.get("type") == "plugin" and len(outs) == 6)
    print(f"回讀 卡 {len(b['nodes'])}（推 {len(nodes)}）邊 {len(b['edges'])}（推 {len(edges)}）"
          f"｜插件卡出邊 {len(outs)} 條")
    pv, _ = call(f"/projects/{pid}/preview?boardId=board-main&hours=168")
    print("預覽連結（私人）:", pv.get("playUrl"))
    print("專案 id:", pid)
    print("全部對得上" if ok else "★ 對不上")
    sys.exit(0 if ok else 1)


main()
