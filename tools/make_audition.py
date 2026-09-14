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
    urls = json.loads((ROOT / "art/voice/urls.json").read_text(encoding="utf-8"))
    sil = {}
    sp = ROOT / "art/voice/silence.json"
    if sp.exists():
        sil = json.loads(sp.read_text(encoding="utf-8"))
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
            # **Larch 那條線沒有經過替身表**：平台是照板上的字唸的
            # （POST /voice/generate 給的是 nodeId，不是文字），
            # 所以 to_speech 在那條線上沒有施力點。
            # 沒套的時候要看得見「本來會被改成什麼」，不然兩欄一樣等於沒說話。
            sub = ("★ 該套而沒套", tx, said) if said != tx else None
        else:
            line, voice = "本機", "CosyVoice3 克隆"
            sub = ("有套", tx, said) if said != tx else None
        voiced.append({
            "who": sp_, "text": tx, "emo": emo or "", "key": k,
            "line": line, "voice": voice,
            "has": k in urls,
            "sub": sub,
            "sil": sil.get(k, {}).get("silence"),
            "dur": sil.get(k, {}).get("dur"),
        })
    return voiced, silent


CSS = """
:root{--bg:#faf8f5;--ink:#221f1c;--dim:#6b645c;--line:#e0d9d0;--card:#fff;--warn:#8a4b1f;--larch:#2f5d50}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Noto Sans TC","PingFang TC",system-ui,sans-serif}
header{padding:20px 18px 12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
h1{margin:0 0 6px;font-size:19px;letter-spacing:.02em}
.sum{color:var(--dim);font-size:13px}
.bar{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;align-items:center}
button.f{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:4px 10px;border-radius:999px;cursor:pointer;font-size:13px}
button.f.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
input[type=search]{flex:1;min-width:180px;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);font-size:13px}
main{padding:14px 18px 60px;max-width:1180px}
.grp{margin:26px 0 10px;font-size:15px;font-weight:600;border-left:3px solid var(--ink);padding-left:8px}
.grp small{font-weight:400;color:var(--dim)}
table{width:100%;border-collapse:collapse}
td{border-bottom:1px solid var(--line);padding:8px 6px;vertical-align:top}
td.t{min-width:260px}
.emo{color:var(--dim);font-size:12px}
audio{height:32px;width:210px}
.tag{display:inline-block;font-size:12px;padding:1px 7px;border-radius:4px;border:1px solid var(--line)}
.tag.larch{color:var(--larch);border-color:var(--larch)}
.sil{font-variant-numeric:tabular-nums;font-size:13px;white-space:nowrap}
.sil.hi{color:var(--warn);font-weight:600}
.sub{font-size:12px;color:var(--dim);max-width:230px}
.sub b{color:var(--warn);font-weight:600}
.none{color:var(--dim)}
tr.quiet td{background:#f4f1ec}
@media (prefers-color-scheme:dark){:root{--bg:#17151300;--ink:#eee}}
"""

JS = """
const rows=[...document.querySelectorAll('tr[data-who]')];
const grps=[...document.querySelectorAll('.grp')];
let who='', q='';
function apply(){
  rows.forEach(r=>{
    const okW = !who || r.dataset.who===who;
    const okQ = !q || r.dataset.s.includes(q);
    r.style.display = (okW&&okQ) ? '' : 'none';
  });
  grps.forEach(g=>{
    const tb=g.nextElementSibling;
    const any=[...tb.querySelectorAll('tr')].some(r=>r.style.display!=='none');
    g.style.display=any?'':'none'; tb.style.display=any?'':'none';
  });
}
document.querySelectorAll('button.f').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('button.f').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); who=b.dataset.w||''; apply();
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
    p.append(f'<div class=sum>{len(voiced)} 句有配音（去重後）・{len(silent)} 句設計上不配音・'
             f'{n_sub} 句經過讀音替身・<b>{n_gap} 句該套而沒套</b>'
             + (f'・頭尾靜音平均 {sum(sils)/len(sils):.2f} 秒、最多 {max(sils):.2f} 秒' if sils else '')
             + '</div>')
    p.append('<div class=bar><button class="f on" data-w="">全部</button>')
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
            s = (r["who"] + r["text"]).lower()
            p.append(f'<tr data-who="{e(w)}" data-s="{e(s)}">'
                     f'<td class=t>{e(r["text"])}{emo}</td>'
                     f'<td>{au}</td><td class="{sc}">{siltxt}</td>'
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
                 f'<td class=t>{e(tx)}</td><td>{e(who)}</td><td></td>'
                 f'<td class=sub>{e(why)}</td></tr>')
    p.append(f'</table></main><script>{JS}</script>')
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"寫出 {OUT}")
    print(f"  有配音 {len(voiced)} 句、沒配音 {len(silent)} 句（去重前）")
    print(f"  經過替身 {n_sub} 句、該套而沒套 {n_gap} 句")
    if sils:
        print(f"  頭尾靜音：量到 {len(sils)} 句，平均 {sum(sils)/len(sils):.3f} 秒、最多 {max(sils):.3f} 秒")


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    build()
