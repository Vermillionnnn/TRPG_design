"""Hourglass: two glass bulbs between wooden caps on three thin posts.

    hourglass.build("Hourglass", loc=(-0.35, 2.75, 0.786))

Origin is under the bottom cap.
"""
import math

from assets.lib import cone, cyl, group, material, sphere


def build(name="Hourglass", loc=(0, 0, 0), rot_z=0.0, *, height=0.2, wood="darkwood"):
    wood = material(wood) if isinstance(wood, str) else wood
    s = height / 0.2
    mid = 0.1 * s
    p = []
    for k, sgn in enumerate((-1, 1)):
        p.append(cyl(f"{name}Cap{k}", 0.05 * s, 0.015 * s, (0, 0, mid + sgn * 0.09 * s), wood, verts=12))
        p.append(cone(f"{name}Bulb{k}", 0.04 * s, 0.008 * s, 0.085 * s, (0, 0, mid + sgn * 0.045 * s),
                      material("clear_glass"), rot=(0 if sgn < 0 else math.pi, 0, 0), verts=14))
    p.append(cone(name + "Sand", 0.03 * s, 0.0, 0.03 * s, (0, 0, mid - 0.07 * s),
                  material("old_parchment"), verts=12))
    for k in range(3):
        a = k * 2 * math.pi / 3
        p.append(sphere(f"{name}Post{k}", 0.008 * s, (0.045 * s * math.cos(a), 0.045 * s * math.sin(a), mid),
                        wood, scale=(1, 1, 11), segs=6))
    return group(name, p, loc, rot_z)
