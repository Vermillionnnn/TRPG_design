"""Bookcase curved to follow a round wall: plinth with toe, shelves with front
lips, dividers, a two-step crown, and rows of books (some leaning, gilt bands
on the thicker spines).

    curved_bookshelf.build("Shelf", loc=polar(4.86, a), rot_z=a - math.pi / 2, radius=4.86)

Origin is on the floor at the middle of the back; the shelf is concave toward
local -y, centred on a circle of `radius` whose centre is at (0, -radius).
Place it at polar(radius, a) with rot_z = a - pi/2 to hug a wall of that radius.
"""
import math
import random

from assets.lib import Batch, as_material, box, group, material, polar, shell


def build(name="CurvedBookshelf", loc=(0, 0, 0), rot_z=0.0, *, radius=4.86, arc=25.0, height=4.05,
          depth=0.42, shelf_gap=0.47, sections=2, wood="darkwood", books=None, rng=None):
    """arc: degrees the case spans; sections: bays between the dividers.
    books: list of cover materials (default the palette's bookcols)."""
    rng = rng or random.Random(9)
    wood = as_material(wood, name + "Wood", 0.55)
    gilt = material("brass")
    books = books or material("bookcols")
    C = (0, -radius, 0)
    r_back, r_front = radius, radius - depth
    a0 = math.pi / 2 - math.radians(arc) / 2
    a1 = math.pi / 2 + math.radians(arc) / 2
    top = height

    def at(r, a, z):
        x, y, _ = polar(r, a)
        return (x + C[0], y + C[1], z)

    p = [shell(name + "Back", r_back, r_back - 0.03, 0.1, top, wood, arc=(a0, a1), segs=64, loc=C),
         shell(name + "Plinth", r_front + 0.02, r_back, 0.06, 0.24, wood, arc=(a0 - 0.01, a1 + 0.01),
               segs=64, loc=C),
         shell(name + "PlinthToe", r_front - 0.01, r_front - 0.03, 0.06, 0.1, wood,
               arc=(a0 - 0.01, a1 + 0.01), segs=64, loc=C),
         shell(name + "Crown", r_front - 0.06, r_back, top, top + 0.08, wood, arc=(a0 - 0.02, a1 + 0.02),
               segs=64, loc=C, r_out_top=r_front - 0.1),
         shell(name + "CrownCap", r_front - 0.11, r_back, top + 0.08, top + 0.12, wood,
               arc=(a0 - 0.025, a1 + 0.025), segs=64, loc=C)]
    divs = [a0 + (a1 - a0) * k / sections for k in range(sections + 1)]
    B = Batch()
    zz, k = 0.24, 0
    while zz < top:
        p.append(shell(f"{name}Board{k}", r_front, r_back, zz, zz + 0.03, wood, arc=(a0, a1), segs=64, loc=C))
        p.append(shell(f"{name}Lip{k}", r_front + 0.005, r_front - 0.012, zz - 0.02, zz + 0.03, wood,
                       arc=(a0, a1), segs=64, loc=C))
        if zz + shelf_gap > top:
            break
        for d0, d1 in zip(divs, divs[1:]):
            a = d0 + 0.012
            while a < d1 - 0.015:
                tw = rng.uniform(0.025, 0.07)
                th = rng.uniform(0.26, 0.42)
                td = rng.uniform(0.2, 0.3)
                rm = r_back - 0.03 - td / 2
                da = tw / rm
                if rng.random() < 0.05:
                    a += da * 2.5
                    continue
                lean = rng.uniform(-0.15, 0.15) if rng.random() < 0.12 else 0
                am = a + da / 2
                zc = zz + 0.03 + th / 2 - abs(lean) * 0.05
                B.box(rng.choice(books), (td, tw, th), at(rm, am, zc), rz=am, rx=lean)
                if tw > 0.04 and not lean:
                    for bz in (-0.36, 0.34):
                        B.box(gilt, (0.004, tw + 0.002, 0.008), at(rm - td / 2, am, zc + bz * th), rz=am)
                a += da * 1.03
        zz += shelf_gap
        k += 1
    p += B.build(name + "Books", bev=0.003)
    for i, a in enumerate(divs):
        p.append(box(f"{name}Divider{i}", (r_back - r_front, 0.045, top - 0.1),
                     at((r_back + r_front) / 2, a, (top + 0.1) / 2), wood, rot=(0, 0, a), bev=0.008))
    return group(name, p, loc, rot_z)
