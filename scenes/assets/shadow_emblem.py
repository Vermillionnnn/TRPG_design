"""The Shadow party's sigil: a black sun eclipsed in a silver corona and ray ring, pierced by a dagger.

    shadow_emblem.build("Crest", loc=(0, -0.08, 3.8), radius=0.42)   # on a wall facing -y

Origin is at the centre of the sigil, which lies in the local xz plane facing -y.
"""
import math

from assets.lib import as_material, box, cyl, group, material, sphere, torus


def build(name="ShadowEmblem", loc=(0, 0, 0), rot_z=0.0, *, radius=0.4, grip="shadow_trim"):
    """radius of the ray ring (m); grip: colour of the dagger grip."""
    r, rot = radius, (math.pi / 2, 0, 0)
    silver = material("silver")
    parts = [cyl(name + "Corona", r * 0.62, 0.01, (0, 0, 0), silver, rot=rot, verts=40, smooth=False),
             cyl(name + "Sun", r * 0.55, 0.012, (r * 0.08, -0.004, r * 0.05), material("void"), rot=rot,
                 verts=40, smooth=False),
             torus(name + "Ring", r * 0.8, r * 0.035, (0, 0, 0), silver, rot=rot)]
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        ln = r * (0.28 if k % 2 else 0.18)
        rr = r * 0.8 + ln / 2 + r * 0.05
        parts.append(box(f"{name}Ray{k}", (r * 0.05, 0.008, ln), (rr * math.cos(a), 0, rr * math.sin(a)),
                         silver, rot=(0, math.pi / 2 - a, 0), bev=0))
    # a dagger driven down through the eclipse
    parts += [box(name + "Blade", (r * 0.1, 0.01, r * 1.4), (0, -0.012, -r * 0.2), silver, bev=0),
              box(name + "Guard", (r * 0.5, 0.012, r * 0.07), (0, -0.014, r * 0.55), silver, bev=0),
              box(name + "Grip", (r * 0.07, 0.012, r * 0.3), (0, -0.014, r * 0.75),
                  as_material(grip, name + "GripMat"), bev=0),
              sphere(name + "Pommel", r * 0.06, (0, -0.014, r * 0.93), silver, segs=8)]
    return group(name, parts, loc, rot_z)
