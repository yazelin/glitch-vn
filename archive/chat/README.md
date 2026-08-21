# 聊天卡：技術驗過了，劇情沒過

2026-08-21 擱置。技術可行，但**沒有故事理由**——格莉奇就站在畫面上，
對話框就在下面，再開一個聊天視窗那是網頁功能，不是劇情。
提過三個切入點（開機的空檔／傳訊息給不在的他／守則本），都不夠。

留著是因為驗證結果本身有用，之後想到理由可以直接接。

## 驗過的

`miniGame` 卡的 `miniGameHtml` 會被播放器渲染成：

```jsx
<iframe sandbox="allow-scripts" srcDoc={data.miniGameHtml} />
```

雙向橋接（`Preview-*.js`）：

| 方向 | 訊息 | 作用 |
|---|---|---|
| iframe → Larch | `larch:ready` | 要資料 |
| Larch → iframe | `larch:init` | 送 `{variables, assets, locale}` |
| iframe → Larch | `larch:set {name,value}` | 寫回故事變數 |
| iframe → Larch | `larch:complete {result,score}` | 結束這張卡 |

讀寫各有白名單，欄位是 `miniGameReadVars` / `miniGameWriteVars`。
**`miniGameReadVars` 沒填就一個變數都不給**（`Q3()` 的實作是 `if(!l.length) return {}`）。

這個白名單就是「三種記憶範圍」的實作點：格莉奇的卡只給今天的變數，
黑洞先生的卡給全部——兩個角色的差別，字面意義上就是 context window 的差別。

llmshare 的 CORS 實測（sandbox iframe 的 origin 是 `null`）：

```
access-control-allow-origin: *
access-control-allow-headers: authorization,content-type
```

通。瀏覽器可以直接打。

## 為什麼有 proxy.py

`miniGameHtml` 會原封不動送給每個玩家，金鑰寫在裡面等於公開，
而且 llmshare 是共享閘道，燒的不只是自己的額度。

所以 `proxy.py` 把金鑰留在伺服器，**人設也留在伺服器不吃前端傳的**——
前端只能說要跟誰講話，不能自己塞 system prompt。就算有人挖到端點，
他能做的也只是跟格莉奇聊天。

跑：`source ~/.bashrc && python3 proxy.py`（預設 127.0.0.1:8099）

## 沒驗到的

整條鏈沒有實際跑通過。驗的是每一段的合約，沒有真的建一張卡放進遊戲玩。
