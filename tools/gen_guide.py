#!/usr/bin/env python3
"""《調查篇》公式站的產生器。跑：python3 tools/gen_guide.py

**不要手寫那些頁面。** 門檻這個禮拜改過五次（0x 從十一趟到六趟、保全從三趟到兩趟、
貓草的條件從 == 0 改成 <= 0），手寫的公式站在第一次改門檻的當天就會失真。
這一支的資料來源只有兩個：

  larch/inv/out/board.json   建置產出的板子：選單規則、條件、變數、卡片
  design/調查篇-*.md         稿子：總表、機制、跟正篇的關係那幾段散文

輸出寫到 docs/guide/（2026-09-11 拍板上架；在那之前放在 repo 根目錄的 guide/，
因為 docs 一推上 main 就等於公開）。正篇站的 nav 有一格「調查篇」指到這裡。
"""
import json
import pathlib
import re
import html
import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARD = json.loads((ROOT / "larch/inv/out/board.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs/guide"
TODAY = datetime.date.today().isoformat()

LOC_NAME = {"lobby": "一樓", "roof": "頂樓收音機店", "street": "車站前那條街",
            "busstop": "車站前站牌", "metro": "南港站二號出口", "store": "便利商店",
            "parts": "材料行", "laundry": "自助洗衣店", "figure": "手辦店",
            "studio": "斑比工作室", "booth": "錄音間門口", "tower14": "十四樓大廳"}
SLOT_NAME = ["上午", "下午", "晚上", "深夜"]
# 玩家看得到的名字。板上鐵塔顯示成經紀人，斑比在問到名字之前是「畫她的人」。
DISPLAY = {"鐵塔": "經紀人（鐵塔）", "斑比": "斑比（畫她的人）"}

# ── 條件轉人話 ────────────────────────────────────────────────
# 變數名對玩家沒有意義，公式站要寫的是「他要見過你幾次」。
VAR_TEXT = {
    "day": "第 {v} 天", "slot": "時段", "night_visits": "深夜出過門 {v} 次",
    "strikes": "筆記上劃掉 {v} 條", "hole_sightings": "跟那個穿西裝的擦身而過 {v} 次",
    "cat_visits": "深夜找過他 {v} 次", "met_櫃檯": "去過櫃檯 {v} 趟",
    "met_保全": "碰過保全 {v} 次", "met_店員": "碰過店員 {v} 次",
    "met_諾亞": "碰過諾亞 {v} 次", "met_管理員": "碰過管理員 {v} 次",
    "met_斑比": "碰過她 {v} 次", "met_鐵塔": "碰過經紀人 {v} 次",
    "met_貓草": "碰過他 {v} 次", "met_材料行老闆": "碰過老闆 {v} 次",
    "trust_斑比": "她的信任 {v}", "trust_貓草": "他的信任 {v}",
    "trust_店員": "店員的信任 {v}", "trust_保全": "保全的信任 {v}",
    "trust_管理員": "管理員的信任 {v}",
}
FLAG_TEXT = {
    "open_roof": "頂樓開了", "open_parts": "材料行開了", "open_laundry": "洗衣店開了",
    "open_studio": "工作室開了", "open_figure": "手辦店開了", "open_tower14": "十四樓開了",
    "names_seen": "看過那面牆", "clue_list": "拿到那六行名單", "note_mailbox": "抄過信箱",
    "seen_booth": "去過錄音間門口", "laundry_night1": "洗衣店待過一晚",
    "zero_answered": "0x 回答過了", "guard_told": "保全講過對面那個人",
    "seen_catgrass_home": "去過他家", "clue_notfix": "深夜碰過經紀人",
    "tube_bought": "買到那顆管子", "tube_given": "管子交出去了",
    "see_admin": "管理員說過那個人", "rec_ok": "錄音機修好了",
    "see_stairs": "管理員說過他走樓梯", "see_clerk": "店員說過那個人",
    "see_noah": "諾亞說過那個人", "see_parts": "老闆說過那個人",
    "see_cat": "他說過那個人", "see_bambi": "她說過那個人", "see_guard": "保全說過對面那個人",
    "seen_lostbox": "看過失物箱", "admin_third": "管理員那件事問到第三次",
    "bambi_revised": "她說過上次講錯了", "bambi_third": "同一件事問過她第三次",
    "cat_reask": "周邊那件事再問過", "noah_reask": "同一件事再問過諾亞",
    "cat_room_mentioned": "他提過他的房間", "deadend_cat_glitch": "問過他她的東西在哪一區",
    "deadend_cat": "問過他她是不是真的會忘", "note_blank": "翻到那一頁空白的",
    "open_store": "便利商店開了", "open_catgrass_home": "他家的門口出現了",
    "clue_cantfix": "拿到修不好那一條", "clue_real": "拿到四十版那一條",
    "clue_real_noah": "拿到諾亞那一條", "clue_older": "拿到日期比較早那一條",
    "clue_notebook": "拿到守則本那一條", "clue_lostbox": "拿到失物箱那一條",
    "clue_seventh": "拿到第七行那一條", "names_seen": "看過那面牆",
    "blocked_agency": "在經紀公司門口被擋過", "strike_cat_buy": "劃掉他買周邊那一條",
    "strike_fake": "劃掉她是裝的那一條", "note_mailbox": "抄過信箱",
    "noah_intro": "上過頂樓", "noah_alone": "諾亞下樓過", "met_flyer": "跟發傳單的講過話",
}
ITEM_TEXT = {"rec_guard": "保全那一卷", "rec_noah": "諾亞那一卷", "rec_clerk": "店員那一卷",
             "rec_bambi": "她那一卷", "rec_parts": "老闆那一卷"}
OPS = {"gte": "≥", "lte": "≤", "gt": ">", "lt": "<", "eq": "="}


def cond_text(c):
    var, op, val = c["variable"], c["op"], c.get("value")
    if op == "hasItem":
        return "背包裡有" + ITEM_TEXT.get(str(val), str(val))
    if var in FLAG_TEXT:
        base = FLAG_TEXT[var]
        if val is True:
            return base
        # 否定句：「洗衣店開了」→「洗衣店還沒開」，「看過那面牆」→「還沒看過那面牆」
        if base.endswith("開了"):
            return base[:-2] + "還沒開"
        if base.endswith("了"):
            return base[:-1] + "還沒發生"
        return f"還沒{base}"
    if var in VAR_TEXT:
        t = VAR_TEXT[var]
        if op == "eq":
            return t.format(v=val)
        return t.format(v=f"{OPS.get(op, op)} {val}")
    if var.startswith("asked_"):
        who = var.split("_")[1:]
        name = "、".join(who)
        return f"問過{name}" if val is True else f"還沒問過{name}"
    if var.startswith(("note_", "see_", "clue_", "deadend_", "strike_", "open_")):
        nice = var.replace("note_", "記下").replace("see_", "問到").replace("clue_", "線索")
        return f"{nice} 成立" if val is True else f"還沒{nice}"
    if val is True or val is False:
        return f"{var} 成立" if val is True else f"還沒{var}"
    return f"{var} {OPS.get(op, op)} {val}"


def rule_conds(r):
    if not r["conds"]:
        return "隨時"
    return "，".join(cond_text(c) for c in r["conds"])


# ── 頁面骨架 ────────────────────────────────────────────────
CSS = """
@font-face{font-family:"Noto Serif TC";font-style:normal;font-weight:400;font-display:swap;
  src:url("../fonts/noto-serif-tc-400.woff2") format("woff2")}
@font-face{font-family:"Noto Serif TC";font-style:normal;font-weight:600;font-display:swap;
  src:url("../fonts/noto-serif-tc-600.woff2") format("woff2")}
:root{
  --bg:#04080c; --ink:#0b1a22; --win:#11161b; --sunk:#0a1319;
  --hair:rgba(255,255,255,.07); --hair2:rgba(255,255,255,.12);
  --cy:#25c2e8; --mint:#7cf3c0; --purple:#b78bff;
  --text:#dfe8ec; --muted:#93a3ac; --faint:#6d7d84; --r:3px;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);
  font:16px/1.85 "Noto Serif TC",Songti TC,PMingLiU,Georgia,serif}
nav.top{position:sticky;top:0;z-index:8;background:var(--bg);border-bottom:1px solid var(--hair)}
nav.top .in{max-width:64em;margin:0 auto;padding:11px 24px;display:flex;gap:18px;
  flex-wrap:wrap;align-items:baseline;font-size:14px}
nav.top .home{font-weight:600;color:var(--text);text-decoration:none;margin-right:auto}
nav.top a.l{color:var(--muted);text-decoration:none}
nav.top a.l:hover{color:var(--mint);text-shadow:0 0 9px rgba(124,243,192,.55)}
nav.top a.l[aria-current]{color:var(--cy)}
main{max-width:64em;margin:0 auto;padding:34px 24px 90px}
h1{font-size:clamp(26px,4.4vw,38px);line-height:1.25;margin:0 0 8px;letter-spacing:.02em}
h2{font-size:22px;margin:46px 0 6px;letter-spacing:.02em}
h2::before{content:"";display:block;width:34px;height:2px;background:var(--cy);margin-bottom:12px}
h3{font-size:17px;margin:26px 0 4px;color:var(--cy)}
p{margin:0 0 14px;max-width:44em}
.lede{color:var(--muted)}
strong{color:#fff;font-weight:600}
code{font:13.5px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;
  background:var(--sunk);border:1px solid var(--hair);padding:.06em .38em;border-radius:var(--r)}
table{border-collapse:collapse;width:100%;font-size:14.5px;margin:14px 0}
.box{overflow-x:auto;border:1px solid var(--hair);border-radius:var(--r);background:var(--win)}
th,td{padding:9px 13px;text-align:left;border-bottom:1px solid var(--hair);white-space:nowrap}
thead th{color:var(--muted);font-weight:400;font-size:13px;background:var(--sunk)}
tbody tr:last-child td{border-bottom:none}
td.w{white-space:normal;min-width:16em}
.yes{color:var(--mint)}.no{color:var(--faint)}.refuse{color:var(--purple)}
.tag{font-size:12.5px;color:var(--faint);border:1px solid var(--hair2);
  padding:1px 7px;border-radius:999px;margin-left:8px;white-space:nowrap}
.spoiler{border:1px solid var(--hair2);border-radius:var(--r);padding:0 16px;margin:20px 0;background:var(--win)}
.spoiler summary{cursor:pointer;padding:13px 0;color:var(--cy);font-size:15px;list-style:none}
.spoiler summary::before{content:"▸ ";}
.spoiler[open] summary::before{content:"▾ ";}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(15em,1fr));gap:2px;margin:16px 0}
.cards a{display:block;padding:15px 16px;background:var(--win);border:1px solid var(--hair);
  text-decoration:none;color:var(--text)}
.cards a:hover{border-color:var(--mint);color:var(--mint)}
.cards small{display:block;color:var(--faint);font-size:13px;margin-top:3px}
footer{max-width:64em;margin:0 auto;padding:24px;border-top:1px solid var(--hair);
  color:var(--faint);font-size:13.5px}
"""

PAGES = [("index.html", "怎麼玩"), ("canon.html", "跟正篇的關係"), ("people.html", "出場人物"),
         ("places.html", "地點與時段"), ("threads.html", "支線與條件"),
         ("walkthrough.html", "完整攻略"), ("glossary.html", "名詞表")]


def nav(current):
    out = ['<nav class="top"><div class="in">',
           '<a class="home" href="index.html">調查篇・公式站</a>']
    for f, label in PAGES:
        cur = " aria-current='page'" if f == current else ""
        out.append(f'<a class="l" href="{f}"{cur}>{label}</a>')
    out.append('<a class="l" href="../index.html">回正篇</a>')
    out.append("</div></nav>")
    return "".join(out)


def page(fn, title, body, desc=""):
    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}・格莉奇與黑洞先生・調查篇</title>
<meta name="description" content="{html.escape(desc)}">
<style>{CSS}</style>
</head>
<body>
{nav(fn)}
<main>
{body}
</main>
<footer>《格莉奇與黑洞先生・調查篇》公式站　這一頁由 <code>tools/gen_guide.py</code>
從板子與稿子產生，{TODAY} 重建。門檻改了就重跑，不要手改這裡。</footer>
</body>
</html>
"""
    (OUT / fn).write_text(doc, encoding="utf-8")


# ── 一、怎麼玩 ────────────────────────────────────────────────
def build_index():
    rules = BOARD["rules"]
    locs = sorted({r["dest"] for r in rules})
    body = f"""
<h1>調查篇怎麼玩</h1>
<p class="lede">她不在畫面上。你會在十四天裡一直錯過她，然後從別人嘴裡把她拼回來。
這一頁講機制，剩下的分在上面那幾頁。</p>

<h2>一次開板，一個時段</h2>
<p>板子攤開就是她出門前的那張街區圖。你只選要去哪裡，時間自己往前走：
<strong>上午、下午、晚上、深夜</strong>，深夜過完換日。深夜要到<strong>第四天</strong>才亮，
前三天她還在照正常時間睡。</p>

<div class="box"><table>
<thead><tr><th>區間</th><th>可出門</th></tr></thead>
<tbody>
<tr><td>第一天（上午是開場，不經過板）</td><td>2 段</td></tr>
<tr><td>第二到三天</td><td>各 3 段</td></tr>
<tr><td>第四到十三天</td><td>各 4 段</td></tr>
<tr><td>合計</td><td><strong>48 段</strong>　白天 25、晚上 13、深夜 10</td></tr>
</tbody></table></div>

<p>第十四天上午只有收尾，玩家不選地點。<strong>時間是這一款唯一的成本</strong>，
沒有失敗、沒有扣分、沒有戰鬥，只有「今天這一段要花在誰身上」。</p>

<h2>板上那張便條</h2>
<p>左上角那張便條是她自己寫的待辦，最多三行，會照現在的時段排：
寫了時段又對得上的排前面。<strong>它是全篇唯一的引導</strong>，
而且是用她的口氣寫的，不是任務清單。實測不看便條的玩家一輪都走不完。</p>

<h2>信任是次數換的</h2>
<p>沒有好感度選項，也沒有正確答案。每一個人的信任只有一種升法：<strong>一直出現</strong>。
店員要見三次才願意講一件事；深夜那個人要三個晚上才開口；十四樓的櫃檯要去六趟。
這一款在講的事就是這個。</p>

<h2>背包裡有三樣</h2>
<div class="box"><table>
<thead><tr><th>道具</th><th>用途</th></tr></thead>
<tbody>
<tr><td>守則本</td><td class="w">她自己的筆記。問到的東西會記進去，玩家也可以自己打字。
第一頁是那六個 ID，見過的人才填得進去。</td></tr>
<tr><td>手機</td><td class="w">四頁：訊息、她的貼文、留言區、直播。舊留言翻得到，訊息只收不回。</td></tr>
<tr><td>錄音機</td><td class="w">有人講話的時候按得下去。錄到的那一卷進背包，可以再播一次，
其中一卷還能放給另一個人聽。<strong>有兩個人不給錄。</strong></td></tr>
</tbody></table></div>

<h2>地點</h2>
<p>板上總共 {len(locs)} 個地點，一開始只有幾個，其餘要有人告訴你才會出現在板上。
誰在哪裡、什麼時候在，見<a href="places.html">地點與時段</a>。</p>

<div class="cards">
<a href="canon.html">跟正篇的關係<small>什麼時候發生、為什麼找不到他們</small></a>
<a href="people.html">出場人物<small>誰能問誰，四十二種組合裡真的有東西的那些</small></a>
<a href="threads.html">支線與條件<small>每一格要什麼條件才開</small></a>
<a href="walkthrough.html">完整攻略<small>逐日路線，有雷</small></a>
</div>
"""
    page("index.html", "怎麼玩", body,
         "《格莉奇與黑洞先生・調查篇》的機制說明：時段、便條、信任、背包、地點。")


# ── 二、跟正篇的關係 ──────────────────────────────────────────
def build_canon():
    body = """
<h1>跟正篇的關係</h1>
<p class="lede">調查篇是外傳。玩之前不必讀完正篇，讀過的人會多聽懂幾句。</p>

<h2>時間點：正文之後</h2>
<p>正篇結束在第十二天早上，她走出房間去問他今天累不累。
<strong>調查篇發生在那之後不特定的某一段日子</strong>，玩家不知道也不需要知道那件事。
兩邊的「十二天」與「十四天」是各自的十四天，沒有因果。</p>

<h2>玩家是誰</h2>
<p>一個沒有名字的人。她帶著一本本子、一台會卡的錄音機，來查一個直播主是不是真的會忘記。
遊戲從頭到尾不解釋她為什麼要查，也不給她動機。<strong>她問得到的東西全部是別人的事。</strong></p>

<h2>為什麼永遠找不到他們兩個</h2>
<h3>格莉奇：她無所不在，只是隔著一層螢幕</h3>
<p>一樓的公告螢幕、便利商店的循環廣告、車站的廣告看板、材料行的舊電視、
十四樓大廳那台沒有開聲音的螢幕。她會講話，你聽得到，可是你走到哪裡她都在別的地方。</p>

<h3>黑洞先生：每個人看到的都不一樣</h3>
<p>正典寫死了：看到的是那個人自己叫不出名字的缺口的形狀。
她的遺忘是一整件、邊緣乾淨的，所以她看到的他有形狀。
普通人的遺忘是糊的，看到的就是一個很高的、穿西裝的先生，平凡到不值得跟人提起。</p>
<p>所以本子上那七份目擊沒有兩份一樣，而<strong>八份裡有一份是矮的</strong>。
遊戲把它們並排放在同一頁上，一個字都不解釋。</p>

<h2>那六個 ID</h2>
<p>正篇第六章她查過自己守則本的第一頁：七條橫線，前六條上面有字。
調查篇讓你從另一邊把那六個人找出來，而<strong>第七行到最後還是空的</strong>。</p>

<details class="spoiler"><summary>這一段有雷：那六個是誰</summary>
<p>看過斑比那面牆的人會拿到六行 ID。名字要玩家自己在守則本第一頁填，
下拉裡只有你真的見過的人。第五行那個人自己不知道他在上面，
第六行那個帳號兩年前就刪了，只有一個人講得出他的事。</p>
</details>

<h2>不點破</h2>
<p>這一款有一條寫在設計稿最前面的規矩：<strong>重複要溫柔，永遠不點破</strong>。
沒有任何一張卡會說「你發現他們講的不一樣」，也沒有系統提示告訴你哪一條是線索。
矛盾就擺在那裡，看不看得出來是你的事。</p>
"""
    page("canon.html", "跟正篇的關係", body,
         "調查篇發生在正篇之後，為什麼永遠找不到格莉奇與黑洞先生，以及那六個 ID。")


# ── 三、出場人物與關係 ────────────────────────────────────────
def build_people():
    md = (ROOT / "design/調查篇-問答矩陣.md").read_text(encoding="utf-8")
    block = md[md.index("| 問誰＼關於"):]
    rows = [ln for ln in block.split("\n") if ln.startswith("|")][:11]
    head = [c.strip() for c in rows[0].strip("|").split("|")]
    matrix = []
    for ln in rows[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) == len(head):
            matrix.append(cells)

    def mark(x):
        if x == "○":
            return '<span class="yes">○</span>'
        if x == "拒":
            return '<span class="refuse">拒</span>'
        return '<span class="no">—</span>'

    thead = "".join(f"<th>{html.escape(h)}</th>" for h in head)
    tbody = "".join(
        "<tr><td>" + html.escape(r[0]) + "</td>" +
        "".join(f"<td>{mark(c)}</td>" for c in r[1:]) + "</tr>" for r in matrix)
    n_yes = sum(c == "○" for r in matrix for c in r[1:])
    body = f"""
<h1>出場人物</h1>
<p class="lede">八個問得到的人，七個被問的對象。
<span class="yes">○</span> 有話講、<span class="no">—</span> 沒話講、
<span class="refuse">拒</span> 拒絕回答。</p>

<div class="box"><table>
<thead><tr>{thead}</tr></thead>
<tbody>{tbody}</tbody>
</table></div>

<p>五十六格裡有記號的二十五格，其中 {n_yes} 格有話講。
<strong>其餘三十一格是空的，而且是刻意的</strong>：
稿子一句台詞都沒有替它們寫，問不到就是問不到。</p>

<h2>他們是誰</h2>
<div class="box"><table>
<thead><tr><th>人</th><th>在哪裡</th><th>他給的是什麼</th></tr></thead>
<tbody>
<tr><td>管理員</td><td>一樓・白天</td><td class="w">這棟樓的營運。他的目擊是七份裡最平的一份。</td></tr>
<tr><td>諾亞</td><td>頂樓收音機店</td><td class="w">修收音機的老先生。他是那六個名字裡的一個，而他自己不知道。</td></tr>
<tr><td>斑比</td><td>洗衣店晚上、工作室</td><td class="w">畫她的人。她那面牆是全篇唯一真的看到那六個名字的地方。</td></tr>
<tr><td>經紀人（鐵塔）</td><td>錄音間門口、便利商店深夜</td><td class="w">白天只給官方版本，深夜的他是另一個人。他不給錄音。</td></tr>
<tr><td>0x</td><td>十四樓大廳</td><td class="w">全作唯一一個沒有辦法不記得的人。兩分鐘，一次性。</td></tr>
<tr><td>貓草</td><td>便利商店深夜</td><td class="w">關東煮、兩顆蘿蔔、一杯無糖。他不給錄音，錄了那一晚不算。</td></tr>
<tr><td>便利商店店員</td><td>便利商店・任一時段</td><td class="w">第三次才記得你。他知道這條街晚上還有什麼開著。</td></tr>
<tr><td>材料行老闆</td><td>材料行・白天</td><td class="w">那顆真空管。他看過那個穿西裝的三次。</td></tr>
<tr><td>保全</td><td>十四樓・晚上與深夜</td><td class="w">不在上面那張表裡。他手上有全篇唯一一份對不起來的目擊。</td></tr>
</tbody></table></div>
"""
    page("people.html", "出場人物", body,
         "調查篇的八個人物與那張誰能問誰的總表。")


# ── 四、地點與時段 ──────────────────────────────────────────
def board_tables():
    """從 board.html 撈兩張表：地點常駐（live）與訪客機率（VISITS）。
    那兩張是玩家看得到的行為，直接讀卡片原始碼，不要另外抄一份。"""
    js = (ROOT / "larch/cards/board.html").read_text(encoding="utf-8")
    spots = []
    blk = re.search(r"var SPOTS=\[(.*?)\n\];", js, re.S).group(1)
    for m in re.finditer(r"\{id:'(\w+)',\s*name:'(.+?)',\s*live:\[(.*?)\]"
                         r"(?:,\s*gate:'(\w+)')?", blk):
        live = [x.strip().strip("'") for x in m.group(3).split(",")]
        spots.append({"id": m.group(1), "name": m.group(2),
                      "live": ["" if x == "null" else x for x in live],
                      "null": [x == "null" for x in live],
                      "gate": m.group(4) or ""})
    visits = []
    blk2 = re.search(r"var VISITS=\[(.*?)\n\];", js, re.S).group(1)
    for m in re.finditer(r"\['(\w+)',\s*(\d),'(.+?)',\s*([\w.]+)", blk2):
        visits.append((m.group(1), int(m.group(2)), m.group(3), m.group(4)))
    return spots, visits


def build_places():
    spots, visits = board_tables()
    extra = {}
    for loc, slot, who, pr in visits:
        extra.setdefault(loc, []).append((SLOT_NAME[slot], who, pr))
    rows = []
    for sp in spots:
        cells = []
        for i in range(4):
            if sp["null"][i]:
                cells.append('<span class="no">沒開</span>')
            elif sp["live"][i]:
                cells.append('<span class="yes">' + html.escape(DISPLAY.get(sp["live"][i], sp["live"][i])) + "</span>")
            else:
                cells.append('<span class="no">開著，可能沒人</span>')
        gate = FLAG_TEXT.get(sp["gate"], sp["gate"]) if sp["gate"] else "一開始就在"
        vis = "；".join(f"{s} {DISPLAY.get(w, w)}" + ("" if pr in ("1.00", "1") else f"（{pr}）")
                        for s, w, pr in extra.get(sp["id"], [])) or "—"
        rows.append("<tr><td>" + html.escape(sp["name"]) + "</td>" +
                    "".join(f"<td>{c}</td>" for c in cells) +
                    f'<td class="w">{html.escape(gate)}</td><td class="w">{html.escape(vis)}</td></tr>')
    body = f"""
<h1>地點與時段</h1>
<p class="lede">誰常駐在哪裡、什麼時候在、要什麼條件那個地方才會出現在板上。
括號裡的數字是他剛好也在的機率，去到第二或第三次就一定遇得到。</p>

<div class="box"><table>
<thead><tr><th>地點</th><th>上午</th><th>下午</th><th>晚上</th><th>深夜</th><th>怎麼開</th><th>誰會剛好也在</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>

<h2>兩件要知道的</h2>
<p><strong>「開著，可能沒人」跟「沒開」是兩件事。</strong>
一樓的晚上沒有常駐，管理員下班了，可是那正是那個穿西裝的唯一會出現的時段。
空手而回本來就是這一款的一部分。</p>
<p><strong>錄音間門口永遠進不去。</strong>那是刻意的。你會在騎樓那個門口被擋住，
而那件事會讓深夜在便利商店撞到他變成整款最好的一個瞬間。</p>
"""
    page("places.html", "地點與時段", body, "調查篇十二個地點的常駐、時段與開啟條件。")


# ── 五、支線與條件 ──────────────────────────────────────────
def build_threads():
    by_loc = {}
    for r in BOARD["rules"]:
        if not r.get("label"):
            continue
        by_loc.setdefault(r["dest"], []).append(r)
    blocks = []
    for loc in sorted(by_loc, key=lambda l: list(LOC_NAME).index(l) if l in LOC_NAME else 99):
        rows = []
        for r in sorted(by_loc[loc], key=lambda r: (min(r["slots"]), r.get("label"))):
            slots = "、".join(SLOT_NAME[i] for i in sorted(r["slots"]))
            if len(r["slots"]) == 4:
                slots = "任一時段"
            rows.append(f'<tr><td class="w">{html.escape(r["label"])}</td>'
                        f'<td>{slots}</td><td class="w">{html.escape(rule_conds(r))}</td></tr>')
        blocks.append(f"""<h2>{html.escape(LOC_NAME.get(loc, loc))}
<span class="tag">{len(rows)} 格</span></h2>
<div class="box"><table>
<thead><tr><th>那一格</th><th>時段</th><th>要什麼</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>""")
    body = f"""
<h1>支線與條件</h1>
<p class="lede">板上每一個地方能點的每一格，以及它要什麼條件才會出現。
全部從板子直接產，共 {len(BOARD['rules'])} 格。<strong>這一頁有雷。</strong></p>
<details class="spoiler" open><summary>展開全部條件</summary>
{''.join(blocks)}
</details>
"""
    page("threads.html", "支線與條件", body, "調查篇每一格的觸發條件，從板子直接產生。")


# ── 六、完整攻略 ────────────────────────────────────────────
def build_walkthrough(route_file):
    rows, day, slot, place = [], None, None, None
    for ln in pathlib.Path(route_file).read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^=== 板 第 (\d+) 天 ・ (上午|下午|晚上|深夜)", ln)
        if m:
            day, slot, place = m.group(1), m.group(2), None
            continue
        m = re.match(r"^→ 去 (\S+)", ln)
        if m:
            place = m.group(1)
            continue
        m = re.search(r"→ 選「(.+?)」", ln)
        if m and place:
            rows.append((day, slot, place, m.group(1)))
            place = None
            continue
        # 打開包包挑東西也是一步，而且不挑就接不下去（失物箱、諾亞信箱、放錄音給管理員聽）。
        # 它不是選單那一格，是那一格演到一半跳出來的，所以要另外抓。
        m = re.search(r"\[背包\] 挑「(.+?)」", ln)
        if m and rows:
            d0, s0, p0, c0 = rows[-1]
            rows.append((d0, s0, p0, f"（打開包包，挑「{m.group(1)}」）"))
    out, last = [], None
    for d, s_, p, c in rows:
        head = f'<tr><td rowspan="0">第 {d} 天</td>' if d != last else "<tr><td></td>"
        last = d
        out.append(f'<tr><td>{"第 " + d + " 天" if head.startswith("<tr><td r") else ""}</td>'
                   f"<td>{s_}</td><td>{html.escape(p)}</td>"
                   f'<td class="w">{html.escape(c)}</td></tr>')
    body = f"""
<h1>完整攻略</h1>
<p class="lede"><strong>整頁有雷。</strong>底下這條路線是真的跑完的一輪，
不是推算的：六條線全部走到，守則本第一頁六個名字填滿，
最後那一頁六行註解也全滿。共 {len(rows)} 步。</p>

<h2>先記六件事</h2>
<div class="box"><table>
<thead><tr><th>要點</th><th>為什麼</th></tr></thead>
<tbody>
<tr><td class="w">深夜留給那條街</td><td class="w">開洗衣店與洗衣店第一晚都不限時段，晚上做就好。
十個深夜要留給深夜才有的人。</td></tr>
<tr><td class="w">第三天下午去騎樓那個門口</td><td class="w">跟著他進電梯那一場裡選問 0x，
十四樓當天就開。靠別的路要等到第七天以後，後面全部來不及。</td></tr>
<tr><td class="w">工作室先問守則本</td><td class="w">工作室有三個問題，只有守則本那一格會把信任推到三。
另外兩個問完再問，不然兩個晚上就沒了。</td></tr>
<tr><td class="w">不要對深夜那個人按錄音</td><td class="w">他會轉身，那一晚不算。
可以錄的是店員、老闆、諾亞、保全。</td></tr>
<tr><td class="w">有三格會跳出包包</td><td class="w">失物箱、把信箱那一頁拿給諾亞看、
把保全那一段放給管理員聽。演到一半會跳出包包，要挑指定那一件才接得下去
（前兩格是守則本，第三格是錄音・保全）。不挑的話會再問一次，兩次都不挑就回板，
那一場下次還會出現。</td></tr>
<tr><td class="w">六個名字要自己填</td><td class="w">六個 ID 都抄到之後，守則本會多一個
「第一頁」分頁。名單那一頁的註解跟第一頁的名字是兩回事，兩邊都要做才是完整結局。</td></tr>
</tbody></table></div>

<details class="spoiler" open><summary>逐日路線（{len(rows)} 步）</summary>
<div class="box"><table>
<thead><tr><th>天</th><th>時段</th><th>去哪裡</th><th>做什麼</th></tr></thead>
<tbody>{''.join(out)}</tbody></table></div>
</details>

<p>第十四天上午自動收尾，不用選。走完這一條的人，最後那一頁六行都會有她自己問到的東西。</p>
"""
    page("walkthrough.html", "完整攻略", body, "調查篇的逐日路線，取自真的跑完的一輪。")


# ── 七、名詞表 ──────────────────────────────────────────────
def build_glossary():
    seen = {}
    for r in BOARD["rules"]:
        for c in r["conds"]:
            seen.setdefault(c["variable"], 0)
            seen[c["variable"]] += 1
    rows = []
    for v, n in sorted(seen.items(), key=lambda kv: -kv[1]):
        if v in ("dest", "pick", "slot"):
            continue
        desc = FLAG_TEXT.get(v) or (VAR_TEXT.get(v, "").format(v="N") if v in VAR_TEXT else "")
        rows.append(f'<tr><td><code>{html.escape(v)}</code></td>'
                    f'<td class="w">{html.escape(desc or "—")}</td><td>{n}</td></tr>')
    body = f"""
<h1>名詞表</h1>
<p class="lede">板上真的被拿來當條件的旗標與計數，共 {len(rows)} 個。
給想拆解這一款怎麼運作的人。<strong>有雷。</strong></p>
<details class="spoiler"><summary>展開</summary>
<div class="box"><table>
<thead><tr><th>名字</th><th>意思</th><th>被幾格讀到</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
</details>
"""
    page("glossary.html", "名詞表", body, "調查篇的變數與旗標一覽。")


def build_stub(fn, title, note):
    body = f"""<h1>{html.escape(title)}</h1>
<p class="lede">{html.escape(note)}</p>
<p>這一頁還沒有做。</p>"""
    page(fn, title, body, note)


def main():
    OUT.mkdir(exist_ok=True)
    build_index()
    build_canon()
    build_people()
    build_places()
    build_threads()
    route = ROOT / "design/調查篇-通關路線.txt"
    if route.exists():
        build_walkthrough(route)
    else:
        build_stub("walkthrough.html", "完整攻略", "還沒有把跑通的那一輪存進 design/調查篇-通關路線.txt。")
    build_glossary()
    print(f"寫出 {OUT}/ 共 {len(PAGES)} 頁")
    print(f"  規則 {len(BOARD['rules'])} 條、變數 {len(BOARD['variables'])} 個、卡片 {len(BOARD['nodes'])} 張")


if __name__ == "__main__":
    main()
