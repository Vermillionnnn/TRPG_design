"""Stylised tree: a broadleaf with lumpy foliage clumps, or a three-tier pine.

    tree.build("Oak", loc=(1.5, 9, 0.0), height=3.6, crown=1.1)
    tree.build("Apple", loc=(13, 7.6, 0), height=2.8, crown=0.75, clumps=7, lumpy=True, fruit="apple")
    tree.build("Pine", loc=(1.2, 11, 0), kind="pine", height=4.4)

Origin is at the foot of the trunk.
"""
import math
import random

from assets.lib import Batch, as_material, blob, cone, cyl, group, material


def build(name="Tree", loc=(0, 0, 0), rot_z=0.0, *, kind="leafy", height=3.4, crown=1.0, leaf=None,
          clumps=4, lumpy=False, fruit=None, rng=None):
    """kind: "leafy" or "pine". crown: foliage radius scale (leafy). leaf: foliage material.
    clumps: number of foliage clumps; lumpy gives finer, deeper lumps (less smooth).
    fruit: colour of small fruit dotted over the crown (None for none).
    rng: random source (default: fixed seed, same tree every time)."""
    rng = rng or random.Random(5)
    h, r, parts = height, crown, []
    log = material("log")
    if kind == "pine":
        parts.append(cyl(name + "Trunk", 0.12, h * 0.3, (0, 0, h * 0.15), log, verts=8))
        for k in range(3):
            rk = h * (0.28 - 0.07 * k)
            parts.append(cone(f"{name}Tier{k}", rk, 0.0, h * 0.42, (0, 0, h * (0.32 + 0.2 * k) + h * 0.18),
                              as_material(leaf, name + "LeafMat") or material("pine"),
                              rot=(0, 0, rng.uniform(0, 1)), verts=8, smooth=False))
        return group(name, parts, loc, rot_z)

    leaf = as_material(leaf, name + "LeafMat") or material("leaf")
    parts.append(cone(name + "Trunk", 0.16, 0.07, h * 0.65, (0, 0, h * 0.32), log, verts=10))
    spread, noise, subdiv = (0.6, 0.12, 4) if lumpy else (0.45, 0.3, 3)
    centres = []
    for k in range(clumps):
        off = (0, 0, 0) if k == 0 else (rng.uniform(-spread, spread) * r, rng.uniform(-spread, spread) * r,
                                        rng.uniform(-0.25, 0.35) * r)
        rk = r * rng.uniform(0.6, 0.85) * (0.8 if lumpy else 1.0)
        c = (off[0], off[1], h * 0.75 + off[2])
        centres.append((c, rk))
        parts.append(blob(f"{name}Crown{k}", rk, c, leaf, strength=(0.45 if lumpy else 0.35) * r,
                          noise=noise, subdiv=subdiv))
    if lumpy:
        # a few short limbs reaching into the outer clumps
        for k, (c, _) in enumerate(centres[1:]):
            ln = math.hypot(c[0], c[1])
            if ln < 0.15:
                continue
            ang = math.atan2(c[2] - h * 0.55, ln)
            parts.append(cyl(f"{name}Limb{k}", 0.045, math.hypot(ln, c[2] - h * 0.55),(c[0] / 2, c[1] / 2, (h * 0.55 + c[2]) / 2), log,
                             rot=(0, math.pi / 2 - ang, math.atan2(c[1], c[0])), verts=8))
    if fruit:
        b = Batch()
        fm = as_material(fruit, name + "FruitMat")
        for k in range(18):
            c, rk = rng.choice(centres)
            a, el = rng.uniform(0, 2 * math.pi), rng.uniform(-0.3, 0.9)
            d = rk * 1.05
            b.ball(fm, 0.055, (c[0] + d * math.cos(a) * math.cos(el), c[1] + d * math.sin(a) * math.cos(el),
                               c[2] + d * math.sin(el)))
        parts += b.build(name + "Fruit", smooth=True)
    return group(name, parts, loc, rot_z)
