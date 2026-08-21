# 完整劇本

一天一個檔。這是**進 Larch 之前**的劇本，先在這裡寫好、審好，再轉成 `tools/build_day*.py`。

| 檔案 | 這一天播什麼 | 玩家做什麼 |
|---|---|---|
| [day1.md](day1.md) | 雜談 | 搶答 |
| [day2.md](day2.md) | 遊戲實況 | 指路 |
| [day3.md](day3.md) | 歌回 | 點歌 |
| [day4.md](day4.md) | 讀粉絲來信 | 寫信 |
| [day5.md](day5.md) | 企劃：做菜 | 只能看（＋一個要不要洩漏的選擇） |
| [day6.md](day6.md) | 提示詞掛掉 | 搶答，而且只有你答得出來 |
| [day7.md](day7.md) | 週年回顧 | 把你保管的東西講出來＋結局 |

設計依據在 [../story.md](../story.md)。

## 標記怎麼讀

| 寫法 | 意思 |
|---|---|
| `〔旁白〕` | 沒有 speaker 的 dialogue 卡 |
| `格莉奇：` / `黑洞先生：` | 有 speaker 的 dialogue 卡 |
| `留言區：` | 留言區的假留言，一次刷三到四則 |
| `【選擇】` | choice 卡 |
| `【輸入】` | input 卡 |
| `▸` | setVariable |
| `〔某某〕` 開頭的段落 | 那個分支才會走到 |

## 檢查

```bash
python3 tools/check_script.py     # 句子太長、代名詞太密
~/speak-tw/bin/speak-tw design/script/*.md
```
