# Mixes the recorded music clips over a synthesized campfire/cricket bed, with whooshes on the cuts.
# writes $WORK/mix_raw.wav (peak-normalized; make_video.sh sets the final loudness)
import os, subprocess, numpy as np, wave, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_tracks import WORK, DUR, WHOOSH, THUMP, meta, tracks
TRACKS = tracks()
SR = 48000
N = int(DUR * SR)
rng = np.random.default_rng(7)
def load(c):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(WORK, 'audio', c, 'audio.webm'), '-ar', str(SR), '-ac', '2', '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
from scipy.signal import lfilter, butter
music = np.zeros((N, 2))
for name, tr in TRACKS.items():
    if not tr['dur']: continue
    a = load(tr['clip']); m, st = meta(tr['clip'])
    a0 = m['audioStart'] - st                     # clip time at audio sample 0
    s = int((tr['t0'] - a0) * SR); n = int(tr['dur'] * SR)
    seg = np.zeros((n, 2)); src = a[max(0, s):s + n]; seg[max(0, -s):max(0, -s) + len(src)] = src[:n - max(0, -s)]
    env = np.ones(n); fi = int(tr['fi'] * SR); fo = int(tr['fo'] * SR)
    if fi: env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
    if fo: env[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    o = int(tr['out'] * SR)
    music[o:o + n] += seg * env[:, None] * tr.get('g', 1)
# --- ambience: fire roar + crackles + crickets ---
t = np.arange(N) / SR
w = rng.standard_normal((N, 2))
b, a = butter(2, 380 / (SR / 2)); roar = lfilter(b, a, w, axis=0)
roar *= (0.75 + 0.25 * np.sin(2 * np.pi * 0.37 * t + 1) * np.sin(2 * np.pi * 0.11 * t))[:, None]
roar /= np.abs(roar).max(); roar *= 0.10
crack = np.zeros((N, 2))
bh, ah = butter(2, 1800 / (SR / 2), 'high')
k = 0.0
while True:
    k += rng.exponential(1 / 7.0)
    if k > DUR - .1: break
    L = int(SR * rng.uniform(.004, .03)); i = int(k * SR)
    burst = rng.standard_normal(L) * np.exp(-np.linspace(0, 6, L)) * rng.uniform(.05, .5) ** 1.5
    pan = rng.uniform(.3, .7)
    crack[i:i + L, 0] += burst * (1 - pan); crack[i:i + L, 1] += burst * pan
crack = lfilter(bh, ah, crack, axis=0) * 0.55
crick = np.zeros(N)
for c0 in np.arange(0.4, DUR, 1.7):
    for j in range(3):
        st_ = c0 + j * 0.09 + rng.uniform(0, .02); L = int(.05 * SR); i = int(st_ * SR)
        if i + L >= N: break
        tt = np.arange(L) / SR
        crick[i:i + L] += np.sin(2 * np.pi * 4300 * tt) * np.sin(np.pi * tt / tt[-1]) ** 2 * (0.5 + 0.5 * np.sin(2 * np.pi * 90 * tt))
crick = np.stack([crick * .6, crick * .4], 1) * 0.012
amb = roar + crack + crick
# ambience level: up front over the fire, tucked under the music, back up at the end
lvl = np.interp(t, [0, .2, 3.0, 3.6, 5.6, 6.8, 40.6, 42.2, 43.0], [0, 2.2, 2.2, 1.3, 1.8, .7, .7, 2.0, 2.0])
amb *= lvl[:, None]
# --- sfx: whooshes and a thump ---
sfx = np.zeros((N, 2))
bw = rng.standard_normal(int(.7 * SR))
for tc, g in WHOOSH:
    L = len(bw); i = int((tc - .38) * SR); tt = np.linspace(0, 1, L)
    # sweep a bandpass upward by morphing between low- and high-passed noise
    lo = lfilter(*butter(2, 700 / (SR / 2)), bw); hi = lfilter(*butter(2, 2500 / (SR / 2), 'high'), bw)
    x = (lo * (1 - tt) + hi * tt) * np.sin(np.pi * tt) ** 3 * 0.22 * g
    pan = np.linspace(.2, .8, L)
    sfx[i:i + L, 0] += x * (1 - pan); sfx[i:i + L, 1] += x * pan
for tc in THUMP:
    L = int(.6 * SR); i = int(tc * SR); tt = np.arange(L) / SR
    x = np.sin(2 * np.pi * (55 * tt + 20 * (1 - np.exp(-tt * 20)) / 20)) * np.exp(-tt * 7) * .35
    sfx[i:i + L] += x[:, None]
mix = music + amb + sfx
mix[:int(.05 * SR)] *= np.linspace(0, 1, int(.05 * SR))[:, None]
mix[-int(.5 * SR):] *= np.linspace(1, 0, int(.5 * SR))[:, None] ** 2
mix /= max(1e-9, np.abs(mix).max()) / 0.9
with wave.open(os.path.join(WORK, 'mix_raw.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
print('mix ok')
