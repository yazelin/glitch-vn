# 格莉奇與黑洞先生

一天一圈的繁體中文視覺小說，做在 [Larch](https://larch.yapiflow.com) 上。

格莉奇的記憶體只有 4KB，每天睡醒清空。黑洞先生是她的室友，白天上班，
永遠吃不飽，會把她忘掉的東西吃掉。玩家是她的外接記憶體。

每天中午會有一件小事，玩家決定它的去處：留在她的 4KB、給黑洞先生吃、
或是交給玩家保管。七天之後結帳。

## 這個 repo 裡有什麼

這裡放的是**建置工具**，遊戲本體在 Larch 上。

    tools/daykit.py          共用的板子建構器（卡片、連線、條件、事件池）
    tools/build_dayN.py      各天的劇本。改劇本改這裡，不要只改線上版
    tools/pull.py            把 Larch 上的專案整包抓下來存進 backup/
    tools/gen_docs.py        從 backup/project.json 生 docs/mechanics.md
    tools/sim_board.py       走遍一塊板子的所有玩法，抓斷線與環
    tools/check_pronouns.py  代名詞規則檢查（妳／你／全名）
    tools/dump_board.py      把一塊板子印成可讀劇本，拿去給人審
    backup/project.json      Larch 專案的完整副本

`build_day1.py` 與 `build_day2.py` 在一次暫存目錄被清空時弄丟了。那兩天只存在於
`backup/project.json` 裡，所以那份**一定要進版控**，不可以再 gitignore 掉。
要改那兩天只能就地補（做法看 `tools/patch_day2_jump.py`）。

## 改完要跑的

    python3 tools/build_dayN.py      # 重建那一天
    python3 tools/pull.py            # 抓回來存檔
    python3 tools/sim_board.py board-dayN
    python3 tools/check_pronouns.py
    python3 tools/gen_docs.py        # 更新機制表

## 代名詞規則

- 「妳」只指格莉奇，「你」只指玩家，旁白用「她」指格莉奇
- 格莉奇對黑洞先生說話：句首叫名字，後面省略主語
- 他不在畫面上的時候一律寫全名，代稱會被讀成在指玩家
- `check_pronouns.py` 會擋，不要靠記性

## 機制

看 [docs/mechanics.md](docs/mechanics.md)。那份是程式生的，不要手改。

## 授權

MIT，林亞澤。
