"""Framed oil portrait of a wizard: stepped gilt frame with corner rosettes and
a crest, a varnished canvas painted in low relief (arched window with a night
sky, a crimson drape, a half-length figure in black robes with a dark beard,
holding a black staff topped with a silver star, one hand on a red book),
a brass nameplate and a hanging cord.

    portrait.build("Portrait", loc=(0, 4.98, 2.1), plate="KHELBEN ARUNSUN")

Origin is at the wall face under the middle of the frame (put z at the height
of the frame's bottom edge); the picture faces local -y.
"""
import math

import bpy

from assets.lib import (arch_slab, box, cone, cyl, group, lathe, mat, material, noisy_mat, sphere)


def paint(name, c1, c2, scale=40.0):
    """Oil paint: brush-streak noise, a little bump, a varnished sheen."""
    return noisy_mat(name, c1, c2, scale, 0.45, stretch=(1, 1, 4), bump=0.15)


def build(name="Portrait", loc=(0, 0, 0), rot_z=0.0, *, width=0.86, height=1.1, border=0.12,
          robe=(0.012, 0.011, 0.016), beard=(0.02, 0.016, 0.014), plate="KHELBEN ARUNSUN", cord=True):
    """width, height: the canvas; border: frame width. plate=None for no nameplate."""
    W, Hc, b = width, height, border
    gold, brass = material("gold"), material("brass")
    cz = b + Hc / 2                      # canvas centre height above the origin
    p = []
    # stepped frame: back board, wide flat, raised bead, sight-edge lip (each a ring of 4 bars)
    for k, (inset, depth, wide, m) in enumerate([(0.0, 0.03, b, brass), (0.012, 0.055, b - 0.03, gold),
                                                 (b - 0.035, 0.07, 0.022, gold),
                                                 (b - 0.012, 0.045, 0.014, brass)]):
        ow, oh = W + 2 * b - 2 * inset, Hc + 2 * b - 2 * inset
        y = -depth / 2
        for side, (sx, sz, px, pz) in enumerate([(ow, wide, 0, cz + oh / 2 - wide / 2),
                                                 (ow, wide, 0, cz - oh / 2 + wide / 2),
                                                 (wide, oh, -ow / 2 + wide / 2, cz),
                                                 (wide, oh, ow / 2 - wide / 2, cz)]):
            p.append(box(f"{name}Frame{k}_{side}", (sx, depth, sz), (px, y, pz), m, bev=0.004 if k else 0.002))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * (W / 2 + b / 2)
            z = cz + sz * (Hc / 2 + b / 2)
            p.append(sphere(f"{name}Rosette{sx}{sz}", 0.035, (x, -0.06, z), gold, scale=(1, 0.45, 1), segs=14))
            p.append(sphere(f"{name}RosetteBoss{sx}{sz}", 0.014, (x, -0.075, z), brass, segs=10))
    # crest on the top rail
    p.append(cyl(name + "Crest", 0.07, 0.03, (0, -0.045, cz + Hc / 2 + b + 0.03), gold,
                 rot=(math.pi / 2, 0, 0), verts=24))
    p.append(cone(name + "CrestFinial", 0.025, 0.0, 0.07, (0, -0.045, cz + Hc / 2 + b + 0.12), gold, verts=10))
    # canvas ground: dark umber with a warm glow behind the head
    p.append(box(name + "Canvas", (W, 0.01, Hc), (0, -0.012, cz), paint(name + "Ground", (0.03, 0.022, 0.015),
                                                                        (0.11, 0.075, 0.045), 6), bev=0))
    y0 = -0.018                                        # painted surface
    # background: arched window with a night sky and a pale moon, and a crimson drape
    p.append(arch_slab(name + "PaintWindow", 0.3, 0.32, 0.004,
                       paint(name + "Sky", (0.03, 0.05, 0.14), (0.08, 0.12, 0.28), 8),
                       (-0.2, y0, cz + 0.02), bev=0))
    p.append(sphere(name + "PaintMoon", 0.03, (-0.26, y0 - 0.003, cz + 0.36),
                    mat(name + "MoonPaint", (0.85, 0.82, 0.65), 0.5), scale=(1, 0.15, 1), segs=12))
    for k in range(5):
        p.append(cyl(f"{name}Drape{k}", 0.035, Hc * 0.9, (W / 2 - 0.05 - k * 0.045, y0, cz + 0.02),
                     paint(name + "Drape", (0.18, 0.02, 0.03), (0.42, 0.05, 0.06), 30), verts=10))
    # the figure, half length, in low relief
    zb = b                                             # bottom of the canvas
    robe_m = paint(name + "Robe", robe, tuple(c * 3 + 0.02 for c in robe), 25)
    torso = lathe(name + "Robe", [(0.27, 0.0), (0.26, 0.25), (0.25, 0.45), (0.24, 0.55), (0.2, 0.62),
                                  (0.09, 0.66), (0.05, 0.68), (0.0, 0.69)], (0, y0 - 0.02, zb), robe_m, segs=32)
    torso.scale = (1, 0.18, 1)
    p.append(torso)
    trim = paint(name + "Trim", (0.12, 0.03, 0.2), (0.25, 0.08, 0.4), 30)
    for sx in (-1, 1):
        p.append(box(f"{name}RobeTrim{sx}", (0.035, 0.012, 0.6), (sx * 0.045, y0 - 0.072, zb + 0.32), trim,
                     rot=(0, sx * math.radians(6), 0), bev=0.003))
        p.append(sphere(f"{name}Clasp{sx}", 0.012, (sx * 0.045, y0 - 0.078, zb + 0.56), gold, segs=8))
    p.append(cone(name + "Collar", 0.13, 0.07, 0.09, (0, y0 - 0.035, zb + 0.68), robe_m, verts=20))
    bpy.context.object.scale = (1, 0.35, 1)
    skin = paint(name + "Skin", (0.42, 0.28, 0.2), (0.62, 0.43, 0.32), 20)
    beard_m = paint(name + "Beard", beard, (0.16, 0.14, 0.13), 60)
    hz = zb + 0.83
    p += [sphere(name + "Head", 0.095, (0, y0 - 0.04, hz), skin, scale=(1, 0.5, 1.22), segs=24),
          sphere(name + "Hair", 0.1, (0, y0 - 0.03, hz + 0.04), beard_m, scale=(1.02, 0.45, 1.05), segs=20),
          sphere(name + "Nose", 0.017, (0, y0 - 0.088, hz - 0.01), skin, scale=(0.8, 1, 1.5), segs=10)]
    beard_o = cone(name + "Beard", 0.085, 0.015, 0.24, (0, y0 - 0.06, hz - 0.15), beard_m,
                   rot=(math.pi, 0, 0), verts=20)
    beard_o.scale = (1, 0.45, 1)
    p.append(beard_o)
    p.append(box(name + "BeardStreak", (0.012, 0.004, 0.09), (0.018, y0 - 0.1, hz - 0.12),
                 paint(name + "Grey", (0.45, 0.45, 0.45), (0.7, 0.7, 0.7), 60), rot=(0, 0.1, 0), bev=0.004))
    for sx in (-1, 1):
        p.append(sphere(f"{name}Moustache{sx}", 0.03, (sx * 0.03, y0 - 0.083, hz - 0.045), beard_m,
                        scale=(1.4, 0.5, 0.5), segs=10))
        p.append(sphere(f"{name}Eye{sx}", 0.009, (sx * 0.035, y0 - 0.088, hz + 0.02),
                        mat(name + "EyePaint", (0.02, 0.02, 0.025), 0.3), segs=8))
        p.append(box(f"{name}Brow{sx}", (0.04, 0.008, 0.01), (sx * 0.036, y0 - 0.088, hz + 0.042), beard_m,
                     rot=(0, -sx * 0.25, 0), bev=0))
    # staff in the right hand, book under the left
    sx = 0.27
    p.append(cyl(name + "Staff", 0.012, Hc * 0.92, (sx, y0 - 0.05, zb + Hc * 0.46),
                 noisy_mat("PaintStaff", (0.01, 0.01, 0.012), (0.04, 0.035, 0.05), 10, 0.3), verts=10))
    star = mat(name + "StarPaint", (0.85, 0.87, 0.92), 0.25, 1.0)
    for k in range(4):
        p.append(box(f"{name}StarRay{k}", (0.075, 0.006, 0.012), (sx, y0 - 0.055, zb + Hc * 0.86), star,
                     rot=(0, k * math.pi / 4, 0), bev=0))
    p.append(sphere(name + "StarCore", 0.014, (sx, y0 - 0.058, zb + Hc * 0.86), star, segs=10))
    p.append(sphere(name + "HandR", 0.035, (sx, y0 - 0.075, zb + 0.32), skin, scale=(1, 0.6, 1.2), segs=12))
    p.append(box(name + "Book", (0.18, 0.03, 0.12), (-0.17, y0 - 0.08, zb + 0.13),
                 paint(name + "BookPaint", (0.3, 0.03, 0.03), (0.5, 0.08, 0.06), 30), rot=(0, -0.25, 0),
                 bev=0.006))
    p.append(sphere(name + "HandL", 0.035, (-0.13, y0 - 0.1, zb + 0.2), skin, scale=(1.2, 0.6, 1), segs=12))
    if plate:
        p.append(box(name + "Plate", (0.34, 0.012, 0.055), (0, -0.065, b / 2), brass, bev=0.004))
        cu = bpy.data.curves.new(name + "PlateText", "FONT")
        cu.body = plate
        cu.size = 0.026
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.extrude = 0.0008
        t = bpy.data.objects.new(name + "PlateText", cu)
        bpy.context.collection.objects.link(t)
        t.location = (0, -0.072, b / 2)
        t.rotation_euler = (math.pi / 2, 0, 0)
        t.data.materials.append(mat(name + "Engraving", (0.05, 0.035, 0.015), 0.5, 0.8))
        p.append(t)
    if cord:
        top = cz + Hc / 2 + b
        for sx in (-1, 1):
            d = math.hypot(W / 2, 0.35)
            c = cyl(f"{name}Cord{sx}", 0.004, d, (sx * W / 4, -0.01, top + 0.175), material("darkwood"), verts=6)
            c.rotation_euler = (0, -sx * math.atan2(W / 2, 0.35), 0)
            p.append(c)
        p.append(sphere(name + "Nail", 0.012, (0, -0.012, top + 0.35), material("iron"), segs=8))
    return group(name, p, loc, rot_z)
