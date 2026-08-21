# 格莉奇與黑洞先生

七天的繁體中文視覺小說，做在 [Larch](https://larch.yapiflow.com) 上。

格莉奇是 VTuber，粉絲的名字就叫「記憶體」。直播的時候她旁邊有提示詞、有留言區，
所以她記得住每一個人。她卡住的那一秒，留言區刷起來，她挑一則唸出來——唸出來的才留得住。
玩家一天只有三次搶答機會，而她一天會卡住五到六次。

下播之後那些全部關掉。**而她會忘記把麥克風也關掉。** 鏡頭朝著天花板，
幾千個人都散了，只剩下沒有把分頁關掉的那一個人。

黑洞先生跟直播沒有關係。他就是室友，不上鏡，整個人活在下播之後那一段。

## 這個 repo 裡有什麼

這裡放的是**建置工具**，遊戲本體在 Larch 上。

    design/story.md          劇情設計（前提、世界規則、七天結構、結局）
    design/script/dayN.md    完整台詞。**先在這裡寫好審好，再轉成 build 腳本**
    tools/daykit.py          共用的板子建構器（卡片、連線、條件、記憶格）
    tools/build_v2_dayN.py   線上這一版的劇本。改劇本改這裡，不要只改線上版
    tools/build_dayN.py      舊前提版（板子還在專案裡，但不是入口）
    tools/pull.py            把 Larch 上的專案整包抓下來存進 backup/
    tools/gen_docs.py        從 backup/project.json 生 docs/mechanics.md
    tools/gen_site.py        生 docs/manual.html（說明書＋攻略站）
    tools/gen_about.py       生 docs/index.html（製作記錄＋介紹）
    tools/verify.py          一個指令跑完所有檢查（改完劇本跑這支）
    tools/sim_board.py       走遍一塊板子的所有玩法，抓斷線與環
    tools/check_pronouns.py  代名詞規則檢查（妳／你／全名）
    tools/check_wiring.py    驗圖本身：斷頭邊、孤島、死路、選項沒接線
    tools/check_plain.py     線上卡片的可讀性（句子太長、代名詞太密）
    tools/check_script.py    同一套規則，但掃 design/script/*.md
    （daykit.push() 會先跑 split_narration()：把寫在台詞裡的
      「（她走出去了。）」自動拆成獨立的旁白卡，不然她會把括號唸出來）
    tools/export_script.py   把線上版印成可讀劇本（分支縮排）→ docs/script.txt
    art/                     背景原始檔（開播前／直播中／天花板）
    tools/dump_board.py      把一塊板子印成可讀劇本，拿去給人審
    tools/reverse_board.py   從線上版反推出建置腳本（腳本弄丟時用）
    backup/project.json      Larch 專案的完整副本

`build_day1.py` 與 `build_day2.py` 曾經在一次暫存目錄被清空時弄丟，後來用
`reverse_board.py` 從 `backup/project.json` 反推回來（節點與連線逐筆比對過，
完全一致），現在那兩天跟其他天一樣可以重建。`backup/project.json` **一定要
進版控**，不可以再 gitignore 掉——它是唯一的完整副本。

## 改完要跑的

    python3 tools/build_v2_dayN.py   # 重建那一天
    python3 tools/verify.py          # 模擬 + 跳躍 + 變數 + speak-tw + 代名詞，離開碼非 0 就是有問題
    python3 tools/gen_docs.py        # 更新機制表
    python3 tools/gen_site.py        # 更新說明書站

## 哪一版在線上

`activeBoardId` 指到 `board-v2-day1`。舊前提那七塊板（`board-dayN`）還留在專案裡
可以對照，但玩家進去看到的是新的。兩條線 `verify.py` 都會驗。

## 二週目

Larch 的變數是專案層級、有預設值，新開一場就回預設，平台沒有 NG+。

這個遊戲不靠平台：第七天結尾把 `ngPlus` 立起來。第一天下播之後，她把玩家介紹給室友，
**如果玩家以前來過，黑洞先生會抬起頭，看向鏡頭**——他是唯一發現鏡頭還開著的人。
她不會發現，她每天都清空。

## 代名詞規則

- 「妳」只指格莉奇，「你」只指玩家，旁白用「她」指格莉奇
- 格莉奇對黑洞先生說話：句首叫名字，後面省略主語
- 他不在畫面上的時候一律寫全名，代稱會被讀成在指玩家
- `check_pronouns.py` 會擋，不要靠記性

## 機制

看 [docs/mechanics.md](docs/mechanics.md)，或 `docs/index.html`（同樣的資料，
排版過的說明書＋攻略站）。**兩份都是程式從 `backup/project.json` 生的，不要手改**——
手寫的攻略一定會跟遊戲對不上。

要開 GitHub Pages：Settings → Pages → Source 選 `main` 分支的 `/docs` 資料夾。
`docs/index.html` 就是首頁，不需要額外設定。劇透用 `<details>` 收起來，
標題沿用遊戲裡「交給你保管」的說法。

## 這個 repo 裡有劇透

`design/script/*.md` 跟 `tools/build_v2_day*.py` 是完整劇本，
`docs/mechanics.md` 是完整機制表，`docs/script.txt` 是整份劇本。
想自己玩一次的話先別看原始碼。

## 金鑰

`tools/` 底下的腳本讀 `~/.config/larch/key`，`chat/proxy.py` 讀環境變數
`LLMSHARE_API_KEY`。**原始碼裡不放金鑰**，歷史裡也沒有。

## 授權

MIT，林亞澤。角色（格莉奇、黑洞先生）的設定正典在
[ai-brain-site](https://github.com/yazelin/ai-brain-site) 的 `persona.json`。
