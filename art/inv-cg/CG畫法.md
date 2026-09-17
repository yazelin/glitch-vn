# 調查篇 CG 怎麼畫（2026-09-17 收成，之後每一張都照這份）

## 一、主角只有一個依據：女性。所以畫面上只准出現她的兩隻手＋她的本子

- 永遠不畫她的臉與身體；鏡頭就是她的視線（第一人稱）。
- **手**：成年女性的手，指甲短、乾淨、**不塗指甲油**，沒有戒指、手鍊、手錶。
  指甲要每張一致（指甲油不會天天換）；**袖子不用一致**（衣服天天換，他 2026-09-17 說的），提示詞裡不要限定袖子。
  沒有正式人設，「不塗」是 2026-09-17 照多數既有 CG 定的；他要改成塗，就全部一起改。
- **本子**：就是她買的守則本周邊，`art/items/item-rulebook.png`——厚的、磨舊的深色皮面書，書脊有凸稜、書口泛黃。
  每張都把這張圖當參考傳進去，不要讓模型自己想一本。
- **錄音機**（錄音那五場）：`art/items/item-recorder.png`——深灰直立長方形口袋錄音機，上半是圓孔喇叭網、下半是透明卡帶窗，
  頂端一排按鍵**剛好四顆：一紅（最左）三黑**（提示詞要寫 EXACTLY FOUR，模型會自己多畫一顆；2026-09-17 材料行那張畫成五顆，他抓到的）。
  **立著放**在櫃台上她這一側（跟道具圖一樣直立，不是平躺），正面朝觀者、
  按鍵在正上方那條邊、紅色錄音燈亮著。同樣每張都傳圖。（2026-09-17 第一次寫「lying on the counter」，四張變成平躺、按鍵跑到側邊，
  只有諾亞那張自己立起來——他抓到的，之後一律寫 STANDS UPRIGHT。）

## 一之二、場景裡固定的東西（畫錯過的）

- **斑比工作室那面牆＝兩年份格莉奇的直播截圖**：同一個人（格莉奇，銀白短髮、青色眼睛、深色連帽衫）幾十張小圖釘滿整面牆，
  螢幕上也是她。參考 `cg-story-bambi-wall-v3.webp` 的牆與 `art/sprite-glitch.png`。畫成風景照或城市照就是錯的（2026-09-17 他抓到）。

- **背景要跟遊戲裡的場景圖同一間店**：每個地點都有 `art/bg-investigation/bg-<地點>-<day|evening|night>.png`，
  照那場的時段把那張傳進去當背景參考，明寫「色調與乾淨度照這張」。便利商店是台灣 7-11 那種：白牆一條綠條、日光燈、
  磨石子地、藍白冷藏櫃、咖啡機、包子蒸櫃、關東煮；深夜店內也是全亮。模型自己畫會變成灰暗倉庫（2026-09-17 店員第三版，他抓到）。
  只有錄音機／守則本那種道具是用道具圖，背景不要靠模型自己想。

## 一之三、既有 CG 還沒統一的地方（2026-09-17 對過六張的手部）

- 指甲：`golden-hat`、`lost-notebook`、`this-episode` 沒塗；`bambi-wall-v3`、`promise-v2` 是紫色指甲油。標準是**不塗**，那兩張之後要重修。
  他說 `golden-hat-v2`、`lost-notebook-v1` 的手看起來最正常——重畫時拿這兩張當手部的畫風錨；`promise-v2`、`seventh-line-v1` 的袖口也可以。
  不行的是 `this-episode-v2`（袖口抄了格莉奇的）。
- 本子：`two-minutes`、`this-episode` 畫成線圈筆記本，跟守則本（皮面、凸稜書脊）不是同一本。標準是守則本。
- 袖子：`promise` 是米白毛衣，其他深色。**不用統一**（衣服會換），但 `this-episode-v2` 的袖口跟手機畫面裡格莉奇的連帽衫袖口一模一樣——
  是模型把畫面裡那個人的衣服抄到主角手上（2026-09-17 他抓到）。畫面裡有格莉奇時要明寫「主角的袖子跟她的不同」。
  這張還有線圈筆記本要換成守則本，重畫時一起處理。

## 二、空間一定要有俯視平面圖（`layout-guides/*.svg` → png）

沒有俯視圖的圖全部空間錯過（`rejected/` 那些）：門、街、天空跑到對方背後。規則寫在 svg 裡，四個區塊由上到下：
「對方背後只能看見的東西」→「完整實體隔板（櫃台／工作檯／桌子）」→「女主角，背對入口」→「鏡頭朝內拍」→「入口只能在玩家背後」。
現有：`clerk-counter`、`guard-counter`、`parts-counter`、`reception-counter`、`roof-workbench`、`studio-desk`。新地點就照 `clerk-counter.svg` 複製一份改字，
`python3 -c "import cairosvg; cairosvg.svg2png(url='x.svg', write_to='x.png', output_width=1600, output_height=900)"`。

## 三、提示詞骨架（Codex image-edit，`codex-imagegen.sh <prompt> <out> <參考圖…>`）

參考圖順序固定：**1 前一版或畫風錨（既有 CG）、2 俯視圖、3 錄音機、4 守則本、5 該時段的場景背景圖**（要換人物立繪再往後加）。
沒有立繪的人（店員、材料行老闆、保全）就拿他既有的 CG 當人物錨，提示詞要說「只取人物，不要抄它的背景」。
提示詞照 `rebuild-direction-manifest.json` 那幾條的寫法：
「Edit reference image 1. Reference image 2 is a TOP-DOWN FLOOR PLAN and must control spatial direction, not visual style.
Image 3 is the EXACT recorder …（把外觀寫出來）… Image 4 is the EXACT notebook …
Female protagonist appears ONLY as her two hands and this notebook … short clean UNPAINTED nails, no rings …
CAMERA AND PROTAGONIST are on the customer side facing inward; the entrance is BEHIND THE CAMERA and must not appear.
<對方> sits/stands behind a continuous solid <隔板>. Directly behind <對方> show only <那一側的東西>. Absolutely no <入口／街／天空／窗> anywhere.」

## 三之二、道具要放在看得見的水平檯面上

高櫃台的圖（材料行那種）畫面下半常常整片是櫃台的**垂直正面**，道具「放在櫃台上」就會被畫在那面板子上、看起來懸空
（2026-09-17 材料行那張，他抓到的）。提示詞要明寫：畫面下方是櫃台在玩家這一側的**水平檯面**、看得到遠端的邊、
錄音機與本子放在檯面上、有影子貼著木頭。俯視圖也要標「錄音機與本子在玩家這一側的檯面」。

## 三之三、同一張圖不要一改再改

image-edit 每改一次就多一代損失，斑比那張改到第四版整張出現波紋（2026-09-17 他抓到）。一張圖最多編輯兩次；
要改的東西超過兩件，就**從立繪＋俯視圖＋道具圖重生一張全新的**，把所有要求一次寫進提示詞，不要拿舊圖當底再改。

## 四、驗收（每張都要看）

1. 對方背後沒有門、街、天空、玻璃、電梯。
2. 錄音機跟 `item-recorder.png` 同一台（紅鍵在左、上網下窗）。
3. 本子跟 `item-rulebook.png` 同一本。
4. 手：不塗指甲油、沒飾品；只有手，沒有臉。
5. 人物跟立繪同一個人（髮型、眼鏡、衣服）。
過了才 `ffmpeg -vf scale=1536:-1 -quality 85` 轉 webp 進 `art/inv-cg/`，再用 `larch/add_tape_cgs.py`（先讀線上再補）掛上去。
**換圖要用新檔名**（媒體庫照檔名快取，同名會拿到舊圖）。
