# 《格莉奇與黑洞先生》機制表

這份文件是 `tools/gen_docs.py` 從 Larch 專案讀出來生的，不要手改。
改完劇本跑 `python3 tools/pull.py && python3 tools/gen_docs.py`。

## 一、規模

- 天數：7
- 卡片：596（其中素材庫 134 張不在遊玩路徑上）
- 連線：680
- 變數：44

## 二、變數

| 變數 | 說明 | 預設 | 誰會動它 |
|---|---|---|---|
| `playerName` | 玩家名字：她存進 4KB 的第一格。對話中用 {{playerName}} | `記憶體` | Day 1、Day 2 |
| `slotUsed` | 已用記憶格：0–4。滿了就得決定東西去哪 | `0` | Day 1、Day 2、Day 3、Day 4、Day 7 |
| `fedCount` | 餵給黑洞先生的件數：決定門邊備用短靴堆的高度與他的描述 | `0` | Day 1、Day 2、Day 3、Day 4 |
| `givenCount` | 交給玩家保管的件數：存進核心硬碟的件數 | `0` | Day 1、Day 2、Day 3、Day 4、Day 6、Day 7 |
| `routeCat` | 貓叫聲的去處：keep / feed / give | `` | （沒有卡片會動） |
| `routeStar` | 那顆星的去處：keep / feed / give | `` | （沒有卡片會動） |
| `ruleLine` | 守則最後一條：玩家替她寫的那一條 | `` | （沒有卡片會動） |
| `routeName` | 你的名字的去處：keep / feed / give。決定結局 | `` | （沒有卡片會動） |
| `recallCat` | 貓叫的回想結果：玩家有沒有記住那聲貓叫：right／wrong／空=沒交給玩家 | `` | （沒有卡片會動） |
| `recallStar` | 星星的回想結果：玩家有沒有記住那顆星：right／wrong／空=沒交給玩家 | `` | （沒有卡片會動） |
| `breadRoute` | 麵包的去處：eat=他吃了／keep=她自己記住／give=交給玩家 | `` | （沒有卡片會動） |
| `overwrote` | 被擠掉的那件事：cat／star／空。4KB 滿了強制覆蓋時記錄 | `` | （沒有卡片會動） |
| `witness` | 玩家留下的那句話：麵包遞出那一刻，玩家寫給明天的她 | `` | （沒有卡片會動） |
| `dayCount` | 第幾天：迴圈計數,從 1 開始 | `1` | Day 1、Day 3、Day 4、Day 5、Day 6、Day 7 |
| `ruleVersion` | 守則版本：每天填完空位就 +1 | `1004` | Day 1、Day 2、Day 3、Day 4、Day 5、Day 6、Day 7 |
| `holeFeet` | 黑洞先生的腳數：餵他 +1、沒餵 -1;立繪與靴子堆跟著變 | `6` | Day 1、Day 2、Day 3、Day 4、Day 5 |
| `dejaVu` | 似曾相識指數：她開始覺得今天好像發生過 | `0` | Day 2、Day 4 |
| `savedOk` | 玩家有沒有存檔：0=沒存,隔天她會不認識你 | `0` | Day 1 |
| `fedToday` | 今天餵過他沒有：每天早上歸零,一天只吃得下一個 | `0` | Day 1、Day 2、Day 3、Day 4、Day 5 |
| `todayEvent` | 今天抽到的事件：random 抽出來的編號 | `0` | Day 2、Day 4 |
| `usedNote` | 紙條事件用過了：事件池去重 | `0` | Day 1 |
| `usedPicture` | 門口的畫用過了：事件池去重 | `0` | （沒有卡片會動） |
| `usedBoot` | 少一隻靴子用過了：事件池去重 | `0` | （沒有卡片會動） |
| `ruleLine1` | 第一天寫的守則：玩家親手打的字,後面會被引用 | `` | Day 1 |
| `ruleLine2` | 第二天寫的守則：同上 | `` | Day 2 |
| `breadState` | 麵包在哪：fridge=冰箱／player=玩家保管／hole=他保管／eaten=被吃／self=她自己記住 | `fridge` | Day 3 |
| `countedFeet` | 她數過他的腳沒有：Day 5 她第一次數。前面一直「她從來不數」 | `0` | Day 4 |
| `ruleLine3` | 第三天寫的守則：玩家親手打的字 | `` | Day 3 |
| `ruleLine4` | 第四天寫的守則：玩家親手打的字 | `` | Day 4 |
| `ruleLine5` | 第五天寫的守則：玩家親手打的字 | `` | Day 5 |
| `ruleLine6` | 第六天寫的守則：玩家親手打的字 | `` | Day 6 |
| `usedPlant` | 歪著長的植物用過了：事件池去重 | `0` | Day 4 |
| `usedReceipt` | 凌晨三點的收據用過了：事件池去重;麵包前史碎片 | `0` | Day 4 |
| `usedButton` | 口袋裡的鈕扣用過了：事件池去重 | `0` | Day 4 |
| `usedFlour` | 水槽的麵粉痕跡用過了：事件池去重;麵包前史碎片 | `0` | Day 4 |
| `usedMap` | 牆上的地圖用過了：事件池去重 | `0` | Day 4 |
| `todayRoute` | 今天的去處：當天中午那件事送去哪:keep/feed/give | `` | Day 4、Day 5 |
| `usedDoorNote` | 門墊紙條已用：事件池去重 | `0` | Day 4 |
| `blankPage` | 空白頁怎麼處理：tear/keep/ask | `` | Day 6 |
| `handoverLine` | 託付麵包時說的話：玩家替她寫的那句 | `` | Day 6 |
| `breadKept` | 麵包託給他了：Day 6 交出去=1 | `0` | Day 6 |
| `toldHer` | 玩家告訴她了：Day 7 中午有沒有把 Day 3 的記憶還她 | `0` | Day 7 |
| `ending` | 結局：A-full/A-eat/B/C | `` | Day 7 |
| `overwroteCount` | 被擠掉過幾件：記憶體滿了還硬塞,被擠掉的件數 | `0` | Day 4 |

## 三、每天的選擇與後果

### Day 1・你是誰

**第一天・中午｜填空 → `playerName`**：你是新來的吧？我沒印象。不過我對誰都沒印象，所以這不算什麼。

**第一天・中午｜「今天要跟他說謝謝」這件事，要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - `usedNote` 設為 `1`
    - `slotUsed` 加 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `usedNote` 設為 `1`
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `usedNote` 設為 `1`
    - `givenCount` 加 `1`

**第一天・夜晚｜填空 → `ruleLine1`**：這個空位你幫我填。寫一句話，給明天的我。

**第一天・夜晚｜存檔了嗎？**

- 1. 我存好了。
    - `savedOk` 設為 `1`
- 2. 我不想存。
    - `savedOk` 設為 `0`

### Day 2・靴子與裂痕

**第二天・早晨｜填空 → `playerName`**：那……可以再告訴我一次嗎？這次記得存。

**第二天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - `slotUsed` 加 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`

**第二天・夜晚｜填空 → `ruleLine2`**：第 {{ruleVersion}} 版的空位。今天換這一句。你幫我寫。

**這天會依狀態分岔的地方**

- `savedOk` ＝ `0` → 你是誰？
- `todayEvent` ＝ `1` → 事件1
- `todayEvent` ＝ `2` → 事件2
- `todayEvent` ＝ `3` → 事件3
- `usedPicture` ＝ `1` → 事件2
- `usedBoot` ＝ `1` → 事件3

### Day 3・麵包

**第三天・中午｜「冰箱裡有一塊我做的麵包」這件事，要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - `slotUsed` 加 `1`
    - `breadState` 設為 `self`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `breadState` 設為 `hole`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `breadState` 設為 `player`

**第三天・深夜｜填空 → `ruleLine3`**：空位在這裡。今天要留什麼給明天的我？

**這天會依狀態分岔的地方**

- `breadState` ＝ `hole` → 他吃掉了
- `breadState` ＝ `self` → 她留著

### Day 4・數靴子

**第四天・中午｜要還一件給她嗎？**

- 1. 還給她（她今天會記得，明天照樣忘）
    - `givenCount` 加 `-1`
    - `slotUsed` 加 `1`
- 2. 先留著（等更值得的時候）
    - （不動變數）

**第四天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - （條件：`slotUsed` ≥ `4`）`overwroteCount` 加 `1`
    - （條件：`slotUsed` ≥ `4`）`todayRoute` 設為 `keep`
    - （條件：`slotUsed` ≥ `4`）`usedPlant` 設為 `1`
    - `slotUsed` 加 `1`
    - `todayRoute` 設為 `keep`
    - `usedPlant` 設為 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `todayRoute` 設為 `feed`
    - `usedPlant` 設為 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `todayRoute` 設為 `give`
    - `usedPlant` 設為 `1`

**第四天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - （條件：`slotUsed` ≥ `4`）`overwroteCount` 加 `1`
    - （條件：`slotUsed` ≥ `4`）`todayRoute` 設為 `keep`
    - （條件：`slotUsed` ≥ `4`）`usedReceipt` 設為 `1`
    - `slotUsed` 加 `1`
    - `todayRoute` 設為 `keep`
    - `usedReceipt` 設為 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `todayRoute` 設為 `feed`
    - `usedReceipt` 設為 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `todayRoute` 設為 `give`
    - `usedReceipt` 設為 `1`

**第四天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - （條件：`slotUsed` ≥ `4`）`overwroteCount` 加 `1`
    - （條件：`slotUsed` ≥ `4`）`todayRoute` 設為 `keep`
    - （條件：`slotUsed` ≥ `4`）`usedButton` 設為 `1`
    - `slotUsed` 加 `1`
    - `todayRoute` 設為 `keep`
    - `usedButton` 設為 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `todayRoute` 設為 `feed`
    - `usedButton` 設為 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `todayRoute` 設為 `give`
    - `usedButton` 設為 `1`

**第四天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - （條件：`slotUsed` ≥ `4`）`overwroteCount` 加 `1`
    - （條件：`slotUsed` ≥ `4`）`todayRoute` 設為 `keep`
    - （條件：`slotUsed` ≥ `4`）`usedFlour` 設為 `1`
    - `slotUsed` 加 `1`
    - `todayRoute` 設為 `keep`
    - `usedFlour` 設為 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `todayRoute` 設為 `feed`
    - `usedFlour` 設為 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `todayRoute` 設為 `give`
    - `usedFlour` 設為 `1`

**第四天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - （條件：`slotUsed` ≥ `4`）`overwroteCount` 加 `1`
    - （條件：`slotUsed` ≥ `4`）`todayRoute` 設為 `keep`
    - （條件：`slotUsed` ≥ `4`）`usedDoorNote` 設為 `1`
    - `slotUsed` 加 `1`
    - `todayRoute` 設為 `keep`
    - `usedDoorNote` 設為 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `todayRoute` 設為 `feed`
    - `usedDoorNote` 設為 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `todayRoute` 設為 `give`
    - `usedDoorNote` 設為 `1`

**第四天・中午｜這件事要放哪裡？**

- 1. 留在我這裡（明天睡醒就忘了）
    - （條件：`slotUsed` ≥ `4`）`overwroteCount` 加 `1`
    - （條件：`slotUsed` ≥ `4`）`todayRoute` 設為 `keep`
    - （條件：`slotUsed` ≥ `4`）`usedMap` 設為 `1`
    - `slotUsed` 加 `1`
    - `todayRoute` 設為 `keep`
    - `usedMap` 設為 `1`
- 2. 給黑洞先生吃（他會長回一隻腳）
    - `fedToday` 加 `1`
    - `fedCount` 加 `1`
    - `holeFeet` 加 `1`
    - `todayRoute` 設為 `feed`
    - `usedMap` 設為 `1`
- 3. 交給你保管（留得住，但你要回來）
    - `givenCount` 加 `1`
    - `todayRoute` 設為 `give`
    - `usedMap` 設為 `1`

**第四天・傍晚｜填空 → `ruleLine4`**：空位在這裡。今天要留什麼給明天的我？

**這天會依狀態分岔的地方**

- `givenCount` ≥ `1` → 對了。我好像有東西寄在你那邊。你
- `todayEvent` ＝ `1` → 事件1
- `todayEvent` ＝ `2` → 事件2
- `todayEvent` ＝ `3` → 事件3
- `todayEvent` ＝ `4` → 事件4
- `todayEvent` ＝ `5` → 事件5
- `todayEvent` ＝ `6` → 事件6
- `usedPlant` ＝ `1` → 事件2
- `usedReceipt` ＝ `1` → 事件3
- `usedButton` ＝ `1` → 事件4
- `usedFlour` ＝ `1` → 事件5
- `usedDoorNote` ＝ `1` → 事件6
- `todayRoute` ＝ `feed` → 他吃掉了
- `todayRoute` ＝ `keep` → 她留著
- `todayEvent` ＝ `1` → 痕跡1
- `todayEvent` ＝ `2` → 痕跡2
- `todayEvent` ＝ `3` → 痕跡3
- `todayEvent` ＝ `4` → 痕跡4
- `todayEvent` ＝ `5` → 痕跡5
- `todayEvent` ＝ `6` → 痕跡6

### Day 5・他請假

**第五天・中午｜這個中午她只做一件事。你要她做什麼？**

- 1. 去數門邊的靴子（他昨天叫她不要數）
    - `todayRoute` 設為 `d5-a1`
- 2. 問他「以前」是什麼時候
    - `todayRoute` 設為 `d5-a2`
- 3. 什麼都不做，就坐在原地
    - `todayRoute` 設為 `d5-a3`

**第五天・傍晚｜填空 → `ruleLine5`**：空位在這裡。今天要留什麼給明天的我？

**第五天・傍晚｜填空 → `ruleLine5`**：空位在這裡。今天要留什麼給明天的我？

**第五天・傍晚｜填空 → `ruleLine5`**：空位在這裡。今天要留什麼給明天的我？

**這天會依狀態分岔的地方**

- `todayRoute` ＝ `d5-a1` → 守則引子（a1）
- `todayRoute` ＝ `d5-a2` → 守則引子（a2）

### Day 6・那一頁不是我寫的

**第六天・中午｜這頁空白守則，你要她怎麼處理？**

- 1. 撕掉（那不是她的格式）
    - `blankPage` 設為 `tear`
- 2. 留著空白，什麼都不動
    - `blankPage` 設為 `keep`
- 3. 在頁緣寫「晚上你寫」
    - `blankPage` 設為 `ask`

**第六天・中午｜填空 → `handoverLine`**：她要對黑洞先生說一句話，好讓他分得出「吃」跟「保管」的差別。

**第六天・傍晚｜填空 → `ruleLine6`**：空位在這裡。今天要留什麼給明天的我？

**這天會依狀態分岔的地方**

- `blankPage` ＝ `tear` → 旁白
- `blankPage` ＝ `keep` → 旁白

### Day 7・麵包

**第七天・中午｜你手上還留著她那天說的話。她說：「我的手記得怎麼包保鮮膜，可是我的腦不記得為什麼要包。」**

- 1. 還給她（她會知道自己為什麼烤）
    - `toldHer` 設為 `1`
    - `slotUsed` 加 `1`
- 2. 先不說（讓她自己想）
    - （不動變數）

**第七天・中午｜最後一件事。這塊麵包要放哪裡？**

- 1. 留給黑洞先生（放回桌上，等他回來）
    - `ending` 設為 `A`
- 2. 她自己吃掉（腦子記不住，至少讓身體記得）
    - `ending` 設為 `B`
- 3. 交給你保管（她再也不會記得，但你會）
    - `ending` 設為 `C`
    - `givenCount` 加 `1`

**這天會依狀態分岔的地方**

- `breadState` ＝ `player` → 選擇
- `fedCount` ≥ `1` → 我吃不下了。

## 四、結局

最後一天的結局由兩件事決定：中午把麵包放到哪裡，以及**這一週餵過黑洞先生幾次**。

- **結局A・放回桌上**（`ending` = `A`）
- **結局B・舌頭會記得**（`ending` = `B`）
- **結局C・交給你**（`ending` = `C`）

「留給黑洞先生」這條路再分兩種：`fedCount` ≥ 1 時他吃不下（那塊麵包會一直放在桌上），
`fedCount` = 0 時他吃得下。前六天每一次「餵他」都在花掉他的胃，帳單開在最後一天。
