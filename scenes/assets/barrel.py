"""Wooden barrel with two iron hoops and a dark lid.

    barrel.build("Barrel", loc=(1, 2, 0), radius=0.2, height=0.5)

Origin is under the barrel.
"""
from assets.lib import cyl, group, material


def build(name="Barrel", loc=(0, 0, 0), rot_z=0.0, *, radius=0.25, height=0.6):
    """radius, height in metres."""
    r, h = radius, height
    parts = [cyl(name + "Body", r, h, (0, 0, h / 2), material("wood"), verts=16)]
    for dz in (0.1, h - 0.1):
        parts.append(cyl(f"{name}Band{dz:.1f}", r + 0.01, 0.04, (0, 0, dz), material("iron"), verts=16))
    parts.append(cyl(name + "Lid", r - 0.02, 0.02, (0, 0, h), material("darkwood"), verts=16))
    return group(name, parts, loc, rot_z)
