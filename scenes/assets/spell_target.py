"""Spell practice target: a bronze disc hung on chains from a timber frame, engraved with
glowing rune rings and a bright bullseye, its face pitted with soot scorches.

    spell_target.build("Target", loc=(13, 3, 0), rot_z=-math.pi / 2)

Origin is on the ground at the centre of the frame; the disc faces local -y.
"""
import math
import random

from assets.lib import Batch, as_material, box, cyl, group, mat, material, point_light, torus


def build(name="SpellTarget", loc=(0, 0, 0), rot_z=0.0, *, radius=0.4, height=1.9, glow="arcane_cyan",
          light=True, rng=None):
    """radius of the disc and height of the frame (m). glow: material, palette key or (r, g, b).
    rng: random source for the scorch marks."""
    rng = rng or random.Random(8)
    r, h = radius, height
    wood, iron, glow = material("darkwood"), material("iron"), as_material(glow, name + "Glow", 0.3)
    span = r + 0.22
    parts = []
    for sx in (-1, 1):
        parts += [box(f"{name}Post{sx}", (0.1, 0.1, h), (sx * span, 0, h / 2), wood),
                  box(f"{name}Foot{sx}", (0.12, 0.6, 0.08), (sx * span, 0, 0.04), wood),
                  box(f"{name}Brace{sx}", (0.06, 0.06, 0.45), (sx * span, 0.16, 0.25), wood, rot=(0.6, 0, 0))]
    parts.append(box(name + "Beam", (2 * span + 0.24, 0.12, 0.12), (0, 0, h + 0.02), wood))
    zc = h - 0.2 - r
    for sx in (-1, 1):
        parts.append(cyl(f"{name}Chain{sx}", 0.008, h - zc - r * 0.7, (sx * r * 0.6, 0, (h + zc + r * 0.7) / 2),
                         iron, verts=6))
    rot = (math.pi / 2, 0, 0)
    parts += [cyl(name + "Disc", r, 0.04, (0, 0, zc), material("brass"), rot=rot, verts=40),
              torus(name + "Rim", r, 0.02, (0, 0, zc), iron, rot=rot, major_segments=40, minor_segments=8)]
    for k, f in enumerate((0.75, 0.5)):
        parts.append(torus(f"{name}Ring{k}", r * f, 0.008, (0, -0.022, zc), glow, rot=rot,
                           major_segments=40, minor_segments=6))
    b = Batch()
    b.cyl(glow, r * 0.18, 0.01, (0, -0.022, zc), rx=math.pi / 2, segs=20)
    for k in range(10):     # small glowing glyph dots between the rings
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0.2, 0.9) * r
        b.ball(glow, 0.012, (d * math.cos(a), -0.024, zc + d * math.sin(a)), scale=(1, 0.3, 1))
    soot = mat("Soot", (0.03, 0.025, 0.02), 1)
    for k in range(6):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0.25, 0.85) * r
        b.cyl(soot, rng.uniform(0.03, 0.07) * r / 0.4, 0.006, (d * math.cos(a), -0.021, zc + d * math.sin(a)),
              rx=math.pi / 2, segs=10)
    parts += b.build(name + "Marks")
    if light:
        parts.append(point_light(name + "Light", (0, -0.3, zc), 8, (0.4, 0.8, 1.0), radius=0.2))
    return group(name, parts, loc, rot_z)
