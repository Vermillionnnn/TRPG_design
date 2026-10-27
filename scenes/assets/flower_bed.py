"""Raised flower bed: stone kerb, dark soil and a patch of flowers.

    flower_bed.build("Bed", loc=(5, 7, 0.08), width=1.6, depth=0.45, colors=["bloom_red", "bloom_white"])

Origin is under the centre of the bed; width runs along x.
"""
from assets import flower_patch
from assets.lib import box, group, material


def build(name="FlowerBed", loc=(0, 0, 0), rot_z=0.0, *, width=1.2, depth=0.5,
          colors=("bloom_red", "bloom_yellow", "bloom_white"), count=None, rng=None):
    """width / depth of the kerb (m); count: flowers (default about 22 per square metre)."""
    parts = [box(name + "Kerb", (width, depth, 0.22), (0, 0, 0.07), material("flag"), bev=0.03),
             box(name + "Soil", (width - 0.1, depth - 0.1, 0.04), (0, 0, 0.17), material("soil"), bev=0),
             flower_patch.build(name + "Flowers", (0, 0, 0.18), rx=width / 2 - 0.1, ry=depth / 2 - 0.1,
                                count=count or int(width * depth * 22), colors=colors, rng=rng)]
    return group(name, parts, loc, rot_z)
