"""Small work desk with four legs and a low shelf.

    desk.build("Desk", loc=(0.3, 0.45, 0), rot_z=math.pi / 2)

Origin is on the floor under the desk centre; the long side runs along local x.
"""
from assets.lib import box, group, material


def build(name="Desk", loc=(0, 0, 0), rot_z=0.0, *, width=0.8, depth=0.48, height=0.78):
    """height is the centre of the desktop; its top surface is 2.5 cm higher."""
    dark = material("darkwood")
    parts = [box(name + "Top", (width, depth, 0.05), (0, 0, height), material("wood"), bev=0.01)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(f"{name}Leg{sx}{sy}", (0.05, 0.05, height - 0.03),
                             (sx * (width / 2 - 0.05), sy * (depth / 2 - 0.05), (height - 0.03) / 2), dark))
    parts.append(box(name + "Shelf", (width - 0.08, depth - 0.06, 0.03), (0, 0, 0.2), dark))
    return group(name, parts, loc, rot_z)
