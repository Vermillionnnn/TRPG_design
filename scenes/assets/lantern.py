"""Square iron lantern with a glowing core and a warm point light.

    lantern.build("Lantern", loc=(1, 0, 1.8), energy=25)

Origin is under the lantern's base plate; hang it from a bracket or a wall.
"""
from assets.lib import as_material, box, cone, group, material, point_light

BASE = 0.125   # origin to the centre of the glow


def build(name="Lantern", loc=(0, 0, 0), rot_z=0.0, *, energy=40, color=(1.0, 0.62, 0.28), glow="flame"):
    """energy (W) and colour of the point light; energy 0 leaves the light out.
    glow: material or palette key of the core (e.g. "arcane_cyan" for a magic light)."""
    iron, z = material("iron"), BASE
    parts = [box(name + "Cap", (0.16, 0.16, 0.04), (0, 0, z + 0.12), iron, bev=0.005),
             cone(name + "Top", 0.1, 0.0, 0.08, (0, 0, z + 0.18), iron, verts=4, smooth=False),
             box(name + "Base", (0.14, 0.14, 0.03), (0, 0, z - 0.11), iron, bev=0.004),
             box(name + "Glow", (0.1, 0.1, 0.18), (0, 0, z), as_material(glow, name + "GlowMat"), bev=0.01)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(f"{name}Bar{sx}{sy}", (0.015, 0.015, 0.22), (sx * 0.065, sy * 0.065, z), iron, bev=0))
    if energy:
        parts.append(point_light(name + "Light", (0, 0, z), energy, color, radius=0.08))
    return group(name, parts, loc, rot_z)
