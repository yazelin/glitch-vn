#!/usr/bin/env python3
"""小說版的檢查。線性的東西要驗的東西少，可是還是不能靠眼睛。"""
import json, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from config import PROJ, BASE, H, ROOT, STORE, api  # noqa: E402

p = api()
bad, warn = [], []
cids = {c["id"] for c in p.get("characters", [])}
for b in p["boards"]:
    N = {n["id"]: n for n in b["nodes"]}
    out = {}
    for e in b["edges"]:
        if e["source"] not in N: bad.append(f"{b['id']}：邊的來源不存在 {e['source']}")
        if e["target"] not in N: bad.append(f"{b['id']}：邊的目標不存在 {e['target']}")
        out.setdefault(e["source"], []).append(e["target"])
    tgt = {t for v in out.values() for t in v}
    start = [n["id"] for n in b["nodes"] if n["data"].get("start")]
    for n in b["nodes"]:
        d, nid = n["data"], n["id"]
        if nid not in tgt and nid not in start:
            bad.append(f"{b['id']}：{nid} 沒有入邊（走不到）")
        if nid not in out and d.get("type") != "boardJump" and not d.get("chapterEnd"):
            bad.append(f"{b['id']}：{nid} 沒有出邊（點下去就停住）")
        if d.get("type") in (None, "dialogue") and not (d.get("text") or "").strip():
            bad.append(f"{b['id']}：{nid} 是空的對話卡")
        if d.get("characterId") and d["characterId"] not in cids:
            bad.append(f"{b['id']}：{nid} 的 characterId 對不到角色")
        for L in (d.get("characterLayers") or []):
            if not L.get("url"): bad.append(f"{b['id']}：{nid} 有立繪圖層沒有圖")
        if d.get("type") == "scene" and not d.get("background"):
            bad.append(f"{b['id']}：{nid} 場景卡沒有背景")
        # 兩個人站同一格＝立繪疊在一起，畫面上只看得到一個。
        # 2026-09-12 中過：第四章那一場黑洞先生「在她背後的走廊經過」，
        # 寫的人把她的 farRight 複製了一次，五張卡兩個人疊著，那句話演不出來。
        _slots = [a.get("slot") for a in ((d.get("stage") or {}).get("actors") or [])]
        _dup = {x for x in _slots if _slots.count(x) > 1}
        if _dup:
            bad.append(f"{b['id']}：{nid} 有兩個人站同一格 {sorted(_dup)}　"
                       + "、".join(f"{a.get('name')}@{a.get('slot')}"
                                   for a in ((d.get("stage") or {}).get("actors") or [])))
    # 主線是線性的，只有 choice 卡可以分岔，而且每一條都要接回同一張主線卡。
    for s, t in out.items():
        if len(t) <= 1: continue
        if N[s]["data"].get("type") != "choice":
            bad.append(f"{b['id']}：{s} 有 {len(t)} 條出邊，可是它不是選項卡")
        elif len(t) != len(N[s]["data"].get("choices") or []):
            bad.append(f"{b['id']}：{s} 有 {len(t)} 條出邊，選項卻有 "
                       f"{len(N[s]['data'].get('choices') or [])} 個")
    # 支線一定要匯流：每一條走到底都要落在同一張主線卡上
    for n in b["nodes"]:
        if n["data"].get("type") != "choice": continue
        ends = set()
        for t0 in out.get(n["id"], []):
            seen, cur = set(), t0
            while cur and cur not in seen and len(out.get(cur, [])) == 1:
                seen.add(cur); cur = out[cur][0]
            ends.add(cur)
        if len(ends) > 1:
            bad.append(f"{b['id']}：{n['id']} 的支線沒有匯流，落在 {sorted(ends)}")
    kinds = {}
    for n in b["nodes"]:
        k = n["data"].get("type") or "dialogue"
        kinds[k] = kinds.get(k, 0) + 1
    lines = sum(len(n["data"].get("dialogueLines") or []) for n in b["nodes"])
    # **翻譯是平台上翻的，建置腳本產不出來。** 重建一章而沒有把它撈回來的話
    # 這個數字會直接變成 0，印出來才看得見（見 novelkit.Chapter.push）。
    loc = sum(1 for n in b["nodes"] if n["data"].get("localizations"))
    print(f"{b['name']}：{len(b['nodes'])} 卡　{kinds}　多句對話 {lines} 句"
          f"　翻譯 {loc} 張")
    print(f"  起點 {start or '★ 沒有起點卡'}")
# ── 旁白不要幫別人講話 ───────────────────────────────
# 整張卡的每一段都是「…」的旁白卡，名牌會寫「旁白」可是內容是別人的台詞。
# 小說裡靠引號就分得出來，視覺小說分不出來——讀者只看得到名牌。
for b0 in p["boards"]:
    for n in b0["nodes"]:
        d = n["data"]
        if d.get("speaker") != "旁白":
            continue
        ls = [x.strip() for x in (d.get("text") or "").split("\n") if x.strip()]
        if ls and all(x.startswith("「") and x.endswith("」") for x in ls):
            bad.append(f"{b0['id']}：{n['id']} 旁白在唸別人的台詞，要給講者　{ls[0][:18]}")

# ── 跨章的站位 ───────────────────────────────────────
# **場景卡與跳章卡沒寫 stage 的話，播放器會保留上一張的人。**
# 第二章結尾黑洞先生站著，跳到第三章他就跟著出現在開頭。
# 修法是這兩種卡也寫一個演員數為零的 stage（市集的場景卡就是這樣清台的）。
for b in p["boards"]:
    for n in (b["nodes"][0], b["nodes"][-1]):
        d = n["data"]
        # actor-none 是清台用的透明演員，不是台上的人（見 novelkit.GHOST）。
        who = [a["name"] for a in (d.get("stage") or {}).get("actors", [])
               if a.get("id") != "actor-none"]
        where = "章首" if n is b["nodes"][0] else "章末"
        if "stage" not in d:
            bad.append(f"{b['id']}：{n['id']}（{where}）沒有 stage 欄位，"
                       f"播放器會沿用上一張的人")
        elif who:
            bad.append(f"{b['id']}：{n['id']}（{where}）台上還有 {'／'.join(who)}")

# ── 站位的兩個常見錯 ─────────────────────────────────
# 一、旁白講到某個人在場，可是台上沒有他
# 二、某個人站在台上很久，中間沒有講話也沒有被提到
# 兩個都是「站位綁在段落邊界、不是綁在劇情上」的症狀，第一章都犯過。
CAST = ["格莉奇", "黑洞先生", "貓草", "鐵塔", "0x", "斑比", "諾亞"]
QUIET = 6
for b in p["boards"]:
    on = {}
    # 只在留言區出現的人（大頭貼）不算「在場」，旁白寫「貓草沒有回」不是站位漏掉。
    inperson = {a["name"] for n in b["nodes"]
                for a in (n["data"].get("stage") or {}).get("actors", [])
                if "chat-" not in a.get("url", "")}
    for i, n in enumerate(b["nodes"]):
        d = n["data"]
        names = {a["name"] for a in (d.get("stage") or {}).get("actors", [])}
        txt = (d.get("text") or "") + " ".join(
            l.get("text", "") for l in (d.get("dialogueLines") or []))
        speak = {d.get("speaker")} | {l.get("speaker") for l in (d.get("dialogueLines") or [])}
        # 只抓「旁白用某人當句首描述他在場」——「黑洞先生坐在沙發上」要抓，
        # 「第三則是斑比自己轉的」不要抓（那只是提到名字）。
        heads = {l.strip()[:6] for l in (d.get("text") or "").split("\n")}
        for who in CAST:
            present = (who in inperson and d.get("speaker") == "旁白"
                       and any(h.startswith(who) for h in heads))
            if present and who not in names:
                warn.append(f"{b['id']}：{n['id']} 旁白說「{who}」在場，可是台上沒有他")
            if who in names:
                if who in speak or who in txt:
                    on[who] = i
                elif i - on.get(who, i) >= QUIET:
                    warn.append(f"{b['id']}：{n['id']} 「{who}」已經站了 {i - on[who]} 張卡"
                                f"沒講話也沒被提到，要不要讓他退場")
                    on[who] = i
            else:
                on.pop(who, None)

# ── CG 收藏：畫廊清單與解鎖點是兩份資料，要對得起來 ──
# 只設 locked 不給解鎖點＝十四張永遠的問號；只給解鎖點不設 locked＝一開遊戲
# 就在收藏裡看到「錄音間・第十一次」這種有雷的標題。兩邊都要數。
_items = (p.get("settings") or {}).get("cgGalleryItems") or []
if _items:
    _hit = {}
    for b in p["boards"]:
        for n in b["nodes"]:
            d = n["data"]
            for op in (d.get("cgOps") or []):
                where = f"{b['id']}:{n['id']}"
                # **只有 setVariable 吃 cgOps。** 寫在對話卡上平台不會報錯，
                # 只是永遠不解鎖。
                if d.get("type") != "setVariable":
                    bad.append(f"{where} 的 cgOps 掛在 {d.get('type')} 卡上，"
                               f"只有 setVariable 吃得到")
                # **text 不可以留空。** 卡片模式下就是一張點不動的空白卡。
                if not (d.get("text") or "").strip():
                    bad.append(f"{where} 是沒有字的 setVariable 卡，卡片模式會卡死")
                if (op.get("mode") or "unlock") != "unlock":
                    continue
                _hit.setdefault(op.get("url"), []).append(where)
    _gal = {x.get("url"): x.get("title") for x in _items}
    for x in _items:
        if not x.get("locked"):
            bad.append(f"CG「{x.get('title')}」沒有 locked，一開遊戲就看得到（劇透）")
        if x.get("url") not in _hit:
            bad.append(f"CG「{x.get('title')}」沒有解鎖點，畫廊裡會是永遠的問號")
    for _u, _w in _hit.items():
        if _u not in _gal:
            bad.append(f"解鎖了畫廊沒有的圖：{str(_u)[-42:]}（{_w[0]}）")
        elif len(_w) > 1:
            warn.append(f"CG「{_gal[_u]}」有 {len(_w)} 個解鎖點：{'、'.join(_w)}")
    print(f"\nCG 收藏：{len(_items)} 張，鎖著 {sum(1 for x in _items if x.get('locked'))} 張，"
          f"解鎖動作 {sum(len(v) for v in _hit.values())} 個，"
          f"對到 {len([u for u in _hit if u in _gal])} 張")

# ── 配音有沒有掛齊 ───────────────────────────────────
# **鍵算錯不會報錯，只會安靜地沒有聲音。** 查表的鍵是「講者＋台詞＋情緒」，
# 少一個欄位就全部對不上，而那要聽完六百多句才發現。這裡直接數。
import voice as V
_vu = ROOT / "art/voice/urls.json"
if _vu.exists():
    urls = json.loads(_vu.read_text(encoding="utf-8"))
    want = got = 0
    miss = []
    for b in p["boards"]:
        for n in b["nodes"]:
            d = n["data"]
            if (d.get("type") or "dialogue") != "dialogue":
                continue
            # speakText 優先，跟 novelkit._voice 用同一個規則：畫面上的字
            # 跟要唸的字不一定一樣（系統訊息不唸）。
            items = ([(l.get("speaker"), l.get("text"), l.get("emotion"),
                       l.get("voiceUrl")) for l in d.get("dialogueLines") or []]
                     or [(d.get("speaker"), d.get("speakText") or d.get("text"),
                          d.get("emotion"), d.get("voiceUrl"))])
            for sp, tx, em, u in items:
                if not sp or not tx or not tx.strip():
                    continue
                if V.key(sp, tx, em or None) not in urls:
                    continue          # 這一句本來就沒生（例如只有標點）
                want += 1
                if u:
                    got += 1
                elif len(miss) < 5:
                    miss.append(f"{b['id']}：{n['id']} {sp}「{tx[:14]}」")
    print(f"\n配音：有網址的 {want} 句，掛上 {got} 句")
    for x in miss:
        bad.append(f"配音沒掛上　{x}")

# ── art/voice 與 docs/voice 要一致 ──────────────────
# **這個坑踩過兩次。** 一次是 publish_voice 只比檔案大小，換了內容但大小
# 剛好一樣的一百九十二個檔被整批跳過；一次是手動刪檔重生之後忘了同步，
# 六十六個檔在 docs 裡根本不存在。兩次都是聽的人先發現的。
_a = ROOT / "art/voice"
_d = ROOT / "docs/voice"
if _a.exists() and _d.exists():
    A = {p.name: p.read_bytes() for p in _a.glob("*.mp3")}
    D = {p.name: p.read_bytes() for p in _d.glob("*.mp3")}
    miss = [n for n in A if n not in D]
    diff = [n for n in A if n in D and A[n] != D[n]]
    if miss or diff:
        bad.append(f"docs/voice 沒跟上：缺 {len(miss)} 個、內容不同 {len(diff)} 個"
                   f"（跑 python3 tools/publish_voice.py）")
    else:
        print(f"發佈：art 與 docs 一致（{len(A)} 個檔）")

# **挑選過的錄音有沒有被重生蓋掉。** 檔名是內容雜湊，重生就是就地覆蓋，
# 使用者聽過幾十支才挑出來的那一支會安靜地消失（實際發生過一次）。
_pk = ROOT / "art/voice/picked.json"
if _pk.exists():
    import subprocess as _sp
    _p = json.loads(_pk.read_text())
    _lost = []
    for _k, _v in _p.items():
        _src, _ins = pathlib.Path(_v["source"]), ROOT / f"art/voice/{_k}.mp3"
        if not _src.exists() or not _ins.exists():
            continue
        _d = [float(_sp.run(["ffprobe", "-v", "error", "-show_entries",
              "format=duration", "-of", "csv=p=0", str(x)],
              capture_output=True, text=True).stdout or 0) for x in (_src, _ins)]
        if abs(_d[0] - _d[1]) > 0.25:
            _lost.append(_k)
    if _lost:
        bad.append(f"挑選過的錄音被蓋掉 {len(_lost)} 句"
                   f"（跑 python3 tools/collect_picks.py --check 看是哪幾句）")
    else:
        print(f"挑選：{len(_p)} 句使用者指名的錄音都還在")

# **背景樂要逐段掃過有沒有人聲。** 這批是生成的，模型很容易在中段塞進
# 人聲：bgm-living 的 135～210 秒有人在說話，而挑選的時候只聽了前 30 秒，
# 所以完全沒發現。掃法見 tools/scan_bgm_vocal.py——whisper 不能用，
# 純音樂會讓它產生幻覺（十一支有十支被轉成整排的「Thank you.」）。
# gemini 也只有「有人在說話」那一項可信，「哼唱墊底」大量誤判——
# 被判有哼唱的四支，人耳聽起來一支都沒有。

# **背景樂的響度要一致。** 只壓換上去的那幾支、留著沒換的不動，
# 同一個專案就有兩種標準，混著聽有幾場特別吵（聯動直播室那場中過）。
import subprocess as _sp2
_bgm = ROOT / "art/bgm"
if _bgm.exists():
    _lv = []
    for _f in sorted(_bgm.glob("*.mp3")):
        _r = _sp2.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(_f), "-af",
                       "loudnorm=I=-18:TP=-2:LRA=9:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True)
        _i = _r.stderr.rfind("{")
        if _i >= 0:
            _lv.append((_f.stem, float(json.loads(_r.stderr[_i:])["input_i"])))
    _out = [n for n, v in _lv if abs(v + 18.0) > 1.0]
    if _out:
        bad.append(f"背景樂響度不一致：{_out}（跑 python3 tools/level_bgm.py --fix）")
    elif _lv:
        _sp = max(v for _, v in _lv) - min(v for _, v in _lv)
        print(f"背景樂：{len(_lv)} 支響度差 {_sp:.1f} dB")

print()
for x in bad: print("  ★", x)
for x in warn: print("  ・", x)
print("全部通過。" if not bad else f"★ {len(bad)} 個問題")
sys.exit(1 if bad else 0)
