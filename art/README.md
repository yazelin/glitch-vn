# 背景素材（新前提版）

一天三段各一張。原圖已經上傳到 Larch，這裡留一份原始檔。

| 檔案 | 用在哪 | 內容 |
|---|---|---|
| `bg-pre.jpg` | 開播前 | 同一個房間，補光燈是暗的，大螢幕只有一個等待進度環，窗外是傍晚 |
| `bg-live.jpg` | 直播中 | 補光燈開著，大螢幕是直播畫面（立繪框＋留言區＋提示欄），窗外是白天 |
| `bg-ceiling.jpg` | 下播後 | **鏡頭倒在桌上，朝著天花板。** 水泥板、管線、一盞暗掉的吸頂燈，中間偏左有一片微弱的冷光 |

`bg-ceiling.jpg` 是這一版的關鍵：下播之後玩家看不到她，只看得到天花板上的光。
所以下播後那一段的台詞卡全部不帶立繪（`daykit.Board.voiceonly`）。

## 怎麼產的

`.11` 的 gemini-web `/api/edit`，拿舊背景（縮到 1024px）當參考圖，一次生一張。
放大**不要**用 realesrgan——這台跑出來是全黑圖，而且退出碼還是 0。
1376→1920 只有 1.4 倍，LANCZOS 就夠，存成 JPEG q90 約 400KB。

存檔前一定要驗平均亮度跟標準差，全黑圖光看檔案大小是看不出來的。

## 角色立繪（2026-08-22）

`sprite-*.png` 七張，全身、透明背景。五個新角色是 codex 產的，
`sprite-glitch.png` 與 `sprite-blackhole.png` 是從 Larch 抓下來的既有素材。

站台用的 WebP 由 `tools/gen_novel.py` 生，**會先裁掉四周全透明的邊再縮**——
不裁的話每張留白不一樣，排在一起有的大有的小。裁完之後長寬比差很多，
所以版面一律照**高度**對齊。

| 檔案 | 角色 | 一眼認出來的記號 |
|---|---|---|
| `sprite-catgrass.png` | 貓草 | 胸前那枚泛黃、有裂痕的像素貓徽章 |
| `sprite-tower.png` | 鐵塔 | 右耳的冷藍色懸浮光條耳麥 |
| `sprite-zerox.png` | 0x | 右耳上方那個半透明的浮動標籤。**2026-08-22 重畫過**：第一版是亮面半透明的抽卡風，跟其他四個格格不入，改成啞光制服、扣到領口、雙手垂直對稱。她賣的是精確，不是亮 |
| `sprite-bambi.png` | 斑比 | 十指纏滿的淡紫、霓虹藍指套與膠布 |
| `sprite-noah.png` | 諾亞 | 額頭上那具鑲著真空管的雙目放大鏡 |

### 怎麼產的（踩到的兩個坑都在這）

**產圖走 codex-imagegen（`$imagegen` / gpt-image），不走 gemini-web。**

**一兩張就用本機**（序列，一張 60 到 90 秒）：

```bash
~/.claude/skills/codex-imagegen/codex-imagegen.sh "<prompt>" "<out.png>" ref-sprite.jpg </dev/null
```

**一批就用 .11 的 codex-image-service**（同一個 `$imagegen` 後端，可是有非同步 job API
＋多個 ChatGPT 帳號輪流，真的可以並行）：

```bash
B=https://ching-tech.ddns.net/codex-image
K=$(cat ~/.config/codex-image/auth)
curl -s "$B/v1/images/jobs" -H "Authorization: Bearer $K" -H 'content-type: application/json' \
     -d '{"prompt":"...","n":1}'            # → 202 {"id":"img_...","status":"queued"}
curl -s "$B/v1/images/jobs/<id>" -H "Authorization: Bearer $K"
```

端點：`/v1/images/generate`（同步）、`/v1/images/jobs`（非同步）、
`/v1/images/jobs/{id}`（查）、`/v1/vision`（看圖回文字）。2026-08-22 實測都活著。

拿 `glitch-plain` 當畫風參考圖，**綠幕**背景。一張約 60 到 90 秒，序列跑，
`</dev/null` 不能少（`codex exec` 會吃 stdin，不加會一直掛著）。

gemini-web 這條線留給文字：出點子、寫設定、審稿、玩家模擬。

**白底不能用。** 去背 skill 直接擋下白底：0X 是銀白髮、諾亞是斑白髮、斑比穿白 T，
全域白色去背會把它們靜默吃掉，而且不報錯。這五個角色身上沒有綠色，所以綠幕是安全的。

**`cutout.py check` 說殘留色邊 0，可是眼睛看得到綠。** 那支只清「碰得到畫面邊界」的
連通區域（這是對的，眼白跟反光才留得住），但髮絲之間、手臂內側那種**被主體圍住的
背景**它到不了。補了 `interior.py` 那一道才乾淨——skill 自己也寫了「驗證指標會說謊」，
負控制（貼洋紅）是唯一抓得到的方法。

**沒有量化壓縮。** 256 色會讓髮絲出現色帶，這種尺寸的立繪看得很清楚。維持原檔。

### 為什麼換掉 gemini-web 那一版

第一版是 gemini-web `/api/edit` 產的，換成 codex 之後線條、解剖、材質（皮製工具腰帶、
半透明披肩、拖鞋）整體好一階。**畫面的部分一律走 codex，gemini-web 那條線留給文字。**

代價是色調比 `glitch-plain` 深、飽和度高，粉彩感沒有那麼重。
這件事可以解釋成「格莉奇是粉彩的偶像，她周圍的人是現實的顏色」，
可是那是解釋，不是設計。要統一的話就是重畫格莉奇那一張，不是把這五張洗淡。


## 場景背景（2026-08-22）

原始檔在 `out/`，站台不吃，是給 Larch 用的。

**第一版整組跑掉了。** 我的 prompt 只寫「同樣的藍紫夜色」，codex 就往電影感的方向走：
暗很多、飽和度低很多、厚塗、有景深。跟舊的房間擺在一起像兩個美術指導。

**釘住的方式是把亮度跟上色手法寫成規則**，不要只描述顏色：

- Same overall BRIGHTNESS as the references. Do NOT make this darker or more cinematic.
- Same SATURATED blue-violet and lilac palette. Do NOT desaturate toward grey-blue.
- Same FLAT lofi-anime cel shading, minimal gradients, no depth-of-field, no bloom.

而且**參考圖給兩張**（同一個房間的不同時間），模型比較不會把單張當特例。

另外：畫到有文字的道具（守則本攤開）一定要明講「頁面必須完全空白，
不可以有任何看得懂的字」，不然會生出假中文。

## 頭像 `avatar/`

從立繪切出來的圓形頭像，七個角色各一張，512×512。用途見 `../larch/README.md`：
播放器沒有大頭照功能，這是拿立繪圖層假出來的。

### 第二到第七章的十一張（2026-08-22）

`art/bg-manifest.json` 就是那一批的 prompt，跑 `python3 tools/gen_art.py art/bg-manifest.json`。

| 檔案 | 用在哪 |
|---|---|
| `bg-booth` | 二・錄音間、視訊會議、樣品 |
| `bg-greenroom` | 三・彩排休息室 |
| `bg-studio-day` | 三・聯動直播（同一個房間，白天，補光燈開著） |
| `bg-corridor` | 三・後台走廊（感應燈一段一段熄） |
| `bg-bambi-studio` | 四・斑比的工作室 |
| `bg-apartment-hall` | 五・凌晨鎖在門外 |
| `bg-noah-shop` | 五・諾亞的收音機店 |
| `bg-stairs` | 五・樓梯口交會 |
| `bg-street-day` | 六・車站前外景 |
| `bg-office-14f` | 七・0x 公司十四樓會客室 |
| `bg-kitchen-morning` | 七・最後她去找麵粉 |

三條釘住風格的規則照抄上一批（亮度、飽和度、平塗），**再加兩條**：

- 這批大多不是那個房間，所以每一句都要寫死 `THIS IS NOT A BEDROOM. No bed, no server rack, no TV.`
  少寫的話會生出「同一張床換擺設」，那是上一批踩過的坑。
- 白天的場景（街上、十四樓、廚房）不能硬套夜色，改成**把丁香紫與青色推進陰影**，
  這樣亮度差很多也還是同一個美術指導。

驗收看的是 `亮度／標準差／色偏` 三個數字加一張九宮格對照，不是逐張點開。
