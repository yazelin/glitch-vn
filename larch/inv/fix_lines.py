#!/usr/bin/env python3
"""2026-10-01 台詞審查的修正，做法同 patch_live.py：讀線上、逐句改、PUT 回去、對卡數線數。

每一筆指名「哪張卡第幾句、哪段字換成哪段字」，改之前先比對整句原文，
對不上就停（代表線上被別人改過，要人看）；已經是新字就跳過，所以可重跑。
審查理由寫在 design/調查篇-台詞審查-2026-10-01.md，編號跟這裡的 OPS 一致。

兩類：
  A 免重配：旁白（無聲）、括號裡的舞台指示（配音管線本來就濾掉）、同音字（他／她、你／妳）、講者名。
  B 要重配：台詞的音變了。不帶 --regen 不會動，免得字跟聲音對不上；重配之後再帶 --regen 推。

    python3 larch/inv/fix_lines.py --dry                       # 讀線上，只印會改哪幾句
    python3 larch/inv/fix_lines.py --dry --snapshot x.json      # 對存好的版子快照算，不連線
    python3 larch/inv/fix_lines.py                             # 推 A 類
    python3 larch/inv/fix_lines.py --regen                     # A＋B 一起推（B 的音檔要先重生好）
"""
import argparse, datetime, json, pathlib, sys, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_live import request  # noqa: E402  Bearer + If-Match 都在那裡

BID = "board-main"
SHE = "妳"

# (編號, 類, 卡, 第幾句, 找, 換)；找＝None 表示改講者名，換＝新講者名
OPS = [
    # 一、旁白把主角寫成「玩家」（正典：旁白指主角一律「她」）
    ("A01", "A", "inv-191", 9, "玩家把本子", "她把本子"),
    ("A02", "A", "inv-338", 9, "玩家的手", "她的手"),
    ("A03", "A", "inv-367", 0, "玩家走過去", "她走過去"),
    ("A04", "A", "inv-373", 0, "玩家還沒有開口", "她還沒有開口"),
    ("A05", "A", "inv-378", 0, "玩家把本子收起來", "她把本子收起來"),
    ("A06", "A", "inv-378", 2, "玩家停下來", "她停下來"),
    ("A07", "A", "inv-384", 2, "玩家還沒有問", "她還沒有問"),
    ("A08", "A", "inv-389", 3, "玩家往旁邊", "她往旁邊"),
    ("A09", "A", "inv-649", 1, "玩家把鐵門帶上。她沒有回頭。", "她把鐵門帶上。桌前那個人沒有回頭。"),
    ("A10", "A", "inv-063", 5, "（他看了玩家一眼）", "（他看了她一眼）"),
    ("A11", "A", "inv-338", 6, "看了一眼玩家手上", "看了一眼她手上"),
    # 二、旁白人稱與名字
    ("A12", "A", "inv-348", 26, "她看了他零點四秒。", "0x 看了她零點四秒。"),
    ("A13", "A", "inv-467", 22, "斑比從那一疊裡", "那個人從那一疊裡"),
    ("A14", "A", "inv-161", 0, "她還沒開口。斑比先講。", "她還沒開口，對方先講了。"),
    ("A15", "A", "inv-164", 4, "斑比沒有等她回答。", "對方沒有等她回答。"),
    # 三、筆記與台詞的同音字（音檔不變）
    ("A16", "A", "inv-657", 0, "他記得我", "她記得我"),
    ("A17", "A", "inv-657", 0, "他一天遞出去", "她一天遞出去"),
    *[(f"A18.{i}", "A", c, n, "你", SHE) for i, (c, n) in enumerate([
        ("inv-240", 3), ("inv-240", 14), ("inv-247", 0), ("inv-250", 2), ("inv-250", 4),
        ("inv-253", 2), ("inv-253", 10), ("inv-253", 16), ("inv-253", 20), ("inv-253", 24),
        ("inv-256", 0), ("inv-256", 2), ("inv-348", 6), ("inv-348", 14), ("inv-588", 7),
        ("inv-594", 1), ("inv-594", 5), ("inv-598", 1), ("inv-598", 7), ("inv-598", 8),
        ("inv-598", 10), ("inv-656", 1), ("inv-604", 2), ("inv-604", 4)], 1)],
    # 四、建置漏進台詞的設計註記（音檔當初就沒唸這行）
    ("A19", "A", "inv-629", 0, "\n（後期這一行會被劃掉。）", ""),
    ("A20", "A", "inv-073", 0, "信箱那邊", "信箱那邊。"),
    ("A21", "A", "inv-448", 0, "信箱那邊", "信箱那邊。"),
    # 五、講者名比她知道的多（問到名字是 inv-153）
    ("A22", "A", "inv-168", None, "斑比", "抱洗衣粉的人"),
    ("A23", "A", "inv-649", None, "斑比", "畫她的人"),
    ("A24", "A", "inv-161", None, "斑比", "畫她的人"),
    ("A25", "A", "inv-164", None, "斑比", "畫她的人"),
    ("A26", "A", "inv-150", None, "斑比", "畫她的人"),
    ("A27", "A", "inv-tape-rec_bambi", None, "斑比", "畫她的人"),
    # B：音變了，要重配
    ("B01", "B", "inv-656", 0, "小姐，補習班。", "補習班，看一下。"),
    ("B02", "B", "inv-198", 22, "中山北路那家還有舊的。", "站前那家還有舊的。"),
    ("B04", "B", "inv-535", 11, "說是公司派來的。", "說是公司派來的。你這個講法我沒聽過。"),
    ("B05", "B", "inv-537", 4, "一個月兩次。", "一個月兩次。還有一個，一整袋菜放在信箱前面就走了，隔天回來還問我是誰放的。"),
    ("B06", "B", "inv-411", 4, "報過三次。", "報過四次。"),
    ("B07", "B", "inv-651", 2, "二十年。", "十幾年。"),
]
# 不收的：inv-202 筆記把貓草轉述那句抄漏「因為」「啊」是設計刻意的（問答矩陣「這一格的註」：留著，不要幫他補）。

# 設計稿裡頭尾兩句是旁白、只有中間那句是筆記（橋段2「（旁白・描述動作）」），建置把三句併成玩家一句。
# 拆回三行；玩家那句跟 inv-445 同字，直接借它的音檔，所以不用重配。
SPLITS = {
    "A28": ("inv-408", "本子今天第一次翻開。四點多了。\n我答應過他。\n那一行下面沒有字。他闔上本子。", [
        ("旁白", "本子今天第一次翻開。四點多了。", "描述動作"),
        ("玩家", "我答應過他。", "@inv-445"),
        ("旁白", "那一行下面沒有字。她闔上本子。", "描述動作"),
    ]),
}


def holders(d):
    return d.get("dialogueLines") or [d]


def apply(board, kinds, log):
    nodes = {n["id"]: n for n in board["nodes"]}
    done = skip = 0
    for oid, kind, cid, idx, find, rep in OPS:
        if kind not in kinds:
            continue
        d = nodes[cid]["data"]
        if idx is None:                       # 講者名：每一行、卡層、舞台演員一起換
            hs = [h for h in holders(d) if h.get("speaker") == find]
            if not hs and any(h.get("speaker") == rep for h in holders(d)):
                skip += 1
                continue
            assert hs, f"{oid} {cid}：找不到講者 {find}"
            for h in hs:
                h["speaker"] = rep
            if d.get("speaker") == find:
                d["speaker"] = rep
            for a in (d.get("stage") or {}).get("actors", []):
                if a.get("name") == find:
                    a["name"] = rep
            log.append(f"{oid} {cid} 講者 {find} → {rep}（{len(hs)} 句）")
            done += 1
            continue
        h = holders(d)[idx]
        t = h["text"]
        # 做過了就跳過：刪除類看舊字還在不在；替換類看新字在不在（「那邊」→「那邊。」這種新字包著舊字的也算）
        if (find not in t) if not rep else (rep in t and (find not in t or find in rep)):
            skip += 1
            continue
        if find in t:
            new = t.replace(find, rep) if find == "你" else t.replace(find, rep, 1)
        else:
            raise SystemExit(f"{oid} {cid}#{idx} 原文對不上，線上可能被改過：{t!r}")
        if new == t:
            skip += 1
            continue
        h["text"] = new
        if h is not d and idx == 0 and d.get("text") == t:   # 卡層 text 跟第一句同步
            d["text"] = new
        log.append(f"{oid} {cid}#{idx}\n    舊：{t}\n    新：{new}")
        done += 1
    for oid, (cid, old, rows) in SPLITS.items():
        if "A" not in kinds:
            continue
        d = nodes[cid]["data"]
        if d.get("dialogueLines"):
            skip += 1
            continue
        if d.get("text") != old:
            raise SystemExit(f"{oid} {cid} 原文對不上，線上可能被改過：{d.get('text')!r}")
        lines = []
        for i, (sp, text, emo) in enumerate(rows):
            l = {"id": f"l{i}", "text": text, "emotion": "" if emo.startswith("@") else emo, "speaker": sp}
            if emo.startswith("@"):
                l["voiceUrl"] = nodes[emo[1:]]["data"]["voiceUrl"]
            lines.append(l)
        d["dialogueLines"] = lines
        d.pop("voiceUrl", None)
        d["text"], d["speaker"] = "我答應過他。", "玩家"
        log.append(f"{oid} {cid} 拆成三行：旁白／玩家（借 inv-445 音檔）／旁白")
        done += 1
    return done, skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--regen", action="store_true", help="連 B 類一起推（音檔要先重生）")
    ap.add_argument("--snapshot", help="GET /boards/board-main 存下來的 JSON；給了就不連線")
    a = ap.parse_args()
    kinds = {"A", "B"} if a.regen else {"A"}

    if a.snapshot:
        payload, etag = json.loads(pathlib.Path(a.snapshot).read_text(encoding="utf-8")), None
    else:
        payload, etag = request(f"/boards/{BID}")
    board = payload.get("board", payload)
    before = (len(board["nodes"]), len(board["edges"]))
    log = []
    done, skip = apply(board, kinds, log)
    print("\n".join(log))
    print(f"改 {done} 句、已改過跳過 {skip}（類別 {'＋'.join(sorted(kinds))}；卡 {before[0]}、邊 {before[1]}）")
    if a.dry or a.snapshot or not done:
        return
    bk = HERE / "backups" / f"board-main-{datetime.datetime.now():%Y%m%d-%H%M}-before-fix-lines.json"
    bk.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    for attempt in range(5):
        try:
            request(f"/boards/{BID}", "PUT", {"name": board.get("name", BID), "kind": board.get("kind", "story"),
                    "mode": board.get("mode", "story"), "nodes": board["nodes"], "edges": board["edges"],
                    "summary": "fix_lines.py：2026-10-01 台詞審查"}, etag)
            break
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            print(f"  409，重讀再送（第 {attempt + 1} 次）")
            payload, etag = request(f"/boards/{BID}")
            board = payload.get("board", payload)
            apply(board, kinds, [])
    back, _ = request(f"/boards/{BID}")
    back = back.get("board", back)
    after = (len(back["nodes"]), len(back["edges"]))
    left, _ = apply(back, kinds, [])
    print(f"  回讀：卡 {after[0]}/{before[0]}　邊 {after[1]}/{before[1]}　還沒改到 {left} 句",
          "一致" if after == before and not left else "★ 不一致，去查")
    assert after == before and not left


if __name__ == "__main__":
    main()
