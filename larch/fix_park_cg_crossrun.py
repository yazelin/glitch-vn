#!/usr/bin/env python3
"""讓遊樂園五款遊戲依本次結果解鎖完整／未集齊 CG，並以跨周目收藏防止重播。"""

from __future__ import annotations

import json
import pathlib
import urllib.request


PROJECT_ID = "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4"
BASE = f"https://larch.ink/api/agent/projects/{PROJECT_ID}"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
ORIGINAL_PROJECT_COVER = (
    "https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/"
    "2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/1789116293673_cover.webp"
)

GAMES = [
    {
        "key": "gacha", "label": "扭蛋", "event": "gacha", "state": "gacha_state",
        "title": "扭蛋全收集", "complete_file": "cg-gacha-complete-v2.webp",
        "complete_text": "恭喜你集齊全部扭蛋！這張遊樂園紀念 CG 送給你。",
        "incomplete_title": "扭蛋未集齊紀念", "incomplete_file": "cg-gacha-complete-v1.webp",
        "incomplete_text": "這次還沒有集齊全部扭蛋，但這段遊樂園回憶也值得收藏。",
    },
    {
        "key": "claw", "label": "娃娃", "event": "claw", "state": "claw_state",
        "title": "娃娃全收集", "complete_file": "cg-claw-complete-v2.webp",
        "complete_text": "恭喜你夾到全部娃娃！這張遊樂園紀念 CG 是你的了。",
        "incomplete_title": "娃娃未集齊紀念", "incomplete_file": "cg-claw-complete-v1.webp",
        "incomplete_text": "這次還沒有夾齊全部娃娃，先把這段可愛的回憶送給你。",
    },
    {
        "key": "slots", "label": "777 拉霸", "event": "slots", "state": "slots_state",
        "title": "777 全收集", "complete_file": "cg-slots-complete-v2.webp",
        "complete_text": "恭喜你集齊全部 777 中獎角色！這張遊樂園紀念 CG 送給你。",
        "incomplete_title": "777 未集齊紀念", "incomplete_file": "cg-slots-complete-v1.webp",
        "incomplete_text": "這次還沒有集齊全部中獎角色，先留下這張拉霸紀念 CG。",
    },
    {
        "key": "wheel", "label": "幸運轉盤", "event": "wheel", "state": "wheel_state",
        "title": "幸運轉盤全收集", "complete_file": "cg-wheel-complete-v2.webp",
        "complete_text": "恭喜你讓幸運轉盤遇見了全員！這張遊樂園紀念 CG 送給你。",
        "incomplete_title": "幸運轉盤未集齊紀念", "incomplete_file": "cg-wheel-complete-v1.webp",
        "incomplete_text": "這次轉盤還沒有遇見全員，先收藏今天的幸運紀念。",
    },
    {
        "key": "pinball", "label": "霓虹鋼珠台", "event": "pinball", "state": "pinball_state",
        "title": "霓虹鋼珠台全點亮", "complete_file": "cg-pinball-complete-v2.webp",
        "complete_text": "恭喜你點亮全部角色燈！這張遊樂園紀念 CG 送給你。",
        "incomplete_title": "霓虹鋼珠台未集齊紀念", "incomplete_file": "cg-pinball-complete-v1.webp",
        "incomplete_text": "這次還沒有點亮全員，先收下這張霓虹鋼珠台紀念 CG。",
    },
]


def request(path="", method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        headers["If-Match"] = etag
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as response:
        raw = response.read()
        return (json.loads(raw) if raw else {}), response.headers.get("ETag")


def base36(number):
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if not number:
        return "0"
    result = ""
    while number:
        result = digits[number % 36] + result
        number //= 36
    return result


def cg_key(url):
    value = 2166136261
    for char in url:
        value ^= ord(char)
        value = (value * 16777619) & 0xFFFFFFFF
    return f"__larch_cg__:{base36(len(url))}-{base36(value)}"


def all_condition(result_variable, cg_url, title):
    conditions = [
        {"variable": result_variable, "variableLabel": result_variable, "op": "eq", "value": True},
        {"variable": cg_key(cg_url), "variableLabel": title, "op": "eq", "value": False},
    ]
    return {
        "kind": "variable", "match": "all", "conditions": conditions,
        **conditions[0],
    }


def game_html(spec, source_url):
    key, event, state = spec["key"], spec["event"], spec["state"]
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#10091d}}iframe{{display:block;width:100%;height:100%;border:0}}</style></head><body><iframe id="game" title="{spec["label"]}" src="{source_url}"></iframe><script>
var game=document.getElementById('game'),state=null,parkMusic=null,parkMusicUrl='';
function music(d){{if(d.url&&(!parkMusic||parkMusicUrl!==d.url)){{if(parkMusic)parkMusic.pause();parkMusicUrl=d.url;parkMusic=new Audio(d.url);parkMusic.loop=true;parkMusic.preload='metadata';parkMusic.volume=.27}}if(!parkMusic)return;if(d.action==='mute'){{parkMusic.muted=!!d.muted;if(d.muted)parkMusic.pause()}}if(d.action==='play'&&!d.muted){{parkMusic.muted=false;parkMusic.play().catch(function(){{}})}}}}
parent.postMessage({{type:'larch:ready'}},'*');
addEventListener('message',function(e){{var d=e.data;if(!d||!d.type)return;if(d.type==='larch:init'){{var raw=d.variables&&d.variables.{state};try{{state=raw?JSON.parse(raw):null}}catch(err){{state=null}}return}}if(e.source!==game.contentWindow)return;if(d.type==='glitch-park:music'){{music(d);return}}if(d.type==='{event}:ready'){{game.contentWindow.postMessage({{type:'{event}:state',state:state}},'*');return}}if(d.type==='{event}:save'){{state=d.state;parent.postMessage({{type:'larch:set',name:'{state}',value:JSON.stringify(state)}},'*');return}}if(d.type==='{event}:exit'){{if(parkMusic)parkMusic.pause();var complete=!!d.complete;parent.postMessage({{type:'larch:set',name:'cg_{key}_trigger',value:complete}},'*');parent.postMessage({{type:'larch:set',name:'cg_{key}_incomplete_trigger',value:!complete}},'*');setTimeout(function(){{parent.postMessage({{type:'larch:complete',result:'exit',payload:{{complete:complete}}}},'*')}},240)}}}});
</script></body></html>'''


def main():
    project, project_etag = request()
    board_raw, board_etag = request("/boards/board-main")
    board = board_raw.get("board", board_raw)
    original_nodes = json.loads(json.dumps(board["nodes"]))
    original_edges = json.loads(json.dumps(board["edges"]))
    nodes = board["nodes"]
    edges = board["edges"]
    by_id = {node["id"]: node for node in nodes}
    media = {asset.get("name"): asset.get("url") for asset in project.get("media", [])}

    for spec in GAMES:
        for field in ("complete_file", "incomplete_file"):
            if not media.get(spec[field]):
                raise RuntimeError(f"素材庫缺少 {spec[field]}")

    gallery = project["settings"].get("cgGalleryItems", [])
    gallery_by_url = {item.get("url"): item for item in gallery}
    # 修正既有鋼珠台未集齊標題的錯字。
    gallery_by_url[media["cg-pinball-complete-v1.webp"]]["title"] = "霓虹鋼珠台未集齊紀念"
    # 從 2026-09-16 CG 修改前的專案快照恢復；CG 接線不應替換專案縮圖。
    # Larch stores the project-list thumbnail and the in-player title cover
    # separately.  Keep both explicit so the title screen cannot fall back to
    # media[0] when CG assets are added or reordered.
    project["settings"]["projectThumbnail"] = ORIGINAL_PROJECT_COVER
    project["settings"]["titleCoverImage"] = ORIGINAL_PROJECT_COVER

    obsolete = {
        f"cg_{spec['key']}_unlocked" for spec in GAMES
    } | {
        f"cg_{spec['key']}_incomplete_unlocked" for spec in GAMES
    }
    project["variables"] = [
        variable for variable in project.get("variables", [])
        if variable.get("name") not in obsolete
    ]

    row_y = {
        "gacha": -6000,
        "claw": -5400,
        "slots": -4800,
        "wheel": -4200,
        "pinball": -3600,
    }
    by_id["inv-park-gacha"]["position"] = {"x": 0, "y": -4800}

    for index, spec in enumerate(GAMES):
        key = spec["key"]
        game_id = f"inv-park-game-{key}"
        game = by_id[game_id]
        game["position"] = {"x": 400, "y": row_y[key]}
        old_html = game["data"]["miniGameHtml"]
        marker = 'src="'
        source_url = old_html.split(marker, 1)[1].split('"', 1)[0]
        game["data"]["miniGameHtml"] = game_html(spec, source_url)
        game["data"]["miniGameReadVars"] = [spec["state"]]
        game["data"]["miniGameWriteVars"] = [
            spec["state"], f"cg_{key}_trigger", f"cg_{key}_incomplete_trigger"
        ]

        complete_url = media[spec["complete_file"]]
        incomplete_url = media[spec["incomplete_file"]]
        full_dialogue = by_id[f"inv-park-cg-{key}"]
        full_unlock = by_id[f"inv-park-cg-unlock-{key}"]
        full_dialogue["position"] = {"x": 800, "y": row_y[key] - 130}
        full_unlock["position"] = {"x": 1160, "y": row_y[key] - 130}
        full_dialogue["data"].update({
            "text": spec["complete_text"], "title": f"格莉奇：{spec['title']}",
            "background": complete_url,
        })
        full_unlock["data"].pop("variableOps", None)
        full_unlock["data"]["cgOps"] = [{
            "id": f"op-cg-{key}-gallery", "url": complete_url, "mode": "unlock"
        }]

        incomplete_dialogue_id = f"inv-park-cg-{key}-incomplete"
        incomplete_unlock_id = f"inv-park-cg-unlock-{key}-incomplete"
        incomplete_dialogue = {
            "id": incomplete_dialogue_id,
            "type": "story",
            "position": {"x": 800, "y": row_y[key] + 130},
            "data": {
                "type": "dialogue", "title": f"格莉奇：{spec['incomplete_title']}",
                "speaker": "格莉奇", "text": spec["incomplete_text"],
                "background": incomplete_url, "transition": "fade", "transitionMs": 420,
            },
        }
        incomplete_unlock = {
            "id": incomplete_unlock_id,
            "type": "story",
            "position": {"x": 1160, "y": row_y[key] + 130},
            "data": {
                "type": "setVariable", "title": f"解鎖：{spec['incomplete_title']}",
                "text": "新的遊樂園紀念 CG 已加入收藏。",
                "cgOps": [{
                    "id": f"op-cg-{key}-incomplete-gallery",
                    "url": incomplete_url, "mode": "unlock",
                }],
            },
        }
        for new_node in (incomplete_dialogue, incomplete_unlock):
            current = by_id.get(new_node["id"])
            if current:
                current.update(new_node)
            else:
                nodes.append(new_node)
                by_id[new_node["id"]] = new_node

        removed_ids = {
            f"e-park-game-{key}-cg", f"e-park-game-{key}-return",
            f"e-park-cg-{key}-unlock", f"e-park-cg-{key}-lobby",
            f"e-park-game-{key}-incomplete-cg",
            f"e-park-cg-{key}-incomplete-unlock",
            f"e-park-cg-{key}-incomplete-lobby",
        }
        edges[:] = [edge for edge in edges if edge.get("id") not in removed_ids]
        first = next((i for i, edge in enumerate(edges) if edge.get("source") == game_id), len(edges))
        routes = [
            {
                "id": f"e-park-game-{key}-cg", "source": game_id,
                "target": f"inv-park-cg-{key}", "animated": True, "sourceHandle": "right",
                "data": {"condition": all_condition(f"cg_{key}_trigger", complete_url, spec["title"])},
            },
            {
                "id": f"e-park-game-{key}-incomplete-cg", "source": game_id,
                "target": incomplete_dialogue_id, "animated": True, "sourceHandle": "right",
                "data": {"condition": all_condition(
                    f"cg_{key}_incomplete_trigger", incomplete_url, spec["incomplete_title"]
                )},
            },
            {
                "id": f"e-park-game-{key}-return", "source": game_id,
                "target": "inv-park-gacha", "animated": True, "sourceHandle": "right",
            },
        ]
        edges[first:first] = routes
        edges.extend([
            {
                "id": f"e-park-cg-{key}-unlock", "source": f"inv-park-cg-{key}",
                "target": f"inv-park-cg-unlock-{key}", "animated": True, "sourceHandle": "right",
            },
            {
                "id": f"e-park-cg-{key}-lobby", "source": f"inv-park-cg-unlock-{key}",
                "target": "inv-park-gacha", "animated": True, "sourceHandle": "right",
            },
            {
                "id": f"e-park-cg-{key}-incomplete-unlock", "source": incomplete_dialogue_id,
                "target": incomplete_unlock_id, "animated": True, "sourceHandle": "right",
            },
            {
                "id": f"e-park-cg-{key}-incomplete-lobby", "source": incomplete_unlock_id,
                "target": "inv-park-gacha", "animated": True, "sourceHandle": "right",
            },
        ])

    request("", "PUT", {
        "project": project,
        "summary": "遊樂園十張 CG 改用跨周目收藏判斷，並分流集齊與未集齊結果",
    }, project_etag)
    # 專案層更新也會推進整體版號；重讀白板取得新 ETag，並確認期間沒有內容異動。
    latest_raw, board_etag = request("/boards/board-main")
    latest_board = latest_raw.get("board", latest_raw)
    if latest_board.get("nodes") != original_nodes or latest_board.get("edges") != original_edges:
        raise RuntimeError("白板在處理期間被其他來源修改，已停止寫入以免覆蓋")
    request("/boards/board-main", "PUT", {
        "name": board["name"], "kind": board.get("kind", "story"),
        "mode": board.get("mode", "story"), "nodes": nodes, "edges": edges,
        "summary": "五款遊戲依集齊狀態解鎖對應 CG，取得過的 CG 不再重播",
    }, board_etag)
    print("遊樂園 5 張全收集與 5 張未集齊 CG 已完成跨周目分流。")


if __name__ == "__main__":
    main()
