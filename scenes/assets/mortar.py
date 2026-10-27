"""Stone mortar with a pestle leaning in it.

    mortar.build("Mortar", loc=(0.18, 0.4, 0.805))

Origin is under the mortar.
"""
import math

from assets.lib import cyl, group, material


def build(name="Mortar", loc=(0, 0, 0), rot_z=0.0, *, radius=0.05):
    stone = material("stone")
    parts = [cyl(name + "Bowl", radius, radius * 1.2, (0, 0, radius * 0.6), stone, verts=16),
             cyl(name + "Pestle", 0.012, 0.13, (0, 0.01, radius * 1.6), stone,
                 rot=(math.radians(25), 0, 0), verts=8)]
    return group(name, parts, loc, rot_z)
