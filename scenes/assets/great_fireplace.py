"""Large dressed-stone fireplace: coursed jambs, a flat arch with a basalt
keystone, a moulded oak mantel on stacked corbels, a staggered chimney breast
with a string course, andirons, logs, flames and embers.

    great_fireplace.build("Hearth", loc=polar(4.98, a), rot_z=a - math.pi / 2)

Origin is on the floor at the wall face under the middle of the fireplace; the
hearth opens toward local -y. The mantel top is at z = 1.765. Flames are
<name>Flame<i> and the fire light <name>Light, so a scene can animate them.
"""
import math
import random

from assets.lib import Batch, box, cyl, group, material, point_light, sphere


def build(name="GreatFireplace", loc=(0, 0, 0), rot_z=0.0, *, chimney_top=4.35, fire=True, rng=None):
    """chimney_top: height the chimney breast is coursed up to. rng: random source (default seed 14)."""
    rng = rng or random.Random(14)
    smoked, basalt = material("smoked_stone"), material("blackstone")
    oak = material("darkwood")
    p = [box(name + "Hearth", (2.1, 0.9, 0.1), (0, -0.5, 0.1), material("stone"), bev=0.02),
         box(name + "HearthEdge", (2.16, 0.06, 0.12), (0, -0.94, 0.1), basalt, bev=0.02),
         box(name + "Back", (1.2, 0.05, 1.2), (0, -0.03, 0.7), material("soot"), bev=0)]

    def stone():
        # soot-darkened stone mixed with basalt so firelight doesn't wash it out
        return basalt if rng.random() < 0.35 else smoked

    B = Batch()
    for sx in (-1, 1):
        zz, k = 0.15, 0
        while zz < 1.3:
            hh = rng.uniform(0.22, 0.3)
            ww = 0.36 if k % 2 else 0.3
            B.box(stone(), (ww, 0.6, hh - 0.015), (sx * (0.72 + (ww - 0.3) / 2), -0.3, zz + hh / 2))
            zz += hh
            k += 1
    # flat arch over the opening: wedge-cut voussoirs and a keystone
    for k in range(7):
        px = -0.6 + k * 0.2
        B.box(basalt if k == 3 else smoked, (0.19, 0.6, 0.36 if k == 3 else 0.3),
              (px, -0.31 if k == 3 else -0.3, 1.47 if k == 3 else 1.44), ry=math.radians(-px * 22))
    # chimney breast above the mantel, coursed and staggered, stepping back at a string course
    rowz, row = 1.86, 0
    while rowz < chimney_top:
        hh = 0.28
        px = -0.8 + (0.0 if row % 2 else 0.17)
        while px < 0.8:
            ww = min(rng.uniform(0.3, 0.45), 0.8 - px)
            if ww > 0.08:
                B.box(stone(), (ww - 0.015, 0.36, hh - 0.015),
                      (px + ww / 2, -0.18 + rng.uniform(-0.01, 0.01), rowz + hh / 2))
            px += ww
        rowz += hh
        row += 1
        if row == 1:
            p.append(box(name + "StringCourse", (1.72, 0.42, 0.08), (0, -0.2, rowz), basalt, bev=0.015))
    p += B.build(name + "Stones", bev=0.02)
    # mantel shelf with a bead and frieze, on two-step corbels
    p += [box(name + "Mantel", (2.3, 0.62, 0.09), (0, -0.36, 1.72), oak, bev=0.02),
          box(name + "MantelBead", (2.24, 0.05, 0.05), (0, -0.67, 1.66), oak, bev=0.02),
          box(name + "MantelFrieze", (2.0, 0.08, 0.12), (0, -0.6, 1.6), oak, bev=0.01)]
    for sx in (-1, 1):
        for k, (dy, dz, sz) in enumerate([(-0.55, 1.6, 0.14), (-0.59, 1.52, 0.1)]):
            p.append(box(f"{name}Corbel{sx}{k}", (0.16, 0.12 + 0.08 * k, sz), (sx * 0.95, dy, dz), oak,
                         bev=0.012))
        p.append(sphere(f"{name}CorbelBoss{sx}", 0.03, (sx * 0.95, -0.72, 1.52), oak, segs=10))
    if fire:
        iron = material("iron")
        for sx in (-1, 1):
            p.append(box(f"{name}Andiron{sx}", (0.04, 0.4, 0.04), (sx * 0.3, -0.3, 0.2), iron, bev=0))
        for i, (dx, tilt) in enumerate([(-0.12, 0.25), (0.12, -0.25), (0.0, 0.0)]):
            p.append(cyl(f"{name}Log{i}", 0.06, 0.7, (dx, -0.25, 0.27 + (0.08 if i == 2 else 0)),
                         material("wood"), rot=(0, math.pi / 2, tilt), verts=10))
        for i in range(9):
            hh = 0.25 + rng.uniform(0, 0.25)
            f = sphere(f"{name}Flame{i}", 0.08, (rng.uniform(-0.25, 0.25), -0.25, 0.35 + hh / 2),
                       material("fire"), scale=(0.8, 0.8, hh / 0.16), segs=10)
            f.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0)
            p.append(f)
        for i in range(10):
            p.append(sphere(f"{name}Ember{i}", 0.025, (rng.uniform(-0.3, 0.3), rng.uniform(-0.4, -0.15), 0.18),
                            material("ember"), segs=8))
        p.append(point_light(name + "Light", (0, -0.6, 0.45), 320, (1.0, 0.45, 0.15), radius=0.25))
    return group(name, p, loc, rot_z)
