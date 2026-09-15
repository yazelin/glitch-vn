#!/usr/bin/env python3
"""一個角色的台詞串成一份稿，丟給 Larch 一次唸完，抓回長檔。

**為什麼不逐句。** 平台的 `POST /voice/generate` 一行一次，實測每句約 44 秒；
57 句就是四十分鐘。串成一份稿一次呼叫，一個長檔就全部有了。
正篇的黑洞先生、諾亞、鐵塔本來就是這樣做的（`tools/split_take.py` 的檔頭）。

**規模控制在 50 句上下。** split_take 的實測：10/10、18/18、26/26、50/50 一次到位，
152 句那份試了五次才成。不要為了省一次呼叫把一百多句塞進同一塊。

稿是我們自己組的，所以**讀音替身在這條路上有效**（逐句那條沒有——
平台是照板上的字唸的，我們插不進去）。

    python3 tools/larch_take.py 保全 --board inv
    python3 tools/larch_take.py 保全 --board inv --dry    # 只印稿不呼叫

抓回來的長檔放 art/voice/takes/<角色>.mp3，接著跑：
    ~/voice-venv/bin/python tools/split_take.py 保全 art/voice/takes/保全.mp3
"""
import argparse, json, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "larch"))
sys.path.insert(0, str(ROOT / "larch/inv"))
TAKES = ROOT / "art/voice/takes"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
# 拿來放稿的卡：**用沙盒專案，不要動正式那塊板子**。
SANDBOX = "project-5aae449c-12f0-46d3-8c2c-dbcde62b0769"   # 「__AI測試（可刪）」


def script_of(who, board):
    import gen_voice as G, voice as V
    rows = [(t, e, k) for w, t, e, k in G.utterances()
            if w == who and (not board or G.BOARD_OF.get(k) == board)]
    # **一句一行，而且是替身版的文字**：split_take 對齊時用的也是 to_speech 的輸出。
    lines = [V.to_speech(t) for t, _, _ in rows]
    return rows, "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("who")
    ap.add_argument("--board", default="", help="inv＝只取調查篇；空＝全部")
    ap.add_argument("--voice", default="", help="蓋掉 LARCH_VOICE 裡的音色")
    ap.add_argument("--project", default=SANDBOX)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    import push as P
    from voice import LARCH_VOICE as LV
    rows, text = script_of(a.who, a.board)
    if not rows:
        sys.exit(f"找不到 {a.who} 的台詞")
    vid = a.voice or (LV.get(a.who) or (None,))[0]
    if not vid:
        sys.exit(f"{a.who} 沒有指定 Larch 音色，用 --voice 給一個")
    print(f"{a.who}：{len(rows)} 句、{len(text)} 字、音色 {vid}")
    if len(rows) > 60:
        print("★ 超過 60 句。split_take 的實測是 50 句以內一次到位，建議分塊。")
    if a.dry:
        print("-" * 40); print(text[:600]); return 0

    # 稿放進沙盒專案的一張對話卡，再對那張卡叫生成。
    nid = f"take-{a.who}"
    board = P.api("GET", f"/projects/{a.project}/boards/board-main")
    board = board.get("board") or board
    nodes = [n for n in board.get("nodes", []) if n["id"] != nid]
    nodes.append({"id": nid, "type": "story", "position": {"x": 0, "y": 0},
                  "data": {"type": "dialogue", "title": f"長檔：{a.who}",
                           "speaker": a.who, "text": text}})
    P.api("PUT", f"/projects/{a.project}/boards/board-main",
          {"name": board.get("name") or "沙盒", "nodes": nodes,
           "edges": board.get("edges", []), "summary": f"長檔稿：{a.who}"})
    print("稿放上沙盒卡了，開始生成（長檔會跑比較久）")

    t0 = time.time()
    r = P.api("POST", f"/projects/{a.project}/voice/generate",
              {"nodeId": nid, "voiceId": vid, "emotion": ""})
    url = (r.get("asset") or {}).get("url")
    if not url:
        sys.exit(f"回傳沒有網址：{json.dumps(r, ensure_ascii=False)[:200]}")
    got = (r.get("text") or "").strip()
    if got != text.strip():
        print(f"★ 平台唸的跟稿不同：長度 {len(got)} vs {len(text)}")
    TAKES.mkdir(parents=True, exist_ok=True)
    out = TAKES / f"{a.who}.mp3"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as f:
        out.write_bytes(f.read())
    # 長檔這條路記的是「稿上的字」，也就是 to_speech 的輸出——那才是實際唸出去的。
    # 逐句那條（gen_larch_voice.py）記的是板上的字，因為平台照板上的字唸。
    # **兩條路線的語意不同，改替身之後誰會被判定過期也不同**，不要合併。
    import json as _j
    sp = ROOT / "art/voice/spoken.json"
    rec = _j.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    import voice as _V
    for t, _e, k in rows:
        rec[k] = _V.to_speech(t)
    sp.write_text(_j.dumps(rec, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"抓回來了：{out}　{out.stat().st_size//1024}KB　花了 {time.time()-t0:.0f} 秒")
    print(f"接著跑：~/voice-venv/bin/python tools/split_take.py {a.who} {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
