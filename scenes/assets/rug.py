"""Round rug with a gold border.

    rug.build("Rug", loc=(2.3, 1.7, 0.05), radius=1.15)

Origin is on the floor at the centre.
"""
from assets.lib import as_material, cyl, group, mat


def build(name="Rug", loc=(0, 0, 0), rot_z=0.0, *, radius=1.15, color="rug", border=(0.6, 0.42, 0.12)):
    """color: material, palette key or (r, g, b); border: (r, g, b) or None."""
    parts = [cyl(name + "Field", radius, 0.02, (0, 0, 0.01), as_material(color, name + "Wool", 1.0), verts=48)]
    if border:
        trim = mat("RugGold" if tuple(border) == (0.6, 0.42, 0.12) else name + "Trim", tuple(border), 0.8)
        parts.append(cyl(name + "Border", radius + 0.05, 0.015, (0, 0, 0.005), trim, verts=64))
    return group(name, parts, loc, rot_z)
