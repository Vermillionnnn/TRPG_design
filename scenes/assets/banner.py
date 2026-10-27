"""Swallowtail wall banner with gold trim, a crescent moon and stars, on a brass rod.

    banner.build("Banner", loc=(0, 0.45, 2.3), rot_z=math.pi / 2)   # on a wall at x = 0

Origin is at the middle of the banner on the wall face; the banner faces local -y.
"""
import math

import bpy

from assets.lib import as_material, assign, box, cyl, group, mat, material, sphere


def star_mesh(name, r_out, r_in, loc, material, points=5, thick=0.006):
    """Flat star in the XZ plane, facing -y."""
    verts, n = [], points * 2
    for k in range(n):
        r = r_out if k % 2 == 0 else r_in
        a = math.pi / 2 + k * math.pi / points
        verts.append((r * math.cos(a), 0, r * math.sin(a)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [list(range(n))])
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    sol = o.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = thick
    return assign(o, material)


def build(name="Banner", loc=(0, 0, 0), rot_z=0.0, *, width=0.8, length=1.05, notch=0.22,
          cloth=(0.05, 0.05, 0.25), emblem=True):
    """width / length of the cloth (m), notch depth of the swallowtail.
    cloth: (r, g, b) or material. emblem adds the crescent moon and stars.
    """
    top, bot = 0.5, 0.5 - length
    outline = [(-width / 2, top), (width / 2, top), (width / 2, bot), (0, bot + notch), (-width / 2, bot)]
    cloth = (mat("BannerCloth", cloth, 0.9) if tuple(cloth) == (0.05, 0.05, 0.25)
             else as_material(cloth, name + "ClothMat"))
    gold, brass = material("gold"), material("brass")

    def flag(part, scale, depth, m):
        me = bpy.data.meshes.new(part)
        me.from_pydata([(x * scale, -depth, z * scale) for x, z in outline], [], [list(range(len(outline)))])
        o = bpy.data.objects.new(part, me)
        bpy.context.collection.objects.link(o)
        return assign(o, m)

    parts = [flag(name + "Trim", 1.0, 0.09, gold), flag(name + "Cloth", 0.94, 0.095, cloth),
             box(name + "Rod", (width + 0.25, 0.04, 0.04), (0, -0.12, top + 0.03), brass)]
    for sx in (-1, 1):
        parts.append(sphere(f"{name}Finial{sx}", 0.035, (sx * (width / 2 + 0.13), -0.12, top + 0.03), brass, segs=10))
    if emblem:
        # crescent moon: gold disc with a cloth-coloured disc offset over it
        rot = (math.radians(90), 0, 0)
        parts += [cyl(name + "Moon", 0.2, 0.006, (0, -0.1, 0.1), gold, rot=rot, verts=40, smooth=False),
                  cyl(name + "MoonCut", 0.17, 0.006, (0.08, -0.101, 0.14), cloth, rot=rot, verts=40, smooth=False),
                  star_mesh(name + "StarBig", 0.08, 0.035, (0.12, -0.104, -0.12), gold),
                  star_mesh(name + "StarA", 0.045, 0.02, (-0.2, -0.104, 0.32), gold),
                  star_mesh(name + "StarB", 0.035, 0.015, (0.22, -0.104, 0.35), gold),
                  star_mesh(name + "StarC", 0.03, 0.013, (-0.22, -0.104, -0.18), gold)]
    return group(name, parts, loc, rot_z)
