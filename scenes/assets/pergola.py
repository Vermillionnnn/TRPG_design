"""Timber pergola overgrown with a climbing vine: posts, long beams, cross slats, woody
stems twisting up the corner posts and along the beams, a leaf canopy with hanging
tendrils, and fruit (grapes) or flower racemes (wisteria) dangling between the slats.

    pergola.build("Pergola", loc=(12, 9.75, 0.1))                      # grapevine
    pergola.build("Pergola", loc=(12, 9.75, 0.1), vine="wisteria")    # violet racemes

Origin is on the ground at the centre; posts stand at x = +-width/2, the beams run along y.
"""
import math
import random

from assets.lib import Batch, box, curve, group, material


def _along(pts, step):
    """Points every `step` metres along a polyline."""
    out = []
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        n = max(1, int(d / step))
        out += [tuple(a[i] + (b[i] - a[i]) * k / n for i in range(3)) for k in range(n)]
    return out


def build(name="Pergola", loc=(0, 0, 0), rot_z=0.0, *, width=2.5, depth=3.0, height=2.5, posts=3,
          vine="grape", cover=1.0, rng=None):
    """width / depth: post spacing (m); height: post height; posts: posts per side.
    vine: "grape", "wisteria" or None (bare timber). cover: how dense the leaf canopy is (0-1).
    rng: random source (default: fixed seed)."""
    rng = rng or random.Random(9)
    wood = material("wood")
    parts = []
    for sx in (-1, 1):
        for k in range(posts):
            y = -depth / 2 + k * depth / (posts - 1)
            parts.append(box(f"{name}Post{sx}{k}", (0.14, 0.14, height), (sx * width / 2, y, height / 2), wood))
        parts.append(box(f"{name}Beam{sx}", (0.12, depth + 0.8, 0.2), (sx * width / 2, 0, height + 0.05), wood))
    n_slats = int((depth + 0.6) / 0.45) + 1
    slat_y = [-(depth + 0.6) / 2 + k * 0.45 for k in range(n_slats)]
    for k, y in enumerate(slat_y):
        parts.append(box(f"{name}Slat{k}", (width + 0.5, 0.07, 0.12), (0, y, height + 0.21), wood))
    if not vine:
        return group(name, parts, loc, rot_z)

    stem = material("log")
    top = height + 0.3
    leaves = Batch()
    tones = (material("leaf"), material("leaf"), material("leaf_light"))

    def leaf_at(p, spread=0.12, size=1.0):
        leaves.ball(rng.choice(tones), rng.uniform(0.06, 0.09) * size,
                    (p[0] + rng.uniform(-spread, spread), p[1] + rng.uniform(-spread, spread),
                     p[2] + rng.uniform(-spread, spread) * 0.6),
                    scale=(1, 0.7, 0.3), rx=rng.uniform(-0.8, 0.8), ry=rng.uniform(-0.8, 0.8),
                    rz=rng.uniform(0, math.pi))

    # woody stems: spiral up each corner post, then wander along the beam and out over the slats
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        px, py = sx * width / 2, sy * depth / 2
        turns, ph = rng.uniform(1.6, 2.4), rng.uniform(0, 2 * math.pi)
        pts = []
        for k in range(15):
            t = k / 14
            a = ph + t * turns * 2 * math.pi
            pts.append((px + 0.1 * math.cos(a), py + 0.1 * math.sin(a), t * (height + 0.1)))
        y = py
        for k in range(5):
            y -= sy * depth / 9
            pts.append((px + rng.uniform(-0.08, 0.08), y, height + 0.2 + rng.uniform(0, 0.08)))
        parts.append(curve(f"{name}Stem{i}", pts, 0.035, stem, taper=0.35))
        for p in _along(pts[6:], 0.12):
            leaf_at(p, 0.1, 0.8 if p[2] < height else 1.0)
        # side shoots across a few slats toward the middle
        for j in rng.sample(range(n_slats), 3):
            y0 = slat_y[j]
            shoot = [(px, y0, top - 0.05)]
            for k in range(1, 5):
                shoot.append((px - sx * width * 0.13 * k, y0 + rng.uniform(-0.08, 0.08), top + rng.uniform(-0.02, 0.06)))
            parts.append(curve(f"{name}Shoot{i}_{j}", shoot, 0.018, stem, taper=0.3))

    # leaf canopy over the slats, with tendrils hanging off their edges
    for y in slat_y:
        x = -width / 2 - 0.25
        while x < width / 2 + 0.25:
            for dy, dz, p in ((0, 0.02, 0.95), (-0.15, -0.02, 0.7), (0.15, -0.02, 0.7), (0, 0.1, 0.5)):
                if rng.random() < p * cover:
                    leaf_at((x, y + dy, top + dz), 0.12, 0.85)
            x += 0.06
        for _ in range(int(4 * cover)):
            x, ln = rng.uniform(-width / 2, width / 2), rng.uniform(0.2, 0.6)
            for k in range(int(ln / 0.07)):
                leaf_at((x + rng.uniform(-0.03, 0.03), y + 0.06, height + 0.12 - k * 0.07), 0.04, 0.8)
    parts += leaves.build(name + "Leaves", smooth=True)

    # fruit or flowers hanging between the slats
    hang = Batch()
    if vine == "wisteria":
        cols = (material("wisteria"), material("wisteria2"))
        n, ln_range, r0 = 34, (0.25, 0.5), 0.05
    else:
        cols = (material("grape_green"), material("grape_green"), material("grape_red"))
        n, ln_range, r0 = 26, (0.2, 0.32), 0.09
    for k in range(n):
        x = rng.uniform(-width / 2 + 0.15, width / 2 - 0.15)
        y = rng.choice(slat_y[:-1]) + 0.225 + rng.uniform(-0.08, 0.08)
        ln, col = rng.uniform(*ln_range), rng.choice(cols)
        z0 = height + 0.1
        m = int(ln / 0.012)
        for j in range(m):
            t = j / max(1, m - 1)
            ring = r0 * (1 - 0.85 * t) * rng.uniform(0.5, 1.0)
            a = j * 2.4
            hang.ball(col, 0.026 + 0.012 * (1 - t), (x + ring * math.cos(a), y + ring * math.sin(a), z0 - t * ln))
        if vine != "wisteria":
            parts.append(curve(f"{name}Stalk{k}", [(x, y, z0 + 0.12), (x, y + 0.02, z0 + 0.05), (x, y, z0)],
                               0.006, stem))
    parts += hang.build(name + "Hang", smooth=True)
    return group(name, parts, loc, rot_z)
