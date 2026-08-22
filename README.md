# 格莉奇與黑洞先生

一本繁體中文小說。

兩年前開台第一天來了七個人。她說，我要記住每一個來的人，我保證。

**她記得六個。**

線上閱讀：[yazelin.github.io/glitch-vn](https://yazelin.github.io/glitch-vn/)

## 這個 repo 裡有什麼

    novel/chNN.md            小說本文，七章。**支線不寫進來**
    design/novel.md          故事聖經：主軸、七個人、角色卡、寫法規則
    design/vn-routes.json    遊玩版的七個支線點，larch/dump_routes.py 抓的
    art/                     原始美術：14 張場景、7 張立繪、23 張表情差分、11 首 BGM
    docs/                    GitHub Pages 站台，程式生的，不要手改
    tools/gen_novel.py       產生站台（首頁／本文／角色／遊玩版／sitemap／robots）
    tools/gen_og.py          生 OG 分享圖與 favicon（合成，不是生成模型畫的）
    tools/gen_art.py         批次產圖，走 .11 的 codex-image
    tools/gen_bgm.py         批次產 BGM，走 .11 的 suno-web，一律純音樂
    tools/cut_faces.py       表情差分去背（綠幕→清內部殘留→負控制驗收）
    larch/                   視覺小說版：一章一支 build 腳本，見 larch/README.md
    archive/                 舊版：做在 Larch 上的七天記憶遊戲。已經收掉

## 改完要跑的

    python3 tools/gen_novel.py    # 重生站台（四頁＋sitemap／robots）
    python3 tools/gen_og.py       # 只有改標題或換主角立繪的時候才要重跑
    python3 larch/dump_routes.py  # 改了支線之後，把遊玩版那一頁的資料抓下來
    python3 larch/build_all.py    # 重建 Larch 上的七章

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

MIT，林亞澤。角色（格莉奇、黑洞先生）的設定正典在
[ai-brain-site](https://github.com/yazelin/ai-brain-site) 的 `persona.json`。
