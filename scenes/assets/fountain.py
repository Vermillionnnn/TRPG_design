"""Tiered stone fountain in the Roman manner: a round basin with a moulded rim, a turned
pedestal carrying two bowls, sheets of water spilling from each bowl, and (magic=True)
a glowing orb hovering in a brass ring on top, with runes around the basin.

    fountain.build("Fountain", loc=(6.9, 3.3, 0.1))

Origin is on the ground at the centre.
"""
import math

from assets.lib import (Batch, as_material, cyl, glass_mat, group, lathe, mat, material, mesh_obj,
                        point_light, sphere, torus)


def sheet(name, profile, material, segs=48):
    """Open surface of revolution (no caps) through (radius, z) points: a falling water curtain."""
    verts, faces, n = [], [], len(profile)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        verts += [(r * math.cos(a), r * math.sin(a), z) for r, z in profile]
    for i in range(segs):
        j = (i + 1) % segs
        faces += [(i * n + k, j * n + k, j * n + k + 1, i * n + k + 1) for k in range(n - 1)]
    o = mesh_obj(name, verts, faces, material, smooth_angle=80)
    o.visible_shadow = False
    return o


def build(name="Fountain", loc=(0, 0, 0), rot_z=0.0, *, radius=1.0, magic=True, glow="arcane_cyan"):
    """radius of the basin (m); everything scales with it. magic adds the floating orb and runes."""
    s = radius
    stone = material("flag")
    pool = mat("PoolWater", (0.10, 0.28, 0.34), 0.05)
    falls = glass_mat("FallingWater", (0.75, 0.92, 1.0))
    P = lambda pts: [(r * s, z * s) for r, z in pts]       # noqa: E731
    parts = [
        # basin wall with a rolled rim, the floor and the water surface
        lathe(name + "Basin", P([(0.86, 0.0), (1.0, 0.0), (1.0, 0.06), (0.97, 0.1), (0.97, 0.3), (1.05, 0.34),
                                 (1.06, 0.42), (1.0, 0.45), (0.88, 0.45), (0.86, 0.42), (0.86, 0.001)]),
              (0, 0, 0), stone, segs=48),
        cyl(name + "Floor", 0.87 * s, 0.06 * s, (0, 0, 0.03 * s), stone, verts=48),
        cyl(name + "Water", 0.87 * s, 0.01 * s, (0, 0, 0.36 * s), pool, verts=48),
        # pedestal, lower bowl, upper column, upper bowl, finial
        lathe(name + "Pedestal", P([(0.2, 0.0), (0.2, 0.08), (0.14, 0.14), (0.1, 0.3), (0.12, 0.55), (0.09, 0.8),
                                    (0.12, 0.84), (0.35, 0.9), (0.52, 1.0), (0.55, 1.07), (0.49, 1.08),
                                    (0.46, 1.04), (0.07, 1.04), (0.07, 1.4), (0.1, 1.45), (0.06, 1.5),
                                    (0.08, 1.55), (0.22, 1.6), (0.3, 1.68), (0.31, 1.72), (0.27, 1.72),
                                    (0.25, 1.69), (0.06, 1.69), (0.05, 1.8), (0.08, 1.84), (0.0, 1.9)]),
              (0, 0, 0), stone, segs=40),
        cyl(name + "BowlWater", 0.47 * s, 0.01 * s, (0, 0, 1.065 * s), pool, verts=40),
        cyl(name + "CupWater", 0.26 * s, 0.01 * s, (0, 0, 1.705 * s), pool, verts=32),
        # water spilling over both bowl rims into the pool below
        sheet(name + "FallLow", P([(0.555, 1.07), (0.58, 0.95), (0.61, 0.7), (0.63, 0.37)]), falls),
        sheet(name + "FallHigh", P([(0.315, 1.71), (0.33, 1.6), (0.36, 1.35), (0.38, 1.08)]), falls),
    ]
    # a few wishing coins on the basin floor
    b = Batch()
    for k, (r, a) in enumerate(((0.4, 0.3), (0.55, 1.9), (0.3, 3.0), (0.62, 4.4), (0.5, 5.4))):
        b.cyl(material("brass"), 0.025 * s, 0.006 * s, (r * s * math.cos(a), r * s * math.sin(a), 0.065 * s),
              rx=0.1 * k, segs=10)
    parts += b.build(name + "Coins")
    if magic:
        glow = as_material(glow, name + "Glow", 0.2)
        parts += [sphere(name + "Orb", 0.09 * s, (0, 0, 2.08 * s), glow, segs=16),
                  torus(name + "OrbRing", 0.16 * s, 0.008 * s, (0, 0, 2.08 * s), material("brass"),
                        rot=(math.radians(70), 0, math.radians(20)), major_segments=40, minor_segments=6),
                  point_light(name + "OrbLight", (0, 0, 2.08 * s), 30, (0.4, 0.8, 1.0), radius=0.1 * s),
                  point_light(name + "PoolLight", (0, 0, 0.5 * s), 12, (0.4, 0.8, 1.0), radius=0.6 * s)]
        runes = Batch()
        for k in range(16):
            a = k * 2 * math.pi / 16
            r = 0.975 * s
            shape = ((0.06, 0.012), (0.012, 0.06), (0.045, 0.045))[k % 3]
            runes.box(glow, (shape[0] * s, 0.01 * s, shape[1] * s), (r * math.cos(a), r * math.sin(a), 0.2 * s),
                      rz=a + math.pi / 2, ry=math.pi / 4 if k % 3 == 2 else 0)
        parts += runes.build(name + "Runes")
    return group(name, parts, loc, rot_z)
