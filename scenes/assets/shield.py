"""Round shield with a boss and an optional metal rim, standing on its edge.

    shield.build("Shield", loc=(0, 0, 0), color="red")

Origin is under the bottom edge; the face looks toward local -y.
"""
import math

from assets.lib import as_material, cyl, group, torus


def build(name="Shield", loc=(0, 0, 0), rot_z=0.0, *, radius=0.3, color="red", boss="iron", rim=None):
    """color / boss / rim: material, palette key or (r, g, b); rim=None leaves the edge bare."""
    up = (math.radians(90), 0, 0)
    parts = [cyl(name + "Face", radius, 0.05, (0, 0, radius), as_material(color, name + "Paint", 0.9),
                 rot=up, verts=32),
             cyl(name + "Boss", 0.07, 0.07, (0, -0.03, radius), as_material(boss, name + "BossMetal"),
                 rot=up, verts=16)]
    if rim:
        parts.append(torus(name + "Rim", radius, 0.025, (0, -0.01, radius), as_material(rim, name + "RimMetal"),
                           rot=up))
    return group(name, parts, loc, rot_z)
