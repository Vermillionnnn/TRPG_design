"""Little wooden rack holding a row of glowing vials.

    vial_rack.build("Vials", loc=(0.38, 0.23, 0.805), colors=["glass_potion_r", (1, 0.8, 0.1)])

Origin is under the rack centre; the vials stand in a row along local x.
"""
from assets.lib import as_material, box, cyl, group, material

COLORS = ["glass_potion_r", "glass_potion_b", "glass_potion_g", "arcane_cyan"]


def build(name="VialRack", loc=(0, 0, 0), rot_z=0.0, *, colors=COLORS):
    """colors: one entry per vial, each a material, palette key or (r, g, b)."""
    parts = [box(name + "Rack", (0.065 * len(colors), 0.08, 0.03), (0, 0, 0.03), material("darkwood"), bev=0.004)]
    for i, c in enumerate(colors):
        x = (i - (len(colors) - 1) / 2) * 0.065
        parts.append(cyl(f"{name}Vial{i}", 0.017, 0.13, (x, 0, 0.07),
                         as_material(c, f"{name}Liquid{i}", 0.1), verts=10))
    return group(name, parts, loc, rot_z)
