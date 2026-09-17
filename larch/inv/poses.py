"""立繪差分的切換規則（2026-09-17 作者拍板的十張，art/inv-cast/sprite-<誰>-<姿勢>.png）。

依據是劇本裡台詞前的括號指示與旁白寫的動作（「（沒有抬頭）」「諾亞低下頭去」）。
規則只看**這一張卡的文字**；同一段落裡換過姿勢就沿用到段落結束（人不會每句話都換姿勢），
段落開頭回到基本立繪。旁白寫的是她當下知道的叫法（修收音機的、那個客人），別名表要含這些。

push.py（建置）與 larch/apply_poses.py（線上先讀再改）都用 pose_map()；兩邊算出來的表要一樣。
不碰邊、不碰變數、不碰文字：唯一改的是舞台上那個人的圖片網址。
"""
import re

# 誰 → 別名（講者名、旁白叫法、舞台演員名都可能是這些）
ALIAS = {
    "諾亞": ["諾亞", "修收音機的"],
    "貓草": ["貓草", "那個客人", "客人"],
    "斑比": ["斑比", "畫她的人", "洗衣店那個人"],
    "管理員": ["管理員"],
    "店員": ["店員", "便利商店店員"],
}
# 差分檔（沒有列的組合就是基本立繪）
FILES = {
    ("諾亞", "down"): "art/inv-cast/sprite-noah-down.png", ("諾亞", "up"): "art/inv-cast/sprite-noah-up.png",
    ("貓草", "away"): "art/inv-cast/sprite-catgrass-away.png", ("貓草", "face"): "art/inv-cast/sprite-catgrass-face.png",
    ("斑比", "away"): "art/inv-cast/sprite-bambi-away.png", ("斑比", "look"): "art/inv-cast/sprite-bambi-look.png",
    ("管理員", "report"): "art/inv-cast/sprite-admin-report.png", ("管理員", "stare"): "art/inv-cast/sprite-admin-stare.png",
    ("店員", "think"): "art/inv-cast/sprite-clerk-think.png", ("店員", "smile"): "art/inv-cast/sprite-clerk-smile.png",
}
# 誰 → [(正規式, 姿勢[, 只在本人講話時算])]，照順序第一個中的算；"base" 表示回到基本立繪（沿用就此中斷）。
# 2026-09-17 審過 105 列之後的修正：「抬頭」不可以吃到「沒有抬頭」；上來了／沿著牆走／拉窗口這種動作要回基本；
# 「停了一下」在旁白裡常是在講玩家，只在本人講話時算。
UP = r"(?<!沒有)(?<!沒)抬頭|抬起頭"
RULES = {
    "諾亞": [(r"沒有抬頭|低下頭|低著頭|繼續弄|在剝|拆開|對著燈|鉗子|工作檯上|沒有停手|沒有回頭", "down"),
           (r"上來了|站起來|走過來|坐下", "base"),
           (UP + r"|看了她|看著她|看她|轉過來", "up")],
    "貓草": [(r"沒有回頭|沒有抬頭|手機|背對|沒有看她|把杯子|看外面", "away"),
           (r"看了她一眼|看她|看著她|轉過來|回頭|下巴指|把盒子轉過來|" + UP, "face"),
           (r"很快地|站起來|把螢幕轉過來|點開", "base")],
    "斑比": [(r"對著螢幕|看著烘乾機|看著收銀台|沒有回頭|盯著|沒有抬頭|畫著|低頭|回到椅子上|轉回螢幕", "away"),
           (r"沿著牆|取下|疊起來|右下角|站起來|按了牆上", "base"),
           (r"把筆蓋|轉過來|看她|看著她|看了她|" + UP, "look"),
           (r"停了一下", "look", True)],
    "管理員": [(r"沒有抬頭|把窗口拉下來|拿起筷子|放下筷子|伸手到信箱", "base"),
             (r"報表|翻到下一頁|拿起單子|看單子", "report"),
             (r"看了她三秒|哼了一聲|停住|抱胸|想了一下|看了一眼|" + UP, "stare")],
    "店員": [(r"笑", "smile", True),        # 旁白「紙板人形…笑得跟上次一樣標準」是立牌在笑，只認店員自己的
           (r"看了立牌一眼|刷了條碼|沒有抬頭", "base"),
           (r"想了一下|停了一下|（停）|想了想", "think")],
}
NARRATORS = {"旁白", "", None}


def who_of_name(name):
    for who, al in ALIAS.items():
        if name in al:
            return who
    return None


def _lines(d):
    return d.get("dialogueLines") or [{"speaker": d.get("speaker"), "text": d.get("text")}]


def pose_of_card(d, current, why=None):
    """回傳這張卡的姿勢表 {誰: 姿勢}（含沿用）。current 是段落到目前為止的表。why 給的話記下觸發的那一行。

    一張卡是一整段對話（十幾行），舞台上的圖整張卡只有一種，所以取卡裡**第一個**指示＝卡出現時的姿勢；
    後面幾行的動作要等下一張卡才看得到（2026-09-17 斑比「（沒有回頭）…（把筆蓋拿出來）」那張抓到）。"""
    cur = dict(current); found = set()
    if why is not None:
        why.clear()
    for L in _lines(d):
        sp, tx = L.get("speaker"), L.get("text") or ""
        if not tx:
            continue
        who_sp = who_of_name(sp)
        targets = [who_sp] if who_sp else ([w for w, al in ALIAS.items() if any(a in tx for a in al)] if sp in NARRATORS else [])
        for who in targets:
            if who in found:
                continue
            for rule in RULES.get(who, []):
                rx, pose, self_only = (rule + (False,))[:3]
                if self_only and who_sp != who:
                    continue
                m = re.search(rx, tx)
                if m:
                    if pose == "base":
                        cur.pop(who, None)
                    else:
                        cur[who] = pose
                    found.add(who)
                    if why is not None:
                        why[who] = f"{sp or '旁白'}：{tx[:40]}〔{m.group(0)}→{pose}〕"
                    break
    return cur


def pose_map(segments):
    """segments = [[card_dict, ...], ...]（每段照播放順序）。回傳 {card_id: {誰: 姿勢}}，只列有差分檔的組合。"""
    out = {}
    for cards in segments:
        cur = {}
        for n in cards:
            d = n["data"]
            if d.get("type") != "dialogue":
                continue
            cur = pose_of_card(d, cur)
            hit = {w: p for w, p in cur.items() if (w, p) in FILES}
            if hit:
                out[n["id"]] = hit
    return out


if __name__ == "__main__":
    seg = [{"id": "a", "data": {"type": "dialogue", "speaker": "修收音機的", "text": "（沒有抬頭）這麼早。"}},
           {"id": "b", "data": {"type": "dialogue", "speaker": "玩家", "text": "我來問一件事。"}},
           {"id": "c", "data": {"type": "dialogue", "speaker": "旁白", "text": "修收音機的抬頭看了她一眼。"}},
           {"id": "d", "data": {"type": "dialogue", "speaker": "旁白", "text": "那個客人沒有回頭。"}},
           {"id": "e", "data": {"type": "dialogue", "dialogueLines": [{"speaker": "斑比", "text": "（沒有回頭）等一下。"},
                                                                      {"speaker": "斑比", "text": "（把筆蓋從嘴裡拿出來）只有一個人會講這個。"}]}},
           {"id": "f", "data": {"type": "dialogue", "speaker": "旁白", "text": "修收音機的上來了，一手拎著空袋子。"}},
           {"id": "g", "data": {"type": "dialogue", "speaker": "管理員", "text": "（沒有抬頭）幫我拿著。"}},
           {"id": "h", "data": {"type": "dialogue", "speaker": "旁白", "text": "她抄到第五行停了一下。斑比回到椅子上。"}}]
    m = pose_map([seg])
    assert m == {"a": {"諾亞": "down"}, "b": {"諾亞": "down"}, "c": {"諾亞": "up"}, "d": {"諾亞": "up", "貓草": "away"},
                 "e": {"諾亞": "up", "貓草": "away", "斑比": "away"},
                 "f": {"貓草": "away", "斑比": "away"},                     # 上來了 → 諾亞回基本
                 "g": {"貓草": "away", "斑比": "away"},                     # 沒有抬頭 → 管理員不是抬頭
                 "h": {"貓草": "away", "斑比": "away"}}, m                  # 停了一下是玩家的；回到椅子上 → 側身
    assert pose_map([[seg[1]]]) == {}          # 段落開頭沒有指示就是基本立繪
    print("ok")
