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
# 誰 → [(正規式, 姿勢)]，照順序第一個中的算；"base" 表示回到基本立繪
RULES = {
    "諾亞": [(r"沒有抬頭|低下頭|低著頭|繼續弄|在剝|拆開|對著燈|鉗子|工作檯上|沒有停手|沒有回頭", "down"),
           (r"抬頭|抬起頭|看了她|看著她|看她|轉過來|站起來|走過來|上來了", "up")],
    "貓草": [(r"沒有回頭|沒有抬頭|手機|很快地|背對|沒有看她|把杯子", "away"),
           (r"看了她一眼|看她|看著她|站起來|轉過來|回頭|下巴指|把盒子轉過來|抬頭", "face")],
    "斑比": [(r"對著螢幕|看著烘乾機|看著收銀台|沒有回頭|右下角|盯著|沒有抬頭|畫著|低頭", "away"),
           (r"抬頭|看她|看著她|看了她|把筆蓋|轉過來|停了一下|回頭", "look")],
    "管理員": [(r"報表|翻到下一頁|拿起單子|看單子", "report"),
             (r"看了她三秒|哼了一聲|停住|抱胸|抬頭|想了一下|看了一眼|放下報表|把窗口拉下來", "stare")],
    "店員": [(r"笑", "smile"),
           (r"想了一下|停了一下|（停）|想了想|看了立牌一眼", "think")],
}
NARRATORS = {"旁白", "", None}


def who_of_name(name):
    for who, al in ALIAS.items():
        if name in al:
            return who
    return None


def _lines(d):
    return d.get("dialogueLines") or [{"speaker": d.get("speaker"), "text": d.get("text")}]


def pose_of_card(d, current):
    """回傳這張卡的姿勢表 {誰: 姿勢}（含沿用）。current 是段落到目前為止的表。

    一張卡是一整段對話（十幾行），舞台上的圖整張卡只有一種，所以取卡裡**第一個**指示＝卡出現時的姿勢；
    後面幾行的動作要等下一張卡才看得到（2026-09-17 斑比「（沒有回頭）…（把筆蓋拿出來）」那張抓到）。"""
    cur = dict(current); found = set()
    for L in _lines(d):
        sp, tx = L.get("speaker"), L.get("text") or ""
        if not tx:
            continue
        who_sp = who_of_name(sp)
        targets = [who_sp] if who_sp else ([w for w, al in ALIAS.items() if any(a in tx for a in al)] if sp in NARRATORS else [])
        for who in targets:
            if who in found:
                continue
            for rx, pose in RULES.get(who, []):
                if re.search(rx, tx):
                    cur[who] = pose; found.add(who)
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
                                                                      {"speaker": "斑比", "text": "（把筆蓋從嘴裡拿出來）只有一個人會講這個。"}]}}]
    m = pose_map([seg])
    assert m == {"a": {"諾亞": "down"}, "b": {"諾亞": "down"}, "c": {"諾亞": "up"}, "d": {"諾亞": "up", "貓草": "away"},
                 "e": {"諾亞": "up", "貓草": "away", "斑比": "away"}}, m      # e：取第一個指示
    assert pose_map([[seg[1]]]) == {}          # 段落開頭沒有指示就是基本立繪
    print("ok")
