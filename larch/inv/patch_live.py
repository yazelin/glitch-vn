#!/usr/bin/env python3
"""不重建、不整包推，直接修線上版子上的三件事：

  一、講者名照 push.py 的 DISPLAY（鐵塔→經紀人、貓草→客人、諾亞→修收音機的）：
      dialogue 的 speaker、多人卡每一行的 speaker、舞台演員的名字。
  二、調查板／選單／謝幕那幾張卡 HTML 裡嵌的名字表（DISPLAY_UI／DISPLAY 的 JSON）換成現在的。
  三、voiceUrl 從 GitHub Pages 換成 jsDelivr（novelkit.cdn()）。

**做法跟 larch/add_*.py 一樣：先讀線上現在的版子，在上面改，再 PUT 回去。**
不碰任何沒動到的卡，所以樂園五款遊戲、CG 解鎖那些線上才有的東西原封不動。
推之前跟推之後都對卡數與邊數，變了就是出事。

    python3 larch/inv/patch_live.py --dry                 # 讀線上，只印會改幾處，不寫
    python3 larch/inv/patch_live.py --dry --snapshot x.json   # 對著存好的快照算，不連線
    python3 larch/inv/patch_live.py                       # 真的改
"""
import argparse, json, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import push as PUSH          # DISPLAY／DISPLAY_UI 只在那裡寫一次
import novelkit as NK        # cdn()

KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
STATE = json.loads((HERE / "state.json").read_text(encoding="utf-8"))
BASE = f"https://larch.ink/api/agent/projects/{STATE['projectId']}"
# 主版最後推：平台把最後一次 PUT 的版子當主線（activeBoardId），配音生成只在主線找卡。
BOARDS = ("board-credits", "board-main")


def request(path, method="GET", body=None, etag=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if etag:
        h["If-Match"] = etag
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data, h, method=method), timeout=300) as r:
        raw = r.read()
        return (json.loads(raw) if raw else {}), r.headers.get("ETag")


def swap_tables(html, stats):
    """卡片 HTML 裡嵌的名字表：找到以「{"鐵塔": …」開頭的 JSON 物件，整個換掉。
    有 "斑比" 那一層的是 DISPLAY_UI（調查板、選單），沒有的是 DISPLAY（謝幕）。"""
    dec = json.JSONDecoder()
    i = 0
    while True:
        i = html.find('{"鐵塔":', i)
        if i < 0:
            return html
        obj, end = dec.raw_decode(html, i)
        new = PUSH.DISPLAY_UI if "斑比" in obj else PUSH.DISPLAY
        rep = json.dumps(new, ensure_ascii=False)
        if html[i:end] != rep:
            stats["table"] += 1
        html = html[:i] + rep + html[end:]
        i += len(rep)


# 四、調查板卡片裡的劇情軌道那一段換成新的（larch/cards/board.html 同一段，改了要兩邊一起改）。
#     線上那張卡的 HTML 是 push.py 從 board.html 灌進去的，除了照片表與名字表之外原文不動，
#     所以拿舊段落原文去找，找到就換。找不到＝線上已經是新的，或 board.html 又改過，都印出來。
RAIL_OLD = """    var rs = railTo ? spotAt(railTo) : null;
    if(!rs || !drawn(rs) || !isOpen(rs) || rs.live[slot]===null || rs.live[slot]===undefined){"""
RAIL_NEW = """    var rs = railTo ? spotAt(railTo) : null;
    if(rs && !rs.sealed){
      [].concat(rs.gate||[], rs.showIf||[]).forEach(function(k){
        if(k && values[k]!==true && values[k]!=='true'){ values[k]=true; setVar(k, true); }
      });
    }
    if(!rs || !drawn(rs) || !isOpen(rs) || rs.live[slot]===null || rs.live[slot]===undefined){"""


# 遊樂園不吃時段（board.html start() 那一行，改了要兩邊一起改）
PARK_OLD = "  if(values.dest){ advance(); setVar('dest',''); setVar('here',''); }"
PARK_NEW = "  if(values.dest){ if(values.dest!=='park') advance(); setVar('dest',''); setVar('here',''); }"


def swap_board_js(html, stats):
    for old, new, name in ((RAIL_OLD, RAIL_NEW, "rail"), (PARK_OLD, PARK_NEW, "rail")):
        if old in html:
            html = html.replace(old, new, 1); stats[name] += 1
        elif new not in html:
            print(f"  ★ 調查板卡片裡找不到這一段的新舊版本（{old[:30]}…），去對 board.html")
    return html


# 五、筆記卡的 `~~劃掉~~` 改成組合字元畫線（build.py 同一條規則），字改了配音代號也跟著變，
#     所以每一句都用原講者＋現在的字重查一次 urls.json，查得到就換成新檔（順便走 jsDelivr）。
STRIKE = re.compile(r"~~(.+?)~~")


def strike(text):
    return STRIKE.sub(lambda m: "".join(ch + "̶" for ch in m.group(1)), text)


def rekey_voice(holder, speaker, stats):
    import voice as V
    if not speaker:
        return
    u = NK.VOICE_URLS.get(V.key(speaker, holder.get("speakText") or holder.get("text"), holder.get("emotion") or None))
    if u and NK.cdn(u) != holder.get("voiceUrl"):
        holder["voiceUrl"] = NK.cdn(u); stats["rekey"] += 1


def patch(board, stats):
    disp = PUSH.DISPLAY
    for n in board["nodes"]:
        d = n["data"]
        if d.get("type") == "miniGame" and "function walkMap()" in (d.get("miniGameHtml") or ""):
            d["miniGameHtml"] = swap_board_js(d["miniGameHtml"], stats)
        # 六、謝幕字卷的副標：2026-09-09 拉成十四天，字卷那張卡沒跟上（字是隔開排的，grep「十二天」找不到）
        for k in ("miniGameHtml", "pluginHtml", "html"):
            if isinstance(d.get(k), str) and "十 二 天" in d[k]:
                d[k] = d[k].replace("調 查 篇　・　十 二 天", "調 查 篇　・　十 四 天"); stats["strike"] += 1
        if d.get("type") == "dialogue" and "~~" in (d.get("text") or ""):
            d["text"] = strike(d["text"]); stats["strike"] += 1
        # 講者還是原名的時候先重查配音（改名之後就對不到 urls.json 的鍵了）
        if d.get("type") == "dialogue":
            if d.get("dialogueLines"):
                for l in d["dialogueLines"]:
                    rekey_voice(l, l.get("speaker"), stats)
            else:
                rekey_voice(d, d.get("speaker"), stats)
    for n in board["nodes"]:
        d = n["data"]
        if d.get("speaker") in disp:
            d["speaker"] = disp[d["speaker"]]; stats["speaker"] += 1
        for l in d.get("dialogueLines") or []:
            if l.get("speaker") in disp:
                l["speaker"] = disp[l["speaker"]]; stats["speaker"] += 1
            if l.get("voiceUrl") and NK.cdn(l["voiceUrl"]) != l["voiceUrl"]:
                l["voiceUrl"] = NK.cdn(l["voiceUrl"]); stats["voice"] += 1
        for a in (d.get("stage") or {}).get("actors") or []:
            if a.get("name") in disp:
                a["name"] = disp[a["name"]]; stats["speaker"] += 1
        if d.get("voiceUrl") and NK.cdn(d["voiceUrl"]) != d["voiceUrl"]:
            d["voiceUrl"] = NK.cdn(d["voiceUrl"]); stats["voice"] += 1
        for k in ("miniGameHtml", "pluginHtml", "html"):
            if isinstance(d.get(k), str) and '{"鐵塔":' in d[k]:
                d[k] = swap_tables(d[k], stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--snapshot", help="GET /projects/:id 存下來的 JSON；給了就不連線")
    a = ap.parse_args()

    snap = json.loads(pathlib.Path(a.snapshot).read_text(encoding="utf-8")) if a.snapshot else None
    for bid in BOARDS:
        if snap:
            board, etag = next(b for b in snap["boards"] if b["id"] == bid), None
        else:
            # 一塊一塊讀：PUT 第一塊會推進整個專案的版本號，第二塊的 ETag 要在它自己 PUT 前才拿（不然 409）
            payload, etag = request(f"/boards/{bid}")
            board = payload.get("board", payload)
        before = (len(board["nodes"]), len(board["edges"]))
        stats = {"speaker": 0, "voice": 0, "table": 0, "rail": 0, "strike": 0, "rekey": 0}
        patch(board, stats)
        print(f"{bid}：講者名 {stats['speaker']} 處、音檔網址 {stats['voice']} 處（其中換新檔 {stats['rekey']}）、"
              f"名字表 {stats['table']} 張卡、調查板軌道段落 {stats['rail']}、刪除線 {stats['strike']} 張"
              f"　（卡 {before[0]}、邊 {before[1]}，不動）")
        if a.dry or not any(stats.values()):
            continue
        # 編輯器分頁開著就會一直墊高版本號（config.py 那邊記過），409 就重讀、重改、重送。
        for attempt in range(5):
            try:
                request(f"/boards/{bid}", "PUT", {
                    "name": board.get("name", bid), "kind": board.get("kind", "story"), "mode": board.get("mode", "story"),
                    "nodes": board["nodes"], "edges": board["edges"],
                    "summary": "patch_live.py：講者名改成她知道的叫法、音檔改走 jsDelivr"}, etag)
                break
            except urllib.error.HTTPError as e:
                if e.code != 409 or attempt == 4:
                    raise
                print(f"  409 版本被墊高，重讀再送（第 {attempt + 1} 次）")
                payload, etag = request(f"/boards/{bid}")
                board = payload.get("board", payload)
                patch(board, {k: 0 for k in stats})
        back, _ = request(f"/boards/{bid}")
        back = back.get("board", back)
        after = (len(back["nodes"]), len(back["edges"]))
        print(f"  回讀：卡 {after[0]}/{before[0]}　邊 {after[1]}/{before[1]}", "一致" if after == before else "★ 不一致，去查")
        assert after == before


if __name__ == "__main__":
    main()
