# 格莉奇 Live2D 分層

來源：`../sprite-glitch.png`（598×1536）→ Lanczos 2 倍 → 1196×3072。
Real-ESRGAN 在這台機器吐全黑圖，別去試。

| 檔案 | 內容 |
|---|---|
| `glitch.psd` | 34 層，Cubism Editor 直接匯入 |
| `layers/*.png` | 全畫布透明 PNG，**檔名前綴＝疊放順序**（小的在後） |
| `build.py` | 切層＋補洞＋合成眼皮與嘴形。座標寫死在 `LAYERS` 裡 |
| `mkpsd.py` | 堆 PSD。需要 venv：`python3 -m venv .venv --system-site-packages && .venv/bin/pip install pytoshop` |
| `final_body.png` / `final_head.png` | 驗收圖：原圖／預設姿態／閉眼張嘴 |

## 兩條規則

**切**：由前往後，每層取「自己的多邊形 ∩ 還沒被前面的層拿走」。

**補**：只補「被排在我上面的層拿走的像素」，加 12px 安全邊，夾在角色輪廓內。
用整個多邊形當補的範圍會蓋掉鄰居 — 這個錯誤犯過三次，症狀是脖子、裙頭、
肩膀出現深色橫帶。

眼、眉是**獨立層**（不參與搶像素），因為瀏海本來就蓋在它們上面；
但 `50_hair_front` 要排除眼睛橢圓，否則虹膜與睫毛符合「髮色」條件會被瀏海收走。

## 驗收

`build.py` 跑完後，把 34 層疊回去（隱藏 22/23 眼皮與 42-46 嘴形）跟原圖比：
平均色差 1.6/765，色差大於 90 的像素 0.42%。這個數字壞掉就是切法動到了。

## 層表（後 → 前）

```
01_particles   glitch 方塊          58_hood        帽子
05_hair_back   後髮                 59_skirt       裙
10_face_base   臉底（合成）          60_neck        脖子
20/21 eye_R/L  眼      ← 獨立層      61_choker      頸環
22/23 lid_R/L  眼皮（合成）          62_hoodie      帽T（含背帶／貼片／帽繩／口袋）
30/31 brow_R/L 眉      ← 獨立層      70/71 hand_L/arm_L
40_mouth       閉嘴                 73/74 hand_R/arm_R
42-46 mouth    A/I/U/E/O（合成）     80_bag         包
50_hair_front  瀏海                 86_strap_hang  垂下的吊帶
55_clip        髮夾＋天線            95/96 warmer_L/R  襪套
56/57 leg_L/R  腿（右腿含黑襪腿環）    98/99 shoe_L/R    鞋
```

## 已知限制

- **臉底是合成的**，不是原畫。額頭用中位膚色平塗，殘留一點眉睫的痕跡。
  它只在轉頭與眨眼時露出一點點，可用；要更好就人手重畫這一張。
- **嘴形五種是幾何畫的**。原圖的嘴只有 25×6 px，放大也撐不起 A/I/U/E/O，
  沒有原畫可切。顏色取自原圖唇線 `(142,104,112)`。
- **眼皮的睫毛是畫的弧線**，不是原畫的睫毛。複製原睫毛像素會變成黑塊。
- 補洞是平塗延伸，大面積的洞（帽T 在手臂底下）會偏平，Cubism 裡看得出來但蓋得住。

## 接下來

1. Windows 分割區（`nvme0n1p3`）裝 Cubism Editor，匯入 `glitch.psd`。
2. 綁標準參數：`ParamAngleX/Y/Z`、`ParamEyeLOpen`、`ParamEyeROpen`、
   `ParamMouthOpenY`、`ParamMouthForm`、`ParamBodyAngleX`、`ParamBreath`。
   命名要照官方，Larch 才驅動得動。
3. FREE 版限制：1 張貼圖 ≤2048px、100 ArtMesh、30 參數、50 變形器、30 part。
   34 層在額度內，緊的是貼圖尺寸。
4. 匯出 runtime 檔 → GitHub repo **保留目錄結構** → jsDelivr →
   Larch 素材包加一筆 `remote: true` 指到 `glitch.model3.json`。
   `POST /media` 會給亂數扁平檔名，把 model3.json 的相對路徑打斷，不能走那條。

---

# 在 Ubuntu 用 Wine 跑 Cubism Editor（2026-09-05 實測可行）

Cubism Editor 官方只支援 Windows 10/11 與 macOS，**但 Wine 跑得起來**。

**關鍵事實：Cubism Editor 是 Java 程式**（bundled JRE ＋ JOGL 走 OpenGL），
不是原生 Direct3D 應用。所以 DXVK 根本用不到（裝了也沒壞事），真正在做事的是
Wine 的 OpenGL，那一塊成熟得多。實測拿到：

```
OpenGL Version : 4.6 (Core Profile) Mesa 25.2.8
Renderer       : Mesa Intel(R) Graphics (RPL-P)
```

## 環境

- Wine **9.0**（Ubuntu 24.04 內建就夠，不必升到 10.x，省掉 sudo）
- prefix `~/.wine-cubism`（win64），DXVK 已裝但用不到
- 安裝：`WINEPREFIX=~/.wine-cubism wine Live2D_Cubism_Setup_5.3.04.exe /S`
  （NSIS 靜默安裝，247 MB，exit 0）
- 下載頁掛 Cloudflare Turnstile，**curl 抓不到安裝檔，要人工點**

## 啟動：用 `run-cubism.sh`

授權在 Wine 下**不會跨重啟記住**，每次啟動要過兩個對話框，腳本都處理掉了：

1. `Start` 對話框 — 第 4 顆 `Start as FREE version`（**第 3 顆是 42 天 PRO 試用，別按**）
2. `Confirm` 對話框 — `Welcome! Start as FREE version with limited functions` → OK

## GUI 自動化的四個坑

1. **點擊前一定要 `xdotool windowactivate`。** 沒有焦點的話 `xdotool click` 靜默失效。
2. **`xwd` 要抓 client 不能抓 frame。** 視窗清單列出的是 `mutter-x11-frames` 外框，
   抓它只會拿到背景。要先 `xwininfo -id <frame> -children` 找出 `java.exe` 那個子視窗。
3. **`xwd -root` 在 Xwayland 下回 `BadMatch`**，抓不了整個桌面，只能一個視窗一個視窗抓。
4. **Swing 選單是輕量元件，畫在主視窗裡，不是獨立 X 視窗**，所以視窗清單看不到，
   截主視窗也常常抓不到。**改用鍵盤快捷鍵**：`Ctrl+O` 會開出獨立的 `Open` 對話框，
   那個抓得到，也能用 `xdotool type` 直接打 Windows 路徑（`C:\glitch\glitch.psd`）。

## 命令列參數可以直接帶 PSD

`run-cubism.sh 'C:\glitch\glitch.psd'` 就會開。（一度以為參數被授權對話框吃掉，
其實是那時候的 PSD 壞的，見下一節。）匯入時會跳 `Model settings` 問要怎麼處理，
預設第一項 `Create new model from PSD file` 就對，腳本自動按 OK。

要臨時開別的檔用 `Ctrl+O`，Open 對話框是獨立視窗抓得到，類型篩選是
`Cubism (*.cmo3|*.cmox|*.psd|*.can3|*.canx|*.cmp3)`。

## UI 語言

啟動腳本寫死 `-Duser.language=zh`（簡體中文）。四支 `.bat` 都改成 `en` 就是英文。
Cubism 沒有正體中文。若要留中文介面，得把系統字型連進 prefix，否則全是豆腐框：

```bash
FD=~/.wine-cubism/drive_c/windows/Fonts; mkdir -p $FD
find /usr/share/fonts ~/.local/share/fonts -type f \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.ttc' \) \
  -exec ln -sf {} $FD/ \;
```
再把 `FontSubstitutes` 的 `MS Shell Dlg` / `Tahoma` 指到 `Noto Sans CJK TC`。

## PSD 一定要自己寫，pytoshop 產的 Cubism 不吃

pytoshop 寫出來的 PSD 缺 **Image Resources 區塊**（長度 0），Cubism 解析到
Layer&Mask 段會丟：

```
Read Header:26
Read ColorModeData:4
com.live2d.graphics.psd.a: error signature ::  @ 0x00000026
```

層數本身是對的（檔案 0x2a 就是 `0x0022` = 34），純粹是容器格式問題。
`mkpsd.py` 已改成自己照 Adobe 規格組，補齊三樣：

- `8BIM 03ed` 解析度區塊（pytoshop 漏的就是這個）
- 每層的 `luni` Unicode 圖層名
- 合成影像段

壓縮用 **RLE（PackBits）**，相容性最好；ZIP 有些讀取器不吃，而 pytoshop 的 RLE
會炸 `NameError: packbits`（C 擴充沒編）。PackBits 的重複碼 `257-k` 在剩一個 byte 時
會算出 256 爆掉，要退回字面碼。自檢：`DEMO=1 python3 mkpsd.py`。

GIMP 這條放棄了：3.2.4 的 `-b` 批次在 snap 下掛住，script-fu API 又改版。

## 匯入實測結果（2026-09-05）

34 層全部進去，名稱正確，Cubism 自動生了標準參數（Angle X/Y/Z、EyeL Open、EyeL Smile），
畫布渲染正常。Profile 是 SDK5.3/Cubism5.3。

## .moc3 匯出實測成功（2026-09-05）

**整條路徑在 Ubuntu 上跑得通，不必開 Windows。** 產物在 `../../docs/live2d/model/`（放 docs 底下，GitHub Pages 直接服務）：

```
glitch.moc3                 19,328 B   MOC3 / version 5 / little-endian
glitch.model3.json             155 B
glitch.cdi3.json             2,122 B   27 個參數
glitch.2048/texture_00.png   2.4 MB    2048×2048 RGBA
```

參數 ID 都是標準命名（ParamAngleX/Y/Z、ParamEyeLOpen、ParamEyeBallX/Y、ParamBrowLY…），
Larch 驅動得動。

### 匯出的順序（漏一步就會被擋）

1. `File → Export → Runtime file` 直接按會跳 **`Invoke after texture atlas is generated.`**
2. 要先 `Modeling → Texture Atlas → Edit Texture Atlas`：2048×2048、Margin 3px、
   Layout target = Mesh、Scale 自動、允許旋轉。生完看右邊 `Unset textures only` 是空的
   才代表 34 層都排進去了。
3. 再回去匯出。Export settings 記得勾 **Export hidden ArtMeshes**，
   否則隱藏的替代層（眼皮、五個嘴形）會被靜默丟掉。

貼圖空間很夠：2048² ＝ 420 萬像素，34 層實際只佔約 180 萬。
（唯一浪費的是 `01_particles`：glitch 方塊散佈全畫布，邊界框等於整張圖，
吃掉一大格卻幾乎全透明。想省空間就把粒子拆成幾個小層。）

### 選單這一步自動化不了

File / Modeling 選單是 Swing 輕量彈出層，在 Wine 下既不是獨立 X 視窗、`xwd` 也抓不到，
xdotool 點不到。**但每個對話框本身都是獨立視窗**，抓得到也點得到，所以只有「拉開選單」
那一下要人工。

### 相容性退路

**Export Version 一定要選 SDK 5.0 或更舊。** 一開始用預設的 `For SDK 5.3 / Cubism5.3`
匯出，moc3 version byte = 6，而**公開發行的 Cubism Core 只到 5.1.0、支援的 moc3 最高是 5**，
`Moc.fromArrayBuffer` 直接回 null（不丟例外，pixi-live2d-display 只報 `Unknown error`）。
改選 SDK 5.0 重匯得到 version byte 5 就正常了。官方樣本（Hiyori）的 moc3 是 version byte 3，
所以 Larch 那邊同樣吃不下 v6——這一項跟平台收不收無關，本來就要改。

驗法（本機 Playwright，不靠目測）：

```js
Live2DCubismCore.Version.csmGetLatestMocVersion()   // Core 支援的最高版本
new Uint8Array(mocBuffer)[4]                        // 檔案自己的版本
!!Live2DCubismCore.Moc.fromArrayBuffer(mocBuffer)   // 真正的判準
```

**匯入後的 ArtMesh 名字是 `ArtMesh0`…`ArtMesh32`，不是 PSD 圖層名。** parts 也是空的。
所以 runtime 沒辦法用名字定位圖層（想在網頁端把眼皮關掉就辦不到）。
rigging 的時候要自己在 Cubism 裡把 ArtMesh 改名、編好 Part，否則之後很難處理。

## 展示頁

`docs/live2d/index.html` → <https://yazelin.github.io/glitch-vn/live2d/>
載入結果寫在 `window.__demo`（`{status, params, drawables, size}`），
用 Playwright 讀那個驗收，不判讀畫面。

---

# Larch 不收自訂 Live2D 模型（2026-09-05 實測）

把 `export/` 的模型加進素材包，`PUT /api/agent/asset-packs/<id>` 回 **403**：

> 目前只能使用 Yayapipi Studio 提供的 Live2D 官方模型；一般用戶不能上傳、匯入或替換其他 Live2D 模型。

素材包沒有被動到（123 筆原封不動，是寫入前就被擋）。**這是平台政策，不是技術問題。**

## Larch 裡 Live2D 怎麼用（讀官方示範作品得到）

`GET https://larch.ink/api/marketplace/official-live2d-breathing-stage?play=1`（免登入）

Live2D actor 跟一般立繪 actor 用同一組欄位，沒有任何專屬欄位：

```jsonc
{"id":"layer-l2d-mao", "characterId":"l2d-mao", "name":"虹色Mao",
 "url":"https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@5-r.5/Samples/Resources/Mao/Mao.model3.json",
 "slot":"left", "offsetX":0, "offsetY":0, "scale":0.78, "enter":"fade"}
```

角色定義也一樣，`portraitUrl` 直接放 model3.json。**差別只在 url 指向 `.model3.json`，
播放器自己認。** 所以我們的模型格式上完全塞得進去——但素材包端點會擋。
版子端點（`PUT /projects/:id/boards/:boardId`）也許沒有同一道檢查，
**但那是繞過平台明示的規則，不要做。**

## 這個模型能去哪

1. **跟 Larch 作者提。** 正當路徑。若對方鬆綁或願意收，直接掛上去就能動。
2. **放自己的網站。** 用 Cubism Web SDK，掛在 `yazelin.github.io/glitch-vn`
   或格莉奇 OS 站。完全自己控制，沒有平台限制，反而是更合適的家。
3. **Larch 裡繼續用靜態立繪。** 現況就是這樣，actor 掛 `loop:"breathe"` 已經有呼吸感。
