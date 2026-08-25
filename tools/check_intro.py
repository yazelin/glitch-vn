#!/usr/bin/env python3
"""逐段重新辨識自介配音，比對原文，抓「唸錯字」。

**判準是拼音，不是字。** 一開始只比整段字串相似度，結果 103 字的自介裡
「記憶體」被唸成「記物體」、「口頭禪」被唸成「口頭呢」，相似度還有 0.96，
檢查照樣綠燈——**局部的錯字被整段長度稀釋掉了**。是使用者自己聽出來的。

改成逐一比對每個差異的拼音：

    同音同調   她→他、莉→力、立繪→例會、勢→室   ASR 分不出來，不是配音的問題
    同音不同調 背(bèi)→杯(bēi)、數(shù)→書(shū)   **聲調唸錯，要修**
    不同音     憶(yì)→物(wù)、禪(chán)→呢(ne)    **唸錯字，要修**

ASR 輸出常常是簡體，直接比字元會整段判成不一樣，所以先轉正體。

    python3 tools/check_intro.py          # ASR 跑一次再比對
    python3 tools/check_intro.py --cached  # 用上次的 .asr.txt，只重跑比對

要 pypinyin 與 opencc（在 .venv 裡，見 README）。ASR 借 CosyVoice 的 venv 跑，
因為 whisper 的 CUDA 相依在那邊。
"""
import difflib, json, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INTRO = ROOT / "art/voice/intro"
COSY = pathlib.Path.home() / "CosyVoice/.venv/bin/python"

ASR_SNIPPET = r'''
import sys, pathlib, whisper
m = whisper.load_model("large-v3-turbo", device="cuda")
for w in sorted(pathlib.Path(sys.argv[1]).glob("*.wav")):
    t = m.transcribe(str(w), language="zh", initial_prompt="繁體中文")["text"]
    w.with_suffix(".asr.txt").write_text(t, encoding="utf-8")
    print("  聽過", w.name)
'''


def asr():
    subprocess.check_call([str(COSY), "-c", ASR_SNIPPET, str(INTRO)],
                          env=dict(os.environ, MODELSCOPE_OFFLINE="1", HF_HUB_OFFLINE="1"))


def reroll(slugs, meta):
    """指名重生。**這是這個管線唯一有效的修法**：同一句生幾版挑一版。
    同音替身只治得了系統性的走音（「口頭禪」那種六版全錯的），
    一半一半的是手氣，替身救不了。"""
    who = sorted({meta[s]["who"] for s in slugs})
    print(f"\n重生：{'、'.join(who)}")
    subprocess.check_call([sys.executable, str(ROOT / "tools/gen_intro.py"),
                           "--only", *who])


def main():
    if "--cached" not in sys.argv:
        asr()
    from pypinyin import lazy_pinyin, Style
    import opencc
    cc = opencc.OpenCC("s2twp")
    norm = lambda t: re.sub(r"[^一-鿿 A-Za-z0-9]", "", cc.convert(t)).replace(" ", "")

    meta = json.loads((ROOT / "art/voice/intro.json").read_text(encoding="utf-8"))
    vf = ROOT / "art/voice/views.json"
    if vf.exists():
        # 「別人怎麼說」跟自介同一條管線，也要一起驗。
        for v in json.loads(vf.read_text(encoding="utf-8")):
            meta[v["slug"]] = {"who": v["who"], "text": v["text"]}
    bad, failed = 0, []
    for slug, d in meta.items():
        f = INTRO / f"{slug}.asr.txt"
        if not f.exists():
            print(f"FAIL  {slug:22s} 沒有辨識結果"); bad += 1; failed.append(slug); continue
        heard = f.read_text(encoding="utf-8")
        # 表演指示外洩：指示太長的時候會被整句唸出來
        if "台灣腔" in heard or "語氣說" in heard:
            print(f"FAIL  {slug:22s} 表演指示被唸出來了"); bad += 1; failed.append(slug); continue
        a, b = norm(d["text"]), norm(heard)
        real = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
            if tag == "equal":
                continue
            x, y = a[i1:i2], b[j1:j2]
            # 數字寫法不算（四 vs 4、七百三十 vs 730）
            if re.fullmatch(r"[0-9]+", y) or re.fullmatch(r"[0-9]+", x):
                continue
            # 大小寫不算
            if x.lower() == y.lower():
                continue
            # **含拉丁字母的片段一律跳過。** 「0x」這種 ASR 認不穩（認成 LinX、0X、零艾克斯），
            # 每一版都會報一次，而那從來不是配音的問題。
            if re.search(r"[A-Za-z]", x + y):
                continue
            # 語氣詞的聲調沒有對錯（喔／哦、嗯／恩），跳過
            if set(x) <= set("喔哦噢嗯恩啊阿耶欸唷喲呀哪") or set(y) <= set("喔哦噢嗯恩啊阿耶欸唷喲呀哪"):
                continue
            tx, ty = lazy_pinyin(x, style=Style.TONE3), lazy_pinyin(y, style=Style.TONE3)
            if tx == ty:
                continue                      # 同音同調：ASR 選錯字，不是配音的問題
            px, py = lazy_pinyin(x), lazy_pinyin(y)
            # **同音不同調不可以跳過。** 「背(bèi)→杯(bēi)」「數(shù)→書(shū)」
            # 就長這樣，而那是真的唸錯，使用者聽得出來。它也可能只是 ASR 挑錯字，
            # 所以列成「要聽」而不是直接判死。
            kind = "字音" if px != py else "聲調"
            real.append((kind, f"「{x}」({'/'.join(tx)}) 唸成「{y}」({'/'.join(ty)})"))
        hard = [r for r in real if r[0] == "字音"]
        if hard:
            bad += 1
            failed.append(slug)
        if real:
            print(f"{'FAIL' if hard else 'WARN'}  {slug:22s} {len(real)} 處")
            for kind, r in real:
                print(f"        {kind}　{r}")
        else:
            print(f"ok    {slug:22s} 拼音全對")
    print(f"\n=== {len(meta) - bad}/{len(meta)} 沒有唸錯字"
          f"（標「聲調」的要自己聽一次，那也可能只是 ASR 挑錯字）===")
    return failed, meta


def loop():
    rounds = int(sys.argv[sys.argv.index("--reroll") + 1]) if "--reroll" in sys.argv else 0
    for i in range(rounds + 1):
        if i:
            print(f"\n──────── 第 {i} 輪重生 ────────")
        failed, meta = main()
        if not failed or i == rounds:
            sys.exit(1 if failed else 0)
        reroll(failed, meta)
        if "--cached" in sys.argv:
            sys.argv.remove("--cached")


if __name__ == "__main__":
    loop()


