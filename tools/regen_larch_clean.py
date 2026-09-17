#!/usr/bin/env python3
"""走 Larch 音色的句子，讓平台唸「該唸的字」而不是「板上的字」（括號舞台指示、替身）。

    python3 tools/regen_larch_clean.py --keys v-…,v-…

做法跟 tools/regen_larch_paren.py 一樣是暫時改板：
    1. 讀線上版子（**不是本機重建**，樂園那些卡都在），存一份原樣
    2. 受影響的那幾行 text 換成 voice.to_speech() 的結果，PUT 上去
    3. 逐行生成、抓回 art/voice/<代號>.mp3（代號照原本顯示的字算，跟 urls.json 一致）
    4. **把第 1 步存的原樣 PUT 回去**（不是 push.py——push.py 會把樂園洗掉），推前推後對卡數
中途失敗也會走到第 4 步。線上講者是顯示名（經紀人／修收音機的），先換回本名才算得到代號。
"""
import argparse, json, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch")); sys.path.insert(0, str(ROOT / "larch/inv"))
import voice as V
import push as P

KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
PID = json.loads((ROOT / "larch/inv/state.json").read_text())["projectId"]
BASE = f"https://larch.ink/api/agent/projects/{PID}"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
OUT = ROOT / "art/voice"


def req(path, method="GET", body=None, etag=None):
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        h["If-Match"] = etag
    r = urllib.request.urlopen(urllib.request.Request(BASE + path, json.dumps(body, ensure_ascii=False).encode() if body is not None else None, h, method=method), timeout=300)
    raw = r.read()
    return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def put_board(board, why):
    for attempt in range(5):
        _, etag = req("/boards/board-main")
        try:
            req("/boards/board-main", "PUT", {"name": board.get("name", "調查篇"), "kind": board.get("kind", "story"), "mode": board.get("mode", "story"),
                                             "nodes": board["nodes"], "edges": board["edges"], "summary": why}, etag)
            return
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    a = ap.parse_args()
    want = {x for x in a.keys.replace(",", " ").split() if x}
    REV = {v: k for k, v in P.DISPLAY.items()}
    LV = V.LARCH_VOICE

    payload, _ = req("/boards/board-main")
    board = payload.get("board", payload)
    original = json.loads(json.dumps(board))          # 原樣，最後要 PUT 回去
    n0 = (len(board["nodes"]), len(board["edges"]))

    # 找受影響的行，改成要唸的字
    targets = []   # (nodeId, lineIndex|None, 本名, 原字, 代號)
    for n in board["nodes"]:
        d = n["data"]
        rows = [(i, l) for i, l in enumerate(d.get("dialogueLines") or [])] or [(None, d)]
        for i, l in rows:
            sp = REV.get(l.get("speaker"), l.get("speaker")); tx = l.get("speakText") or l.get("text")
            if not sp or not tx:
                continue
            k = V.key(sp, tx, l.get("emotion") or None)
            if k in want:
                said = V.to_speech(str(tx))
                l["text"] = said
                if "speakText" in l:
                    l["speakText"] = said
                targets.append((n["id"], i, sp, tx, k, said))
    miss = want - {t[4] for t in targets}
    if miss:
        print(f"★ 板上找不到：{sorted(miss)}")
    if not targets:
        return 1
    print(f"暫時改板：{len(targets)} 行去括號／換替身")
    put_board(board, "regen_larch_clean 暫時版：這幾行改成要唸的字，生完馬上換回")
    spoken_p = ROOT / "art/voice/spoken.json"
    spoken = json.loads(spoken_p.read_text(encoding="utf-8"))
    ok = fail = 0
    try:
        for nid, idx, sp, tx, k, said in targets:
            body = {"nodeId": nid, "boardId": "board-main", "voiceId": LV[sp][0], "emotion": "", "rememberForCharacter": False}
            if idx is not None:
                body["lineIndex"] = idx
            try:
                r, _ = req("/voice/generate", "POST", body)
                url = (r.get("asset") or {}).get("url")
                got = (r.get("text") or "").strip()
                if got and got != said.strip():
                    print(f"  ★ 平台唸的字不是我們給的：{got[:30]!r}")
                data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
                # level_voice 讀 art/voice、先把原檔備份到 pre-level 再壓；這裡順手也放一份到 pre-level，
                # 讓「壓過的」與「原始的」兩邊都是這一版（帳本用檔名對雜湊，新檔自然會重壓）
                (OUT / f"{k}.mp3").write_bytes(data); (OUT / "pre-level" / f"{k}.mp3").write_bytes(data)
                spoken[k] = said
                spoken_p.write_text(json.dumps(spoken, ensure_ascii=False, indent=0), encoding="utf-8")
                ok += 1; print(f"  {ok + fail}/{len(targets)} {sp} {said[:22]!r}")
            except Exception as e:
                fail += 1; print(f"  ★ {sp} {said[:22]!r} {e}")
            time.sleep(0.5)
    finally:
        put_board(original, "regen_larch_clean：換回原樣（括號回來）")
        back, _ = req("/boards/board-main"); back = back.get("board", back)
        n1 = (len(back["nodes"]), len(back["edges"]))
        chk = next((l.get("text") for n in back["nodes"] if n["id"] == targets[0][0]
                    for l in ([n["data"]] if targets[0][1] is None else [n["data"]["dialogueLines"][targets[0][1]]])), None)
        print(f"換回原樣：卡 {n1[0]}/{n0[0]} 邊 {n1[1]}/{n0[1]}", "一致" if n1 == n0 else "★ 不一致", "| 第一行現在：", repr((chk or "")[:24]))
    print(f"完成：{ok} 個，失敗 {fail} 個")
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
