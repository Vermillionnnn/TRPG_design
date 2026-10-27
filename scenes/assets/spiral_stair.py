"""Spiral stair: basalt wedge steps with oak treads round a stone newel, oak
balusters and a helical handrail.

    spiral_stair.build("Stair", loc=(-3.7, 0.9, 0), height=4.6)

Origin is on the floor at the centre of the newel. The first step points along
`start` (radians, from +x) and the stair turns counter-clockwise going up.
"""
import math

import bpy
from mathutils import Vector

from assets.lib import Batch, cyl, group, material, polar


def build(name="SpiralStair", loc=(0, 0, 0), rot_z=0.0, *, height=4.6, steps=22, turn=20.0,
          radius=1.0, start=math.radians(-60)):
    """turn: degrees each step rotates; radius: outer edge of the treads."""
    basalt, oak = material("blackstone"), material("darkwood")
    rise = height / steps
    dstep = math.radians(turn)
    r_mid = radius * 0.58
    p = [cyl(name + "Newel", 0.16, height + 0.3, (0, 0, (height + 0.3) / 2), material("stone"), verts=16)]
    B = Batch()
    for i in range(steps):
        a = start + i * dstep
        z = (i + 1) * rise
        x, y, _ = polar(r_mid, a)
        B.box(basalt, (radius * 0.9, 0.36, rise), (x, y, z - rise / 2), rz=a)
        B.box(oak, (radius * 0.92, 0.38, 0.04), (x, y, z + 0.02), rz=a)
        bx, by, _ = polar(radius * 0.98, a)
        B.box(oak, (0.05, 0.05, 0.9), (bx, by, z + 0.47), rz=a)
    p += B.build(name + "Steps", bev=0.01)
    pts = [Vector(polar(radius * 0.98, start + t / 4 * dstep, (t / 4 + 1) * rise + 0.92))
           for t in range(steps * 4 + 1)]
    cu = bpy.data.curves.new(name + "Handrail", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.03
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for pt, v in zip(sp.points, pts):
        pt.co = (*v, 1)
    rail = bpy.data.objects.new(name + "Handrail", cu)
    bpy.context.collection.objects.link(rail)
    rail.data.materials.append(oak)
    p.append(rail)
    return group(name, p, loc, rot_z)
