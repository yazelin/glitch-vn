#!/usr/bin/env python3
"""Day 2・靴子與裂痕 —— 這支是 reverse_board.py 從線上版反推出來的。

原本的建置腳本弄丟了(暫存目錄被清空),所以卡片是原樣印出來的,沒有還原成
say()／chain()。台詞照樣直接改這裡,改完跑這支重建,不要只改線上版。
"""
import sys; sys.path.insert(0, "/home/ct/glitch-vn/tools")
from daykit import Board, G, HOLE

b = Board('board-day2', 'Day 2・靴子與裂痕', '早：沒存檔的話她不認識你\u3000中：隨機抽今天的事件\u3000晚：引用你昨天寫的守則')

b.add('d2m-scene', {'bgm': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787213051881_bgm-theme.mp3', 'text': '又一個早上。窗外的城市看起來跟昨天一模一樣，可是她不知道昨天長什麼樣。', 'type': 'scene', 'start': True, 'title': '第二天・早晨', 'bgmLoop': True, 'bgmVolume': 0.3, 'background': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787242985373_bg-morning-v2.png'}, x=0, y=0)
b.add('d2m-boot', {'text': '逼——嗶！', 'type': 'dialogue', 'title': '逼——嗶！', 'emotion': '當機', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196243145_glitch-error.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=300, y=0)
b.add('d2m-load', {'text': '系統讀取中……（過久）', 'type': 'dialogue', 'title': '系統讀取中……（過久）', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=600, y=0)
b.add('d2m-hub', {'text': '……', 'type': 'dialogue', 'title': '她抬頭看你', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=900, y=0)
b.add('d2m-lost1', {'text': '你是誰？', 'type': 'dialogue', 'title': '你是誰？', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1200, y=220)
b.add('d2m-lost2', {'text': '昨天沒有人幫我存下來。所以你昨天說的話、你的名字，我這裡一格都沒有。', 'type': 'dialogue', 'title': '昨天沒有人幫我存下來。所以你昨天', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1500, y=220)
b.add('d2m-lost3', {'text': '外接記憶體要自己按存檔。我說過了。', 'type': 'dialogue', 'title': '外接記憶體要自己按存檔。我說過了', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=1800, y=220)
b.add('d2m-relearn', {'text': '那……可以再告訴我一次嗎？這次記得存。', 'type': 'input', 'title': '再說一次你的名字', 'inputVariable': 'playerName', 'inputPlaceholder': '再輸入一次…'}, x=2100, y=220)
b.add('d2m-ok1', {'text': '早安，{{playerName}}。', 'type': 'dialogue', 'title': '早安，{{playerName}', 'emotion': '開心', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196225907_glitch-happy.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1200, y=-220)
b.add('d2m-ok2', {'text': "我不記得你。可是牆上寫著你的名字。\n而且我今天醒得比較快。\n有人替我省下一格。", 'type': 'dialogue', 'title': '我不記得你。可是牆上寫著你的名字', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=1500, y=-220)
b.add('d2m-join', {'text': '今天是第幾天我不知道。我從來不知道。', 'type': 'dialogue', 'title': '今天是第幾天我不知道。我從來不知', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=2400, y=0)
b.add('d2m-rule', {'text': '可是守則知道。它已經改到第 {{ruleVersion}} 版了。', 'type': 'dialogue', 'title': '可是守則知道。它已經改到第 {{', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=2700, y=0)
b.add('d2m-quote', {'text': '昨天那一版的空位上寫著——「{{ruleLine1}}」。那是你寫的。', 'type': 'dialogue', 'title': '昨天那一版的空位上寫著——「{{', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=3000, y=0)
b.add('d2m-quote2', {'text': '我照做。反正我也想不出別的辦法。', 'type': 'dialogue', 'title': '我照做。反正我也想不出別的辦法。', 'emotion': '開心', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196225907_glitch-happy.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=3300, y=0)
b.add('d2m-door', {'text': '我出門了。', 'type': 'dialogue', 'title': '我出門了。', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=3600, y=0)
b.add('d2m-feet', {'text': '門邊那疊沒人穿的短靴，今天的高度對得上他身上 {{holeFeet}} 隻腳。她沒有數，她從來不數。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=3900, y=0)
b.add('d2n-scene', {'text': '太陽爬到窗戶正上方。黑洞先生上班去了。', 'type': 'scene', 'title': '第二天・中午', 'background': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787223994106_bg-noon.png'}, x=4200, y=0)
b.add('d2n-alone', {'text': '又剩我一個。……還有你。', 'type': 'dialogue', 'title': '又剩我一個。……還有你。', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=4500, y=0)
b.add('d2n-roll', {'text': '', 'type': 'setVariable', 'title': '抽今天的事件', 'variableOps': [{'id': 'op-0', 'max': 3, 'min': 1, 'kind': 'random', 'variable': 'todayEvent'}]}, x=4800, y=0)
b.add('d2n-gate-picture', {'text': '門口地上有一張素描，畫的是一堆靴子。筆觸是我自己的，可是我不記得畫過。', 'type': 'dialogue', 'title': '事件1', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=5100, y=-260)
b.add('d2n-gate-boot', {'text': '我數了門口的靴子。比我印象中少一隻——左腳的。可是我的印象只有三秒長，所以也可能沒少。', 'type': 'dialogue', 'title': '事件2', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=5400, y=0)
b.add('d2n-gate-crack', {'text': '黑洞先生西裝的肩膀那裡裂了一道。我問他怎麼弄的，他說「舊的」。可是我昨天好像沒看到——我也不確定我昨天看了什麼。', 'type': 'dialogue', 'title': '事件3', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=5700, y=260)
b.add('d2n-q', {'text': '這件事要放哪裡？\n（記憶體 {{slotUsed}}／4\u3000黑洞先生今天吃了 {{fedToday}}／1）', 'type': 'choice', 'title': '選擇', 'choices': ['留在我這裡（明天睡醒就忘了）', '給黑洞先生吃（他會長回一隻腳）', '交給你保管（留得住，但你要回來）'], 'choiceMode': 'branch'}, x=6000, y=0)
b.add('d2n-keep', {'text': '她把今天這件事留在自己的記憶體裡。', 'type': 'setVariable', 'title': '留著', 'variableOps': [{'id': 'op-0', 'kind': 'add', 'value': 1, 'variable': 'slotUsed'}]}, x=6300, y=-240)
b.add('d2n-feed', {'text': '晚上黑洞先生會把它吃掉。門邊會少一隻靴子——他多長回了一隻腳。', 'type': 'setVariable', 'title': '餵他', 'variableOps': [{'id': 'op-0', 'kind': 'add', 'value': 1, 'variable': 'fedToday'}, {'id': 'op-1', 'kind': 'add', 'value': 1, 'variable': 'fedCount'}, {'id': 'op-2', 'kind': 'add', 'value': 1, 'variable': 'holeFeet'}]}, x=6300, y=0)
b.add('d2n-give', {'text': '她把今天這件事交到你手上。現在只有你記得。', 'type': 'setVariable', 'title': '交給你', 'variableOps': [{'id': 'op-0', 'kind': 'add', 'value': 1, 'variable': 'givenCount'}]}, x=6300, y=240)
b.add('d2n-after', {'text': '好。那我們等黑洞先生回來。', 'type': 'dialogue', 'title': '好。那我們等他回來。', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=6600, y=0)
b.add('d2e-scene', {'text': '螢幕又變成房間裡唯一的光。', 'type': 'scene', 'title': '第二天・夜晚', 'background': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787242999310_bg-night-v2.png'}, x=6900, y=0)
b.add('d2e-back', {'text': '我回來了。', 'type': 'dialogue', 'title': '我回來了。', 'emotion': '餓', 'speaker': '黑洞先生', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787203345974_blackhole-hungry.webp', 'characterId': 'character-25c9632f-cd67-49d0-a4bd-2757b51127e7', 'characterPosition': 'center'}, x=7200, y=0)
b.add('d2e-deja', {'text': '……奇怪。', 'type': 'dialogue', 'title': '……奇怪。', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=7500, y=0)
b.add('d2e-deja2', {'text': '我剛剛好像做過這件事。翻守則、填空位、跟你說晚安。', 'type': 'dialogue', 'title': '我剛剛好像做過這件事。翻守則、填', 'emotion': '發呆', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787196233341_glitch-thinking.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=7800, y=0)
b.add('d2e-deja3', {'text': '可是我記憶體裡沒有這一段。所以應該是我搞錯了。', 'type': 'dialogue', 'title': '可是我記憶體裡沒有這一段。所以應', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=8100, y=0)
b.add('d2e-dejaset', {'text': '', 'type': 'setVariable', 'title': '似曾相識 +1', 'variableOps': [{'id': 'op-0', 'kind': 'add', 'value': 1, 'variable': 'dejaVu'}]}, x=8400, y=0)
b.add('d2e-rulein', {'text': '第 {{ruleVersion}} 版的空位。今天換這一句。你幫我寫。', 'type': 'input', 'title': '填空位', 'inputVariable': 'ruleLine2', 'inputPlaceholder': '寫一句話…', 'inputSuggestions': ['靴子的數量要數。', '問他肩膀怎麼了。', '昨天的我也在。']}, x=8700, y=0)
b.add('d2e-rulever', {'text': '她寫上去。第 {{ruleVersion}} 版，完成。', 'type': 'setVariable', 'title': '守則 +1', 'variableOps': [{'id': 'op-0', 'kind': 'add', 'value': 1, 'variable': 'ruleVersion'}]}, x=9000, y=0)
b.add('d2e-save', {'text': '記得存檔。你不存的話，明天我又要重新認識你一次。', 'type': 'dialogue', 'title': '記得存檔。你不存的話，明天我又要', 'emotion': '平常', 'speaker': '格莉奇', 'character': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/project-e14f9260-e4c0-4ce7-9d2d-70203cdec591/1787216668992_glitch-plain.webp', 'characterId': 'character-15c41e1f-ca37-424f-8c49-ac1031a42928', 'characterPosition': 'center'}, x=9300, y=0)
b.add('d2e-sleep', {'text': '她躺回床上。螢幕的光慢慢暗下去。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=9600, y=0)
b.add('d2e-tbc', {'text': '她躺回床上。門邊那疊短靴裡，裂開的那一雙在最上面。', 'type': 'dialogue', 'title': '旁白', 'speaker': '旁白', 'characterPosition': 'center'}, x=9900, y=0)
b.add('d2e-jump', {'text': '天亮了。', 'type': 'boardJump', 'title': '下一天', 'jumpNodeId': 'd3m-scene', 'jumpBoardId': 'board-day3'}, x=10200, y=0)

b.link('d2m-scene', 'd2m-boot', 'right')
b.link('d2m-boot', 'd2m-load', 'right')
b.link('d2m-load', 'd2m-hub', 'right')
b.link('d2m-hub', 'd2m-lost1', 'right', cond={'op': 'eq', 'value': 0, 'variable': 'savedOk'})
b.link('d2m-lost1', 'd2m-lost2', 'right')
b.link('d2m-lost2', 'd2m-lost3', 'right')
b.link('d2m-lost3', 'd2m-relearn', 'right')
b.link('d2m-hub', 'd2m-ok1', 'right')
b.link('d2m-ok1', 'd2m-ok2', 'right')
b.link('d2m-relearn', 'd2m-join', 'right')
b.link('d2m-ok2', 'd2m-join', 'right')
b.link('d2m-join', 'd2m-rule', 'right')
b.link('d2m-rule', 'd2m-quote', 'right')
b.link('d2m-quote', 'd2m-quote2', 'right')
b.link('d2m-quote2', 'd2m-door', 'right')
b.link('d2m-door', 'd2m-feet', 'right')
b.link('d2m-feet', 'd2n-scene', 'right')
b.link('d2n-scene', 'd2n-alone', 'right')
b.link('d2n-alone', 'd2n-roll', 'right')
b.link('d2n-roll', 'd2n-gate-picture', 'right', cond={'op': 'eq', 'value': 1, 'variable': 'todayEvent'})
b.link('d2n-roll', 'd2n-gate-boot', 'right', cond={'op': 'eq', 'value': 2, 'variable': 'todayEvent'})
b.link('d2n-roll', 'd2n-gate-crack', 'right', cond={'op': 'eq', 'value': 3, 'variable': 'todayEvent'})
b.link('d2n-gate-picture', 'd2n-gate-boot', 'right', cond={'op': 'eq', 'value': 1, 'variable': 'usedPicture'})
b.link('d2n-gate-boot', 'd2n-gate-crack', 'right', cond={'op': 'eq', 'value': 1, 'variable': 'usedBoot'})
b.link('d2n-roll', 'd2n-gate-crack', 'right')
b.link('d2n-gate-picture', 'd2n-q', 'right')
b.link('d2n-gate-boot', 'd2n-q', 'right')
b.link('d2n-gate-crack', 'd2n-q', 'right')
b.link('d2n-q', 'd2n-keep', 'choice-0')
b.link('d2n-q', 'd2n-feed', 'choice-1')
b.link('d2n-q', 'd2n-give', 'choice-2')
b.link('d2n-keep', 'd2n-after', 'right')
b.link('d2n-feed', 'd2n-after', 'right')
b.link('d2n-give', 'd2n-after', 'right')
b.link('d2n-after', 'd2e-scene', 'right')
b.link('d2e-scene', 'd2e-back', 'right')
b.link('d2e-back', 'd2e-deja', 'right')
b.link('d2e-deja', 'd2e-deja2', 'right')
b.link('d2e-deja2', 'd2e-deja3', 'right')
b.link('d2e-deja3', 'd2e-dejaset', 'right')
b.link('d2e-dejaset', 'd2e-rulein', 'right')
b.link('d2e-rulein', 'd2e-rulever', 'right')
b.link('d2e-rulever', 'd2e-save', 'right')
b.link('d2e-save', 'd2e-sleep', 'right')
b.link('d2e-sleep', 'd2e-tbc', 'right')
b.link('d2e-tbc', 'd2e-jump', 'right')

# ══════════════════ 打磨（三輪會審之後）══════════════════

# ── 一、沒存檔那條原本在唸玩家 ──
# 「外接記憶體要自己按存檔。我說過了。」——這是在罵人，而且罰的是玩家。
# glm 給了更好的方向：讓「沒存檔」本身變得有意思，而不是變成懲罰。
b.settext("d2m-lost3", "所以我只能重問一次。有點尷尬，"
                       "不過我每天都在重問，所以也還好。")
b.settext("d2m-relearn", "你隨便講一個都行，我就當那是真的。\n"
                         "反正明天我也會忘——除非這次有人幫我按存檔。")

# ── 二、晚上要對中午的選擇有反應 ──
for nid, route in (("d2n-keep", "keep"), ("d2n-feed", "feed"), ("d2n-give", "give")):
    b.addops(nid, [{"variable": "todayRoute", "kind": "set", "value": route}])

ex = 3600
r_feed = b.say("d2e-r-feed", "黑洞先生今天回來得比平常穩，走路的時候沒有搖。\n格莉奇發現過一件事，現在在他身上。\n她連自己發現過什麼都不記得。",
               who=None, title="他吃掉了", x=ex, y=-260)
r_keep = b.say("d2e-r-keep", "她想跟他講今天發現的那件事。話到嘴邊，"
               "她發現自己已經不確定那是什麼了。", who=None, title="她留著", x=ex, y=0)
r_give = b.say("d2e-r-give", "她今天沒有東西可以跟他講。她發現的那件事在你那裡，"
               "她連自己交出去過都不知道。", who=None, title="交給你了", x=ex, y=260)
b.unlink("d2e-back", "d2e-deja")
b.link("d2e-back", r_feed, "right", cond={"variable": "todayRoute", "op": "eq", "value": "feed"})
b.link("d2e-back", r_keep, "right", cond={"variable": "todayRoute", "op": "eq", "value": "keep"})
b.link("d2e-back", r_give)
for r in (r_feed, r_keep, r_give):
    b.link(r, "d2e-deja")

# ── 三、去重閘門讀的變數沒有人寫 ──
# 三個事件的閘門用 usedPicture／usedBoot 做去重（抽到用過的就往下掉），可是
# 沒有任何卡片寫入這兩個變數，那兩條分支永遠不會成立。抽中就記起來。
# verify.py 現在會抓這種「有人讀沒人寫」的變數。
b.addops("d2n-gate-picture", [{"variable": "usedPicture", "kind": "set", "value": 1}])
b.addops("d2n-gate-boot", [{"variable": "usedBoot", "kind": "set", "value": 1}])

# ── 四、開機速度反映昨天有沒有存檔 ──
# minimax 的點子。原本兩條路共用「系統讀取中……（過久）」，可是有人幫她留住
# 昨天的話，開機本來就該不一樣。這比多寫一句解釋有用。
b.remove("d2m-load")
b.link("d2m-boot", "d2m-hub")
lost = b.say("d2m-load-lost", "系統讀取中……\n……\n……算了。今天沒人幫我。",
             face="當機", title="讀取失敗", x=600, y=300)
okl = b.say("d2m-load-ok", "系統讀取中……（這次比較快）",
            face="發呆", title="讀取成功", x=600, y=-300)
b.unlink("d2m-hub", "d2m-lost1")
b.unlink("d2m-hub", "d2m-ok1")
b.link("d2m-hub", lost, "right", cond={"variable": "savedOk", "op": "eq", "value": 0})
b.link("d2m-hub", okl)
b.link(lost, "d2m-lost1")
b.link(okl, "d2m-ok1")
b.settext("d2m-ok2", "我不記得你。可是牆上寫著你的名字，"
                     "而且我今天醒得比較快——有人替我省下一格。")

# ══════════════ 記憶格（第二輪打磨）══════════════
# 記憶格要在每一天都存在，玩家在 Day 1 學到的東西不能中途消失。
wake = b.wake("d2m", prefill=[])
b.unlink("d2m-scene", "d2m-boot")
b.link("d2m-scene", wake)
b.link(wake, "d2m-boot")

# 有存檔的話，你的名字還在第一格；沒存檔的話她重問一次
b.addops("d2m-ok1", [{"variable": "slot1", "kind": "set", "valueFrom": "playerName"},
                     {"variable": "slotUsed", "kind": "set", "value": 1}])
b.addops("d2m-relearn", [{"variable": "slot1", "kind": "set", "valueFrom": "playerName"},
                         {"variable": "slotUsed", "kind": "set", "value": 1}])

# 中午那件事要走共用的記憶格
b.settext("d2n-keep", "她把今天這件事收進腦子裡。")
b.dropop("d2n-keep", "slotUsed")   # 共用零件會加,這裡不能再加
b.addops("d2n-keep", [{"variable": "pending", "kind": "set", "value": "今天發現的那件事"}])
store_gate, store_outs = b.store(
    "d2n-mem",
    "她說到一半停住了。最舊的那一格自己掉出去了，她連它存在過都不知道。",
    x=3600, y=-700)
b.unlink("d2n-keep", "d2n-after")
b.link("d2n-keep", store_gate)
for n in store_outs:
    b.link(n, "d2n-after")

# 晚上唸一次格子
rep = b.chain([
    ("d2e-mem1", "睡前唸一次。「{{slot1}}」、「{{slot2}}」、「{{slot3}}」、「{{slot4}}」。", "平常", G),
    ("d2e-mem2", "有幾格是空的。我不知道那幾格本來有沒有裝過東西。", "發呆", G),
], x=4600, y=-300, link_prev=False)
b.unlink("d2e-back", "d2e-r-feed")
b.unlink("d2e-back", "d2e-r-keep")
b.unlink("d2e-back", "d2e-r-give")
b.link("d2e-back", rep[0])
b.link(rep[-1], "d2e-r-feed", "right", cond={"variable": "todayRoute", "op": "eq", "value": "feed"})
b.link(rep[-1], "d2e-r-keep", "right", cond={"variable": "todayRoute", "op": "eq", "value": "keep"})
b.link(rep[-1], "d2e-r-give")

# ══════════════ 開機就滿了（第三輪：給 Day 2 自己的形狀）══════════════
# 每一天要長得不一樣。Day 3 是探索、Day 4 是事件池、Day 5 是他在家。
# Day 2 的形狀是：**她開機的時候四格就是滿的**，什麼都裝不進去，得先刪一格。
#
# 這也是「刪掉東西」的教學——而且教得很痛：四格裡有一格是你的名字。
# Day 3 之後改成「最舊的自己掉出去、玩家沒得挑」，所以這是全遊戲唯一一次
# 玩家真的挑得了要忘掉什麼。挑過一次，才知道後面那個「沒得挑」有多不一樣。

full = b.setvar("d2m-full",
    [{"variable": "slot2", "kind": "set", "value": "昨天的殘留快取"},
     {"variable": "slot3", "kind": "set", "value": "一段沒有來源的聲音"},
     {"variable": "slot4", "kind": "set", "value": "門邊有東西裂開了"},
     {"variable": "slotUsed", "kind": "set", "value": 4}],
    text="", title="開機就滿了", x=1800, y=0)
b.unlink("d2m-join", "d2m-rule")
b.link("d2m-join", full)

pre = b.chain([
    ("d2m-f1", "等一下。我開機的時候，四格就已經是滿的了。", "當機", G),
    ("d2m-f2", "「{{slot1}}」、「{{slot2}}」、「{{slot3}}」、「{{slot4}}」。", "平常", G),
    ("d2m-f3", "昨天應該全部清空才對。可是這四個東西還在，而且我不記得自己放進去過。", "發呆", G),
    ("d2m-f4", "滿的話我今天什麼都裝不進來。得先丟掉一格。", "平常", G),
    ("d2m-f5", "你幫我挑。我自己挑不出來——我又不知道它們哪個重要。", "平常", G),
], x=2100, y=0, link_prev=False)
b.link(full, pre[0])

dq = b.choice("d2m-delq", "要刪掉哪一格？\n（刪掉的那件，黑洞先生今天會吃掉。）",
              ["刪掉「{{slot1}}」", "刪掉「{{slot2}}」",
               "刪掉「{{slot3}}」", "刪掉「{{slot4}}」"],
              x=3900, y=0)
b.link(pre[-1], dq)

dx = 4300
DEL = [
    ("name", "刪掉你",
     "格莉奇把第一格清掉。\n「好，空出來了。」她轉過來，看著螢幕。「……你是誰？」\n牆上那個名字還在，可是她的腦子裡已經沒有了。\n她整天都會叫你「你」。",
     [{"variable": "slot1", "kind": "set", "value": ""}]),
    ("cache", "刪掉殘留快取",
     "格莉奇把第二格清掉。什麼事都沒有發生。\n「這個應該是垃圾吧。」她說。\n她說對了，可是她永遠不會知道自己說對了。",
     [{"variable": "slot2", "kind": "set", "value": ""}]),
    ("sound", "刪掉那段聲音",
     "她把第三格清掉。\n"
     "「那是什麼聲音來著。有點像揉東西的聲音，很小聲，在很晚的時候。」\n"
     "話說到一半那段聲音就沒了。她愣了一下，然後聳肩。",
     [{"variable": "slot3", "kind": "set", "value": ""}]),
    ("crack", "刪掉裂開那件事",
     "她把第四格清掉。\n"
     "「門邊有東西裂開了？哪裡？」她走過去看，那疊靴子好好地堆在那裡。\n"
     "裂痕就在最上面那一雙上，她的眼睛掃過去，沒有停。",
     [{"variable": "slot4", "kind": "set", "value": ""}]),
]
outs = []
for k, (tag, title, text, ops) in enumerate(DEL):
    n = b.setvar(f"d2m-del-{tag}",
                 ops + [{"variable": "d2Deleted", "kind": "set", "value": tag},
                        {"variable": "slotUsed", "kind": "set", "value": 3},
                        {"variable": "fedCount", "kind": "add", "value": 1},
                        {"variable": "holeFeet", "kind": "add", "value": 1}],
                 text=text, title=title, x=dx, y=(k - 1.5) * 200)
    b.link(dq, n, f"choice-{k}")
    outs.append(n)

back = b.say("d2m-del-after", "三格。今天可以裝三件事。", who=G, face="平常",
             title="空出來了", x=dx + 500, y=0)
for n in outs: b.link(n, back)
b.link(back, "d2m-rule")

# 晚上他會提到今天被吃掉的那一格。他一天只吃得下一件，所以中午餵他就不吃這個。
ex2 = 5200
EAT = [
    ("name", "黑洞先生今天吃到一個名字。\n"
     "那個名字現在在他裡面，一個字都沒有少。\n"
     "可是他遞不出來。記憶進去就出不來了。", -300),
    ("sound", "黑洞先生今天吃到一段聲音。\n那聲音很小，在很晚的時候。\n像有人在揉什麼。", -100),
    ("crack", "黑洞先生今天吃到一道裂痕。\n門邊那疊靴子今天看起來完好如新。", 100),
    ("cache", "黑洞先生今天吃到一團什麼都不是的東西。\n他嚼了很久。", 300),
]
eat_nodes = []
for tag, text, yy in EAT:
    n = b.say(f"d2e-eat-{tag}", text, who=None, title=f"他吃了（{tag}）", x=ex2, y=yy)
    eat_nodes.append((tag, n))
# 刪掉名字的話，他會讓她知道有人存在過。這是 Day 2 唯一一個情感錨點——
# 兩家說這天只有機制驚奇，情感沒有推進。
nm = b.chain([
    ("d2e-nm1", "什麼名字？", "平常", G),
    ("d2e-nm2", "妳的朋友。", "預設", HOLE),
    ("d2e-nm3", "我有朋友？", "當機", G),
    ("d2e-nm4", "黑洞先生沒有回答第二次。\n她站在原地。\n她看著螢幕的方向，看了很久。", "平常", None),
    ("d2e-nm5", "如果我有朋友，那個人現在在哪裡？", "發呆", G),
    ("d2e-nm6", "她正在看著你。她不知道自己正在看著你。", "平常", None),
], x=ex2 + 300, y=-500, link_prev=False)

join2 = b.say("d2e-eat-join", "她沒有注意到。她從來不注意這種事。", who=None,
              title="她沒注意", x=ex2 + 2400, y=0)
b.link(b.find("d2e-eat-name")["id"], b.find("d2e-nm1")["id"])
b.link(nm[-1], join2)
for tag, n in eat_nodes:
    b.link("d2e-mem2", n, "right", cond={"variable": "d2Deleted", "op": "eq", "value": tag})
    if tag != "name":
        b.link(n, join2)
b.unlink("d2e-mem2", "d2e-r-feed")
b.unlink("d2e-mem2", "d2e-r-keep")
b.unlink("d2e-mem2", "d2e-r-give")
b.link("d2e-mem2", join2)
b.link(join2, "d2e-r-feed", "right", cond={"variable": "todayRoute", "op": "eq", "value": "feed"})
b.link(join2, "d2e-r-keep", "right", cond={"variable": "todayRoute", "op": "eq", "value": "keep"})
b.link(join2, "d2e-r-give")

# 結尾的鉤子。這一天她剛剛才知道自己有一個朋友,而那個朋友就在螢幕外面。
hook2 = b.chain([
    ("d2e-hook1", "我今天知道了一件事。我有一個朋友。", "平常", G),
    ("d2e-hook2", "明天我不會記得這件事。我連自己知道過都不會知道。", "平常", G),
    ("d2e-hook3", "可是你會記得。所以明天你要來提醒我。", "平常", G),
], x=6400, y=0, link_prev=False)
b.unlink("d2e-sleep", "d2e-tbc")
b.link("d2e-sleep", hook2[0])
b.link(hook2[-1], "d2e-tbc")

b.push('Day 2・靴子與裂痕：從線上版反推重建')
