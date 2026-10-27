"""Pigeonhole cabinet for scrolls and sealed writs, on a three-drawer base
with brass label frames, carved pilaster strips and a cornice.

    scroll_cabinet.build("Cabinet", loc=(3.8, 2.6, 0), rot_z=-0.98)

Origin is on the floor under the middle of the cabinet; the open front faces
local -y (back against a wall at +y).
"""
import random

from assets.lib import Batch, as_material, box, group, material


def build(name="ScrollCabinet", loc=(0, 0, 0), rot_z=0.0, *, width=1.5, height=2.6, depth=0.5,
          cols=6, rows=8, wood="wood", trim="darkwood", rng=None):
    """height is the pigeonhole section above the 0.6 m drawer base."""
    rng = rng or random.Random(4)
    wood, trim = as_material(wood, name + "Wood", 0.6), as_material(trim, name + "Trim", 0.55)
    w, h, d = width, height, depth
    brass, paper = material("brass"), material("paper")
    p = [box(name + "Shelf", (w, d, 0.06), (0, 0, 0.6), wood),
         box(name + "Base", (w, d, 0.55), (0, 0, 0.3), wood),
         box(name + "Toe", (w + 0.06, d + 0.04, 0.1), (0, 0, 0.07), trim, bev=0.01),
         box(name + "Top", (w + 0.1, d + 0.06, 0.08), (0, 0, 0.6 + h), wood),
         box(name + "Cornice", (w + 0.18, d + 0.1, 0.06), (0, -0.02, 0.6 + h + 0.07), trim, bev=0.015)]
    for sx in (-1, 1):
        p.append(box(f"{name}Side{sx}", (0.05, d + 0.02, h + 0.6), (sx * (w / 2 + 0.025), 0, (h + 0.6) / 2),
                     trim, bev=0.01))
        p.append(box(f"{name}Pilaster{sx}", (0.07, 0.03, h - 0.1), (sx * (w / 2 + 0.03), -d / 2 - 0.01,
                                                                    0.6 + h / 2), wood, bev=0.01))
    for i in range(3):
        px = -w / 3 + i * w / 3
        p += [box(f"{name}Drawer{i}", (w / 3 - 0.04, 0.02, 0.42), (px, -d / 2 - 0.005, 0.32), wood,
                  bev=0.01),
              box(f"{name}Label{i}", (0.12, 0.012, 0.06), (px, -d / 2 - 0.02, 0.42), brass, bev=0.003),
              box(f"{name}LabelCard{i}", (0.1, 0.012, 0.045), (px, -d / 2 - 0.022, 0.42), paper, bev=0),
              box(f"{name}Pull{i}", (0.12, 0.02, 0.03), (px, -d / 2 - 0.025, 0.26), brass, bev=0.004)]
    # pigeonhole grid and the scrolls in it, merged per material
    B = Batch()
    cw, rh = w / cols, (h - 0.1) / rows
    for i in range(cols + 1):
        B.box(wood, (0.025, d, h), (-w / 2 + i * cw, 0, 0.6 + h / 2))
    for j in range(rows + 1):
        B.box(wood, (w, d, 0.02), (0, 0, 0.63 + j * rh))
    B.box(wood, (w, 0.02, h), (0, d / 2 - 0.01, 0.6 + h / 2))
    for i in range(cols):
        for j in range(rows):
            for k in range(rng.randint(0, 4)):
                px = -w / 2 + (i + 0.5) * cw + rng.uniform(-0.06, 0.06)
                pz = 0.65 + j * rh + 0.035 + (k // 2) * 0.05
                roll = material("old_parchment") if rng.random() < 0.8 else paper
                B.cyl(roll, 0.022, d * 0.9, (px, -0.03, pz), rx=1.5708, segs=8)
                if rng.random() < 0.3:
                    B.box(material("seal_wax"), (0.03, 0.005, 0.03), (px, -d / 2 + 0.02, pz))
    p += B.build(name + "Grid", bev=0.002)
    return group(name, p, loc, rot_z)
