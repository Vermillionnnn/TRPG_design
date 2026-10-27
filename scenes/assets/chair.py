"""Wooden spindle-back chair (the one around the homebase table).

    from assets import chair
    chair.build("Chair0", loc=(1, 2, 0), rot_z=0.5, cushion=(0.22, 0.05, 0.35))

Origin is on the floor under the seat centre; the backrest sits at local +y,
so the sitter faces local -y.
"""
import math

from assets.lib import as_material, box, cyl, group


def build(name="Chair", loc=(0, 0, 0), rot_z=0.0, *,
          seat_height=0.45, width=0.45, back_height=0.55, back_tilt=6.0,
          spindles=3, leg_radius=0.025, wood="wood", cushion=None):
    """Build the chair and return its root empty.

    seat_height, width, back_height are in metres; back_tilt in degrees.
    wood, cushion: material, palette key or (r, g, b); cushion=None leaves the seat bare.
    """
    wood = as_material(wood, name + "Wood", 0.6)
    cushion = as_material(cushion, name + "CushionMat")
    off = width / 2 - 0.035                  # leg offset from the centre
    k = seat_height / 0.45                   # stretchers follow the seat height
    tilt = (math.radians(-back_tilt), 0, 0)
    back_z = seat_height + 0.015             # bottom of the back posts

    parts = [box(name + "Seat", (width, width, 0.05), (0, 0, seat_height), wood, bev=0.015)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(f"{name}Leg{sx}{sy}", leg_radius, seat_height,
                             (sx * off, sy * off, seat_height / 2), wood, verts=10))
        # side stretchers between legs
        parts.append(box(f"{name}Stretch{sx}", (0.025, 2 * off - 0.02, 0.025),
                         (sx * off, 0, 0.13 * k), wood))
    parts.append(box(name + "StretchF", (2 * off - 0.02, 0.025, 0.025), (0, -off, 0.18 * k), wood))
    for sx in (-1, 1):
        parts.append(box(f"{name}Back{sx}", (0.05, 0.05, back_height),
                         (sx * off, off + 0.01, back_z + back_height / 2), wood, rot=tilt))
    parts.append(box(name + "BackRail", (width - 0.02, 0.045, 0.12),
                     (0, off + 0.04, back_z + back_height - 0.055), wood, rot=tilt, bev=0.015))
    span = 2 * off - 0.18
    for i in range(spindles):
        x = (i - (spindles - 1) / 2) * (span / (spindles - 1) if spindles > 1 else 0)
        parts.append(box(f"{name}Spindle{i}", (0.025, 0.025, back_height - 0.15),
                         (x, off + 0.02, back_z + (back_height - 0.15) / 2 + 0.025), wood, rot=tilt))
    if cushion:
        parts.append(box(name + "Cushion", (width - 0.05, width - 0.05, 0.06),
                         (0, 0, seat_height + 0.05), cushion, bev=0.025))
    return group(name, parts, loc, rot_z)
