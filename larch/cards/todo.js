// 她的待辦：照當下狀態寫兩三行她自己的判斷。板上的便條與筆記卡「明天」那一頁共用這一份。
// 這是引導，可是全部要用她的口氣，不可以有一句像系統提示（design/調查篇.md 零）。
// 推送層把這一份塞進 board.html 與 notes.html 的 /*@@TODO@@*/。
function todoLines(v){
  function n(k){ var x=Number(v[k]); return isNaN(x)||v[k]===''||v[k]==null?0:x; }
  function b(k){ return v[k]===true||v[k]==='true'; }
  // 兩層：P 是通往那面牆的那條線（店員 → 洗衣店 → 工作室），永遠排在前面；
  // L 是其他值得去的地方。只有三行位置，主線被擠掉的話玩家會走不到結局（2026-09-08）。
  var P=[], Q=[], L=[];
  if(!b('open_roof')) L.push('先從樓下問起。');
  else if(n('met_諾亞')<1) L.push('樓上那間，門開著就是有開。');
  if(b('open_parts') && n('met_材料行老闆')<1) L.push('車站後面那家材料行。那顆管子。');
  if(b('tube_bought') && !b('tube_given')) L.push('管子買到了。拿上去頂樓給他。');
  if(n('day')>=2 && n('hole_sightings')===0) L.push('晚上七點多，一樓。信箱前面。');
  if(n('hole_sightings')>=1 && !b('see_admin')) L.push('問管理員那個穿西裝的。');
  if(n('hole_sightings')===1 && n('day')>=5) L.push('一樓晚上。他還會來。');
  if(n('hole_sightings')===2 && n('day')>=10) L.push('一樓晚上。再去一次。');
  if(n('day')>=4 && n('night_visits')===0) L.push('深夜。便利商店還開著。');
  if(b('open_laundry') && !b('laundry_night1')) P.push('隔壁那家洗衣店，深夜也開。');
  if(b('laundry_night1') && n('trust_斑比')<2) P.push('洗衣店那個人晚上會在。再去一次。');
  if(b('open_studio') && n('trust_斑比')<3) P.push('晚上去工作室。稿子帶著。');  // 寫時段，不然深夜也被拿去跑工作室
  if(n('trust_斑比')>=3 && !b('names_seen')) P.push('深夜再去工作室一次。');
  if(b('names_seen') && n('strikes')<3) P.push('回頭看前幾天寫的結論。');
  // 牆看到之後主線就結束了，第一層空出來，十四樓那一行升上去（2026-09-09）：
  // 只讀第一行的玩家九輪零次碰到 0x，就是因為那一行永遠排在第二層。
  var t14up=false, sumLine=-1;
  if(b('open_tower14') && !b('zero_answered')){
    var t14 = n('met_櫃檯')>=5 ? '白天的十四樓大廳。再約一個訪問。' : '白天的十四樓大廳。再跟櫃檯約一次訪問。';
    if(b('names_seen')){ P.push(t14); t14up=true; } else Q.push(t14);
  }
  // 收尾那一行：還有線沒走完的話，先讓她自己說一句，不然玩家第九天就把本子寫完了。
  if(b('clue_list') && n('day')>=4 && n('night_visits')>=3 && n('strikes')>=3){
    var left=[];
    if(!b('zero_answered') && b('open_tower14') && !t14up) left.push('白天的十四樓，那個訪問');
    if(n('trust_貓草')<3) left.push('深夜那個人');
    if(n('trust_保全')<3 && b('open_tower14')) left.push('大廳那個保全');
    if(left.length) P.push('本子還有空的地方。'+left[0]+'我還沒問完。');
    else { P.push('本子差不多了。剩下的時間再走一遍。'); sumLine=P.length-1; }
  }
  // 2026-09-07 自動玩家跑完一輪抓到的斷點：店員的信任、貓草那條線、抄信箱，沒有人提醒就永遠走不到
  if(n('day')>=2 && !b('note_mailbox')) L.push('晚上去一樓，把信箱的名牌抄下來。');
  if(n('day')>=2 && n('trust_店員')<1) P.push(n('met_店員')>=3 ? '便利商店晚上再去一次。問店員一件事。' : '便利商店。多去幾次，讓他認得。');

  // 2026-09-08 自動玩家第十天才問到這一句：原本掛了 trust_貓草，把通往斑比的唯一一條路壓在貓草那條線後面
  if(n('trust_店員')>=1 && !b('open_laundry') && n('day')>=4) P.push('問店員這條街深夜還有什麼開著。');
  // 十四樓那條線自己排一層：它不是結局的必要條件，可是沒有人提醒就不會有人去第六次。
  // 白天她只會擋掉（短版一張卡），要問到十四樓那件事得深夜去（問答矩陣 四）
  if(!b('open_tower14') && b('open_studio')) Q.push('深夜去工作室。問她 0x 那張圖是誰畫的。');
  // 貓草那條線本來排在第三層，二十五輪自動試玩一次都沒有浮上來（深夜全給了工作室）。
  if(n('night_visits')>=1 && n('trust_貓草')<1) Q.push('深夜的便利商店。關東煮前面那個人，再去講一次。');
  // 他的後兩階：不提醒的話玩家升到一就停在那裡（十四天那一批第十二天才升到一，第十三天沒有人告訴他要幹嘛）
  if(n('trust_貓草')===1 && n('met_鐵塔')>=1 && !b('asked_貓草_鐵塔')) Q.push('深夜的便利商店。問他她的經紀人。');
  if(n('trust_貓草')>=2 && !b('asked_貓草_格莉奇')) Q.push('深夜的洗衣店。他有時候也在那裡。');
  // 三階之後他才會讓人跟他回家，而且要先有那六行名單（橋段2 九）
  if(n('trust_貓草')>=3 && b('clue_list') && !b('seen_catgrass_home')) Q.push('深夜的便利商店。他說可以去他家。');
  // 「本子差不多了」是收尾用的一句，底下還有事情可以做的時候不佔位置
  if(sumLine>=0 && Q.length) P.splice(sumLine,1);
  L=P.concat(Q,L);
  if(!L.length) L.push('再去一次同一個地方。');
  return L.slice(0,3);
}
