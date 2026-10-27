"""Wooden tankard with an iron band, foam on top and a ring handle at +x.

    tankard.build("Tankard", loc=(0, 0, 0.82))
"""
import math

from assets.lib import cyl, group, mat, material, torus


def build(name="Tankard", loc=(0, 0, 0), rot_z=0.0, *, radius=0.05, height=0.13, foam=True):
    wood = material("wood")
    parts = [cyl(name + "Body", radius, height, (0, 0, height / 2), wood, verts=16),
             cyl(name + "Band", radius + 0.002, 0.015, (0, 0, height - 0.03), material("iron"), verts=16),
             torus(name + "Handle", 0.035, 0.01, (radius + 0.01, 0, height / 2), wood,
                   rot=(math.radians(90), 0, 0))]
    if foam:
        parts.append(cyl(name + "Foam", radius - 0.004, 0.01, (0, 0, height + 0.001),
                         mat("Foam", (0.95, 0.9, 0.75), 0.9), verts=16))
    return group(name, parts, loc, rot_z)
