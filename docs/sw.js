/* 格莉奇與黑洞先生：離線小說站。
   HTML network-first（線上拿最新、離線吃快取），圖與音檔 cache-first。

   兩層快取，因為壽命不一樣：
     SHELL  五個頁面 + manifest + icon，每次部署就換版
     ASSET  立繪、場景、七百多個語音檔，只有同名檔換內容才需要動
   共用一個版本名的話，每次改一行字就把二十幾 MB 的音檔整包刪掉重抓，
   而 cache.put 失敗是靜默的——排最後、檔案最大的音檔最容易掉，
   結果就是「圖都在、按播放沒有聲音」。 */

/* cache:start — tools/update_sw.py 產生，勿手改 */
const SHELL_CACHE = 'gvn-shell-1f26dbc41b';
const ASSET_CACHE = 'gvn-assets-e0cfae77e1';
/* cache:end */

const KEEP = [SHELL_CACHE, ASSET_CACHE];
/* **前綴要跨專案唯一。** CacheStorage 是 per-origin，yazelin.github.io 底下
   所有專案共用同一份（SW 的 scope 只管 fetch，管不到快取）。無差別
   caches.delete 等於每次改版把別站的離線包整包清空，而且毫無徵兆。 */
const PREFIX = 'gvn-';
const MATCH = { ignoreSearch: true, ignoreVary: true };

const SHELL_FILES = [
  './', './index.html', './novel.html', './characters.html',
  './timeline.html', './extras.html', './vn.html', './credits.html',
  './manifest.webmanifest', './offline.json',
  './img/icon-v2-192.png', './img/icon-v2-512.png',
  './img/icon-v2-maskable-512.png', './img/icon-v2-32.png',
  './img/og.jpg',
  './fonts/noto-serif-tc-400.woff2', './fonts/noto-serif-tc-600.woff2',
];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL_CACHE);
    /* addAll 是全有全無：單一檔 404 會讓整次更新失敗，而使用者只會看到
       「沒有更新」。allSettled 讓其他檔照樣進去。 */
    await Promise.allSettled(SHELL_FILES.map((u) => c.add(u)));
    /* 立繪與場景（3.7MB / 34 張）順手補進 ASSET。只補「快取裡沒有的」——
       ASSET_CACHE 沒換名就代表內容沒變，無條件 add 等於每次部署重抓一次。 */
    try {
      const list = await (await fetch('./offline.json')).json();
      const a = await caches.open(ASSET_CACHE);
      await Promise.allSettled(list.img.map(async (u) => {
        if (!(await a.match(u, MATCH))) await a.add(u);
      }));
    } catch (err) { /* 清單抓不到不該擋住整次更新 */ }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys
      .filter((k) => k.startsWith(PREFIX) && !KEEP.includes(k))
      .map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

/* 從快取回應帶 Range 的請求要自己合成 206。回「200 但沒有 Content-Range」
   有些情境會被媒體端拒收，而症狀是「Format error」，看起來像檔案壞掉。 */
async function rangeFrom(res, range) {
  const m = /bytes=(\d*)-(\d*)/.exec(range || '');
  if (!m) return res;
  const buf = await res.arrayBuffer();
  const total = buf.byteLength;
  const start = m[1] ? parseInt(m[1], 10) : 0;
  const end = m[2] ? parseInt(m[2], 10) : total - 1;
  if (start >= total) {
    return new Response(null, { status: 416,
      headers: { 'Content-Range': `bytes */${total}` } });
  }
  const h = new Headers(res.headers);
  h.set('Content-Range', `bytes ${start}-${end}/${total}`);
  h.set('Content-Length', String(end - start + 1));
  h.set('Accept-Ranges', 'bytes');
  return new Response(buf.slice(start, end + 1), { status: 206, headers: h });
}

const isAsset = (p) => /\/(voice|img)\//.test(p)
  || /\.(mp3|webp|png|jpg|jpeg|svg|woff2?)$/i.test(p)
  || p.endsWith('/offline.json');

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  /* 跨域（Google Fonts、Larch、YouTube）不碰：SW 快取跨域回應會拿到
     opaque response，量不出成功與否，而且吃配額。 */
  if (url.origin !== self.location.origin) return;

  const range = req.headers.get('range');

  if (req.mode === 'navigate' || /\.html?$/.test(url.pathname)
      || url.pathname.endsWith('/')) {
    /* HTML network-first。**導覽 fallback 要 ignoreSearch**，
       否則 novel.html?ch=3 這種帶 query 的連結離線時 miss。 */
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        const c = await caches.open(SHELL_CACHE);
        await c.put(req, res.clone()).catch(() => {});
        return res;
      } catch (err) {
        return (await caches.match(req, MATCH))
          || (await caches.match('./index.html', MATCH))
          || Response.error();
      }
    })());
    return;
  }

  if (!isAsset(url.pathname)) return;

  e.respondWith((async () => {
    const hit = await caches.match(req, MATCH);
    if (hit) return range ? rangeFrom(hit.clone(), range) : hit;
    try {
      /* 帶 Range 去抓會拿到 206，那個存進快取之後別人拿到的是半截檔。
         所以另外用不帶 Range 的請求抓完整檔存起來，再切給這一次用。 */
      if (range) {
        const full = await fetch(new Request(url.toString(), { mode: 'cors' }));
        if (full.ok) {
          const c = await caches.open(ASSET_CACHE);
          await c.put(url.toString(), full.clone()).catch(() => {});
          return rangeFrom(full, range);
        }
      }
      const res = await fetch(req);
      if (res.ok) {
        const c = await caches.open(ASSET_CACHE);
        await c.put(req, res.clone()).catch(() => {});
      }
      return res;
    } catch (err) {
      return Response.error();
    }
  })());
});


/* ── 語音離線包（使用者按鈕觸發） ───────────────────────
   730 個檔、24MB。不放 install：那是全有全無的窗口，而 cache.put 失敗是
   靜默的。改成頁面按鈕觸發，做完回頭逐項 cache.match 實查，
   **不准用「fetch 成功次數」宣告完成**——配額不足時 fetch 照回 200。 */
const VOICE = () => fetch('./offline.json').then((r) => r.json()).then((j) => j.voice);

async function have(urls) {
  const c = await caches.open(ASSET_CACHE);
  let n = 0;
  for (const u of urls) if (await c.match(u, MATCH)) n++;
  return n;
}

async function warm(urls, onTick) {
  const c = await caches.open(ASSET_CACHE);
  const q = urls.slice();
  let done = 0;
  /* 併發壓在 6：Pages 被密集平行請求打會回 503，而 503 進不了快取
     也不會拋錯，症狀是「下載完了卻少幾個檔」。失敗的重試一次。 */
  const worker = async () => {
    while (q.length) {
      const u = q.pop();
      if (!(await c.match(u, MATCH))) {
        for (let i = 0; i < 2; i++) {
          try {
            const res = await fetch(u, { cache: 'no-store' });
            if (res.ok) { await c.put(u, res); break; }
          } catch (err) { /* 下一輪重試 */ }
        }
      }
      onTick(++done);
    }
  };
  await Promise.all(Array.from({ length: 6 }, worker));
}

self.addEventListener('message', (e) => {
  const port = e.ports && e.ports[0];
  const reply = (m) => { if (port) port.postMessage(m); };
  if (!e.data || !e.data.type) return;
  e.waitUntil((async () => {
    const urls = await VOICE();
    if (e.data.type === 'status') {
      reply({ have: await have(urls), total: urls.length });
    } else if (e.data.type === 'warm') {
      await warm(urls, (n) => reply({ tick: n, total: urls.length }));
      reply({ have: await have(urls), total: urls.length, done: true });
    }
  })());
});
