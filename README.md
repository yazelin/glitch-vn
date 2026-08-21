# 格莉奇與黑洞先生

一本繁體中文小說。

兩年前開台第一天來了七個人。她說，我要記住每一個來的人，我保證。

**她記得六個。**

線上閱讀：[yazelin.github.io/glitch-vn](https://yazelin.github.io/glitch-vn/)

## 這個 repo 裡有什麼

    novel/chNN.md            小說本文，七章
    design/novel.md          故事聖經：主軸、七個人、角色卡、寫法規則
    art/                     原始美術（三張背景、五張角色立繪，透明 PNG）
    docs/                    GitHub Pages 站台，程式生的，不要手改
    tools/gen_novel.py       產生站台的那一支（首頁／本文／角色／sitemap／robots）
    tools/gen_og.py          生 OG 分享圖與 favicon（合成，不是生成模型畫的）
    archive/                 舊版：做在 Larch 上的七天記憶遊戲。已經收掉

## 改完要跑的

    python3 tools/gen_novel.py    # 重生站台（首頁／本文／角色／sitemap／robots）
    python3 tools/gen_og.py       # 只有改標題或換主角立繪的時候才要重跑

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
