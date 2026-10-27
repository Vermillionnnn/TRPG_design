"""Round potion flask with a narrow neck; the glass glows faintly.

    potion.build("Potion", loc=(0, 0, 0), liquid="glass_potion_b")

Origin is under the flask.
"""
from assets.lib import as_material, cyl, group, sphere


def build(name="Potion", loc=(0, 0, 0), rot_z=0.0, *, radius=0.05, liquid="glass_potion_r"):
    """liquid: material, palette key (glass_potion_r / _b / _g) or (r, g, b)."""
    liquid = as_material(liquid, name + "Liquid", 0.1)
    parts = [sphere(name + "Flask", radius, (0, 0, radius), liquid),
             cyl(name + "Neck", radius * 0.3, radius * 1.2, (0, 0, radius * 2.4), liquid, verts=8)]
    return group(name, parts, loc, rot_z)
