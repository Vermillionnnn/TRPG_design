"""Straw training dummy: burlap body and head on a cross post, a painted target on the chest.

    training_dummy.build("Dummy", loc=(3, 2, 0), rot_z=math.pi / 2)

Origin is under the post; the chest mark faces -y.
"""
from assets.lib import as_material, box, cyl, group, material, sphere


def build(name="Dummy", loc=(0, 0, 0), rot_z=0.0, *, mark="red_paint"):
    """mark: colour of the painted cross (material, palette key or (r, g, b)); None for none."""
    log, burlap, straw = material("log"), material("burlap"), material("straw")
    parts = [cyl(name + "Post", 0.06, 1.7, (0, 0, 0.85), log, verts=10),
             box(name + "Arms", (0.9, 0.07, 0.07), (0, 0, 1.3), log),
             sphere(name + "Body", 0.24, (0, 0, 1.1), burlap, scale=(1, 0.75, 1.35), segs=14),
             sphere(name + "Head", 0.14, (0, 0, 1.62), burlap, segs=12),
             cyl(name + "Belt", 0.2, 0.05, (0, 0, 0.95), material("rope"), verts=14),
             box(name + "Foot", (0.6, 0.1, 0.08), (0, 0, 0.12), log),
             box(name + "Foot2", (0.1, 0.6, 0.08), (0, 0, 0.12), log)]
    for sx in (-1, 1):
        parts.append(sphere(f"{name}Straw{sx}", 0.06, (sx * 0.47, 0, 1.3), straw, scale=(1.4, 1, 1), segs=8))
    if mark:
        paint = as_material(mark, name + "MarkMat")
        parts.append(box(name + "MarkV", (0.03, 0.02, 0.22), (0, -0.18, 1.12), paint, bev=0))
        parts.append(box(name + "MarkH", (0.22, 0.02, 0.03), (0, -0.18, 1.12), paint, bev=0))
    return group(name, parts, loc, rot_z)
