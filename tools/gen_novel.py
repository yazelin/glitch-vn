#!/usr/bin/env python3
"""小說站：docs/index.html（首頁）、novel.html（本文）、characters.html（角色）。

這一份取代了舊的 gen_site / gen_about / gen_docs / gen_script_site 那一整組——
那些是舊的七天記憶遊戲版的文件，已經搬到 archive/。

站台只有小說。立繪在 docs/img/，是 art/ 那批原始 PNG 縮出來的 WebP。
"""
import html, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _icons import ICONS

ROOT = pathlib.Path.home() / "glitch-vn"
DOCS = ROOT / "docs"
LINKS = [
    ("gh",   "https://github.com/yazelin/glitch-vn", "原始碼"),
    ("fb",   "https://www.facebook.com/yaze.lin.gm", "Facebook"),
    ("bmc",  "https://buymeacoffee.com/yazelin",     "請亞澤喝咖啡"),
    ("blog", "https://yazelin.github.io/",           "亞澤的部落格"),
]

# 角色。引文一律取自本文，而且避開第七章的答案。
CAST = [
    ("glitch", "格莉奇", "", "AI 虛擬主播，頻道兩年。她很聰明，講話正常，判斷力完整。"
     "壞掉的只有把記憶取出來那一步。",
     "我知道啊。我只是叫不出來。這兩件事不一樣。"),
    ("blackhole", "黑洞先生", "", "她的室友。沒有腳，一叢穿短靴的觸手撐起西裝。"
     "他吃被忘掉的事，不吃任何食物。外套內側深不見底。",
     "像口袋裡有東西，可是那個口袋不是我的。"),
    ("catgrass", "貓草", "@CatGrass_80", "開台第一天隨手滑進來的人，現在全勤、等級八十。"
     "他害怕頻道紅，因為小房間裡他才是被記得的那一個。",
     "我那天也在啊。"),
    ("tower", "鐵塔", "@Tower_Manager", "經紀人。只看數據跟周邊庫存。"
     "他發現她的毛病有話題性，正在阻止她修好。",
     "妳今天聲音有點啞。明天少講一點話。"),
    ("zerox", "0x", "@Null_0x99", "同期出道的 AI，企業勢頂級歌姬，標榜零失誤。"
     "她把格莉奇當成必須抹除的恥辱。",
     "因為我全部都記得。"),
    ("bambi", "斑比", "@Bambi_Draft3", "接案繪師，畫她的立繪。"
     "為了畫出無瑕的神作，她把稿改到格莉奇開始懷疑自己記錯。",
     "妳是唯一一個每次都在看的人。"),
    ("noah", "諾亞", "@Radio_Noah", "住頂樓修古董收音機。他至今不懂什麼是 VTuber，"
     "只知道隔壁那個小姑娘常常把自己鎖在門外。",
     "因為妳每次都是第一次問啊。"),
]

VARPAT = re.compile(r"\{\{([^}]+)\}\}")


def E(t):
    return VARPAT.sub(lambda m: f"<var>{m.group(1)}</var>", html.escape(str(t)))


CSS = """
/* 配色對齊 ai-brain-site（格莉奇OS）：--bg #04080c、--ink #0b1a22、--cy #25c2e8。
   **刻意只做深色。** 這個站要被 ai-brain-site 用 iframe 嵌進去，
   而那邊永遠是深的；跟著使用者的系統主題翻會在裡面變成一塊白。 */
:root{
  --bg:#04080c; --ink:#0b1a22; --win:#11161b; --sunk:#0a1319;
  --hair:rgba(255,255,255,.07); --hair2:rgba(255,255,255,.12);
  --cy:#25c2e8; --cy-d:#17a0c4; --mint:#7cf3c0; --purple:#b78bff;
  --text:#dfe8ec; --muted:#93a3ac; --faint:#68787f;
  --r:3px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"Noto Serif TC",Georgia,serif;font-size:18px;line-height:2.05;
  -webkit-text-size-adjust:100%}
img{max-width:100%;display:block}
a{color:var(--cy)}
.ui{font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace}
.wrap{max-width:38em;margin:0 auto;padding:0 24px 100px}
.wide{max-width:64em}

nav.top{position:sticky;top:0;z-index:8;background:rgba(4,8,12,.92);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--hair)}
nav.top .in{max-width:64em;margin:0 auto;padding:11px 24px;display:flex;
  align-items:center;gap:18px;font-size:14px;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
nav.top .home{font-weight:600;color:var(--text);text-decoration:none;
  font-family:"Noto Serif TC",serif}
nav.top a.l{color:var(--muted);text-decoration:none}
nav.top a.l:hover,nav.top a.l[aria-current]{color:var(--cy)}

.eyebrow{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;
  letter-spacing:.24em;color:var(--cy);margin-bottom:18px}

/* 主視覺：兩個主角一左一右，字在中間。這兩個是主角，其他五個是名單上的人。 */
.key{display:grid;grid-template-columns:1fr minmax(0,25em) 1fr;align-items:end;
  margin:22px auto 0;max-width:66em}
.key .lead{display:flex;justify-content:center}
.key .lead img{height:clamp(300px,42vw,560px);width:auto;max-width:100%;
  object-fit:contain;filter:drop-shadow(0 18px 38px rgba(0,0,0,.6))}
.key .mid{padding:0 18px 60px;text-align:center}
.mid h1{font-weight:600;font-size:clamp(32px,5.4vw,50px);line-height:1.24;
  margin:0 0 22px;text-wrap:balance}
.mid .lede{margin:0 auto;max-width:22em;font-size:18px;line-height:1.95}
.mid .lede b{color:var(--cy);font-weight:600}
.cta{margin:36px 0 0;display:flex;gap:12px;justify-content:center;flex-wrap:wrap;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.cta a{font-size:15px;text-decoration:none;padding:11px 26px;border-radius:var(--r);
  border:1px solid var(--cy);color:var(--cy)}
.cta a.solid{background:var(--cy);color:var(--bg);font-weight:600}
.cta a:hover{border-color:var(--mint);color:var(--mint)}
.cta a.solid:hover{background:var(--mint);color:var(--bg)}
@media (max-width:900px){
  .key{grid-template-columns:1fr 1fr;grid-template-areas:"m m" "l r"}
  .key .mid{grid-area:m;padding-bottom:20px}
  .key .lead.l{grid-area:l;justify-content:flex-end}
  .key .lead.r{grid-area:r;justify-content:flex-start}
  .key .lead img{height:230px}
}

.rest{margin:74px auto 0;padding-top:32px;border-top:1px solid var(--hair)}
.rest h2{margin:0 0 4px;font-family:"Noto Serif TC",serif;font-size:22px;font-weight:600}
.rest p.sub{margin:0 0 8px;color:var(--muted);font-size:15px;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.strip{display:flex;align-items:flex-end;justify-content:center;flex-wrap:wrap}
.strip a{text-decoration:none;color:var(--muted);text-align:center;margin:0 -4px;
  padding:12px 8px 6px;border-radius:var(--r)}
.strip a:hover{background:var(--ink);color:var(--cy)}
.strip img{height:230px;width:auto;filter:drop-shadow(0 10px 22px rgba(0,0,0,.5))}
.strip .nm{font-size:13.5px;margin-top:8px;white-space:nowrap;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
@media (max-width:760px){ .strip img{height:130px} .strip .nm{font-size:12px} }

.note{margin:56px 0 0;padding:24px 26px;background:var(--ink);border-radius:var(--r);
  border:1px solid var(--hair);font-size:15.5px;line-height:1.95;color:var(--muted);
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.note b{color:var(--text)}

.cast{display:grid;gap:46px;margin-top:44px}
.card{display:grid;grid-template-columns:230px 1fr;gap:30px;align-items:center}
/* 照高度對齊，不照寬度。裁掉透明邊之後每個人的長寬比差很多。 */
.card .pic{display:flex;justify-content:center;align-items:flex-end;height:400px}
.card img{height:100%;width:auto;max-width:100%;object-fit:contain;
  filter:drop-shadow(0 10px 24px rgba(0,0,0,.5))}
.card h3{margin:0 0 2px;font-size:23px;font-weight:600}
.card .id{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;
  color:var(--faint);margin-bottom:14px}
.card p{margin:0 0 16px;font-size:15.5px;line-height:1.95;color:var(--muted);
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.card q{display:block;quotes:none;border-left:2px solid var(--mint);padding-left:16px;
  font-size:17px;font-weight:600;line-height:1.85;color:var(--text)}
@media (max-width:700px){
  .card{grid-template-columns:1fr;gap:16px;justify-items:center;text-align:center}
  .card .pic{height:260px}
  .card q{border-left:0;border-top:2px solid var(--mint);padding:12px 0 0;text-align:center}
}

header.bk{padding:56px 0 28px}
header.bk h1{font-weight:600;font-size:clamp(30px,6vw,44px);line-height:1.3;
  margin:0 0 14px;text-wrap:balance}
header.bk p{margin:0;color:var(--muted);font-size:15.5px;line-height:1.8;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
hr.rule{border:0;border-top:1px solid var(--hair);margin:0}
nav.toc{position:sticky;top:45px;z-index:5;display:flex;flex-wrap:wrap;gap:6px;
  padding:10px 0;background:rgba(4,8,12,.94);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--hair);
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
nav.toc a{text-decoration:none;color:var(--muted);border:1px solid var(--hair2);
  border-radius:var(--r);padding:4px 9px;background:var(--ink);white-space:nowrap}
nav.toc a:hover{color:var(--cy);border-color:var(--cy)}
h2.ch{font-weight:600;font-size:20px;margin:56px 0 30px;color:var(--cy);
  font-family:ui-monospace,Menlo,Consolas,monospace;letter-spacing:.1em;
  scroll-margin-top:108px}
h2.ch::before{content:"";display:block;width:34px;border-top:2px solid var(--cy);
  margin-bottom:16px}
h3.sec{font-weight:400;font-size:15px;margin:52px 0 30px;color:var(--faint);
  text-align:center;letter-spacing:.5em;text-indent:.5em}
p{margin:0 0 1.35em}
blockquote{margin:1.3em 0;padding:2px 0 2px 18px;border-left:2px solid var(--mint);
  color:var(--text);font-weight:600}
blockquote p{margin:0}
.chat{margin:1.2em 0;padding:12px 16px;background:var(--ink);border-radius:var(--r);
  border:1px solid var(--hair);font-size:15px;line-height:1.85;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.chat b{color:var(--purple);font-weight:500}
.chat div+div{margin-top:2px}
pre{background:var(--sunk);border:1px solid var(--hair);border-radius:var(--r);
  padding:16px 18px;overflow-x:auto;font-family:ui-monospace,Menlo,Consolas,monospace;
  font-size:14px;line-height:1.9;color:var(--muted);margin:1.3em 0}
code,var{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9em;
  color:var(--mint);background:var(--sunk);border-radius:var(--r);padding:1px 6px;
  font-style:normal}
strong{font-weight:600}
footer{margin-top:78px;padding-top:24px;border-top:1px solid var(--hair);
  color:var(--faint);font-size:14px;line-height:1.85;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
footer a{color:var(--muted)}
.promo{display:flex;gap:12px;margin-top:14px}
.promo a{display:inline-flex;color:var(--muted)}
.promo a:hover{color:var(--cy)}
.promo svg{width:20px;height:20px}
@media (max-width:600px){ body{font-size:17px;line-height:1.95} .wrap{padding:0 20px 80px} }
"""


def render(md):
    out, buf, mode = [], [], None

    def inline(t):
        t = E(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        return t

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
            out.append("<pre>" + "\n".join(html.escape(l) for l in buf) + "</pre>")
        else:
            out.append("<p>" + "<br>".join(inline(l) for l in buf) + "</p>")
        buf, mode = [], None

    inpre = False
    for raw in md.split("\n"):
        line = raw.rstrip()
        if line.startswith("```"):
            flush()
            if not inpre:
                mode = "pre"
            inpre = not inpre
            continue
        if inpre:
            buf.append(line); mode = "pre"; continue
        if not line.strip():
            flush(); continue
        if line.startswith("# "):
            flush(); continue
        if line.startswith("## "):
            flush()
            t = line[3:].strip()
            cls = "sec" if len(t) <= 3 else "ch"
            tag = "h3" if cls == "sec" else "h2"
            out.append(f'<{tag} class="{cls}">{inline(t)}</{tag}>')
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


def build_images():
    """從 art/ 的原始 PNG 生站台用的 WebP。

    **先裁掉四周全透明的邊再縮。** 不裁的話每張的留白不一樣，
    排在一起會有的大有的小。裁完之後每張的長寬比不同（0x 站得直、手垂著，
    比別人窄很多），所以版面一律照**高度**對齊，不要照寬度。
    """
    from PIL import Image
    import json
    ART = ROOT / "art"
    OUT = DOCS / "img"; OUT.mkdir(parents=True, exist_ok=True)
    src = {n: ART / f"sprite-{n}.png" for n in
           ("catgrass", "tower", "zerox", "bambi", "noah")}
    # 這兩張的原始檔在 Larch 上，抓下來的副本放 art/
    for n, f in (("glitch", "sprite-glitch.png"), ("blackhole", "sprite-blackhole.png")):
        if (ART / f).exists():
            src[n] = ART / f
    for name, path in src.items():
        im = Image.open(path).convert("RGBA")
        im = im.crop(im.getchannel("A").getbbox())
        for tag, h, q in (("card", 520, 82), ("full", 1100, 86)):
            o = im.copy(); o.thumbnail((1200, h), Image.LANCZOS)
            o.save(OUT / f"{name}-{tag}.webp", "WEBP", quality=q, method=6)
    print(f"  立繪 {len(src)} 個角色 x 2 尺寸")


PROMO = ('<div class="promo">' + "".join(
    f'<a href="{u}" target="_blank" rel="noopener" aria-label="{t}" title="{t}">{ICONS[k]}</a>'
    for k, u, t in LINKS) + "</div>")


def page(title, desc, body, cur, wide=False):
    nav = "".join(
        f'<a class="l" href="{h}"{" aria-current=\'page\'" if h == cur else ""}>{n}</a>'
        for h, n in (("index.html", "首頁"), ("novel.html", "閱讀"),
                     ("characters.html", "角色")))
    return f'''<title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500&family=Noto+Serif+TC:wght@400;600&display=swap">
<style>{CSS}</style>
<nav class="top"><div class="in">
<a class="home" href="index.html">格莉奇與黑洞先生</a>{nav}
</div></nav>
<div class="wrap{" wide" if wide else ""}">
{body}
<footer>
<p>《格莉奇與黑洞先生》　MIT　林亞澤　　角色設定正典在
<a href="https://github.com/yazelin/ai-brain-site">ai-brain-site</a> 的 persona.json</p>
{PROMO}
</footer>
</div>
'''


# ── 本文 ────────────────────────────────────────────────
chapters = sorted((ROOT / "novel").glob("ch*.md"))
body, toc = [], []
for i, p in enumerate(chapters, 1):
    md = p.read_text(encoding="utf-8")
    title = next((l[2:].strip() for l in md.split("\n") if l.startswith("# ")), p.stem)
    toc.append(f'<a href="#c{i}">{i}・{html.escape(title.split("・")[-1])}</a>')
    body.append((f'<h2 class="ch" id="c{i}" style="margin-top:34px">' if not body
                 else f'<hr class="rule"><h2 class="ch" id="c{i}">')
                + html.escape(title) + "</h2>")
    body.append(render(md))

(DOCS / "novel.html").write_text(page(
    "格莉奇與黑洞先生",
    "兩年前開台第一天來了七個人。她答應要記住每一個，而她記得六個。",
    f'''<header class="bk">
<div class="eyebrow">全七章</div>
<h1>格莉奇與黑洞先生</h1>
<p>兩年前開台第一天來了七個人。她說，我要記住每一個來的人，我保證。</p>
</header>
<nav class="toc">{"".join(toc)}</nav>
{"".join(body)}''', "novel.html"), encoding="utf-8")

# ── 角色頁 ──────────────────────────────────────────────
cards = "".join(f'''<div class="card">
<div class="pic"><img src="img/{k}-full.webp" alt="{html.escape(n)}" loading="lazy"></div>
<div><h3>{html.escape(n)}</h3>
<div class="id">{html.escape(i) or "&nbsp;"}</div>
<p>{html.escape(d)}</p><q>「{html.escape(q)}」</q></div></div>''' for k, n, i, d, q in CAST)

(DOCS / "characters.html").write_text(page(
    "角色・格莉奇與黑洞先生", "七個人，加上一個沒有名字的第七行。",
    f'''<header class="bk"><div class="eyebrow">角色</div>
<h1>名單上的人</h1>
<p>守則本第一頁上有七行。上面只有六個名字。</p></header>
<div class="cast">{cards}</div>''', "characters.html", wide=True), encoding="utf-8")

# ── 首頁 ────────────────────────────────────────────────
# 主角是前兩個。七個人等重排一列的話，看不出來這本書是誰的故事。
rest = "".join(
    '<a href="characters.html"><img src="img/{k}-card.webp" alt="{n}" loading="lazy">'
    '<div class="nm">{n}</div></a>'.format(k=k, n=html.escape(n))
    for k, n, *_ in CAST[2:])
chars = sum(len(re.sub(r"\s", "", p.read_text(encoding="utf-8"))) for p in chapters)
home = """<div class="key">
<div class="lead l"><img src="img/glitch-full.webp" alt="格莉奇" fetchpriority="high"></div>
<div class="mid">
<div class="eyebrow">繁體中文小說・全七章</div>
<h1>格莉奇與黑洞先生</h1>
<p class="lede">兩年前開台第一天來了七個人。<br>
她說，我要記住每一個來的人，我保證。<br><br>
<b>她記得六個。</b></p>
<div class="cta">
<a class="solid" href="novel.html">開始閱讀</a>
<a href="characters.html">看角色</a>
</div>
</div>
<div class="lead r"><img src="img/blackhole-full.webp" alt="黑洞先生" fetchpriority="high"></div>
</div>
<div class="rest">
<h2>名單上還有五個人</h2>
<p class="sub">開台第一天在的那七個，兩年後散在各處。</p>
<div class="strip">REST</div>
</div>
<div class="note">
<p><b>格莉奇是 AI 虛擬主播。</b>她很聰明，講話正常，判斷力完整。
壞掉的只有把記憶取出來那一步：她知道有某件事、知道自己在乎過，就是叫不出內容。</p>
<p><b>黑洞先生是她的室友。</b>他吃被忘掉的事，不吃任何食物。
吃進去的永遠在他裡面，可是拿不出來，連他自己也拿不到。</p>
<p><b>她每天睡前在守則本上抄一次第一頁。</b>那一頁上有七行。
上面只有六個名字。第七行是一句話，字跡是她自己的。</p>
<p>全七章，約 CHARS 字。沒有機制，沒有選項，就是一本小說。</p>
</div>""".replace("REST", rest).replace("CHARS", f"{chars:,}")
(DOCS / "index.html").write_text(page(
    "格莉奇與黑洞先生",
    "一本繁體中文小說。兩年前開台第一天來了七個人，她答應要記住每一個，而她記得六個。",
    home, "index.html", wide=True), encoding="utf-8")

build_images()
print(f"寫好三頁：index / novel（{len(chapters)} 章、{chars} 字）/ characters")

APPLY = pathlib.Path.home() / ".claude/skills/promo-footer/apply.py"
if APPLY.exists():
    for f in ("index.html", "novel.html", "characters.html"):
        r = subprocess.run([sys.executable, str(APPLY), str(DOCS / f), "glitch-vn"],
                           capture_output=True, text=True)
        print(f"  {f}: {(r.stdout or r.stderr).strip()}")
