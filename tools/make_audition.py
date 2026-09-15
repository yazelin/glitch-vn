#!/usr/bin/env python3
"""產生試聽對照頁：一句台詞一列，可以直接播，並且說明它是怎麼來的。

**不上線。** 產出的是本機開得起來的單一 HTML，音檔走相對路徑指到 docs/voice。

每一列回答四個問題：
    這句話是誰講的、聽起來是什麼樣子（inline audio）、
    是哪一條線配的（本機 CosyVoice3 還是 Larch 的哪一支音色）、
    有沒有經過讀音替身（原文與實際唸出去的字）。

沒配音的也列出來，並且寫明原因——**原因寫成人看得懂的句子**，
因為看這一頁的人要判斷的是「這樣對不對」，不是「程式怎麼分類」。

    python3 tools/make_audition.py            # 寫出 試聽對照.html
"""
import argparse, html, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "試聽對照.html"


def rows():
    import voice as V
    from voice import LARCH_VOICE as LV
    labels = json.loads((ROOT / "art/voice/larch-labels.json").read_text(encoding="utf-8"))
    SPOKEN = json.loads((ROOT / "art/voice/spoken.json").read_text(encoding="utf-8"))
    urls = json.loads((ROOT / "art/voice/urls.json").read_text(encoding="utf-8"))
    sil = {}
    sp = ROOT / "art/voice/silence.json"
    if sp.exists():
        sil = json.loads(sp.read_text(encoding="utf-8"))
    # 瑕疵掃描（~/vn-bgm/scan_defects.py --speech --phase-check）標到的
    fl = ROOT / "art/voice/flagged.json"
    flagged = set(json.loads(fl.read_text(encoding="utf-8"))) if fl.exists() else set()
    # 店員那幾句的 A/B：同一句的原文版與替身版並排，給人耳判
    # 逐列的引擎來歷。**從產生那個檔的路徑判定，不從角色反推**——
    # 保全與店員中途換過音色，有些句子走逐句有些走長檔，角色層看不見這種例外。
    SRC = {}
    srcp = ROOT / "art/voice/source.json"
    if srcp.exists():
        SRC = json.loads(srcp.read_text(encoding="utf-8"))
    ab = {}
    abp = ROOT / "art/voice/ab/meta.json"
    if abp.exists():
        for x in json.loads(abp.read_text(encoding="utf-8")):
            ab.setdefault(x["key"], {})[x["tag"]] = x["file"]
    # 建議先聽（tools/listen_list.py）：把 1900 句收到幾十句
    LIS = {}
    lp = ROOT / "art/voice/listen.json"
    if lp.exists():
        LIS = json.loads(lp.read_text(encoding="utf-8"))
    board = json.loads((ROOT / "larch/inv/out/board.json").read_text(encoding="utf-8"))

    items = []
    for n in board["nodes"]:
        d = n["data"]
        dl = d.get("dialogueLines") or []
        if dl:
            for l in dl:
                items.append((l.get("speaker"), l.get("text"), l.get("emotion"), d.get("type")))
        elif d.get("text"):
            items.append((d.get("speaker"), d.get("speakText") or d.get("text"),
                          d.get("emotion"), d.get("type")))
    for t in (board.get("tapes") or []):
        items.append((t["who"], t["quote"], None, "tape"))

    voiced, silent, seen = [], [], set()
    for sp_, tx, emo, typ in items:
        tx = (tx or "").strip()
        if not tx:
            continue
        # ── 沒配音的三類。原因寫給人看，不是寫分類代號。
        if not sp_:
            silent.append((typ or "", tx, "這張卡沒有講者——選項卡與小遊戲卡的字是介面文字，不是台詞。"))
            continue
        if (emo or "") == "描述動作":
            why = ("錄音機的動作聲，不是誰在講話。" if "錄音機" in tx
                   else "舞台指示：描述動作的旁白，設計上就不配音（斜體那幾行）。")
            silent.append((sp_, tx, why))
            continue
        if not tx.strip("…．. 　"):
            silent.append((sp_, tx, "整句只有刪節號，沒有字可以唸——那是沉默本身。"))
            continue
        k = V.key(sp_, tx, emo or None)
        if k in seen:
            continue
        seen.add(k)
        said = V.to_speech(tx)
        if sp_ in LV:
            vid, lab = labels[sp_]
            line, voice = "Larch", lab
            # **替身有沒有套，看 spoken.json 記的是哪一種字**（見那兩支工具的註解）：
            #   長檔（larch_take.py）記 to_speech 的輸出 → 套了
            #   逐句（gen_larch_voice.py）記板上的字 → 沒套，平台照板上的字唸
            rec = SPOKEN.get(k)
            if said == tx:
                sub = None
            elif rec == said:
                sub = ("有套（長檔）", tx, said)
            elif rec == tx:
                sub = ("★ 該套而沒套（逐句）", tx, said)
            else:
                sub = ("？沒有紀錄", tx, said)
        else:
            line, voice = "本機", "CosyVoice3 克隆"
            sub = ("有套", tx, said) if said != tx else None
        voiced.append({
            "who": sp_, "text": tx, "emo": emo or "", "key": k,
            "line": line, "voice": voice,
            # **要看實體檔案，不能看 urls.json。** 那份是發佈時寫的，
            # 中間重生過就會脫節——2026-09-14 有 157 列指向不存在的檔，
            # 在頁面上的長相是「點了沒聲音」，跟「這句配音壞掉」一模一樣。
            "has": (ROOT / "docs/voice" / f"{k}.mp3").exists(),
            "sub": sub,
            "sil": sil.get(k, {}).get("silence"),
            "dur": sil.get(k, {}).get("dur"),
            "flag": k in flagged,
            "src": SRC.get(k, {"line": "不確定", "why": "沒有來歷紀錄（在來歷表建立之前生的）"}),
            "ab": ab.get(k),
            "pick": LIS.get(k),
        })
    return voiced, silent


CSS = """
/* 淺色是完整的一套；深色**每一個變數都要重新給**。
   2026-09-14 踩到：只換了 --bg 與 --ink，卡片底色還是白的，
   而且 --bg 寫成 #17151300（尾巴那兩位是 alpha=00，全透明），
   深色模式下就是白底配近白字，整頁看不見。 */
:root{
  --bg:#faf8f5; --ink:#221f1c; --dim:#6b645c; --line:#e0d9d0;
  --card:#fff; --row:#f4f1ec; --warn:#8a4b1f; --larch:#2f5d50; --pick:#9b2226;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#171513; --ink:#eae5de; --dim:#9a9188; --line:#33302c;
    --card:#211e1b; --row:#211e1b; --warn:#e0a06a; --larch:#7fbfa8; --pick:#f08a8a;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Noto Sans TC","PingFang TC",system-ui,sans-serif}
header{padding:20px 18px 12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
h1{margin:0 0 6px;font-size:19px;letter-spacing:.02em}
.sum{color:var(--dim);font-size:13px}
.bar{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;align-items:center}
button.f{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:4px 10px;border-radius:999px;cursor:pointer;font-size:13px}
button.f.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
input[type=search]{flex:1;min-width:180px;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);font-size:13px}
main{padding:14px 18px 60px;max-width:1180px}
.grp{margin:26px 0 10px;font-size:15px;font-weight:600;border-left:3px solid var(--ink);padding-left:8px}
.grp small{font-weight:400;color:var(--dim)}
/* **要 fixed。** auto 版面下長台詞會把台詞欄撐到滿版，
   最右邊的替身欄被壓成一個字寬的直條（2026-09-15 踩到）。 */
table{width:100%;border-collapse:collapse;table-layout:fixed}
td{border-bottom:1px solid var(--line);padding:8px 6px;vertical-align:top}
td:nth-child(2){width:18%}td:nth-child(3){width:16%}td:nth-child(4){width:8%}
td.t{width:34%;word-break:break-word}
.emo{color:var(--dim);font-size:12px}
audio{height:32px;width:210px}
.tag{display:inline-block;font-size:12px;padding:1px 7px;border-radius:4px;border:1px solid var(--line)}
.tag.larch{color:var(--larch);border-color:var(--larch)}
.sil{font-variant-numeric:tabular-nums;font-size:13px;white-space:nowrap}
.sil.hi{color:var(--warn);font-weight:600}
.sub{font-size:12px;color:var(--dim);width:24%;word-break:break-word}
.sub b{color:var(--warn);font-weight:600}
.none{color:var(--dim)}
tr.quiet td{background:var(--row)}
.flagbox{margin-top:6px;padding:6px 8px;border-left:3px solid var(--warn);background:var(--row);font-size:12px;color:var(--dim);max-width:420px}
.flagbox b{color:var(--warn)}
.abbox{margin-top:6px;padding:6px 8px;border-left:3px solid var(--larch);background:var(--row);font-size:12px;color:var(--dim);max-width:460px}
.abbox b{color:var(--larch)}
.abbox audio{height:28px;width:180px;vertical-align:middle}
.eng{font-size:12px;color:var(--dim);border-left:3px solid var(--line);padding-left:6px}
.eng.larch{color:var(--larch);border-color:var(--larch)}
.pickbox{margin-top:6px;padding:6px 8px;border-left:3px solid var(--pick);background:var(--row);font-size:12px;color:var(--dim);max-width:460px}
.pickbox b{color:var(--pick)}
tr.pick td.t{box-shadow:inset 3px 0 0 var(--pick)}
button.f.pickf{color:var(--pick);border-color:var(--pick)}
.eng.unk{color:var(--warn);border-color:var(--warn);font-weight:600}
"""

JS = """
const rows=[...document.querySelectorAll('tr[data-who]')];
const grps=[...document.querySelectorAll('.grp')];
let who='', q='', pick=false;
function apply(){
  rows.forEach(r=>{
    const okW = !who || r.dataset.who===who;
    const okQ = !q || r.dataset.s.includes(q);
    const okP = !pick || r.dataset.pick==='1';
    r.style.display = (okW&&okQ&&okP) ? '' : 'none';
  });
  grps.forEach(g=>{
    const tb=g.nextElementSibling;
    const any=[...tb.querySelectorAll('tr')].some(r=>r.style.display!=='none');
    g.style.display=any?'':'none'; tb.style.display=any?'':'none';
  });
}
document.querySelectorAll('button.f').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('button.f').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); who=b.dataset.w||''; pick=b.dataset.pick==='1'; apply();
});
document.querySelector('input[type=search]').oninput=e=>{q=e.target.value.trim();apply();};
"""


def build():
    voiced, silent = rows()
    import collections
    by = collections.OrderedDict()
    for r in sorted(voiced, key=lambda x: (x["line"] != "Larch", x["who"])):
        by.setdefault(r["who"], []).append(r)
    e = html.escape
    n_sub = sum(1 for r in voiced if r["sub"] and r["sub"][0] == "有套")
    n_gap = sum(1 for r in voiced if r["sub"] and r["sub"][0].startswith("★"))
    sils = [r["sil"] for r in voiced if r["sil"] is not None]
    p = []
    p.append(f"<!doctype html><meta charset=utf-8><title>調查篇配音對照</title><style>{CSS}</style>")
    p.append("<header><h1>《格莉奇與黑洞先生・調查篇》配音對照</h1>")
    n_flag = sum(1 for r in voiced if r.get("flag"))
    n_ab = sum(1 for r in voiced if r.get("ab"))
    p.append(f'<div class=sum>{len(voiced)} 句有配音（去重後）・{len(silent)} 句設計上不配音・'
             f'{n_sub} 句經過讀音替身・<b>{n_gap} 句該套而沒套</b>'
             + (f'・頭尾靜音平均 {sum(sils)/len(sils):.2f} 秒、最多 {max(sils):.2f} 秒' if sils else '')
             + f'・瑕疵掃描標到 {n_flag} 句・{n_ab} 句有 A/B 兩版'
             + '</div>'
             + '<div class=sum style="margin-top:6px">'
               '舞台指示（括號）<b>沒有被唸出去</b>：板上 88 句含括號，逐句比對'
               '「實際唸出去的文字」全部不含括號，驗不了的 0 句。<br>'
               '瑕疵掃描：2116 個檔，<b>6 句疑似</b>、39 句要看一眼、2071 句乾淨。'
               '<b>6 個紅燈全部通不過相位檢驗</b>，跟前一輪 4196 個檔的結論一致，'
               '很可能是切窗切出來的。那支工具對「音量正常但頻譜變成寬頻雜訊」有效，'
               '<b>對截斷、爆音、吞字無效</b>——所以零紅燈不等於全部正確。'
               '</div>')
    npick = sum(1 for r in voiced if r.get("pick"))
    p.append('<div class=bar><button class="f on" data-w="">全部</button>'
             f'<button class="f pickf" data-w="" data-pick="1">建議先聽<small> {npick}</small></button>')
    for w in by:
        p.append(f'<button class=f data-w="{e(w)}">{e(w)}<small> {len(by[w])}</small></button>')
    p.append('<button class=f data-w="＿沒配音">沒配音</button>')
    p.append('<input type=search placeholder="搜台詞…"></div></header><main>')

    for w, rs in by.items():
        line = rs[0]["line"]; voice = rs[0]["voice"]
        tag = f'<span class="tag larch">Larch・{e(voice)}</span>' if line == "Larch" else f'<span class=tag>本機・{e(voice)}</span>'
        p.append(f'<div class=grp>{e(w)} <small>{len(rs)} 句</small> {tag}</div><table>')
        for r in rs:
            sil = r["sil"]
            sc = "sil hi" if (sil or 0) >= 0.5 else "sil"
            siltxt = f'{sil:.2f} 秒' if sil is not None else '—'
            if r["sub"]:
                kind, raw, said = r["sub"]
                if kind.startswith("★"):
                    sub = (f'<b>{e(kind)}</b>　Larch 照板上的字唸<br>'
                           f'實際唸出去：{e(raw)}<br>替身表本來會改成：{e(said)}')
                else:
                    sub = f'{e(kind)}<br>板上：{e(raw)}<br>唸出去：{e(said)}'
            else:
                sub = '<span class=none>—</span>'
            src = f'docs/voice/{r["key"]}.mp3'
            au = (f'<audio controls preload=none src="{src}"></audio>' if r["has"]
                  else '<span class=none>沒有檔</span>')
            emo = f'<div class=emo>{e(r["emo"])}</div>' if r["emo"] else ''
            if r.get("flag"):
                emo += ('<div class=flagbox><b>瑕疵掃描標到這一句</b><br>'
                        '6 個紅燈<b>全部通不過相位檢驗</b>，很可能是切窗切出來的，'
                        '聽起來正常是預期內。聽到真的有雜訊才回報。</div>')
            if r.get("ab"):
                a1 = r["ab"].get("原文"); a2 = r["ab"].get("替身")
                emo += ('<div class=abbox><b>這一句有兩個版本，請並排聽</b><br>'
                        'ASR 說兩版同音／所以這條替身在 Larch 上可能沒作用／'
                        '請聽它們是不是聽起來也一樣。<br>'
                        + (f'原文版 <audio controls preload=none src="art/voice/ab/{a1}"></audio><br>' if a1 else '')
                        + (f'替身版 <audio controls preload=none src="art/voice/ab/{a2}"></audio>' if a2 else '')
                        + '</div>')
            pk = r.get("pick")
            if pk:
                emo += ('<div class=pickbox><b>建議先聽</b>　' + e(pk["why"])
                        + (f'<br>聽寫聽成：{e(pk["got"])}' if pk.get("got") else '')
                        + '</div>')
            s = (r["who"] + r["text"]).lower()
            src = r.get("src") or {}
            ln = src.get("line", "不確定")
            cls = "eng larch" if ln.startswith("Larch") else ("eng" if ln.startswith("本機") else "eng unk")
            engine = f'<div class="{cls}" title="{e(src.get("why",""))}">{e(ln)}</div>'
            p.append(f'<tr data-who="{e(w)}" data-s="{e(s)}"'
                     f'{" data-pick=1 class=pick" if pk else ""}>'
                     f'<td class=t>{e(r["text"])}{emo}</td>'
                     f'<td>{au}</td>{"<td>" + engine + "</td>"}'
                     f'<td class="{sc}">{siltxt}</td>'
                     f'<td class=sub>{sub}</td></tr>')
        p.append('</table>')

    p.append(f'<div class=grp>沒配音的 <small>{len(silent)} 句</small> '
             '<span class=tag>設計上就不該有聲音</span></div><table>')
    seen = set()
    for who, tx, why in silent:
        if (who, tx) in seen:
            continue
        seen.add((who, tx))
        p.append(f'<tr class=quiet data-who="＿沒配音" data-s="{e((who+tx).lower())}">'
                 f'<td class=t>{e(tx)}</td><td>{e(who)}</td><td></td><td></td>'
                 f'<td class=sub>{e(why)}</td></tr>')
    p.append(f'</table></main><script>{JS}</script>')
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"寫出 {OUT}")
    print(f"  有配音 {len(voiced)} 句、沒配音 {len(silent)} 句（去重前）")
    print(f"  經過替身 {n_sub} 句、該套而沒套 {n_gap} 句")
    print(f"  建議先聽 {sum(1 for r in voiced if r.get('pick'))} 句")
    if sils:
        print(f"  頭尾靜音：量到 {len(sils)} 句，平均 {sum(sils)/len(sils):.3f} 秒、最多 {max(sils):.3f} 秒")


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    build()
