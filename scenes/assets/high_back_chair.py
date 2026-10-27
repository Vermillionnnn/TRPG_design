"""Carved high-backed chair: turned front legs and finials, tufted back pad,
scrolled arms and a pointed crest with a glowing gem (the Blackstaff's seat).

    high_back_chair.build("Throne", loc=(0, 3.3, 0))

Origin is on the floor under the seat centre; the backrest sits at local +y,
so the sitter faces local -y.
"""
from assets.lib import (as_material, box, group, lathe, material, mesh_obj, sphere)

TURNED_LEG = [(0.03, 0.0), (0.038, 0.03), (0.03, 0.06), (0.026, 0.12), (0.034, 0.2),
              (0.036, 0.23), (0.026, 0.27), (0.022, 0.36), (0.03, 0.42), (0.034, 0.46)]
FINIAL = [(0.03, 0.0), (0.035, 0.015), (0.02, 0.03), (0.045, 0.07), (0.04, 0.1), (0.015, 0.13),
          (0.022, 0.15), (0.0, 0.2)]
ARM_POST = [(0.02, 0.0), (0.028, 0.03), (0.016, 0.1), (0.026, 0.17), (0.02, 0.22)]


def build(name="HighBackChair", loc=(0, 0, 0), rot_z=0.0, *, back_height=1.45, wood="darkwood",
          cushion="velvet", gem="arcane_purple", tufts=True):
    """back_height in metres above the seat; gem=None leaves the crest plain."""
    wood = as_material(wood, name + "Wood", 0.55)
    cushion = as_material(cushion, name + "Cushion")
    seat_h = 0.46
    bh = back_height
    p = [box(name + "Seat", (0.6, 0.54, 0.06), (0, 0, seat_h - 0.03), wood, bev=0.01),
         box(name + "Apron", (0.58, 0.5, 0.1), (0, 0, seat_h - 0.1), wood, bev=0.008),
         box(name + "Cushion", (0.52, 0.48, 0.08), (0, -0.01, seat_h + 0.04), cushion, bev=0.035),
         box(name + "Stretcher", (0.5, 0.03, 0.04), (0, -0.23, 0.12), wood, bev=0.005)]
    for px in (-0.26, 0.26):
        p.append(lathe(f"{name}FrontLeg{px}", TURNED_LEG, (px, -0.23, 0), wood, segs=16))
        p.append(box(f"{name}BackLeg{px}", (0.06, 0.06, seat_h - 0.05), (px, 0.23, (seat_h - 0.05) / 2),
                     wood, bev=0.008))
    for px in (-0.27, 0.27):
        p.append(box(f"{name}Stile{px}", (0.07, 0.07, bh), (px, 0.25, seat_h + bh / 2), wood, bev=0.01))
        p.append(lathe(f"{name}Finial{px}", FINIAL, (px, 0.25, seat_h + bh), wood, segs=16))
    p.append(box(name + "BackPanel", (0.48, 0.04, bh - 0.25), (0, 0.26, seat_h + bh / 2 + 0.02),
                 wood, bev=0.006))
    p.append(box(name + "BackPad", (0.42, 0.05, bh - 0.4), (0, 0.225, seat_h + bh / 2 + 0.02),
                 cushion, bev=0.02))
    if tufts:
        for i in range(3):
            for j in range(5):
                p.append(sphere(f"{name}Tuft{i}{j}", 0.01,
                                (-0.12 + i * 0.12, 0.198, seat_h + 0.35 + j * (bh - 0.6) / 4),
                                material("pewter"), segs=6))
    p.append(box(name + "TopRail", (0.6, 0.08, 0.1), (0, 0.25, seat_h + bh - 0.02), wood, bev=0.015))
    for px in (-0.31, 0.31):
        p.append(box(f"{name}Arm{px}", (0.07, 0.52, 0.045), (px, -0.01, seat_h + 0.26), wood, bev=0.012))
        p.append(sphere(f"{name}ArmScroll{px}", 0.04, (px, -0.27, seat_h + 0.26), wood, segs=12))
        p.append(lathe(f"{name}ArmPost{px}", ARM_POST, (px, -0.22, seat_h + 0.02), wood, segs=12))
    # pointed crest board above the top rail
    zc = seat_h + bh + 0.03
    verts = [(-0.3, 0.24, zc), (0.3, 0.24, zc), (0.0, 0.24, zc + 0.27)]
    verts += [(x, y + 0.02, z) for x, y, z in verts]
    p.append(mesh_obj(name + "Crest", verts, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2),
                                              (2, 5, 3, 0)], wood, smooth_angle=0))
    if gem:
        p.append(sphere(name + "CrestGem", 0.035, (0, 0.225, zc + 0.1),
                        as_material(gem, name + "Gem", 0.2), segs=12))
    return group(name, p, loc, rot_z)
