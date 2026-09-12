#!/usr/bin/env python3
"""路人那批走 Larch 的音色：呼叫平台生成、抓回本機、照內容雜湊命名。

**為什麼不是走 tools/gen_voice.py。** 本機選角池的男聲用完了（見 larch/voice.py
的 LARCH_VOICE 檔頭），這九個角色的音色掛在平台上。平台的 `POST /voice/generate`
一行一次，回傳裡直接帶 mp3 網址，抓下來就是一個普通檔案。

**抓下來之後就跟本機生的走同一條路**：art/voice/<代號>.mp3 → level_voice 統一響度
→ publish_voice 進 docs/voice → urls.json → build 掛回板子。
不留在平台上的理由：平台那份改不了響度（音檔在它的 R2 上），而且那是另一個
事實來源，urls.json 與它會慢慢分岔。

    python3 tools/gen_larch_voice.py --list     # 只列出要生幾句
    python3 tools/gen_larch_voice.py            # 生（已經有檔的自動跳過，可以中斷續跑）

**中斷續跑是必要的不是方便。** 184 句一次跑完要好幾分鐘，中途失敗留下的是
「有些角色換好了、有些還沒」，而那個狀態從檔案上看不出來（交辦狀態-1806.md 第一條）。
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
sys.path.insert(0, str(ROOT / "larch/inv"))
OUT = ROOT / "art/voice"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")


def todo(board):
    """回 [(nodeId, lineIndex 或 None, 講者, 台詞, emotion, 代號)]。"""
    import voice as V
    from voice import LARCH_VOICE as LV
    have = {p.stem for p in OUT.glob("*.mp3")} | {p.stem for p in (ROOT / "docs/voice").glob("*.mp3")}
    rows, seen = [], set()
    for n in board["nodes"]:
        d = n.get("data") or {}
        dl = d.get("dialogueLines") or []
        items = ([(i, l.get("speaker"), l.get("text"), l.get("emotion")) for i, l in enumerate(dl)]
                 if dl else [(None, d.get("speaker"), d.get("speakText") or d.get("text"), d.get("emotion"))])
        for idx, sp, tx, emo in items:
            if sp not in LV or not tx or not str(tx).strip():
                continue
            k = V.key(sp, tx, emo or None)
            # 同一句話在板上會出現好幾次，生一次就夠（檔名是內容雜湊）
            if k in seen or k in have:
                continue
            seen.add(k)
            rows.append((n["id"], idx, sp, tx, emo or "", k))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--who", default="")
    a = ap.parse_args()

    import push as P
    from voice import LARCH_VOICE as LV
    pid = json.loads((ROOT / "larch/inv/state.json").read_text())["projectId"]
    board = P.api("GET", f"/projects/{pid}/boards/board-main")
    board = board.get("board") or board
    rows = todo(board)
    if a.who:
        rows = [r for r in rows if r[2] == a.who]

    import collections
    by = collections.Counter(r[2] for r in rows)
    print(f"要生 {len(rows)} 句（去重後）")
    for w, c in by.most_common():
        print(f"  {w:<8}{c:>4} 句　{LV[w][0]}")
    if a.list:
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for i, (nid, idx, sp, tx, emo, k) in enumerate(rows, 1):
        body = {"nodeId": nid, "voiceId": LV[sp][0], "emotion": emo or ""}
        if idx is not None:
            body["lineIndex"] = idx
        try:
            r = P.api("POST", f"/projects/{pid}/voice/generate", body)
            url = (r.get("asset") or {}).get("url")
            if not url:
                raise RuntimeError(f"回傳沒有網址：{json.dumps(r, ensure_ascii=False)[:120]}")
            # **要比對回傳的 text。** 平台是照 nodeId/lineIndex 去板上抓字的，
            # 板上那一行跟我們手上這一句不一樣的話，生出來的是別句話，
            # 而檔名（內容雜湊）會讓它看起來完全正確。
            got = (r.get("text") or "").strip()
            if got != str(tx).strip():
                raise RuntimeError(f"平台唸的跟我們要的不同：{got[:20]!r} != {str(tx)[:20]!r}")
            # **下載要帶瀏覽器 UA。** 音檔在 Cloudflare R2 後面，Python 預設的
            # `Python-urllib/3.x` 會被擋成 403（內文 `error code: 1010`，那是
            # 瀏覽器完整性檢查，不是權限也不是節流）。curl 帶得過是因為它的 UA 不一樣。
            # **這個 403 出現在下載那一步，不是在產生那一步**——產生已經成功了，
            # 平台那邊也計費了，只是檔案抓不回來。2026-09-12 為此誤判成「整批被節流」，
            # 還寫了一段退避重試，退避對它完全無效。
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as f:
                (OUT / f"{k}.mp3").write_bytes(f.read())
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  ★ {sp}｜{str(tx)[:16]}｜{e}")
        time.sleep(0.5)      # 對平台客氣一點，不是必要的
        if i % 20 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}　成功 {ok}　失敗 {fail}")
    print(f"完成：{ok} 個，失敗 {fail} 個（再跑一次會只補失敗的那些）")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
