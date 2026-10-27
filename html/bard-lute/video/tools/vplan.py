# plans the deterministic re-capture: which run, virtual time and region each output frame needs
# writes $WORK/vplan.json
import json, os
WORK = os.environ.get('WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
FPS, N = 30, 1290
ANCHOR = dict(idle=0.0, sting=1.0, green=1.0, scar=1.0, tempus=1.0, pad=1.5, game=1.0)
TRACKS = {  # name: (run, out, offset from the run's anchor)
  'idle': ('idle', 0.0, 0.3), 'idle2': ('idle', 38.0, 0.6), 'sting': ('sting', 3.22, -0.02),
  'green': ('green', 6.3, 0.1), 'scar': ('scar', 15.2, 0.15), 'tempus': ('tempus', 17.9, 0.15),
  'pad': ('pad', 21.0, -0.15), 'game': ('game', 26.85, 17.85),
}
REG = {
  'fireZ': dict(x=500, y=370, w=624, h=351, sc=3.84), 'full': dict(x=156, y=17, w=968, h=774, sc=2.2),
  'artA': dict(x=350, y=75, w=480, h=270, sc=4.8), 'artB': dict(x=225, y=250, w=660, h=380, sc=3.43),
  'artC': dict(x=90, y=20, w=620, h=355, sc=4.09), 'artD': dict(x=240, y=345, w=800, h=455, sc=2.79),
  'pad': dict(x=140, y=395, w=1135, h=500, sc=1.6), 'game': dict(x=150, y=455, w=1125, h=445, sc=1.6),
  'gameZ': dict(x=720, y=557, w=560, h=222, sc=3.2),
}
def uses(t):
    u = []
    if t < 3.2: u.append(('idle', 'fireZ'))
    elif t < 6.6:
        u.append(('sting', 'full'))
        if t < 3.8: u.append(('sting', 'fireZ'))
    elif t < 13.0:
        u.append(('green', 'artA' if t < 8.2 else 'artB' if t < 9.8 else 'artC' if t < 11.4 else 'artD'))
    elif t < 21.0:
        if t < 15.85: u.append(('green', 'full'))
        if 15.45 <= t < 18.55: u.append(('scar', 'full'))
        if t >= 18.15: u.append(('tempus', 'full'))
    elif t < 27.0: u.append(('pad', 'pad'))
    elif t < 38.0:
        u.append(('game', 'game'))
        if 30.5 <= t < 33.75: u.append(('game', 'gameZ'))
    else: u.append(('idle2', 'full'))
    return u
needs = {}
for k in range(N):
    t = k / FPS
    for tr, rn in uses(t):
        run, out, off = TRACKS[tr]
        v = round(ANCHOR[run] + off + (t - out), 4)
        needs.setdefault(run, {}).setdefault(v, set()).add(rn)
plan = {run: [dict(v=v, regions=sorted(r)) for v, r in sorted(d.items())] for run, d in needs.items()}
json.dump(dict(plan=plan, regions=REG, anchor=ANCHOR,
               tracks={k: dict(clip=r, out=o, t0=ANCHOR[r] + off) for k, (r, o, off) in TRACKS.items()}),
          open(os.path.join(WORK, 'vplan.json'), 'w'))
print({r: len(p) for r, p in plan.items()})
