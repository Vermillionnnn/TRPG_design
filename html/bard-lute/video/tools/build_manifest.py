# collects the captured frames into $WORK/manifest.json for the compositor
import json, os
WORK = os.environ.get('WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
P = json.load(open(os.path.join(WORK, 'vplan.json')))
runs = {}
for run in P['plan']:
    regs = {}
    base = os.path.join(WORK, 'frames', run)
    for rn in os.listdir(base):
        d = os.path.join(base, rn)
        if not os.path.isdir(d): continue
        regs[rn] = dict(P['regions'][rn], frames=sorted(float(f[:-4]) for f in os.listdir(d)), dir=d + '/')
    runs[run] = dict(regions=regs, anchor=P['anchor'][run])
log = json.load(open(os.path.join(WORK, 'frames', 'game', 'log.json')))
events = [dict(t=e['t'], combo=e['combo'], fb=e['fb']) for e in log['ev']]
json.dump(dict(dur=43.0, tracks=P['tracks'], runs=runs, events=events), open(os.path.join(WORK, 'manifest.json'), 'w'))
print('manifest:', {r: sum(len(g['frames']) for g in v['regions'].values()) for r, v in runs.items()})
