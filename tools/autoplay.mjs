// 自動玩家：照調查板的便條走，從第一天玩到結局，整份對白與每一步決定存進 scratchpad/transcript.txt。
// 用法：node tools/autoplay.mjs（讀 larch/inv/preview.json 的 playUrl；Playwright 取自 line-sticker-studio 的 node_modules）
// 2026-09-07 用它連跑九輪，抓到十幾個門檻與接線的 bug（見 git log 同日）。它是個笨玩家：便條沒提到的地方輪流去。
// 照板上便條走的自動玩家：從第一天玩到結局，整份對白與每一步決定存進 transcript
import { createRequire } from 'node:module';
const require_ = createRequire(import.meta.url);
const { chromium } = require_('/home/ct/line-sticker-studio/node_modules/playwright');
import fs from 'node:fs';
const SD=process.env.OUT || '/tmp';
// 走法：notes＝照便條（預設）、firstline＝只看便條第一行、casual＝一半的深夜不出門、
// explore＝不看便條，挑去得最少的地方、random＝擲骰。
// random 用固定種子，同一個 SEED 跑出來一樣，方便重現。
const POLICY=process.env.POLICY || 'notes';
let seed=(Number(process.env.SEED)||1)>>>0;
const rnd=()=>{ seed=(seed+0x6D2B79F5)>>>0; let t=seed; t=Math.imul(t^t>>>15,t|1); t^=t+Math.imul(t^t>>>7,t|61); return ((t^t>>>14)>>>0)/4294967296; };
const rpick=(a)=>a[Math.floor(rnd()*a.length)];
const pv = JSON.parse(fs.readFileSync('/home/ct/glitch-vn/larch/inv/preview.json','utf8'));
// 記憶體吃緊的機器上一次跑一輪也會被系統擋掉，所以關掉用不到的東西（2026-09-09）
const browser = await chromium.launch({ args: ['--disable-gpu','--disable-dev-shm-usage',
  '--disable-extensions','--no-sandbox','--js-flags=--max-old-space-size=384','--renderer-process-limit=2'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on('pageerror', e => out(`PAGE ERR: ${String(e).slice(0,200)}`));
const T=[]; const out=(s)=>{ T.push(s); };
const flush=()=>fs.writeFileSync(`${SD}/transcript.txt`, T.join('\n'));
const text = async () => (await page.locator('body').innerText()).replace(/\s+/g,' ').replace(/存檔 讀取 歷史 自動 快轉 全屏 標題 設定/,'').replace(/點擊對話框繼續/,'').replace(/^\d+\s*/,'').trim();
const frames = () => page.frames().filter(f => f !== page.mainFrame());
const frameWith = async (s) => { for (const f of frames()) { try { if ((await f.locator('body').innerText()).includes(s)) return f; } catch(e){} } return null; };
const boardFrame = () => frameWith('今天要去哪');
const menuFrame = async () => { for (const f of frames()) { try { if (await f.locator('button.seg').count() || await f.locator('button#skip', { hasText: '先走' }).count()) return f; } catch(e){} } return null; };
const done = new Set(); const visits = {}; const phoneDays = new Set(); let outings=0; let lastCard=''; let stuck=0;
const SPOT_HINT = [['樓下','一樓'],['信箱','一樓'],['管理員','一樓'],['一樓','一樓'],['樓上那間','頂樓收音機店'],['頂樓','頂樓收音機店'],['材料行','材料行'],['便利商店','便利商店'],['洗衣店','自助洗衣店'],['工作室','斑比工作室'],['經紀公司','車站前那條街'],['車站','車站前那條街'],['十四樓','十四樓大廳'],['手辦','手辦店'],['關東煮','便利商店'],['那家店','便利商店'],['店員','便利商店']];
const pickSpot = async (bf) => {
  const when = await bf.locator('#when').textContent();
  let todo = await bf.locator('.todo p').allTextContents();
  if (POLICY==='firstline') todo = todo.slice(0,1);   // 只讀第一行的人
  lastTodo = todo;
  const spots = []; for (const b of await bf.locator('button.spot:not([disabled])').all()) spots.push({ name: (await b.locator('.name').textContent()).trim(), who: (await b.locator('.who').textContent()).trim(), el: b });
  out(`\n=== 板 ${when} | 便條：${todo.join(' / ')} | 可去：${spots.map(s=>s.name+'('+s.who+')').join('、')}`);
  let target=null;
  const slotName = (when.match(/上午|下午|晚上|深夜/)||[''])[0];
  if (POLICY==='casual' && slotName==='深夜' && rnd()<0.5) { out('→ 這個深夜不出門'); return 'skip'; }
  if (POLICY==='random') { target=rpick(spots); }
  else if (POLICY!=='explore') for (const line of todo) { const t=(line.match(/上午|下午|晚上|深夜|白天/)||[''])[0];
    if (t==='白天' ? (slotName!=='上午'&&slotName!=='下午') : (t && t!==slotName)) continue; for (const [k,n] of SPOT_HINT) if (line.includes(k)) { const s=spots.find(x=>x.name===n); if (s) { target=s; break; } } if (target) break; }
  if (!target) { spots.sort((a,b)=>(visits[a.name]||0)-(visits[b.name]||0)); target=spots[0]; }
  if (!target) return null;
  visits[target.name]=(visits[target.name]||0)+1; outings++;
  out(`→ 去 ${target.name}`);
  await target.el.click(); return target.name;
};
let lastTodo = [];
const pickMenu = async (mf, spot, when) => {
  const items=[]; for (const b of await mf.locator('button.seg').all()) items.push({ label:(await b.locator('.label').textContent()).trim(), el:b });
  const fresh0 = items.filter(i=>!done.has(spot+'|'+i.label)); const fresh = fresh0.filter(i=>!/再問|第三次|同一件事/.test(i.label)).concat(fresh0.filter(i=>/再問|第三次|同一件事/.test(i.label)));
  out(`  選單（${items.map(i=>i.label).join('、')}）`);
  // 便條提到的字出現在哪一格的標籤裡，那一格優先（人會這樣讀）
  const overlap = (a,b) => { let best=0; for (let i=0;i<a.length;i++) for (let j=i+3;j<=a.length;j++) if (b.includes(a.slice(i,j))) best=Math.max(best,j-i); return best; };
  const hinted = fresh.map(i => ({ i, s: Math.max(0, ...lastTodo.map(t => overlap(i.label, t))) })).filter(x => x.s >= 3).sort((a,b) => b.s - a.s).map(x => x.i);
  const pick = POLICY==='random' ? (rpick(fresh.length?fresh:items))
             : POLICY==='explore' ? (fresh[0] || items[items.length-1])
             : (hinted[0] || fresh[0] || items[items.length-1]);
  if (!pick) { out('  選單空的（'+(await mf.locator('.empty').allTextContents()).join('')+'），先走'); await mf.locator('button', { hasText: '先走' }).first().click().catch(()=>{}); return; }
  done.add(spot+'|'+pick.label); out(`  → 選「${pick.label}」`); await pick.el.click();
};
await page.goto(pv.playUrl, { waitUntil: 'load', timeout: 60000 }); await page.waitForTimeout(4000);
await page.locator('button', { hasText: '開始遊戲' }).first().click(); await page.waitForTimeout(3000);
let spot=null, when=''; const t0=Date.now();
for (let step=0; step<6000 && Date.now()-t0 < 40*60*1000; step++){
  const t = await text();
  if (t.includes('開始遊戲') && t.includes('繼續遊戲')) { out('\n=== 回到標題（遊戲結束）'); break; }
  const bf = await boardFrame();
  if (bf) { await page.waitForTimeout(600); const bf2=await boardFrame(); if(!bf2) continue; when = await bf2.locator('#when').textContent();
    // 每天上午開一次手機翻一遍（design/調查篇-手機.md 驗收）：HUD 背包 → 手機 → 使用道具 → 記下看到的貼文 → 收起來
    if (when.includes('上午') && !phoneDays.has(when.split(' ・')[0])) { phoneDays.add(when.split(' ・')[0]);
      try { await page.mouse.click(1180,112); await page.waitForTimeout(1200); const it=page.locator('text=手機').first(); if (await it.count()) { await it.click(); await page.waitForTimeout(500); }
        const use=page.locator('button', { hasText: '使用道具' }).first(); if (await use.count()) { await use.click(); await page.waitForTimeout(2500); }
        let pf=null; for (const f of frames()) { try { if ((await f.locator('#close').count())) pf=f; } catch(e){} }
        if (pf) { const msgs=(await pf.locator('.msg .bub').allTextContents()).map(t=>t.slice(0,16)); await pf.locator('nav button', { hasText: '格莉奇' }).click(); await page.waitForTimeout(300);
          const posts=await pf.locator('.post .txt').allTextContents(); out(`  [手機] 訊息 ${msgs.length} 則 ${JSON.stringify(msgs)}；貼文 ${posts.length} 則：${posts.map(t=>t.slice(0,10)).join('｜')}`);
          await pf.locator('#close').click(); await page.waitForTimeout(2000); }
        else { out('  [手機] 打不開'); await page.keyboard.press('Escape'); }
      } catch(e) { out('  [手機] 出錯 '+String(e).slice(0,80)); }
      continue; } spot = await pickSpot(bf2); if (spot==='skip') { await bf2.locator('#skip').click(); await page.waitForTimeout(2000); continue; }
    if (!spot) { out('沒地方可去，這一段不出門'); await bf2.locator('#skip').click(); } await page.waitForTimeout(2500); continue; }
  const mf = await menuFrame();
  if (mf) { await pickMenu(mf, spot, when); await page.waitForTimeout(1800); continue; }
  const opts = await page.locator('button', { hasText: /^0[1-9]\s/ }).all();
  if (opts.length) { const labels=[]; for (const o of opts) labels.push((await o.textContent()).trim()); out(`  [選項] ${labels.join(' | ')} → 選 ${labels[0]}`); await opts[0].click(); await page.waitForTimeout(900); continue; }
  if (await frameWith('她 記 住 的')) { await page.waitForTimeout(1500); stuck=0; continue; }   // 片尾字卷自己走，等它
  if (t && t !== lastCard) { out('  ' + t.slice(0,220)); lastCard = t; stuck=0; } else { stuck++; if (stuck>40) { out('★ 卡住 40 下沒變：'+t.slice(0,120)); await page.screenshot({ path: `${SD}/stuck.png` }); break; } }
  await page.mouse.click(640,640); await page.waitForTimeout(420);
  if (step % 50 === 0) flush();
}
out(`\n=== 走法 ${POLICY} 種子 ${process.env.SEED||1}`);
out(`\n=== 統計：出門 ${outings} 次，到過 ${JSON.stringify(visits)}，選過 ${done.size} 格，${Math.round((Date.now()-t0)/1000)} 秒`);
flush(); await page.screenshot({ path: `${SD}/autoplay-end.png` }); await browser.close();
console.log(T.slice(-3).join('\n'));
