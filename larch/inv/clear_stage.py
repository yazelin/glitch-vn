"""段落收尾清場卡（2026-09-17 他抓到：換場景時前一場的人跑進後一場）。

每個段落最後那張「回調查板」的 boardJump 前面插一張沒有人的空卡：台上只放看不見的演員（novelkit 實測，
空的 actors 會把上一張的人留著），沒有字、零點三秒自己走。手機橫幅的觸發變數（open_studio、pr_request_sent）
從前一張搬到清場卡上，橫幅跳出來時畫面上已經沒有人。

push.py（建置）與 larch/add_clear_stage.py（線上先讀再補）都呼叫 apply()；用 id `clear-<boardJump id>` 冪等。
選單的「回板」（`*-back`）不插：那裡還沒進場景。
"""

BANNER_VARS = {"open_studio", "pr_request_sent"}   # 跟 push.py 的 phones 那張表對應


def ghost_stage(ghost):
    return ({"actors": [{"id": "actor-none", "url": ghost, "name": "", "slot": "center",
                         "scale": 0.01, "offsetX": 0, "offsetY": 0, "enter": "fade", "loop": "none"}]},
            [{"id": "layer-none", "url": ghost, "position": "center", "x": 0, "y": 0, "scale": 0.01, "opacity": 1, "flipX": False}])


def apply(nodes, edges, board_card, ghost):
    """就地改 nodes／edges，回傳插了幾張。"""
    by = {n["id"]: n for n in nodes}
    inn = {}
    for e in edges:
        inn.setdefault(e["target"], []).append(e)
    n = 0
    for bj in [x for x in nodes if x["data"].get("type") == "boardJump" and x["data"].get("jumpNodeId") == board_card
               and not x["id"].endswith("-back")]:
        cid = f"clear-{bj['id']}"
        preds = inn.get(bj["id"], [])
        if cid in by or not preds:
            continue
        stage, layers = ghost_stage(ghost)
        data = {"type": "dialogue", "title": "（清場）", "text": "", "speaker": "", "stage": stage, "characterLayers": layers,
                "autoAdvance": {"enabled": True, "mode": "delay", "delayMs": 300}}
        moved = []
        for e in preds:
            p = by[e["source"]]["data"]
            keep = [op for op in p.get("variableOps") or [] if op.get("variable") not in BANNER_VARS]
            moved += [op for op in p.get("variableOps") or [] if op.get("variable") in BANNER_VARS]
            if keep:
                p["variableOps"] = keep
            else:
                p.pop("variableOps", None)
        if moved:
            data["variableOps"] = moved
        pos = bj.get("position") or {"x": 0, "y": 0}
        node = {"id": cid, "type": "story", "position": {"x": pos.get("x", 0) - 180, "y": pos.get("y", 0) + 120}, "data": data}
        if bj.get("parentId"):
            node["parentId"] = bj["parentId"]
        nodes.append(node); by[cid] = node
        for e in preds:
            e["target"] = cid
        edges.append({"id": f"edge-{cid}-go", "source": cid, "target": bj["id"], "sourceHandle": "right", "animated": True})
        n += 1
    return n


def apply_autorecord(nodes, edges):
    """劇情模式跳過「開錄音機／不開」：前一張卡多一條 mode=='story' 的條件邊直接接到「開錄音機」那條分支
    （排在既有的邊前面，跟 CG 解鎖卡同一種寫法）。自由探索照舊。2026-09-17 他問「劇情模式是否固定只能按錄，以免沒拿到 CG」。"""
    by = {n["id"]: n for n in nodes}
    n = 0
    for ch in [x for x in nodes if x["data"].get("type") == "choice" and (x["data"].get("choices") or [""])[0] == "開錄音機"]:
        rec = next((e["target"] for e in edges if e["source"] == ch["id"] and e.get("sourceHandle") == "choice-0"), None)
        if not rec:
            continue
        for pred in [e["source"] for e in edges if e["target"] == ch["id"]]:
            eid = f"edge-autorec-{ch['id']}-{pred}"
            if any(e.get("id") == eid for e in edges):
                continue
            leaf = {"variable": "mode", "op": "eq", "value": "story"}
            cond = {"kind": "variable", **leaf, "match": "all", "conditions": [leaf]}
            first = next(i for i, e in enumerate(edges) if e["source"] == pred)
            edges.insert(first, {"id": eid, "source": pred, "target": rec, "sourceHandle": "right", "animated": True, "data": {"condition": cond}})
            n += 1
    return n


if __name__ == "__main__":
    nodes = [{"id": "p", "type": "story", "data": {"type": "dialogue"}},
             {"id": "c", "type": "story", "data": {"type": "choice", "choices": ["開錄音機", "不開"]}},
             {"id": "rec", "type": "story", "data": {"type": "plugin"}}, {"id": "no", "type": "story", "data": {"type": "dialogue"}}]
    edges = [{"id": "e1", "source": "p", "target": "c"}, {"id": "e2", "source": "c", "target": "rec", "sourceHandle": "choice-0"},
             {"id": "e3", "source": "c", "target": "no", "sourceHandle": "choice-1"}]
    assert apply_autorecord(nodes, edges) == 1 and edges[0]["target"] == "rec" and edges[0]["data"]["condition"]["value"] == "story"
    assert apply_autorecord(nodes, edges) == 0

    nodes = [{"id": "b", "type": "story", "data": {"type": "miniGame"}},
             {"id": "d1", "type": "story", "data": {"type": "dialogue", "variableOps": [{"variable": "open_studio"}, {"variable": "x"}]}},
             {"id": "j", "type": "story", "position": {"x": 10, "y": 10}, "data": {"type": "boardJump", "jumpNodeId": "b"}},
             {"id": "m-back", "type": "story", "data": {"type": "boardJump", "jumpNodeId": "b"}}]
    edges = [{"id": "e1", "source": "d1", "target": "j"}, {"id": "e2", "source": "b", "target": "m-back"}]
    assert apply(nodes, edges, "b", "g") == 1
    assert edges[0]["target"] == "clear-j" and edges[-1]["source"] == "clear-j" and edges[-1]["target"] == "j"
    assert nodes[1]["data"]["variableOps"] == [{"variable": "x"}] and nodes[-1]["data"]["variableOps"] == [{"variable": "open_studio"}]
    assert apply(nodes, edges, "b", "g") == 0     # 冪等
    print("ok")
