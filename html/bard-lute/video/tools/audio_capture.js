// Real-time audio capture: plays the page and records what it sends to the speakers
// usage: node audio_capture.js <page.html> <outDir> <song:<id>|pad|game|sting>
const { chromium } = require('playwright');
const fs = require('fs');
const bot = require('./bot.js');

// tap the page's output: the first connection to a destination is mirrored into a MediaRecorder
const AUDIO_HOOK = `
(() => {
  const orig = AudioNode.prototype.connect;
  AudioNode.prototype.connect = function (dest, ...rest) {
    const r = orig.call(this, dest, ...rest);
    if (dest instanceof AudioDestinationNode && !window.__recDest) {
      window.__recDest = dest.context.createMediaStreamDestination();
      orig.call(this, window.__recDest);
      window.__chunks = [];
      window.__rec = new MediaRecorder(window.__recDest.stream, { mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 256000 });
      window.__rec.ondataavailable = e => window.__chunks.push(e.data);
      window.__recStartEpoch = Date.now();
      window.__rec.start(250);
    }
    return r;
  };
})();`;

const RUNS = {
  song: async (p, mark, id) => {
    await p.selectOption('#playSong', id);
    await p.waitForTimeout(300);
    await p.click('#play'); mark('play'); await p.waitForTimeout(14000);
  },
  sting: async (p, mark) => {
    await p.waitForTimeout(500); await p.keyboard.press('Digit1'); mark('strum'); await p.waitForTimeout(4000);
  },
  pad: async (p, mark) => {
    await p.evaluate(() => window.scrollTo(0, document.querySelector('.pad').getBoundingClientRect().top + scrollY - 40));
    await p.waitForTimeout(1500); mark('ready');
    for (const [k, w] of [['Digit1', 700], ['Digit2', 700], ['Digit3', 700], ['Digit1', 900]]) { await p.keyboard.press(k); await p.waitForTimeout(w); }
    mark('keys');
    for (const k of ['KeyA', 'KeyS', 'KeyD', 'KeyF', 'KeyG', 'KeyH', 'KeyJ', 'KeyK', 'KeyL', 'Semicolon', 'Quote']) { await p.keyboard.press(k); await p.waitForTimeout(110); }
    await p.waitForTimeout(400);
    for (const k of ['KeyH', 'KeyK', 'KeyL', 'Semicolon', 'KeyL', 'KeyK', 'KeyJ', 'KeyG']) { await p.keyboard.press(k); await p.waitForTimeout(300); }
    await p.keyboard.press('Digit4'); await p.waitForTimeout(600); await p.keyboard.press('Digit1'); await p.waitForTimeout(1500);
  },
  game: async (p, mark) => {
    await p.evaluate(bot, 12345);
    await p.selectOption('#speed', '0.8');
    await p.selectOption('#gameSong', 'greensleeves');
    await p.evaluate(() => window.scrollTo(0, document.querySelector('.pad').getBoundingClientRect().top + scrollY));
    await p.waitForTimeout(500);
    await p.click('#gameBtn'); mark('gameStart');
    await p.waitForTimeout(34000);
  },
};

(async () => {
  const [file, out, which] = process.argv.slice(2);
  const [kind, arg] = which.split(':');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
  await ctx.addInitScript(AUDIO_HOOK);
  const p = await ctx.newPage();
  p.on('pageerror', e => console.log('err:', e.message));
  await p.goto('file://' + file);
  await p.waitForTimeout(700);
  const marks = {};
  const mark = k => { marks[k] = Date.now() / 1000; };
  mark('start');
  await RUNS[kind](p, mark, arg);
  const audio = await p.evaluate(async () => {
    await new Promise(r => { window.__rec.onstop = r; window.__rec.stop(); });
    const buf = new Uint8Array(await new Blob(window.__chunks, { type: 'audio/webm' }).arrayBuffer());
    let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return { b64: btoa(s), startEpoch: window.__recStartEpoch / 1000 };
  });
  fs.writeFileSync(out + '/audio.webm', Buffer.from(audio.b64, 'base64'));
  fs.writeFileSync(out + '/meta.json', JSON.stringify({ marks, audioStart: audio.startEpoch }, null, 1));
  console.log(out, 'audio ok');
  await b.close();
})();
