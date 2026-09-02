# 格莉奇與黑洞先生

一本繁體中文小說。

兩年前開台第一天來了七個人。她說，我要記住每一個來的人，我保證。

**她記得六個。**

線上閱讀：[yazelin.github.io/glitch-vn](https://yazelin.github.io/glitch-vn/)
（每一句都能點來聽）

視覺小說版：[在 Larch 上玩](https://larch.ink/play/market/yaze/glitch)（Larch 七日創作者挑戰・最佳人氣。短網址跟著帳號與 slug 走，改名就會壞；不會變的是 UUID 版 `larch.ink/play/market/a2a10427-7326-4a86-b806-c2476fc1c22a`）

六十分鐘完整遊玩：[YouTube](https://youtu.be/J9OMebCjr9Y)　·　[原始檔](https://github.com/yazelin/glitch-vn/releases/tag/v1.0-play)（330 MB，程式自動玩一次錄的，見 `tools/capture`）

## 這個 repo 裡有什麼

    novel/chNN.md            小說本文，七章。**支線不寫進來**
    novel/番外/*.md          書外的短篇，一篇一個檔，檔名就是篇名。見下面「番外」
    design/novel.md          故事聖經：主軸、七個人、角色卡、寫法規則
    design/vn-routes.json    遊玩版的七個支線點，larch/dump_routes.py 抓的
    art/                     原始美術：14 張場景、7 張立繪、23 張表情差分、11 首 BGM
    docs/                    GitHub Pages 站台，程式生的，不要手改
    tools/gen_novel.py       產生站台（首頁／本文／角色／遊玩版／sitemap／robots）
    tools/gen_og.py          生 OG 分享圖與 favicon（合成，不是生成模型畫的）
    tools/gen_art.py         批次產圖，走 .11 的 codex-image
    tools/gen_bgm.py         批次產 BGM，走 .11 的 suno-web，一律純音樂
    tools/cut_faces.py       表情差分去背（綠幕→清內部殘留→負控制驗收）
    tools/make_icons.py      PWA 圖示（從立繪按實際 ink 邊界裁，不是目測置中）
    tools/update_sw.py       用內容 hash 產 sw.js 的快取版號，別手動 bump
    tools/offline_test.mjs   離線包驗收（配負控制：沒下載時語音必須是解不出來的）
    tools/gen_intro.py       角色頁的配音：自我介紹，加上「別人怎麼說」
    tools/check_intro.py     逐段重新辨識比對原文。**判準是拼音不是字**
    tools/check_sync.py      確認格莉奇OS 與部落格的自介跟這裡是同一份
    tools/scan_voice_f0.py   量基頻，抓出被換成別人聲音的句子
    tools/say_test.mjs       自介鈕驗收（真的按下去，不是檢查 HTML 有沒有那顆鈕）
    tools/contrast_test.mjs  量算出來的顏色對比。**--ink 是面板底色不是文字色**，
                             用錯會變成黑底黑字，肉眼在某些螢幕上還「看得到一點」
    tools/prune_voice.py     清掉沒人用的配音。**--selfcheck 一定要過**（見下）
    tools/map_audio.py       小說段落對回配音檔，產生 design/audiobook.json
    larch/                   視覺小說版：一章一支 build 腳本，見 larch/README.md
    larch/cards/             插件卡（Larch 的 miniGame），單檔 HTML，見下面「調查篇」
    archive/                 舊版：做在 Larch 上的七天記憶遊戲。已經收掉

### 《調查篇》：外傳，設計中

玩家扮演一個對不明現象有興趣的普通人，在同一棟樓附近打聽格莉奇的事。
**直到最後都不能真的找到格莉奇跟黑洞先生**，那是這款最大的規矩。

    design/調查篇.md              總設計：這個故事在講什麼、核心迴圈、硬約束
    design/調查篇-場景.md         十二個地點、線索表、問答矩陣、關係與解鎖
    design/調查篇-變數.md         **實作的時候唯一要看的表**：誰讀誰寫、七個閘誰打開
    design/調查篇-信心.md         他的信心怎麼掉下來：四次遭遇、三階段筆記、最後那一頁
    design/調查篇-第一天-定稿.md  第一天，16 格 81 張卡
    design/調查篇-橋段.md         第一批六場
    design/調查篇-第二天.md       第二天，初稿
    larch/cards/board.html        調查板：選地點、算遇到誰、時間往前走
    larch/cards/notes.html        調查筆記：名單／目擊／問答／空白頁
    larch/cards/host.html         假的 Larch 宿主，開發用
    art/bg-investigation/         七張新場景背景

**動這條線之前先讀 `design/調查篇.md` 的「零、這個故事在講什麼」。**
那一節是用來擋一個具體的失敗：材料（熬夜、記不得、自己的字自己不認得）
跟恐怖片的材料一模一樣，不先讀就會寫成恐怖片。已經發生過一次。

驗收：

    node tools/card_test.mjs           # 實跑 postMessage 契約，sandbox 跟正式一樣
    python3 tools/vars.py              # 掃出所有變數，抓命名衝突
    python3 tools/vars.py --cards      # 比對插件卡跟設計文件有沒有分家
    python3 tools/tone.py              # 掃台詞有沒有走味（旁白在猜／加溫度／金句／神祕化）
    python3 tools/gen_page.py          # 重生玩家筆記那幾頁（行首 ~ 代表被劃掉）

## 改完要跑的

    python3 tools/gen_novel.py    # 重生站台（四頁＋sitemap／robots）
    python3 tools/gen_og.py       # 只有改標題或換主角立繪的時候才要重跑
    python3 tools/sample_palette.py --write   # 換立繪之後重量顏色，寫進 design/palette.json
                                  # 改了 CSS 的 :root 要一起改 palette.json 的 site，
                                  # 不然 gen_novel 會擋下來（那份資料就是色卡的來源）
    python3 larch/dump_routes.py  # 改了支線之後，把遊玩版那一頁的資料抓下來
    python3 larch/build_all.py    # 重建 Larch 上的七章
    python3 tools/update_sw.py    # 動到 docs/ 就要跑，不跑瀏覽器不知道有新版
    node tools/offline_test.mjs   # 動到 sw.js 或離線清單就要跑
    node tools/contrast_test.mjs  # 動到配色就要跑
    python3 tools/gen_intro.py    # 只重生「唸出來的字或表演指示變了」的
    .venv/bin/python tools/check_intro.py --reroll 3   # 驗發音，錯的自動重生
    python3 tools/check_sync.py   # 改了自介就要跑：另外兩個站是複製過去的
    python3 tools/map_audio.py    # 改了小說正文或 VN 台詞就要跑
    python3 tools/prune_voice.py  # 只列不刪。**要刪之前先跑 --selfcheck**：
                                  # 它 glob 的是檔名，而保留清單只裝 v-<hex>，
                                  # 所以角色頁那 15 段自介曾經被整批誤刪過

## 角色頁的配音

兩種：**自我介紹**（一個角色一段）與**別人怎麼說**（一個角色對另一個角色的看法）。
都在 `tools/gen_intro.py` 的 `INTRO` 與 `VIEWS` 裡，跟全書共用同一組參考音，
**不可以另外選角**：角色頁聽到的聲音跟書裡不是同一個人的話，這個功能就是反效果。

「別人怎麼說」**只寫書裡真的有交集的組合**（諾亞與黑洞先生在樓梯口點過頭、
鐵塔請斑比重畫本子、聯動企劃是兩邊經紀人談的），而且**只放觀察不放事件**：
寫「我看他每天七點回來」可以，寫「他跟我說過他為什麼留下來」不行，那等於在正文之外偷加一場戲。

### 驗收：判準是拼音，不是字

`check_intro.py` 逐段重新辨識再比對原文。一開始只比整段字串相似度，結果 103 字的
自介裡「記憶體」唸成「記物體」、「口頭禪」唸成「口頭呢」，相似度還有 0.96，
檢查照樣綠燈。**局部的錯字被整段長度稀釋掉了**，是使用者自己聽出來的。

現在逐一比對每個差異的拼音：

    同音同調   她→他、立繪→例會、勢→室      ASR 分不出來，不是配音的問題
    同音不同調 背(bèi)→杯(bēi)、數(shù)→書(shū)  聲調唸錯，列成「要聽」
    不同音     憶(yì)→物(wù)、禪(chán)→呢(ne)   唸錯字，直接判 FAIL

### 自介有三份

音檔與逐字稿的唯一事實來源在這裡，**格莉奇OS 與部落格各複製一份過去**
（SW 的 scope 只到各站底下，指到 `/glitch-vn/` 的音檔離線抓不到）。
而複製是靠人記得，已經漏過一次：改寫了黑洞先生的自介、推了小說站，
另外兩個站停在舊版，是使用者聽出來的。改完自介一定要跑 `tools/check_sync.py`。

### 挑好的那一版要放進 picked

同一句生幾版挑一版是常態，而**挑好的那一版被下一次重生蓋掉就回不來了**
（gen_intro 生成前會先 unlink 舊檔）。使用者指名的錄音放
`art/voice/intro/picked/<slug>.mp3`，gen_intro 就不再生它，直接複製那一份出去，
`--all` 也蓋不掉。這跟書裡台詞的 `art/voice/picked.json` 是同一件事。

### 唸錯了怎麼修

**先分清楚是系統性的還是手氣。** 同一句生六版：

- 六版全錯 → 系統性，用同音替身（`voice.SUB`）。「零失誤」被唸成「零一五」、
  「背得出來」的背唸成 bēi，都是這種。真的救不了就改寫，
  「口頭禪」那個 chán 音六版全錯而且替身也救不了，那句話就不要用那個詞。
- 一半一半 → 手氣，替身沒有用，**重生幾版挑一版**：`check_intro.py --reroll 3`。

**voice_batch 看到 wav 已存在就跳過**，所以改了文字直接跑會得到「要生 0」而且不報錯。
`gen_intro.py` 自己記帳（`art/voice/intro-take.json`）比對送進模型的字與指示，變了才刪舊檔重跑。

## 離線（PWA）

站台是可安裝的離線 App。快取分兩層：`SHELL`（六頁＋manifest＋icon＋字型，每次
部署換版）與 `ASSET`（立繪、場景、612 句語音，只有同名檔換內容才動）。共用一個
版本名的話，改一行字就把二十幾 MB 音檔整包刪掉重抓，而 `cache.put` 失敗是靜默的。

**語音不放 install。** 那是全有全無的窗口，排最後、檔案最大的最容易靜默掉，症狀
是「圖都在、按播放沒有聲音」。改成頁尾一顆按鈕，下載完回頭逐項 `cache.match`
實查才敢說「已可離線」，不准數 fetch 成功次數，配額不足時 fetch 照回 200。

**字型自架，不要用 Google Fonts CDN**（跨域，SW 快取不到，離線一定壞）。只切站上
真的用得到的 1184 字。**加新文字之後要重切**，不然新字會掉到系統字型。

    NODE_PATH=$(npm root) node ~/pwa-skill/tools/pwa-check.mjs docs   # 在有 playwright 的 repo 底下跑

## 番外

正文之外的短篇，多半是**有人問了什麼，而那個答案用講的不如用寫的**。
放 `novel/番外/`，一篇一個檔，跑 `gen_novel.py` 就會出現在站上的「番外」那一頁。

```markdown
<!-- 內部筆記包在 HTML 註解裡，publish 的時候會整段拿掉 -->

# 篇名

日期：2026-08-24
起因：有讀者看完全書之後問……

---

正文（排版跟正文七章同一套）
```

**起因要公開。** 這一頁的價值有一半在「有人問了什麼，所以補了這一段」，
只放故事的話讀者看不出它為什麼存在。內部的正典檢查清單留在註解裡。

**加了新文字之後要重切字型**，不然新字會掉到系統字型，同一行兩種臉：

    python3 ~/pwa-skill/tools/selfhost-font.py --family "Noto Serif TC" --weights 400,600 \
        --out docs/fonts --chars-from docs/*.html

番外**不進 VN**。遊玩版是七章加謝幕，這條線不動。

## 小說與遊玩版的分界

**小說站讀到的是完整七章，沒有選項。** 這是使用者定的規矩：
先把讀的人當一般讀者，讓他們讀到好的劇本，再來考慮要不要讓他參與。

視覺小說版多了立繪、場景、表情差分、配樂，以及每章一個支線。
**支線只決定鏡頭停在哪一樣東西上，主線一個字都不會變**，三條走完接回同一張卡。
讀者不在故事裡：沒有角色對他說話，也沒有記憶考題。
那一頁在 `docs/vn.html`，資料來源是 `design/vn-routes.json`。

## 寫作規則

寫在 `design/novel.md` 第六節。三條最重要的：

- **寫散文，不寫劇本。** 有景、有內心、有整段敘述。
- **她很聰明，只是記性不好。** 壞掉的只有取出記憶那一步。
  不可以寫成「欸？我有答應過嗎？」，那是她連事實都沒有了。
- **不是每一段都要跟記憶有關。** 至少一半的篇幅是這些人在過他們的生活。

交稿前跑 `~/speak-tw/bin/speak-tw novel/*.md`。

## 授權

**雙軌**：小說正文、立繪、配音與站台內容是 **CC BY-NC 4.0**（見 `LICENSE`），
工具與程式碼是 **MIT**（見 `LICENSE-CODE`）。兩者都是林亞澤。

創作內容可以自由分享改作、須標示出處、不可商用；商業使用含角色授權要先問過。
角色（格莉奇、黑洞先生）的設定正典在
[ai-brain-site](https://github.com/yazelin/ai-brain-site) 的 `persona.json`。
