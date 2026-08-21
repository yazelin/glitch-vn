#!/usr/bin/env python3
"""把 novel/*.md 排成看得下去的閱讀頁 → docs/novel.html。

跟 gen_script_site.py 同一套配色與字體（從遊戲美術取的），不另外配一套。
這一頁是給讀者的，所以沒有變數、沒有分支、沒有機制，就是小說。
"""
import html, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _icons import ICONS

ROOT = pathlib.Path.home() / "glitch-vn"
E = html.escape
LINKS = [
    ("gh",   "https://github.com/yazelin/glitch-vn", "原始碼"),
    ("fb",   "https://www.facebook.com/yaze.lin.gm", "Facebook"),
    ("bmc",  "https://buymeacoffee.com/yazelin",     "請亞澤喝咖啡"),
    ("blog", "https://yazelin.github.io/",           "亞澤的部落格"),
]

CSS = """
:root{
  --ground:#f3f1f8; --surface:#ffffff; --sunk:#e6e3f0;
  --line:#d3cfe2; --text:#1e1e34; --muted:#565273; --faint:#8b87a3;
  --glitch:#4a4aa8; --lamp:#8f5a1f; --r:3px;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --ground:#0e0e20; --surface:#17172e; --sunk:#0a0a19;
  --line:#2b2b4c; --text:#e4e1ef; --muted:#a09cbd; --faint:#75718f;
  --glitch:#a8a8e8; --lamp:#d9a05b;
}}
:root[data-theme="dark"]{
  --ground:#0e0e20; --surface:#17172e; --sunk:#0a0a19;
  --line:#2b2b4c; --text:#e4e1ef; --muted:#a09cbd; --faint:#75718f;
  --glitch:#a8a8e8; --lamp:#d9a05b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--text);
  font-family:"Noto Serif TC",Georgia,serif;font-size:18px;line-height:2.05;
  -webkit-text-size-adjust:100%}
.wrap{max-width:38em;margin:0 auto;padding:0 24px 100px}
header{padding:72px 0 34px}
header .eyebrow{font-family:"DM Mono",ui-monospace,monospace;font-size:12px;
  letter-spacing:.22em;color:var(--glitch);margin-bottom:14px}
header h1{font-weight:600;font-size:clamp(30px,6vw,44px);line-height:1.3;
  margin:0 0 14px;text-wrap:balance}
header p{margin:0;color:var(--muted);font-size:15.5px;line-height:1.8;
  font-family:"Noto Sans TC",system-ui,sans-serif}
hr.rule{border:0;border-top:1px solid var(--line);margin:0}

h2.ch{font-weight:600;font-size:21px;margin:56px 0 30px;color:var(--glitch);
  font-family:"DM Mono",ui-monospace,monospace;letter-spacing:.12em}
h2.ch::before{content:"";display:block;width:34px;border-top:2px solid var(--glitch);
  margin-bottom:16px}
/* 章內的小節只是換氣，不是標題。壓小、置中、不要跟章名同一個重量 */
h3.sec{font-weight:400;font-size:15px;margin:52px 0 30px;color:var(--faint);
  text-align:center;letter-spacing:.5em;text-indent:.5em}
p{margin:0 0 1.35em}
blockquote{margin:1.3em 0;padding:2px 0 2px 18px;border-left:2px solid var(--lamp);
  color:var(--text);font-weight:600}
blockquote p{margin:0}
/* 聊天室的留言。它們是介面，不是散文，所以換字體、換節奏 */
.chat{margin:1.2em 0;padding:12px 16px;background:var(--sunk);border-radius:var(--r);
  font-family:"Noto Sans TC",system-ui,sans-serif;font-size:15px;line-height:1.85}
.chat b{color:var(--lamp);font-weight:500}
.chat div+div{margin-top:2px}
pre{background:var(--sunk);border-radius:var(--r);padding:16px 18px;overflow-x:auto;
  font-family:"DM Mono",ui-monospace,monospace;font-size:14px;line-height:1.9;
  color:var(--muted);margin:1.3em 0}
code{font-family:"DM Mono",ui-monospace,monospace;font-size:.9em;color:var(--muted);
  background:var(--sunk);border-radius:var(--r);padding:1px 6px}
strong{font-weight:600}
footer{margin-top:80px;padding-top:24px;border-top:1px solid var(--line);
  color:var(--faint);font-size:14px;font-family:"Noto Sans TC",system-ui,sans-serif;
  line-height:1.85}
footer a{color:var(--muted)}
.promo{display:flex;gap:12px;margin-top:14px}
.promo a{display:inline-flex;color:var(--muted)}
.promo a:hover{color:var(--glitch)}
.promo svg{width:20px;height:20px}
@media (max-width:600px){ body{font-size:17px;line-height:1.95} .wrap{padding:0 20px 80px} }
"""


def render(md):
    """夠用就好的 markdown：段落、## 標題、> 引用、``` 區塊、聊天室、粗體。"""
    out, buf, mode = [], [], None

    def flush():
        nonlocal buf, mode
        if not buf:
            mode = None
            return
        if mode == "chat":
            out.append('<div class="chat">' + "".join(
                f"<div>{inline(l)}</div>" for l in buf) + "</div>")
        elif mode == "quote":
            out.append("<blockquote><p>" + "<br>".join(inline(l) for l in buf) + "</p></blockquote>")
        elif mode == "pre":
            out.append("<pre>" + "\n".join(E(l) for l in buf) + "</pre>")
        else:
            out.append("<p>" + "<br>".join(inline(l) for l in buf) + "</p>")
        buf, mode = [], None

    def inline(t):
        t = E(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        return t

    inpre = False
    for raw in md.split("\n"):
        line = raw.rstrip()
        if line.startswith("```"):
            if inpre:
                flush()
            else:
                flush(); mode = "pre"
            inpre = not inpre
            continue
        if inpre:
            buf.append(line); mode = "pre"; continue
        if not line.strip():
            flush(); continue
        if line.startswith("# "):
            flush(); continue                      # 標題由頁面自己出
        if line.startswith("## "):
            flush()
            t = line[3:].strip()
            tag = "h3 class=\"sec\"" if len(t) <= 2 else "h2 class=\"ch\""
            out.append(f"<{tag}>{inline(t)}</{tag.split()[0]}>")
            continue
        if line.startswith("> "):
            body = line[2:]
            m = "chat" if body.lstrip().startswith("**") and "：" in body else "quote"
            if mode not in (None, m):
                flush()
            mode = m; buf.append(body); continue
        if mode in ("chat", "quote"):
            flush()
        mode = mode or "p"
        buf.append(line)
    flush()
    return "".join(out)


chapters = sorted((ROOT / "novel").glob("ch*.md"))
body = []
for p in chapters:
    md = p.read_text(encoding="utf-8")
    title = next((l[2:].strip() for l in md.split("\n") if l.startswith("# ")), p.stem)
    body.append(f'<h2 class="ch" style="margin-top:34px">{E(title)}</h2>' if not body
                else f'<hr class="rule"><h2 class="ch">{E(title)}</h2>')
    body.append(render(md))

promo = ('<div class="promo">' + "".join(
    f'<a href="{u}" target="_blank" rel="noopener" aria-label="{t}" title="{t}">{ICONS[k]}</a>'
    for k, u, t in LINKS) + "</div>")

HTML = f'''<title>格莉奇與黑洞先生</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500&family=Noto+Serif+TC:wght@400;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header>
<div class="eyebrow">分支對話小說</div>
<h1>格莉奇與黑洞先生</h1>
<p>兩年前開台第一天來了七個人。她說，我要記住每一個來的人，我保證。</p>
</header>
<hr class="rule">
{"".join(body)}
<footer>
<p>目前寫到第 {len(chapters)} 章。這一頁只有小說，沒有機制。</p>
<p>《格莉奇與黑洞先生》　MIT　林亞澤　　角色設定正典在
<a href="https://github.com/yazelin/ai-brain-site">ai-brain-site</a> 的 persona.json</p>
{promo}
</footer>
</div>
'''

out = ROOT / "docs/novel.html"
out.write_text(HTML, encoding="utf-8")
print(f"寫好 {out}（{len(HTML)//1024} KB，{len(chapters)} 章）")

APPLY = pathlib.Path.home() / ".claude/skills/promo-footer/apply.py"
if APPLY.exists():
    r = subprocess.run([sys.executable, str(APPLY), str(out), "glitch-vn"],
                       capture_output=True, text=True)
    print("  推廣 footer:", r.stdout.strip() or r.stderr.strip())
