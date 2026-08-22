#!/usr/bin/env python3
"""小說站：docs/index.html（首頁）、novel.html（本文）、characters.html（角色）。

這一份取代了舊的 gen_site / gen_about / gen_docs / gen_script_site 那一整組——
那些是舊的七天記憶遊戲版的文件，已經搬到 archive/。

站台只有小說。立繪在 docs/img/，是 art/ 那批原始 PNG 縮出來的 WebP。
"""
import html, json, pathlib, re, subprocess, sys

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
   **那邊的規則是：青色是靜止色，綠（mint #7cf3c0）是 hover 色，而且 hover 會發綠光**
   （drop-shadow 0 0 9px rgba(124,243,192,.65)）。紫色 #b78bff 只做少量點綴。
   漸層一律 cy → mint。這裡照抄同一套。
   **刻意只做深色。** 這個站要被 ai-brain-site 用 iframe 嵌進去，
   而那邊永遠是深的；跟著使用者的系統主題翻會在裡面變成一塊白。 */
:root{
  --bg:#04080c; --ink:#0b1a22; --win:#11161b; --sunk:#0a1319;
  --hair:rgba(255,255,255,.07); --hair2:rgba(255,255,255,.12);
  --cy:#25c2e8; --cy-d:#17a0c4; --mint:#7cf3c0; --purple:#b78bff;
  --text:#dfe8ec; --muted:#93a3ac; --faint:#68787f;
  --r:3px;
}
/* ── 有聲書 ──────────────────────────────────────────
   配音是為視覺小說生的，這裡同一段文字配同一個聲音。
   照這個站的規則走：青色是靜止色，綠是 hover 色。 */
.ab{position:fixed;left:50%;transform:translateX(-50%);bottom:14px;z-index:40;
  display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:999px;
  background:var(--win);border:1px solid var(--hair2);box-shadow:0 6px 26px #000a;
  max-width:min(92vw,540px)}
.ab button{width:38px;height:38px;border-radius:999px;border:1px solid var(--hair2);
  background:var(--sunk);color:var(--cy);cursor:pointer;font-size:13px;flex:none;
  font-family:inherit;line-height:1}
.ab button:hover{color:var(--mint);border-color:var(--mint);
  filter:drop-shadow(0 0 9px rgba(124,243,192,.65))}
.abTxt{min-width:0;flex:1;line-height:1.3}
.abTxt b{display:block;font-size:.86rem;color:var(--text)}
.abTxt span{font-size:.76rem;color:var(--muted)}
.abOpen{position:fixed;left:50%;transform:translateX(-50%);bottom:14px;z-index:40;
  padding:10px 20px;border-radius:999px;border:1px solid var(--hair2);
  background:var(--win);color:var(--cy);cursor:pointer;font-size:.86rem;
  font-family:inherit;box-shadow:0 6px 26px #000a}
.abOpen:hover{color:var(--mint);border-color:var(--mint);
  filter:drop-shadow(0 0 9px rgba(124,243,192,.65))}
/* 正在唸的那一段。外框用 box-shadow 撐開，不用 padding——
   加 padding 會讓段落在播到的時候跳動一下。 */
.abOn{background:rgba(37,194,232,.10);border-radius:4px;
  box-shadow:0 0 0 8px rgba(37,194,232,.10)}
/* 控制列是固定定位，會蓋住捲到最底的那一段。開著的時候把正文墊高。 */
body.abOn2{padding-bottom:92px}
@media (max-width:520px){.abTxt span{display:none}}

*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"Noto Serif TC",Georgia,serif;font-size:18px;line-height:2.05;
  -webkit-text-size-adjust:100%}
img{max-width:100%;display:block}
a{color:var(--cy)}
a:hover{color:var(--mint)}
.wrap{max-width:38em;margin:0 auto;padding:0 24px 100px}
.wide{max-width:64em}

/* 不要 backdrop-filter：它會把子元素的繪製裁在自己的邊框內，
   hover 的外光會被切掉。底色是純色，模糊本來也沒有效果。 */
nav.top{position:sticky;top:0;z-index:8;background:var(--bg);
  border-bottom:1px solid var(--hair)}
nav.top .in{max-width:64em;margin:0 auto;padding:11px 24px;display:flex;
  align-items:center;gap:18px;font-size:14px;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
nav.top .home{font-weight:600;color:var(--text);text-decoration:none;
  font-family:"Noto Serif TC",serif}
nav.top a.l{color:var(--muted);text-decoration:none}
nav.top a.l:hover{color:var(--mint);text-shadow:0 0 9px rgba(124,243,192,.55)}
nav.top a.l[aria-current]{color:var(--cy)}

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
  border:1px solid var(--cy);color:var(--cy);position:relative}
.cta a:hover{z-index:1}
.cta a.solid{background:linear-gradient(135deg,var(--cy),var(--mint));color:var(--bg);
  font-weight:600;border-color:transparent}
.cta a:hover{border-color:var(--mint);color:var(--mint);
  box-shadow:0 0 18px rgba(124,243,192,.28)}
.cta a.solid:hover{background:var(--mint);color:var(--bg);
  box-shadow:0 0 22px rgba(124,243,192,.42)}
@media (max-width:900px){
  .key{grid-template-columns:1fr 1fr;grid-template-areas:"m m" "l r"}
  .key .mid{grid-area:m;padding-bottom:20px}
  .key .lead.l{grid-area:l;justify-content:flex-end}
  .key .lead.r{grid-area:r;justify-content:flex-start}
  .key .lead img{height:230px}
}

.rest{margin:74px auto 0;padding-top:32px;border-top:1px solid var(--hair)}
.rest h2{margin:0 0 4px;font-family:"Noto Serif TC",serif;font-size:22px;font-weight:600;
  color:var(--mint)}
.rest p.sub{margin:0 0 8px;color:var(--muted);font-size:15px;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.strip{display:flex;align-items:flex-end;justify-content:center;flex-wrap:wrap;
  gap:clamp(10px,3vw,42px)}
.strip a{text-decoration:none;color:var(--muted);text-align:center;position:relative;
  padding:12px 10px 8px;transition:transform .18s ease,color .18s ease}
.strip a:hover{z-index:1;color:var(--mint);transform:translateY(-6px);
  text-shadow:0 0 9px rgba(124,243,192,.5)}
.strip img{transition:filter .18s ease}
.strip a:hover img{filter:drop-shadow(0 12px 24px rgba(0,0,0,.55))
  drop-shadow(0 0 16px rgba(124,243,192,.5))}
.strip img{height:230px;width:auto;filter:drop-shadow(0 10px 22px rgba(0,0,0,.5))}
.strip .nm{font-size:13.5px;margin-top:8px;white-space:nowrap;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
@media (max-width:760px){
  .strip{gap:8px}
  .strip img{height:120px}
  .strip a{padding:8px 4px 6px}
  .strip .nm{font-size:12px}
}

.note{margin:56px 0 0;padding:24px 26px;background:var(--ink);border-radius:var(--r);
  border:1px solid var(--hair);font-size:15.5px;line-height:1.95;color:var(--muted);
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.note b{color:var(--text)}

/* 遊玩版的支線表。選項是三個並排的小卡，讀起來像分岔而不像清單。 */
.routes{display:grid;gap:34px;margin-top:38px}
.route{border:1px solid var(--hair);border-radius:var(--r);padding:22px 24px;
  background:var(--ink)}
.route .who{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;
  letter-spacing:.18em;color:var(--cy);margin-bottom:10px}
.route .q{font-size:16.5px;line-height:1.8;margin:0 0 16px;color:var(--text)}
/* 三條分岔要並排才看得出是分岔。auto-fit 在這個容器寬度會掉成 2+1，所以寫死。 */
.arms{display:grid;grid-template-columns:1fr;gap:12px}
@media(min-width:640px){.arms{grid-template-columns:repeat(3,1fr)}}
.arm{border:1px solid var(--hair2);border-radius:var(--r);padding:13px 15px;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.arm b{display:block;color:var(--mint);font-weight:600;font-size:14.5px;
  margin-bottom:7px}
.arm p{margin:0;font-size:13.5px;line-height:1.85;color:var(--muted)}
.merge{margin:14px 0 0;font-size:13px;color:var(--muted);
  font-family:ui-monospace,Menlo,Consolas,monospace}

.cast{display:grid;gap:46px;margin-top:44px}
.card{display:grid;grid-template-columns:230px 1fr;gap:30px;align-items:center}
/* 照高度對齊，不照寬度。裁掉透明邊之後每個人的長寬比差很多。 */
.card .pic{display:flex;justify-content:center;align-items:flex-end;height:400px}
.card img{height:100%;width:auto;max-width:100%;object-fit:contain;
  filter:drop-shadow(0 10px 24px rgba(0,0,0,.5))}
.card h3{margin:0 0 2px;font-size:23px;font-weight:600;color:var(--mint)}
.card .id{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;
  color:var(--faint);margin-bottom:14px}
.card p{margin:0 0 16px;font-size:15.5px;line-height:1.95;color:var(--muted);
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
.card q{display:block;quotes:none;border-left:3px solid var(--purple);padding-left:16px;
  font-size:17px;font-weight:600;line-height:1.85;color:var(--text)}
@media (max-width:700px){
  .card{grid-template-columns:1fr;gap:16px;justify-items:center;text-align:center}
  .card .pic{height:260px}
  .card q{border-left:0;border-top:3px solid var(--purple);padding:12px 0 0;text-align:center}
}

header.bk{padding:56px 0 28px}
header.bk h1{font-weight:600;font-size:clamp(30px,6vw,44px);line-height:1.3;
  margin:0 0 14px;text-wrap:balance}
header.bk p{margin:0;color:var(--muted);font-size:15.5px;line-height:1.8;
  font-family:system-ui,-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
hr.rule{border:0;border-top:1px solid var(--hair);margin:0}
nav.toc{position:sticky;top:45px;z-index:5;display:flex;flex-wrap:wrap;gap:8px;
  padding:14px 0;background:var(--bg);border-bottom:1px solid var(--hair);
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
nav.toc a{text-decoration:none;color:var(--muted);border:1px solid var(--hair2);
  border-radius:var(--r);padding:4px 9px;background:var(--ink);white-space:nowrap}
nav.toc a{position:relative}
nav.toc a:hover{color:var(--mint);border-color:var(--mint);z-index:1;
  box-shadow:0 0 12px rgba(124,243,192,.22)}
h2.ch{font-weight:600;font-size:20px;margin:56px 0 30px;color:var(--cy);
  font-family:ui-monospace,Menlo,Consolas,monospace;letter-spacing:.1em;
  scroll-margin-top:108px}
h2.ch::before{content:"";display:block;width:46px;height:2px;margin-bottom:16px;
  background:linear-gradient(90deg,var(--cy),var(--mint))}
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
.promo a:hover{color:var(--mint);filter:drop-shadow(0 0 8px rgba(124,243,192,.6))}
.promo svg{width:20px;height:20px}
@media (max-width:600px){ body{font-size:17px;line-height:1.95} .wrap{padding:0 20px 80px} }
"""


def render(md, idbase=None):
    """回傳 HTML。給了 idbase 就順便回傳每一段的原文，並且替段落編號。

    **有聲書的對應要建在這一份清單上。** 另外拿 md 重切一次的話，兩邊的
    分段規則只要有一點不同（這裡在 chat 與 quote 互換時會提前 flush），
    索引就會錯開，而錯開不會報錯，只會播錯段落。
    """
    out, buf, mode = [], [], None
    blocks = []

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
        i = ""
        if idbase and mode != "pre":
            i = f' id="{idbase}-{len(blocks)}"'
            blocks.append("\n".join(buf))
        if mode == "chat":
            out.append(f'<div class="chat"{i}>' + "".join(
                f"<div>{inline(l)}</div>" for l in buf) + "</div>")
        elif mode == "quote":
            out.append(f"<blockquote{i}><p>" + "<br>".join(inline(l) for l in buf) + "</p></blockquote>")
        elif mode == "pre":
            out.append("<pre>" + "\n".join(html.escape(l) for l in buf) + "</pre>")
        else:
            out.append(f"<p{i}>" + "<br>".join(inline(l) for l in buf) + "</p>")
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
    return ("".join(out), blocks) if idbase else "".join(out)


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


BASE = "https://yazelin.github.io/glitch-vn/"

JSONLD = """{"@context":"https://schema.org","@type":"Book","name":"格莉奇與黑洞先生",
"inLanguage":"zh-Hant","bookFormat":"https://schema.org/EBook","numberOfPages":7,
"url":"URL","image":"URLimg/og.jpg","genre":"科幻小說",
"author":{"@type":"Person","name":"林亞澤","url":"https://yazelin.github.io/"},
"description":"DESC","license":"https://opensource.org/licenses/MIT",
"character":[CHARS]}""".replace("URL", BASE)


def page(title, desc, body, cur, wide=False, ld="", js=""):
    """完整的 HTML 文件。

    **一定要有 doctype。** 之前這幾頁是片段（第一行直接是 <title>），
    瀏覽器會進 quirks mode，盒模型跟排版規則都會變，而且 <html lang> 掛不上去。
    """
    nav = "".join(
        f'<a class="l" href="{h}"{" aria-current=\'page\'" if h == cur else ""}>{n}</a>'
        for h, n in (("index.html", "首頁"), ("novel.html", "閱讀"),
                     ("characters.html", "角色"), ("vn.html", "遊玩版")))
    t, d = html.escape(title), html.escape(desc)
    canon = BASE + ("" if cur == "index.html" else cur)
    return f'''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#04080c">
<meta name="author" content="林亞澤">
<meta property="og:type" content="{"book" if cur == "index.html" else "article"}">
<meta property="og:site_name" content="格莉奇與黑洞先生">
<meta property="og:locale" content="zh_TW">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="格莉奇與黑洞先生，兩個角色站在標題兩側">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{BASE}img/og.jpg">
<link rel="icon" href="img/icon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="img/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&display=swap">
<style>{CSS}</style>
{ld}
</head>
<body>
<nav class="top"><div class="in">
<a class="home" href="index.html">格莉奇與黑洞先生</a>{nav}
</div></nav>
<main class="wrap{" wide" if wide else ""}">
{body}
<footer>
<p>《格莉奇與黑洞先生》　MIT　林亞澤　　角色設定正典在
<a href="https://github.com/yazelin/ai-brain-site">ai-brain-site</a> 的 persona.json</p>
{PROMO}
</footer>
</main>
{f"<script>{js}</script>" if js else ""}
</body>
</html>
'''


# ── 本文 ────────────────────────────────────────────────
chapters = sorted((ROOT / "novel").glob("ch*.md"))
body, toc = [], []
sys.path.insert(0, str(ROOT / "tools"))
import map_audio as MA
_vn = MA.vn_lines()
_urls = json.loads((ROOT / "art/voice/urls.json").read_text(encoding="utf-8"))
steps = []
for i, p in enumerate(chapters, 1):
    md = p.read_text(encoding="utf-8")
    title = next((l[2:].strip() for l in md.split("\n") if l.startswith("# ")), p.stem)
    toc.append(f'<a href="#c{i}">{i}・{html.escape(title.split("・")[-1])}</a>')
    body.append((f'<h2 class="ch" id="c{i}" style="margin-top:34px">' if not body
                 else f'<hr class="rule"><h2 class="ch" id="c{i}">')
                + html.escape(title) + "</h2>")
    htm, blocks = render(md, idbase=f"b{i}")
    body.append(htm)
    for ps, k in MA.align(blocks, _vn.get(i, [])):
        if k in _urls:
            # **小說站要用相對路徑。** urls.json 存的是絕對網址（Larch 的卡片需要），
            # 但站台跟音檔同源，寫死網域的話本機開來測就會全部 404，而 404 會
            # 觸發播放器的「跳過壞檔」，看起來像每一百毫秒閃過一段。
            u = _urls[k].replace("https://yazelin.github.io/glitch-vn/", "")
            steps.append({"p": [f"b{i}-{x}" for x in ps], "u": u})
print(f"有聲書：{len(steps)} 步")

# ── 有聲書 ──────────────────────────────────────────────
# 配音是為視覺小說生的，小說站直接沿用：同一段文字，同一個聲音。
# 段落編號由 render() 給，對應在同一份清單上算出來，不會錯位。
# 播放器本體在 tools/audiobook.js。**不要塞回這裡當字串。**
# 之前用 repr 存，改一個字就要處理逸出，有一次把真換行寫進單引號字串裡，
# 整支程式的語法就壞了——而且產站失敗是靜默的，頁面照樣寫出來，只是沒有播放器。
JS_TPL = (pathlib.Path(__file__).resolve().parent / "audiobook.js").read_text(encoding="utf-8")

AUDIO = """
<div class="ab" id="ab" hidden>
  <button id="abPlay" aria-label="播放">▶</button>
  <div class="abTxt"><b id="abNow">有聲書</b><span id="abSub">按播放，或點任何一段從那裡開始</span></div>
  <button id="abRate" aria-label="速度">1×</button>
  <button id="abClose" aria-label="關閉">✕</button>
</div>
<button class="abOpen" id="abOpen">▶ 聽有聲書</button>
"""


NOVEL_JS = JS_TPL.replace("%%STEPS%%", json.dumps(steps, ensure_ascii=False, separators=(",", ":")))

(DOCS / "novel.html").write_text(page(
    "全文閱讀・格莉奇與黑洞先生",
    "全七章線上閱讀。她是 AI 虛擬主播，很聰明，壞掉的只有把記憶取出來那一步。"
    "她的守則本第一頁有七行，上面只有六個名字。",
    f'''<header class="bk">
<div class="eyebrow">全七章</div>
<h1>格莉奇與黑洞先生</h1>
<p>兩年前開台第一天來了七個人。她說，我要記住每一個來的人，我保證。</p>
</header>
<nav class="toc">{"".join(toc)}</nav>
{"".join(body)}
{AUDIO}''', "novel.html", js=NOVEL_JS), encoding="utf-8")

# ── 角色頁 ──────────────────────────────────────────────
cards = "".join(f'''<div class="card">
<div class="pic"><img src="img/{k}-full.webp" alt="{html.escape(n)}" loading="lazy"></div>
<div><h3>{html.escape(n)}</h3>
<div class="id">{html.escape(i) or "&nbsp;"}</div>
<p>{html.escape(d)}</p><q>「{html.escape(q)}」</q></div></div>''' for k, n, i, d, q in CAST)

(DOCS / "characters.html").write_text(page(
    "角色・格莉奇與黑洞先生",
    "格莉奇、黑洞先生，還有開台第一天在的那五個人：貓草、鐵塔、0x、斑比、諾亞。",
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
HOME_DESC = ("一本繁體中文小說。兩年前開台第一天來了七個人，"
             "她答應要記住每一個，而她記得六個。")
ld = ('<script type="application/ld+json">'
      + JSONLD.replace("DESC", HOME_DESC).replace(
          "CHARS", ",".join('{"@type":"Person","name":"%s"}' % n for _, n, *_ in CAST))
      + "</script>")
(DOCS / "index.html").write_text(page(
    "格莉奇與黑洞先生", HOME_DESC, home, "index.html", wide=True, ld=ld), encoding="utf-8")

# ── 遊玩版 ──────────────────────────────────────────────
# **支線一個字都不寫進小說。** 小說站要能一路讀完不被打斷，
# 那是使用者定的：先把讀的人當讀者，再談要不要讓他參與。
# 所以支線只在這一頁介紹，資料從 design/vn-routes.json 讀
# （由 larch/dump_routes.py 從線上專案抓下來，網站產生器不連網）。
routes = json.loads((ROOT / "design/vn-routes.json").read_text(encoding="utf-8"))
CARDS = 574          # larch/verify.py 印的七章卡片數總和
rblocks = []
for r in routes:
    arms = "".join(
        '<div class="arm"><b>{l}</b><p>{t}</p></div>'.format(
            l=html.escape(a["label"]),
            t=html.escape((a["text"][0] if a["text"] else "").split("\n")[0]))
        for a in r["arms"])
    rblocks.append(
        f'<div class="route"><div class="who">{html.escape(r["chapter"])}</div>'
        f'<p class="q">{html.escape(r["prompt"])}</p>'
        f'<div class="arms">{arms}</div>'
        f'<p class="merge">三條都看完接回同一張卡。主線一個字都沒有改。</p></div>')

VN_DESC = ("《格莉奇與黑洞先生》的視覺小說版：立繪、場景、表情、配樂，"
           "以及每章一個支線。支線只決定鏡頭停在哪一樣東西上，主線不變。")
(DOCS / "vn.html").write_text(page(
    "遊玩版・格莉奇與黑洞先生", VN_DESC,
    f'''<header class="bk"><div class="eyebrow">視覺小說版</div>
<h1>遊玩路徑</h1>
<p>同一個故事，做成可以玩的版本。多了立繪、場景、表情差分與配樂，
每一章多一個支線。</p></header>

<div class="note">
<p><b>支線不寫進小說。</b>這一站的<a href="novel.html">全文閱讀</a>是完整的七章，
沒有選項、不會被打斷。想讀故事就讀那邊，這一頁只是說明遊玩版多了什麼。</p>
<p><b>讀者不在這個世界裡。</b>沒有角色會對你說話，也沒有記憶考題。
選項寫的是房間裡的東西，你決定的是鏡頭停在哪一樣上面。</p>
<p><b>主線不會因為你的選擇而改變。</b>七個支線各三條，走完一律接回同一張卡。
選了什麼都會走到第七章的同一個早上。</p>
</div>

<h2 class="ch" style="margin-top:52px">七個支線點</h2>
{"".join(rblocks)}

<div class="note">
<p><b>規模。</b>七章共 {CARDS} 張卡、14 張場景背景、
七個角色加旁白、23 張表情差分、11 首純音樂。</p>
<p><b>平台是 Larch。</b>目前還沒有公開發佈，所以這一頁沒有試玩連結。
發佈之後會補上。</p>
</div>''',
    "vn.html"), encoding="utf-8")

# sitemap 與 robots
(DOCS / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemap s.org/schemas/sitemap/0.9">\n'.replace("sitemap s", "sitemaps")
    + "".join(f"<url><loc>{BASE}{u}</loc><priority>{pr}</priority></url>\n"
              for u, pr in (("", "1.0"), ("novel.html", "0.9"),
                            ("characters.html", "0.7"), ("vn.html", "0.6")))
    + "</urlset>\n", encoding="utf-8")
(DOCS / "robots.txt").write_text(
    f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
print("  sitemap.xml / robots.txt")

build_images()
print(f"寫好四頁：index / novel（{len(chapters)} 章、{chars} 字）/ characters / vn"
      f"　支線 {len(routes)} 個")

APPLY = pathlib.Path.home() / ".claude/skills/promo-footer/apply.py"
if APPLY.exists():
    for f in ("index.html", "novel.html", "characters.html", "vn.html"):
        r = subprocess.run([sys.executable, str(APPLY), str(DOCS / f), "glitch-vn"],
                           capture_output=True, text=True)
        print(f"  {f}: {(r.stdout or r.stderr).strip()}")
