"""Stone fireplace with chimney, wooden mantel, logs, flickering flames and embers.

    fireplace.build("Fireplace", loc=(0, 2.55, 0), rot_z=math.pi / 2)   # on a wall at x = 0

Origin is on the floor at the wall face, under the middle of the fireplace; the
hearth opens toward local -y. Flames are named <name>Flame<i> / <name>FlameCore<i>
and the fire light <name>Light, so a scene can animate them.
"""
import math
import random

from assets.lib import box, cyl, group, mat, material, point_light, sphere


def build(name="Fireplace", loc=(0, 0, 0), rot_z=0.0, *, fire=True, rng=None):
    """fire adds logs, flames, embers and a warm light. rng: random source for the flames (default seed 0)."""
    rng = rng or random.Random(0)
    stone, dark = material("stone"), material("darkwood")
    parts = [box(name + "Base", (1.2, 0.55, 0.12), (0, -0.27, 0.11), stone, bev=0.03),
             box(name + "SideA", (0.22, 0.45, 1.1), (-0.49, -0.22, 0.6), stone, bev=0.03),
             box(name + "SideB", (0.22, 0.45, 1.1), (0.49, -0.22, 0.6), stone, bev=0.03),
             box(name + "Lintel", (1.2, 0.5, 0.25), (0, -0.25, 1.25), stone, bev=0.03),
             box(name + "Mantel", (1.4, 0.6, 0.08), (0, -0.3, 1.41), dark),
             box(name + "Chimney", (0.9, 0.4, 1.6), (0, -0.2, 2.25), stone, bev=0.03),
             box(name + "Back", (0.8, 0.05, 0.95), (0, -0.03, 0.65), mat("Soot", (0.03, 0.025, 0.02), 1))]
    if fire:
        for i, (dx, rz) in enumerate([(-0.15, 0.3), (0.15, -0.3), (0.0, 0.0)]):
            parts.append(cyl(f"{name}Log{i}", 0.06, 0.55, (dx, -0.25, 0.22 + (0.08 if i == 2 else 0)),
                             material("wood"), rot=(math.radians(90), 0, rz - math.pi / 2), verts=10))
        core = mat("FireCore", (0, 0, 0), 1, emit=(1.0, 0.42, 0.03), emit_strength=4)
        for i in range(9):
            h = 0.25 + rng.uniform(0, 0.25)
            depth = 0.25 + rng.uniform(-0.05, 0.05)
            loc_f = (rng.uniform(-0.22, 0.22), -depth, 0.3 + h / 2)
            f = sphere(f"{name}Flame{i}", 0.08, loc_f, material("fire"), scale=(0.8, 0.8, h / 0.16), segs=10)
            f.rotation_euler = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), -math.pi / 2)
            parts.append(f)
            if i < 4:
                parts.append(sphere(f"{name}FlameCore{i}", 0.045, (loc_f[0], loc_f[1], loc_f[2] - 0.04), core,
                                    scale=(1, 1, h / 0.14), segs=8))
        for i in range(10):
            depth = 0.25 + rng.uniform(-0.12, 0.12)
            parts.append(sphere(f"{name}Ember{i}", 0.03, (rng.uniform(-0.3, 0.3), -depth, 0.19),
                                material("ember"), segs=8))
        parts.append(point_light(name + "Light", (0, -0.6, 0.6), 160, (1.0, 0.5, 0.18), radius=0.25))
    return group(name, parts, loc, rot_z)
