// 插件卡的機械驗收。**不是截圖看一眼**：實際跑一遍 postMessage 契約，
// 檢查寫回的變數對不對、完成事件帶的東西對不對。
// iframe 的 sandbox 跟正式一模一樣（allow-scripts，沒有 same-origin）。
//
//   node tools/card_test.mjs
// playwright 沒裝在這個 repo（見 reference_local_disk_full_and_test_tooling）。
// 用 createRequire 指到別的 repo 那一份，ESM 的 import 不吃 NODE_PATH。
import { createRequire } from 'node:module';
const require_ = createRequire(import.meta.url);
const { chromium } = require_(process.env.PW ||
  '/home/ct/line-sticker-studio/node_modules/playwright');
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const DIR = path.resolve('larch/cards');
const PORT = Number(process.env.PORT || 8231);
const MIME = { '.html': 'text/html; charset=utf-8' };

const server = http.createServer((req, res) => {
  const f = path.join(DIR, decodeURIComponent(req.url.split('?')[0]).replace(/^\//, ''));
  if (!f.startsWith(DIR) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'text/plain' });
  res.end(fs.readFileSync(f));
});
await new Promise(r => server.listen(PORT, r));

let fails = 0;
const ok = (label, pass, detail = '') => {
  console.log(`  ${pass ? 'ok  ' : '★ FAIL'} ${label}${detail ? '  ' + detail : ''}`);
  if (!pass) fails++;
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

// 宿主收到的訊息會被推進 window.__msgs
async function open(card, values) {
  await page.goto(`http://localhost:${PORT}/host.html`, { waitUntil: 'load' });
  await page.evaluate(v => {
    window.__msgs = [];
    const orig = window.onmessage;
    window.addEventListener('message', e => { if (e.data && e.data.type) window.__msgs.push(e.data); });
    document.getElementById('vals').value = JSON.stringify(v);
  }, values);
  await page.click(`[data-card="${card}"]`);
  await page.waitForFunction(() => window.__msgs.some(m => m.type === 'larch:ready'), { timeout: 8000 });
  await page.waitForTimeout(350);
  return page.frameLocator('#f');
}
const msgs = () => page.evaluate(() => window.__msgs);

console.log('\n=== 調查板 ===');
{
  const V = { day: 3, slot: 2, met: '管理員,店員' };   // 什麼都沒開，只有一開始那五個
  const fr = await open('board.html', V);

  const when = await fr.locator('#when').textContent();
  ok('標頭顯示第幾天與時段', when.includes('第 3 天') && when.includes('晚上'), when);

  const openSpots = fr.locator('button.spot:not(.locked)');
  ok('解鎖的畫成可點的', (await openSpots.count()) === 5, `${await openSpots.count()} 個`);
  // 沒開又有提示的要看得到（灰的），沒開又沒提示的（trust 3 私人地方）根本不畫。
  const locked = fr.locator('button.spot.locked');
  ok('沒開但有提示的畫成灰的', (await locked.count()) === 7, `${await locked.count()} 個`);
  // trust 3 那五個私人地方是「場景不是地點」，板上永遠不該有它們。
  ok('貓草家不在板上（那是場景不是地點）',
     (await fr.locator('button.spot', { hasText: '貓草家' }).count()) === 0);
  const roofHint = fr.locator('button.spot.locked', { hasText: '頂樓收音機店' });
  ok('提示用他自己的口氣',
     (await roofHint.locator('.who').textContent()).includes('我需要一個壞掉的東西'));
  ok('灰的點不下去', await roofHint.isDisabled());

  // **一樓的晚上一定要進得去**，那是黑洞先生唯一會出現的時段。
  // 「沒有常駐」不等於「沒開」，這一條之前寫錯過，把全作最重要的一場關掉了。
  const lobby = fr.locator('button.spot', { hasText: '一樓' });
  ok('一樓晚上進得去', !(await lobby.isDisabled()));
  ok('一樓晚上標「開著，可能沒人」', (await lobby.locator('.who').textContent()) === '開著，可能沒人');

  const store = fr.locator('button.spot:not(.locked)', { hasText: '便利商店' });
  ok('去過的人才顯示名字', (await store.locator('.who').textContent()) === '店員');
  const street = fr.locator('button.spot:not(.locked)', { hasText: '車站前那條街' });
  ok('沒去過的人只顯示「沒去過」', (await street.locator('.who').textContent()) === '沒去過');

  await fr.locator('button.spot', { hasText: '一樓' }).click();
  await page.waitForFunction(() => window.__msgs.some(m => m.type === 'larch:complete'), { timeout: 5000 });
  const m = await msgs();
  const sets = Object.fromEntries(m.filter(x => x.type === 'larch:set').map(x => [x.name, x.value]));
  const done = m.find(x => x.type === 'larch:complete');

  ok('寫回 dest', sets.dest === 'lobby', JSON.stringify(sets.dest));
  ok('時段往前走一格', sets.slot === 3, `slot=${sets.slot}`);
  ok('沒有跨日（還沒到深夜）', sets.day === undefined, `day=${sets.day}`);
  ok('完成事件帶目的地', done && done.result === 'lobby');
  ok('here 一定含常駐的管理員或晚上的黑洞先生',
     typeof sets.here === 'string' && (sets.here.includes('黑洞先生') || sets.here === ''),
     `here="${sets.here}"（一樓晚上常駐是空，黑洞先生 60%）`);
}

console.log('\n=== 調查板：一顆布林開一個地方 ===');
{
  // **解鎖要能被一張普通對話卡打開。** 逗號清單要「讀出來、加一個、寫回去」，
  // 對話卡做不到；布林的話管理員講完那句話直接把 open_roof 設 true 就好。
  const shut = await open('board.html', { day: 2, slot: 0, met: '管理員' });
  ok('open_roof 沒設，頂樓是灰的',
     (await shut.locator('button.spot', { hasText: '頂樓收音機店' }).getAttribute('class')).includes('locked'));
  const opened = await open('board.html', { day: 2, slot: 0, open_roof: true, met: '管理員,諾亞' });
  const roofOpen = opened.locator('button.spot', { hasText: '頂樓收音機店' });
  ok('open_roof = true，頂樓就開了', !(await roofOpen.getAttribute('class')).includes('locked'));
  ok('開了之後顯示常駐的人', (await roofOpen.locator('.who').textContent()) === '諾亞');
  // 字串 'true' 也要吃（Larch 的變數型別可能是文字）
  const asText = await open('board.html', { day: 2, slot: 0, open_roof: 'true', met: '管理員,諾亞' });
  ok('字串 true 也算開',
     !(await asText.locator('button.spot', { hasText: '頂樓收音機店' }).getAttribute('class')).includes('locked'));
}

console.log('\n=== 調查板：錄音間門口永遠進不去 ===');
{
  const fr = await open('board.html',
    { day: 5, slot: 0, met: '管理員,店員,貓草' });
  const booth = fr.locator('button.spot', { hasText: '錄音間門口' });
  ok('booth 不管怎樣都是灰的', (await booth.getAttribute('class')).includes('locked'));
  ok('booth 點不下去', await booth.isDisabled());
  ok('booth 的提示永遠是那一句',
     (await booth.locator('.who').textContent()).includes('可是我進不去'));
  ok('設什麼變數貓草家都不會出現在板上',
     (await fr.locator('button.spot', { hasText: '貓草家' }).count()) === 0);
}

console.log('\n=== 調查板：深夜之後換日 ===');
{
  const fr = await open('board.html', { day: 3, slot: 3, met: '店員,貓草' });
  await fr.locator('button.spot:not(.locked)', { hasText: '便利商店' }).click();
  await page.waitForFunction(() => window.__msgs.some(m => m.type === 'larch:complete'), { timeout: 5000 });
  const sets = Object.fromEntries((await msgs()).filter(x => x.type === 'larch:set').map(x => [x.name, x.value]));
  ok('深夜之後 slot 歸零', sets.slot === 0, `slot=${sets.slot}`);
  ok('深夜之後 day 加一', sets.day === 4, `day=${sets.day}`);
  ok('深夜便利商店貓草必定在', String(sets.here).includes('貓草'), `here="${sets.here}"`);
}

console.log('\n=== 調查筆記 ===');
{
  const V = {
    notes: 'name_cat,name_tower,name_zero,name_bambi,name_noah,name_del,' +
           'see_admin,see_noah,see_guard,see_zero,clue_real,clue_older',
    notes_free: JSON.stringify(['他說「因為你問了」。'])
  };
  const fr = await open('notes.html', V);

  const items = fr.locator('ol.names li');
  ok('六個名字加上空的第七行', (await items.count()) === 7, `畫了 ${await items.count()} 行`);
  ok('第七行是空的', (await items.nth(6).textContent()).includes('（　）'));
  ok('第一個是 @CatGrass_80', (await items.nth(0).locator('.id').textContent()) === '@CatGrass_80');

  await fr.locator('nav button', { hasText: '目擊' }).click();
  const cards = fr.locator('.sight .card');
  ok('只並排已經拿到的那幾份', (await cards.count()) === 4, `畫了 ${await cards.count()} 份`);
  // 0x 那一列是拒答，可是它一樣要並排出來：那一份的內容就是「她不講」。
  const zero = fr.locator('.sight .card', { hasText: '0x' });
  ok('0x 那一列畫得出來，內容是「不回答」',
     (await zero.locator('div').last().textContent()) === '不回答。');
  const all = await fr.locator('main').textContent();
  ok('不加「這些描述不一致」之類的提示', !/不一致|矛盾|不同|注意/.test(all));

  await fr.locator('nav button', { hasText: '問答' }).click();
  const qa = fr.locator('.qa h3');
  ok('問答按人分組', (await qa.count()) === 2, `分了 ${await qa.count()} 組`);

  await fr.locator('nav button', { hasText: '空白頁' }).click();
  ok('讀得回舊的那一則', (await fr.locator('.free .txt').count()) === 1);
  await fr.locator('textarea').fill('那個高個子跟保全講的不像同一個人。');
  await fr.locator('button.act', { hasText: '記下來' }).click();
  await page.waitForTimeout(250);
  const sets = (await msgs()).filter(x => x.type === 'larch:set' && x.name === 'notes_free');
  ok('打字寫回 notes_free', sets.length >= 1);
  const saved = JSON.parse(sets[sets.length - 1].value);
  ok('存的是兩則', saved.length === 2, JSON.stringify(saved).slice(0, 60));

  // 上限
  await fr.locator('textarea').fill('あ'.repeat(260));
  const len = await fr.locator('textarea').inputValue();
  ok('單則卡在 200 字', len.length === 200, `${len.length} 字`);
}

console.log('\n=== sandbox：卡片不可以碰 localStorage ===');
{
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  await open('notes.html', { notes: '', notes_free: '' });
  const bad = await page.frameLocator('#f').locator('main').textContent();
  ok('沒有 same-origin 也照樣畫得出來', bad.length > 0);
  ok('沒有未捕捉的錯誤', errs.length === 0, errs.join(' | ').slice(0, 120));
}

await browser.close();
server.close();
console.log(fails ? `\n★ ${fails} 項沒過\n` : '\n全部通過\n');
process.exit(fails ? 1 : 0);
