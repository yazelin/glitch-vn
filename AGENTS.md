# 給接手的人或 AI（Claude、Codex、agy 或任何 CLI）

這個 repo 是《格莉奇與黑洞先生》：七章小說、Larch 視覺小說正篇，以及外傳《調查篇》。
2026-09 的主線工作是《調查篇》（Larch 第二屆創作者挑戰，9/20 23:59 截止）。動任何東西之前先讀下面三份，順序照列。

## 先讀

1. `交接-2026-09-18.md` — 最新狀態（素材整理、全 webp、切卡、進板流暢化）。前一天在 `交接-2026-09-17.md`，更早在 `交接-2026-09-12.md`。
2. `design/調查篇.md` 的「零、這個故事在講什麼」— 不先讀會把故事寫成恐怖片，已經發生過。
3. `larch/RELEASES.md` — 每一版發了什麼、貼進市集後台的文字。**最新：調查篇 1.5，2026-09-20 已發佈，網址 https://larch.ink/play/market/yaze/glitch-inv。** 上一版 1.4 是 2026-09-18 發佈的市集 release 5。

## 現況（卡數與公式站更新於 2026-09-20，其餘為 2026-09-18 晚）

- 調查篇 Larch 專案 id 在 `larch/inv/state.json`（`project-d2fea918-…`）。正篇是另一個專案（`larch/config.py`），別搞混。
- 線上版子：925 張卡／1059 條線（含 109 張清場卡、13 個群組框；1.4 是 923／1057，1.5 多了開場書桌場景與公式站入口兩張卡），謝幕版子 7／6，公式站版子 9／8。素材庫 209 筆、沒引用 0、圖全部 webp、沒有任何網址指到正篇專案。
- 公式站：第三塊版子（id `board-f375ecf1-87ad-4a9c-b8fc-fb126c9c5000`）用 miniGame 的 iframe 嵌 `https://yazelin.github.io/glitch-vn/guide/`，由開場選單第三項進入，看完回開場書桌場景 `inv-open-desk`（現在的起點）。這些卡只存在線上，`push.py` 整包重建會洗掉；換說明站網址要改 `formula-guide` 卡裡的 HTML。說明頁內嵌時隱藏「回正篇」是 `tools/gen_guide.py` 產生的。細節見 `larch/RELEASES.md` 的 1.5。
- 語音：1479 句走 jsDelivr（`docs/voice/`），諾亞與經紀人 103 句是 Larch AI 配音留在 R2，有在用。
- 軟木板與拍立得拼版走 jsDelivr 釘 commit（`larch/inv/patch_live.py` 的 `_CDN`）；Larch 素材庫留一份給素材打包。
- 角色工坊是空的：立繪都是卡片上直接放圖的網址，不是角色。

## 鐵律（每一條都是踩過雷才寫的）

- **線上版子只能「讀下來→改→PUT 回去→對卡數線數」**，用 `larch/inv/patch_live.py`、`larch/add_*.py`、`larch/inv/swap_urls.py`、`larch/inv/split_331.py` 這一類腳本。
  `push.py` 整包重建會洗掉只在線上的東西（遊樂園五款、CG 解鎖、清場卡、切卡、姿勢差分），作者明講「樂園不可以被清掉」。推前先備份到 `larch/inv/backups/`。
- Larch API 沒有「改一張卡」的端點，所以改一張也是整塊版子 PUT；帶 `If-Match`，409 就重讀重送。502／504 不代表沒寫入，重跑前先讀回來對。
- **網頁編輯器開著舊分頁時，「網站同步」會把舊副本寫回專案**（2026-09-20 蓋掉了 agent 的三次修改，靠版本紀錄還原）。agent 改完、發佈或同步之前，先把編輯器分頁重新整理，再對一次卡數。
- **發佈只能在網頁後台按**，agent API 填不進更新說明；發佈時 remix 允許、活動標籤（第二屆創作者挑戰）要維持。更新說明先寫在 `larch/RELEASES.md` 再貼。
- 改路線、門檻、接線一定跑 `MODE=story node tools/autoplay.mjs`（一次只跑一輪）；改卡片程式一定同步三處：本機 `larch/cards/*.html`、`patch_live.py` 的替換對、線上。
- 卡片程式（調查板、手機、選單、謝幕）是整份 HTML 塞在卡片欄位裡，改本機檔線上不會變；要登記「舊字→新字」的替換對再推。同一段連改多版時要留過渡對，並把最終版塞回原本那組，驗法是三個起點各套兩次結果一樣（交接 09-18 有寫）。
- 素材：圖一律 webp 且專案內要有一份、repo 也要有原檔（作者是原創作者）；重的東西走 jsDelivr；生圖只用 Larch／本機 codex／.11 codex-image 三條。
- 秘密：Larch 金鑰 `~/.config/larch/key`、codex-image 金鑰 `~/.config/codex-image/auth`，不進 repo、不寫進卡片。
- 這個 repo 常有另一條線同時在寫（design/、build.py、push.py、docs/img 會出現未提交的改動）：**只 add 自己動的檔，不要 `git add -A`**。
- 中文：正體中文、對外文字全形標點、不用 emoji、不用「不是 X，是 Y」的假對比句。

## 常用工具

    python3 larch/inv/patch_live.py [--dry]            線上版子的所有替換對（名字、網址、卡片程式段落）
    python3 larch/inv/swap_urls.py 對照表.json [--project] [--dry]   換網址；--project 連設定與變數
    python3 larch/inv/split_331.py [--dry]             inv-331 切卡（可重跑）
    python3 tools/webp_live.py <GET /projects 快照>      找還在用的 PNG／JPG 轉 webp 到 art/live-webp/
    python3 larch/apply_poses.py                       照 design/調查篇-立繪姿勢.tsv 換姿勢差分
    MODE=story BAG=守則本 FILLPAGE1=1 node tools/autoplay.mjs   自動玩家
    python3 tools/sim_rail.py --live <快照>             照劇情軌道走的變數模擬器
    python3 tools/gen_guide.py                         產 docs/guide/（劇情路徑頁、收藏畫廊）

API 的坑（欄位形狀、條件線、配音、發佈）整理在 Claude 的記憶檔 `reference_larch_agent_api`，repo 內對應的是 `larch/README.md` 與各腳本開頭的註解。
