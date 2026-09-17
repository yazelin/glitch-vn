// 驗證 Larch CG 收藏跨周目條件：解鎖、重開後略過、查詢、鎖回。
import { createRequire } from 'node:module';
const require_ = createRequire(import.meta.url);
const { chromium } = require_('/home/ct/line-sticker-studio/node_modules/playwright');

const URL = process.argv[2];
const PROJECT = process.argv[3];
if (!URL || !PROJECT) throw new Error('用法：node tools/test_cg_crossrun.mjs <previewUrl> <projectId>');

const browser = await chromium.launch({
  executablePath: '/snap/bin/chromium',
  args: ['--no-sandbox', '--disable-gpu', '--mute-audio'],
});
const context = await browser.newContext({viewport: {width: 1280, height: 720}});
const page = await context.newPage();
page.setDefaultTimeout(20000);
await page.addInitScript(() => {
  const original = Storage.prototype.setItem;
  window.__cgWrites = [];
  Storage.prototype.setItem = function(key, value) {
    if (String(key).startsWith('larch-cg-')) window.__cgWrites.push([key, value]);
    return original.call(this, key, value);
  };
});

const body = async () => (await page.locator('body').innerText()).replace(/\s+/g, ' ').trim();
const cgState = async () => JSON.parse(await page.evaluate(
  key => localStorage.getItem(`larch-cg-${key}`) || '{}', PROJECT));
const clickText = async text => {
  const button = page.getByRole('button').filter({hasText: text}).first();
  await button.waitFor({state: 'visible'});
  await button.click();
  await page.waitForTimeout(350);
  // 對話仍在逐字顯示時，第一次點擊只會補完文字；按鈕若還在就再點一次。
  if (await button.isVisible().catch(() => false)) {
    await button.click();
  }
  await page.waitForTimeout(700);
};
const advance = async () => {
  await page.waitForTimeout(2600);
  await page.mouse.click(640, 640);
  await page.waitForTimeout(900);
};
const openFresh = async () => {
  await page.goto(URL, {waitUntil: 'load', timeout: 120000});
  await page.waitForTimeout(2500);
  await clickText('開始遊戲');
  await page.waitForTimeout(1200);
};
const expectText = async (needle, label) => {
  let text = '';
  for (let attempt = 0; attempt < 12; attempt += 1) {
    text = await body();
    if (text.includes(needle)) break;
    await page.waitForTimeout(350);
  }
  if (!text.includes(needle)) throw new Error(`${label}：找不到「${needle}」\n${text.slice(0, 800)}`);
  console.log(`PASS ${label}: ${needle}`);
};
const resetWrites = async () => page.evaluate(() => { window.__cgWrites = []; });
const writes = async () => page.evaluate(() => window.__cgWrites || []);

// 從完全沒拿過 CG 的瀏覽器開始。
await page.goto(URL, {waitUntil: 'load', timeout: 120000});
await page.evaluate(key => localStorage.removeItem(`larch-cg-${key}`), PROJECT);

// 1. 尚未解鎖：應走 unlock 卡，並寫入跨周目 localStorage。
await openFresh();
await clickText('解鎖流程');
await resetWrites();
await advance();
let state = await cgState();
if (Object.keys(state).length !== 1) throw new Error(`解鎖後收藏數不是 1：${JSON.stringify(state)}`);
if ((await writes()).length < 1) throw new Error('unlock 沒有寫入 CG localStorage');
await expectText('第一次取得：現在播放並解鎖這張 CG', '首次看變量走未解鎖分支');
console.log('PASS unlock 寫入跨周目收藏:', JSON.stringify(state));

// 2. 重載相當於回標題重新開始；一般流程狀態重建，但 CG localStorage 保留。
await openFresh();
await clickText('解鎖流程');
await resetWrites();
await advance();
state = await cgState();
if (Object.keys(state).length !== 1) throw new Error('第二輪 CG 收藏狀態遺失');
if ((await writes()).length !== 0) throw new Error('已解鎖略過分支仍然重寫了 CG 收藏');
await expectText('沒有再次解鎖，也沒有再次播放', '重開後看變量走已解鎖略過分支');
console.log('PASS 已解鎖時略過：沒有再次執行 unlock，也不播 CG');

// 3. 直接查詢特殊 CG 條件，應得到已解鎖。
await openFresh();
await clickText('查詢目前 CG 狀態');
await advance();
await expectText('讀到：已解鎖', '查詢功能直接讀到已解鎖');

// 4. 鎖回後 localStorage 必須清掉。
await openFresh();
await resetWrites();
await clickText('鎖回測試 CG');
state = await cgState();
if (Object.keys(state).length !== 0) throw new Error(`鎖回後仍有收藏：${JSON.stringify(state)}`);
if ((await writes()).length < 1) throw new Error('lock 沒有更新 CG localStorage');
console.log('PASS lock 移除跨周目收藏');

// 5. 再開一次查詢，應得到尚未解鎖。
await openFresh();
await clickText('查詢目前 CG 狀態');
await advance();
await expectText('讀到：尚未解鎖', '鎖回後查詢讀到尚未解鎖');

await page.screenshot({path: '/tmp/larch-cg-crossrun-final.png'});
await browser.close();
console.log('ALL PASS');
