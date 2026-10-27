"""Heavy two-pedestal writing desk: oak top with a leather inlay, drawers on the
sitter's side, studded panels facing the visitors.

    writing_desk.build("Desk", loc=(0, 2.45, 0))

Origin is on the floor under the middle of the desk; the visitors' side
(studded panels) faces local -y and the drawers face +y. The top surface is at
`height` + 0.006 (the leather inlay).
"""
from assets.lib import as_material, box, group, material, sphere


def build(name="WritingDesk", loc=(0, 0, 0), rot_z=0.0, *, width=2.3, depth=1.05, height=0.78,
          top="wood", body="darkwood", leather="desk_leather"):
    top, body = as_material(top, name + "Top", 0.6), as_material(body, name + "Body", 0.55)
    leather = as_material(leather, name + "Leather")
    W, D, H = width, depth, height
    iron = material("iron")
    p = [box(name + "Top", (W, D, 0.08), (0, 0, H - 0.04), top, bev=0.02),
         box(name + "TopEdge", (W + 0.06, D + 0.06, 0.04), (0, 0, H - 0.1), body, bev=0.012),
         box(name + "Leather", (W - 0.3, D - 0.25, 0.006), (0, 0.02, H + 0.003), leather, bev=0),
         box(name + "Modesty", (W - 1.3, 0.04, 0.4), (0, -D / 2 + 0.08, H - 0.32), body),
         box(name + "Apron", (W - 0.1, 0.04, 0.1), (0, -D / 2 + 0.05, H - 0.17), body)]
    for sx in (-1, 1):
        px = sx * (W / 2 - 0.35)
        p.append(box(f"{name}Pedestal{sx}", (0.62, D - 0.1, H - 0.2), (px, 0, (H - 0.2) / 2 + 0.06),
                     body, bev=0.015))
        p.append(box(f"{name}Plinth{sx}", (0.68, D - 0.04, 0.08), (px, 0, 0.09), body, bev=0.015))
        for k in range(3):
            zz = 0.22 + k * 0.17
            p.append(box(f"{name}Drawer{sx}{k}", (0.52, 0.02, 0.14), (px, D / 2 - 0.04, zz), top,
                         bev=0.008))
            p.append(box(f"{name}DrawerPull{sx}{k}", (0.1, 0.02, 0.02), (px, D / 2 - 0.02, zz), iron,
                         bev=0.003))
        p.append(box(f"{name}FrontPanel{sx}", (0.5, 0.02, 0.45), (px, -D / 2 + 0.04, 0.4), top,
                     bev=0.01))
        for dx in (-0.2, 0.2):
            for dz in (0.2, 0.6):
                p.append(sphere(f"{name}Stud{sx}{dx}{dz}", 0.015, (px + dx, -D / 2 + 0.025, dz),
                                iron, segs=8))
    return group(name, p, loc, rot_z)
