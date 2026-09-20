# 格莉奇遊樂園插件卡：接線規格

`park.html` 是一張 Larch `miniGame` 卡的完整原始碼，取代原本「1 張 choice 入口卡 + 5
張獨立 miniGame 橋接卡」的六卡結構。卡片自己畫選單畫面（背景／BGM／6 個按鈕），玩家選
哪一款就把內嵌 iframe 換成對應的 `glitch-park-<game>` 外部遊戲；5 款遊戲共用同一套
`larch:*` ↔ `<game>:*` 橋接協定，只差遊戲代號、state 變數名、iframe 網址三個參數。

這份文件寫給兩種人看：**接這張卡的人**（下面「卡片本體」到「下游要接的邊」）、
**改 `glitch-park-*` 那 5 個 repo 的人**（下面「內嵌遊戲協定」）。

## 卡片本體：Larch node 要設哪些欄位

```jsonc
{
  "type": "miniGame",
  "title": "格莉奇遊樂園",
  "text": "今晚想先玩哪一台？",
  "miniGameHtml": "<!-- park.html 整份內容 -->",
  "miniGameFrame": { "showTitle": false, "showButton": false },
  "miniGameSkippable": true,
  "miniGamePresentation": "fullscreen",
  "miniGameReadVars": [
    "gacha_state", "claw_state", "slots_state", "wheel_state", "pinball_state"
  ],
  "miniGameWriteVars": [
    "gacha_state", "claw_state", "slots_state", "wheel_state", "pinball_state",
    "cg_gacha_trigger", "cg_gacha_incomplete_trigger",
    "cg_claw_trigger", "cg_claw_incomplete_trigger",
    "cg_slots_trigger", "cg_slots_incomplete_trigger",
    "cg_wheel_trigger", "cg_wheel_incomplete_trigger",
    "cg_pinball_trigger", "cg_pinball_incomplete_trigger",
    "park_leave_trigger"
  ]
}
```

`miniGameWriteVars` 這份清單一定要完整——Larch 只接受在這裡列出的變數名的
`larch:set`，漏一個那個遊戲的存檔或觸發就會被靜默擋掉，不會有錯誤訊息。

## 需要哪些專案變數

| 變數 | 型別 | 預設 | 用途 |
|---|---|---|---|
| `gacha_state` / `claw_state` / `slots_state` / `wheel_state` / `pinball_state` | string | `""` | 該款遊戲自己的存檔，JSON 字串，格式由遊戲自己定義，卡片只負責讀出來轉交、存回去轉交，不解析內容 |
| `cg_<game>_trigger` | boolean | `false` | 該款遊戲「這次離開時是否完整收集」 |
| `cg_<game>_incomplete_trigger` | boolean | `false` | 該款遊戲「這次離開時沒有完整收集」，跟上面那個永遠剛好一真一假 |
| `park_leave_trigger` | boolean | `false` | 玩家在選單按「← 離開遊樂園」時設為 `true` |

`<game>` 是 `gacha`／`claw`／`slots`／`wheel`／`pinball` 五選一，所以 `cg_*_trigger` 系列共
10 個變數。新增變數走 `PUT /api/agent/projects/:projectId`（整包 project，body 包一層
`{"project": {...}, "summary": "..."}`），在 `variables` 陣列尾端 append，其餘欄位原樣送回。

## 輸出契約：卡片會在什麼時候寫什麼、送出什麼

卡片對 Larch host 只送兩種訊號，永遠是這個順序：

1. **玩完一款遊戲，遊戲送 `<game>:exit {complete}`**
   → 卡片依序送出：
   `larch:set cg_<game>_trigger = complete`
   `larch:set cg_<game>_incomplete_trigger = !complete`
   （延遲 240ms，讓前面兩個 set 有時間送達）
   `larch:complete {result:"exit", payload:{complete}}`
2. **選單按「← 離開遊樂園」（沒進任何遊戲）**
   → 卡片送出：
   `larch:set park_leave_trigger = true`
   （延遲 150ms）
   `larch:complete {result:"exit", payload:{}}`

除了正在互動的那一款遊戲自己的 `cg_<game>_trigger`／`cg_<game>_incomplete_trigger`，
卡片**不會**動到其他 9 個 trigger 變數，也不會動 `park_leave_trigger`（反之亦然）——所以
下游條件只要各自檢查自己那一組，不用擔心被別的遊戲的觸發值影響。

卡片每次被進入（`larch:init`）都固定顯示選單畫面，不記得上次選了哪一款；玩完一輪、
CG 播完再繞回這張卡，會是全新的選單畫面，不是回到剛才那個遊戲。

## 下游要接的邊（全部從 `right` handle 出發）

同一張卡的完成事件要分岔到 12 個不同去處，所以這 12 條邊都掛在 `inv-park-gacha`
（或你自己的入口卡 id）同一個 `sourceHandle:"right"` 上，靠 `data.condition` 互斥：

| 條件 | 目標 | 說明 |
|---|---|---|
| `cg_<game>_trigger==true` 且 `__larch_cg__:<hash>==false` | 該款「全收集」CG 對話卡 | 10 條裡的 5 條，`<hash>` 是全收集 CG 圖片網址算出來的 |
| `cg_<game>_incomplete_trigger==true` 且 `__larch_cg__:<hash>==false` | 該款「未集齊紀念」CG 對話卡 | 另外 5 條 |
| `park_leave_trigger==true` | 離開遊樂園後要去的地方（例如 `inv-001`） | 1 條 |
| （無條件，排最後） | 指回卡片自己 | 1 條，前面 11 條都不成立時的保底：這輪沒有新東西要秀，直接重新顯示選單 |

`__larch_cg__:<hash>` 是 Larch 內建 CG 收藏系統的偽變數，不用宣告在 `project.variables`
裡，`hash` 由 CG 圖片網址算出來（FNV-1a 後 base36），可以從既有卡片的
`data.condition` 抄，不用自己重算。

**每個 `cg_<game>_trigger`／`cg_<game>_incomplete_trigger`「全收集」跟「未集齊」各自的
CG 只會播一次**，靠的就是 `__larch_cg__:<hash>==false` 這個子條件；播過一次之後由下面
的解鎖卡把它設成 `true`，之後同一款遊戲再怎麼玩，這條邊都不會再被選中，會落到「無條
件」那條保底邊，回選單。

條件邊的巢狀結構長這樣（`match:"all"` + `conditions[]`，外層的 `variable`/`value` 是
內層第一個條件的重複，兩邊要填一樣的值）：

```jsonc
{
  "op": "eq", "kind": "variable", "match": "all",
  "variable": "cg_claw_incomplete_trigger", "value": true,
  "conditions": [
    { "op": "eq", "variable": "cg_claw_incomplete_trigger", "value": true,
      "variableLabel": "cg_claw_incomplete_trigger" },
    { "op": "eq", "variable": "__larch_cg__:4y-1tp6txt", "value": false,
      "variableLabel": "娃娃未集齊紀念" }
  ],
  "variableLabel": "cg_claw_incomplete_trigger"
}
```

CG 對話卡後面接一張 `setVariable` 卡負責解鎖：

```jsonc
{
  "type": "setVariable",
  "text": "新的遊樂園紀念 CG 已加入收藏。",
  "cgOps": [{ "id": "op-cg-claw-incomplete-gallery", "url": "<CG 圖片網址>", "mode": "unlock" }]
}
```

再接一條無條件邊指回入口卡（`inv-park-gacha`），讓玩家看完 CG 後回到選單。

## 內嵌遊戲要講的協定（給 `glitch-park-*` 那 5 個 repo）

卡片跟外部遊戲 iframe 之間的協定，5 款遊戲完全一致，只差 `<game>` 代號：

| 方向 | 訊息 | 說明 |
|---|---|---|
| 遊戲 → 卡片 | `{type:"<game>:ready"}` | 遊戲載入完成，跟卡片要存檔 |
| 卡片 → 遊戲 | `{type:"<game>:state", state}` | 回傳存檔（`state` 是 `larch:init` 拿到的 `<game>_state` 解析後的物件，沒有存檔就是 `null`） |
| 遊戲 → 卡片 | `{type:"<game>:save", state}` | 存檔有變動時送，`state` 可以是任意可 `JSON.stringify` 的物件 |
| 遊戲 → 卡片 | `{type:"<game>:exit", complete}` | 玩家離開這款遊戲，`complete` 是 boolean，代表這次是否收集完整 |
| 遊戲 → 卡片 | `{type:"glitch-park:music", action, url, muted}` | 控制共用的遊樂園主題曲（5 款遊戲共用同一份音檔，由卡片這層持有唯一的 `Audio` 物件），`action` 是 `"play"`／`"mute"` |

新增一款遊戲要動的地方：`park.html` 裡的 `GAMES` 常數加一筆（`title`、`src`）、選單
`<ul id="choices">` 加一顆按鈕（`data-game="<key>"`）、卡片 node 的
`miniGameReadVars`/`miniGameWriteVars` 各加一個變數、專案變數加
`<key>_state`／`cg_<key>_trigger`／`cg_<key>_incomplete_trigger` 三個、下游加一組
CG 對話卡＋解鎖卡＋2 條條件邊。外部遊戲那邊只要照上表協定，把 `<game>` 換成新代號即可。

## 部署與測試踩過的雷

- **`park.html` 只是本機備份，不會自動同步到線上。** 這張卡是直接用 agent API upsert
  到專案的，不在 `push.py`/`build_all.py` 的重建管線裡（跟原本遊樂園五張卡同一類）。
  改了 `park.html` 之後要自己用 `PATCH /boards/:boardId/nodes/:nodeId` 把新內容寫回線
  上，光改本機檔案線上不會變。
- **新增／覆蓋多條共用同一個 handle 的條件邊，不能用 `POST /nodes` 分批加。** 這個端
  點的 upsert 對同一個 `(source, sourceHandle)` 只會保留最新一條，一次塞多條同 handle
  不同條件的邊會互相蓋掉。要嘛一次用整塊 board 的 flat-body PUT
  （`{id,kind,mode,name,nodes,edges,summary}`，**不要**包成 `{"board":{...}}`，那樣
  server 會收下但完全不生效，卡數線數不變、版本號卻照樣往上跳，很容易誤判成「已經套
  用成功」）整批寫入，要嘛用 `PATCH` 單卡端點改卡片本體、邊另外用整塊 PUT 補。
- **大專案（近千張卡）的 agent API 常常要 40–80 秒才回應**，`curl --max-time` 抓太短
  會被判定逾時，但寫入其實已經成功。502／504／timeout 都不代表沒寫入，重試前務必先
  重新 GET 一次確認目前卡數/邊數，避免重覆寫入或誤判。
- **`cardId=X` 的單卡預覽測不出多卡路由對不對。** 用
  `GET /projects/:id/preview?cardId=X` 只能確認「這張卡自己的畫面對不對」；一旦這張卡
  完成、路由跳到範圍外的另一張卡，預覽工具顯示的「這張卡片播完了」畫面背景是跟實際
  路由結果無關的通用收尾畫面（不管是這張合併卡還是原本的舊結構都一樣），不能拿來判
  斷條件邊有沒有選對目標。要驗證某張特定卡的內容，直接對那張卡的 id 開一次
  `cardId=<那張卡>` 的預覽；要驗證完整路由，只能靠真人連續玩一輪。
