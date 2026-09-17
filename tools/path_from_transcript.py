#!/usr/bin/env python3
"""把自動玩家的逐字稿（tools/autoplay.mjs 的 transcript.txt）整理成劇情路徑資料。

    python3 tools/path_from_transcript.py <transcript.txt> --board <線上版子快照.json> [--out design/調查篇-劇情路徑.json]

輸出一棵樹：opening → days[] → steps[]（每個時段一步：去哪、選什麼、板上的便條、對話、筆記、收到的 CG 與錄音帶）→ ending。
tools/gen_guide.py 拿它產 docs/guide/path.html（劇情路徑）。給人看，也給 AI 看。

逐字稿的坑：打字機效果會先印半句再印整句（同講者、後一行以前一行開頭），要去掉前一行。
CG 解鎖卡在逐字稿裡只有「新的調查篇紀念 CG 已加入收藏。」沒有標題：標題從版子算——
這一步選的段落（或當下的插播）沿邊走到哪幾張解鎖卡，照順序對上。
"""
import argparse, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "larch/inv"))

SLOTS = ["上午", "下午", "晚上", "深夜"]
# 路線上真的錄的五場（larch/inv/clear_stage.py AUTOREC 同一份）
TAPE_OF = {"問諾亞那個穿西裝的": "錄音・諾亞", "問斑比她一個人住嗎": "錄音・斑比", "問店員那個穿西裝的": "錄音・店員",
           "問老闆那個穿西裝的": "錄音・材料行老闆", "聽他講": "錄音・保全"}
CG_LINE = re.compile(r"^新的調查篇(角色)?紀念 CG 已加入收藏。$")
BOARD_RE = re.compile(r"^=== 板 第 (\d+) 天 ・ (\S+) \| 便條：(.*?) \| 可去：(.*)$")


def norm(t):
    return re.sub(r"\s+", "", t or "")[:20]


def cg_map(board_path):
    """解鎖卡前一張對話的文字（去空白取前 20 字）→ CG 標題。逐字稿裡 CG 那一行的前一行就是那張對話。"""
    b = json.loads(pathlib.Path(board_path).read_text(encoding="utf-8"))
    b = b.get("project", b); b = next(x for x in b["boards"] if x["id"] == "board-main") if "boards" in b else b.get("board", b)
    by = {n["id"]: n for n in b["nodes"]}; inn = {}
    for e in b["edges"]:
        inn.setdefault(e["target"], []).append(e["source"])
    m = {}      # 同一張來源卡後面可能接兩張解鎖卡（十四樓第六次：「第六次」與「兩分鐘」），所以是清單、照邊的順序
    for n in b["nodes"]:
        t = n["data"].get("title") or ""
        if not t.startswith("解鎖："):
            continue
        p, seen = n["id"], set()
        while p and p not in seen:
            seen.add(p); p = (inn.get(p) or [None])[0]
            if p and by[p]["data"].get("type") == "dialogue" and (by[p]["data"].get("text") or "").strip():
                d = by[p]["data"]
                txt = (d.get("dialogueLines") or [{}])[-1].get("text") if d.get("dialogueLines") else d.get("text")
                m.setdefault(norm(txt), []).append(t.replace("解鎖：", "")); break
    return m


def dedupe(lines):
    out = []
    for sp, tx in lines:
        if out and out[-1][0] == sp and tx.startswith(out[-1][1]) and len(tx) >= len(out[-1][1]):
            out[-1] = (sp, tx)
        else:
            out.append((sp, tx))
    return out


def parse(path, cgs):
    steps, opening, ending = [], [], []
    cur = None; pending_cg = []
    box = opening          # 現在的台詞往哪裡收
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        ln = raw.rstrip()
        m = BOARD_RE.match(ln)
        if m:
            day, slot, note, dests = int(m.group(1)), m.group(2), m.group(3), m.group(4)
            cur = {"day": day, "slot": slot, "slotIdx": SLOTS.index(slot) if slot in SLOTS else -1, "boardNote": [s.strip() for s in note.split(" / ") if s.strip()],
                   "open": [d.strip() for d in dests.split("、") if d.strip()], "go": None, "menu": [], "pick": None, "lines": [], "cg": [], "tapes": []}
            steps.append(cur); box = cur["lines"]; continue
        if ln.startswith("→ 去 ") and cur:
            cur["go"] = ln[4:].strip(); continue
        if ln.startswith("  選單（") and cur:
            cur["menu"] = [s for s in ln[4:].rstrip("）").split("、") if s]; continue
        mp = re.match(r"^\s*→ 選「(.*)」\s*$", ln)
        if mp and cur:
            cur["pick"] = mp.group(1); cur["tapes"] = [TAPE_OF[cur["pick"]]] if cur["pick"] in TAPE_OF else []; continue
        if ln.startswith("  謝幕  "):          # 謝幕版子的卡：前綴不同；那張 CG 就是「調查篇・謝幕」
            rest = ln[len("  謝幕  "):].strip()
            if CG_LINE.match(rest):
                box.append(("__cg__", "調查篇・謝幕"))
            elif rest:
                sp, _, tx = rest.partition(" "); box.append((sp if tx else "", (tx or sp).strip()))
            continue
        if ln.startswith("  調查篇  ") or ln.strip() == "調查篇":
            rest = ln[len("  調查篇  "):] if ln.startswith("  調查篇  ") else ""
            if not rest.strip():          # 空的一行（打字機剛開始）不是台詞，也不可以當 CG 的前一行
                continue
            if CG_LINE.match(rest.strip()):
                box.append(("__cg__", rest.strip())); continue
            # 打字機效果：CG 那句也會先印「新的」「新的調查篇紀念 CG 已」「CG」這種半截，不是對話
            if norm(rest) and (norm(rest) in norm("新的調查篇角色紀念 CG 已加入收藏。") or norm(rest) in norm("新的調查篇紀念 CG 已加入收藏。")):
                continue
            sp, _, tx = rest.partition(" ")
            if not tx:               # 沒講者的卡（畫面字）
                sp, tx = "", sp
            box.append((sp, tx.strip()))
    # 結局：第 14 天上午不開板，收尾插播直接接在第 13 天深夜那一步後面；從那句旁白切開
    if steps:
        last = steps[-1]["lines"]
        cut = next((i for i, (sp, tx) in enumerate(last) if sp == "旁白" and tx.startswith("早上下樓的時候看一下信箱那邊")), None)
        if cut is not None:
            ending = last[cut:]; steps[-1]["lines"] = last[:cut]
    # 去重、把 CG 行換成標題（用前一行對話的文字對；謝幕那張在別的版子上，逐字稿看不到）
    def finish(lines):
        lines = dedupe(lines); got = []; out = []; used = {}
        for sp, tx in lines:
            if sp == "__cg__":
                if tx == "調查篇・謝幕":
                    got.append(tx); continue
                prev = norm(out[-1][1]) if out else ""
                if prev not in cgs:       # 打字機沒印完就切到 CG 卡（少最後一個「。」）：允許前綴對
                    prev = next((k for k in cgs if len(prev) >= 8 and (k.startswith(prev) or prev.startswith(k))), prev)
                cands = cgs.get(prev, []); k = used.get(prev, 0); used[prev] = k + 1
                got.append(cands[k] if k < len(cands) else (cands[-1] if cands else f"？{tx}"))
            else:
                out.append([sp, tx])
        return out, got
    opening, _ = finish(opening)
    for s in steps:
        s["lines"], s["cg"] = finish(s["lines"])
        # 逐字稿裡玩家寫本子的段落沒有標記：拿最後一段夠長的玩家獨白當這一步的筆記
        s["note"] = next((tx for sp, tx in reversed(s["lines"]) if sp == "玩家" and len(tx) >= 30), None)
    ending, ending_cg = finish(ending)
    days = []
    for s in steps:
        if not days or days[-1]["day"] != s["day"]:
            days.append({"day": s["day"], "steps": []})
        days[-1]["steps"].append(s)
    return {"source": str(path), "opening": opening, "days": days, "ending": ending, "endingCg": ending_cg}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("transcript"); ap.add_argument("--board", required=True)
    ap.add_argument("--out", default=str(ROOT / "design/調查篇-劇情路徑.json")); a = ap.parse_args()
    data = parse(a.transcript, cg_map(a.board))
    pathlib.Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(d["steps"]) for d in data["days"]); cg = sum(len(s["cg"]) for d in data["days"] for s in d["steps"]) + len(data["endingCg"])
    tapes = [t for d in data["days"] for s in d["steps"] for t in s["tapes"]]
    print(f"{len(data['days'])} 天 {n} 步、CG {cg} 張、錄音帶 {len(tapes)} 卷 {tapes}、開場 {len(data['opening'])} 句、結局 {len(data['ending'])} 句 → {a.out}")
    for d in data["days"]:
        for s in d["steps"]:
            print(f"  {s['day']}|{s['slotIdx']} {s['go'] or '—'}：{s['pick'] or '—'}　台詞 {len(s['lines'])}　CG {s['cg']}　筆記 {'有' if s['note'] else '無'}")


if __name__ == "__main__":
    main()
