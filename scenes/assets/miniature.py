"""Tabletop miniature: iron base, cone body and a small head.

    miniature.build("Mini", loc=(2.1, 1.8, 0.83), color="red")

Origin is under the base.
"""
from assets.lib import as_material, cone, cyl, group, material, sphere


def build(name="Miniature", loc=(0, 0, 0), rot_z=0.0, *, color="blue"):
    """color: material, palette key or (r, g, b) for the body."""
    parts = [cyl(name + "Base", 0.025, 0.01, (0, 0, 0.005), material("iron"), verts=12),
             cone(name + "Body", 0.02, 0.008, 0.06, (0, 0, 0.04), as_material(color, name + "Paint", 0.9), verts=8),
             sphere(name + "Head", 0.011, (0, 0, 0.075), material("wax"), segs=8)]
    return group(name, parts, loc, rot_z)
