#!/usr/bin/env python3
"""主角連結（2026-10-01 作者要的三件事）：玩家對主角的投射、提醒打開手機、讓玩家在守則本寫自己的筆記。

做法同 larch/add_*.py：讀線上、在上面補、PUT 回去、對卡數線數。可重跑（新卡在就跳過）。
設計理由與每一處的前後文：design/調查篇-主角連結.md（--review 產生）。

  一、桌前每一天多一兩句她自己的生活（無聲旁白）。第一、二天是新卡，其餘接在「第N天。」那張後面。
  二、第一天與第三到十三天，筆記之後問一題：選「寫一句」就翻開守則本的空白頁，頁首是今天的題目；
      寫下的字存進 notes_free，結局在第七行之前唸回第一則與最後一則（free_echo）。
  三、第二天收尾（第三天早上）手機亮一下，選「看一下」直接打開手機。板上便條底下多一行「包包」小字（bagLine）。
  四、三場對話後面加「怎麼回」的選項，路線不變，只換對方回的那一句。

新台詞先不配音（作者 2026-10-01 決定），之後 tools/gen_voice.py 補。
卡片程式（board／notes／todo.js）本機檔同步改過；整包重建之後重跑這支就會再補一次。

    python3 larch/inv/add_bond.py --dry                    # 讀線上，只印會加什麼
    python3 larch/inv/add_bond.py --review design/調查篇-主角連結.md   # 產對照稿（不寫線上）
    python3 larch/inv/add_bond.py                          # 推
"""
import argparse, copy, datetime, json, pathlib, sys, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_live import request  # noqa: E402

BID = "board-main"
CN = "零一二三四五六七八九十"
def cn(d): return CN[d] if d <= 10 else "十" + CN[d - 10]

# 一、桌前她自己的生活。判準照調查篇.md 零：講重複或被記住；不寫寂寞、不寫恐怖；
# 不寫任何依路線而定的事（收尾卡不看玩家去了哪裡）。
LIFE = {
    1: "桌上那本守則本的書籤還夾在第一頁。刷卡的時候店員問她要不要包裝。她說不用，要用的。",
    2: "她把錄音機、手機、本子在桌上排成一排。明天要帶的就這三樣。",
    3: "鬧鐘響之前她就醒了。她先摸到的是本子，不是手機。",
    4: "睡前她把明天要去的地方唸了一遍。唸到第三個就睡著了。",
    5: "刷牙的時候她發現自己在哼一樓那段廣告。哼到「欸，等一下」那裡，停了一下。",
    6: "她把本子的橡皮筋拉開，又套回去。第三次才翻開。",
    7: "她在本子封底內側寫了一個「燈」字，圈起來。",
    8: "她把鬧鐘往後調了一個小時。想了一下，又調回來。",
    9: "出門前她在門口站了一下，把包包裡的東西點了一遍。本子、手機、錄音機。她每天都點。",
    10: "洗臉的時候她對著鏡子說了一聲早安，跟聊天室那些人一樣。說完自己笑了一下。",
    11: "她現在每天早上先翻本子最後一頁，看昨天的自己寫了什麼，再決定今天去哪。",
    12: "本子已經寫掉一半。她用手指壓了一下還沒寫的那一疊，還很厚。",
    13: "她寫完最後一行，把書籤從第一頁拿出來，夾到明天那一頁。",
}
# 第三到十三天接在這張旁白後面；第一、二天沒有旁白卡，新開一張插在場景與筆記中間
NARR = {3: "inv-475", 4: "inv-479", 5: "inv-483", 6: "inv-487", 7: "inv-491", 8: "inv-495",
        9: "inv-499", 10: "inv-503", 11: "inv-507", 12: "inv-511", 13: "inv-515"}
NEWNARR = {1: ("inv-628", "inv-629"), 2: ("inv-642", "inv-643")}

# 二、每晚一題。題目是她問自己的，所以用「我」；玩家替她寫。
NOTE = {1: "inv-629", 3: "inv-476", 4: "inv-480", 5: "inv-484", 6: "inv-488", 7: "inv-492", 8: "inv-496",
        9: "inv-500", 10: "inv-504", 11: "inv-508", 12: "inv-512", 13: "inv-516"}
ASK = {
    1: "今天問到的人裡面，最想再見一次的是誰。",
    3: "到現在為止，誰講的話最不像在說謊。",
    4: "深夜的街上，跟白天差在哪裡。",
    5: "如果她真的會忘，她最先忘掉的會是什麼。",
    6: "今天有沒有人記得我。",
    7: "這幾天聽到的話裡面，我記得最清楚的一句。",
    8: "為什麼沒有人修好她。我現在的答案。",
    9: "被認出來的那一下，我在想什麼。",
    10: "那個穿西裝的人，換我來形容。",
    11: "如果她明天把我忘了，我想先跟她講哪一件事。",
    12: "我想對她說的一句話。",
    13: "明天要記得的事。",
}

# 三、第二天收尾（第三天早上播）的手機（這一天沒有題目：守則本與手機卡都沒有出口，一個插播裡只能接一張）
PHONE_NARR = "手機在枕頭旁邊亮了一下。螢幕上是她的帳號發的新貼文。"

# 結局：第一頁那份名單唸完、第七行之前
ECHO = ("inv-452", "inv-454", "她把本子翻到最後面，自己寫的那幾頁。\n{{free_echo}}\n她翻回第一頁。")

# 四、對話後面的回法。(錨點卡, 下一張, 選項卡的字, [(選項, [(講者, 台詞), …]), …])
REPLY = [
    ("inv-544", "inv-545", "他回去弄手上那台。", [
        ("你人真好。", [("玩家", "你人真好。"), ("修收音機的", "（沒有抬頭）她問，我就答。")]),
        ("……", [("旁白", "她沒有再問。他也沒有再講。螺絲起子轉了兩圈。")]),
    ]),
    ("inv-623", "inv-624", "他把杯子推過來。", [
        ("辛苦了。", [("玩家", "辛苦了。"), ("店員", "（停了一下）……還好。很少人講這個。")]),
        ("謝謝。", [("玩家", "謝謝。"), ("店員", "慢走。")]),
    ]),
    ("inv-326", "inv-327", "斑比看著那疊紙。", [
        ("為什麼不問？", [("玩家", "為什麼不問。"), ("斑比", "……問了，她要想很久。我不想讓她想。")]),
        ("我也不會問。", [("玩家", "我也不會問。"), ("斑比", "（看了她一眼）……嗯。")]),
    ]),
]

VARS = [
    {"id": "free_prompt", "name": "free_prompt", "type": "string", "label": "桌前那一題（守則本空白頁的頁首；收起來清空）", "defaultValue": ""},
    {"id": "free_count", "name": "free_count", "type": "number", "label": "空白頁寫了幾則", "defaultValue": 0},
    {"id": "free_echo", "name": "free_echo", "type": "string", "label": "結局唸回來的那兩則", "defaultValue": "那幾頁是空的。她一行都沒有寫。"},
]

# ── 卡片程式：同一組替換對同時套在本機檔與線上卡（每一組都 assert 找得到，做過就跳過）
NOTES_PAIRS = [
    ("var values={}, vars={}, done=false, free=[], tab=0, dirty=false;",
     "var values={}, vars={}, done=false, free=[], tab=0, dirty=false, wantFree=false;"),
    ("function saveFree(){ setVar('notes_free', JSON.stringify(free)); dirty=false; }",
     "function saveFree(){ setVar('notes_free', JSON.stringify(free)); setVar('free_count', free.length); setVar('free_echo', freeEcho()); dirty=false; }\n"
     "// 結局唸回來的那兩則（add_bond.py）。桌前那一題寫下的會帶「第N天｜」。\n"
     "function freeEcho(){\n"
     "  function say(t){ var m=String(t).match(/^(第.+?天)｜([\\s\\S]*)$/); return m ? m[1]+'她寫：「'+m[2]+'」' : '她寫過：「'+t+'」'; }\n"
     "  if(!free.length) return '那幾頁是空的。她一行都沒有寫。';\n"
     "  if(free.length===1) return '只有一則。'+say(free[0]);\n"
     "  return say(free[0])+'\\n'+say(free[free.length-1]);\n"
     "}"),
    ("  var ta=el('textarea'); ta.placeholder='自己寫點什麼。系統不會動這一頁。';",
     "  var ask=String(values.free_prompt||'').split('｜');\n"
     "  if(ask.length===2){ var h=el('p','ask',ask[1]); h.style.cssText='margin:0 0 .5em;font-style:italic;color:var(--cyan)'; box.insertBefore(h,box.firstChild); }\n"
     "  var ta=el('textarea'); ta.placeholder=ask.length===2?'寫一句。系統不會動這一頁。':'自己寫點什麼。系統不會動這一頁。';"),
    ("    free.push(t.slice(0,MAXLEN)); saveFree(); render();",
     "    var day=String(values.free_prompt||'').split('｜');\n"
     "    free.push((day.length===2?day[0]+'｜':'')+t.slice(0,MAXLEN)); saveFree(); render();"),
    ("  if(tab>=tabs.length) tab=0;",
     "  if(wantFree){ tab=tabs.indexOf('空白頁'); wantFree=false; }\n  if(tab>=tabs.length||tab<0) tab=0;"),
    ("  render();\n  document.getElementById('close')",
     "  wantFree=!!values.free_prompt;\n  render();\n  document.getElementById('close')"),
    ("    setVar('open_notes', false);   // interrupt 卡靠這個放人回原處",
     "    setVar('open_notes', false);   // interrupt 卡靠這個放人回原處\n    if(values.free_prompt) setVar('free_prompt', '');"),
]
BAGLINE = (
    "\n// 便條底下那一行「包包」小字（add_bond.py）：不佔上面三行，只提醒手機與本子。\n"
    "function bagLine(v){\n"
    "  function n(k){ var x=Number(v[k]); return isNaN(x)||v[k]===''||v[k]==null?0:x; }\n"
    "  var phone=n('phone_day_seen')<n('day'), book=n('free_count')===0;\n"
    "  if(n('day')<=1 && phone) return '包包裡有本子跟手機。手機亮過，還沒看。';\n"
    "  if(phone) return '手機亮過。還沒看。';\n"
    "  if(book && n('day')<=5) return '本子後面還空著。寫一句自己的。';\n"
    "  return '';\n"
    "}\n")
TODO_PAIRS = [("  return L.slice(0,3);\n}", "  return L.slice(0,3);\n}" + BAGLINE)]
BOARD_PAIRS = [
    ("todoLines(values).forEach(function(t){ var p=document.createElement('p'); p.textContent=t; todo.appendChild(p); });",
     "todoLines(values).forEach(function(t){ var p=document.createElement('p'); p.textContent=t; todo.appendChild(p); });\n"
     "  if(typeof bagLine==='function'){ var bl=bagLine(values); if(bl){ var bp=document.createElement('p'); bp.className='bag'; bp.textContent=bl; todo.appendChild(bp); } }"),
]
BOARD_CSS = (".todo p{margin:0;font:italic clamp(12px,1.55vw,14px)/1.5 \"Noto Serif TC\",\"Songti TC\",\"PMingLiU\",Georgia,serif}",
             ".todo p.bag{margin-top:.45em;padding-top:.35em;border-top:1px dashed rgba(0,0,0,.18);font-size:.9em;color:var(--ink2)}")


def swap(text, pairs, tag):
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, f"{tag}：找不到或不只一處 {old[:40]!r}"
        text = text.replace(old, new)
    return text


def css(text):
    old, add = BOARD_CSS
    if add in text:
        return text
    assert text.count(old) == 1, "board：找不到 .todo p 那一行"
    return text.replace(old, old + "\n" + add)


def todo_into_live(html):
    """線上卡裡的 todoLines 是推送時塞進去的整份 todo.js，所以補在它的結尾。"""
    return swap(html, TODO_PAIRS, "todo") if "function todoLines" in html else html


# ── 版子
def make(board, stats, review):
    nodes = {n["id"]: n for n in board["nodes"]}
    edges = board["edges"]
    if "bond-echo" in nodes:
        return
    eid = [0]

    def edge(s, t, h="right"):
        eid[0] += 1
        edges.append({"id": f"e-bond-{eid[0]}", "source": s, "target": t, "animated": True, "sourceHandle": h})

    def retarget(s, old_t, new_t):
        e = [e for e in edges if e["source"] == s and e["target"] == old_t]
        assert len(e) == 1, f"{s}→{old_t} 這條線不是剛好一條"
        e[0]["target"] = new_t

    def place(anchor, nid, data, dx=0, dy=180):
        a = nodes[anchor]
        n = {"id": nid, "type": "story", "data": data,
             "position": {"x": a["position"]["x"] + dx, "y": a["position"]["y"] + dy}}
        if a.get("parentId"):
            n["parentId"], n["extent"] = a["parentId"], "parent"
        board["nodes"].append(n); nodes[nid] = n
        stats["cards"] += 1
        return n

    def look(src, keep=("stage", "characterLayers", "background")):
        return {k: copy.deepcopy(v) for k, v in nodes[src]["data"].items() if k in keep}

    def dlg(src, lines, title):
        sp = next((s for s, _ in lines if s != "旁白"), "旁白")
        first = next((t for s, t in lines if s == sp), lines[0][1])
        d = {"type": "dialogue", "title": title, "speaker": sp, "text": first,
             "dialogueLines": [{"id": f"l{i}", "text": t, "emotion": "描述動作" if s == "旁白" else "", "speaker": s}
                               for i, (s, t) in enumerate(lines)]}
        d.update(look(src))
        return d

    def choice(text, opts, title):
        return {"type": "choice", "text": text, "title": title, "choices": opts,
                "choiceMode": "branch", "choiceConditions": [None] * len(opts)}

    # 一、生活
    for d, nid in NARR.items():
        t = nodes[nid]["data"]["text"]
        if LIFE[d] not in t:
            nodes[nid]["data"]["text"] = t + "\n" + LIFE[d]
            stats["narr"] += 1
            review.append(("一、桌前", f"第{cn(d)}天", nid, [("旁白", t)], [("旁白", LIFE[d])], NOTE.get(d)))
    for d, (scene, note) in NEWNARR.items():
        nid = f"bond-life-{d}"
        place(note, nid, {"type": "dialogue", "title": LIFE[d][:14], "speaker": "旁白", "text": LIFE[d]}, dx=-200, dy=-160)
        retarget(scene, note, nid); edge(nid, note)
        review.append(("一、桌前", f"第{cn(d)}天", nid, [], [("旁白", LIFE[d])], note))

    # 二、每晚一題
    for d, note in NOTE.items():
        q, s = f"bond-ask-{d}", f"bond-ask-{d}-set"
        place(note, q, choice("筆還沒蓋上。\n" + ASK[d], ["寫一句", "先不寫"], f"桌前一題：第{cn(d)}天"))
        place(note, s, {"type": "setVariable", "title": "（翻開空白頁）",
                        "variableOps": [{"id": "op-free_prompt", "kind": "set", "value": f"第{cn(d)}天｜{ASK[d]}", "variable": "free_prompt"}]}, dy=360)
        edge(note, q); edge(q, s, "choice-0"); edge(s, "inv-notes")
        review.append(("二、每晚一題", f"第{cn(d)}天", q, [("玩家（筆記）", nodes[note]["data"]["text"])],
                       [("選項", "筆還沒蓋上。\n" + ASK[d] + "\n→ 寫一句（翻開守則本空白頁，頁首是這一題）／先不寫")], None))

    # 結局唸回來
    a, b, text = ECHO
    place(a, "bond-echo", {"type": "dialogue", "title": "她自己寫的那幾頁", "speaker": "旁白", "text": text}, dy=180)
    retarget(a, b, "bond-echo"); edge("bond-echo", b)
    review.append(("二、每晚一題", "結局（第一頁名單之後、第七行之前）", "bond-echo",
                   [("玩家（筆記）", nodes[a]["data"]["text"])], [("旁白", text.replace("{{free_echo}}", "〔第一天她寫：「…」／第十二天她寫：「…」；沒寫過的人唸：那幾頁是空的。她一行都沒有寫。〕"))],
                   b))

    # 三、手機
    place("inv-643", "bond-phone", {"type": "dialogue", "title": "手機亮了一下", "speaker": "旁白", "text": PHONE_NARR})
    place("inv-643", "bond-phone-q", choice("", ["看一下", "等一下再看"], "第二天：手機"), dy=360)
    edge("inv-643", "bond-phone"); edge("bond-phone", "bond-phone-q"); edge("bond-phone-q", "inv-phone", "choice-0")
    review.append(("三、手機", "第三天早上（第二天的收尾，桌前筆記之後）", "bond-phone", [("玩家（筆記）", nodes["inv-643"]["data"]["text"])],
                   [("旁白", PHONE_NARR), ("選項", "看一下（直接打開手機）／等一下再看")], None))

    # 四、回法
    for k, (anc, nxt, prompt, opts) in enumerate(REPLY, 1):
        q = f"bond-reply-{k}"
        place(anc, q, choice(prompt, [o for o, _ in opts], f"回法：{prompt}"), dy=200)
        retarget(anc, nxt, q)
        added = [("選項", prompt + "\n→ " + "／".join(o for o, _ in opts))]
        for i, (o, lines) in enumerate(opts):
            nid = f"{q}-{i}"
            place(anc, nid, dlg(anc, lines, f"回法：{o}"), dx=200 * i, dy=380)
            edge(q, nid, f"choice-{i}"); edge(nid, nxt)
            added += [("　選「" + o + "」", "")] + lines
        stats["reply"] += 1
        ad = nodes[anc]["data"]
        tail = (ad.get("dialogueLines") or [ad])[-3:]
        review.append(("四、回法", ad.get("title", "")[:20], q, [(l.get("speaker", ""), l["text"]) for l in tail], added, nxt))

    # 卡片程式與變數宣告
    for nid in ("inv-notes",):
        d = nodes[nid]["data"]
        d["miniGameHtml"] = todo_into_live(swap(d["miniGameHtml"], NOTES_PAIRS, "notes"))
        for v in ("free_prompt",):
            if v not in d["miniGameReadVars"]: d["miniGameReadVars"].append(v)
        for v in ("free_prompt", "free_count", "free_echo"):
            if v not in d["miniGameWriteVars"]: d["miniGameWriteVars"].append(v)
    d = nodes["inv-001"]["data"]
    d["miniGameHtml"] = css(swap(todo_into_live(d["miniGameHtml"]), BOARD_PAIRS, "board"))
    for v in ("phone_day_seen", "free_count"):
        if v not in d["miniGameReadVars"]: d["miniGameReadVars"].append(v)
    stats["edges"] = eid[0]


# 回法的配音（2026-10-01 補）：玩家與斑比本機克隆、諾亞與店員 Larch（去括號生）。
# 玩家那句「謝謝。」板上本來就有同一句的音檔，直接借（BORROW）。
CDN = "https://cdn.jsdelivr.net/gh/yazelin/glitch-vn@main/docs/voice/"
VOICE = {("bond-reply-1-0", 0): "v-e3bff5566b8b0570", ("bond-reply-1-0", 1): "v-a9020434c82df8bd",
         ("bond-reply-2-0", 0): "v-e3bf29418e1f6f50", ("bond-reply-2-0", 1): "v-af5b7ce7356b7878",
         ("bond-reply-2-1", 1): "v-5605453cb01b225d",
         ("bond-reply-3-0", 0): "v-c886fe2de1a5c33d", ("bond-reply-3-0", 1): "v-abf8ee5e91456d2a",
         ("bond-reply-3-1", 0): "v-69b9697ad8387a6e", ("bond-reply-3-1", 1): "v-223f5e5054895122"}
BORROW = {("bond-reply-2-1", 0): ("玩家", "謝謝。")}


def voice(board):
    """掛音檔；做過就跳過。回傳掛了幾句。"""
    nodes = {n["id"]: n for n in board["nodes"]}
    have = {}
    for n in board["nodes"]:
        for l in n["data"].get("dialogueLines") or []:
            if l.get("voiceUrl"):
                have.setdefault((l.get("speaker"), l["text"]), l["voiceUrl"])
    want = {k: CDN + v + ".mp3" for k, v in VOICE.items()}
    for k, sp_tx in BORROW.items():
        assert sp_tx in have, f"板上找不到可以借的 {sp_tx}"
        want[k] = have[sp_tx]
    n = 0
    for (cid, i), url in want.items():
        l = nodes[cid]["data"]["dialogueLines"][i]
        if l.get("voiceUrl") != url:
            l["voiceUrl"] = url
            n += 1
    return n


def local_files():
    """本機三個卡片檔同步（不連線）。"""
    C = HERE.parent / "cards"
    for name, fn in (("notes.html", lambda t: swap(t, NOTES_PAIRS, "notes")),
                     ("todo.js", lambda t: swap(t, TODO_PAIRS, "todo")),
                     ("board.html", lambda t: css(swap(t, BOARD_PAIRS, "board")))):
        p = C / name
        t = p.read_text(encoding="utf-8")
        new = fn(t)
        if new != t:
            p.write_text(new, encoding="utf-8")
            print(f"本機 {name} 已改")


def write_review(review, path):
    out = ["# 《調查篇》主角連結：改動對照稿（2026-10-01）", "",
           "灰色是線上原本就有的前後文，**新**標的是這次加的。新台詞都還沒配音。", ""]
    sec = None
    for s, where, nid, before, added, nxt in review:
        if s != sec:
            out += ["", f"## {s}", ""]; sec = s
        out.append(f"### {where}（`{nid}`）")
        for sp, t in before:
            out.append("> " + (f"{sp}：" if sp else "") + t.replace("\n", "\n> "))
        if before:
            out.append(">")
        for sp, t in added:
            out.append(f"> **新** {sp}" + (f"：{t}" if t else "").replace("\n", "\n> "))
        if nxt:
            out.append(f">\n> （接回原本的 `{nxt}`）")
        out.append("")
    pathlib.Path(path).write_text("\n".join(out), encoding="utf-8")
    print("對照稿寫到", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--review")
    ap.add_argument("--snapshot")
    a = ap.parse_args()
    payload, etag = (json.loads(pathlib.Path(a.snapshot).read_text(encoding="utf-8")), None) if a.snapshot else request(f"/boards/{BID}")
    board = payload.get("board", payload)
    before = (len(board["nodes"]), len(board["edges"]))
    stats = {"cards": 0, "narr": 0, "reply": 0, "edges": 0}
    review = []
    make(board, stats, review)
    stats["voice"] = voice(board)
    print(f"掛音檔 {stats['voice']} 句")
    print(f"新卡 {stats['cards']}、新線 {stats['edges']}、桌前旁白接上 {stats['narr']}、回法 {stats['reply']}（原本卡 {before[0]}、邊 {before[1]}）")
    if a.review:
        write_review(review, a.review)
    if a.dry or a.review or a.snapshot:
        return
    local_files()
    if not stats["cards"] and not stats["voice"]:
        return
    want = (len(board["nodes"]), len(board["edges"]))
    bk = HERE / "backups" / f"board-main-{datetime.datetime.now():%Y%m%d-%H%M}-before-bond.json"
    bk.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    for attempt in range(5):
        try:
            request(f"/boards/{BID}", "PUT", {"name": board.get("name", BID), "kind": board.get("kind", "story"),
                    "mode": board.get("mode", "story"), "nodes": board["nodes"], "edges": board["edges"],
                    "summary": "add_bond.py：主角連結（桌前生活、每晚一題、手機、回法）"}, etag)
            break
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 4:
                raise
            payload, etag = request(f"/boards/{BID}"); board = payload.get("board", payload)
            make(board, {k: 0 for k in stats}, []); voice(board)
    back, _ = request(f"/boards/{BID}"); back = back.get("board", back)
    got = (len(back["nodes"]), len(back["edges"]))
    print(f"  回讀：卡 {got[0]}（預期 {want[0]}）　邊 {got[1]}（預期 {want[1]}）", "一致" if got == want else "★ 不一致")
    assert got == want
    proj, etag = request("")
    proj = proj.get("project", proj)
    have = {v["name"] for v in proj["variables"]}
    add = [v for v in VARS if v["name"] not in have]
    if add:
        proj["variables"] += add
        request("", "PUT", {"project": proj}, etag)
        print("  變數補上：", ", ".join(v["name"] for v in add))


if __name__ == "__main__":
    main()
