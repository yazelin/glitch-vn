#!/usr/bin/env python3
"""劇本 markdown 的「讀一遍就要懂」檢查。

check_plain.py 讀的是 Larch 上的卡片，這一支讀 design/script/*.md，
讓劇本在進 Larch 之前就先過一輪。規則跟 check_plain 同一套：
句子太長、代名詞太密、旁白整句被引號包起來。
"""
import re, sys, pathlib

VAR = re.compile(r"\{\{[^}]+\}\}")
SENT = re.compile(r"[^。！？\n]+[。！？]?")
LINE = re.compile(r"^(格莉奇|黑洞先生|旁白|留言區)")

def sentences(t):
    return [s.strip() for s in SENT.findall(VAR.sub("○○○", t)) if s.strip()]

bad = []
for p in sorted(pathlib.Path("design/script").glob("day*.md")):
    text = p.read_text(encoding="utf-8")
    for i, ln in enumerate(text.split("\n"), 1):
        s = ln.strip()
        if not s or s.startswith(("#", "|", "▸", "**", "留言區：", "變數")):
            continue
        # 台詞行才檢查。清單、指示行不算。
        body = s.split("：", 1)[1] if "：" in s and LINE.match(s.lstrip("〔")) else s
        for sent in sentences(body):
            if len(sent) > 30:
                bad.append((p.name, i, f"句子 {len(sent)} 字", sent))
        for pron, cap in (("他", 3), ("她", 4)):
            n = body.count(pron)
            if n >= cap and ("黑洞先生" if pron == "他" else "格莉奇") not in body:
                bad.append((p.name, i, f"「{pron}」{n} 次", s[:40]))
        if s.startswith("〔旁白〕「") and s.endswith("」"):
            bad.append((p.name, i, "旁白整句被引號包住", s[:40]))

for f, i, why, snip in bad:
    print(f"{f}:{i}  {why}\n    {snip}")
print(f"\n掃了 {len(list(pathlib.Path('design/script').glob('day*.md')))} 個檔案，{len(bad)} 處要改")
sys.exit(0)
