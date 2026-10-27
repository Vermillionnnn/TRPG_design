// virtual clock: page time only advances when __step is called
module.exports = `(() => {
  let V = 0;
  const rafQ = new Map(); let rafId = 0;
  const timers = new Map(); let tid = 0;
  performance.now = () => V;
  const base = Date.now(); Date.now = () => base + V;
  window.requestAnimationFrame = cb => { const id = ++rafId; rafQ.set(id, cb); return id; };
  window.cancelAnimationFrame = id => rafQ.delete(id);
  window.setTimeout = (cb, ms, ...a) => { const id = ++tid; timers.set(id, { at: V + Math.max(0, +ms || 0), cb, a }); return id; };
  window.setInterval = (cb, ms, ...a) => { const id = ++tid; timers.set(id, { at: V + Math.max(1, +ms || 0), cb, a, every: Math.max(1, +ms || 0) }); return id; };
  window.clearTimeout = window.clearInterval = id => timers.delete(id);
  const v0s = new WeakMap();
  Object.defineProperty(BaseAudioContext.prototype, 'currentTime', { configurable: true, get() { if (!v0s.has(this)) v0s.set(this, V); return (V - v0s.get(this)) / 1000; } });
  window.__step = ms => {
    const target = V + ms;
    for (;;) {
      let nx = null;
      for (const e of timers) if (e[1].at <= target && (!nx || e[1].at < nx[1].at)) nx = e;
      if (!nx) break;
      const [id, t] = nx; V = Math.max(V, t.at);
      if (t.every) t.at += t.every; else timers.delete(id);
      try { typeof t.cb === 'function' ? t.cb(...t.a) : (0, eval)(t.cb); } catch (e) { console.error(e && e.message); }
    }
    V = target;
    const q = [...rafQ.values()]; rafQ.clear();
    q.forEach(cb => { try { cb(V); } catch (e) { console.error(e && e.message); } });
  };
  window.__sync = () => {
    for (const a of document.getAnimations()) {
      if (a.__v0 === undefined) { a.__v0 = V - (a.currentTime || 0); a.pause(); }
      a.currentTime = V - a.__v0;
    }
    return [scrollX, scrollY];
  };
  window.__V = () => V;
})();`;
