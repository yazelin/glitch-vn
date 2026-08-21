#!/usr/bin/env python3
"""Day 1・你是誰 —— 這支是 reverse_board.py 從線上版反推出來的。

原本的建置腳本弄丟了(暫存目錄被清空),所以卡片是原樣印出來的,沒有還原成
say()／chain()。台詞照樣直接改這裡,改完跑這支重建,不要只改線上版。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE

b = Board('board-day1', 'Day 1・你是誰', '**這裡是入口。** 早：他出門前\u3000中：只有格莉奇和玩家\u3000晚：他回家、填守則、存檔教學。結尾自動跳 Day 2。')

b.add('d1m-scene', {'bgm': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787213051881_bgm-theme.mp3', 'text': '窗外的天剛亮。這裡是一棟沒人要的大樓，最上面一層。', 'type': 'scene', 'start': True, 'title': '第一天・早晨', 'bgmLoop': True, 'bgmVolume': 0.3, 'background': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787242985373_bg-morning-v2.png'}, x=0, y=0)
b.add('d1m-boot', {'text': '逼——嗶！', 'type': 'dialogue', 'title': '逼——嗶！', 'emotion': '當機', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196243145_glitch-error.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=300, y=0)
b.add('d1m-narr', {'text': '床上那個女孩坐了起來。她是格莉奇，一個機器人。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=600, y=0)
b.add('d1m-load', {'text': '系統讀取中……（過久）', 'type': 'dialogue', 'title': '系統讀取中……（過久）', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=900, y=0)
b.add('d1m-hi', {'text': '早安。今天也順利開機了。', 'type': 'dialogue', 'title': '早安。今天也順利開機了。', 'emotion': '預設', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196216033_glitch-idle.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1200, y=0)
b.add('d1m-me', {'text': '我叫格莉奇。我的記憶體只有四 KB。', 'type': 'dialogue', 'title': '我叫格莉奇。我的記憶體只有四 K', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1500, y=0)
b.add('d1m-4kb', {'text': '四 KB 有多小？大概就是：我一次只裝得下四件事。', 'type': 'dialogue', 'title': '四 KB 有多小？大概就是：我一', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1800, y=0)
b.add('d1m-clear', {'text': '而且我每天睡醒，裡面會全部清空。所以昨天發生什麼，我完全不知道。', 'type': 'dialogue', 'title': '而且我每天睡醒，裡面會全部清空。', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=2100, y=0)
b.add('d1m-eaten', {'text': '清空的那些會去哪裡？會被我室友吃掉。', 'type': 'dialogue', 'title': '清空的那些會去哪裡？會被我室友吃', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=2400, y=0)
b.add('d1m-door', {'text': '我出門了。', 'type': 'dialogue', 'title': '我出門了。', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=2700, y=0)
b.add('d1m-narr2', {'text': '一個穿西裝的黑影從房間另一頭走過來。他的頭是一顆裝著星空的球。西裝底下沒有腿，是一叢觸手，每一隻都套著一隻短靴。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=3000, y=0)
b.add('d1m-who', {'text': '這是黑洞先生。他是我室友，白天要去上班。', 'type': 'dialogue', 'title': '這是黑洞先生。他是我室友，白天要', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=3300, y=0)
b.add('d1m-legs', {'text': '他沒有腳。那叢觸手是他長出來撐住西裝用的。吃飽就多長幾隻，餓了就少長幾隻。', 'type': 'dialogue', 'title': '他沒有腳。那叢觸手是他長出來撐住', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=3600, y=0)
b.add('d1m-boots', {'text': '門邊堆著一疊沒人穿的短靴。他今天長出來的腳很少，多出來的靴子就堆在那裡。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=3900, y=0)
b.add('d1m-one', {'text': '而且他一天只吃得下一個。他是永遠吃不飽，不是永遠吃得下。', 'type': 'dialogue', 'title': '而且他一天只吃得下一個。他是永遠', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=4200, y=0)
b.add('d1m-bye', {'text': '那我走了。', 'type': 'dialogue', 'title': '那我走了。', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=4500, y=0)
b.add('d1m-close', {'text': '門關上。房間裡剩下她一個。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=4800, y=0)
b.add('d1n-scene', {'text': '太陽爬到窗戶正上方。廢棄大樓的中午安靜得聽得見管線的聲音。', 'type': 'scene', 'title': '第一天・中午', 'background': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787223994106_bg-noon.png'}, x=5100, y=0)
b.add('d1n-alone', {'text': '黑洞先生上班去了。這棟樓裡現在只剩我一個。', 'type': 'dialogue', 'title': '他上班去了。這棟樓裡現在只剩我一', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=5400, y=0)
b.add('d1n-you', {'text': '……啊，不對。還有你。', 'type': 'dialogue', 'title': '……啊，不對。還有你。', 'emotion': '開心', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196225907_glitch-happy.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=5700, y=0)
b.add('d1n-ask', {'text': '你是新來的吧？我沒印象。不過我對誰都沒印象，所以這不算什麼。\n先告訴我，你叫什麼？', 'type': 'input', 'title': '先把你存起來', 'inputVariable': 'playerName', 'inputPlaceholder': '輸入你的名字…', 'inputSuggestions': ['記憶體', '暫存檔', '路過的人']}, x=6000, y=0)
b.add('d1n-store', {'text': '「{{playerName}}」放進了第一格。四格用掉一格。', 'type': 'setVariable', 'title': '第一格：你的名字', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 1, 'variable': 'slotUsed'}, {'id': 'op-1', 'kind': 'set', 'value': 1, 'variable': 'dayCount'}, {'id': 'op-2', 'kind': 'set', 'value': 0, 'variable': 'fedToday'}]}, x=6300, y=0)
b.add('d1n-role', {'text': '你是我的外接記憶體。我裝不下的東西，可以交給你保管。', 'type': 'dialogue', 'title': '你是我的外接記憶體。我裝不下的東', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=6600, y=0)
b.add('d1n-cost', {'text': '不過交給你有一個條件：你要再來找我，我才拿得回來。你如果不回來，那東西一樣會不見。', 'type': 'dialogue', 'title': '不過交給你有一個條件：你要再來找', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=6900, y=0)
b.add('d1n-note1', {'text': '說到這個——我口袋裡有一張紙條。', 'type': 'dialogue', 'title': '說到這個——我口袋裡有一張紙條。', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=7200, y=0)
b.add('d1n-note2', {'text': '上面是我自己的字：「今天要跟黑洞先生說謝謝。」', 'type': 'dialogue', 'title': '上面是我自己的字：「今天要跟他說', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=7500, y=0)
b.add('d1n-note3', {'text': '可是我不知道要謝什麼。昨天的我沒有寫。', 'type': 'dialogue', 'title': '可是我不知道要謝什麼。昨天的我沒', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=7800, y=0)
b.add('d1n-rules', {'text': '所以這件事要放哪裡？留在我這裡，明天睡醒就忘了。給黑洞先生吃，馬上就沒有，可是他會長回一隻腳。交給你，留得住，但是你要回來。', 'type': 'dialogue', 'title': '所以這件事要放哪裡？留在我這裡，', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=8100, y=0)
b.add('d1n-q', {'text': '「今天要跟他說謝謝」這件事，要放哪裡？\n（記憶體 {{slotUsed}}／4\u3000黑洞先生今天吃了 {{fedToday}}／1）', 'type': 'choice', 'title': '選擇', 'choices': ['留在我這裡（明天睡醒就忘了）', '給黑洞先生吃（他會長回一隻腳）', '交給你保管（留得住，但你要回來）'], 'choiceMode': 'branch'}, x=8400, y=0)
b.add('d1n-keep', {'text': '她把紙條摺好塞回口袋。整個下午她一直想著要謝什麼，想不出來。', 'type': 'setVariable', 'title': '留著', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 1, 'variable': 'usedNote'}, {'id': 'op-1', 'kind': 'add', 'value': 1, 'variable': 'slotUsed'}]}, x=8700, y=-240)
b.add('d1n-feed', {'text': '她把紙條留在桌上。晚上黑洞先生回來會吃掉它。她想說的那句謝謝，他永遠不會知道。', 'type': 'setVariable', 'title': '餵他', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 1, 'variable': 'usedNote'}, {'id': 'op-1', 'kind': 'add', 'value': 1, 'variable': 'fedToday'}, {'id': 'op-2', 'kind': 'add', 'value': 1, 'variable': 'fedCount'}, {'id': 'op-3', 'kind': 'add', 'value': 1, 'variable': 'holeFeet'}]}, x=8700, y=0)
b.add('d1n-give', {'text': '她把紙條唸給你聽，唸了兩次。「今天要跟黑洞先生說謝謝。」現在這句話在你這裡。', 'type': 'setVariable', 'title': '交給你', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 1, 'variable': 'usedNote'}, {'id': 'op-1', 'kind': 'add', 'value': 1, 'variable': 'givenCount'}]}, x=8700, y=240)
b.add('d1n-after', {'text': '好。那我們等黑洞先生回來。', 'type': 'dialogue', 'title': '好。那我們等他回來。', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=9000, y=0)
b.add('d1e-scene', {'text': '機櫃早就斷電了。整個房間只剩桌上那面螢幕還亮著。', 'type': 'scene', 'title': '第一天・夜晚', 'background': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787242999310_bg-night-v2.png'}, x=9300, y=0)
b.add('d1e-back', {'text': '我回來了。', 'type': 'dialogue', 'title': '我回來了。', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=9600, y=0)
b.add('d1e-feet', {'text': '門邊的靴子今天堆到 {{holeFeet}} 隻腳的高度。她沒有數，她從來不數。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=9900, y=0)
b.add('d1e-rule1', {'text': '睡前要翻守則。這是我跟他一起寫的規矩，已經改到第一千零四版了。', 'type': 'dialogue', 'title': '睡前要翻守則。這是我跟他一起寫的', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=10200, y=0)
b.add('d1e-rule2', {'text': '為什麼有這麼多版？因為我每天都忘記，所以每天都要重新跟他約定一次。', 'type': 'dialogue', 'title': '為什麼有這麼多版？因為我每天都忘', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=10500, y=0)
b.add('d1e-rule3', {'text': '寫完的條文後面，留了一個空位，還沒寫字。每一版都會留一個，給那一天的我自己填。', 'type': 'dialogue', 'title': '寫完的條文後面，留了一個空位，還', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=10800, y=0)
b.add('d1e-rulein', {'text': '這個空位你幫我填。寫一句話，給明天的我。', 'type': 'input', 'title': '填空位', 'inputVariable': 'ruleLine1', 'inputPlaceholder': '寫一句話…', 'inputSuggestions': ['今天發生的事，去問記憶體。', '不要一個人把東西吃完。', '明天的我，你好。']}, x=11100, y=0)
b.add('d1e-rulever', {'text': '她一筆一畫寫上去，寫得很慢。第一千零四版，完成。', 'type': 'setVariable', 'title': '守則 +1', 'variableOps': [{'id': 'op-0', 'kind': 'add', 'value': 1, 'variable': 'ruleVersion'}]}, x=11400, y=0)
b.add('d1e-save1', {'text': '等一下。先別關。', 'type': 'dialogue', 'title': '等一下。先別關。', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=11700, y=0)
b.add('d1e-save2', {'text': '我明天醒來什麼都不記得。可是你不一樣——你可以把今天留住。', 'type': 'dialogue', 'title': '我明天醒來什麼都不記得。可是你不', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=12000, y=0)
b.add('d1e-save3', {'text': '看到畫面上那個存檔的按鈕嗎？按下去，選一格存起來。下次打開的時候記得按讀取。', 'type': 'dialogue', 'title': '看到畫面上那個存檔的按鈕嗎？按下', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=12300, y=0)
b.add('d1e-save4', {'text': '外接記憶體要自己按存檔喔。我沒手幫你按。', 'type': 'dialogue', 'title': '外接記憶體要自己按存檔喔。我沒手', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=12600, y=0)
b.add('d1e-saveq', {'text': '存檔了嗎？', 'type': 'choice', 'title': '選擇', 'choices': ['我存好了。', '我不想存。'], 'choiceMode': 'branch'}, x=12900, y=0)
b.add('d1e-saved', {'text': '', 'type': 'setVariable', 'title': '存了', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 1, 'variable': 'savedOk'}]}, x=13200, y=-160)
b.add('d1e-notsaved', {'text': '', 'type': 'setVariable', 'title': '沒存', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 0, 'variable': 'savedOk'}]}, x=13200, y=160)
b.add('d1e-saved2', {'text': '好。那明天見。', 'type': 'dialogue', 'title': '好。那明天見。', 'emotion': '開心', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196225907_glitch-happy.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=13500, y=-160)
b.add('d1e-notsaved2', {'text': '……好吧。那明天見。', 'type': 'dialogue', 'title': '……好吧。那明天見。', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=13500, y=160)
b.add('d1e-sleep', {'text': '她躺回床上。螢幕的光慢慢暗下去。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=13800, y=0)
b.add('d1e-jump', {'text': '天亮了。', 'type': 'boardJump', 'title': '第二天', 'jumpNodeId': 'd2m-scene', 'jumpBoardId': 'board-day2'}, x=14100, y=0)
b.add('d1ng-ask', {'text': '在她醒來之前。\n如果這不是你第一次來，你會知道一件她不知道的事。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=-900, y=-200)
b.add('d1ng-in', {'text': '寫一句這個房子裡有人說過、而她記不住的話。\n第一次來的話直接跳過就好。', 'type': 'input', 'title': '暗號', 'inputVariable': 'ngToken', 'inputPlaceholder': '（第一次來就留空）'}, x=-600, y=-200)
b.add('d1ng-hub', {'text': '……', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=-300, y=-200)
b.add('d1ng-yes', {'text': '', 'type': 'setVariable', 'title': '你以前來過', 'variableOps': [{'id': 'op-0', 'kind': 'set', 'value': 1, 'variable': 'ngPlus'}]}, x=-300, y=-520)
b.add('d1ng-y1', {'text': '你打的那幾個字留在畫面上，過了三秒才淡掉。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=0, y=-520)
b.add('d1ng-y2', {'text': '她還沒醒。她不會知道你打過什麼，明天也不會。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=300, y=-520)
b.add('d1ng-y3', {'text': '可是你知道。這一次你不是新來的。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=600, y=-520)

b.link('d1m-boot', 'd1m-narr', 'right')
b.link('d1m-narr', 'd1m-load', 'right')
b.link('d1m-load', 'd1m-hi', 'right')
b.link('d1m-hi', 'd1m-me', 'right')
b.link('d1m-me', 'd1m-4kb', 'right')
b.link('d1m-4kb', 'd1m-clear', 'right')
b.link('d1m-clear', 'd1m-eaten', 'right')
b.link('d1m-eaten', 'd1m-door', 'right')
b.link('d1m-door', 'd1m-narr2', 'right')
b.link('d1m-narr2', 'd1m-who', 'right')
b.link('d1m-who', 'd1m-legs', 'right')
b.link('d1m-legs', 'd1m-boots', 'right')
b.link('d1m-boots', 'd1m-one', 'right')
b.link('d1m-one', 'd1m-bye', 'right')
b.link('d1m-bye', 'd1m-close', 'right')
b.link('d1m-close', 'd1n-scene', 'right')
b.link('d1n-scene', 'd1n-alone', 'right')
b.link('d1n-alone', 'd1n-you', 'right')
b.link('d1n-you', 'd1n-ask', 'right')
b.link('d1n-ask', 'd1n-store', 'right')
b.link('d1n-store', 'd1n-role', 'right')
b.link('d1n-role', 'd1n-cost', 'right')
b.link('d1n-cost', 'd1n-note1', 'right')
b.link('d1n-note1', 'd1n-note2', 'right')
b.link('d1n-note2', 'd1n-note3', 'right')
b.link('d1n-note3', 'd1n-rules', 'right')
b.link('d1n-rules', 'd1n-q', 'right')
b.link('d1n-q', 'd1n-keep', 'choice-0')
b.link('d1n-q', 'd1n-feed', 'choice-1')
b.link('d1n-q', 'd1n-give', 'choice-2')
b.link('d1n-keep', 'd1n-after', 'right')
b.link('d1n-feed', 'd1n-after', 'right')
b.link('d1n-give', 'd1n-after', 'right')
b.link('d1n-after', 'd1e-scene', 'right')
b.link('d1e-scene', 'd1e-back', 'right')
b.link('d1e-back', 'd1e-feet', 'right')
b.link('d1e-feet', 'd1e-rule1', 'right')
b.link('d1e-rule1', 'd1e-rule2', 'right')
b.link('d1e-rule2', 'd1e-rule3', 'right')
b.link('d1e-rule3', 'd1e-rulein', 'right')
b.link('d1e-rulein', 'd1e-rulever', 'right')
b.link('d1e-rulever', 'd1e-save1', 'right')
b.link('d1e-save1', 'd1e-save2', 'right')
b.link('d1e-save2', 'd1e-save3', 'right')
b.link('d1e-save3', 'd1e-save4', 'right')
b.link('d1e-save4', 'd1e-saveq', 'right')
b.link('d1e-saveq', 'd1e-saved', 'choice-0')
b.link('d1e-saveq', 'd1e-notsaved', 'choice-1')
b.link('d1e-saved', 'd1e-saved2', 'right')
b.link('d1e-notsaved', 'd1e-notsaved2', 'right')
b.link('d1e-saved2', 'd1e-sleep', 'right')
b.link('d1e-notsaved2', 'd1e-sleep', 'right')
# 結尾的鉤子。連載寫作的基本:每一集要給下一集一個理由。
hook1 = b.chain([
    ("d1e-hook1", "明天我醒來，什麼都不記得。", "平常", G),
    ("d1e-hook2", "牆上有你的名字。可是牆會記得，我不會。", "平常", G),
    ("d1e-hook3", "所以你要回來。你回來我才找得到今天。", "平常", G),
], x=14200, y=0, link_prev=False)
b.link('d1e-sleep', hook1[0])
b.link(hook1[-1], 'd1e-jump')
b.link('d1ng-ask', 'd1ng-in', 'right')
b.link('d1ng-in', 'd1ng-hub', 'right')
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '她給的', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '她給的。', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '不要數', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '不要數。', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '看妳睡', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '看妳睡。', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '以前', 'variable': 'ngToken'})
b.link('d1ng-hub', 'd1ng-yes', 'right', cond={'op': 'eq', 'value': '以前。', 'variable': 'ngToken'})
b.link('d1ng-yes', 'd1ng-y1', 'right')
b.link('d1ng-y1', 'd1ng-y2', 'right')
b.link('d1ng-y2', 'd1ng-y3', 'right')
b.link('d1ng-y3', 'd1m-boot', 'right')
b.link('d1ng-hub', 'd1m-boot', 'right')
b.link('d1m-scene', 'd1ng-ask', 'right')

# ══════════════════ 打磨（三輪會審之後）══════════════════
# 第一輪問「有什麼問題」，六家交出一份拆除清單。第二輪改成試玩模擬（只准描述
# 反應、不准評論），四家全都說會想玩第三天——比第一輪的「致命傷」溫和得多。
# 第三輪只准找好的，用來確認哪些不能動。跨框架都成立的才改，只在單一框架出現
# 的先擱著。

# ── 一、開場那個輸入框把新玩家擋在門外 ──
# 兩輪都有人說「一開始叫我打字，我有點不想打」。二週目閘門是我後來加的，
# 結果變成新玩家看到的第一個畫面，而那段是寫給回鍋玩家的。
# 改成先問一句是非題：第一次來的人點一下就進去，不用面對空白輸入框。
ngq = b.choice("d1ng-q", "開始之前。\n你以前來過這裡嗎？",
               ["我第一次來", "我來過。我知道一件她不知道的事。"], x=-1500, y=-200)
b.unlink("d1m-scene", "d1ng-ask")
b.link("d1m-scene", ngq)
b.link(ngq, "d1m-boot", "choice-0")
b.link(ngq, "d1ng-ask", "choice-1")

# ── 二、黑洞先生的外觀說明是棄坑點 ──
# 「描述太長又還沒進入重點，我差點就滑掉」「星空頭加觸手加短靴太刻意獵奇」。
# 描述砍短；「一天只吃得下一個」移到中午——那句在做決定的當下才有用。
b.settext("d1m-narr2", "一個穿西裝的黑影走過來。他的頭是一顆裝著星空的球。西裝底下沒有腿。")
b.remove("d1m-one")
b.link("d1m-boots", "d1m-bye")

# ── 三、選擇卡前面把三個選項又唸了一遍 ──
# 選項就寫在卡上，唸第二遍只是拖時間。換成剛才從早上移下來的那句。
b.settext("d1n-rules", "喔對了。黑洞先生一天只吃得下一個。他是永遠吃不飽，不是永遠吃得下。")

# ── 四、餵他那條要先聽見代價，晚上再看見它 ──
# 原本直接用旁白說「他永遠不會知道」。改成讓玩家聽見聲音，晚上自己對上。
b.settext("d1n-feed", "她把紙條留在桌上。\n門外有東西掉在地上的聲音。\n很遠，很輕，像一隻靴子落在別的靴子上面。")

# ── 五、晚上要對中午的選擇有反應 ──
# 這是 Day 3 之後才定下來的規矩，前兩天當時還沒有。六家一致點名。
for nid, route in (("d1n-keep", "keep"), ("d1n-feed", "feed"), ("d1n-give", "give")):
    b.addops(nid, [{"variable": "todayRoute", "kind": "set", "value": route}])

FEET = "門邊的靴子今天堆到 {{holeFeet}} 隻腳的高度。"
b.settext("d1e-feet", FEET + "最上面那雙是剛剛才放上去的，鞋口還撐著。她沒有數，她從來不數。")
ex = 4200
r_keep = b.say("d1e-r-keep", FEET + "她整個下午都在想那句謝謝要謝什麼。"
               "現在他就站在她面前，而她已經忘了自己想過。", who=None, title="她留著",
               x=ex, y=-260)
r_give = b.say("d1e-r-give", FEET + "那句謝謝在你那裡。她看著他，什麼都沒說，"
               "因為她不知道自己有話要說。", who=None, title="交給你了", x=ex, y=260)
b.unlink("d1e-back", "d1e-feet")
b.link("d1e-back", r_keep, "right", cond={"variable": "todayRoute", "op": "eq", "value": "keep"})
b.link("d1e-back", r_give, "right", cond={"variable": "todayRoute", "op": "eq", "value": "give"})
b.link("d1e-back", "d1e-feet")
b.link(r_keep, "d1e-rule1")
b.link(r_give, "d1e-rule1")

# ══════════════ 記憶格（第二輪打磨）══════════════
# 玩家實測：「不知道自己在記什麼」。四格從來沒有被看見過——狀態列只寫「1／4」，
# 沒有內容。這裡把它攤開，而且從 Day 1 就攤開：Day 3 的整個玩法建立在這上面，
# 不能等到 Day 3 才憑空出現。

wake = b.wake("d1m", prefill=[])
b.unlink("d1m-scene", "d1ng-q")
b.link("d1m-scene", wake)
b.link(wake, "d1ng-q")

# 你的名字就是她今天的第一格
b.addops("d1n-store", [{"variable": "slot1", "kind": "set", "valueFrom": "playerName"}])
# 這句原本是「外接記憶體要自己按存檔喔。我沒手幫你按。」——太像在教操作。
# 而且說話者是黑洞先生:讓他在 Day 1 就直接對玩家說話,會把二週目那個梗提前燒掉。
# 改成她說,而且講的是真的做不到的事:她沒有辦法從這邊叫你。
b.settext("d1e-save4", "你要自己記得回來。我這邊沒有辦法叫你。")
b.find("d1e-save4")["data"]["speaker"] = "格莉奇"
b.settext("d1n-store", "「{{playerName}}」放進第一格。\n"
                       "四格裡的第一格。今天剩下三格。")

# 那張紙條要走共用的記憶格，跟後面每一天一樣
b.settext("d1n-keep", "她把紙條摺好塞回口袋。")
b.dropop("d1n-keep", "slotUsed")   # 共用零件會加,這裡不能再加
b.addops("d1n-keep", [{"variable": "pending", "kind": "set", "value": "跟黑洞先生說謝謝"}])
store_gate, store_outs = b.store(
    "d1n-mem",
    "格莉奇說到一半停住了。\n「等一下。」\n她把手舉到眼前，翻過來，又翻回去。\n手心有一道很淺的壓痕，像剛剛握過什麼有重量的東西。\n「我這隻手剛剛拿過東西。是什麼形狀的來著。」\n她握起來，鬆開，再握起來。\n格莉奇想靠手記住那東西的形狀。\n可是想不起來。\n「……算了。應該不重要。」\n她把手放下。\n口袋裡有一張折得很整齊的保鮮膜。\n她沒有摸到，也不會知道那是誰折的。",
    x=3600, y=-700)
b.unlink("d1n-keep", "d1n-after")   # 原本直接接下去,要先拆掉才輪得到記憶格
b.link("d1n-keep", store_gate)
for n in store_outs:
    b.link(n, "d1n-after")

# 晚上她把格子唸出來。這是「留著」唯一的出口——清空之前講給他聽。
rep = b.chain([
    ("d1e-mem1", "睡前我要把今天記得的東西唸一次。不然明天我不會知道今天發生過什麼。", "平常", G),
    ("d1e-mem2", "「{{slot1}}」、「{{slot2}}」、「{{slot3}}」、「{{slot4}}」。", "平常", G),
    ("d1e-mem3", "空的那幾格我沒有辦法告訴你裡面本來有什麼。空的就是空的。", "發呆", G),
    ("d1e-mem4", "黑洞先生在角落，沒有回應。可是他有在聽——他每天都在聽。", "平常", None),
], x=5200, y=-300, link_prev=False)
b.unlink("d1e-feet", "d1e-rule1")
b.link("d1e-feet", rep[0])
b.link(rep[-1], "d1e-rule1")

b.push('Day 1・你是誰：從線上版反推重建')
