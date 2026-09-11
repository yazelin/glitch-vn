// 正篇自動玩家：從標題一路點下去，記下十四張 CG 各在哪一步解開。
// 正篇是線性的（七章＋謝幕），所以比調查篇那支簡單：點對話框前進、選項挑第一個。
// 要驗的是「十四張 setVariable 卡都點得過去，沒有一張卡住」。
//
// 用法：OUT=/tmp node tools/autoplay_main.mjs <playUrl> <projectId> [stopAfter]
//   playUrl   GET /api/agent/projects/:id/preview 拿的（私人連結，不要進 repo）
//   stopAfter 14＝解到第十四張就收工（第十四張在第七章，謝幕那一塊沒有 CG）
//
// **片尾字卷那張是 miniGame 卡，點對話框過不去**：畫面上有「略過小遊戲」，
// 播完會換成「套用結果並繼續」，要按那顆按鈕。這支的卡住處理只認得「跳過」，
// 2026-09-11 已經把「略過」「套用」加進 WANT，現在走得到底。那張卡本身是好的（單獨玩過一次
// 會走到「故事暫告一段落」）。要驗到底就把那兩個字樣加進 WANT。
//
// 調查篇那條線是 tools/autoplay.mjs，那支要照板上的便條決定去哪；正篇是線性的，
// 只要點得過去就好。
import { createRequire } from 'node:module';
const require_ = createRequire(import.meta.url);
const { chromium } = require_('/home/ct/line-sticker-studio/node_modules/playwright');
import fs from 'node:fs';

const URL = process.argv[2];
const PROJ = process.argv[3];
const STOP = Number(process.argv[4] || 0);      // 0＝走到底
const OUT = (process.env.OUT || '/tmp') + '/';
const LOG = [];
const out = (s) => { LOG.push(s); console.log(s); };
const flush = () => fs.writeFileSync(OUT + 'playthrough.txt', LOG.join('\n'));

const browser = await chromium.launch({ args: ['--disable-gpu', '--disable-dev-shm-usage',
  '--no-sandbox', '--mute-audio'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
ctx.setDefaultTimeout(15000);                    // 什麼都不准無限等（上一輪卡在片尾字卷）
const page = await ctx.newPage();
page.on('pageerror', e => out(`PAGE ERR: ${String(e).slice(0, 120)}`));

const guard = (pr, dflt) => Promise.race([
  pr.catch(() => dflt),
  new Promise(r => setTimeout(() => r(dflt), 20000)),
]);
const text = async () => (await guard(page.locator('body').innerText(), ''))
  .replace(/\s+/g, ' ').replace(/存檔 讀取 歷史 自動 快轉 全屏 標題 設定/, '')
  .replace(/點擊對話框繼續/, '').trim();
const frames = () => page.frames().filter(f => f !== page.mainFrame());
const cg = async () => {
  try {
    const raw = await guard(page.evaluate(k => localStorage.getItem('larch-cg-' + k), PROJ), '{}');
    return Object.keys(JSON.parse(raw || '{}'));
  } catch (e) { return []; }
};

// 負控制：另開一個分頁看標題畫面的畫廊，不影響正在玩的那一頁
// （localStorage 同源共用，所以看得到目前解到哪）。
const peekGallery = async (tag, file) => {
  const p2 = await ctx.newPage();
  try {
    await p2.goto(URL, { waitUntil: 'load', timeout: 120000 });
    await p2.waitForTimeout(4000);
    await p2.locator('button', { hasText: /CG 收藏/ }).first().click();
    await p2.waitForTimeout(2000);
    await p2.screenshot({ path: OUT + file });
    const t = (await p2.locator('body').innerText()).replace(/\n+/g, ' | ');
    out(`  [畫廊 ${tag}] ${t.slice(0, 620)}`);
    const imgs = await p2.$$eval('img', xs => xs.map(x => x.src)
      .filter(s => /\/17\d{11}_/.test(s)).map(s => s.split('_').pop()));
    out(`  [畫廊 ${tag}] 真的畫出來的圖 ${imgs.length} 張：${JSON.stringify(imgs)}`);
    // 語言切換：清掉 ja-JP 之後標題與設定裡都不該再有
    const lang = await p2.evaluate(() => document.body.innerText)
      .then(s => /日語|日本語|ja-JP|語言|Language/.test(s));
    out(`  [畫廊 ${tag}] 畫面上有語言字樣：${lang}`);
  } catch (e) { out(`  [畫廊 ${tag}] 出錯 ${String(e).slice(0, 120)}`); }
  await p2.close();
};

await page.goto(URL, { waitUntil: 'load', timeout: 120000 });
await page.waitForTimeout(4000);
const btns = await page.$$eval('button', bs => bs.map(x => x.textContent.trim()).filter(Boolean));
out(`標題按鈕：${JSON.stringify(btns)}`);
out(`標題上有語言選單：${btns.some(b => /語言|Language|日語|日本語/.test(b))}`);
out(`[開場] 解鎖 ${JSON.stringify(await cg())}`);
await peekGallery('開場', 'cg-00-gallery-before.png');
await page.locator('button', { hasText: /開始遊戲/ }).first().click();
await page.waitForTimeout(3000);

let last = '', stuck = 0, cards = 0, peeked = false;
const have = new Set(await cg());
const t0 = Date.now();
for (let step = 0; step < 6000 && Date.now() - t0 < 40 * 60 * 1000; step++) {
  const t = await text();
  if (/開始遊戲/.test(t) && /繼續遊戲/.test(t)) { out(`\n=== 回到標題（走完了），共 ${cards} 張卡`); break; }

  // 選項卡：標籤長成「01問他…」，元件在 shadow DOM 裡，只有 locator 穿得過。
  const opts = [];
  for (const b of await guard(page.getByRole('button').filter({ hasText: /^\s*0[1-9]/ }).all(), [])) {
    const s = ((await guard(b.textContent(), '')) || '').replace(/[\s 　]+/g, ' ').trim();
    if (s.length < 3 || s.length > 40) continue;
    const box = await b.boundingBox().catch(() => null);
    if (!box || box.height > 90) continue;
    if (!opts.some(o => o.s === s)) opts.push({ b, s });
  }
  if (opts.length) {
    out(`  [選項] ${opts.map(o => o.s).join(' | ')} → 選 ${opts[0].s}`);
    await opts[0].b.click({ timeout: 4000 }).catch(() => {});
    await page.waitForTimeout(900);
    stuck = 0; continue;
  }

  if (t && t !== last) {
    cards++; last = t; stuck = 0;
    if (/記住這個畫面/.test(t)) out(`  ★ 第 ${cards} 張　CG 卡：${t.slice(0, 58)}`);
    else if (cards % 60 === 0) out(`  第 ${cards} 張：${t.slice(0, 58)}`);
    for (const k of await cg()) if (!have.has(k)) {
      have.add(k);
      out(`  ＋解鎖第 ${have.size} 張（第 ${cards} 張卡）：${String(k).split('_').pop()}`);
      if (have.size === 7 && !peeked) { peeked = true; await peekGallery('走到一半', 'cg-mid-gallery.png'); }
      if (STOP && have.size >= STOP) { out(`\n=== 解到第 ${STOP} 張，收工（共 ${cards} 張卡）`); step = 1e9; }
    }
  } else {
    stuck++;
    if (stuck % 9 === 8) {
      const NAV = ['存檔', '讀取', '歷史', '自動', '快轉', '全屏', '標題', '設定', '背包', '關閉'];
      // 「略過小遊戲」「套用結果並繼續」是片尾字卷那張 miniGame 卡的按鈕（2026-09-11 補）
      const WANT = /確定|好的|繼續|知道了|完成|跳過|略過|套用|回去|離開|返回/;
      let hit = false;
      for (const scope of [page, ...frames()]) {
        for (const b of await guard(scope.getByRole('button').all(), [])) {
          const lb = ((await guard(b.textContent(), '')) || '').replace(/\s+/g, '').trim();
          if (!lb || NAV.includes(lb) || /^\d+$/.test(lb) || lb.length > 12) continue;
          if (stuck < 26 && !WANT.test(lb)) continue;
          out(`  [卡住] 試著點「${lb}」`);
          await b.click({ timeout: 2500 }).catch(() => {});
          hit = true; break;
        }
        if (hit) break;
      }
      if (!hit) await page.keyboard.press('Escape').catch(() => {});
    }
    if (stuck > 40) {
      out(`★ 卡住 40 下沒變（第 ${cards} 張）：${t.slice(0, 160)}`);
      await page.screenshot({ path: OUT + 'stuck.png' }).catch(() => {});
      break;
    }
  }
  await page.mouse.click(640, 640).catch(() => {});
  await page.waitForTimeout(380);
  if (step % 100 === 0) flush();
}

const end = await cg();
out(`\n[走完] 解鎖 ${end.length} 張`);
for (const k of end) out(`   ${String(k).split('_').pop()}`);
await peekGallery('走完之後', 'cg-end-gallery.png');
flush();
await page.screenshot({ path: OUT + 'playthrough-end.png' }).catch(() => {});
await browser.close();
