"""Compose a Latin titulus from the Uncial letters already outlined in bard-lute.

The bard-lute titulus "HIC · IOCVLATOR · CANIT · AD · IGNEM" is one SVG path in
Uncial Antiqua (SIL OFL). This splits it into glyphs and lays out a new line
from the same letters, centred on x = 500 of the 1000 x 800 fresco, so the new
page needs no font download. Available letters: A C D E G H I L M N O R T V and ·.

    python3 html/scribe-scroll/tools/compose_titulus.py 'HIC·MAGA·CARMINA·NOTAT' > out/titulus.txt
"""
import pathlib
import re
import sys

HTML = pathlib.Path(__file__).resolve().parents[2]
SRC = HTML / 'bard-lute' / 'bard-lute.html'
LETTERS = list('HIC·IOCVLATOR·CANIT·AD·IGNEM')
GAP, DOT_GAP = 6.0, 19.0  # the spacing measured between letters and around the dots in the original

src = SRC.read_text(encoding='utf-8')
d = re.search(r'aria-label="HIC · IOCVLATOR · CANIT · AD · IGNEM" fill="#8f3324" d="([^"]+)"', src).group(1)

# parse into subpaths of (command, absolute coords); the path only uses M L H V Q Z
toks = re.findall(r'[MLHVQZ]|-?\d+\.?\d*', d)
subs, cur, i, px, py = [], None, 0, 0.0, 0.0
while i < len(toks):
    t = toks[i]
    i += 1
    if t == 'M':
        cur = []
        subs.append(cur)
        px, py = float(toks[i]), float(toks[i + 1])
        i += 2
        cur.append(('M', [px, py]))
    elif t in 'LQ':
        n = 2 if t == 'L' else 4
        while i < len(toks) and toks[i] not in 'MLHVQZ':
            v = list(map(float, toks[i:i + n]))
            i += n
            cur.append((t, v))
            px, py = v[-2], v[-1]
    elif t == 'H':
        while i < len(toks) and toks[i] not in 'MLHVQZ':
            px = float(toks[i])
            i += 1
            cur.append(('L', [px, py]))
    elif t == 'V':
        while i < len(toks) and toks[i] not in 'MLHVQZ':
            py = float(toks[i])
            i += 1
            cur.append(('L', [px, py]))
    elif t == 'Z':
        cur.append(('Z', []))


def bbox(sp):
    xs = [v[k] for _, v in sp for k in range(0, len(v), 2)]
    return min(xs), max(xs)


# a subpath lying inside the previous glyph's x-range is its counter (the hole in O, A, R...)
glyphs = []
for sp in subs:
    b = bbox(sp)
    if glyphs and b[0] >= glyphs[-1]['b'][0] - .5 and b[1] <= glyphs[-1]['b'][1] + .5:
        glyphs[-1]['s'].append(sp)
    else:
        glyphs.append({'s': [sp], 'b': b})
assert len(glyphs) == len(LETTERS), (len(glyphs), len(LETTERS))
G = {}
for c, g in zip(LETTERS, glyphs):
    G.setdefault(c, g)

text = sys.argv[1]
items, x = [], 0.0
for k, c in enumerate(text):
    g = G[c]
    if k:
        x += DOT_GAP if (c == '·' or text[k - 1] == '·') else GAP
    items.append((g, x))
    x += g['b'][1] - g['b'][0]
off = 500 - x / 2
out = ''
for g, gx in items:
    dx = off + gx - g['b'][0]
    for sp in g['s']:
        for c, v in sp:
            v = [round(v[j] + (dx if j % 2 == 0 else 0), 1) for j in range(len(v))]
            out += c + ' '.join('%g' % n for n in v)
print(out)
