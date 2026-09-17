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
import names as NAMES        # 旁白不講名字
import clear_stage as CS     # ghost_stage()
STAGE_CLEAR = {"inv-457", "inv-458", "inv-459", "inv-460"}   # 結局段：諾亞「門幫我帶一下」之後的四張

_R2 = "https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/"
_MAIN = _R2 + "project-bec1644c-0dfe-4447-86c0-0c592e2f939f/"      # 正篇專案
_INV = _R2 + "project-d2fea918-c0eb-4ab6-aefb-2fe9a75dc7c4/"       # 調查篇專案
# 深夜背景掛到正篇專案的圖（一樓／頂樓／斑比工作室；build.py 的 BG 表深夜欄寫了本機沒有的名字，
# 查找落到正篇）→ 換成調查篇自己的傍晚那張。2026-09-17 他在調查板與斑比深夜對話抓到。
NIGHT_FIX = {
    _MAIN + "1787369280354_bg-apartment-hall.jpg": _INV + "1789173031125_bg-lobby-evening.png",
    _MAIN + "1787369384500_bg-noah-shop.jpg":      _INV + "1789173061225_bg-roof-evening.png",
    _MAIN + "1787369297485_bg-bambi-studio.jpg":   _INV + "1789173211426_bg-studio-evening.png",
}

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


# 遊樂園照樣吃時段（board.html start() 那一行，改了要兩邊一起改）。
# 2026-09-17 曾改成不吃，作者說原設計就是要吃，改回來；線上那張卡若還是「不吃」那版，換回去。
PARK_OLD = "  if(values.dest){ if(values.dest!=='park') advance(); setVar('dest',''); setVar('here',''); }"
PARK_NEW = "  if(values.dest){ advance(); setVar('dest',''); setVar('here',''); }"


# 劇情模式在軌道目的地訪客一律在場（board.html whoIsThere()，改了要兩邊一起改）。
# 2026-09-17：第 5 天深夜鐵塔 0.25 沒骰到，選單全放行，後面整條走歪。
VIS_OLD_A = "  var out=[], s=null, i, m=triesMap(), dirty=false;\n  for(i=0;i<SPOTS.length;i++) if(SPOTS[i].id===spotId) s=SPOTS[i];"
VIS_NEW_A = ("  var out=[], s=null, i, m=triesMap(), dirty=false;\n"
             "  var forced=false;\n"
             "  if(String(values.mode||'free')==='story'){ var rw=walkMap()[num(values.day,1)+','+slot]; forced=!!(rw && rw.loc===spotId); }\n"
             "  for(i=0;i<SPOTS.length;i++) if(SPOTS[i].id===spotId) s=SPOTS[i];")
VIS_OLD_B = "    if(Math.random()<pr || (pity>0 && c>=pity)){ out.push(v[2]); m[key]=0; }"
VIS_NEW_B = "    if(forced || Math.random()<pr || (pity>0 && c>=pity)){ out.push(v[2]); m[key]=0; }"


# 調查板換成真的細紋軟木貼圖（2026-09-17 作者給參考圖；art/board-cork.webp 已上傳到媒體庫）。
# board.html 同一段改了要兩邊一起改；push.py 整包推時是用 /*@@CORK@@*/ 灌網址，這裡直接寫死。
CORK_URL = _INV + "1789638515611_board-cork.webp"
CORK_OLD_SKY = "var SKY=[['#42352c','#2c231d'],['#463629','#2e241c'],['#33291f','#221b15'],['#2a231c','#191410']];\n\n// 地點"
CORK_NEW_SKY = ("var SKY=[['#42352c','#2c231d'],['#463629','#2e241c'],['#33291f','#221b15'],['#2a231c','#191410']];\n"
                "var CORK = " + json.dumps(CORK_URL) + ";\n"
                "var SKY_TEX=[['#c6a687','#a68870'],['#c2a283','#a3856c'],['#957a63','#77604d'],['#6e5644','#574334']];\n\n// 地點")
CORK_OLD_PAINT = ("  var x=c.getContext('2d'), W=c.width, H=c.height;\n"
                  "  var g=x.createLinearGradient(0,0,W*0.4,H); g.addColorStop(0,a); g.addColorStop(1,b);")
CORK_NEW_PAINT = ("  var x=c.getContext('2d'), W=c.width, H=c.height;\n"
                  "  if(CORK){\n"
                  "    var sk=document.getElementById('sky'); sk.className='sky tex';\n"
                  "    if(sk.style.backgroundImage.indexOf(CORK)<0) sk.style.backgroundImage='url(\"'+CORK+'\")';\n"
                  "    var gt=x.createLinearGradient(0,0,W*0.4,H); gt.addColorStop(0,a); gt.addColorStop(1,b);\n"
                  "    x.fillStyle=gt; x.fillRect(0,0,W,H);\n"
                  "    var vt=x.createRadialGradient(W/2,H/2,Math.min(W,H)*0.35,W/2,H/2,Math.max(W,H)*0.75);\n"
                  "    vt.addColorStop(0,'rgba(60,36,16,0)'); vt.addColorStop(1,'rgba(60,36,16,.22)');\n"
                  "    x.fillStyle=vt; x.fillRect(0,0,W,H);\n"
                  "    return;\n"
                  "  }\n"
                  "  var g=x.createLinearGradient(0,0,W*0.4,H); g.addColorStop(0,a); g.addColorStop(1,b);")
CORK_OLD_APPLY = "  window.__sky=SKY[slot]; paintCork(SKY[slot][0], SKY[slot][1]);"
CORK_NEW_APPLY = "  window.__sky=(CORK?SKY_TEX:SKY)[slot]; paintCork(window.__sky[0], window.__sky[1]);"
TEX_OLD = "var SKY_TEX=[['#f6e4cd','#e7cbad'],['#f7dfc0','#e5c39e'],['#c6a687','#a68870'],['#957a63','#77604d']];"
TEX_NEW = "var SKY_TEX=[['#c6a687','#a68870'],['#c2a283','#a3856c'],['#957a63','#77604d'],['#6e5644','#574334']];"
CORK_OLD_CSS = ".sky canvas{position:absolute;inset:0;width:100%;height:100%;display:block}\n.sky::after"
CORK_NEW_CSS = (".sky canvas{position:absolute;inset:0;width:100%;height:100%;display:block}\n"
                ".sky.tex{background-position:center;background-size:cover}\n.sky.tex canvas{mix-blend-mode:multiply}\n.sky::after")


# 拍立得縮圖 atlas＋街廓改四條線（2026-09-17 作者要求；board.html 同一段改了要兩邊一起改）。
_ATLAS = json.loads((HERE.parent.parent / "art/board-atlas.json").read_text(encoding="utf-8"))
_ATLAS["url"] = _INV + "1789656782122_board-atlas.webp"
ATLAS_OLD = "var PHOTOS = "
ATLAS_NEW = "var ATLAS = " + json.dumps(_ATLAS, ensure_ascii=False) + ";\nvar PHOTOS = "
PHOTO_OLD = """    if(been && PHOTOS[s.id]){
      var ph=document.createElement('span'); ph.className='photo';
      var url=PHOTOS[s.id][slot===3?'night':slot===2?'evening':'day']||PHOTOS[s.id].day||PHOTOS[s.id].night;
      if(url) ph.style.backgroundImage='url("'+url+'")'; else ph.className='photo empty';
      b.appendChild(ph);
    } else { b.className+=' note'; }"""
PHOTO_NEW = """    if(been && ((ATLAS&&ATLAS.map[s.id])||PHOTOS[s.id])){
      var ph=document.createElement('span'); ph.className='photo';
      var tk=slot===3?'night':slot===2?'evening':'day';
      if(ATLAS&&ATLAS.map[s.id]){
        var c=ATLAS.map[s.id][tk]||ATLAS.map[s.id].day||ATLAS.map[s.id].night;
        if(c){ ph.style.backgroundImage='url("'+ATLAS.url+'")';
               ph.style.backgroundSize=(ATLAS.cols*100)+'% '+(ATLAS.rows*100)+'%';
               ph.style.backgroundPosition=(c[0]/(ATLAS.cols-1)*100)+'% '+(c[1]/(ATLAS.rows-1)*100)+'%'; }
        else ph.className='photo empty';
      } else {
        var url=PHOTOS[s.id][tk]||PHOTOS[s.id].day||PHOTOS[s.id].night;
        if(url) ph.style.backgroundImage='url("'+url+'")'; else ph.className='photo empty';
      }
      b.appendChild(ph);
    } else { b.className+=' note'; }"""
BLOCK_OLD = """    var r=document.createElementNS(NS,'rect');
    r.setAttribute('x',x0); r.setAttribute('y',y0);
    r.setAttribute('width',(x1-x0).toFixed(2)); r.setAttribute('height',(y1-y0).toFixed(2));
    r.setAttribute('rx','0.6');
    g.appendChild(r);
  }
}"""
BLOCK_NEW = """    var ext=1.4, k=(i*3+j)*4, JIT=[0.18,-0.22,0.12,-0.15,0.2,-0.1,0.14,-0.2,0.1,-0.18,0.16,-0.12,0.2,-0.14,0.11,-0.19,0.13,-0.21,0.17,-0.13,0.1,-0.16,0.19,-0.11];
    var L=[[x0-ext,y0,x1+ext,y0],[x0-ext,y1,x1+ext,y1],[x0,y0-ext,x0,y1+ext],[x1,y0-ext,x1,y1+ext]];
    for(var q=0;q<4;q++){
      var ln=document.createElementNS(NS,'line'), jt=JIT[(k+q)%JIT.length];
      ln.setAttribute('x1',(L[q][0]+(q>1?jt:0)).toFixed(2)); ln.setAttribute('y1',(L[q][1]+(q<2?jt:0)).toFixed(2));
      ln.setAttribute('x2',(L[q][2]+(q>1?-jt:0)).toFixed(2)); ln.setAttribute('y2',(L[q][3]+(q<2?-jt:0)).toFixed(2));
      g.appendChild(ln);
    }
  }
}"""
LINECSS_OLD = "  vector-effect:non-scaling-stroke;stroke-linejoin:round}\n/* 她的便條"
LINECSS_NEW = ("  vector-effect:non-scaling-stroke;stroke-linejoin:round}\n"
               ".map #blocks line{stroke:rgba(255,255,255,.38);stroke-width:1.2;vector-effect:non-scaling-stroke;stroke-linecap:round}\n/* 她的便條")


# 手機卡（inv-phone、phone-bambi、phone-pr；larch/cards/phone.html 灌的）：主題換分頁不洗掉、背光與螢幕光、三句文案。
# 2026-09-17 作者抓到／要求。改了 phone.html 要一起改這裡。
PHONE_PAIRS = [
    ("  document.documentElement.style.colorScheme = theme==='light' ? 'light' : 'dark';", "  document.documentElement.style.colorScheme = 'normal';"),   # inv-phone 那張是更早的寫法
    ('html{color-scheme:dark}   /* 預設暗的;玩家按了那顆鈕才換。不宣告的話捲軸這類 UA 自己畫的東西會跟著玩家的系統走 */', 'html{color-scheme:normal}   /* 2026-09-17 改 normal：dark 會讓透明 iframe 的根畫布被補成純黑，body 的半透明黑就透不出場景。捲軸樣式在上面自己畫了，不靠它 */'),
    ('  radial-gradient(760px 520px at 12% 106%,rgba(37,194,232,.1),transparent 60%),\n  #04080c;', '  radial-gradient(760px 520px at 12% 106%,rgba(37,194,232,.1),transparent 60%),\n  rgba(4,8,12,.72);   /* 半透明壓黑：後面的場景透得出來，光暈疊在上面（2026-09-17 作者要的） */'),
    ("  document.documentElement.style.colorScheme = MODE==='banner' ? 'normal' : (theme==='light' ? 'light' : 'dark');", "  document.documentElement.style.colorScheme = 'normal';   // 全頁也要 normal，根畫布才不會被補黑（見上面 html{color-scheme}）"),
    ("    screen.className=''; page.textContent='';", "    screen.className=''; if(theme==='light') screen.classList.add('t-light'); page.textContent='';"),
    ("  screen.className='page-on off tab-'+p;", "  screen.className='page-on off tab-'+p; if(theme==='light') screen.classList.add('t-light');"),
    ("  screen.classList.toggle('t-light', theme==='light');", "  screen.classList.toggle('t-light', theme==='light');\n  document.body.classList.toggle('t-light', theme==='light');"),
    ("rp.appendChild(el('span',null,'她不回。'));", "rp.appendChild(el('span',null,'簡訊與通知。這裡只收。'));"),
    ("'官方帳號・每天開台'", "'官方帳號・不定時開台'"),
    ("新的插畫。畫她的人說這一版嘴角對了。", "新的插畫。這一版嘴角對了。"),   # phone.html 的 POSTS 與 push.py 灌的 feed JSON 兩種寫法都對得到
    ('<div id="phone"><div id="screen">', '<div id="halo"></div><div id="phone"><div id="screen">'),
    ('body.banner{background:transparent;display:block;padding:0}', '/* 背光與螢幕光（2026-09-17 作者要求，他之前做的手機都有）：#halo 是機身後面那團光，#screen 的 box-shadow 是螢幕本身溢出來的光。\n   跟著主題換色：深色紫青、淺色偏白。背景維持黑，光才漂亮（作者說的）。橫幅模式不畫。 */\n#halo{position:absolute;left:50%;top:50%;width:min(620px,130vw);height:min(1040px,130vh);transform:translate(-50%,-50%);\n  border-radius:50%;pointer-events:none;filter:blur(30px);animation:halo 7s ease-in-out infinite alternate;\n  background:radial-gradient(closest-side,rgba(183,139,255,.34),rgba(37,194,232,.18) 52%,transparent 100%);transition:background .35s}\nbody.t-light #halo{background:radial-gradient(closest-side,rgba(226,236,255,.46),rgba(122,79,208,.20) 52%,transparent 100%)}\n@keyframes halo{from{opacity:.72}to{opacity:1}}\n#screen{box-shadow:0 0 36px rgba(183,139,255,.30),0 0 96px rgba(37,194,232,.18)}\nbody.t-light #screen{box-shadow:0 0 36px rgba(214,228,255,.48),0 0 96px rgba(255,255,255,.2)}\nbody.banner #halo{display:none}\nbody.banner{background:transparent;display:block;padding:0}'),
]


# 2026-09-17 第二次跑把「舊是新的前綴」那三段又插了一遍：先把重複收回一份，之後新的已在就跳過
PHONE_DEDUP = [
    ('<div id="halo"></div><div id="halo"></div>', '<div id="halo"></div>'),
    (" if(theme==='light') screen.classList.add('t-light'); if(theme==='light') screen.classList.add('t-light');", " if(theme==='light') screen.classList.add('t-light');"),
    ("  document.body.classList.toggle('t-light', theme==='light');\n  document.body.classList.toggle('t-light', theme==='light');", "  document.body.classList.toggle('t-light', theme==='light');"),
]


def swap_phone_js(html, stats):
    for dup, one in PHONE_DEDUP:
        while dup in html:
            html = html.replace(dup, one); stats["phone"] += 1
    for old, new in PHONE_PAIRS:
        if new in html:
            continue
        if old in html:
            html = html.replace(old, new, 1); stats["phone"] += 1
        elif new not in html:
            print(f"  ★ 手機卡裡找不到這一段的新舊版本（{old[:30]}…），去對 phone.html")
    return html


def swap_board_js(html, stats):
    for old, new, name in ((RAIL_OLD, RAIL_NEW, "rail"), (PARK_OLD, PARK_NEW, "rail"),
                           (VIS_OLD_A, VIS_NEW_A, "rail"), (VIS_OLD_B, VIS_NEW_B, "rail"),
                           (CORK_OLD_SKY, CORK_NEW_SKY, "rail"), (CORK_OLD_PAINT, CORK_NEW_PAINT, "rail"),
                           (CORK_OLD_APPLY, CORK_NEW_APPLY, "rail"), (CORK_OLD_CSS, CORK_NEW_CSS, "rail"), (TEX_OLD, TEX_NEW, "rail"),
                           (PHOTO_OLD, PHOTO_NEW, "rail"), (BLOCK_OLD, BLOCK_NEW, "rail"), (LINECSS_OLD, LINECSS_NEW, "rail")):
        if new in html:
            continue
        if old in html:
            html = html.replace(old, new, 1); stats[name] += 1
        else:
            print(f"  ★ 調查板卡片裡找不到這一段的新舊版本（{old[:30]}…），去對 board.html")
    if "var ATLAS = " not in html and ATLAS_OLD in html:      # atlas 表只加一次（插在 PHOTOS 前面）
        html = html.replace(ATLAS_OLD, ATLAS_NEW, 1); stats["rail"] += 1
    return html


# 五、筆記卡的 `~~劃掉~~` 改成組合字元畫線（build.py 同一條規則），字改了配音代號也跟著變，
#     所以每一句都用原講者＋現在的字重查一次 urls.json，查得到就換成新檔（順便走 jsDelivr）。
STRIKE = re.compile(r"~~(.+?)~~")


def strike(text):
    # `~~…~~` 與早先上線的 U+0336 組合字元版本，都換成純文字記號「〔劃掉：…〕」（播放器把組合字元印成方框）
    text = STRIKE.sub(r"〔劃掉：\1〕", text)
    return re.sub(r"(?:.̶)+", lambda m: "〔劃掉：" + m.group(0).replace("̶", "") + "〕", text)


def rekey_voice(holder, speaker, stats):
    import voice as V
    if not speaker:
        return
    u = NK.VOICE_URLS.get(V.key(speaker, holder.get("speakText") or holder.get("text"), holder.get("emotion") or None))
    if u and NK.cdn(u) != holder.get("voiceUrl"):
        holder["voiceUrl"] = NK.cdn(u); stats["rekey"] += 1


def patch(board, stats):
    disp = PUSH.DISPLAY
    ghost = next(a["url"] for n in board["nodes"] for a in (n["data"].get("stage") or {}).get("actors") or [] if a.get("id") == "actor-none")
    for n in board["nodes"]:
        d = n["data"]
        if d.get("type") == "miniGame" and "function walkMap()" in (d.get("miniGameHtml") or ""):
            d["miniGameHtml"] = swap_board_js(d["miniGameHtml"], stats)
        if d.get("type") == "miniGame" and "function flipTheme(" in (d.get("miniGameHtml") or ""):
            d["miniGameHtml"] = swap_phone_js(d["miniGameHtml"], stats)
        # 六、謝幕字卷的副標：2026-09-09 拉成十四天，字卷那張卡沒跟上（字是隔開排的，grep「十二天」找不到）
        for k in ("miniGameHtml", "pluginHtml", "html"):
            if isinstance(d.get(k), str) and "十 二 天" in d[k]:
                d[k] = d[k].replace("調 查 篇　・　十 二 天", "調 查 篇　・　十 四 天"); stats["strike"] += 1
        if d.get("type") == "dialogue" and ("~~" in (d.get("text") or "") or "̶" in (d.get("text") or "")):
            d["text"] = strike(d["text"]); stats["strike"] += 1
        # 八、斑比工作室深夜掛到正篇的直播間背景（2026-09-17 他抓到）：場景卡與調查板 HTML 裡的網址一起換
        for k in ("background", "backgroundNight", "miniGameHtml", "pluginHtml", "html"):
            for old, new in NIGHT_FIX.items():
                if isinstance(d.get(k), str) and old in d[k]:
                    d[k] = d[k].replace(old, new); stats["studio"] += 1
        # 九、結局段諾亞說完「門幫我帶一下」之後她下樓、跟人擦身，諾亞的立繪卻一路留在台上（2026-09-17 他抓到：
        # 玩家會以為擦身的人是諾亞）。設計稿已補「下台」標記，線上這四張直接清場。
        if n["id"] in STAGE_CLEAR and any(a.get("name") for a in (d.get("stage") or {}).get("actors") or []):
            d["stage"], d["characterLayers"] = CS.ghost_stage(ghost)
            stats["stage"] += 1
        # 七、旁白正文與筆記標籤裡的名字（names.py），要排在重查配音之前：代號照字算
        if d.get("type") == "dialogue":
            stats["names"] += NAMES.hide_names(d)
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
        stats = {"speaker": 0, "voice": 0, "table": 0, "rail": 0, "strike": 0, "rekey": 0, "names": 0, "studio": 0, "stage": 0, "phone": 0}
        patch(board, stats)
        print(f"{bid}：講者名 {stats['speaker']} 處、旁白名字 {stats['names']} 處、工作室背景 {stats['studio']} 處、結局清台 {stats['stage']} 張、手機卡 {stats['phone']} 處、音檔網址 {stats['voice']} 處（其中換新檔 {stats['rekey']}）、"
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
