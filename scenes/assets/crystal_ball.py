"""Crystal ball held by three brass claws on a small stand, with an inner light.

    crystal_ball.build("Orb", loc=(1.8, 1.35, 0.82))

Origin is under the stand. The light is called <name>Light.
"""
import math

from assets.lib import as_material, box, cone, group, material, point_light, sphere


def build(name="CrystalBall", loc=(0, 0, 0), rot_z=0.0, *, radius=0.085, glass="arcane_purple",
          light=True, light_color=(0.65, 0.35, 1.0)):
    """glass: material, palette key or (r, g, b) for the ball."""
    brass = material("brass")
    parts = [cone(name + "Stand", 0.07, 0.03, 0.06, (0, 0, 0.03), brass, verts=16)]
    for k in range(3):
        a = k * 2 * math.pi / 3
        parts.append(box(f"{name}Claw{k}", (0.012, 0.012, 0.08),
                         (0.05 * math.cos(a), 0.05 * math.sin(a), 0.08), brass, bev=0))
    parts.append(sphere(name + "Ball", radius, (0, 0, 0.055 + radius), as_material(glass, name + "Glass", 0.1),
                        segs=24))
    if light:
        parts.append(point_light(name + "Light", (0, 0, 0.195 + radius), 8, light_color, radius=0.05))
    return group(name, parts, loc, rot_z)
