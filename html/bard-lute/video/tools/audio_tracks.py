# where each recorded clip lands in the 43 s mix (times in seconds)
import json, os
WORK = os.environ.get('WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
DUR = 43.0
def meta(c):
    m = json.load(open(os.path.join(WORK, 'audio', c, 'meta.json')))
    return m, m['marks']['start']
def mk(c, mark, off):
    m, st = meta(c)
    return m['marks'][mark] - st + off
# clip: audio capture; out: start in the video; t0: clip time (s after its 'start' mark) at `out`
def tracks():
    return {
      'sting':  dict(clip='sting',       out=3.22,  t0=mk('sting', 'strum', -0.02),          dur=3.6,   fi=.005, fo=1.4),
      'green':  dict(clip='green',       out=6.3,   t0=mk('green', 'play', 0.1),             dur=9.5,   fi=.5,   fo=.7),
      'scar':   dict(clip='scar',        out=15.2,  t0=mk('scar', 'play', 0.15),             dur=3.4,   fi=.45,  fo=.7),
      'tempus': dict(clip='tempus',      out=17.9,  t0=mk('tempus', 'play', 0.15),           dur=3.6,   fi=.45,  fo=.6),
      'pad':    dict(clip='pad',         out=21.0,  t0=mk('pad', 'ready', -0.15),            dur=6.3,   fi=.12,  fo=.5),
      'game':   dict(clip='game',        out=26.85, t0=mk('game', 'gameStart', 17.85),       dur=16.15, fi=.3,   fo=1.4),
    }
WHOOSH = [(6.6, 1), (13.0, 1), (15.5, .55), (18.2, .55), (21.0, 1), (27.0, 1), (38.0, 1)]
THUMP = [3.2]
