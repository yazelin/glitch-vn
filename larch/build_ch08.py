"""第八章・謝幕。故事在第七章結束，這一章是片尾。

三張卡：放映廳（燈還暗著）→ 片尾字卷 → 謝幕（燈亮，全體上台）。

**字卷是一張 miniGame 卡片**，內容在 Pages 上（docs/credits.html），
Larch 這邊只放一層薄殼。改片尾的字或圖只要動那一頁，不用重建這一章。
見 novelkit.Chapter.credits。
"""
import novelkit as nk

CREDITS_URL = "https://yazelin.github.io/glitch-vn/credits.html"

cids = nk.ensure_characters()
c = nk.Chapter("ch08", "謝幕", "片尾字卷與全體謝幕", cids)

# 燈還暗著。故事的最後一句話留在這裡，接在第七章的黑洞先生之後。
# **「完」那一句要讓旁白唸。** 寫在場景卡的 text 上就沒有聲音了——
# 場景卡不配音，只有對話卡有。
c.scene("放映廳", "燈暗下來。", "bg-credits-cinema",
        start=True, transition="fade", ms=900)
c.narrate("《格莉奇與黑洞先生》完")

c.credits(CREDITS_URL, "片尾謝幕", "")

# 燈亮，七個人上台。
c.scene("謝幕", "燈亮了。", "bg-curtain-call", transition="fade", ms=700)
# 最後一句直接當章末，不要再多一張——連著兩張收尾會鬆掉。
# **這一句是格莉奇說的，不是旁白。** 她是那個想被記住的人，
# 謝幕圖裡正在揮手的也是她。
c.end("謝謝你看到這裡。\n"
      "我第一天就說過，我要記住每一個來的人。\n"
      "我保證過。", who="格莉奇", emotion="開心")
c.push("第八章")
