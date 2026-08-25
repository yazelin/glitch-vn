/* 《調查篇》那頁交付用 artifact 的驗收。**不是截圖看一眼**：
   實際點下去，確認 srcdoc + sandbox 裡的插件卡真的跑得起來、
   宿主真的收得到 larch:set 與 larch:complete。

   踩過的坑：卡片的 HTML 直接塞進頁面的話，卡片自己的 script 收尾標籤
   會把外面那一段提早關掉，結果是卡片永遠不執行、畫面一片空白、**而且不報錯**。
   改成 base64。**註解裡也不可以出現那個標籤的字面**，HTML 的剖析器不看 JS 註解。

   頁面在 scratchpad，路徑用 SRC 環境變數覆蓋：
     SRC=/path/to/page.html node tools/artifact_test.mjs
*/
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('/home/ct/line-sticker-studio/node_modules/playwright');
const F = 'file://' + (process.env.SRC ||
  '/tmp/claude-1000/-home-ct/5f49dfff-c545-43be-9111-4f1702204826/scratchpad/investigation.html');
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1100, height: 900 } });
const errs = []; p.on('pageerror', e => errs.push(String(e)));
await p.goto(F, { waitUntil: 'load' });
await p.waitForTimeout(1200);
let fail = 0;
const ok = (l, c, d='') => { console.log(`  ${c ? 'ok  ' : '★ FAIL'} ${l}${d ? '  ' + d : ''}`); if (!c) fail++; };

const fr = p.frameLocator('#stage');
ok('srcdoc + sandbox 裡的調查板畫得出來', (await fr.locator('button.spot').count()) > 0,
   `${await fr.locator('button.spot').count()} 個地點`);
ok('灰的那幾格有提示', (await fr.locator('button.spot.locked .who.hint').count()) > 0);
await fr.locator('button.spot:not(.locked)', { hasText: '便利商店' }).click();
await p.waitForTimeout(500);
const log = await p.locator('#log').textContent();
ok('點下去宿主收得到 larch:set', log.includes('larch:set'), log.split('\n')[0]);
ok('也收得到 larch:complete', log.includes('larch:complete'));

await p.click('[data-card="notes"]');
await p.waitForTimeout(900);
const fr2 = p.frameLocator('#stage');
ok('切到筆記卡', (await fr2.locator('ol.names li').count()) === 7,
   `${await fr2.locator('ol.names li').count()} 行`);
await fr2.locator('nav button', { hasText: '目擊' }).click();
ok('目擊那一頁並排', (await fr2.locator('.sight .card').count()) === 5,
   `${await fr2.locator('.sight .card').count()} 份`);

ok('沒有 JS 例外', errs.length === 0, errs.join(' | ').slice(0, 140));
// 圖片真的載得出來（data: URI 沒截斷）
const broken = await p.evaluate(() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length);
ok('九張圖都解得開', broken === 0, `壞 ${broken} 張`);
const wide = await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
ok('頁面不會橫向捲', !wide);
await p.setViewportSize({ width: 390, height: 844 });
await p.waitForTimeout(300);
const wideM = await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
ok('手機寬度也不會橫向捲', !wideM);

await b.close();
console.log(fail ? `\n★ ${fail} 項沒過\n` : '\n全部通過\n');
process.exit(fail ? 1 : 0);
