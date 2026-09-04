/* 量真實算出來的顏色對比。**不要靠眼睛**，深色主題上 3:1 跟 1.3:1 都「看得到一點」，
   差別要到某些螢幕、某些角度才現形——那正是這顆鈕會被漏掉的原因。
   WCAG：一般文字 4.5:1、大字與 UI 元件邊框 3:1。 */
import http from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';
// playwright 沒裝在這個 repo（見 reference_local_disk_full_and_test_tooling）。
// 用 createRequire 指到別的 repo 那一份，ESM 的 import 不吃 NODE_PATH。
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PW ||
  '/home/ct/line-sticker-studio/node_modules/playwright');
const ROOT='/home/ct/glitch-vn/docs';
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.webmanifest':'application/manifest+json','.webp':'image/webp','.png':'image/png','.woff2':'font/woff2','.mp3':'audio/mpeg','.jpg':'image/jpeg'};
const srv=http.createServer((q,res)=>{const rel=decodeURIComponent(q.url.split('?')[0]).replace(/^\//,'')||'index.html';
 const f=join(ROOT,rel); if(!existsSync(f)||!statSync(f).isFile()){res.writeHead(404);return res.end();}
 const b=readFileSync(f); res.writeHead(200,{'content-type':MIME[extname(f)]||'application/octet-stream','content-length':b.length}); res.end(b);});
await new Promise(r=>srv.listen(0,r));
const b=await chromium.launch(); const p=await b.newPage();
await p.goto(`http://127.0.0.1:${srv.address().port}/`,{waitUntil:'load'});
await p.waitForTimeout(1200);
const r = await p.evaluate(() => {
  const lum = (c) => { const [r,g,b] = c.match(/\d+/g).map(Number).map(v => { v/=255; return v<=.03928 ? v/12.92 : ((v+.055)/1.055)**2.4; });
    return .2126*r + .7152*g + .0722*b; };
  const ratio = (a,bg) => { const [x,y]=[lum(a),lum(bg)].sort((m,n)=>n-m); return (x+.05)/(y+.05); };
  const bg = getComputedStyle(document.body).backgroundColor;
  const out = [];
  for (const [name, sel] of [['下載語音包 按鈕','#dlGo'],['旁邊那行說明','#dlMsg'],['頁尾文字','footer p'],['內文','main p']]) {
    const el = document.querySelector(sel); if (!el) { out.push([name,'找不到']); continue; }
    const cs = getComputedStyle(el);
    out.push([name, ratio(cs.color, bg).toFixed(2), cs.color, sel==='#dlGo' ? ratio(cs.borderTopColor.replace(/[\d.]+\)$/,'1)'), bg).toFixed(2) : '']);
  }
  return { bg, out };
});
console.log('底色', r.bg);
for (const [n, v, c, bd] of r.out)
  console.log(`${(+v>=4.5?'PASS':+v>=3?'WARN':'FAIL')}  ${n.padEnd(14)} ${v}:1  ${c||''} ${bd?'邊框 '+bd+':1':''}`);
await b.close(); srv.close();
const bad = r.out.filter(([, v]) => +v < 4.5);
if (bad.length) { console.log(`\n${bad.length} 項低於 4.5:1`); process.exit(1); }
console.log('\n全部過 4.5:1');
