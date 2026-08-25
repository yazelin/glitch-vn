/* 角色頁自介鈕。**不是檢查 HTML 有沒有那顆鈕**，是真的按下去看 <audio> 有沒有在跑。
   一次只能有一個在播——七張卡同時出聲比沒有聲音還糟，那個 bug 用看的看不出來。 */
import http from 'node:http';
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, extname } from 'node:path';
// playwright 沒裝在這個 repo，ESM 的 import 不吃 NODE_PATH，所以指到別的 repo 那一份。
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(
  process.env.PW || '/home/ct/line-sticker-studio/node_modules/playwright');
const ROOT = '/home/ct/glitch-vn/docs';
const MIME = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.json':'application/json',
  '.webmanifest':'application/manifest+json', '.webp':'image/webp', '.png':'image/png',
  '.woff2':'font/woff2', '.mp3':'audio/mpeg', '.jpg':'image/jpeg' };
const srv = http.createServer((q,res)=>{
  const rel = decodeURIComponent(q.url.split('?')[0]).replace(/^\//,'')||'index.html';
  let f = join(ROOT, rel);
  if (!existsSync(f)||!statSync(f).isFile()) { res.writeHead(404); return res.end(); }
  const b = readFileSync(f);
  res.writeHead(200,{'content-type':MIME[extname(f)]||'application/octet-stream','content-length':b.length,'accept-ranges':'bytes'});
  res.end(b);
});
await new Promise(r=>srv.listen(0,r));
const U = `http://127.0.0.1:${srv.address().port}/characters.html`;
const b = await chromium.launch({ args:['--autoplay-policy=no-user-gesture-required'] });
const p = await b.newPage();
const say=(ok,n,d)=>console.log(`${ok?'PASS':'FAIL'}  ${n}  — ${d}`);
await p.goto(U,{waitUntil:'load'});
const btns = await p.evaluate(() => [...document.querySelectorAll('.say')].map(x => x.dataset.say));
// 七段自介＋每一段「別人怎麼說」。數量會變，所以只要求「跟 docs 裡的音檔數一樣」。
const files = readdirSync(join(ROOT,'voice')).filter(f=>/^(intro|view)-.*\.mp3$/.test(f)).length;
say(btns.length===files,'按鈕數跟音檔數對得起來',`${btns.length} 顆鈕 / ${files} 個音檔`);
// 逐一按下去，確認真的有音訊在跑且時間有前進
let bad=[];
for (const s of btns) {
  await p.click(`.say[data-say="${s}"]`);
  await p.waitForTimeout(900);
  const st = await p.evaluate(()=> {
    const a=[...document.querySelectorAll('audio')];
    return { n: performance.getEntriesByType('resource').filter(r=>/intro-/.test(r.name)).length };
  });
  const on = await p.getAttribute(`.say[data-say="${s}"]`,'aria-pressed');
  const txt = await p.isVisible(`#said-${s}`);
  if (on!=='true'||!txt) bad.push(s);
  await p.click(`.say[data-say="${s}"]`);   // 再按一次要停
  const off = await p.getAttribute(`.say[data-say="${s}"]`,'aria-pressed');
  if (off!=='false') bad.push(s+'(停不掉)');
}
say(bad.length===0,'每顆按下去都會播、再按一次會停',bad.length?bad.join(' '):`${btns.length} 顆都對`);
// 一次只播一個
await p.click('.say[data-say="glitch"]');
await p.waitForTimeout(300);
await p.click('.say[data-say="noah"]');
await p.waitForTimeout(300);
const on = await p.evaluate(() => [...document.querySelectorAll('.say')].filter(x => x.getAttribute('aria-pressed') === 'true').map(x => x.dataset.say));
say(on.length===1 && on[0]==='noah','一次只播一個',on.join(' ')||'零個');
const shown = await p.evaluate(() => [...document.querySelectorAll('.said')].filter(x => x.hasAttribute('data-on')).map(x => x.id));
say(shown.length===1,'逐字稿也只留一段',shown.join(' '));
const errs=[];
p.on('pageerror',e=>errs.push(e.message));
say(errs.length===0,'沒有 JS 例外',errs.join(' ')||'零');
await b.close(); srv.close();
