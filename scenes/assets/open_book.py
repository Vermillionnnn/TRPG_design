"""Open book: two covers with page blocks, tilted up like a V.

    open_book.build("Spellbook", loc=(2.45, 1.2, 0.835), rot_z=-0.26, cover="purple")

Origin is at the middle of the spine; the spine runs along local y.
"""
import math

from assets.lib import as_material, box, group, material


def build(name="OpenBook", loc=(0, 0, 0), rot_z=0.0, *, width=0.18, depth=0.25, thickness=0.015,
          angle=8.0, cover="purple"):
    """width of one cover, depth along the spine, cover thickness (m); angle each half tilts up (deg).
    cover: material, palette key or (r, g, b).
    """
    cover = as_material(cover, name + "Cover", 0.8)
    bev = 0.004 * thickness / 0.015
    parts = []
    for side in (-1, 1):
        rot = (0, side * math.radians(-angle), 0)
        parts.append(box(f"{name}Cover{side}", (width, depth, thickness), (side * width / 2, 0, 0),
                         cover, rot=rot, bev=bev))
        parts.append(box(f"{name}Page{side}", (width - 0.02, depth - 0.02, thickness * 4 / 3),
                         (side * (width / 2 - 0.005), 0, thickness), material("parchment"), rot=rot, bev=bev))
    return group(name, parts, loc, rot_z)
