#!/usr/bin/env python3
"""重配走 Larch 那批含（舞台指示）的台詞。

**平台是照板上的字唸的**，`POST /voice/generate` 只收 nodeId／lineIndex，
不收文字（2026-09-14 實測：回傳的 text 欄位逐字等於卡片上的字，括號也在裡面）。
所以要它不要唸括號，只能讓板上那一行暫時沒有括號：

    1. 抓板子 → 把受影響那幾行的 text 換成 voice.to_speech() 的結果
    2. PUT 上去（**這是暫時的板子，字面上少了括號，玩家會看到**）
    3. 逐行生成、抓回本機（檔名仍照原本要顯示的字算雜湊）
    4. 跑一次正常的 push.py 把真正的板子推回去

第 4 步一定要做，而且要對卡數。中途失敗的話板上會留著沒有括號的字，
那個狀態看起來完全正常——**失敗長相是「畫面少了幾個動作描述」，不會報錯。**
"""
import argparse, json, pathlib, re, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
sys.path.insert(0, str(ROOT / "larch/inv"))
OUT = ROOT / "art/voice"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")


def main():
    ap = argparse.ArgumentParser()
    # **--keys 是給「spoken.json 說配過了、但音檔證明沒有」用的。**
    # 那份紀錄是這支工具自己的跳過依據，它一旦寫錯，這幾句就永遠跳過永遠不修。
    # 真正的判準是聽寫（tools/paren_check.py），不是紀錄。
    ap.add_argument("--keys", default="")
    a = ap.parse_args()
    force = {x for x in a.keys.replace(",", " ").split() if x}
    import push as P, voice as V
    from voice import LARCH_VOICE as LV
    pid = json.loads((ROOT / "larch/inv/state.json").read_text())["projectId"]
    board = P.api("GET", f"/projects/{pid}/boards/board-main")
    board = board.get("board") or board

    # **要重配哪幾句，看我們自己的 board.json，不看線上板子。**
    # 線上那一份可能已經是上一輪推上去的「暫時版」（括號被拿掉了），
    # 拿它當清單的話會回報「要重配 0 句」——2026-09-14 中過：
    # 上一輪被殺在中途，21 句只生了 10 句，重跑卻說沒事做。
    src = json.loads((ROOT / "larch/inv/out/board.json").read_text(encoding="utf-8"))
    want = {}      # (nodeId, lineIndex) → (speaker, 顯示文字, emotion, 代號, 要唸的字)
    spoken_p = ROOT / "art/voice/spoken.json"
    spoken = json.loads(spoken_p.read_text(encoding="utf-8")) if spoken_p.exists() else {}
    for n in src["nodes"]:
        d = n.get("data") or {}
        dl = d.get("dialogueLines") or []
        items = ([(i, l) for i, l in enumerate(dl)] if dl else [(None, d)])
        for idx, holder in items:
            sp = holder.get("speaker")
            tx = holder.get("speakText") or holder.get("text")
            # 選哪幾句：**含（舞台指示）的，加上「逼——嗶」那個提示音**。
            # 不整張替身表套下去——那張表大部分是為本機 CosyVoice 的毛病加的
            # （design/配音待辦.md：「航」那個替身是為本機加的，MiniMax 不見得
            # 有同一個毛病），套到 Larch 上可能反而把對的唸成錯的。
            # 括號與提示音這兩類跟引擎無關：一個是不該唸的動作描述，
            # 一個是寫成兩個字的一聲提示音。
            if sp not in LV or not tx:
                continue
            if not re.search(r"[（(]", str(tx)) and "逼——嗶" not in str(tx):
                continue
            said = V.to_speech(str(tx))
            if not said.strip() or said == tx:
                continue
            k = V.key(sp, str(tx), holder.get("emotion") or None)
            # **已經是照新文字唸過的就跳過**，靠 spoken.json 比對，不是靠檔案在不在：
            # 檔名是「要顯示的字」的雜湊，改的是「要唸的字」，所以檔名不會變。
            if spoken.get(k) == said and k not in force:
                continue
            # **用「講者＋台詞」當鍵，不要用卡片編號。** 推送層會自己加卡，
            # 所以本機 board.json 的 inv-NNN 跟線上的同名卡不是同一張
            # （2026-09-14：本機 724 張、線上 770 張，對 21 句全部落空，
            # 而它回報的是「要重配 0 句」——看起來像沒事做）。
            ent = (sp, str(tx), holder.get("emotion") or "", k, said)
            want[(sp, str(tx))] = ent      # 板上還是原文
            want[(sp, said)] = ent         # 板上已經是去括號版

    jobs, dirty = [], [False]
    for n in board["nodes"]:
        d = n.get("data") or {}
        dl = d.get("dialogueLines") or []
        items = ([(i, l) for i, l in enumerate(dl)] if dl else [(None, d)])
        for idx, holder in items:
            # **線上那一行可能已經是「拿掉括號」的版本**（上一輪推過暫時版），
            # 所以兩種寫法都要對得到：帶括號的原文、以及去括號之後的字。
            # 只拿原文比對的話，補跑會回報「要重配 0 句」——2026-09-14 連中三次。
            cur = str(holder.get("speakText") or holder.get("text") or "")
            hit = want.get((holder.get("speaker"), cur))
            if not hit:
                continue
            sp, tx, emo, k, said = hit
            jobs.append((n["id"], idx, sp, tx, emo, k, said))
            if cur != said:
                holder["text"] = said    # 暫時把板上的字換掉
                dirty[0] = True
    print(f"要重配 {len(jobs)} 句")
    if not jobs:
        return 0

    if not dirty[0]:
        print("線上那幾行已經是去括號版了，不用再推暫時板子。")
    if dirty[0]:
        P.api("PUT", f"/projects/{pid}/boards/board-main",
              {"name": board.get("name") or "調查篇", "nodes": board["nodes"],
               "edges": board["edges"], "summary": "暫時：拿掉舞台指示以便重配音"})
        print("暫時的板子推上去了。**跑完一定要用 push.py 推回正常版。**")

    ok = fail = 0
    for i, (nid, idx, sp, tx, emo, k, said) in enumerate(jobs, 1):
        body = {"nodeId": nid, "voiceId": LV[sp][0], "emotion": emo}
        if idx is not None:
            body["lineIndex"] = idx
        try:
            r = P.api("POST", f"/projects/{pid}/voice/generate", body)
            got = (r.get("text") or "").strip()
            if got != said.strip():
                raise RuntimeError(f"平台唸的不是我們要的：{got[:24]!r}")
            url = (r.get("asset") or {}).get("url")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as f:
                (OUT / f"{k}.mp3").write_bytes(f.read())
            spoken[k] = said
            spoken_p.write_text(json.dumps(spoken, ensure_ascii=False, indent=0), encoding="utf-8")
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  ★ {sp}｜{tx[:16]}｜{e}")
        time.sleep(0.5)
        if i % 10 == 0 or i == len(jobs):
            print(f"  {i}/{len(jobs)}　成功 {ok}　失敗 {fail}", flush=True)
    print(f"完成 {ok}、失敗 {fail}")
    print("★ 現在去跑 python3 larch/inv/push.py 把正常的板子推回去，並對 776 卡。")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
