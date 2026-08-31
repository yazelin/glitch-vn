# YouTube 上架文案

《格莉奇與黑洞先生》全書完整遊玩影片的標題與說明欄。重新發佈或重錄影片
之後這份還會再用到，所以收在這裡。

**數字都是查過的，不要憑印象改**：六百二十四張卡（八個板子相加）、
一萬兩千字（漢字數，不含標點）、七百句配音、十一首配樂、五十六條讀音替身。

**聲音的數法很容易錯**：有台詞的講者十一個，但旁白不是角色、「畫面裡的她」
就是格莉奇本人出現在螢幕上、「大學生」只有兩句而且跟黑洞先生共用同一支
參考音、「留言區」根本不配音。所以正確的講法是**七個角色加旁白、八種聲音**。
我第一版寫「十個角色」就是把這些全部當成角色去數。

**章節時間戳是從影片本身量出來的**，不是估的：把六十分鐘的音訊整段轉錄，
再用模糊比對找每一章第一句話的位置。轉錄會混簡體字與阿拉伯數字，
直接字串比對抓不到。換影片就要重新量。

**對外文字**：全形標點、不用 emoji、交稿前跑 `~/speak-tw/bin/speak-tw --public`。

---

標題
《格莉奇與黑洞先生》全七章完整遊玩｜用 AI 做的視覺小說，七百句配音

說明欄（以下全部）
──────────────────────────────
《格莉奇與黑洞先生》全七章完整遊玩，六十分鐘。

一個老是自嘲只有 4KB 的虛擬主播，開台第一天來了七個人。她說她要記住每一個來的人。
兩年後，她只記得六個。第七行呢？

這是一部視覺小說，也是一部有聲書。全書七章加片尾謝幕，六百二十四張卡，
一萬兩千字，七百句配音。這支影片從第一句放到最後一句，內容沒有剪，只拿掉了開頭的載入畫面。

▍自己玩一次
https://larch.ink/play/market/a2a10427-7326-4a86-b806-c2476fc1c22a

▍只想讀文字（附逐句朗讀的有聲書）
https://yazelin.github.io/glitch-vn/novel.html

▍章節
00:00　第一章・第一千零四版
07:36　第二章・限時預購
14:17　第三章・99.98
21:42　第四章・第四十版
28:52　第五章・第一次問
36:55　第六章・考完就刪
44:02　第七章・去問他今天累不累
57:50　片尾謝幕
59:10　全體謝幕

▍平台：Larch
這部作品跑在 Larch 上，一個做視覺小說的平台。
https://larch.ink

用它的理由很實際：卡片、分歧、變數、立繪站位、表情差分、背景樂、
片尾的小遊戲卡，這些都是現成的，不用自己寫播放器。它也有 agent API，
所以整部作品是用程式建出來的，每一張卡都在版本控制裡，
改一個字重跑一次就更新。

市集上有其他人的作品可以玩，官方也放了可以直接 Remix 的範本。
想做視覺小說的人可以去看看。

▍怎麼做的
文字是人與 AI 共同創作，定稿由人決定。
立繪、場景、配樂是 AI 生成之後人工修版與挑選。
配音是自架的 CosyVoice3 加上平台提供的 MiniMax，七個角色加旁白、
八種聲音、七百句，每一句都聽過才定案。配樂十一首，全部由 Suno 生成。

過程中比較花時間的是「模型唸錯字」：飲水機唸成蒙水機、鑰匙唸成測試、
傘唸成三。解法是同音字替身表，合成之前把文字換掉，畫面上的字一個都不動。
全書五十六條替身，每一條都記錄了原字、替身、以及它原本錯成什麼。

原始碼、素材、工具全部公開：
https://github.com/yazelin/glitch-vn

▍這支影片是怎麼錄的
自動玩一次錄下來的，沒有人在旁邊按滑鼠。做法照 promo-video 這份管線，
不過它內建的錄影不收聲音，所以另外寫了一支：畫面走 x11grab，
聲音走一個獨立的音訊接收端，翻頁靠攔截播放器的語音元素，
每一句配音播完才點下一張。腳本在 glitch-vn 的 tools/capture。

▍用到的工具（都是公開的）
promo-video　把專案變成宣傳片的零成本管線
https://yazelin.github.io/promo-video-skill/

codex-imagegen　用訂閱額度生圖
https://yazelin.github.io/codex-imagegen-skill/

tts　大量合成語音會撞到的東西
https://github.com/yazelin/tts-skill

cutout　平底色去背
https://github.com/yazelin/cutout-skill

larch-vn　在 Larch 上做視覺小說
https://github.com/yazelin/larch-vn-skill

speak-tw　中文行文檢查
https://github.com/yazelin/speak-tw

▍角色
格莉奇　虛擬主播，愛拿「我只有 4KB」當口頭禪
黑洞先生　她的室友，永遠吃不飽
貓草　宅，在留言區打字的老觀眾
鐵塔　她的經紀人，從來不說再見
0x　記錄精準的另一個主播
斑比　做周邊的設計師，從來不打折
諾亞　頂樓加蓋那間五金雜貨店的老闆，話不多的可愛老人

▍想認識格莉奇
她在別的地方也還在。

格莉奇OS　她的桌面，會跟你聊天
https://yazelin.github.io/ai-brain-site/

格莉奇音樂　她唱的歌
https://yazelin.github.io/glitch-music/

4KB 記憶體的日常搞笑漫畫
https://yazelin.github.io/ai-comic-starter/

角色檔案　格莉奇
https://yazelin.github.io/characters/glitch/

角色檔案　黑洞先生
https://yazelin.github.io/characters/blackhole/

本作的角色介紹
https://yazelin.github.io/glitch-vn/characters.html

▍認識作者
林亞澤，這些東西是我做的。平常在部落格寫怎麼做的。
https://yazelin.github.io/

GitHub https://github.com/yazelin
Facebook https://www.facebook.com/yaze.lin.gm
請亞澤喝咖啡 https://buymeacoffee.com/yazelin

作品採用 CC BY-NC，工具的部分是 MIT。

#視覺小說 #視覺小說製作 #Larch #AI創作 #獨立創作 #有聲書 #原創小說
