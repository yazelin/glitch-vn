#!/usr/bin/env python3
"""線上版子兩件小修，做法同 patch_live.py（讀線上、改、PUT 回去），可重跑（做過就跳過）：

  一、inv-331 從「玩家：Radio Noah。」後面切成兩張：前半諾亞維持 down（沒有抬頭），
      後半新卡 inv-331b 從「旁白：修收音機的把手上的東西放下來。」起用 up（他這一整段唯一抬頭的地方）。
      同一列右邊三張卡（inv-332、clear-inv-333、inv-333）各往右挪一格讓位，只動位置。
  二、兩張故事 CG 解鎖卡（店員點餐、櫃檯第六次）cgOps 裡還留著第一版的解鎖，收藏格只列 direction-v2，
      把第一版那筆拿掉，之後素材庫那兩張第一版就沒人引用了。

    python3 larch/inv/split_331.py --dry
    python3 larch/inv/split_331.py
"""
import argparse, copy, datetime, json, pathlib, sys, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_live import request  # noqa: E402  Bearer + If-Match 都在那裡

BID = "board-main"
SPLIT_AT = "Radio Noah。"          # 這句（含）以前留在 inv-331
NEW_ID = "inv-331b"
UP = "1789649912724_sprite-noah-up.png"
STEP = 360                         # 版子上一格
V1_CG = ("_cg-story-clerk-order.webp", "_cg-story-reception-sixth.webp")


def split(board, stats):
    nodes = {n["id"]: n for n in board["nodes"]}
    if NEW_ID in nodes:
        return
    a = nodes["inv-331"]
    lines = a["data"]["dialogueLines"]
    cut = next(i for i, l in enumerate(lines) if l["text"].strip() == SPLIT_AT) + 1
    b = copy.deepcopy(a)
    b["id"] = NEW_ID
    a["data"]["dialogueLines"] = lines[:cut]
    b["data"]["dialogueLines"] = lines[cut:]
    first = next(l for l in b["data"]["dialogueLines"] if l["speaker"] != "旁白")
    b["data"]["speaker"] = first["speaker"]
    b["data"]["text"] = first["text"]
    b["data"]["title"] = "諾亞：" + first["text"][:20]
    for key in ("stage", "characterLayers"):
        for x in (b["data"].get(key) or {}).get("actors", []) if key == "stage" else b["data"].get(key, []):
            if "sprite-noah-" in x.get("url", ""):
                x["url"] = x["url"].rsplit("/", 1)[0] + "/" + UP
    # 讓位：同列右邊的卡往右一格
    y = a["position"]["y"]
    for n in board["nodes"]:
        if n.get("parentId") == a.get("parentId") and n["position"]["y"] == y and n["position"]["x"] > a["position"]["x"]:
            n["position"]["x"] += STEP
    b["position"] = {"x": a["position"]["x"] + STEP, "y": y}
    board["nodes"].insert(board["nodes"].index(a) + 1, b)
    e = next(e for e in board["edges"] if e["source"] == "inv-331")
    old_target = e["target"]
    e["target"] = NEW_ID
    eid = e["id"] + "b"
    assert eid not in {x["id"] for x in board["edges"]}
    board["edges"].append({"id": eid, "source": NEW_ID, "target": old_target, "animated": True, "sourceHandle": e.get("sourceHandle", "right")})
    stats["split"] = 1


def drop_v1_cg(board, stats):
    for n in board["nodes"]:
        ops = n["data"].get("cgOps")
        if not ops:
            continue
        keep = [o for o in ops if not o.get("url", "").endswith(V1_CG)]
        if len(keep) != len(ops):
            n["data"]["cgOps"] = keep
            stats["cg"] += len(ops) - len(keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    payload, etag = request(f"/boards/{BID}")
    board = payload.get("board", payload)
    before = (len(board["nodes"]), len(board["edges"]))
    bk = HERE / "backups" / f"inv-live-{datetime.datetime.now():%Y%m%d-%H%M}-before-split.json"
    bk.write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
    stats = {"split": 0, "cg": 0}
    split(board, stats); drop_v1_cg(board, stats)
    print(f"切卡 {stats['split']}、拿掉第一版 CG 解鎖 {stats['cg']} 筆（卡 {before[0]}、邊 {before[1]}；備份 {bk.name}）")
    if a.dry or not any(stats.values()):
        return
    want = (before[0] + stats["split"], before[1] + stats["split"])
    for attempt in range(5):
        try:
            request(f"/boards/{BID}", "PUT", {"name": board.get("name", BID), "kind": board.get("kind", "story"),
                    "mode": board.get("mode", "story"), "nodes": board["nodes"], "edges": board["edges"],
                    "summary": "split_331.py：inv-331 切卡讓諾亞抬頭；拿掉第一版 CG 解鎖"}, etag)
            break
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            print(f"  409，重讀再送（第 {attempt + 1} 次）")
            payload, etag = request(f"/boards/{BID}"); board = payload.get("board", payload)
            split(board, {"split": 0, "cg": 0}); drop_v1_cg(board, {"split": 0, "cg": 0})
    back, _ = request(f"/boards/{BID}"); back = back.get("board", back)
    after = (len(back["nodes"]), len(back["edges"]))
    nb = next(n for n in back["nodes"] if n["id"] == NEW_ID)
    print(f"  回讀：卡 {after[0]}（預期 {want[0]}）　邊 {after[1]}（預期 {want[1]}）",
          "一致" if after == want else "★ 不一致，去查",
          "｜新卡立繪", nb["data"]["stage"]["actors"][0]["url"].rsplit("/", 1)[-1],
          "｜台詞", len(nb["data"]["dialogueLines"]), "句")
    assert after == want


if __name__ == "__main__":
    main()
