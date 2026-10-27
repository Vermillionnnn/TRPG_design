"""Waterdeep street light: a glowing driftglobe hovering over the iron cradle of a lamp post.

    driftglobe.build("Lamp", loc=(2, 3, 0))                               # on a post
    driftglobe.build("Floating", loc=(2, 3, 3.0), post=False, energy=90)  # loose globe

Origin is under the post, or at the globe's centre when post=False.
"""
from assets.lib import cyl, group, material, point_light, sphere, torus


def build(name="Driftglobe", loc=(0, 0, 0), rot_z=0.0, *, height=2.3, post=True,
          color=(1.0, 0.82, 0.6), energy=55):
    """height of the post (m); color / energy of the globe's point light."""
    iron, parts, z = material("iron"), [], 0.0
    if post:
        parts += [cyl(name + "Post", 0.05, height, (0, 0, height / 2), iron, verts=10),
                  cyl(name + "Foot", 0.13, 0.14, (0, 0, 0.07), iron, verts=10),
                  torus(name + "Cradle", 0.14, 0.014, (0, 0, height + 0.02), iron, major_segments=24)]
        z = height + 0.22
    parts.append(sphere(name + "Globe", 0.1, (0, 0, z), material("globe"), segs=16))
    parts.append(point_light(name + "Light", (0, 0, z), energy, color, radius=0.1))
    return group(name, parts, loc, rot_z)
