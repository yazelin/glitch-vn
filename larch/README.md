# Larch 小說版

專案：**格莉奇與黑洞先生（小說版）** `project-13660cd5-81d0-4142-9264-5ccd99a3d889`

小說本文在 `../novel/`，這裡是把它改編成視覺小說的那一層。
**這是改編不是轉檔**：小說裡誰在講話是靠上下文讀出來的，視覺小說要指名道姓，
還要決定誰站在哪、哪幾句併成一張卡。那是判斷，不是解析，所以一章一支手寫的腳本。

    novelkit.py      板子建構器（場景、旁白、對話、留言區、章末）
    build_chNN.py    一章一支。改內容改這裡，不要只改線上版
    upload.py        素材上傳 → assets.json
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

## 場景特效

場景卡吃 `visualEffect`，官方範例裡確認過的值只有這五個：

    rain  snow  embers  flash  stars3d

另外還吃 `bgm` / `bgmVolume` / `bgmLoop`。

第一章的客廳與茶几用 `snow`——書裡電視播的就是「雪」，
而且第七章有一句「電視上的雪下了好幾層」。

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
