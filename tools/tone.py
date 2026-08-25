#!/usr/bin/env python3
"""掃《調查篇》的台詞，抓出走味的寫法。

**這一支是為了擋一個已經發生過的失敗。** 第一輪有五個寫手把整款寫成恐怖片，
因為這個故事的材料（熬夜、記不得、自己的字自己不認得）跟恐怖片的材料一模一樣。

抓四類：

  旁白在猜   「像是在確認什麼」。旁白只寫看得到的動作，為什麼是玩家的事
  加了溫度   「詭異」「不寒而慄」這種。旁白是冷的，跟正篇一樣冷
  金句說教   任何一句在總結主題的話。這款的主題從來不被講出來
  神祕化     把黑洞先生寫成謎團。他不神祕，他只是話少

**只掃引言行（`> ` 開頭）與粗體的台詞**，不掃設計註解，
因為註解本來就會引述這些禁止的寫法（第一版沒分開，三筆全是假陽性）。

    python3 tools/tone.py            # 印出來
    python3 tools/tone.py --check    # 有問題就 exit 1
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = sorted(ROOT.glob("design/調查篇*.md"))

PATS = [
    ("旁白在猜", re.compile(r"(像是在|似乎|彷彿|好像在|一副.{1,6}的樣子|顯然|不知道為什麼地)")),
    ("加了溫度", re.compile(r"(不寒而慄|背脊|發毛|詭異|陰森|毛骨|說不出的|莫名的|令人[一-鿿])")),
    ("金句說教", re.compile(r"(這就是|原來.{0,10}就是.{0,6}$|人生就是|的意義)")),
    ("神祕化",   re.compile(r"(謎[一-鿿]|神祕|不可思議|超乎|某種力量|命中註定)")),
]


def script_lines(text):
    """只回傳真正的台詞與旁白，跳過設計註解。"""
    for i, l in enumerate(text.splitlines(), 1):
        t = l.strip()
        if not t.startswith(">"):
            continue
        t = t.lstrip("> ").strip()
        if not t or t.startswith(("**", "|")) and t.endswith("**"):
            continue          # 「**旁白**（scene: lobby）」這種標頭
        yield i, t


def main():
    check = "--check" in sys.argv
    bad = 0
    for f in DOCS:
        hits = []
        for i, t in script_lines(f.read_text(encoding="utf-8")):
            for name, pat in PATS:
                m = pat.search(t)
                if m:
                    hits.append((i, name, m.group(0), t[:60]))
        if hits:
            bad += len(hits)
            print(f"── {f.name}（{len(hits)}）")
            for i, name, w, ctx in hits:
                print(f"  {i:5d}  [{name}] 「{w}」　{ctx}")
            print()
    print(f"掃了 {len(DOCS)} 份　{'沒有走味的寫法' if not bad else f'★ {bad} 處要看'}")
    if check:
        sys.exit(1 if bad else 0)


def selfcheck():
    """負控制：確認這些樣式真的抓得到，而且設計註解不會被誤抓。"""
    good = "> 他把信封收進外套內側，停了半拍，然後才把外套拉好。"
    bad_ = "> 他把信封收進外套內側的時候動作停了半拍，像是在確認什麼。"
    note = "*（這一場不可以寫成「像是在確認什麼」，那是旁白在猜。）*"
    hit = lambda s: [n for n, p in PATS for _ in [1] if p.search(next(iter([t for _, t in script_lines(s)]), ""))]
    assert not hit(good), "乾淨的句子被誤抓"
    assert hit(bad_), "負控制失效：該抓的沒抓到"
    assert not list(script_lines(note)), "設計註解不該進掃描"
    print("selfcheck 過：該抓的抓得到、乾淨的不誤抓、設計註解不掃")


if __name__ == "__main__":
    selfcheck() if "--selfcheck" in sys.argv else main()
