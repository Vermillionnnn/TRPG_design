"""Tall open bookshelf filled with randomly sized, coloured and tilted books.

    bookshelf.build("Shelf", loc=(1.15, 3.75, 0.05), books=True)

Origin is on the floor under the front-to-back centre; the open side faces -y.
"""
import random

from assets.lib import box, group, material

LEVELS = [0.03, 0.5, 0.95, 1.4, 1.85, 2.08]   # shelf boards for the default height


def build(name="Bookshelf", loc=(0, 0, 0), rot_z=0.0, *, width=1.3, height=2.1, depth=0.35,
          books=True, rng=None):
    """books fills the lower four shelves (shelf 1 is always full). rng: random source, default seed 0."""
    rng = rng or random.Random(0)
    dark = material("darkwood")
    levels = [z * height / 2.1 for z in LEVELS]
    parts = [box(name + "SideL", (0.05, depth, height), (-width / 2, 0, height / 2), dark),
             box(name + "SideR", (0.05, depth, height), (width / 2, 0, height / 2), dark),
             box(name + "Back", (width, 0.03, height), (0, depth / 2, height / 2), dark)]
    for i, z in enumerate(levels):
        parts.append(box(f"{name}Board{i}", (width, depth, 0.04), (0, 0, z), dark))
    cols = material("bookcols")
    n = 0
    for li, z in enumerate(levels[:-2] if books else []):
        x = -width / 2 + 0.05
        while x < width / 2 - 0.08:
            if rng.random() < 0.1 and li != 1:
                x += 0.1
                continue
            bw = rng.uniform(0.03, 0.07)
            bh = rng.uniform(0.25, 0.38)
            tilt = rng.uniform(-0.12, 0.0) if rng.random() < 0.15 else 0
            parts.append(box(f"{name}Book{n}", (bw, rng.uniform(0.18, 0.26), bh),
                             (x + bw / 2, -0.02, z + 0.02 + bh / 2), rng.choice(cols),
                             rot=(0, tilt, 0), bev=0.004))
            n += 1
            x += bw + 0.005
    return group(name, parts, loc, rot_z)
