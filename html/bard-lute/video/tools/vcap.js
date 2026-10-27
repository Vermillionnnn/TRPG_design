// deterministic capture: step virtual time, perform actions, screenshot named regions at requested times
const { chromium } = require('playwright');
const fs = require('fs');
const VCLOCK = require('./vclock.js');
async function vcapture({ file, out, needs, actions, dsf = 5 }) {
  // needs: [{v, regions:[name]}], regions: {name:{x,y,w,h,sc}} (viewport css px)
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: dsf });
  await ctx.addInitScript(VCLOCK);
  const p = await ctx.newPage();
  p.on('pageerror', e => console.log('err:', e.message));
  p.on('console', m => { if (m.type() === 'error') console.log('console:', m.text()); });
  await p.goto('file://' + file);
  await p.waitForTimeout(400);
  const cdp = await ctx.newCDPSession(p);
  const step = ms => cdp.send('Runtime.evaluate', { expression: `__step(${ms})` });
  let V = 0; const DT = 1000 / 60;
  const acts = actions.slice().sort((a, b) => a.v - b.v);
  const nd = needs.slice().sort((a, b) => a.v - b.v);
  const end = Math.max(...nd.map(n => n.v), ...acts.map(a => a.v)) * 1000 + 1;
  let ai = 0, ni = 0;
  const log = {};
  fs.mkdirSync(out, { recursive: true });
  const t0 = Date.now(); let shots = 0;
  while (V < end) {
    const nextA = ai < acts.length ? acts[ai].v * 1000 : Infinity, nextN = ni < nd.length ? nd[ni].v * 1000 : Infinity;
    const target = Math.min(V + DT, nextA, nextN);
    if (target > V) { await step(target - V); V = target; }
    while (ai < acts.length && acts[ai].v * 1000 <= V + 1e-6) { await acts[ai].fn(p, log, V / 1000); ai++; }
    while (ni < nd.length && nd[ni].v * 1000 <= V + 1e-6) {
      const n = nd[ni++];
      const [sx, sy] = (await cdp.send('Runtime.evaluate', { expression: '__sync()', returnByValue: true })).result.value;
      for (const rn of n.regions) {
        const r = n.regionDefs[rn];
        const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 93, clip: { x: r.x + sx, y: r.y + sy, width: r.w, height: r.h, scale: r.sc } });
        fs.mkdirSync(`${out}/${rn}`, { recursive: true });
        fs.writeFileSync(`${out}/${rn}/${n.v.toFixed(4)}.jpg`, Buffer.from(shot.data, 'base64')); shots++;
      }
    }
  }
  fs.writeFileSync(out + '/log.json', JSON.stringify(log));
  console.log(out, 'shots', shots, 'in', ((Date.now() - t0) / 1000).toFixed(1) + 's');
  await b.close();
}
module.exports = { vcapture };
