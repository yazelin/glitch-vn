#!/usr/bin/env python3
"""建一個乾淨的示範專案，給 arcade-hub 插件當說明書。

跑一次會建新專案；之後再跑帶 --project <id> 就是重推那個專案的版子。

    python3 larch/cards/park-arcade-demo.py              # 建新專案
    python3 larch/cards/park-arcade-demo.py --project project-xxxx   # 重推

示範的重點是**接線**不是美術：兩款遊戲各自接「收齊／未集齊」兩條邊，
另外三格留空示範停用，最後一條無條件邊當保底。CG 怎麼接寫在卡片台詞裡。
"""
import argparse, json, pathlib, sys, time, urllib.request

NAME = "小遊戲集合・示範"
DESC = ("「小遊戲集合」插件卡的使用示範，走一遍大概三分鐘。這裡沒有劇情。\n\n"
        "畫面上是一個遊樂園選單，五款小遊戲都是真的能玩的網頁遊戲（扭蛋機、夾娃娃機、"
        "777 拉霸、幸運轉盤、霓虹鋼珠台），玩完離開會回到示範，告訴你剛才那張卡寫了哪個"
        "變量、下一步的邊憑什麼選中它。\n\n"
        "想自己用的話：插件在素材商城搜「遊樂園小遊戲集合」，五款遊戲的原始碼是 MIT，"
        "照抄跟卡片溝通的那三個訊息就能把自己的遊戲接上來。最後一張卡列了五個 repo 與"
        "各自怎麼判「收齊」。")

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
API = "https://larch.ink/api/agent"
MANIFEST = ROOT / "larch/cards/park-arcade.larch-plugin.json"
BG = ("https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/"
      "larch/project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4/1789499006706_bg-park-lobby-v1.webp")
BGM = "https://yazelin.github.io/glitch-park-gacha/assets/audio/glitch-park-theme.mp3"
# 市集縮圖：大廳那張裁 16:9、底部壓暗、標題本機合成上去（art/park/cover-arcade-demo.webp）。
# 封面不要跟第一張卡的背景用同一張：那張是乾淨的場景，封面要自己站得住。
COVER = "https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-892df123-4806-4343-95be-44f1c65056e4/1789967439188_cover-arcade-demo.webp"

# 五款全開。前兩款接完整的分岔（收齊／未集齊各一張卡），示範接法；
# 其餘三款共用一張卡，示範「同一組邊可以收斂到同一個去處」，順便讓版子不要爆炸。
GAMES = [("gacha",   "◉ 扭蛋機",     "https://yazelin.github.io/glitch-park-gacha/",   "轉到的角色數＝全部角色數"),
         ("claw",    "◇ 夾娃娃機",   "https://yazelin.github.io/glitch-park-claw/",    "夾到的娃娃數＝全部獎品數"),
         ("slots",   "✦ 777 拉霸",   "https://yazelin.github.io/glitch-park-slots/",   "收集到的角色數＝全部角色數"),
         ("wheel",   "◎ 幸運轉盤",   "https://yazelin.github.io/glitch-park-wheel/",   "抽到的角色數＝全部角色數"),
         ("pinball", "● 霓虹鋼珠台", "https://yazelin.github.io/glitch-park-pinball/", "點亮的名字數＝全部名字數")]
FULL = 2          # 前兩款做完整分岔

VARS = [v for k, _, _, _ in GAMES
        for v in (f"demo_{k}_state", f"demo_cg_{k}", f"demo_cg_{k}_no")] + ["demo_leave"]


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
    values = {"subtitle": "玩哪一台？（五格全開；前兩款示範完整分岔，後三款收斂到同一張卡）",
              "background": BG, "bgmUrl": BGM, "bgmVolume": 0.27,
              "leaveLabel": "← 離開（示範結束）", "leaveResultVar": "demo_leave"}
    for i, (key, label, url, _) in enumerate(GAMES, 1):
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
            "pluginReadVars": [f"demo_{k}_state" for k, _, _, _ in GAMES],
            "pluginWriteVars": [f"demo_{k}_state" for k, _, _, _ in GAMES]
                               + [f"demo_cg_{k}" for k, _, _, _ in GAMES]
                               + [f"demo_cg_{k}_no" for k, _, _, _ in GAMES] + ["demo_leave"],
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
                        "text": "arcade-hub 插件示範。\n下一張就是那張卡：一個選單、五款外部小遊戲，"
                                "離開時把「這次有沒有收齊」寫進變量。\n玩完回來，畫面上會告訴你剛才寫了哪個變量、"
                                "這條邊憑什麼選中它。\n最後那張卡列了五款的 repo 與各自怎麼判「收齊」。",
                        "transition": "fade", "transitionMs": 360,
                        "autoAdvance": {"enabled": False}}, 0, 0)
    node("demo-park", plugin_node(), 360, 0)
    node("demo-end", say("示範結束", [
        "你按了離開，所以卡片寫了 demo_leave = true，這條邊就是判它。",
        "從那張卡出去的邊有六條：兩款各兩條（收齊／未集齊）、一條離開、一條無條件的保底。",
        "保底那條指回卡片自己——沒有任何新東西要演的時候，玩家就是重新看到選單。"]), 720, 320)

    for i, (key, label, _, _) in enumerate(GAMES[:FULL]):
        y = -260 + i * 200
        win, lose = f"demo-{key}-win", f"demo-{key}-lose"
        # 觸發變量寫進去之後沒人清就會一直成立：玩完別款再離開時，這一條又會被選中。
        # 調查篇靠每條邊多掛一個「這張 CG 還沒播過」擋住，沒有 CG 的專案就要自己清回 false。
        reset_win, reset_lose = f"demo-{key}-win-reset", f"demo-{key}-lose-reset"
        node(reset_win, {"type": "setVariable", "title": f"{label}：清掉收齊的旗標",
                         "text": "（把剛才那個變量清回 false，不然下次玩別款、離開時這條邊又會成立。）",
                         "variableOps": [{"id": f"op-{key}-win", "name": f"demo_cg_{key}",
                                          "mode": "set", "value": False}]}, 1080, y)
        node(reset_lose, {"type": "setVariable", "title": f"{label}：清掉未集齊的旗標",
                          "text": "（同樣清回 false。用完就清，是這個插件最容易漏掉的一步。）",
                          "variableOps": [{"id": f"op-{key}-lose", "name": f"demo_cg_{key}_no",
                                           "mode": "set", "value": False}]}, 1080, y + 100)
        node(win, say(f"{label}：收齊", [
            f"卡片寫了 demo_cg_{key} = true、demo_cg_{key}_no = false。",
            f"這條邊的條件就是 demo_cg_{key} == true。",
            "正式專案在這裡接 CG 對話卡，後面再接一張 setVariable 卡把 CG 解鎖；"
            "想讓它只播一次，條件再加一個 Larch 的 CG 收藏判斷。",
            "下一張就是把這個變量清回 false 的卡——不清的話，你之後玩別款、離開時這條邊會再成立一次。"]), 720, y)
        node(lose, say(f"{label}：還沒收齊", [
            f"卡片寫了 demo_cg_{key}_no = true、demo_cg_{key} = false。",
            "兩個變量永遠一真一假，所以這兩條邊不會同時成立。",
            "為什麼不共用一個變量問 ==false：沒玩過的那幾款預設就是 false，"
            "那樣接的話你玩完任何一款，其他款的「未集齊」都會跟著成立。"]), 720, y + 100)
        edge("demo-park", win, cond(f"demo_cg_{key}"))
        edge("demo-park", lose, cond(f"demo_cg_{key}_no"))
        edge(win, reset_win)
        edge(lose, reset_lose)
        edge(reset_win, "demo-park")
        edge(reset_lose, "demo-park")

    # 後三款：六條邊收斂到同一張卡，清旗標那張一次清六個變量
    rest = GAMES[FULL:]
    node("demo-rest", say("後三款：玩完了", [
        "這三款（" + "、".join(g[1] for g in rest) + "）在示範裡共用這一張卡。",
        "六條邊（三款各兩條）指到同一個去處，這在正式專案很常見：分岔不一定要一對一。",
        "要各自演不同的東西，就照前兩款那樣各接各的。"]), 1080, 260)
    node("demo-rest-reset", {"type": "setVariable", "title": "後三款：清掉旗標",
                             "text": "（一張 setVariable 卡可以一次清好幾個變量。）",
                             "variableOps": [{"id": f"op-rest-{k}-{suf}", "name": f"demo_cg_{k}{suf}",
                                              "mode": "set", "value": False}
                                             for k, _, _, _ in rest for suf in ("", "_no")]}, 1440, 260)
    for key, _, _, _ in rest:
        edge("demo-park", "demo-rest", cond(f"demo_cg_{key}"))
        edge("demo-park", "demo-rest", cond(f"demo_cg_{key}_no"))
    edge("demo-rest", "demo-rest-reset")
    edge("demo-rest-reset", "demo-park")

    # 五款各自的實作說明：協定一樣，「收齊」的定義各自不同
    node("demo-games", say("五款參考實作", [
        "選單上那五款都是獨立的網頁遊戲，各自一個 repo、各自一個 GitHub Pages，"
        "跟這張卡之間只靠三個 postMessage 訊息溝通。",
        "程式碼是 MIT，照抄協定那一段就能把自己的遊戲接上來（角色與美術另外授權，不要一起拿）。",
    ] + [f"{label}：github.com/yazelin/glitch-park-{key}　協定前綴 {key}　「收齊」的定義是{rule}"
         for key, label, _, rule in GAMES] + [
        "要接自己的遊戲，照著做三件事：載入完送 前綴:ready 跟卡片要存檔；"
        "存檔有變動送 前綴:save 帶新的存檔；玩家按離開送 前綴:exit 帶 complete 布林值。",
        "卡片會把存檔轉交給你指定的變量，把 complete 轉成那兩個一真一假的旗標。"]), 1080, 560)
    edge("demo-end", "demo-games")

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
            "name": NAME,
            "description": DESC})
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
    p["name"] = NAME
    p["description"] = DESC
    p["projectThumbnail"] = COVER         # 市集列表的縮圖，不設就是空的
    st["titleScreenEnabled"] = True
    st["titleScreen"] = {"frame": None, "layers": [
        {"id": "name", "kind": "text", "role": "title", "text": "小遊戲集合・示範",
         "x": 50, "y": 34, "size": 6.5},
        {"id": "desc", "kind": "text", "role": "description",
         "text": "arcade-hub 插件卡怎麼接自己的小遊戲", "x": 50, "y": 46, "size": 1.3},
        {"id": "action-start", "kind": "button", "action": "start", "icon": True,
         "x": 50, "y": 62, "size": 1.25, "width": 19}]}
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
    want = len([e for e in edges if e["source"] == "demo-park"])
    ok = (len(b["nodes"]) == len(nodes) and len(b["edges"]) == len(edges)
          and got.get("type") == "plugin" and len(outs) == want
          and len([k for k in got["pluginValues"] if k.startswith("game")]) == len(GAMES))
    print(f"回讀 卡 {len(b['nodes'])}（推 {len(nodes)}）邊 {len(b['edges'])}（推 {len(edges)}）"
          f"｜插件卡出邊 {len(outs)} 條")
    pv, _ = call(f"/projects/{pid}/preview?boardId=board-main&hours=168")
    print("預覽連結（私人）:", pv.get("playUrl"))
    print("專案 id:", pid)
    print("全部對得上" if ok else "★ 對不上")
    sys.exit(0 if ok else 1)


main()
