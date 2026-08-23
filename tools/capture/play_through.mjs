// 把發佈後的 Larch 作品從頭到尾自動玩一次，畫面與聲音一起錄下來。
//
// **Playwright 的 recordVideo 不錄聲音**，這個作品的重點是七百句配音，
// 所以錄影交給 ffmpeg：x11grab 抓 Xvfb 的畫面、pulse 抓一個 null sink 的
// monitor。瀏覽器用 PULSE_SINK 導進那個 sink，不會混到桌面其他聲音。
//
// 翻頁不能用固定秒數：每句配音長度不一樣，等太短會蓋掉尾音、等太長整支
// 拖到兩小時。做法是攔截 new Audio()，語音播完才點下一張。
//
//   node play_through.mjs <發佈網址>
import { chromium } from "playwright";

const URL = process.argv[2];
if (!URL) { console.error("要給發佈網址"); process.exit(1); }
const MAX_CARDS = Number(process.env.MAX_CARDS || 2000);
const GAP = Number(process.env.GAP || 450);          // 語音播完到翻頁之間的呼吸
const IDLE_CAP = Number(process.env.IDLE_CAP || 3500); // 沒有語音的卡片停多久

const browser = await chromium.launch({
  headless: false,
  // **--kiosk 沒有用**，Playwright 自己管視窗會忽略它。分頁列與網址列共 88 px，
  // 改成螢幕開 1280x808、錄完由 ffmpeg 裁掉上面那 88 px（見 record.sh）。
  args: ["--no-sandbox", "--autoplay-policy=no-user-gesture-required",
         "--window-position=0,0", "--window-size=1280,808",
         "--use-gl=angle", "--use-angle=swiftshader"],
});
// viewport 給 null，讓頁面吃滿整個 kiosk 視窗
const ctx = await browser.newContext({ viewport: null });
const page = await ctx.newPage();

// 攔截語音。Larch 用 new Audio() 播 voiceUrl，那些元素不在 DOM 裡，
// querySelector 找不到，只能從建構子攔。
await page.addInitScript(() => {
  window.__voice = { playing: false, last: "", count: 0 };
  const OA = window.Audio;
  window.Audio = function (...a) {
    const el = new OA(...a);
    const src = String(a[0] || "");
    if (/\/voice\/v-/.test(src)) {
      window.__voice.playing = true;
      window.__voice.last = src.split("/").pop();
      window.__voice.count++;
      const done = () => { window.__voice.playing = false; };
      el.addEventListener("ended", done);
      el.addEventListener("error", done);
      el.addEventListener("pause", done);
    }
    return el;
  };
});

await page.goto(URL, { waitUntil: "load" });
await page.waitForTimeout(3000);

// 標題畫面：按「開始遊戲」。**用 Playwright 的真點擊**，不要用 evaluate 裡的
// el.click()——那不是可信任的使用者事件，這個播放器有些按鈕不吃。
await page.getByText("開始遊戲", { exact: false }).first().click({ timeout: 20000 });

// 開始之後還有一個預載畫面（「正在把這一幕要用到的立繪與場景讀進來 87%」）。
// **讓它讀完，不要按「直接開始」。** 按了反而進不去（實測按完三十秒都沒有
// 對話框）。六十個素材讀滿大概兩三分鐘，等就是了。
for (let i = 0; i < 600; i++) {
  const ok = await page.evaluate(() => !!document.querySelector(".vn2-box.click-advance"));
  if (ok) break;
  if (i % 60 === 0) {
    const pc = await page.evaluate(() => {
      const m = document.body.innerText.match(/(\d+)%\s*·\s*(\d+)\s*\/\s*(\d+)/);
      return m ? m[0] : "";
    });
    if (pc) console.log(`  預載 ${pc}`);
  }
  await page.waitForTimeout(500);
}
await page.waitForTimeout(1500);
console.log("READY");                       // 錄影腳本看到這行才開始錄

const state = () => page.evaluate(() => {
  const box = document.querySelector(".vn2-box.click-advance");
  const txt = document.querySelector(".vn2-text")?.innerText || "";
  // **選項的 class 是空的**，class 掛在容器 .vn2-choices 上。
  // 照 class 過濾按鈕會一個都抓不到，然後就一直空點對話框（實測空點了
  // 一千九百多次、錄了一小時的同一張卡）。
  const choices = [...document.querySelectorAll(".vn2-choices button")];
  // miniGame 的片尾自己會跑，跑完 Larch 才往下走，這裡不要亂點
  const mini = !!document.querySelector("iframe");
  return { hasBox: !!box, txt: txt.slice(0, 40), voice: window.__voice,
           choices: choices.length, mini,
           end: /謝謝你看到這裡|返回|回到首頁|THE END/.test(document.body.innerText) };
});

let cards = 0, idle = 0, lastTxt = "", stuck = 0;
for (; cards < MAX_CARDS; ) {
  const s = await state();
  if (s.mini) {                              // 片尾在跑
    // **跑完不會自己往下走。** Larch 收到 larch:complete 之後會顯示
    // 「完成 · complete」加一顆「套用結果並繼續」，要按那顆才會進下一張。
    const done = await page.evaluate(() =>
      [...document.querySelectorAll("button")].some(b => /套用結果並繼續/.test(b.innerText || "")));
    if (done) {
      await page.getByText("套用結果並繼續", { exact: false }).first().click({ timeout: 10000 });
      console.log("  片尾跑完，按了套用結果並繼續");
      await page.waitForTimeout(2500);
      idle = 0;
      continue;
    }
    await page.waitForTimeout(2000);
    idle += 2000;
    if (idle > 300000) { console.log("★ 片尾等太久（五分鐘），停"); break; }
    continue;
  }
  if (s.choices > 0) {                       // 分歧卡：一律選第一個
    await page.evaluate(() => document.querySelector(".vn2-choices button")?.click());
    console.log(`  分歧卡 → 選第一個`);
    await page.waitForTimeout(1200);
    continue;
  }
  if (s.voice?.playing) {                    // 這一句還在唸
    await page.waitForTimeout(250);
    idle = 0;
    continue;
  }
  if (!s.hasBox) {                           // 沒有對話框（過場中）
    await page.waitForTimeout(400);
    idle += 400;
    if (idle > 30000) { console.log("卡住三十秒，停"); break; }
    continue;
  }
  await page.waitForTimeout(GAP);
  await page.evaluate(() => document.querySelector(".vn2-box.click-advance")?.click());
  cards++;
  // **文字沒變就是沒前進。** 沒有這一段的話，遇到點不動的卡片會一路空點到
  // 上限：實測在一張選項卡上點了一千九百多次，錄出一小時的同一個畫面。
  // **「文字是空的」也算沒前進。** 原本寫成 else if (s.txt)，於是故事播完
  // 之後的結束畫面（沒有 .vn2-text）兩個分支都不跑，在那裡空點到上限——
  // 實測多錄了三十三分鐘。
  if (s.txt && s.txt !== lastTxt) { lastTxt = s.txt; stuck = 0; }
  else {
    stuck++;
    if (stuck >= 15) {
      console.log(`★ 卡住了：點了 ${stuck} 次都沒前進「${s.txt}」`);
      console.log("  畫面上有的按鈕：", await page.evaluate(() =>
        [...document.querySelectorAll("button")].map(b =>
          (b.className || "(無 class)") + "|" + b.innerText.replace(/\n/g, "/").slice(0, 20)).slice(0, 8)));
      break;
    }
  }
  if (cards % 25 === 0) console.log(`  第 ${cards} 張　語音 ${s.voice?.count ?? 0} 句　${s.txt}`);
  // 沒有語音的卡片（場景卡）給一點閱讀時間
  const after = await state();
  if (!after.voice?.playing) await page.waitForTimeout(Math.min(IDLE_CAP, 1200));
  idle = 0;
}
const fin = await state();
console.log(`結束：走了 ${cards} 張卡，播了 ${fin.voice?.count ?? 0} 句語音`);
console.log("DONE");
await page.waitForTimeout(4000);
await ctx.close();
await browser.close();
