const { chromium } = require('playwright');
// Renders the compositor frame by frame.
// usage: node render.js frames <from> <to>   |   node render.js stills <t> [<t> ...]
const fs = require('fs');
const path = require('path');
const WORK = process.env.WORK || path.join(__dirname, '..', '.work');
const S = WORK + '/';
const FONTS = ['ZCOOLXiaoWei', 'UncialAntiqua', 'NotoSerifSC-500', 'NotoSerifSC-700', 'NotoSerifSC-900'];
(async () => {
  const mode = process.argv[2];
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.log('err:', e.message));
  p.on('console', m => console.log('console:', m.text()));
  await p.goto('file://' + path.join(__dirname, 'comp.html'));
  await p.addStyleTag({ content: FONTS.map(f => {
    const [fam, w] = { ZCOOLXiaoWei: ['XW', 400], UncialAntiqua: ['Uncial', 400] }[f] || ['NS', +f.split('-')[1]];
    return `@font-face{font-family:${fam};font-weight:${w};src:url(file://${S}fonts/${f}.ttf)}`;
  }).join('\n') });
  await p.evaluate(m => window.init(m), JSON.parse(fs.readFileSync(S + 'manifest.json')));
  if (mode === 'stills') {
    fs.mkdirSync(S + 'stills', { recursive: true });
    for (const t of process.argv.slice(3).map(Number)) {
      await p.evaluate(t => window.render(t), t);
      await p.screenshot({ path: `${S}stills/t${t.toFixed(2)}.jpg`, quality: 80, type: 'jpeg' });
    }
  } else {
    const [a, z] = process.argv.slice(3).map(Number), FPS = 30;
    fs.mkdirSync(S + 'video_frames', { recursive: true });
    for (let i = a; i < z; i++) {
      await p.evaluate(t => window.render(t), i / FPS + 1e-4);
      await p.screenshot({ path: `${S}video_frames/${String(i).padStart(5, '0')}.jpg`, quality: 92, type: 'jpeg' });
    }
  }
  await b.close();
})();
