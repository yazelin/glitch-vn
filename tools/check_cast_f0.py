#!/usr/bin/env python3
"""每個角色的產出音高，對得上設計稿指定的那支參考音嗎。

    python3 tools/check_cast_f0.py                # 全角色掃一次
    python3 tools/check_cast_f0.py --self-test    # 負控制（兩個方向）

**跟 tools/scan_voice_f0.py 的分工**：那一支抓「同一個角色裡某幾句變成別人」
（句級的離群）。這一支抓「整個角色從頭到尾都是別人」（角色級的整體偏移）。
2026-09-12 之前沒有任何東西在看後者。

## 這支工具是怎麼來的

保全的參考音是 `28-原聲.wav`，**59.9 Hz**，設計稿特別註明「比黑洞先生還低，
誰都不會撞」。實際生出來是 **202 Hz**，比計畫高 3.38 倍——整整高了一個八度多，
而且落進材料行老闆（217）與櫃檯（228）中間，正好破壞那張兩軸表要避開的撞聲。
五十七句全部如此，而且**一路沒有任何檢查看得到**：

  ・`voice_batch.py` 的音高守門（F0_LO/F0_HI = 0.87/1.25）比的是「這一段對參考音」，
    可是它量參考音用的是預設的 fmin=60，**而保全的音高就在那條線上**，量不準就守不住。
  ・代聽分不出來，而且是**原理上分不出來**：強迫二選一只產生相對答案
    （「哪一半比較老」），回答不了絕對位置（「這一半是不是 60 Hz」）。

**根因是 pyin 的偵測範圍。** `librosa.pyin` 要給 fmin/fmax，超出範圍的音高會被
折回範圍內或判成無聲。預設常用的 fmin=60 對一般人聲夠，對 59.9 Hz 的角色不夠。
所以這支一律用很寬的範圍（40–500 Hz）去量，寬到八度錯誤一定看得見——
**量測的範圍要比你預期的錯誤更寬，不然錯誤會落在範圍外而看不到。**

## 門檻

比值（產出中位數 ÷ 參考音）落在 **0.80–1.25** 算過。依據：
  ・四個正常角色實測 0.95、0.98、0.99、1.05，離 1.0 都在 5% 內
  ・壞掉的保全是 3.38（八度錯誤最少是 2.0）
中間空得很開，門檻放哪裡都行；取 0.80–1.25 是照 `voice_batch.py` 既有的
F0_LO/F0_HI 再放寬一點，跟那一支的語彙一致。
**換一批素材要重訂，不要沿用這個數字。**
"""
import argparse, collections, importlib.util, pathlib, statistics, sys, warnings

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice"
LO, HI = 0.80, 1.25
FMIN, FMAX = 40, 500      # 寬到八度錯誤一定看得見，見檔頭
SAMPLE = 25               # 每個角色抽幾句量中位數


# ── 第二層：產出的絕對音高，對得上這個角色的性別與年齡嗎 ────────────
#
# **第一層（產出對參考音的比值）只抓得到「走音」，抓不到「參考音本身就選錯」。**
# 2026-09-12 實例：店員的參考音 `20-原聲.wav` 穩定在 245 Hz（四種偵測範圍都一樣），
# 而設計稿寫他是「二十出頭男」。產出 252 Hz、比值 1.03——**第一層完全乾淨**，
# 因為它忠實複製了一個女聲。第一層問的是「有沒有照著做」，
# 第二層問的是「要做的那件事本身對不對」。
#
# 區間的依據是外部既有事實，不是這個專案的設定：
#   成年男聲說話基頻一般 85–155 Hz，成年女聲 165–255 Hz。
# 放寬到下面這組是為了留給年齡與個體差異（少年偏高、老年偏低），
# **落在灰帶不叫失敗，只標出來給人看**——這一層是指出「值得查」，不是判死。
#
# 性別與年齡全部有出處：design/調查篇-場景.md 的立繪表（「二十出頭男」
# 「四十幾歲男」「五十幾歲女」…），正篇角色見各自的設計文件。
# **推測的標「推」**，之後有人寫明了要回來改。
MALE, FEMALE = (75, 185), (155, 300)
CAST = {
    # 角色：      (性別, 合理區間, 出處)
    "管理員":      ("男", MALE,   "場景.md 立繪表：六十幾歲男"),
    "保全":        ("男", MALE,   "場景.md 立繪表：四十幾歲男"),
    "店員":        ("男", MALE,   "場景.md 立繪表：二十出頭男"),
    "材料行老闆":  ("女", FEMALE, "場景.md 立繪表：五十幾歲女"),
    "櫃檯":        ("女", FEMALE, "場景.md 立繪表：三十幾歲女"),
    "貓草":        ("男", MALE,   "問答矩陣.md：貓草二十三"),
    "諾亞":        ("男", MALE,   "voice.py：七十幾歲，MiniMax 詼諧長者"),
    "鐵塔":        ("男", MALE,   "voice.py：MiniMax 廣播主持"),
    "黑洞先生":    ("男", MALE,   "正典角色"),
    # **例外要具名並帶理由，不要用放寬門檻的方式吸收掉。**
    # 格莉奇的參考音 glitch.wav 本來就是 422 Hz，那是刻意的角色設定（AI 主播的高音），
    # 不是選錯素材。產出 368／380 忠實複製了它，第一層比值 0.87／0.90 也正常。
    # 把全域上限從 300 拉高來消掉這兩個誤報的話，這一層對所有高音角色就整個失效了
    # ——而高音正是它該看的地方。所以只給這兩個自己的區間。
    # 這條適用於之後所有的例外：放寬門檻會連帶讓所有還沒出現的問題一起被吸收。
    "格莉奇":      ("女", (300, 470), "刻意的高音設定，參考音 glitch.wav 就是 422 Hz"),
    "畫面裡的她":  ("女", (300, 470), "跟格莉奇共用 glitch.wav"),
    "玩家":        ("女", FEMALE, "2026-09 拍板玩家固定女性"),
    "旁白":        ("女", FEMALE, "推：沿用玩家那條線"),
    "斑比":        ("女", FEMALE, "推：設計稿只寫「畫她的人」，沒寫性別"),
    "0x":          ("女", FEMALE, "推：AI 角色，沒寫性別"),
    "大學生":      ("男", MALE,   "推：正篇第六章路人，共用管理員的參考音"),
}


def f0(path):
    """回 (中位數, 有音高的幀數)。**量不到回 (None, 幀數)，不是回 None。**

    2026-09-12 踩過：這一支原本量不到就回 None，而呼叫端把 None 從樣本裡濾掉，
    於是「這個檔量不出基頻」跟「這個檔不存在」共用同一個結果。
    我因此回報過「十五次生成有一次沒拿到 voiceUrl」——**檔案一直都在**，
    是一句 1.10 秒的短台詞（「這裡不能站。」）pyin 一幀都抓不到。
    那個假訊號害人去查一個不存在的缺陷。

    **量不到跟東西不在是兩件事，不可以共用一個回傳值。**
    今天同一個形狀出現過五次：尾巴壞掉（量到的是靜音）、B 比較老（量到的是相對量）、
    57 條死網址（量到的是舊表）、參考音 59.9 Hz（量到的是雜訊）、這一次。
    """
    import numpy as np, librosa
    warnings.filterwarnings("ignore")
    y, sr = librosa.load(str(path), sr=16000)
    f, _, _ = librosa.pyin(y, fmin=FMIN, fmax=FMAX, sr=sr)
    f = f[~np.isnan(f)]
    return (float(np.median(f)) if len(f) > 10 else None), len(f)


def by_speaker():
    spec = importlib.util.spec_from_file_location("gv", ROOT / "tools/gen_voice.py")
    gv = importlib.util.module_from_spec(spec); sys.modules["gv"] = gv
    spec.loader.exec_module(gv)
    d = collections.defaultdict(list)
    for u in gv.utterances():
        p = OUT / f"{u[3]}.mp3"
        if p.exists():
            d[u[0]].append(p)
    return d


def scan(only=None):
    import voice as V
    files = by_speaker()
    print(f"{'角色':<10}{'參考音':>9}{'產出中位':>10}{'比值':>8}{'句數':>6}  ")
    bad = []
    for who in sorted(files, key=lambda w: -len(files[w])):
        if only and who != only:
            continue
        ref = V.VOICE.get(who)
        if not (ref and ref[0]):
            continue
        rp = pathlib.Path(ref[0])
        if not rp.is_absolute():
            rp = ROOT / ref[0]
        if not rp.exists():
            print(f"{who:<10}{'參考音不在':>9}"); continue
        rf, _ = f0(rp)
        _res = [f0(p) for p in files[who][:SAMPLE]]
        got = [v for v, _n in _res if v]
        unmeasurable = len([1 for v, _n in _res if v is None])   # **單獨數，不要默默丟掉**
        if not rf or not got:
            print(f"{who:<10}{'量不到':>9}"); continue
        med = statistics.median(got)
        r = med / rf
        ok = LO <= r <= HI
        # 第二層：產出的絕對區間對不對得上性別
        g = CAST.get(who)
        note = ""
        if g:
            sex, (glo, ghi), _src = g
            if not (glo <= med <= ghi):
                note = f"　▲ {sex}聲該落在 {glo}–{ghi}，產出 {med:.0f}"
        print(f"{who:<10}{rf:>9.1f}{med:>10.1f}{r:>8.2f}{len(got):>6}  "
              f"{'' if ok else '★ 走音（比值超出 %.2f–%.2f）' % (LO, HI)}{note}"
              f"{'　（另有 %d 句量不到，沒算進中位數）' % unmeasurable if unmeasurable else ''}")
        if not ok:
            bad.append((who, "走音", r))
        if note:
            bad.append((who, "區間", med))
    return bad


def self_test():
    """兩個方向：已知壞掉的要紅、已知正常的不可以誤報。"""
    print("── 負控制 ──")
    print("已知壞掉的（保全，八度錯誤，重生前留著當樣本）：")
    b1 = [x for x in scan(only="保全") if x[1] == "走音"]
    print(f"  → {'○ 抓到了' if b1 else '★ 沒抓到'}")
    print("\n已知正常的（管理員）：")
    b2 = [x for x in scan(only="管理員") if x[1] == "走音"]
    print(f"  → {'○ 沒有誤報' if not b2 else '★ 誤報了'}")
    ok = bool(b1) and not b2
    print(f"\n{'PASS 負控制有效：兩個方向都動' if ok else '★ 負控制失敗，這道檢查不可信'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    bad = scan()
    print()
    if bad:
        drift = sorted({b[0] for b in bad if b[1] == "走音"})
        rng = sorted({b[0] for b in bad if b[1] == "區間"})
        if drift:
            print(f"★ 走音（產出對不上自己的參考音）：{drift}")
        if rng:
            print(f"▲ 區間可疑（產出落在性別不合的音域，多半是**參考音選錯**）：{rng}")
        return 1
    print("全部角色的產出音高都對得上參考音")
    return 0


if __name__ == "__main__":
    sys.exit(main())
