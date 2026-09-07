// 她的待辦：照當下狀態寫兩三行她自己的判斷。板上的便條與筆記卡「明天」那一頁共用這一份。
// 這是引導，可是全部要用她的口氣，不可以有一句像系統提示（design/調查篇.md 零）。
// 推送層把這一份塞進 board.html 與 notes.html 的 /*@@TODO@@*/。
function todoLines(v){
  function n(k){ var x=Number(v[k]); return isNaN(x)||v[k]===''||v[k]==null?0:x; }
  function b(k){ return v[k]===true||v[k]==='true'; }
  var L=[];
  if(!b('open_roof')) L.push('先從樓下問起。');
  else if(n('met_諾亞')<1) L.push('樓上那間，門開著就是有開。');
  if(b('open_parts') && n('met_材料行老闆')<1) L.push('車站後面那家材料行。那顆管子。');
  if(n('day')>=2 && n('hole_sightings')===0) L.push('晚上七點多，一樓。信箱前面。');
  if(n('hole_sightings')>=1 && !b('see_admin')) L.push('問管理員那個穿西裝的。');
  if(n('hole_sightings')===1 && n('day')>=5) L.push('一樓晚上。他還會來。');
  if(n('hole_sightings')===2 && n('day')>=8) L.push('一樓晚上。再去一次。');
  if(n('day')>=4 && n('night_visits')===0) L.push('深夜。便利商店還開著。');
  if(b('open_laundry') && !b('laundry_night1')) L.push('隔壁那家洗衣店，深夜也開。');
  if(b('laundry_night1') && n('trust_斑比')<2) L.push('洗衣店那個人晚上會在。再去一次。');
  if(b('open_studio') && n('trust_斑比')<3) L.push('畫她的人約我去工作室。稿子帶著。');
  if(n('trust_斑比')>=3 && !b('names_seen')) L.push('深夜再去工作室一次。');
  if(b('names_seen') && n('strikes')<3) L.push('回頭看前幾天寫的結論。');
  if(b('clue_list') && n('day')>=4 && n('night_visits')>=3 && n('strikes')>=3) L.push('上午，頂樓。把筆記寫完。');
  if(!L.length) L.push('再去一次同一個地方。');
  return L.slice(0,3);
}
