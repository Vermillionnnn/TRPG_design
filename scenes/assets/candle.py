"""Wax candle with a flame and (optionally) a small warm point light.

    candle.build("Candle", loc=(0, 0, 0), height=0.15)

Origin is under the candle; the flame sits on top.
"""
from assets.lib import cyl, group, material, point_light, sphere


def build(name="Candle", loc=(0, 0, 0), rot_z=0.0, *, height=0.15, radius=0.025, light=True):
    """height, radius in metres; light adds a point light just above the flame."""
    parts = [cyl(name + "Wax", radius, height, (0, 0, height / 2), material("wax"), verts=12),
             sphere(name + "Flame", 0.018, (0, 0, height + 0.025), material("flame"),
                    scale=(1, 1, 1.8), segs=8)]
    if light:
        parts.append(point_light(name + "Light", (0, 0, height + 0.08), 6, (1.0, 0.6, 0.25),
                                 radius=0.02))
    return group(name, parts, loc, rot_z)
