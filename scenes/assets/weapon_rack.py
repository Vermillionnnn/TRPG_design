"""Floor-standing weapon rack: slotted base block, two posts and a notched top rail.

    weapon_rack.build("Rack", loc=(2.8, 3.8, 0.05))

Origin is on the floor under the rack centre. Weapons are placed by the scene:
blades stand in the slot block (top at z 0.18) and lean on the rail (z 0.8).
"""
from assets.lib import box, group, material


def build(name="WeaponRack", loc=(0, 0, 0), rot_z=0.0, *, width=1.0):
    dark = material("darkwood")
    parts = [box(name + "Base", (width, 0.25, 0.1), (0, 0, 0.05), dark),
             box(name + "SlotBlock", (width, 0.12, 0.08), (0, -0.02, 0.14), dark),
             box(name + "Top", (width, 0.1, 0.07), (0, 0.02, 0.8), dark),
             box(name + "TopFront", (width, 0.03, 0.07), (0, -0.08, 0.8), dark)]
    for i, sx in enumerate((-0.5, 0.5)):
        parts.append(box(f"{name}Post{i}", (0.08, 0.08, 0.85), (sx * width, 0.02, 0.45), dark))
    return group(name, parts, loc, rot_z)
