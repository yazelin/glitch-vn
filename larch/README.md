# Larch 小說版

專案 id 寫在 **`config.py` 一個地方**（`PROJ`），要換專案改那一行就好。
其他腳本一律 `from config import …`。

    現在的  格莉奇與黑洞先生            project-bec1644c-0dfe-4447-86c0-0c592e2f939f
    廢棄的  …（小說版）               project-13660cd5-…  ← 做壞了，別再動
    廢棄的  …（舊版・七天記憶遊戲）      project-e14f9260-…  ← 已清空

小說本文在 `../novel/`，這裡是把它改編成視覺小說的那一層。
**這是改編不是轉檔**：小說裡誰在講話是靠上下文讀出來的，視覺小說要指名道姓，
還要決定誰站在哪、哪幾句併成一張卡。那是判斷，不是解析，所以一章一支手寫的腳本。

    config.py        專案 id 與 API（**只有這裡寫 PROJ**）
    novelkit.py      板子建構器（場景、旁白、對話、留言區、章末）
    settings.py      標題畫面、對話框樣式、封面、CG 收藏
    make_chat_avatar.py  聊天頭貼（圓形頭像放進跟立繪同尺寸的透明畫布）
    preview.py       本地預覽合成（播放器要登入，看不到自己做的東西）
    build_chNN.py    一章一支（ch01–ch07）。改內容改這裡，不要只改線上版
    build_all.py     照順序跑完七章
    verify.py        檢查：斷邊、孤島、死路、空卡、立繪對不對得上、有沒有意外分岔
    dump.py          把板子印成可讀的樣子，驗節奏用（線上要登入才玩得到）
    assets.json      素材網址

## 素材與角色：照平台的方式做，不要自己發明

Larch 自己的「角色工坊」提示詞裡寫得很清楚，skill 文件沒提：

    上傳素材   POST /media       {name, mimeType, base64, category}
               category：scene 場景／character 立繪／prop 道具
               **沒帶 category 全部會掉進道具。**

    更新角色   POST /characters  {characterId, ...要改的欄位}
               只覆蓋你傳的欄位。**帶 id 會變成新增一個重複角色，要帶 characterId。**
               差分：expressions:[{name, emotion, imageUrl, kind:"expression"}]

角色不是只有名字。`portraitUrl` 是基礎立繪，`expressions` 是表情差分，
`secrets` 是「知道但不主動說」的東西。全部沒填的話，角色工坊那一頁會顯示
「基礎立繪：尚未上傳／表情差分（0）」。

`setup.py` 跑一次就會把素材與角色弄到一致。

## 七章怎麼接起來

一章一個板子（`ch01`…`ch07`），**用 `boardJump` 卡接下一章**，不要用 `end()`：
`end()` 寫的 `chapterEnd` 是「到這裡結束」，讀者按下去就沒有下一步了。
只有第七章用 `end()`。

    c.jump("ch02", "ch02-001", "（接第二章・限時預購）")

節點 id 是 `<板子 id>-<三位數>`，所以下一章的第一張永遠是 `chNN-001`，可以直接寫死。
`verify.py` 對 `boardJump` 不判死路，對 `chapterEnd` 也不判。

## 站位跟著劇情走，不要跟著段落走

第一章犯過一次，很值得記：`stage()` 寫在每個 `# ── 二 ──` 的開頭，
結果變成「旁白說他坐在沙發上，可是台上沒有人」而且「他要等換場才會消失」。

規矩是：**旁白講到某人在場的那一句，他就要在台上；他離開的那一句，就要把他拿掉。**
`verify.py` 會抓這兩件事：

- 旁白**用某人當句首**描述他在場（「黑洞先生坐在沙發上」），可是台上沒有他
- 某人站了超過六張卡沒講話也沒被提到

只在留言區出現的人（掛 `chat-` 頭貼的）不算在場，
所以「貓草沒有回」不會被誤判成站位漏掉。

## 表情差分：卡片填 emotion 還不夠

**舞台上那個角色的 `url` 也要一起換成差分圖。** 市集的專案兩個都寫：

    卡片   data.emotion = "放聲大笑"
    舞台   stage.actors[i].url = 那個 emotion 對應的 expressions[].imageUrl

只填 `emotion` 的話畫面不會換臉。我原本就是只填 emotion，
所以連格莉奇本來就有的六張差分都等於沒在用。
`emotion` 沒有對應的差分（例如 `平靜` 而角色沒有那一張）就退回 `portraitUrl`，
市集的資料裡也是這樣，所以「平靜」可以拿來當回到基礎立繪的寫法。

對應表在兩個地方，**要一起改**：`novelkit.EXPR`（建卡片時查）
與 `setup.FACES`（上傳與寫進角色時查）。

差分是**整張全身立繪**，不是只有臉的裁切。產圖的做法見 `../art/README.md`。

## 支線：讀者不在這個世界裡

`branch()` 產生一張 `choice` 卡加上幾條短支線，每一條走完都接回主線的下一張卡。

    data: {type:"choice", text, title, choices:[字串], choiceMode:"branch",
           choicePlacement:"center"}
    邊：  sourceHandle:"choice-<i>"、targetHandle:"top"、label 就是選項文字

三條寫作規矩（使用者定的，不是我發明的）：

- **讀者只是在讀這本書的人**，不是故事裡的角色。所以選項寫的是房間裡的東西，
  不是「你要做什麼」，旁白也不對讀者說話。
- **不要出記憶考題。** 舊版那套「記住四格再回答」整個廢掉了。
- **主線一個字都不能變。** 支線只加細節，走完一律匯流。

`verify.py` 會擋：只有 `choice` 卡可以有多條出邊、出邊數要等於選項數、
每一條支線最後要落在同一張卡上。

**支線不寫進小說。** `novel/*.md` 是完整的七章、沒有選項，小說站直接從那裡生，
一路讀得完不會被打斷。支線只在小說站的「遊玩版」那一頁介紹，資料由
`larch/dump_routes.py` 從線上專案抓成 `design/vn-routes.json`，
`tools/gen_novel.py` 只讀那個檔——網站產生器不連網，介紹頁也不會跟實際做的東西漂掉。

**選項卡自己也要帶立繪。** 第一版用 `_add` 直接產生，結果台上的人在選項那一張消失、
選完又出現，跟「旁白清掉立繪」是同一個坑，而且更明顯，因為讀者會停在那一張。

## 場景特效

場景卡吃 `visualEffect`，官方範例裡確認過的值只有這五個：

    rain  snow  embers  flash  stars3d

另外還吃 `bgm` / `bgmVolume` / `bgmLoop`。

第一章的客廳與茶几用 `snow`——書裡電視播的就是「雪」，
而且第七章有一句「電視上的雪下了好幾層」。

## 演出詞彙表（2026-08-22 從市集挖的）

市集上別人發佈的作品**可以直接抓下來讀，不用登入**：

    GET https://larch.yapiflow.com/api/marketplace/{發佈 id}?play=1

回的是完整的專案 JSON。這是目前為止最有用的一份資料來源——
skill 文件與範例專案都沒有這麼完整。以下全部是從那裡讀出來的實際用值：

**舞台 `stage.actors[]`**（比 `characterLayers` 多了動畫，兩個都要寫）

    {id, url, name, slot, scale, offsetX, offsetY, enter, loop, loopSpeed, loopStrength}
    slot    left / center / right
    enter   fade zoom spring bounce blur glide riseUp swoopIn
            walkInLeft arcLeft arcRight slideLeft slideRight slideDown
    loop    breathe nod sway shiver hop pulse none

**`loop` 是關鍵。** 沒有 loop 的立繪就是一張不會動的貼圖；
市集上的作品幾乎每個角色都掛 `breathe`。

**轉場**（掛在**對話卡**上，不是只有場景卡）

    transition    fade wipeLeft wipeRight blurCut flash irisIn fadeBlack none
    transitionMs  一般 260–420

**畫面特效** `visualEffect`

    rain snow embers flash stars3d petals vignette speedLines none

**標題畫面的兩個坑**

一、**按鈕是 layer，不會自己出現。** 只放三層文字的話，畫面上一個按鈕都沒有：

    {"id":"action-start",    "kind":"button", "action":"start",    "icon":true, x,y,size,width}
    {"id":"action-continue", "kind":"button", "action":"continue", ...}
    {"id":"action-gallery",  "kind":"button", "action":"gallery",  ...}
    {"id":"languages",       "kind":"language", x,y,size}

二、**標題畫面吃的是第一張卡的背景**，不是 `projectThumbnail`。
`projectThumbnail` 是市集與列表的縮圖。所以：

    第一張卡的背景   乾淨的封面（沒有文字，文字交給 layer 畫）
    projectThumbnail 有標題燒上去的那張（縮圖要自己站得住）

**專案設定** `settings`（`larch/settings.py` 在管）

    titleScreenEnabled / titleScreen{frame, layers[{id,kind,role,x,y,size,align,width}]}
    titleCoverShade / titleCoverPositionX / titleCoverPositionY / projectThumbnail
    dialogueUi{preset, presentation, fontFamily, fontSize, nameFontSize,
               textColor, speakerColor, accentColor, borderColor,
               panelColor, panelOpacity, panelWidth, panelPadding, borderRadius}
    cgGalleryEnabled / cgGallerySource / cgGalleryItems[{url,title}]
    cursorMode / cursorImage / cursorEffects{effects:[squash,tilt,ripple,trail,particles]}
    stageFit / keepActorsInFrame / textSpeed / typingEffect / autoAdvanceDelay

**沒有這些的專案跟有這些的專案，差的是「像不像一款遊戲」。**
第一版我什麼都沒設，所以沒有開始畫面，對話框是預設的灰盒子，立繪不會呼吸。

## 用得到的兩個平台功能

從前端 bundle 挖出來的，skill 文件沒寫：

    characterLayers  一張卡可以站好幾個人，各自有 position/scale/opacity/flipX
    dialogueLines    一張卡可以裝一整段來回對話，不必一句一張卡

沒有這兩個，兩個人鬥嘴會變成點十次滑鼠，而且畫面上只站得了一個人。

## 對話框沒有大頭照這個東西

播放器的 bundle 裡 `avatar` 出現**零次**。角色資料上有 avatar 欄位，可是播放器不讀，
畫面上會出現的只有 `characterLayers`。

所以聊天的大頭貼是**用立繪圖層假的**：`art/avatar/` 那七張是從立繪切出來的圓形頭像，
掛成一個 `scale: .22`、擺在左下角的圖層。貓草人不在那個房間裡，
用小頭像剛好把「他在另一個空間」講清楚，比讓他站進客廳合理。

`chat()` 會自己認：訊息全部是同一個人講的（`"貓草：…"`），就掛他的頭像跟名字，
並且把名字前綴去掉，讀起來像聊天訊息。

## 三個踩過的坑

**旁白不要給 `speaker: ""`，整個欄位不要帶。** 實測過的行為是「沒有 speaker 的
dialogue 會變旁白」，空字串是沒驗過的狀態。

**旁白不要清掉立繪。** `narrate()` 一開始沒有帶 `characterLayers`，結果人在旁白時消失、
講話時又出現，讀起來是閃的。要讓畫面沒有人就明講 `stage()` 清空。

**右側角色不要 flipX。** 0x 耳邊的標籤、貓草胸前的徽章都是不對稱的，鏡射過去記號會跑到另一邊。

**不要用「有沒有人被引用」來清孤兒素材。** 我這樣做過一次，把還在用的立繪整組刪掉了，
因為判斷的當下角色欄位還沒寫進去。要清就用同名去重，並且以 `assets.json` 為準。

**章末要標出來。** `end()` 會寫一個 `chapterEnd`，不然 `verify.py` 分不出
「刻意的終點」跟「接漏了」。

## 舊版

舊的七天記憶遊戲在另一個專案（`project-e14f9260-…`），2026-08-22 已清空板子與變數，
素材留著。整包備份在 `../backup/project-before-wipe.json`，腳本在 `../archive/`。
**agent API 刪不掉專案**（`DELETE` 回 404），所以那個空殼還在列表上。
