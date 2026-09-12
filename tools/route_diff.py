#!/usr/bin/env python3
"""比兩份通關逐字稿的**路線**，不是比文字。

用法：
    python3 tools/route_diff.py 基準.txt 新的.txt

**為什麼不能逐行 diff。** 逐字稿會把打字機動畫的中途狀態也記下來，
所以同一句話在兩趟裡的截斷點不一樣：

    基準  旁白 一棟舊大樓。信箱牆的漆掉
    新的  旁白 一棟舊大樓。信箱牆的漆掉了一半，第三排

那是時序雜訊，跟路線無關。2026-09-12 實測：濾掉手機、載入進度、開場選之後，
逐行 diff 還有 1504 行，而真正不同的路線決定只有 112 行。
**逐行 diff 會滿江紅，然後讓人回去找一個不存在的 bug。**

所以這支只抽兩種行：
    === 板 第 N 天 ・ 時段 | 便條：… | 可去：…     （每一次開板的狀態）
    → 選「…」                                      （每一次選了什麼）

再加檔尾那行統計（秒數忽略，那本來就每次不同）。

**它會指出第一個分岔點，並且明講分岔之前是不是完全一致。**
那一句是負控制：如果你的解釋是「某某東西在起點多消耗一次擲骰」，
它預測「分岔前完全一致」；分岔前就不一致的話，那個解釋是錯的，還有別的東西在動。

## 驗收標準是「統計一致」，不是「逐格一致」

`larch/cards/board.html` 第 262 行：

    if(Math.random()<pr || (pity>0 && c>=pity)){ out.push(v[2]); m[key]=0; }

訪客出不出現用的是**未定種子的 `Math.random()`**。自動玩家的 `SEED`
只管它自己選哪一格，管不到遊戲內部的擲骰。所以同一條指令跑兩次，
「某天某地有沒有人在」就會不同，連帶讓那一格的選單有幾格也不同。

**所以逐格重現在這個系統上本來就做不到。** 標準定成統計一致
（出門次數、每個地點的造訪數、選過幾格）**不是放寬，是這個系統的上限**。

逐格的差異仍然要看，但判準是「能不能定位到來源」：
2026-09-12 那一輪四項差異，三項定位到（秒數＝執行時間、結局從「回到標題」
變「走到謝幕」＝謝幕版子 09-12 才推上去、多一格＝上面那顆骰子），
一項部分定位（手辦店兩格對調，上游是同一顆骰子，中間傳遞路徑沒驗）。
**定位不到的差異不可以接受**——不明來源一旦封進基準，之後沒有人會發現。

要真正逐格可重現，得讓那顆骰子吃一個種子。那是改遊戲程式來服務驗收，
不在這支工具的範圍。

## 這支工具是怎麼來的（2026-09-12）

重產基準的時候路線對不上。當時的解釋是「開場多了模式卡，在起點多消耗一次擲骰，
把後面整串位移了」——聽起來很合理，而且統計上「選過 37 格」變「38 格」剛好差一，
看起來是佐證。

拿這支跑負控制，那個解釋**被推翻**：分岔不在起點，在第 2 天晚上的第 9 個決定，
而前 8 個完全一致。再去看那一格，兩邊的選單一模一樣：

    基準：  → 選「抄信箱的名牌」（PREFER）
    新的：  → 選「去信箱那邊」

真因是**舊基準是帶著 `PREFER=` 跑的**（11 處強制指定要點哪一格），
而重現指令只寫了 `SEED=3`。不是板子變了，是產生指令沒記全。

**所以這支存在的理由有兩層**：表面上是「逐行 diff 會被打字機動畫汙染」，
底下是「一個聽起來合理、統計上還有佐證的解釋，可以錯得很徹底」。
會分岔就用它定位，不要憑統計數字推原因。

**連帶的規矩：基準的產生指令必須完整記錄，一個輸入都不能漏。**
漏掉的那個一定是最關鍵的——不關鍵的漏了也看不出來。
所以 `design/調查篇-通關路線.txt` 的檔頭自己帶著產生它的完整指令。
"""
import argparse, difflib, pathlib, re, sys

DAY = re.compile(r"^=== 板 第 (\d+) 天 ・ (\S+)")
PICK = re.compile(r"→ 選「(.+?)」")
STAT = re.compile(r"^=== 統計：(.*)$")


# 判準是**通用的，不是列舉行別**：逐字稿裡的行分兩種來源——
#   一、遊戲演出來的字（開頭是「調查篇」或「謝幕」，那是台詞），以及載入進度
#   二、自動玩家自己印的（去哪裡、選了什麼、開了背包、卡住了、板面長什麼樣）
# **第二種全部納入**，因為那就是「這一輪做了什麼」；第一種全部排除，
# 因為它會被打字機動畫的截斷點汙染（見檔頭）。
#
# 唯一的例外是 `[手機]`：它是唯讀的快照，而且**貼文則數本來就會隨著改貼文而變**，
# 納進來的話「改貼文」這件預期中的事會讓路線比對變紅。手機那幾行由驗收點 B/C/D 另外比。
#
# 列舉行別行不通的理由：2026-09-12 第一版只抽「板」與「選」兩種，
# 結果 `[第一頁]`（FILLPAGE1 開背包填筆記）看不到——那是會改遊戲狀態的互動，
# 於是出現「前 78 個決定一致、可是第 79 格的選單從六格剩一格」。
# 下一種狀態互動出現時，列舉法會再瞎一次。
GAME = re.compile(r"^\s*(調查篇|謝幕)(\s|$)")
# 基準檔開頭有一段 `#` 註解（產生它的完整指令，見那個檔的檔頭）。
# 2026-09-12 中過：沒濾掉的話那段會被當成 42 個「決定」，
# 基準跟它自己的來源逐字稿比都會不一致。
HDR = re.compile(r"^\s*#")
NOISE = re.compile(r"正在把這一幕要用到的立繪與場景讀進來")
PHONE = re.compile(r"^\s*\[手機\]")


def route(path):
    """抽出這一輪「做了什麼」。回傳 [(種類, 內容, 第幾天, 時段)]。"""
    out, day, slot = [], None, None
    for raw in pathlib.Path(path).read_text(errors="replace").splitlines():
        ln = raw.strip()
        if not ln or HDR.match(ln) or GAME.match(raw) or NOISE.search(ln) or PHONE.match(raw):
            continue
        m = DAY.match(ln)
        if m:
            day, slot = int(m.group(1)), m.group(2)
            out.append(("板", ln, day, slot)); continue
        m = PICK.search(ln)
        if m:
            out.append(("選", m.group(1), day, slot)); continue
        out.append(("做", ln, day, slot))       # 去哪裡、選單長什麼樣、開背包、卡住
    return out


def stats(path):
    for ln in pathlib.Path(path).read_text(errors="replace").splitlines():
        m = STAT.match(ln.strip())
        if m:
            return re.sub(r"，\d+ 秒$", "", m.group(1))      # 秒數忽略
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("new")
    a = ap.parse_args()
    A, B = route(a.base), route(a.new)
    ka = [f"{t}|{c}" for t, c, _, _ in A]
    kb = [f"{t}|{c}" for t, c, _, _ in B]
    print(f"基準 {len(A)} 個路線決定　新的 {len(B)} 個")

    # 第一個分岔點
    n = min(len(ka), len(kb))
    first = next((i for i in range(n) if ka[i] != kb[i]), n if len(ka) != len(kb) else None)
    if first is None:
        print("路線完全一致")
    else:
        d = A[first] if first < len(A) else B[first]
        print(f"\n第一個分岔：第 {d[2]} 天 ・ {d[3]}（第 {first + 1} 個決定）")
        print(f"  基準：{ka[first] if first < len(ka) else '（到底了）'}"[:120])
        print(f"  新的：{kb[first] if first < len(kb) else '（到底了）'}"[:120])
        # **負控制**：分岔之前是不是真的完全一致
        same = ka[:first] == kb[:first]
        print(f"\n分岔之前的 {first} 個決定：{'完全一致 ○' if same else '★ 也不一致——那表示解釋錯了，還有別的東西在動'}")

    diff = [l for l in difflib.unified_diff(ka, kb, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    print(f"\n路線決定的差異：{len(diff)} 行")

    sa, sb = stats(a.base), stats(a.new)
    print(f"\n統計（秒數已忽略）\n  基準：{sa}\n  新的：{sb}\n  {'一致' if sa == sb else '★ 不一致'}")
    return 0 if (first is None and sa == sb) else 1


if __name__ == "__main__":
    sys.exit(main())
