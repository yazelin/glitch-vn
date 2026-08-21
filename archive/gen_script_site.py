#!/usr/bin/env python3
"""生 docs/script.html —— 一路讀完的完整劇本。

docs/script.txt 是同一份東西的純文字版（給 diff、給模型審）。這一支是給人讀的：
說話的人靠顏色分、分支靠左側的線分層、變數那些機器零件預設收起來。

配色與字體沿用 gen_site.py 那一套（從遊戲美術取的），不另外配一套。
走圖的邏輯在 script_walk.py，跟 export_script.py 共用。
"""
import html, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from script_walk import DAYS, board_events
from _icons import ICONS

VARPAT = __import__("re").compile(r"\{\{([^}]+)\}\}")


def E(t):
    """跳脫之後，把 {{變數}} 變成看得出來是佔位的樣子——混在句子裡讀起來像錯字。"""
    return VARPAT.sub(lambda m: f"<var>{m.group(1)}</var>", html.escape(str(t)))
LINKS = [
    ("gh",   "https://github.com/yazelin/glitch-vn", "原始碼"),
    ("fb",   "https://www.facebook.com/yaze.lin.gm", "Facebook"),
    ("bmc",  "https://buymeacoffee.com/yazelin",     "請亞澤喝咖啡"),
    ("blog", "https://yazelin.github.io/",           "亞澤的部落格"),
]

CSS = """
:root{
  /* 從遊戲美術取的色，跟 manual.html 同一套。黑洞先生 #14142a、格莉奇 #c8c8f0 */
  --ground:#eceaf4; --surface:#ffffff; --sunk:#e2dfee;
  --line:#cdc9de; --text:#20203a; --muted:#5c5878; --faint:#8b87a3;
  --glitch:#4a4aa8; --hole:#3f4a6b; --lamp:#8f5a1f; --rail:#c3bfd8;
  --r:3px;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --ground:#101024; --surface:#191932; --sunk:#0b0b1c;
  --line:#2e2e50; --text:#dedbec; --muted:#9a96b8; --faint:#75718f;
  --glitch:#a8a8e8; --hole:#8794b8; --lamp:#d9a05b; --rail:#33335a;
}}
:root[data-theme="dark"]{
  --ground:#101024; --surface:#191932; --sunk:#0b0b1c;
  --line:#2e2e50; --text:#dedbec; --muted:#9a96b8; --faint:#75718f;
  --glitch:#a8a8e8; --hole:#8794b8; --lamp:#d9a05b; --rail:#33335a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--text);
  font-family:"Noto Sans TC",system-ui,sans-serif;font-size:16.5px;line-height:1.85;
  -webkit-text-size-adjust:100%}
.wrap{max-width:820px;margin:0 auto;padding:0 22px 90px}

header.top{padding:60px 0 26px;border-bottom:1px solid var(--line)}
header.top h1{font-family:"Noto Serif TC",serif;font-weight:600;
  font-size:clamp(28px,5vw,40px);line-height:1.25;margin:0 0 12px;text-wrap:balance}
header.top p{margin:0;color:var(--muted);max-width:34em}
.meta{margin-top:18px;font-family:"DM Mono",ui-monospace,monospace;
  font-size:12.5px;color:var(--faint);letter-spacing:.02em}

nav.days{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:6px;
  padding:10px 0;background:var(--ground);border-bottom:1px solid var(--line)}
nav.days a{font-family:"DM Mono",ui-monospace,monospace;font-size:12.5px;
  text-decoration:none;color:var(--muted);border:1px solid var(--line);
  border-radius:var(--r);padding:4px 9px;background:var(--surface)}
nav.days a:hover{color:var(--glitch);border-color:var(--glitch)}
nav.days .sw{margin-left:auto;display:flex;align-items:center;gap:7px;
  font-family:"DM Mono",ui-monospace,monospace;font-size:12px;color:var(--faint)}
nav.days .sw input{accent-color:var(--glitch)}

section.day{padding-top:44px}
.dh{border-left:3px solid var(--glitch);padding-left:14px;margin-bottom:8px}
.dh .n{font-family:"DM Mono",ui-monospace,monospace;font-size:12px;
  color:var(--glitch);letter-spacing:.14em}
.dh h2{font-family:"Noto Serif TC",serif;font-weight:600;font-size:25px;
  margin:2px 0 4px;text-wrap:balance}
.dh p{margin:0;color:var(--muted);font-size:14.5px}

.scene{margin:34px 0 20px;padding:11px 0 11px 14px;background:var(--sunk);
  border-left:3px solid var(--lamp);border-radius:0 var(--r) var(--r) 0}
.scene b{display:block;font-family:"Noto Serif TC",serif;font-size:15.5px}
.scene span{color:var(--muted);font-size:14.5px}

/* 一行台詞＝名字欄＋內容欄，名字對齊才掃得動 */
.ln{display:grid;grid-template-columns:5.4em 1fr;gap:0 12px;margin:3px 0}
.ln .who{font-family:"DM Mono",ui-monospace,monospace;font-size:12.5px;
  text-align:right;padding-top:5px;color:var(--faint);white-space:nowrap}
.ln.g .who{color:var(--glitch)} .ln.h .who{color:var(--hole)}
.ln .tx{white-space:pre-wrap}
.ln.n .tx{color:var(--muted)}
.ln.g .tx{color:var(--text)}
.ln.h .tx{color:var(--text);font-weight:500}

.chat{margin:8px 0 8px calc(5.4em + 12px);display:flex;flex-direction:column;
  gap:4px;align-items:flex-start}
.chat i{font-style:normal;font-size:13.5px;color:var(--lamp);background:var(--sunk);
  border-radius:11px;padding:3px 11px;line-height:1.55}

.q{margin:16px 0 6px calc(5.4em + 12px);font-family:"Noto Serif TC",serif;
  font-size:15.5px;border-top:1px solid var(--line);padding-top:12px}
.q em{font-style:normal;font-family:"DM Mono",ui-monospace,monospace;
  font-size:11.5px;color:var(--faint);letter-spacing:.1em;display:block}

.br{margin:12px 0 4px;font-size:14px;color:var(--muted)}
.br b{color:var(--text);font-weight:500}
.br code{font-family:"DM Mono",ui-monospace,monospace;font-size:12px;
  color:var(--faint);background:var(--sunk);border-radius:var(--r);padding:1px 5px}
/* 同一個選項底下的有條件路線。它排在主線前面（因為引擎先判它），
   可是讀的人會以為那是主線，所以壓暗、明講「例外」。 */
.br.alt{opacity:.72;font-size:13.5px}
.br.alt b{font-weight:400}
.br.alt .tag{font-family:"DM Mono",ui-monospace,monospace;font-size:11px;
  letter-spacing:.08em;color:var(--lamp);border:1px solid var(--lamp);
  border-radius:var(--r);padding:0 5px;margin-right:6px}
var{font-style:normal;font-family:"DM Mono",ui-monospace,monospace;font-size:.86em;
  color:var(--glitch);background:var(--sunk);border-radius:var(--r);padding:0 4px}
.kids{border-left:1px solid var(--rail);padding-left:16px;margin-left:2px}

.vars{font-family:"DM Mono",ui-monospace,monospace;font-size:11.5px;
  color:var(--faint);margin:3px 0 3px calc(5.4em + 12px)}
body.novars .vars{display:none}
/* 整段只有變數操作、沒有半句台詞的分支（記憶格那四個閘門就是）。
   關掉變數的時候它們是四行空標題，對讀的人是純雜訊。 */
body.novars .machine{display:none}
.loop,.jump{font-family:"DM Mono",ui-monospace,monospace;font-size:12.5px;
  color:var(--faint);margin:8px 0 8px calc(5.4em + 12px)}
.jump{color:var(--glitch)}

footer{margin-top:70px;padding-top:22px;border-top:1px solid var(--line);
  color:var(--faint);font-size:13.5px}
footer a{color:var(--muted)}
.promo{display:flex;gap:12px;margin-top:14px}
.promo a{display:inline-flex;color:var(--muted)}
.promo a:hover{color:var(--glitch)}
.promo svg{width:20px;height:20px}
@media (max-width:600px){
  body{font-size:16px}
  .ln{grid-template-columns:1fr;gap:0}
  .ln .who{text-align:left;padding-top:6px}
  .chat,.q,.vars,.loop,.jump{margin-left:0}
  .kids{padding-left:11px}
}
"""


def speaker_class(who):
    return {"格莉奇": "g", "黑洞先生": "h", "留言區": "c"}.get(who or "", "n")


def render(events):
    """事件流是扁的（每個事件帶 depth），HTML 要巢狀。用一個 depth 堆疊還原。

    另外標記「整段沒有半句台詞」的分支：那種是機器零件（記憶格閘門之類），
    關掉變數的時候要一起收起來，不然會留下一排空的標題。
    """
    out, depth, frames = [], 0, []

    def say_something():
        if frames:
            frames[-1][1] += 1

    for e in events:
        d = e["depth"]
        while d > depth:
            frames.append([len(out), 0])
            out.append('<div class="kids">'); depth += 1
        while d < depth:
            start, visible = frames.pop()
            out.append("</div>"); depth -= 1
            if visible:
                say_something()
            else:
                out[start] = '<div class="kids machine">'
                # 前面那個分支標題也一起標起來
                for i in range(start - 1, -1, -1):
                    if out[i].startswith('<div class="br'):
                        out[i] = out[i].replace('<div class="br', '<div class="br machine', 1)
                        break
        k = e["kind"]
        if k not in ("vars", "branch"):
            say_something()
        if k == "scene":
            out.append(f'<div class="scene"><b>{E(e["title"])}</b>'
                       f'<span>{E(e["text"])}</span></div>')
        elif k == "say":
            who = e["who"]
            if who == "留言區":
                out.append('<div class="chat">'
                           + "".join(f"<i>{E(l)}</i>" for l in e["lines"]) + "</div>")
            else:
                cls = speaker_class(who)
                nm = E(who) if who and who != "旁白" else ""
                out.append(f'<div class="ln {cls}"><div class="who">{nm}</div>'
                           f'<div class="tx">{E(chr(10).join(e["lines"]))}</div></div>')
        elif k == "choice":
            out.append(f'<div class="q"><em>玩家選擇</em>{E(e["text"])}</div>')
        elif k == "input":
            out.append(f'<div class="q"><em>玩家打字 → {E(e["var"] or "")}</em>'
                       f'{E(e["text"])}</div>')
        elif k == "branch":
            cond = f' <code>{E(e["cond"])}</code>' if e["cond"] else ""
            alt = " alt" if e["cond"] and e["label"] is not None else ""
            tag = '<span class="tag">例外</span>' if alt else ""
            if e["label"] is not None:
                out.append(f'<div class="br{alt}">{tag}◆ 選<b>「{E(e["label"])}」</b>'
                           + (f'，而且{cond}' if e["cond"] else "") + "</div>")
            else:
                out.append(f'<div class="br">◆ {"這個狀態" if e["cond"] else "其他情況"}'
                           f'{cond}</div>')
        elif k == "vars":
            t = E(e["text"]) if e["text"] else ""
            ops = f'〔{E(e["ops"])}〕' if e["ops"] else ""
            if e["text"]:
                out.append(f'<div class="ln n"><div class="who"></div>'
                           f'<div class="tx">{t}</div></div>')
            if ops:
                out.append(f'<div class="vars">{ops}</div>')
        elif k == "loop":
            out.append(f'<div class="loop">↩︎ 回到前面的「{E(e["text"])}」</div>')
        elif k == "jump":
            out.append(f'<div class="jump">→ 接到 {E(e["to"])}</div>')
    while depth:
        start, visible = frames.pop()
        out.append("</div>"); depth -= 1
        if not visible:
            out[start] = '<div class="kids machine">'
            for i in range(start - 1, -1, -1):
                if out[i].startswith('<div class="br'):
                    out[i] = out[i].replace('<div class="br', '<div class="br machine', 1)
                    break
    return "".join(out)


nav, body, cards, edges = [], [], 0, 0
for b in DAYS:
    num = int(b["id"].split("day")[-1])
    name = b["name"].split("：")[-1]
    cards += len(b["nodes"]); edges += len(b["edges"])
    nav.append(f'<a href="#d{num}">{num}・{E(name)}</a>')
    body.append(f'''<section class="day" id="d{num}">
<div class="dh"><div class="n">DAY {num}</div><h2>{E(name)}</h2>
<p>{E(b.get("description",""))}</p></div>
{render(board_events(b))}</section>''')

promo = ('<div class="promo">' + "".join(
    f'<a href="{u}" target="_blank" rel="noopener" aria-label="{t}" title="{t}">{ICONS[k]}</a>'
    for k, u, t in LINKS) + "</div>")

HTML = f'''<title>格莉奇與黑洞先生・完整劇本</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500&family=Noto+Serif+TC:wght@500;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
<h1>格莉奇與黑洞先生<br>完整劇本</h1>
<p>七天，一路讀完。分支用左邊那條線分層——那些是岔開的路，玩家一次只走一條，
所以底下同一層的幾條你不會在同一場遊戲裡全部看到。</p>
<div class="meta">{len(DAYS)} 天 · {cards} 張卡 · {edges} 條連線 · 這一頁是程式從遊戲檔案生的</div>
</header>
<nav class="days">{"".join(nav)}
<label class="sw"><input type="checkbox" id="vt"> 顯示變數</label></nav>
{"".join(body)}
<footer>
<p>由 <code>tools/gen_script_site.py</code> 從 Larch 專案生成，不是手寫的。
純文字版在 <a href="script.txt">script.txt</a>，
機制表在 <a href="mechanics.md">mechanics.md</a>，
使用說明在 <a href="manual.html">manual.html</a>。</p>
<p>《格莉奇與黑洞先生》　MIT　林亞澤</p>
{promo}
</footer>
</div>
<script>
// 變數是機器零件，不是故事。預設收起來，想看再打開。
const cb = document.getElementById("vt");
document.body.classList.add("novars");
cb.addEventListener("change", () => document.body.classList.toggle("novars", !cb.checked));
</script>
'''

out = pathlib.Path.home() / "glitch-vn/docs/script.html"
out.write_text(HTML, encoding="utf-8")
print(f"寫好 {out}（{len(HTML) // 1024} KB，{len(DAYS)} 天、{cards} 張卡）")

APPLY = pathlib.Path.home() / ".claude/skills/promo-footer/apply.py"
if APPLY.exists():
    r = subprocess.run([sys.executable, str(APPLY), str(out), "glitch-vn"],
                       capture_output=True, text=True)
    print("  推廣 footer:", r.stdout.strip() or r.stderr.strip())
