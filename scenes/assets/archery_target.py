"""Straw archery butt with painted rings and three arrows, leaning back on two legs and a prop.

    archery_target.build("Target", loc=(4, 6, 0))

Origin is on the ground under the target face; the face looks toward -y.
"""
import math

from assets.lib import box, cyl, group, material


def build(name="Target", loc=(0, 0, 0), rot_z=0.0, *, arrows=3):
    """arrows: how many arrows stick out of the face (0-3)."""
    parts = []
    rings = ((0.45, "straw"), (0.38, "white_paint"), (0.27, "red_paint"), (0.17, "white_paint"),
             (0.08, "red_paint"))
    for k, (r, key) in enumerate(rings):
        parts.append(cyl(f"{name}Ring{k}", r, 0.12 if k == 0 else 0.01, (0, -0.06 - 0.008 * k if k else 0, 1.05),
                         material(key), rot=(math.pi / 2 - 0.15, 0, 0), verts=32))
    for k, (dx, dz) in enumerate(((0.05, 0.08), (-0.15, -0.05), (0.2, 0.2))[:arrows]):
        parts.append(cyl(f"{name}Arrow{k}", 0.008, 0.6, (dx, -0.3, 1.05 + dz), material("wood"),
                         rot=(math.pi / 2 - 0.25, 0, 0.1 * k), verts=6))
    log = material("log")
    for sx in (-1, 1):
        parts.append(box(f"{name}Leg{sx}", (0.06, 0.06, 1.5), (sx * 0.3, 0.05, 0.75), log, rot=(-0.15, 0, 0)))
    parts.append(box(name + "Prop", (0.06, 0.06, 1.4), (0, 0.4, 0.65), log, rot=(0.4, 0, 0)))
    return group(name, parts, loc, rot_z)
