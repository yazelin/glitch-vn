const AB=(()=>{
 const S=%%STEPS%%;
 if(!S.length)return;
 const bar=document.getElementById('ab'), open=document.getElementById('abOpen');
 const bPlay=document.getElementById('abPlay'), bRate=document.getElementById('abRate');
 const now=document.getElementById('abNow'), sub=document.getElementById('abSub');
 const a=new Audio(); a.preload='auto';
 // 下一段先載好，不然每一句之間會有一個明顯的空白。
 const pre=new Audio(); pre.preload='auto';
 let i=-1, playing=false, rate=1;
 const idx=new Map();                       // 段落編號 → 第幾步，點段落用
 S.forEach((s,n)=>s.p.forEach(id=>{ if(!idx.has(id)) idx.set(id,n); }));

 const els=id=>document.getElementById(id);
 function mark(n,on){ (S[n]?.p||[]).forEach(id=>els(id)?.classList.toggle('abOn',on)); }
 function go(n,scroll){
   if(i>=0)mark(i,false);
   i=n;
   if(i>=S.length){stop();return;}
   mark(i,true);
   const first=els(S[i].p[0]);
   if(first&&scroll!==false){
     const r=first.getBoundingClientRect();
     if(r.top<80||r.bottom>innerHeight-140)
       first.scrollIntoView({block:'center',behavior:'smooth'});
   }
   a.src=S[i].u; a.playbackRate=rate;
   if(playing)a.play().catch(()=>{});
   if(S[i+1]){pre.src=S[i+1].u;}
   const ch=(S[i].p[0]||'').split('-')[0].slice(1);
   now.textContent='第 '+ch+' 章';
   sub.textContent=(i+1)+' / '+S.length;
 }
 function play(){
   playing=true; bar.hidden=false; open.hidden=true;
   // 控制列是固定定位，會蓋住捲到最底的那一段，開著的時候把正文墊高。
   document.body.classList.add('abOn2');
   bPlay.textContent='❚❚';
   if(i<0)go(0); else a.play().catch(()=>{});
 }
 function pause(){ playing=false; a.pause(); bPlay.textContent='▶'; }
 function stop(){ pause(); if(i>=0)mark(i,false); i=-1; sub.textContent='讀完了'; }
 a.addEventListener('ended',()=>go(i+1));
 // 檔案掛掉不要卡住整本，跳過去繼續。
 a.addEventListener('error',()=>{ if(playing)go(i+1); });
 bPlay.onclick=()=>playing?pause():play();
 open.onclick=play;
 document.getElementById('abClose').onclick=()=>{
   stop(); bar.hidden=true; open.hidden=false;
   document.body.classList.remove('abOn2');
 };
 bRate.onclick=()=>{ rate=({1:1.25,1.25:1.5,1.5:0.85,0.85:1})[rate]||1;
   a.playbackRate=rate; bRate.textContent=rate+'×'; };
 // 點任何一段就從那裡開始聽。
 addEventListener('click',e=>{
   const t=e.target.closest('[id^="b"]'); if(!t||!idx.has(t.id))return;
   if(e.target.closest('a'))return;
   go(idx.get(t.id),false); play();
 });
 return {play};
})();
