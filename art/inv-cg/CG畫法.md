# 調查篇 CG 怎麼畫（2026-09-17 收成，之後每一張都照這份）

## 一、主角只有一個依據：女性。所以畫面上只准出現她的兩隻手＋她的本子

- 永遠不畫她的臉與身體；鏡頭就是她的視線（第一人稱）。
- **手**：成年女性的手，指甲短、乾淨、**不塗指甲油**，沒有戒指、手鍊、手錶；袖子是素面深色長袖。
  （他 2026-09-17 指出五張圖指甲有的有塗有的沒塗，統一成不塗。）
- **本子**：就是她買的守則本周邊，`art/items/item-rulebook.png`——厚的、磨舊的深色皮面書，書脊有凸稜、書口泛黃。
  每張都把這張圖當參考傳進去，不要讓模型自己想一本。
- **錄音機**（錄音那五場）：`art/items/item-recorder.png`——深灰直立長方形口袋錄音機，上半是圓孔喇叭網、下半是透明卡帶窗，
  頂端一排按鍵、最左那顆是紅色錄音鍵。放在櫃台上她這一側，卡帶窗朝觀者，紅色錄音燈亮著。同樣每張都傳圖。

## 二、空間一定要有俯視平面圖（`layout-guides/*.svg` → png）

沒有俯視圖的圖全部空間錯過（`rejected/` 那些）：門、街、天空跑到對方背後。規則寫在 svg 裡，四個區塊由上到下：
「對方背後只能看見的東西」→「完整實體隔板（櫃台／工作檯／桌子）」→「女主角，背對入口」→「鏡頭朝內拍」→「入口只能在玩家背後」。
現有：`clerk-counter`、`guard-counter`、`parts-counter`、`reception-counter`、`roof-workbench`、`studio-desk`。新地點就照 `clerk-counter.svg` 複製一份改字，
`python3 -c "import cairosvg; cairosvg.svg2png(url='x.svg', write_to='x.png', output_width=1600, output_height=900)"`。

## 三、提示詞骨架（Codex image-edit，`codex-imagegen.sh <prompt> <out> <參考圖…>`）

參考圖順序固定：**1 前一版或畫風錨（既有 CG）、2 俯視圖、3 錄音機、4 守則本**（要換人物立繪／背景再往後加）。
提示詞照 `rebuild-direction-manifest.json` 那幾條的寫法：
「Edit reference image 1. Reference image 2 is a TOP-DOWN FLOOR PLAN and must control spatial direction, not visual style.
Image 3 is the EXACT recorder …（把外觀寫出來）… Image 4 is the EXACT notebook …
Female protagonist appears ONLY as her two hands and this notebook … short clean UNPAINTED nails, no rings …
CAMERA AND PROTAGONIST are on the customer side facing inward; the entrance is BEHIND THE CAMERA and must not appear.
<對方> sits/stands behind a continuous solid <隔板>. Directly behind <對方> show only <那一側的東西>. Absolutely no <入口／街／天空／窗> anywhere.」

## 四、驗收（每張都要看）

1. 對方背後沒有門、街、天空、玻璃、電梯。
2. 錄音機跟 `item-recorder.png` 同一台（紅鍵在左、上網下窗）。
3. 本子跟 `item-rulebook.png` 同一本。
4. 手：不塗指甲油、沒飾品；只有手，沒有臉。
5. 人物跟立繪同一個人（髮型、眼鏡、衣服）。
過了才 `ffmpeg -vf scale=1536:-1 -quality 85` 轉 webp 進 `art/inv-cg/`，再用 `larch/add_tape_cgs.py`（先讀線上再補）掛上去。
**換圖要用新檔名**（媒體庫照檔名快取，同名會拿到舊圖）。
