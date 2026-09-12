#!/usr/bin/env python3
"""劇情模式「走起來不斷」那一層的靜態檢查（規格-劇情模式順順通關.md 第三節）。

    python3 tools/storylint.py
    python3 tools/storylint.py --self-test          # 負控制：拿真的 payload 改，證明會紅

**結束碼是三態，因為 CI 只看結束碼。**

    0   全部驗過而且全綠
    2   沒有紅的，可是有項目沒驗到（SKIP）。**這不是通過**，是「沒驗完」
    1   有紅的

報告裡寫「這不等於這一層過了」卻回 0 的話，接進自動流程就會被當成通過——
工具嘴上說不通過、身體說通過，那正是這支工具要防的東西換到結束碼這一層。
（`--self-test` 是例外，它只回 0／1：負控制要嘛有效要嘛無效，沒有第三態。）

**為什麼是靜態的。** `tools/autoplay.mjs` 的逐字稿只印六種標記
（`[卡住] [手機] [第一頁] [背包] [選項] [錄音帶]`），**背景、BGM、語音一個都沒記**，
所以這一層不可能從逐字稿驗——那份資料裡根本沒有那些欄位。改走板子的靜態資料，
秒級、可重複、不用跑四十分鐘。

**三條規矩（規格第四節）：**

1. 每一項都印「量到幾筆」以及那幾筆是從哪裡數出來的。**量到 0 筆自己紅**，
   不要靠人看出來——2026-09-12 直播那支就是靠「量到 0 天」才看出 B、C 是假綠的。
2. 跑不動的項目標 **SKIP 並寫明為什麼**，不要為了湊全綠硬給一個結果。
   SKIP 不是永久的：資料一出現就會自動轉成實驗（`--self-test` 的**案例五**在證明這件事：
   把 bgm 加進來，S2 當場從 SKIP 轉成實驗並抓到空字串）。
3. 負控制跑在**真的** payload 上。合成資料不同形，負控制在上面全綠地通過，
   證明的是 fixture 不是工具。
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / "larch/inv/out/payload.json"
ROUTE = ROOT / "design/調查篇-通關路線.txt"
SPOKEN = ROOT / "art/voice/spoken.json"

PASS, FAIL, SKIP = "綠", "紅", "SKIP"


class Report:
    def __init__(self):
        self.rows = []

    def add(self, state, name, counted, why=""):
        """counted 是「量到幾筆／從哪數的」，每一項都必須給，不給就是沒在驗。"""
        self.rows.append((state, name, counted, why))

    def show(self):
        for state, name, counted, why in self.rows:
            tag = {PASS: " 綠 ", FAIL: "*紅*", SKIP: "SKIP"}[state]
            print(f"  {tag}  {name}")
            print(f"        量到：{counted}")
            if why:
                for ln in why.split("\n"):
                    print(f"        {ln}")
        bad = sum(1 for r in self.rows if r[0] == FAIL)
        skipped = [r[1].split("　")[0] for r in self.rows if r[0] == SKIP]
        done = len(self.rows) - len(skipped) - bad
        print()
        if bad:
            print(f"  {bad} 項不過。（結束碼 1）")
            return 1
        if skipped:
            # 有 SKIP 的時候**不准說「全部通過」，也不准回 0**。
            # 那句話會讓沒驗到的被當成驗過了，而那個 0 會讓 CI 也這樣以為。
            print(f"  沒有紅的，但 {len(skipped)} 項沒驗到：{'、'.join(skipped)}")
            print(f"  真的驗過的只有 {done} 項。**這不等於這一層過了。**（結束碼 2）")
            return 2
        print("  全部通過。（結束碼 0）")
        return 0


def nodes_of(payload):
    return payload.get("nodes") or []


def lines_of(data):
    dl = data.get("dialogueLines") or []
    if dl:
        return dl
    if data.get("text"):
        # **單人卡的聲音掛在卡片層**（larch/novelkit.py 的 _voice()：多人卡掛行上、
        # 單人卡掛卡上）。合成這一行的時候不把 voiceUrl 帶過來，S3 就會把兩百多張
        # 掛好的卡數成「沒有聲音」——量到的東西跟在意的東西差一層。
        return [{"text": data["text"], "speaker": data.get("speaker", ""),
                 "voiceUrl": data.get("voiceUrl"), "emotion": data.get("emotion")}]
    return []


# ── S0：資料真的讀進來了 ────────────────────────────────────────────────
def check_data(rep, payload, route_steps):
    ns = nodes_of(payload)
    edges = payload.get("edges") or []
    counted = f"卡 {len(ns)} 張、邊 {len(edges)} 條（payload.json）；軌道 {route_steps} 步（通關路線逐字稿的板標頭）"
    if not ns or not route_steps:
        rep.add(FAIL, "S0 資料讀得到", counted,
                "卡數或軌道步數是 0，底下每一項都會「沒東西可驗所以全綠」。\n"
                "這一項就是擋那種假綠的，先修資料來源再看下面。")
        return False
    rep.add(PASS, "S0 資料讀得到", counted)
    return True


# ── S1：背景 ───────────────────────────────────────────────────────────
def check_background(rep, payload):
    ns = nodes_of(payload)
    scenes = [n for n in ns if (n.get("data") or {}).get("type") == "scene"]
    withbg = [n for n in ns if "background" in (n.get("data") or {})]
    missing = [n["id"] for n in scenes if not ((n.get("data") or {}).get("background") or "").strip()]
    bad = []
    for n in withbg:
        v = ((n.get("data") or {}).get("background") or "").strip()
        if not v or v.lower() == "none":
            bad.append((n["id"], "空的"))
        elif not re.match(r"^https?://", v):
            bad.append((n["id"], f"不是網址：{v[:40]}"))
    counted = (f"場景卡 {len(scenes)} 張、宣告了 background 的卡 {len(withbg)} 張"
               f"（payload.json 逐張看 data.type 與 data.background）")
    if missing or bad:
        why = ""
        if missing:
            why += f"場景卡沒有背景：{'、'.join(missing[:6])}{' …' if len(missing) > 6 else ''}\n"
        if bad:
            why += "背景值不對：" + "、".join(f"{i}（{r}）" for i, r in bad[:6])
        rep.add(FAIL, "S1 背景都指得到圖", counted, why.rstrip())
    else:
        rep.add(PASS, "S1 背景都指得到圖", counted)


# ── S2：BGM ────────────────────────────────────────────────────────────
def check_bgm(rep, payload):
    ns = nodes_of(payload)
    withbgm = [n for n in ns if "bgm" in (n.get("data") or {})]
    counted = f"宣告了 bgm 的卡 {len(withbgm)} 張（payload.json 逐張看 data.bgm）"
    if not withbgm:
        rep.add(SKIP, "S2 BGM 換曲點", counted,
                "板上一張卡都沒有 bgm 欄位，所以沒有東西可以驗。\n"
                "BGM 還沒做（交接-2026-09-12.md 第十節「更遠的」）。\n"
                "**這不是通過。** 等 BGM 進板子，這一項會自己轉成實驗，不用改程式。")
        return
    empty = [n["id"] for n in withbgm if not ((n.get("data") or {}).get("bgm") or "").strip()]
    if empty:
        rep.add(FAIL, "S2 BGM 換曲點", counted,
                "這幾張的 bgm 是空字串：" + "、".join(empty[:6]) + "\n"
                "空字串會被平台當成「沒設」，前一首會繼續播。要靜音得掛一段真的無聲音軌。")
    else:
        rep.add(PASS, "S2 BGM 換曲點", counted)


# ── S3：語音 ───────────────────────────────────────────────────────────
def check_voice(rep, payload, spoken):
    ns = nodes_of(payload)
    total = have = 0
    for n in ns:
        for l in lines_of(n.get("data") or {}):
            total += 1
            if l.get("voiceUrl"):
                have += 1
    modes = [n for n in ns if "voiceMode" in (n.get("data") or {})]
    counted = (f"台詞 {total} 句、其中掛了 voiceUrl 的 {have} 句；"
               f"宣告了 voiceMode 的卡 {len(modes)} 張（payload.json 逐句看 dialogueLines）")
    if have == 0:
        extra = ""
        if spoken:
            texts = {v.strip() for v in spoken.values() if isinstance(v, str)}
            board_texts = [str(l.get("text", "")).strip()
                           for n in ns for l in lines_of(n.get("data") or {})]
            board_texts = [t for t in board_texts if t]
            hit = sum(1 for t in board_texts if t in texts)
            uniq = len({t for t in board_texts})
            uhit = len({t for t in board_texts if t in texts})
            extra = (f"\n順帶量的（本機錄好的，還沒掛上板子）：{SPOKEN.name} 有 {len(spoken)} 筆；"
                     f"板上 {len(board_texts)} 句（去重後 {uniq} 種）裡，"
                     f"{hit} 句／{uhit} 種逐字對得到本機錄音。"
                     f"\n（句數可能大於錄音筆數，因為同一句台詞在板上會重複出現。）")
        rep.add(SKIP, "S3 語音掛上去了", counted,
                "板上一句都沒有 voiceUrl，所以沒有東西可以驗。\n"
                "配音還在本機，還沒掛回板子（交接-2026-09-12.md 第十節）。\n"
                "**這不是通過。** 等 voiceUrl 進板子，這一項會自己轉成實驗。" + extra)
        return
    missing = total - have
    if missing:
        rep.add(FAIL, "S3 語音掛上去了", counted, f"還有 {missing} 句沒有 voiceUrl。")
    else:
        rep.add(PASS, "S3 語音掛上去了", counted)


# ── S4：匯出版那道閘 ───────────────────────────────────────────────────
def check_export_gate(rep, project):
    if project is None:
        rep.add(SKIP, "S4 匯出版的語音閘（project.languages[].voiceMode）",
                "0 筆（payload.json 只有 nodes／edges／variables，沒有專案層設定）",
                "線上播放器看卡片的 voiceMode，匯出的單檔版只看 project.languages[].voiceMode，\n"
                "兩邊各要各的。payload.json 裡沒有專案層，所以這一項在這裡驗不到。\n"
                "**要驗得先把專案整包抓下來**（GET /api/agent/projects/:id），再跑一次帶 --project。\n"
                "**這不是通過。**")
        return
    langs = project.get("languages") or []
    counted = f"語言 {len(langs)} 種（專案整包的 project.languages）"
    bad = [l.get("code") for l in langs if (l.get("voiceMode") or "off") == "off"]
    if not langs:
        rep.add(FAIL, "S4 匯出版的語音閘", counted, "一種語言都沒有，匯出版不會播任何聲音。")
    elif bad:
        rep.add(FAIL, "S4 匯出版的語音閘", counted,
                f"這幾種的 voiceMode 是 off：{'、'.join(map(str, bad))}")
    else:
        rep.add(PASS, "S4 匯出版的語音閘", counted)


def route_step_count(path):
    if not path.exists():
        return 0
    return len(re.findall(r"^=== 板 第 \d+ 天 ・ ", path.read_text(encoding="utf-8"), re.M))


def run(payload, route_steps, spoken, project):
    rep = Report()
    ok = check_data(rep, payload, route_steps)
    if ok:
        check_background(rep, payload)
        check_bgm(rep, payload)
        check_voice(rep, payload, spoken)
        check_export_gate(rep, project)
    return rep


# ── 負控制 ─────────────────────────────────────────────────────────────
def self_test(payload, route_steps, spoken):
    import copy

    def first_scene(p):
        for n in nodes_of(p):
            if (n.get("data") or {}).get("type") == "scene":
                return n
        return None

    def mut(fn):
        p = copy.deepcopy(payload)
        fn(p)
        return p

    def clear_bg(p):
        first_scene(p)["data"]["background"] = ""

    def local_bg(p):
        first_scene(p)["data"]["background"] = "art/bg-investigation/bg-lobby.png"

    def no_nodes(p):
        p["nodes"] = []

    def add_bgm(p):
        first_scene(p)["data"]["bgm"] = ""

    def all_present(p):
        """把 bgm 與 voiceUrl 補齊，走通「全部驗過而且全綠」那條路。
        那條路今天在真資料上走不到（S2、S3 必 SKIP），不走一次就等於沒測過。"""
        for n in nodes_of(p):
            d = n.get("data") or {}
            if "bgm" in d or d.get("type") == "scene":
                d["bgm"] = "https://example.invalid/bgm.mp3"
            for l in (d.get("dialogueLines") or []):
                l["voiceUrl"] = "https://example.invalid/v.mp3"
            if d.get("dialogueLines") or d.get("text"):
                d["voiceMode"] = "shared"
                if not d.get("dialogueLines") and d.get("text"):
                    d["dialogueLines"] = [{"text": d["text"], "voiceUrl": "https://example.invalid/v.mp3"}]

    cases = [
        ("一、場景卡的背景清成空字串", "S1", mut(clear_bg), route_steps),
        ("二、背景改成本機路徑（推上去會是破圖）", "S1", mut(local_bg), route_steps),
        ("三、卡片一張都讀不到（量到 0 筆）", "S0", mut(no_nodes), route_steps),
        ("四、軌道解析出 0 步", "S0", payload, 0),
        # 這一種不是「壞掉」，是證明 SKIP 會在資料出現時自動轉成實驗
        ("五、有人把 bgm 加進來了（空字串）", "S2", mut(add_bgm), route_steps),
    ]

    print("好的（真的 payload，沒有動過）：")
    good = run(payload, route_steps, spoken, None)
    good.show()
    # 負控制只問「好的有沒有紅」，SKIP 在這裡是預期狀態，不算失敗
    all_fine = not [r for r in good.rows if r[0] == FAIL]
    for name, want, p, steps in cases:
        print(f"\n{name}　（應該由 {want} 抓到）")
        rep = run(p, steps, spoken, None)
        rep.show()
        red = [r[1][:2] for r in rep.rows if r[0] == FAIL]
        hit = want in red
        if not hit:
            all_fine = False
        print(f"  → 變紅的是：{'、'.join(red) or '沒有'}　"
              f"{'✔ ' + want + ' 抓到了' if hit else '✘ ' + want + ' 沒抓到'}")

    # 最後一案不是壞掉，是走通「全部驗過而且全綠、結束碼 0」那條路。
    print("\n六、補齊 bgm 與 voiceUrl　（應該全綠，結束碼 0）")
    full = mut(all_present)
    rep = run(full, route_steps, spoken, {"languages": [{"code": "zh-Hant", "voiceMode": "shared"}]})
    code = rep.show()
    ok0 = code == 0
    if not ok0:
        all_fine = False
    print(f"  → 結束碼 {code}　{'✔ 全綠那條路走得通' if ok0 else '✘ 補齊了還是沒全綠'}")

    print("\n這份負控制跑在**真的 payload.json 上**，不是合成的。")
    print("案例五不是壞掉，是證明 SKIP 不是永久失明：bgm 一出現，S2 就從 SKIP 轉成實驗並抓到空字串。")
    print("案例六不是壞掉，是走通「全部驗過而且全綠、結束碼 0」那條路——")
    print("那條路今天在真資料上走不到（S2、S3 必 SKIP），不走一次就等於沒測過。")
    print("\n" + ("PASS 負控制有效：好的沒有紅，五種壞法各自被該抓的那一項抓到，全綠那條路也走得通。"
                  if all_fine else
                  "FAIL 負控制無效——先修檢查再談驗收。"))
    return 0 if all_fine else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", default=str(PAYLOAD))
    ap.add_argument("--route", default=str(ROUTE))
    ap.add_argument("--spoken", default=str(SPOKEN))
    ap.add_argument("--project", default=None,
                    help="專案整包 JSON（GET /api/agent/projects/:id）。給了才驗得到 S4")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    payload = json.loads(pathlib.Path(a.payload).read_text(encoding="utf-8"))
    steps = route_step_count(pathlib.Path(a.route))
    sp = pathlib.Path(a.spoken)
    spoken = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else None
    project = None
    if a.project:
        d = json.loads(pathlib.Path(a.project).read_text(encoding="utf-8"))
        project = d.get("project", d)

    if a.self_test:
        return self_test(payload, steps, spoken)   # 負控制只有 0／1
    return run(payload, steps, spoken, project).show()


if __name__ == "__main__":
    sys.exit(main())
