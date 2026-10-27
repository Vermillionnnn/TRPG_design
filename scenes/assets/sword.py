"""Longsword pointing up along local +z.

    s = sword.build("Sword", loc=(0, 0, 1), length=0.9)
    s.rotation_euler = (math.radians(177), 0, 0)   # point down, e.g. in a rack

Origin is at the top of the grip, just under the guard.
"""
from assets.lib import box, cyl, group, material, sphere


def build(name="Sword", loc=(0, 0, 0), rot_z=0.0, *, length=0.9):
    """length is the whole sword, pommel to tip, roughly."""
    brass = material("brass")
    parts = [
        box(name + "Blade", (0.07, 0.015, length * 0.68), (0, 0, length * 0.42), material("steel"), bev=0.004),
        box(name + "Guard", (0.24, 0.04, 0.04), (0, 0, length * 0.07), brass, bev=0.005),
        cyl(name + "Grip", 0.016, length * 0.14, (0, 0, -length * 0.02), material("leather"), verts=8),
        sphere(name + "Pommel", 0.03, (0, 0, -length * 0.1), brass, segs=8),
    ]
    return group(name, parts, loc, rot_z)
