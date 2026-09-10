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
const done = new Set(); const visits = {}; const phoneDays = new Set(); let tapeTried=false, taped=false; let outings=0; let lastCard=''; let stuck=0;
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
  // DEBUG_TAPE=1：優先挑會跳出錄音的那幾格，用來驗錄音帶進背包之後播不播得出來
  if (process.env.DEBUG_TAPE && !taped) {
    const rec = fresh.find(i => /問諾亞那個穿西裝的|問店員那個穿西裝的|問老闆那個穿西裝的/.test(i.label));
    if (rec) { done.add(spot+'|'+rec.label); out(`  → 選「${rec.label}」（找錄音）`); await rec.el.click(); return; }
  }
  // PREFER=甲,乙：指定要優先點的格（用來把難排到的場逼出來驗，例如三張背包卡）
  if (process.env.PREFER) {
    const want = process.env.PREFER.split(',').map(x=>x.trim()).filter(Boolean);
    const hit = items.find(i => want.some(w => i.label.includes(w)));
    if (hit && !done.has(spot+'|'+hit.label)) {
      done.add(spot+'|'+hit.label); out(`  → 選「${hit.label}」（PREFER）`); await hit.el.click(); return;
    }
  }
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
    if ((when.includes('上午') && !phoneDays.has(when.split(' ・')[0])) || (taped && !tapeTried)) { phoneDays.add(when.split(' ・')[0]);
      try { await page.mouse.click(1180,112); await page.waitForTimeout(1200); const it=page.locator('text=手機').first(); if (await it.count()) { await it.click(); await page.waitForTimeout(500); }
        // 錄到的那一卷要能在包包裡聽（design/調查篇-背包與謎題.md）。整輪驗一次就好。
        if (!tapeTried) {
          const tape = page.locator('text=/^錄音・/').first();
          if (await tape.count()) {
            tapeTried = true;
            out('  [錄音帶] 包包裡有 ' + ((await tape.textContent()) || '').trim() + '，播來聽');
            await tape.click().catch(()=>{}); await page.waitForTimeout(500);
            const useTape = page.locator('button', { hasText: '使用道具' }).first();
            if (await useTape.count()) { await useTape.click(); await page.waitForTimeout(2500); }
            continue;
          }
        }
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
  // 選項卡：標籤長成「01 問他 0x 那邊的事」。Larch 的元件在 shadow DOM 裡，
  // querySelectorAll 穿不進去，只有 Playwright 的 locator 穿得過（2026-09-09 抓到：
  // 之前用 evaluate 找元素一直找不到，鐵塔門口那一場因此整段被跳過，十四樓開不了）。
  // 標籤是「01打一行送出去」，數字跟字之間沒有空白（畫面上看到的那個空隙是排版）。
  // 之前的正規式要求數字後面接空白或標點，所以一顆都對不到（2026-09-09 用無障礙樹比對出來）。
  const optLoc = page.getByRole('button').filter({ hasText: /^\s*0[1-9]/ });
  const optHits = [];
  for (const b of await optLoc.all()) {
    const t = ((await b.textContent()) || '').replace(/[\s\u00a0\u3000]+/g, ' ').trim();
    if (t.length < 3 || t.length > 40) continue;                    // 只要最裡面那一層，外框的文字會很長
    const box = await b.boundingBox().catch(() => null);
    if (!box || box.height > 90) continue;
    if (optHits.some(o => o.t === t)) continue;
    optHits.push({ b, t });
  }
  if (!optHits.length && /(^|[\s\u3000])0[1-9][\s\u3000]/.test(t) && process.env.DUMP) {
    // 診斷：看到選項文字卻抓不到元素的時候，把畫面、DOM、無障礙樹都存下來（2026-09-09）
    const names = [];
    for (const b of await page.getByRole('button').all()) {
      names.push({ name: (await b.getAttribute('aria-label')) || '', inner: ((await b.innerText().catch(()=>'')) || '').replace(/\s+/g,' ').trim(),
                   txt: ((await b.textContent().catch(()=>'')) || '').replace(/\s+/g,' ').trim() });
    }
    fs.writeFileSync(`${SD}/choice-buttons.json`, JSON.stringify(names, null, 1));
    fs.writeFileSync(`${SD}/choice-dom.html`, await page.content());
    fs.writeFileSync(`${SD}/choice-aria.txt`, await page.locator('body').ariaSnapshot().catch(e=>String(e)));
    await page.screenshot({ path: `${SD}/choice.png` });
    out('  ★ 選項抓不到，已存 choice-dom.html / choice-aria.txt / choice.png');
    flush(); await browser.close(); process.exit(0);
  }
  // 錄音那一題：對貓草按下去他會轉身，那一晚就不算（design/調查篇-橋段2.md 七）。
  // 自動玩家每一題都選第一個，所以會把他那三個晚上全燒掉。認得出是他就選不開。
  let pick_ = optHits[0];
  if (optHits.length > 1 && /開錄音機/.test(optHits[0].t) && /貓草|關東煮/.test(lastCard)) {
    pick_ = optHits.find(o => /不開/.test(o.t)) || optHits[0];
  }
  if (optHits.length) { out(`  [選項] ${optHits.map(o=>o.t).join(' | ')} → 選 ${pick_.t}`);
    if (/開錄音機/.test(pick_.t)) taped = true;      // 錄到了，下一次開板去包包裡把那一卷播出來
    await pick_.b.click({ timeout: 4000 }).catch(()=>{}); await page.waitForTimeout(900); continue; }
  if (await frameWith('她 記 住 的')) { await page.waitForTimeout(1500); stuck=0; continue; }   // 片尾字卷自己走，等它
  if (t && t !== lastCard) { out('  ' + t.slice(0,220)); lastCard = t; stuck=0; } else { stuck++;
    // 卡住的時候多半是有一個視窗要按（取得道具那種，按鈕在外掛的 iframe 裡）。
    // 跳過工具列、跳過純數字的（那是背包上的件數，點下去只會把背包打開）。
    // 背包卡（open-bag）：外掛 iframe 裡列著道具，點名字就是拿它出來。
    // BAG=守則本 指定要挑哪一件；沒設就不動，讓它照預設分支走。
    if (process.env.BAG && stuck % 5 === 4) {
      for (const f of frames()) {
        const it = f.locator('button, li, [role=button]').filter({ hasText: new RegExp(process.env.BAG) });
        if (await it.count().catch(()=>0)) {
          out(`  [背包] 挑「${process.env.BAG}」`);
          await it.first().click({ timeout: 2500 }).catch(()=>{});
          stuck = 0; break;
        }
      }
      if (stuck === 0) continue;
    }
    if (stuck % 9 === 8) {
      const NAV = ['存檔','讀取','歷史','自動','快轉','全屏','標題','設定','背包','關閉','先走'];
      const WANT = /確定|好的|收下|放進|取得|繼續|知道了|完成|回去|離開|返回/;
      let done_ = false;
      for (const scope of [page, ...frames()]) {
        for (const b of await scope.getByRole('button').all().catch(()=>[])) {
          const label = ((await b.textContent().catch(()=>'')) || '').replace(/\s+/g,'').trim();
          if (!label || NAV.includes(label) || /^\d+$/.test(label) || label.length > 12) continue;
          if (stuck < 26 && !WANT.test(label)) continue;   // 先只點看起來像確認的，再放寬
          out(`  [卡住] 試著點「${label}」`);
          await b.click({ timeout: 2500 }).catch(()=>{});
          done_ = true; break;
        }
        if (done_) break;
      }
      if (!done_) await page.keyboard.press('Escape').catch(()=>{});
    } if (stuck>40) { out('★ 卡住 40 下沒變：'+t.slice(0,120)); await page.screenshot({ path: `${SD}/stuck.png` }); break; } }
  await page.mouse.click(640,640); await page.waitForTimeout(420);
  if (step % 50 === 0) flush();
}
out(`\n=== 走法 ${POLICY} 種子 ${process.env.SEED||1}`);
out(`\n=== 統計：出門 ${outings} 次，到過 ${JSON.stringify(visits)}，選過 ${done.size} 格，${Math.round((Date.now()-t0)/1000)} 秒`);
flush(); await page.screenshot({ path: `${SD}/autoplay-end.png` }); await browser.close();
console.log(T.slice(-3).join('\n'));
