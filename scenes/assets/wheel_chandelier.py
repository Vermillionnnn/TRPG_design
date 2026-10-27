"""Wrought-iron wheel chandelier: rim, hub and spokes, candles in iron cups,
three chains up to a hook, and a warm light.

    wheel_chandelier.build("Chandelier", loc=(0, 2.3, 4.7))

Origin is the hook at the top of the chains (put it on the ceiling or a beam);
the wheel hangs `drop` metres below. The light is <name>Light.
"""
import math

from assets import candle
from assets.lib import cyl, group, material, point_light, shell

from mathutils import Vector


def build(name="WheelChandelier", loc=(0, 0, 0), rot_z=0.0, *, radius=0.9, candles=10, drop=1.1,
          light=380.0):
    """light: watts of the warm point light at the wheel (0 for none)."""
    iron = material("iron")
    z = -drop
    p = [shell(name + "Rim", radius, radius - 0.06, z - 0.03, z + 0.03, iron, segs=64),
         shell(name + "Hub", 0.12, 0.0, z - 0.06, z + 0.06, iron, segs=16)]
    for i in range(6):
        a = 2 * math.pi * i / 6
        o = cyl(f"{name}Spoke{i}", 0.0125, radius - 0.1, (0.5 * (radius - 0.05) * math.cos(a),
                                                          0.5 * (radius - 0.05) * math.sin(a), z),
                iron, rot=(0, math.pi / 2, a), verts=8)
        p.append(o)
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        p0 = Vector(((radius - 0.03) * math.cos(a), (radius - 0.03) * math.sin(a), z))
        d = Vector((0, 0, 0)) - p0
        o = cyl(f"{name}Chain{i}", 0.008, d.length, tuple(p0 + d / 2), iron, verts=6)
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        p.append(o)
    for i in range(candles):
        a = 2 * math.pi * i / candles
        px, py = (radius - 0.03) * math.cos(a), (radius - 0.03) * math.sin(a)
        p.append(cyl(f"{name}Cup{i}", 0.04, 0.03, (px, py, z + 0.045), iron, verts=10))
        p.append(candle.build(f"{name}Candle{i}", (px, py, z + 0.06), height=0.12 + 0.04 * (i % 3),
                              light=False))
    if light:
        p.append(point_light(name + "Light", (0, 0, z + 0.2), light, (1.0, 0.6, 0.28), radius=radius))
    return group(name, p, loc, rot_z)
