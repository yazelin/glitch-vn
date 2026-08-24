/* 驗 glitch-vn 新加的兩件事:圖自動進離線包、語音下載鈕。
   pwa-check 只驗 SHELL 那 15 個檔,這兩件它看不到。
   **配負控制**:按鈕按之前語音必須是「解不出來」,不然綠燈沒有意義。 */
import http from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';
import { chromium } from 'playwright'   /* 沒裝的話:node --experimental-... 或直接指到別的 repo 的 node_modules/playwright/index.mjs */;

const ROOT = '/home/ct/glitch-vn/docs';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json',
  '.webmanifest': 'application/manifest+json', '.css': 'text/css', '.webp': 'image/webp', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg' };
const srv = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\//, '') || 'index.html';
  let f = join(ROOT, rel);
  if (existsSync(f) && statSync(f).isDirectory()) f = join(f, 'index.html');
  if (!existsSync(f) || !statSync(f).isFile()) { res.writeHead(404); return res.end(); }
  const buf = readFileSync(f);
  // 仿 Pages:每個檔都回 Vary: Accept-Encoding + Range
  const base = { 'content-type': MIME[extname(f)] || 'application/octet-stream', vary: 'Accept-Encoding', 'accept-ranges': 'bytes' };
  const m = req.headers.range && /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
  if (m) {
    const s = Number(m[1] || 0), e = m[2] ? Number(m[2]) : buf.length - 1, sl = buf.slice(s, e + 1);
    res.writeHead(206, { ...base, 'content-range': `bytes ${s}-${e}/${buf.length}`, 'content-length': sl.length });
    return res.end(sl);
  }
  res.writeHead(200, { ...base, 'content-length': buf.length });
  res.end(buf);
});
await new Promise((r) => srv.listen(0, r));
const URL0 = `http://127.0.0.1:${srv.address().port}/`;
const VOICE = JSON.parse(readFileSync(join(ROOT, 'offline.json'), 'utf8')).voice[0];
const IMG = JSON.parse(readFileSync(join(ROOT, 'offline.json'), 'utf8')).img.find((u) => u.endsWith('.webp') || u.endsWith('.png'));

const browser = await chromium.launch();
const ctx = await browser.newContext();
const page = await ctx.newPage();
const out = [];
const say = (ok, name, d) => { out.push(`${ok ? 'PASS' : 'FAIL'}  ${name}  — ${d}`); };

// 用真的 <audio> decode,命中快取不等於播得出來
const decode = (u) => page.evaluate((src) => new Promise((res) => {
  const a = new Audio(src);
  a.addEventListener('loadedmetadata', () => res({ ok: true, dur: a.duration }));
  a.addEventListener('error', () => res({ ok: false }));
  setTimeout(() => res({ ok: false, to: true }), 8000);
}), URL0 + u);

await page.goto(URL0, { waitUntil: 'load' });
await page.waitForFunction(() => navigator.serviceWorker.controller, null, { timeout: 20000 });
await page.waitForTimeout(3000);   // install 裡的圖預快取

await ctx.setOffline(true);
const img = await page.evaluate((u) => caches.match(u, { ignoreSearch: true, ignoreVary: true }).then((r) => !!r), IMG);
say(img, '圖自動進離線包', `${IMG} 斷網時在快取裡`);
const neg = await decode(VOICE);
say(!neg.ok, '負控制:沒按下載時語音該是缺的', neg.ok ? '竟然播得出來,這個測試沒有鑑別力' : '斷網解不出來(預期)');

await ctx.setOffline(false);
await page.click('#dlGo');
await page.waitForFunction(() => document.getElementById('dlGo').textContent === '語音已可離線',
  null, { timeout: 600000 }).catch(() => {});
const msg = await page.textContent('#dlMsg');
const btn = await page.textContent('#dlGo');
say(btn === '語音已可離線', '下載鈕跑完並實查通過', `${btn} / ${msg}`);

await ctx.setOffline(true);
const d = await decode(VOICE);
say(d.ok, '斷網後語音真的能解碼', d.ok ? `${VOICE} ${d.dur.toFixed(1)}s` : '解不出來');
const last = JSON.parse(readFileSync(join(ROOT, 'offline.json'), 'utf8')).voice.slice(-1)[0];
const d2 = await decode(last);
say(d2.ok, '清單最後一個也在(掉檔最常掉尾巴)', d2.ok ? `${last} ${d2.dur.toFixed(1)}s` : '解不出來');

await browser.close(); srv.close();
console.log(out.join('\n'));
console.log(`\n=== PASS ${out.filter((l) => l.startsWith('PASS')).length} / FAIL ${out.filter((l) => l.startsWith('FAIL')).length} ===`);
process.exit(out.some((l) => l.startsWith('FAIL')) ? 1 : 0);
