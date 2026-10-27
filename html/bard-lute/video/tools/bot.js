module.exports = (seed) => {
  // plays the falling melody: mostly perfect, a few "good"; logs judgements with epoch time
  window.__ev = [];
  let rnd = seed; const R = () => (rnd = (rnd * 16807) % 2147483647) / 2147483647;
  const piano = document.getElementById('piano');
  let lastCombo = 0, lastMiss = 0;
  const loop = () => {
    const G = window.__G, c = window.__ctx(); if (!c) { requestAnimationFrame(loop); return; } const now = c.currentTime;
    if (G.on) {
      for (const n of G.notes) {
        if (n.time > now + .3) break;
        if (n.state || n.botAt !== undefined && n.pressed) continue;
        if (n.botAt === undefined) { const r = R(); n.botAt = r < .12 ? .13 + R() * .05 : (R() - .5) * .06; }
        if (now >= n.time + n.botAt) {
          n.pressed = true;
          const b = piano.children[n.m - 48];
          b.dispatchEvent(new PointerEvent('pointerdown', { button: 0, bubbles: true, cancelable: true }));
        }
      }
      if (G.combo !== lastCombo || G.miss !== lastMiss) { window.__ev.push({ t: performance.now() / 1000, combo: G.combo, fb: G.fb, p: G.perfect, g: G.good, m: G.miss }); lastCombo = G.combo; lastMiss = G.miss; }
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
};
