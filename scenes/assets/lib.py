"""Shared bpy helpers for scene scripts and assets: primitives and materials.

Every helper creates objects in the active collection and returns them.
"""
import math

import bmesh
import bpy
from mathutils import Euler, Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m


def noisy_mat(name, c1, c2, scale=8.0, rough=0.7, stretch=(1, 1, 1), bump=0.25):
    """Two-tone material driven by noise; gives wood/stone some variation."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = stretch
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def bevel(obj, width=0.01, segs=3):
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = segs
    return obj


def box(name, size, loc, material, rot=(0, 0, 0), bev=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bev:
        bevel(o, bev)
    return assign(o, material)


def cyl(name, r, depth, loc, material, rot=(0, 0, 0), verts=24, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    if smooth:
        bpy.ops.object.shade_smooth()
    return assign(o, material)


def sphere(name, r, loc, material, scale=(1, 1, 1), segs=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=segs,
                                         ring_count=segs // 2)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return assign(o, material)


def cone(name, r1, r2, depth, loc, material, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    return assign(o, material)


def group(name, parts, loc=(0, 0, 0), rot_z=0.0):
    """Parent parts to a new empty called name, then place and turn the empty."""
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def torus(name, major, minor, loc, material, rot=(0, 0, 0), **kw):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=loc, rotation=rot, **kw)
    o = bpy.context.object
    o.name = name
    return assign(o, material)


def point_light(name, loc, energy, color, radius=0.05):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    bpy.context.collection.objects.link(o)
    return o


def polar(r, a, z=0.0):
    return (r * math.cos(a), r * math.sin(a), z)


def smooth_by_angle(obj, degrees=40):
    bpy.context.view_layer.objects.active = obj
    for s in bpy.context.selected_objects:
        s.select_set(False)
    obj.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(degrees))
    return obj


# ---------------------------------------------------------------- generated meshes

def mesh_obj(name, verts, faces, material, loc=(0, 0, 0), rot=(0, 0, 0), smooth_angle=35):
    """Object from raw verts/faces; duplicate verts are merged and normals made consistent."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = rot
    bpy.context.collection.objects.link(o)
    if smooth_angle:
        smooth_by_angle(o, smooth_angle)
    return assign(o, material)


def shell(name, r_out, r_in, z0, z1, material, segs=128, arc=None, loc=(0, 0, 0),
          r_out_top=None, r_in_top=None, rot=(0, 0, 0)):
    """Closed tube (or solid disc when r_in=0) around local Z, optionally only
    over the angular range `arc` = (a0, a1) with capped ends. Tops may taper."""
    ro1 = r_out if r_out_top is None else r_out_top
    ri1 = r_in if r_in_top is None else r_in_top
    if arc:
        a0, a1 = arc
        n = max(2, int(segs * (a1 - a0) / (2 * math.pi)))
        angles = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    else:
        angles = [2 * math.pi * i / segs for i in range(segs)]
    verts = []
    for a in angles:
        c, s = math.cos(a), math.sin(a)
        verts += [(r_out * c, r_out * s, z0), (ro1 * c, ro1 * s, z1),
                  (ri1 * c, ri1 * s, z1), (r_in * c, r_in * s, z0)]
    faces = []
    n = len(angles)
    for i in range(n if not arc else n - 1):
        a, b = 4 * i, 4 * ((i + 1) % n)
        faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2),
                  (a + 2, b + 2, b + 3, a + 3), (a + 3, b + 3, b, a)]
    if arc:
        last = 4 * (n - 1)
        faces += [(3, 2, 1, 0), (last, last + 1, last + 2, last + 3)]
    return mesh_obj(name, verts, faces, material, loc, rot)


def lathe(name, profile, loc, material, segs=24, rot=(0, 0, 0)):
    """Turned part (leg, finial, candlestick) from a (radius, z) profile listed
    bottom to top; radius 0 at either end closes it."""
    verts, faces = [], []
    n = len(profile)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        verts += [(r * math.cos(a), r * math.sin(a), z) for r, z in profile]
    for i in range(segs):
        j = (i + 1) % segs
        for k in range(n - 1):
            faces.append((i * n + k, j * n + k, j * n + k + 1, i * n + k + 1))
    if profile[0][0] > 0:
        faces.append(tuple(i * n for i in reversed(range(segs))))
    if profile[-1][0] > 0:
        faces.append(tuple(i * n + n - 1 for i in range(segs)))
    return mesh_obj(name, verts, faces, material, loc, rot, smooth_angle=50)


def arch_outline(w, h, segs=24):
    """(x, z) outline of a round-headed opening: straight sides h, semicircular head."""
    pts = [(-w / 2, 0.0), (w / 2, 0.0)]
    pts += [(w / 2 * math.cos(math.pi * k / segs), h + w / 2 * math.sin(math.pi * k / segs))
            for k in range(segs + 1)]
    return pts


def arch_slab(name, w, h, thick, material, loc=(0, 0, 0), rot=(0, 0, 0), segs=24, bev=0.006):
    """Round-headed slab (door leaf, pane, cutter) in its local XZ plane, thickness along Y."""
    outline = arch_outline(w, h, segs)
    verts = [(px, dy, pz) for dy in (-thick / 2, thick / 2) for px, pz in outline]
    n = len(outline)
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    o = mesh_obj(name, verts, faces, material, loc, rot, smooth_angle=0)
    if bev:
        bevel(o, bev, 2)
    return o


class Batch:
    """Collects many small boxes / cylinders into one mesh per material (books,
    planks, stones, scrolls); far faster than one object per piece."""

    def __init__(self):
        self.parts = {}

    def _slot(self, material):
        return self.parts.setdefault(material.name, (material, [], []))[1:]

    def box(self, material, size, loc, rz=0.0, rx=0.0, ry=0.0):
        sx, sy, sz = (s / 2 for s in size)
        corners = [Vector((x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
        rot = Euler((rx, ry, rz)).to_matrix()
        verts, faces = self._slot(material)
        base = len(verts)
        verts += [tuple(rot @ c + Vector(loc)) for c in corners]
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
                  (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(base + i for i in f))

    def cyl(self, material, r, length, loc, rz=0.0, rx=0.0, ry=0.0, segs=10):
        rot = Euler((rx, ry, rz)).to_matrix()
        verts, faces = self._slot(material)
        base = len(verts)
        for i in range(segs):
            a = 2 * math.pi * i / segs
            for z in (-length / 2, length / 2):
                verts.append(tuple(rot @ Vector((r * math.cos(a), r * math.sin(a), z)) + Vector(loc)))
        for i in range(segs):
            j = (i + 1) % segs
            faces.append((base + 2 * i, base + 2 * j, base + 2 * j + 1, base + 2 * i + 1))
        faces.append(tuple(base + 2 * i for i in range(segs)))
        faces.append(tuple(base + 2 * i + 1 for i in reversed(range(segs))))

    def build(self, name, bev=0.0):
        """One object per material, named <name>_<material>; returns the objects."""
        out = []
        for key, (material, verts, faces) in self.parts.items():
            me = bpy.data.meshes.new(f"{name}_{key}")
            me.from_pydata(verts, [], faces)
            me.validate()
            o = bpy.data.objects.new(f"{name}_{key}", me)
            bpy.context.collection.objects.link(o)
            assign(o, material)
            if bev:
                bevel(o, bev, 2).modifiers["bevel"].limit_method = "ANGLE"
            out.append(o)
        self.parts = {}
        return out


# ---------------------------------------------------------------- animation

def keyframe(obj, path, fn, target=None, fps=24, frames=48):
    """Key `path` on every frame with value fn(t); periods that divide the clip make it loop."""
    target = target or obj
    for f in range(1, frames + 1):
        t = (f - 1) / fps
        setattr(target, path, fn(t))
        target.keyframe_insert(path, frame=f)


def wave(t, k, ph=0.0):
    """Sine that completes k whole cycles over a 2 s clip."""
    return math.sin(math.pi * k * t + ph)


# ---------------------------------------------------------------- materials

def palette():
    """The shared material palette by key; materials are created once and reused."""
    M = {}
    M["stone"] = noisy_mat("Stone", (0.10, 0.095, 0.09), (0.26, 0.24, 0.22), 6, 0.9)
    M["floor"] = noisy_mat("FloorPlanks", (0.22, 0.12, 0.06), (0.36, 0.21, 0.11),
                           4, 0.65, stretch=(1, 12, 1))
    M["wood"] = noisy_mat("Wood", (0.20, 0.10, 0.04), (0.38, 0.22, 0.10),
                          5, 0.6, stretch=(1, 1, 10))
    M["darkwood"] = noisy_mat("DarkWood", (0.07, 0.04, 0.02), (0.16, 0.09, 0.04),
                              5, 0.55, stretch=(1, 1, 10))
    M["plaster"] = noisy_mat("Plaster", (0.36, 0.29, 0.21), (0.50, 0.42, 0.31), 3, 0.95)
    M["iron"] = mat("Iron", (0.12, 0.12, 0.13), 0.45, 1.0)
    M["steel"] = mat("Steel", (0.7, 0.72, 0.75), 0.25, 1.0)
    M["gold"] = mat("Gold", (1.0, 0.72, 0.25), 0.25, 1.0)
    M["brass"] = mat("Brass", (0.8, 0.55, 0.25), 0.35, 1.0)
    M["parchment"] = mat("Parchment", (0.85, 0.74, 0.52), 0.9)
    M["ink"] = mat("Ink", (0.25, 0.08, 0.05), 0.9)
    M["red"] = mat("RedCloth", (0.45, 0.04, 0.05), 0.9)
    M["blue"] = mat("BlueCloth", (0.05, 0.10, 0.35), 0.9)
    M["green"] = mat("GreenCloth", (0.08, 0.25, 0.10), 0.9)
    M["rug"] = noisy_mat("Rug", (0.06, 0.05, 0.22), (0.20, 0.10, 0.35), 14, 1.0)
    M["leather"] = mat("Leather", (0.25, 0.12, 0.05), 0.7)
    M["wax"] = mat("Wax", (0.95, 0.9, 0.75), 0.5)
    M["flame"] = mat("Flame", (1, 0.6, 0.2), 1, emit=(1.0, 0.5, 0.15), emit_strength=12)
    M["fire"] = mat("Fire", (0, 0, 0), 1, emit=(1.0, 0.16, 0.0), emit_strength=2.5)
    M["ember"] = mat("Ember", (0.1, 0.02, 0.0), 1, emit=(1.0, 0.18, 0.02), emit_strength=8)
    M["glass_potion_r"] = mat("PotionRed", (0.9, 0.05, 0.1), 0.1,
                              emit=(0.9, 0.05, 0.1), emit_strength=1.5)
    M["glass_potion_b"] = mat("PotionBlue", (0.1, 0.3, 1.0), 0.1,
                              emit=(0.1, 0.4, 1.0), emit_strength=2.0)
    M["glass_potion_g"] = mat("PotionGreen", (0.2, 0.9, 0.2), 0.1,
                              emit=(0.2, 0.9, 0.3), emit_strength=1.5)
    M["crystal"] = mat("Crystal", (0.5, 0.3, 1.0), 0.1,
                       emit=(0.55, 0.3, 1.0), emit_strength=6)
    M["purple"] = mat("PurpleCloth", (0.22, 0.05, 0.35), 0.9)
    M["arcane_cyan"] = mat("ArcaneCyan", (0.3, 0.8, 1.0), 0.3,
                           emit=(0.2, 0.75, 1.0), emit_strength=10)
    M["arcane_purple"] = mat("ArcanePurple", (0.6, 0.3, 1.0), 0.2,
                             emit=(0.6, 0.25, 1.0), emit_strength=6)
    M["arcane_green"] = mat("ArcaneGreen", (0.3, 1.0, 0.3), 0.2,
                            emit=(0.25, 1.0, 0.2), emit_strength=4)
    M["window"] = mat("WindowGlow", (0.4, 0.55, 0.9), 0.5,
                      emit=(0.35, 0.5, 0.9), emit_strength=2.0)
    M["bookcols"] = [mat(f"Book{i}", c, 0.8) for i, c in enumerate([
        (0.4, 0.05, 0.05), (0.05, 0.2, 0.08), (0.08, 0.1, 0.35),
        (0.35, 0.25, 0.08), (0.25, 0.08, 0.25), (0.1, 0.08, 0.05)])]
    # added with the Blackstaff office
    M["blackstone"] = noisy_mat("BlackStone", (0.025, 0.024, 0.03), (0.09, 0.085, 0.09), 6, 0.85,
                                bump=0.4)
    M["smoked_stone"] = noisy_mat("SmokedStone", (0.045, 0.042, 0.04), (0.13, 0.12, 0.11), 6, 0.9)
    M["velvet"] = noisy_mat("Velvet", (0.06, 0.02, 0.12), (0.12, 0.04, 0.2), 30, 0.9, bump=0.1)
    M["desk_leather"] = noisy_mat("DeskLeather", (0.18, 0.03, 0.03), (0.32, 0.06, 0.05), 25,
                                  0.55, bump=0.15)
    M["pewter"] = mat("Pewter", (0.45, 0.45, 0.47), 0.4, 1.0)
    M["paper"] = mat("Paper", (0.86, 0.82, 0.72), 0.9)
    M["old_parchment"] = noisy_mat("OldParchment", (0.62, 0.5, 0.32), (0.85, 0.74, 0.52), 9, 0.9,
                                   bump=0.05)
    M["black_ink"] = mat("BlackInk", (0.02, 0.02, 0.03), 0.2)
    M["seal_wax"] = mat("SealWax", (0.5, 0.03, 0.03), 0.4)
    M["clear_glass"] = glass_mat("ClearGlass", (0.9, 0.95, 1.0))
    M["soot"] = mat("Soot", (0.03, 0.025, 0.02), 1)
    M["bone"] = mat("Bone", (0.85, 0.8, 0.68), 0.6)
    return M


def glass_mat(name, color):
    """Clear glass (transmission), for inkwells and hourglasses."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.45
    return m


def material(key):
    """One material from the palette, e.g. material("wood")."""
    return palette()[key]


def as_material(value, name, rough=0.9):
    """Accept a material, a palette key, or an (r, g, b) colour (made into a cloth-like material)."""
    if value is None or isinstance(value, bpy.types.Material):
        return value
    if isinstance(value, str):
        return material(value)
    return mat(name, tuple(value), rough)
