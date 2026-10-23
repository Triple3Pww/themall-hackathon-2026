// Plays the rush-hour scenario in nocap-3d.html on the GPU (headless) and saves every frame with its timestamp,
// plus the moment each step ends. Feed the output to cut-clips.py.
// usage: node record-steps.js <path to playwright package> [out dir, default ./rec]
const { chromium } = require(process.argv[2]);
const fs = require('fs'), path = require('path');
const OUT = path.resolve(process.argv[3] || 'rec'), FR = path.join(OUT, 'frames');
const PAGE = require('url').pathToFileURL(path.resolve(__dirname, '..', 'nocap-3d.html')).href;
(async () => {
  const W = 1920, H = 1080;
  fs.rmSync(FR, { recursive: true, force: true }); fs.mkdirSync(FR, { recursive: true });
  // headless + ANGLE/D3D11 renders on the real GPU (~60 fps); a headed window gets cropped by the screen size
  const b = await chromium.launch({ headless: true, args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(PAGE);
  await p.addStyleTag({ content: '#bar,#stBtns{display:none!important}#story{bottom:28px!important}' });  // video look: no buttons
  await p.waitForTimeout(3000);
  const cdp = await p.context().newCDPSession(p);
  const frames = []; let n = 0;
  cdp.on('Page.screencastFrame', f => {
    const file = path.join(FR, String(n++).padStart(6, '0') + '.jpg');
    fs.writeFileSync(file, Buffer.from(f.data, 'base64'));
    frames.push({ file, t: f.metadata.timestamp });
    cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {});
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: W, maxHeight: H, everyNthFrame: 1 });
  const now = () => Date.now() / 1000;
  await p.waitForTimeout(500);
  const marks = [{ name: 'start', t: now() }];
  await p.evaluate(() => document.getElementById('bRush').click());
  for (let i = 0; i < 14; i++) {
    await p.waitForFunction(() => !document.getElementById('stNext').disabled, null, { timeout: 180000 });
    const k = await p.textContent('#stK');
    // hold on each step's result; the CCTV step waits for its replay to finish
    if (k.includes('วิธีนับ 1/4')) { await p.waitForFunction(() => document.body.dataset.replay === 'done', null, { timeout: 60000 }); await p.waitForTimeout(2000); }
    else await p.waitForTimeout(k.includes('วิธีนับ') ? 4000 : 3000);
    marks.push({ name: k, t: now() });
    if (k.includes('ผลลัพธ์')) break;
    await p.evaluate(() => document.getElementById('stNext').click());
  }
  await cdp.send('Page.stopScreencast');
  await p.waitForTimeout(300);
  fs.writeFileSync(path.join(OUT, 'rec.json'), JSON.stringify({ frames, marks }));
  console.log('frames', frames.length, 'steps', marks.length - 1, 'errors', errs);
  await b.close();
})();
