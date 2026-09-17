"""旁白與玩家筆記裡不能出現她不知道的名字（2026-09-17 他抓到）。

講者名那層是 push.DISPLAY（鐵塔→經紀人、貓草→客人、諾亞→修收音機的），
但旁白正文「諾亞低下頭」「貓草坐在靠窗那一桌」還是把名字講出來了。
全劇沒有人對她說過「諾亞」；「貓草」她只知道是聊天室的 ID，
要到手辦店格莉奇那支片子喊「貓草！」才知道那個客人就是他。
所以旁白一律用她看到的樣子，筆記的來源標籤跟講者名一致。
保留的：格莉奇喊的「貓草！」、玩家問的「有一個 ID 叫貓草」（講者不是旁白，碰不到）。

build.py（產 board.json，配音管線讀它）與 patch_live.py（改線上）都呼叫這一支。
"""
import re

NARRATOR = "旁白"
PROSE = {"諾亞": "修收音機的", "貓草": "那個客人"}
NOTE_LABEL = {"諾亞：": "修收音機的：", "貓草：": "客人："}


def _prose(t):
    for k, v in PROSE.items():
        t = t.replace(k, v)
    return t


def _note(t):
    for k, v in NOTE_LABEL.items():
        t = re.sub(rf"(?m)^{k}", v, t)
    return t


def hide_names(d):
    """就地改一張 dialogue 卡的 text／dialogueLines；回傳改了幾處。"""
    if d.get("type") != "dialogue":
        return 0
    n = 0
    holders = d.get("dialogueLines") or [d]
    for h in holders:
        t = h.get("text") or ""
        if h.get("speaker") == NARRATOR:
            new = _prose(t)
        elif h.get("speaker") == "玩家" and (d.get("title") or "").startswith("筆記："):
            new = _note(t)
        else:
            continue
        if new != t:
            h["text"] = new; n += 1
            if h.get("speakText"):
                h["speakText"] = _prose(h["speakText"]) if h.get("speaker") == NARRATOR else _note(h["speakText"])
    return n


if __name__ == "__main__":
    d = {"type": "dialogue", "speaker": "旁白", "text": "諾亞低下頭去。貓草坐在靠窗那一桌。"}
    assert hide_names(d) == 1 and d["text"] == "修收音機的低下頭去。那個客人坐在靠窗那一桌。"
    d = {"type": "dialogue", "title": "筆記：管理員：很高", "speaker": "玩家", "text": "管理員：很高。\n諾亞：金色的帽子。\n貓草：她講過「我室友」。"}
    assert hide_names(d) == 1 and d["text"] == "管理員：很高。\n修收音機的：金色的帽子。\n客人：她講過「我室友」。"
    d = {"type": "dialogue", "dialogueLines": [{"speaker": "旁白", "text": "玩家走過去。貓草把手機拿起來。"},
                                              {"speaker": "玩家", "text": "有一個 ID 叫貓草。你聽過嗎。"}]}
    assert hide_names(d) == 1 and d["dialogueLines"][1]["text"].count("貓草") == 1
    d = {"type": "dialogue", "speaker": "格莉奇", "text": "貓草！"}
    assert hide_names(d) == 0
    print("ok")
