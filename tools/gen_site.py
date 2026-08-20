#!/usr/bin/env python3
"""從 project.json 生說明書＋攻略站(docs/index.html)。

跟 gen_docs.py 同一個原則:手寫的攻略一定會過期。變數表、每天的選項與後果、
結局條件,全部從專案讀出來 —— 劇本改了重跑就同步。

配色是從遊戲美術取出來的,不是憑空配的:
  黑洞先生的身體  #14142a 靛藍黑
  格莉奇          #c8c8f0 淡紫藍
  房間夜景的燈    #3c2814 暖褐 → 提亮成 #d9a05b
劇透用 <details> 收起來,標題沿用遊戲裡「交給你保管」的說法 ——
這份攻略替你留著,你要回來拿才看得到。
"""
import html, json, pathlib

P = json.load(open(pathlib.Path.home() / "glitch-vn/backup/project.json"))
DAYS = sorted([b for b in P["boards"] if b["id"].startswith("board-day")],
              key=lambda b: int(b["id"].replace("board-day", "")))
V = {v["name"]: v for v in P["variables"]}
E = html.escape
OP = {"eq": "＝", "neq": "≠", "gt": "＞", "gte": "≥", "lt": "＜", "lte": "≤"}
KIND = {"set": "設為", "add": "", "toggle": "翻轉", "random": "隨機"}


def zh(t):
    """對外中文用全形標點。變數說明是我當初寫給自己看的開發筆記,半形逗號分號
    直接搬上站不行。只在中日文字之間換,免得動到 keep/feed/give 這種英文列舉。"""
    import re
    t = str(t or "")
    for half, full in ((",", "，"), (";", "；"), (":", "："), ("(", "（"), (")", "）")):
        t = re.sub(rf"(?<=[\u4e00-\u9fff]){re.escape(half)}", full, t)
        t = re.sub(rf"{re.escape(half)}(?=[\u4e00-\u9fff])", full, t)
    return t


def op_text(op):
    k, val = op["kind"], op.get("value")
    if k == "add":
        n = float(val or 0)
        return f'{op["variable"]} {"+" if n > 0 else ""}{val}'
    if k == "set":
        return f'{op["variable"]} = {val}'
    if k == "random":
        return f'{op["variable"]} 隨機 {op.get("min")}–{op.get("max")}'
    return f'{op["variable"]} {KIND.get(k, k)}'


def effects(board, node_id, handle):
    """這個出口往下會改動哪些變數，依條件分組。

    不分組的話同一個條件會在每個變數前面重印一次，讀起來像雜訊。
    """
    groups = {}
    for e in board["edges"]:
        if e["source"] != node_id or e.get("sourceHandle") != handle:
            continue
        tgt = next((m for m in board["nodes"] if m["id"] == e["target"]), None)
        if not tgt:
            continue
        c = (e.get("data") or {}).get("condition")
        key = (f'{c["variable"]} {OP.get(c["op"], c["op"])} {c["value"]} 時' if c else "")
        seen = groups.setdefault(key, [])
        for op in tgt["data"].get("variableOps") or []:
            t = op_text(op)
            if t not in seen:
                seen.append(t)
    return [(k, v) for k, v in groups.items() if v]


def var_rows():
    written, read = {}, {}
    for b in P["boards"]:
        tag = b["name"].split("・")[0]
        for n in b["nodes"]:
            for op in n["data"].get("variableOps") or []:
                written.setdefault(op["variable"], set()).add(tag)
            if n["data"].get("inputVariable"):
                written.setdefault(n["data"]["inputVariable"], set()).add(tag)
        for e in b["edges"]:
            c = (e.get("data") or {}).get("condition")
            if c:
                read.setdefault(c["variable"], set()).add(tag)
    rows = []
    for name, v in V.items():
        w, r = written.get(name, set()), read.get(name, set())
        days = sorted((w | r) - {"素材庫"}, key=lambda t: (len(t), t))
        if not days:      # 只有素材庫在用 —— 那塊板不是入口,玩家看不到
            continue
        rows.append((name, zh(v.get("label")), zh(v.get("description")),
                     v.get("defaultValue"), days))
    return rows


# ── 每天的資料 ──────────────────────────────────────────
def day_data(b):
    d = {"num": int(b["id"].replace("board-day", "")), "name": b["name"],
         "desc": b.get("description", ""), "cards": len(b["nodes"]),
         "choices": [], "inputs": [], "branches": []}
    seg = ""
    for n in b["nodes"]:
        dd = n["data"]
        if dd.get("type") == "scene":
            t = dd.get("title", "")
            seg = "早" if "早" in t or "清晨" in t else "中" if "中午" in t else "晚" if ("傍晚" in t or "夜" in t) else seg
        if dd.get("type") == "choice":
            opts = []
            for i, c in enumerate(dd.get("choices") or []):
                label = c if isinstance(c, str) else c.get("text", "")
                opts.append((label, effects(b, n["id"], f"choice-{i}")))
            d["choices"].append((seg, dd.get("text", "").split("\n")[0], opts))
        if dd.get("type") == "input":
            d["inputs"].append((seg, dd.get("inputVariable"), dd.get("text", "").split("\n")[0]))
    for e in b["edges"]:
        c = (e.get("data") or {}).get("condition")
        if not c or (e.get("sourceHandle") or "").startswith("choice-"):
            continue
        tgt = next((m for m in b["nodes"] if m["id"] == e["target"]), None)
        d["branches"].append((c["variable"], OP.get(c["op"], c["op"]), c["value"],
                              (tgt["data"].get("title") if tgt else e["target"])))
    return d


DD = [day_data(b) for b in DAYS]
END = next((d for d in DD if d["num"] == 7), None)
TOTAL_CARDS = sum(len(b["nodes"]) for b in DAYS)
TOTAL_EDGES = sum(len(b["edges"]) for b in DAYS)

# ── HTML ────────────────────────────────────────────────
CSS = """
:root{
  /* 從遊戲美術取的色。黑洞先生 #14142a、格莉奇 #c8c8f0、房間夜燈 #3c2814 */
  --void:#14142a; --void-2:#1e1e38; --void-3:#2a2a4a;
  --glitch:#5b5bb8; --glitch-soft:#7a7ad0; --lamp:#a86a28;
  --ground:#eceaf4; --surface:#ffffff; --sunk:#e2dfee;
  --line:#cdc9de; --text:#20203a; --muted:#5c5878; --faint:#88849e;
  --shadow:0 1px 2px rgba(20,20,42,.05),0 8px 24px -12px rgba(20,20,42,.18);
  --r:3px;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --ground:#101024; --surface:#191932; --sunk:#0b0b1c;
  --line:#2e2e50; --text:#dedbec; --muted:#9a96b8; --faint:#6e6a8c;
  --glitch:#a8a8e8; --glitch-soft:#8b8bd4; --lamp:#d9a05b;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.7);
}}
:root[data-theme="dark"]{
  --ground:#101024; --surface:#191932; --sunk:#0b0b1c;
  --line:#2e2e50; --text:#dedbec; --muted:#9a96b8; --faint:#6e6a8c;
  --glitch:#a8a8e8; --glitch-soft:#8b8bd4; --lamp:#d9a05b;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.7);
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--text);
  font-family:"Noto Sans TC",system-ui,sans-serif;
  font-size:16px; line-height:1.85; -webkit-font-smoothing:antialiased;
}
.mono{font-family:"DM Mono","SFMono-Regular",Menlo,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:940px;margin:0 auto;padding:0 24px}
h1,h2,h3{font-family:"Noto Serif TC",Georgia,serif;text-wrap:balance;margin:0}

/* ── 開場 ── */
.hero{padding:88px 0 56px;border-bottom:1px solid var(--line)}
.boot{
  font-family:"DM Mono",monospace;font-size:12px;letter-spacing:.16em;
  color:var(--glitch);text-transform:uppercase;margin-bottom:22px;
}
.hero h1{font-size:clamp(34px,6vw,58px);line-height:1.16;font-weight:600;letter-spacing:.02em}
.hero .sub{margin-top:20px;max-width:36em;color:var(--muted);font-size:17px}

/* 記憶體條:遊戲裡真的有這個狀態列,不是裝飾 */
.slots{display:flex;gap:5px;align-items:center;margin-top:34px;flex-wrap:wrap}
.slot{
  width:52px;height:9px;background:var(--sunk);
  border:1px solid var(--line);border-radius:1px;
}
.slot.on{background:var(--glitch);border-color:var(--glitch)}
.slots .cap{
  font-family:"DM Mono",monospace;font-size:11px;color:var(--faint);
  margin-left:10px;letter-spacing:.1em;
}

/* ── 區塊 ── */
section{padding:56px 0;border-bottom:1px solid var(--line)}
section:last-of-type{border-bottom:0}
.eyebrow{
  font-family:"Noto Sans TC",sans-serif;font-size:12px;letter-spacing:.14em;
  color:var(--faint);margin-bottom:12px;
}
h2{font-size:26px;font-weight:600;letter-spacing:.02em}
section > p{max-width:40em;color:var(--muted);margin:16px 0 0}
section > p strong{color:var(--text);font-weight:500}

/* ── 三個去處 ── */
.routes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin-top:30px}
.route{
  background:var(--surface);border:1px solid var(--line);border-radius:var(--r);
  padding:22px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:10px;
}
.route h3{font-size:17px;font-weight:600}
.route .who{font-family:"DM Mono",monospace;font-size:11px;letter-spacing:.16em;color:var(--glitch);text-transform:uppercase}
.route p{margin:0;font-size:14.5px;color:var(--muted);line-height:1.75}
.route .cost{
  margin-top:auto;padding-top:12px;border-top:1px dashed var(--line);
  font-size:13px;color:var(--lamp);
}

/* ── 一天 ── */
.segs{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:0;margin-top:30px;
  border:1px solid var(--line);border-radius:var(--r);overflow:hidden;background:var(--surface)}
.seg{padding:22px;border-right:1px solid var(--line)}
.seg:last-child{border-right:0}
.seg .t{font-family:"Noto Serif TC",serif;font-size:19px;margin-bottom:8px}
.seg p{margin:0;font-size:14px;color:var(--muted);line-height:1.75}

/* ── 七天 ── */
.days{display:flex;flex-direction:column;gap:1px;margin-top:30px;background:var(--line);
  border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.day{background:var(--surface);padding:20px 22px;display:grid;
  grid-template-columns:44px 1fr auto;gap:18px;align-items:baseline}
.day .n{font-family:"DM Mono",monospace;font-size:13px;color:var(--glitch);letter-spacing:.08em}
.day .nm{font-family:"Noto Serif TC",serif;font-size:17px}
.day .d{grid-column:2;font-size:14px;color:var(--muted);line-height:1.7;margin-top:4px}
.day .c{font-family:"DM Mono",monospace;font-size:12px;color:var(--faint);white-space:nowrap}

/* ── 表 ── */
.tw{overflow-x:auto;margin-top:26px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:640px}
th,td{text-align:left;padding:11px 16px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:"DM Mono",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
   color:var(--faint);font-weight:400;background:var(--sunk);white-space:nowrap}
tr:last-child td{border-bottom:0}
td.v{font-family:"DM Mono",monospace;color:var(--glitch);white-space:nowrap}
td.dv{font-family:"DM Mono",monospace;color:var(--muted);white-space:nowrap}
td.w{color:var(--faint);font-size:12.5px}
.tag{display:inline-block;font-family:"DM Mono",monospace;font-size:11px;
  padding:1px 7px;border:1px solid var(--line);border-radius:2px;color:var(--muted);margin:0 3px 3px 0}

/* ── 劇透閘 ── */
details{
  margin-top:16px;background:var(--surface);border:1px solid var(--line);
  border-radius:var(--r);overflow:hidden;
}
summary{
  cursor:pointer;padding:16px 20px;list-style:none;display:flex;
  align-items:center;gap:12px;font-size:15px;
}
summary::-webkit-details-marker{display:none}
summary::before{
  content:"＋";font-family:"DM Mono",monospace;color:var(--glitch);
  font-size:15px;line-height:1;flex:none;
}
details[open] summary::before{content:"－"}
details[open] summary{border-bottom:1px solid var(--line)}
summary:hover{background:var(--sunk)}
summary:focus-visible{outline:2px solid var(--glitch);outline-offset:-2px}
summary .hint{margin-left:auto;font-family:"DM Mono",monospace;font-size:11px;
  color:var(--faint);letter-spacing:.1em}
.body{padding:20px}
.body > *:first-child{margin-top:0}
.body p{color:var(--muted);font-size:14.5px;max-width:40em}

.note{margin:16px 0 0;padding:12px 16px;border-left:2px solid var(--glitch);
  background:var(--sunk);font-size:13.5px;color:var(--muted);line-height:1.75;border-radius:0 var(--r) var(--r) 0}
.ch{margin:18px 0 0;padding:16px 18px;background:var(--sunk);border-radius:var(--r)}
.ch .q{font-size:14.5px;margin-bottom:12px}
.ch .q em{font-style:normal;font-size:12px;color:var(--glitch);margin-right:9px;
  border:1px solid var(--line);border-radius:2px;padding:1px 7px}
.ch .q .rep{font-family:"DM Mono",monospace;font-size:11px;color:var(--faint);margin-left:9px}
.ch ol{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:9px}
.ch li{font-size:14px}
.ch .fx{font-family:"DM Mono",monospace;font-size:11.5px;color:var(--faint);
  display:block;margin-top:3px;line-height:1.6}

footer{padding:44px 0 72px;color:var(--faint);font-size:13px}
footer a{color:var(--glitch)}
@media (prefers-reduced-motion:no-preference){
  .slot{transition:background .5s ease,border-color .5s ease}
}
@media (max-width:640px){
  .hero{padding:56px 0 40px}
  .seg{border-right:0;border-bottom:1px solid var(--line)}
  .seg:last-child{border-bottom:0}
  .day{grid-template-columns:38px 1fr;gap:12px}
  .day .c{grid-column:2;white-space:normal}
}
"""


def gate(title, hint, inner):
    return (f'<details><summary>{E(title)}<span class="hint">{E(hint)}</span></summary>'
            f'<div class="body">{inner}</div></details>')


def choice_block(seg, q, opts, times=1):
    lis = []
    for label, fx in opts:
        lines = []
        for cond, ops in fx:
            body = "　".join(ops)
            lines.append(f'<span class="fx">{E(("" if not cond else cond + "：") + body)}</span>')
        lis.append(f'<li>{E(label)}{"".join(lines)}</li>')
    rep = f'<span class="rep">×{times}</span>' if times > 1 else ""
    return (f'<div class="ch"><div class="q"><em>{E(seg)}</em>{E(q)}{rep}</div>'
            f'<ol>{"".join(lis)}</ol></div>')


parts = []
parts.append(f'''<div class="wrap"><header class="hero">
<div class="boot"><a href="index.html" style="color:inherit">← 製作記錄</a>　逼——嗶！　系統讀取中</div>
<h1>格莉奇與黑洞先生<br>使用說明</h1>
<p class="sub">一天一圈的視覺小說。她的記憶體只有 4KB，每天睡醒清空。
你是她的外接記憶體——她裝不下的東西可以交給你保管，但你要回來，她才拿得回去。</p>
<div class="slots">
{"".join(f'<div class="slot{" on" if i == 0 else ""}"></div>' for i in range(4))}
<span class="cap">記憶體 1／4　你的名字放在第一格</span>
</div>
</header>''')

parts.append(f'''<section>
<div class="eyebrow">一天的形狀</div>
<h2>每一天都是同一個形狀</h2>
<p>七天，每天走一樣的三段。變的是她在早上發現什麼、你在中午替她決定什麼，
還有他晚上回來時<strong>會不會提到</strong>。</p>
<div class="segs">
<div class="seg"><div class="t">早</div><p>她開機。發現一件她不記得自己做過的事。
每天打斷開機流程的方式都不一樣。</p></div>
<div class="seg"><div class="t">中</div><p>他去上班，只剩她跟你。
今天那件事要放哪裡，你決定。</p></div>
<div class="seg"><div class="t">晚</div><p>他回來，對你中午的選擇有反應。
她寫一句守則給明天的自己，然後存檔。</p></div>
</div>
</section>''')

parts.append("""<section>
<div class="eyebrow">記憶體</div>
<h2>四格，而且看得見</h2>
<p>她一次只裝得下四件事。<strong>四格的內容你看得到</strong>——選項與台詞會把它們唸出來，
所以你隨時知道自己替她留了什麼。</p>
<p>滿了不會問你要丟哪一格。<strong>最舊的那一件自己掉出去</strong>，她沒得挑，你也擋不住，
而且她連它存在過都不會知道。</p>
<p>一件線索單獨看不出東西。<strong>兩件同時還在她腦子裡，她才拼得出來</strong>——
而她一次只裝得下四件。所以「哪兩件同時還在」，就是你整天在決定的事。</p>
<p>拼出來的東西會變成她那天晚上寫進守則的那句話。隔天早上她會唸出來，然後照做。
<strong>那是唯一活得過一個晚上的東西。</strong></p>
</section>""")

parts.append('''<section>
<div class="eyebrow">核心選擇</div>
<h2>三個去處</h2>
<p>每天中午只有一件事要決定，而三個去處<strong>沒有一個是免費的</strong>。</p>
<div class="routes">
<div class="route"><div class="who">留在她這裡</div><h3>她自己記著</h3>
<p>今天她記得。明天睡醒清空，什麼都不剩。</p>
<div class="cost">4KB 只有四格。滿了再留，會擠掉一件她不知道是什麼的舊事。</div></div>
<div class="route"><div class="who">給黑洞先生吃</div><h3>他吃掉</h3>
<p>東西消失，他長回一隻腳，門邊那疊沒人穿的短靴會少一雙。</p>
<div class="cost">他一天只吃得下一件。這禮拜餵過他幾次，最後一天會結帳。</div></div>
<div class="route"><div class="who">交給你保管</div><h3>你替她留著</h3>
<p>留得住。她不會記得自己交出去過。</p>
<div class="cost">你要回來，她才拿得回去。你不回來，那東西一樣不見。</div></div>
</div>
</section>''')

parts.append(f'''<section>
<div class="eyebrow">存檔</div>
<h2>存檔是玩法，不是功能</h2>
<p>她沒有手幫你按。<strong>你不存檔，第二天她不認識你</strong>——你的名字、你昨天說的話，
她那裡一格都沒有。存了，她開機會比較快，而且會叫你的名字。</p>
<p>這是這個遊戲唯一一個「介面上的動作」直接變成劇情的地方。</p>
</section>''')

# 七天
day_rows = []
for d in DD:
    day_rows.append(f'''<div class="day">
<span class="n">DAY {d["num"]}</span>
<span class="nm">{E(d["name"].split("・")[-1])}</span>
<span class="c">{d["cards"]} 張卡</span>
<div class="d">{E(zh(d["desc"].replace("**", "")))}</div>
</div>''')
inner = []
for d in DD:
    blocks = [f'<p>{E(zh(d["desc"].replace("**", "")))}</p>']
    # Day 4 的事件池有六個事件共用同一組選項,逐張印出來是六份一模一樣的雜訊。
    # 只有去重變數(usedPlant/usedReceipt…)不同,那個對玩家沒有意義,所以收成一張。
    merged = []
    for seg, q, opts in d["choices"]:
        sig = (seg, q, tuple(lbl for lbl, _ in opts))
        hit = next((m for m in merged if m[0] == sig), None)
        if hit:
            hit[1] += 1
        else:
            merged.append([sig, 1, (seg, q, opts)])
    for _, times, (seg, q, opts) in merged:
        blocks.append(choice_block(seg, q, opts, times))
    # todayEvent／used* 是事件池的內部管線(抽號碼、去重),印出來是
    # 「usedPicture = 1 → 事件2」這種對玩家沒有意義的東西。濾掉,換一句說明。
    pool = [b for b in d["branches"] if b[0] == "todayEvent" or b[0].startswith("used")]
    real = [b for b in d["branches"] if b not in pool]
    seen, uniq = set(), []
    for v, op, val, t in real:
        k = (v, op, str(val))
        if k not in seen:
            seen.add(k); uniq.append((v, op, val, t))
    if pool:
        n = len({b[2] for b in pool if b[0] == "todayEvent"})
        blocks.append(f'<p class="note">中午是 {n} 選一的事件池，抽到已經出現過的會換下一個。'
                      f'三個去處對每個事件都一樣，差別只在她發現的是什麼。</p>')
    if uniq:
        rows = "".join(f'<tr><td class="v">{E(v)} {E(op)} {E(str(val))}</td><td>{E(str(t or ""))}</td></tr>'
                       for v, op, val, t in uniq)
        blocks.append(f'<div class="tw"><table><thead><tr><th>這個狀態</th><th>會讓你看到</th></tr></thead>'
                      f'<tbody>{rows}</tbody></table></div>')
    inner.append(gate(f'Day {d["num"]}・{d["name"].split("・")[-1]}',
                      f'{len(d["choices"])} 個選擇', "".join(blocks)))

parts.append(f'''<section>
<div class="eyebrow">七天</div>
<h2>這一圈長什麼樣</h2>
<div class="days">{"".join(day_rows)}</div>
<p style="margin-top:26px">底下是每天的選項與它們實際改動的東西。
<strong>會劇透</strong>，所以收起來了——跟遊戲裡一樣，你要自己伸手去拿。</p>
{"".join(inner)}
</section>''')

# 變數表
rows = []
for name, label, desc, dv, days in var_rows():
    tags = "".join(f'<span class="tag">{E(t)}</span>' for t in days)
    rows.append(f'<tr><td class="v">{E(name)}</td><td>{E(label)}'
                f'{("<br><span style=\'color:var(--faint);font-size:12.5px\'>" + E(desc) + "</span>") if desc else ""}</td>'
                f'<td class="dv">{E(str(dv))}</td><td class="w">{tags}</td></tr>')
parts.append(f'''<section>
<div class="eyebrow">機制</div>
<h2>遊戲記得的每一件事</h2>
<p>這些變數跨天累積，也跨章節——它們是專案層級的，不是單日的。
下面這張表是從遊戲檔案讀出來的，不是手寫的。</p>
<div class="tw"><table>
<thead><tr><th>變數</th><th>它記什麼</th><th>初始</th><th>哪幾天會動它</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
</section>''')

# 結局
end_inner = ['<p>最後一天的結局由兩件事決定：中午你把那塊麵包放到哪裡，'
             '還有<strong>這一整個禮拜你餵過他幾次</strong>。</p>']
if END:
    for seg, q, opts in END["choices"]:
        end_inner.append(choice_block(seg, q, opts))
end_inner.append('''<p style="margin-top:20px">「留給黑洞先生」這條路會再分兩種。
他一天只吃得下一件——前六天你每餵他一次，就花掉一次他的胃。
<strong>帳單開在最後一天</strong>：餵過他的玩家，會看到他吃不下那塊她為他烤的麵包。</p>''')
parts.append(f'''<section>
<div class="eyebrow">結局</div>
<h2>四個結局</h2>
<p>三條路，其中一條依你這禮拜的行為再分兩種。</p>
{gate("結局條件與觸發方式", "重度劇透", "".join(end_inner))}
{gate("二週目", "破關後再看", """
<p>這個平台的變數新開一場就回預設，沒有內建的二週目。所以這個遊戲不靠平台——
<strong>你本人就是存檔</strong>。</p>
<p>開場會問你以前來過沒有。說來過，它會請你寫一句「這個房子裡有人說過、
而她記不住的話」。答對了，最後一天會多一段：她還是不記得你，
但這間房子裡有一個永遠不會忘的人。</p>
<p>暗號都是遊戲裡真的出現過、而且猜不到的句子。標點有沒有打都收。</p>""")}
</section>''')

parts.append(f'''<footer>
<p>這份說明由 <span class="mono">tools/gen_site.py</span> 從遊戲檔案生成，
不是手寫的——劇本改了重跑一次就同步。
目前收錄 {len(DAYS)} 天、{TOTAL_CARDS} 張卡、{TOTAL_EDGES} 條連線、{len(var_rows())} 個變數。</p>
<p>《格莉奇與黑洞先生》　MIT　林亞澤</p>
</footer></div>''')

HTML = f'''<title>格莉奇與黑洞先生使用說明</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500&family=Noto+Serif+TC:wght@500;600&display=swap">
<style>{CSS}</style>
{"".join(parts)}
'''

out = pathlib.Path.home() / "glitch-vn/docs/manual.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(HTML, encoding="utf-8")
print(f"寫好 {out}（{len(HTML) // 1024} KB，{len(DAYS)} 天、{len(var_rows())} 個變數）")
