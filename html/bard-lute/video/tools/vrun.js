const { vcapture } = require('./vcap.js');
const bot = require('./bot.js');
// usage: node vrun.js <run>   (run: idle | sting | green | scar | tempus | pad | game)
const fs = require('fs');
const path = require('path');
const WORK = process.env.WORK || path.join(__dirname, '..', '.work');
const run = process.argv[2];
const P = JSON.parse(fs.readFileSync(path.join(WORK, 'vplan.json')));
const A = P.anchor[run];
const key = k => async p => { await p.keyboard.press(k); };
const SONG = { green: 'greensleeves', scar: 'scarborough', tempus: 'tempus' };
let actions = [];
if (run === 'sting') actions = [{ v: A, fn: key('Digit1') }];
if (SONG[run]) actions = [{ v: .3, fn: p => p.selectOption('#playSong', SONG[run]) }, { v: A, fn: p => p.click('#play') }];
const scrollPad = p => p.evaluate(() => window.scrollTo(0, document.querySelector('.pad').getBoundingClientRect().top + scrollY - 40));
if (run === 'pad') {
  actions.push({ v: .2, fn: scrollPad });
  [['Digit1', 0], ['Digit2', .71], ['Digit3', 1.42], ['Digit1', 2.13]].forEach(([k, d]) => actions.push({ v: A + d + .01, fn: key(k) }));
  ['KeyA', 'KeyS', 'KeyD', 'KeyF', 'KeyG', 'KeyH', 'KeyJ', 'KeyK', 'KeyL', 'Semicolon', 'Quote'].forEach((k, i) => actions.push({ v: A + 3.106 + i * .113, fn: key(k) }));
  const m0 = 3.106 + 11 * .113 + .4;
  ['KeyH', 'KeyK', 'KeyL', 'Semicolon', 'KeyL', 'KeyK', 'KeyJ', 'KeyG'].forEach((k, i) => actions.push({ v: A + m0 + i * .305, fn: key(k) }));
}
if (run === 'game') {
  actions.push({ v: .2, fn: async p => { await p.evaluate(bot, 12345); await p.selectOption('#speed', '0.8'); await p.selectOption('#gameSong', 'greensleeves'); } });
  actions.push({ v: .4, fn: p => p.evaluate(() => window.scrollTo(0, document.querySelector('.pad').getBoundingClientRect().top + scrollY)) });
  actions.push({ v: A, fn: p => p.click('#gameBtn') });
}
const last = P.plan[run].at(-1).v;
if (run === 'game') actions.push({ v: last + .01, fn: async (p, log) => { log.ev = await p.evaluate(() => window.__ev); log.stat = await p.evaluate(() => document.getElementById('gameStat').textContent); } });
vcapture({ file: path.join(WORK, 'bard-cap.html'), out: path.join(WORK, 'frames', run), needs: P.plan[run].map(n => ({ ...n, regionDefs: P.regions })), actions });
