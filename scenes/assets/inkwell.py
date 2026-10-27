"""Glass inkwell with a quill standing in it.

    inkwell.build("Inkwell", loc=(0.3, 2.65, 0.786))

Origin is under the inkwell.
"""
import math

from mathutils import Euler, Vector

from assets.lib import cyl, group, material, sphere


def build(name="Inkwell", loc=(0, 0, 0), rot_z=0.0, *, radius=0.04, quill=True):
    p = [cyl(name + "Glass", radius, 0.06, (0, 0, 0.03), material("clear_glass"), verts=16),
         cyl(name + "Ink", radius * 0.8, 0.04, (0, 0, 0.022), material("black_ink"), verts=16)]
    if quill:
        # shaft leans out of the well; the vane runs along its upper half
        tilt = (math.radians(25), 0, math.radians(30))
        axis = Euler(tilt).to_matrix() @ Vector((0, 0, 1))
        foot = Vector((0.0, 0.0, 0.03))
        p.append(cyl(name + "Shaft", 0.004, 0.3, tuple(foot + axis * 0.15), material("paper"), rot=tilt,
                     verts=6))
        vane = sphere(name + "Vane", 0.03, tuple(foot + axis * 0.21), material("paper"), scale=(0.3, 1, 3.0),
                      segs=10)
        vane.rotation_euler = tilt
        p.append(vane)
    return group(name, p, loc, rot_z)
