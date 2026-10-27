"""Round pedestal table with a dark rim and four crossed feet.

    round_table.build("Table", loc=(2.3, 1.7, 0.05))

Origin is on the floor under the table centre.
"""
import math

from assets.lib import box, cyl, group, material


def build(name="RoundTable", loc=(0, 0, 0), rot_z=0.0, *, radius=0.85, height=0.73):
    """height is the tabletop centre above the floor (top surface ~4 cm higher)."""
    wood, dark = material("wood"), material("darkwood")
    parts = [cyl(name + "Top", radius, 0.08, (0, 0, height), wood, verts=48),
             cyl(name + "Rim", radius + 0.01, 0.03, (0, 0, height - 0.05), dark, verts=48),
             cyl(name + "Pedestal", 0.12, height - 0.03, (0, 0, (height - 0.03) / 2 - 0.02), dark, verts=16)]
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        parts.append(box(f"{name}Foot{i}", (0.55, 0.1, 0.08), (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.03),
                         dark, rot=(0, 0, a)))
    return group(name, parts, loc, rot_z)
