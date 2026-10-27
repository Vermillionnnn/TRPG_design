"""Wizard's staff with a glowing head: a crystal point or a ringed orb.

    s = staff.build("Staff", loc=(3, 3.7, 0.15), head="orb")
    s.rotation_euler = (math.radians(-5), 0, 0)   # lean it against a wall

Origin is at the foot of the staff; the staff stands along local +z.
"""
import math

from assets.lib import as_material, cone, cyl, group, material, point_light, sphere, torus

HEADS = {"crystal": ("glass_potion_b", (0.3, 0.5, 1.0), 4),
         "orb": ("arcane_purple", (0.7, 0.3, 1.0), 5)}


def build(name="Staff", loc=(0, 0, 0), rot_z=0.0, *, length=1.6, radius=0.022, head="crystal", wood="wood",
          glow=None, light=True):
    """head: "crystal" or "orb". wood / glow: material, palette key or (r, g, b)."""
    glow_key, light_color, energy = HEADS[head]
    glow = as_material(glow or glow_key, name + "Glow", 0.1)
    parts = [cyl(name + "Shaft", radius, length, (0, 0, length / 2),
                 as_material(wood, name + "Wood", 0.6), verts=10)]
    if head == "crystal":
        top = length + 0.07
        parts.append(cone(name + "Crystal", 0.05, 0.0, 0.16, (0, 0, top), glow, verts=6))
    else:
        top = length + 0.05
        parts.append(torus(name + "Ring", 0.07, 0.012, (0, 0, top), material("brass"),
                           rot=(math.radians(90), 0, 0)))
        parts.append(sphere(name + "Orb", 0.05, (0, 0, top), glow, segs=12))
    if light:
        parts.append(point_light(name + "Light", (0, -0.15, top), energy, light_color, radius=0.04))
    return group(name, parts, loc, rot_z)
