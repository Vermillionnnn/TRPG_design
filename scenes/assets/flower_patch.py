"""Loose patch of flowers (leafy tuft, stem and bloom) scattered inside an ellipse.

    flower_patch.build("Meadow", loc=(2.4, 9.8, 0.08), rx=1.0, ry=1.4, count=40,
                       colors=["bloom_red", "bloom_white"])

Origin is at the centre of the patch, on the ground. All flowers are merged into one
mesh per material, so hundreds of them stay cheap.
"""
import math
import random

from assets.lib import Batch, as_material, group, material


def build(name="Flowers", loc=(0, 0, 0), rot_z=0.0, *, rx=0.5, ry=0.5, count=20,
          colors=("bloom_red", "bloom_yellow", "bloom_white"), size=1.0, rng=None):
    """rx / ry: half-axes of the ellipse (m); count: number of flowers; colors: bloom
    materials or palette keys; size scales stems and blooms. rng: random source."""
    rng = rng or random.Random(7)
    cols = [as_material(c, f"{name}Bloom{i}Mat") for i, c in enumerate(colors)]
    stem, tuft = material("tuft"), material("leaf_light")
    b = Batch()
    for k in range(count):
        a, d = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x, y = rx * d * math.cos(a), ry * d * math.sin(a)
        hgt = rng.uniform(0.16, 0.32) * size
        b.ball(tuft, 0.07 * size, (x, y, 0.03 * size), scale=(1, 1, 0.5), rz=rng.uniform(0, 3))
        b.cyl(stem, 0.008 * size, hgt, (x, y, hgt / 2), rx=rng.uniform(-0.12, 0.12), segs=5)
        c = rng.choice(cols)
        rb = rng.uniform(0.05, 0.07) * size
        b.ball(c, rb, (x, y, hgt), scale=(1, 1, 0.55), rz=rng.uniform(0, 3))
        b.ball(material("bloom_yellow") if c.name != "BloomYellow" else material("soil"), rb * 0.35,
               (x, y, hgt + rb * 0.3))
    return group(name, b.build(name, smooth=True), loc, rot_z)
