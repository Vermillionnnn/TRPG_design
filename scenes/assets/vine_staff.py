"""Gnarled wooden staff wrapped in leafy vines; at the top the wood splits into
curling tendrils that cradle a glowing blue crystal whose lower point is sunk in a wooden cup.

    s = vine_staff.build("Staff", loc=(3, 3.7, 0))
    s.rotation_euler = (math.radians(-6), 0, 0)   # lean it against a wall

Origin is at the foot of the staff; the staff stands along local +z.
"""
import math
import random

from assets.lib import Batch, as_material, curve, group, lathe, mat, material, mesh_obj, noisy_mat, point_light


def crystal(name, zc, r, material):
    """Hexagonal crystal with a short point below and a long point above, centred near zc."""
    verts = [(0, 0, zc - r * 2.2)]
    for z in (zc - r * 0.6, zc + r * 1.0):
        verts += [(r * math.cos(k * math.pi / 3), r * math.sin(k * math.pi / 3), z) for k in range(6)]
    verts.append((0, 0, zc + r * 3.6))
    faces = [(0, 1 + (k + 1) % 6, 1 + k) for k in range(6)]
    faces += [(1 + k, 1 + (k + 1) % 6, 7 + (k + 1) % 6, 7 + k) for k in range(6)]
    faces += [(7 + k, 7 + (k + 1) % 6, 13) for k in range(6)]
    return mesh_obj(name, verts, faces, material, smooth_angle=0)


def build(name="Staff", loc=(0, 0, 0), rot_z=0.0, *, length=1.55, radius=0.022, wood="bark",
          vine=(0.10, 0.17, 0.05), leaf="leaf", crystal_color="sapphire_glow", tendrils=5, blooms=True,
          light=True, rng=None):
    """length: foot to the top of the shaft (the head adds about 0.3 m). wood / vine / leaf:
    material, palette key or (r, g, b); "bark" is this asset's own rough dark wood. crystal_color: material, palette key or (r, g, b);
    the default is this asset's own glowing sapphire. rng: random source for wobble and leaves."""
    rng = rng or random.Random(11)
    if wood == "bark":
        wood = noisy_mat("Bark", (0.07, 0.04, 0.02), (0.26, 0.15, 0.07), 40, 0.75, stretch=(1, 1, 0.15), bump=0.6)
    wood = as_material(wood, name + "Wood", 0.6)
    vine = as_material(vine, name + "Vine", 0.7)
    leaf = as_material(leaf, name + "Leaf", 0.8)
    if crystal_color == "sapphire_glow":
        crystal_color = mat("SapphireGlow", (0.1, 0.3, 1.0), 0.05, emit=(0.05, 0.25, 1.0), emit_strength=1.0)
    glow = as_material(crystal_color, name + "Crystal", 0.05)
    bud = mat("VineBud", (0.3, 0.5, 1.0), 0.3, emit=(0.15, 0.4, 1.0), emit_strength=0.6)
    parts = []

    # shaft: a slightly wandering, knotted pole that thickens toward the top
    pts = []
    for k in range(12):
        z = length * k / 11
        wob = 0.0 if k in (0, 11) else 0.008
        pts.append((rng.uniform(-wob, wob), rng.uniform(-wob, wob), z))
    parts.append(curve(name + "Shaft", pts, radius * 0.85, wood, taper=1.35))
    knots = Batch()
    for k in range(5):
        z = rng.uniform(0.2, 0.9) * length
        a = rng.uniform(0, 2 * math.pi)
        knots.ball(wood, radius * 0.45, (radius * math.cos(a), radius * math.sin(a), z), scale=(1, 1, 1.6), rz=a)

    # head: the shaft swells into a wooden cup; the crystal's lower point is sunk in it
    top = length
    r = 0.042                          # crystal radius
    zc = top + 0.06                     # crystal centre; its lower facets sit inside the cup
    parts.append(lathe(name + "Cup", [(0.0, top - 0.08), (radius * 1.1, top - 0.07), (0.03, top - 0.04),
                                      (0.046, top - 0.005), (0.054, top + 0.03), (0.052, top + 0.045),
                                      (0.046, top + 0.042), (0.0, top + 0.03)], (0, 0, 0), wood, segs=24))
    parts.append(crystal(name + "Crystal", zc, r, glow))
    for k in range(3):                  # small shards breaking out of the cup rim
        a = 2 * math.pi * k / 3 + 0.5
        s = crystal(f"{name}Shard{k}", 0, r * 0.28, glow)
        s.location = (0.044 * math.cos(a), 0.044 * math.sin(a), top + 0.04)
        s.rotation_euler = (-0.5 * math.sin(a), 0.5 * math.cos(a), 0)
        parts.append(s)
    # tendrils grow from the cup, arc well clear of the crystal and curl in above its point
    for k in range(tendrils):
        a = 2 * math.pi * k / tendrils + rng.uniform(-0.15, 0.15)
        twist = 0.9                    # how far each tendril winds around the crystal
        prof = [(0.036, top - 0.04, 0.0), (0.056, top + 0.02, 0.1), (0.085, top + 0.08, 0.3),
                (0.098, top + 0.14, 0.5), (0.088, top + 0.2, 0.7), (0.052, top + 0.26, 0.88),
                (0.018, top + 0.29 + rng.uniform(-0.01, 0.015), 1.02), (0.014, top + 0.265, 1.25)]
        pts = [(d * math.cos(a + twist * f), d * math.sin(a + twist * f), z) for d, z, f in prof]
        parts.append(curve(f"{name}Tendril{k}", pts, radius * 0.5, wood, taper=0.2))

    # three different vines: a thick main vine, a thin tight one low down, a short loose one up top.
    # (start, end as fractions of length, turns, thickness, leaf size, leaf chance, phase, climbs into head,
    #  stem material, leaf material)
    woody = mat("VineWoody", (0.14, 0.08, 0.035), 0.8)
    young = mat("VineYoung", (0.22, 0.36, 0.08), 0.7)
    vines = [(0.3, 1.0, 2.6, 0.0065, 0.036, 0.9, 0.0, True, vine, leaf),
             (0.08, 0.6, 4.5, 0.003, 0.016, 0.3, 2.2, False, woody, leaf),
             (0.6, 1.0, 1.1, 0.0042, 0.024, 0.6, 4.0, True, young, material("leaf_light"))]
    leaves = Batch()
    for v, (f0, f1, turns, thick, lsize, chance, phase, into_head, stem, foliage) in enumerate(vines):
        z0, z1 = length * f0, length * f1 - (0.06 if into_head else 0)
        n = int(24 * turns) + 8
        pts = []
        for i in range(n + 1):
            f = i / n
            z = z0 + (z1 - z0) * f
            a = phase + 2 * math.pi * turns * f
            d = radius * 0.85 * (1.0 + 0.35 * z / length) + thick
            pts.append((d * math.cos(a), d * math.sin(a), z))
        a = phase + 2 * math.pi * turns
        if into_head:                   # climb the cup and on up one tendril
            pts += [(0.05 * math.cos(a + 0.2), 0.05 * math.sin(a + 0.2), top),
                    (0.08 * math.cos(a + 0.45), 0.08 * math.sin(a + 0.45), top + 0.07),
                    (0.1 * math.cos(a + 0.7), 0.1 * math.sin(a + 0.7), top + 0.13)]
        else:                           # the loose end curls away from the shaft
            x, y, z = pts[-1]
            pts += [(x * 1.6 + 0.01 * math.cos(a + 1.6), y * 1.6 + 0.01 * math.sin(a + 1.6), z + 0.03),
                    (x * 2.2, y * 2.2, z + 0.045), (x * 2.0 + 0.01 * math.cos(a + 1.6), y * 2.0, z + 0.03)]
        parts.append(curve(f"{name}Vine{v}", pts, thick, stem, taper=0.35))
        # leaves thin out toward the start of each vine and crowd toward its end
        for i in range(2, len(pts) - 1, 2):
            if rng.random() > chance * (0.3 + 0.7 * i / len(pts)):
                continue
            x, y, z = pts[i]
            a = math.atan2(y, x) + rng.uniform(-0.6, 0.6)
            size = lsize * rng.uniform(0.75, 1.2)
            leaves.ball(foliage, size, (x + size * 0.8 * math.cos(a), y + size * 0.8 * math.sin(a), z),
                        scale=(1.0, 0.5, 0.12), rz=a, ry=rng.uniform(-0.8, -0.2))
            if blooms and v != 1 and rng.random() < 0.18:
                leaves.ball(bud, 0.007, (x + 0.006 * math.cos(a + 1), y + 0.006 * math.sin(a + 1), z + 0.01))
    # a small leaf crown at the foot of the cup
    for k in range(7):
        a = 2 * math.pi * k / 7
        leaves.ball(leaf, 0.028, (0.038 * math.cos(a), 0.038 * math.sin(a), top - 0.045),
                    scale=(1.0, 0.45, 0.12), rz=a, ry=-0.7)
    parts += knots.build(name + "Knots", smooth=True) + leaves.build(name + "Leaves", smooth=True)

    if light:
        parts.append(point_light(name + "Light", (0, -0.12, zc), 3, (0.3, 0.55, 1.0), radius=0.05))
    return group(name, parts, loc, rot_z)
