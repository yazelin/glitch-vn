#!/usr/bin/env python3
"""把線上的遊樂園卡從 miniGame 換成 arcade-hub 插件卡（一次性）。

節點 id 不變（`inv-park-gacha`），變量名也不變，所以下游那 12 條邊一條都不用動：
插件的 5 個結果變量與 5 個未集齊變量直接指到專案原本那 10 個 `cg_*` 變量。

    python3 larch/swap_park_plugin.py --dry     # 只印會變成什麼，不寫
    python3 larch/swap_park_plugin.py           # 真的換

推之前先備份整塊版子到 larch/inv/backups/，推完回讀比對卡數與邊數。
作者的編輯器分頁要關著（If-Match 會擋下衝突，看到 409 就是有人開著）。
"""
import argparse, json, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
PID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BASE = f"https://larch.ink/api/agent/projects/{PID}"
BOARD, NODE = "board-main", "inv-park-gacha"
MANIFEST = ROOT / "larch/cards/park-arcade.larch-plugin.json"

BG = ("https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/"
      "larch/project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4/1789499006706_bg-park-lobby-v1.webp")
BGM = "https://yazelin.github.io/glitch-park-gacha/assets/audio/glitch-park-theme.mp3"
# 照線上選單原本的順序與字，一個字都不改
GAMES = [
    ("◉ 扭蛋機",     "gacha",   "https://yazelin.github.io/glitch-park-gacha/"),
    ("◇ 夾娃娃機",   "claw",    "https://yazelin.github.io/glitch-park-claw/"),
    ("✦ 777 拉霸",   "slots",   "https://yazelin.github.io/glitch-park-slots/"),
    ("◎ 幸運轉盤",   "wheel",   "https://yazelin.github.io/glitch-park-wheel/"),
    ("● 霓虹鋼珠台", "pinball", "https://yazelin.github.io/glitch-park-pinball/"),
]


def request(path, method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        h["If-Match"] = etag
    req = urllib.request.Request(BASE + path, data, h, method=method)
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
        return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def plugin_values():
    # 背景那張在專案素材庫裡，所以走 asset 欄位；主題曲在 GitHub Pages 上，素材庫沒有，
    # 走 bgmUrl（asset 欄位比對不到外部網址，Inspector 會顯示成「未選擇」）。
    v = {"subtitle": "今晚想先玩哪一台？", "background": BG,
         "bgmUrl": BGM, "bgmVolume": 0.27, "leaveLabel": "← 離開遊樂園",
         "leaveResultVar": "park_leave_trigger"}
    # 1.1.0 起一款一行：名稱 | 網址 | 前綴 | 存檔變量 | 結果變量 | 未集齊變量
    # （平台每張卡最多收 30 個欄位，六欄乘五款加全域會被靜默砍掉）
    for i, (label, key, url) in enumerate(GAMES, 1):
        v[f"game{i}"] = " | ".join([label, url, key, f"{key}_state",
                                    f"cg_{key}_trigger", f"cg_{key}_incomplete_trigger"])
    return v


def new_data(old):
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    card = m["cards"][0]
    return {
        "type": "plugin",
        "pluginId": m["id"], "pluginCardId": card["id"],
        "pluginName": m["name"], "pluginCardName": card["name"],
        "pluginIcon": card.get("icon", "dices"), "pluginColor": card.get("color", "#6b2d8f"),
        "pluginVersion": m["version"], "pluginHtml": card["html"],
        "pluginPresentation": "fullscreen", "pluginSkippable": True,
        # 原本那張 miniGame 卡就是 showTitle/showButton 都關，換過來要一樣，
        # 不然畫面上會多一條外框與一顆「套用結果並繼續」。
        "pluginFrame": {"showTitle": False, "showButton": False, "backgroundOpacity": 0},
        "pluginAssets": [], "platforms": ["web"], "voiceMode": "off",
        "pluginValues": plugin_values(),
        # 讀寫白名單照抄原本那張卡：少一個變量，那一款的存檔或觸發會被靜默擋掉
        "pluginReadVars": list(old.get("miniGameReadVars") or old["pluginReadVars"]),
        "pluginWriteVars": list(old.get("miniGameWriteVars") or old["pluginWriteVars"]),
        "title": old["title"], "text": "",
        "transition": old.get("transition", "fade"), "transitionMs": old.get("transitionMs", 420),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    board, etag = request(f"/boards/{BOARD}")
    b = board.get("board", board)
    nodes, edges = b["nodes"], b["edges"]
    ts = time.strftime("%Y%m%d-%H%M")
    bak = ROOT / f"larch/inv/backups/board-main-{ts}-before-plugin-swap.json"
    bak.write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
    print(f"讀到 卡 {len(nodes)} 邊 {len(edges)}｜revision {etag}｜備份 {bak.name}")

    hit = [n for n in nodes if n["id"] == NODE]
    if len(hit) != 1:
        sys.exit(f"找不到 {NODE}（或不只一張）")
    node = hit[0]
    old = node["data"]
    again = old.get("type") == "plugin"
    if again:
        print("這張卡已經是插件卡，原地更新（html 與 pluginValues 重寫）")
    d = new_data(old)
    outs = [e for e in edges if e["source"] == NODE]
    print(f"換：{old['type']} → plugin｜出邊 {len(outs)} 條原樣不動")
    print("pluginValues：", json.dumps(d["pluginValues"], ensure_ascii=False)[:200], "…")
    print("寫入白名單", len(d["pluginWriteVars"]), "個變量｜pluginHtml", len(d["pluginHtml"]), "字")
    if a.dry:
        print("（--dry，沒有寫）")
        return

    node["data"] = d
    body = {"name": b.get("name"), "nodes": nodes, "edges": edges,
            "summary": "遊樂園入口換成 arcade-hub 插件卡（節點 id 與 12 條下游邊不動）"}
    _, new_etag = request(f"/boards/{BOARD}", "PUT", body, etag)
    print("已寫入｜新 revision", new_etag)

    back, _ = request(f"/boards/{BOARD}")
    bb = back.get("board", back)
    got = [n for n in bb["nodes"] if n["id"] == NODE][0]["data"]
    outs2 = [e for e in bb["edges"] if e["source"] == NODE]
    print(f"回讀 卡 {len(bb['nodes'])}（原 {len(nodes)}）邊 {len(bb['edges'])}（原 {len(edges)}）")
    print("回讀卡片型別", got.get("type"), got.get("pluginId"), got.get("pluginCardId"),
          "｜出邊", len(outs2), "條")
    ok = (len(bb["nodes"]) == len(nodes) and len(bb["edges"]) == len(edges)
          and got.get("type") == "plugin" and len(outs2) == len(outs)
          and got.get("pluginValues", {}).get("game5", "").endswith("cg_pinball_incomplete_trigger"))
    print("全部對得上" if ok else "★ 對不上，拿備份回復")
    sys.exit(0 if ok else 1)


main()
