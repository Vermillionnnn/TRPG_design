"""Small stone obelisk on a stepped plinth, a column of glowing runes cut into its face
and a glowing capstone; set in rings around duelling circles and wards.

    runestone.build("Stone", loc=(1, 2, 0), rot_z=0.3)

Origin is under the plinth; the runes face local -y.
"""
import math
import random

from assets.lib import Batch, as_material, box, group, material, mesh_obj, point_light


def build(name="Runestone", loc=(0, 0, 0), rot_z=0.0, *, width=0.28, height=1.0, glow="arcane_cyan",
          light=False, rng=None):
    """width at the foot of the shaft and total height (m). glow: material, palette key or
    (r, g, b) of runes and capstone. rng: random source."""
    rng = rng or random.Random(4)
    stone, glow = material("flag"), as_material(glow, name + "Glow", 0.3)
    w, h = width, height
    z0, z1 = 0.16, h - w * 0.55             # shaft from plinth top to the capstone
    t = w * 0.7                              # half-width at the top of the shaft
    v = [(sx * w / 2, sy * w / 2, z0) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    v += [(sx * t / 2, sy * t / 2, z1) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (3, 2, 1, 0), (4, 5, 6, 7)]
    parts = [box(name + "Plinth", (w + 0.2, w + 0.2, 0.09), (0, 0, 0.045), stone, bev=0.02),
             box(name + "Step", (w + 0.1, w + 0.1, 0.07), (0, 0, 0.125), stone, bev=0.015),
             mesh_obj(name + "Shaft", v, f, material("blackstone"), smooth_angle=0),
             mesh_obj(name + "Cap", [(sx * t / 2, sy * t / 2, z1) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                      + [(0, 0, h)], [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], glow,
                      smooth_angle=0)]
    b = Batch()
    n = 4
    for k in range(n):
        z = z0 + 0.12 + k * (z1 - z0 - 0.2) / n
        tw = w / 2 + (t / 2 - w / 2) * (z - z0) / (z1 - z0)
        shape = rng.choice(((0.08, 0.016), (0.016, 0.08), (0.06, 0.06)))
        b.box(glow, (shape[0] * w / 0.28, 0.01, shape[1] * w / 0.28), (0, -tw - 0.002, z),
              ry=rng.choice((0, math.pi / 4)))
    parts += b.build(name + "Runes")
    if light:
        parts.append(point_light(name + "Light", (0, -w, h * 0.6), 5, (0.4, 0.8, 1.0), radius=0.15))
    return group(name, parts, loc, rot_z)
