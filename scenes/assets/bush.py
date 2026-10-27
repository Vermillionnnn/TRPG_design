"""Low rounded shrub, optionally dotted with blossoms.

    bush.build("Bush", loc=(1, 2, 0), radius=0.4, bloom="bloom_red")

Origin is under the bush.
"""
import math
import random

from assets.lib import Batch, as_material, blob, group, material


def build(name="Bush", loc=(0, 0, 0), rot_z=0.0, *, radius=0.35, leaf="hedge", bloom=None, blooms=9,
          rng=None):
    """radius (m); leaf: foliage material; bloom: blossom colour (None for a plain shrub).
    rng: random source (default: fixed seed)."""
    rng = rng or random.Random(3)
    r = radius
    parts = [blob(name + "Leaves", r, (0, 0, r * 0.55), as_material(leaf, name + "LeafMat"), squash=0.75,
                  strength=0.12)]
    if bloom:
        b = Batch()
        bm = as_material(bloom, name + "BloomMat")
        for k in range(blooms):
            a, el = rng.uniform(0, 2 * math.pi), rng.uniform(0.15, 1.2)
            b.ball(bm, rng.uniform(0.05, 0.07), (r * 0.95 * math.cos(a) * math.cos(el),
                                                 r * 0.95 * math.sin(a) * math.cos(el),
                                                 r * 0.55 + r * 0.75 * math.sin(el)), scale=(1, 1, 0.6))
        parts += b.build(name + "Bloom", smooth=True)
    return group(name, parts, loc, rot_z)
