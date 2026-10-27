"""Build a cutaway of the Blackstaff's office inside Blackstaff Tower (Waterdeep).

Run with:  python3 scenes/blackstaff-office/build_scene.py [--render out.png] [--samples N]
           [--shot wide|close|top] [--res percent] [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P scenes/blackstaff-office/build_scene.py -- --render out.png

Units are metres. The round chamber is centred on the origin; the front half
of the wall (toward -Y) is cut away so the camera can look in.
"""
import math
import random
import sys

import bmesh
import bpy
from mathutils import Vector

random.seed(17)

# ---------------------------------------------------------------- helpers

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


def blackstone_mat():
    """Seamless, glassy black stone with a faint violet sheen."""
    m = bpy.data.materials.new("BlackStone")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.6
    nz.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.012, 0.011, 0.016, 1)
    ramp.color_ramp.elements[1].color = (0.045, 0.04, 0.06, 1)
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.08
    rr.inputs["To Max"].default_value = 0.28
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Coat Weight"].default_value = 0.4
    bsdf.inputs["Coat Roughness"].default_value = 0.05
    bsdf.inputs["Coat Tint"].default_value = (0.75, 0.65, 1.0, 1)
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
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
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
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    return assign(o, material)


def mesh_obj(name, verts, faces, material, loc=(0, 0, 0), rot=(0, 0, 0), smooth_angle=35):
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
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.selected_objects:
        s.select_set(False)
    o.select_set(True)
    if smooth_angle:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
    return assign(o, material)


def shell(name, r_out, r_in, z0, z1, material, segs=128, arc=None, loc=(0, 0, 0),
          r_out_top=None, r_in_top=None, rot=(0, 0, 0)):
    """Closed tube (or solid disc when r_in=0) around local Z, optionally only
    over the angular range `arc` = (a0, a1) with capped ends."""
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


TURNED_LEG = [(0.03, 0.0), (0.038, 0.03), (0.03, 0.06), (0.026, 0.12), (0.034, 0.2),
              (0.036, 0.23), (0.026, 0.27), (0.022, 0.36), (0.03, 0.42), (0.034, 0.46)]
FINIAL = [(0.03, 0.0), (0.035, 0.015), (0.02, 0.03), (0.045, 0.07), (0.04, 0.1), (0.015, 0.13),
          (0.022, 0.15), (0.0, 0.2)]



class Batch:
    """Collects many small boxes into one mesh per material (books, papers,
    pigeonhole boards), which is far faster than one object per box."""

    def __init__(self):
        self.parts = {}

    def box(self, material, size, loc, rz=0.0, rx=0.0, ry=0.0):
        sx, sy, sz = (s / 2 for s in size)
        corners = [Vector((x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
        from mathutils import Euler
        rot = Euler((rx, ry, rz)).to_matrix()
        verts, faces = self.parts.setdefault(material.name, (material, [], []))[1:]
        base = len(verts)
        verts += [tuple(rot @ c + Vector(loc)) for c in corners]
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
                  (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(base + i for i in f))

    def cyl(self, material, r, length, loc, rz=0.0, rx=0.0, ry=0.0, segs=10):
        from mathutils import Euler
        rot = Euler((rx, ry, rz)).to_matrix()
        verts, faces = self.parts.setdefault(material.name, (material, [], []))[1:]
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
        for key, (material, verts, faces) in self.parts.items():
            me = bpy.data.meshes.new(f"{name}_{key}")
            me.from_pydata(verts, [], faces)
            me.validate()
            o = bpy.data.objects.new(f"{name}_{key}", me)
            bpy.context.collection.objects.link(o)
            assign(o, material)
            if bev:
                bevel(o, bev, 2).modifiers["bevel"].limit_method = "ANGLE"
        self.parts = {}


# ---------------------------------------------------------------- materials

def build_materials():
    M = {}
    # stone, wood and plaster use the homebase values so the two scenes match
    M["stone"] = noisy_mat("Stone", (0.10, 0.095, 0.09), (0.26, 0.24, 0.22), 6, 0.9)
    M["blackstone"] = noisy_mat("BlackStone", (0.025, 0.024, 0.03), (0.09, 0.085, 0.09), 6, 0.85,
                                bump=0.4)
    M["planks"] = [noisy_mat(f"FloorPlanks{i}", tuple(c * k for c in (0.22, 0.12, 0.06)),
                             tuple(c * k for c in (0.36, 0.21, 0.11)), 4, 0.65, stretch=(12, 1, 1))
                   for i, k in enumerate((1.0, 0.85, 1.12))]
    M["wood"] = noisy_mat("Wood", (0.20, 0.10, 0.04), (0.38, 0.22, 0.10), 5, 0.6,
                          stretch=(1, 1, 10))
    M["darkwood"] = noisy_mat("DarkWood", (0.07, 0.04, 0.02), (0.16, 0.09, 0.04), 5, 0.55,
                              stretch=(1, 1, 10))
    M["plaster"] = noisy_mat("Plaster", (0.36, 0.29, 0.21), (0.50, 0.42, 0.31), 3, 0.95)
    M["staff"] = blackstone_mat()
    M["black"] = M["blackstone"]
    M["black_matte"] = M["stone"]
    M["walnut"] = M["darkwood"]
    M["oak"] = M["wood"]
    M["silver"] = mat("Pewter", (0.45, 0.45, 0.47), 0.4, 1.0)
    M["brass"] = mat("Brass", (0.8, 0.55, 0.25), 0.3, 1.0)
    M["iron"] = mat("Iron", (0.08, 0.08, 0.09), 0.4, 1.0)
    M["leather"] = noisy_mat("Leather", (0.18, 0.03, 0.03), (0.32, 0.06, 0.05), 25, 0.55,
                             bump=0.15)
    M["velvet"] = noisy_mat("Velvet", (0.06, 0.02, 0.12), (0.12, 0.04, 0.2), 30, 0.9, bump=0.1)
    M["rug"] = rug_mat()
    M["parchment"] = noisy_mat("Parchment", (0.62, 0.5, 0.32), (0.85, 0.74, 0.52), 9, 0.9,
                               bump=0.05)
    M["paper"] = mat("Paper", (0.86, 0.82, 0.72), 0.9)
    M["ink"] = mat("Ink", (0.02, 0.02, 0.03), 0.2)
    M["wax_red"] = mat("SealWax", (0.5, 0.03, 0.03), 0.4)
    M["wax"] = mat("Wax", (0.95, 0.9, 0.75), 0.5)
    M["flame"] = mat("Flame", (1, 0.6, 0.2), 1, emit=(1.0, 0.5, 0.15), emit_strength=14)
    M["fire"] = mat("Fire", (0, 0, 0), 1, emit=(1.0, 0.25, 0.03), emit_strength=6)
    M["ember"] = mat("Ember", (0.1, 0.02, 0.0), 1, emit=(1.0, 0.18, 0.02), emit_strength=8)
    M["glass"] = glass_mat("Glass", (0.9, 0.95, 1.0))
    M["crystal"] = mat("CrystalBall", (0.6, 0.75, 1.0), 0.05,
                       emit=(0.35, 0.55, 1.0), emit_strength=3)
    M["globe"] = mat("Driftglobe", (1, 0.9, 0.7), 0.2, emit=(1.0, 0.82, 0.55), emit_strength=18)
    M["arcane"] = mat("Arcane", (0.5, 0.3, 1.0), 0.2, emit=(0.55, 0.3, 1.0), emit_strength=10)
    M["arcane_faint"] = mat("ArcaneFaint", (0.3, 0.2, 0.6), 0.3,
                            emit=(0.45, 0.25, 1.0), emit_strength=3)
    M["arcane_cyan"] = mat("ArcaneCyan", (0.3, 0.8, 1.0), 0.3,
                           emit=(0.2, 0.75, 1.0), emit_strength=6)
    M["sky"] = sky_mat()
    M["banner"] = noisy_mat("Banner", (0.10, 0.03, 0.18), (0.16, 0.05, 0.26), 20, 0.9)
    M["map"] = map_mat()
    M["canvas"] = noisy_mat("Canvas", (0.04, 0.03, 0.03), (0.16, 0.11, 0.08), 3, 0.7)
    M["leaf"] = noisy_mat("Leaf", (0.02, 0.07, 0.02), (0.08, 0.18, 0.05), 10, 0.7, bump=0.4)
    M["clay"] = mat("Clay", (0.35, 0.13, 0.06), 0.8)
    M["potions"] = [mat(f"Potion{i}", c, 0.1, emit=c, emit_strength=1.5) for i, c in enumerate([
        (0.9, 0.05, 0.1), (0.1, 0.35, 1.0), (0.2, 0.9, 0.3), (0.9, 0.6, 0.1), (0.6, 0.2, 0.9)])]
    M["bookcols"] = [noisy_mat(f"Book{i}", tuple(x * 0.6 for x in c), c, 40, 0.65, bump=0.05)
                     for i, c in enumerate([
                         (0.40, 0.05, 0.05), (0.05, 0.20, 0.08), (0.08, 0.10, 0.35),
                         (0.35, 0.25, 0.08), (0.25, 0.08, 0.25), (0.12, 0.09, 0.06),
                         (0.02, 0.02, 0.025), (0.30, 0.15, 0.05)])]
    return M


def glass_mat(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.45
    return m


def rug_mat():
    """Deep violet rug with a border and a faint medallion, from radial distance."""
    m = bpy.data.materials.new("Rug")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    norm = nt.nodes.new("ShaderNodeMath")
    norm.operation = "DIVIDE"
    norm.inputs[1].default_value = 2.3     # rug radius
    nt.links.new(ln.outputs["Value"], norm.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    stops = [(0.0, (0.35, 0.22, 0.08)), (0.12, (0.10, 0.03, 0.16)), (0.45, (0.30, 0.18, 0.06)),
             (0.48, (0.10, 0.03, 0.16)), (0.82, (0.30, 0.18, 0.06)), (0.86, (0.18, 0.02, 0.04)),
             (0.96, (0.30, 0.18, 0.06))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[1][0], (*stops[1][1], 1)
    for pos, col in stops[2:]:
        e = cr.elements.new(pos)
        e.color = (*col, 1)
    nt.links.new(norm.outputs["Value"], ramp.inputs["Fac"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 60
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
    nt.links.new(nz.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.3
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def sky_mat():
    """Night sky with stars for the scrying windows (the tower has no real ones)."""
    m = bpy.data.materials.new("ScryingSky")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.25, 0.3, 0.6, 1)
    ramp.color_ramp.elements[1].color = (0.02, 0.03, 0.12, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 90
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "LESS_THAN"
    st.inputs[1].default_value = 0.035
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    nt.links.new(vo.outputs["Distance"], st.inputs[0])
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    nt.links.new(st.outputs[0], add.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], add.inputs["A"])
    add.inputs["B"].default_value = (1, 1, 1, 1)
    nt.links.new(add.outputs["Result"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.6
    return m


def map_mat():
    """Parchment with inked district lines and a blue harbour, a stand-in for Waterdeep."""
    m = bpy.data.materials.new("CityMap")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 9
    ink = nt.nodes.new("ShaderNodeMath")
    ink.operation = "LESS_THAN"
    ink.inputs[1].default_value = 0.025
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    nt.links.new(vo.outputs["Distance"], ink.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    sea = nt.nodes.new("ShaderNodeMath")
    sea.operation = "GREATER_THAN"
    sea.inputs[1].default_value = 0.35
    nt.links.new(sep.outputs["X"], sea.inputs[0])
    paper = nt.nodes.new("ShaderNodeMix")
    paper.data_type = "RGBA"
    paper.inputs["A"].default_value = (0.78, 0.66, 0.44, 1)
    paper.inputs["B"].default_value = (0.25, 0.38, 0.45, 1)
    nt.links.new(sea.outputs[0], paper.inputs["Factor"])
    lines = nt.nodes.new("ShaderNodeMix")
    lines.data_type = "RGBA"
    lines.inputs["B"].default_value = (0.15, 0.07, 0.04, 1)
    nt.links.new(ink.outputs[0], lines.inputs["Factor"])
    nt.links.new(paper.outputs["Result"], lines.inputs["A"])
    nt.links.new(lines.outputs["Result"], bsdf.inputs["Base Color"])
    return m


# ---------------------------------------------------------------- room

R = 5.0           # inner radius of the round chamber
WALL = 0.5        # wall thickness
H = 4.6           # floor to cornice
ARC = (0.0, math.pi)   # semicircular office: back half only, open along the X axis
DOOR_A = math.radians(11.25)                 # door centre, between the first two posts
DOOR_HALF = math.radians(8.4)                # half the angle taken by door + frame


def in_door(a):
    return abs(a - DOOR_A) < DOOR_HALF


def wall_angle(deg):
    return math.radians(deg)


def build_room(M):
    shell("Plinth", R + WALL + 0.3, 0, -0.5, 0.0, M["stone"], arc=ARC, segs=160,
          loc=(0, -0.3, 0))
    box("PlinthFront", (2 * (R + WALL + 0.3), 0.3, 0.5), (0, -0.15, -0.25), M["stone"], bev=0.03)
    # floor of oak planks running front to back, ends hidden by a stone kerb
    B = Batch()
    rnd = random.Random(21)
    pw = 0.24
    x = -R + pw / 2
    while x < R:
        y_end = math.sqrt(max(R * R - (abs(x) + pw / 2) ** 2, 0.0))
        y = 0.0
        first = True
        while y < y_end - 0.05:
            ln = rnd.uniform(1.4, 2.6) * (rnd.uniform(0.3, 0.9) if first else 1.0)
            ln = min(ln, y_end - y)
            B.box(rnd.choice(M["planks"]), (pw - 0.008, ln - 0.008, 0.05),
                  (x, y + ln / 2, 0.025))
            # pegs at plank ends
            for py in (y + 0.05, y + ln - 0.05):
                B.cyl(M["darkwood"], 0.009, 0.004, (x, py, 0.051), segs=8)
            y += ln
            first = False
        x += pw
    B.build("FloorPlanks", bev=0.004)
    shell("FloorBase", R + 0.05, 0, -0.01, 0.0, M["darkwood"], arc=ARC, segs=160)
    shell("Kerb", R + WALL + 0.3, R - 0.28, 0.0, 0.08, M["stone"], arc=ARC, segs=160)
    box("FrontSill", (2 * (R + WALL + 0.3), 0.3, 0.1), (0, -0.15, 0.05), M["stone"], bev=0.025)

    # lower wall: courses of dark basalt (the tower's black stone) as separate blocks
    shell("WallCore", R + WALL, R + 0.06, 0.0, H, M["stone"], arc=ARC, segs=160)
    B = Batch()
    for row in range(4):
        z = 0.08 + 0.16 + row * 0.32
        a = ARC[0] + (0.0 if row % 2 else 0.06)
        while a < ARC[1] - 0.02:
            w = rnd.uniform(0.42, 0.62)
            da = min(w / R, ARC[1] - a)
            mid = a + da / 2
            if in_door(mid) or in_door(a) or in_door(a + da):
                a += da
                continue
            B.box(M["blackstone"], (0.12, R * da - 0.03, 0.29),
                  polar(R + 0.02, mid, z + rnd.uniform(-0.01, 0.01)),
                  rz=mid, ry=rnd.uniform(-0.04, 0.04))
            a += da
    B.build("WallStones", bev=0.025)
    # upper wall: timber-framed plaster, as in the homebase
    shell("WallPlaster", R + 0.1, R + 0.04, 1.36, H, M["plaster"], arc=ARC, segs=160)
    # the low beam stops at the door frame
    for k, arc in enumerate(((ARC[0], DOOR_A - DOOR_HALF), (DOOR_A + DOOR_HALF, ARC[1]))):
        shell(f"BeamLow{k}", R + 0.04, R - 0.1, 1.33, 1.47, M["darkwood"], arc=arc, segs=160)
        shell(f"BeamLowLip{k}", R - 0.08, R - 0.13, 1.47, 1.5, M["darkwood"], arc=arc, segs=160)
    shell("BeamTop", R + 0.04, R - 0.14, H - 0.18, H, M["darkwood"], arc=ARC, segs=160)
    posts = [0, 22.5, 45, 67.5, 112.5, 135, 157.5, 180]
    for deg in posts:
        a = wall_angle(deg)
        off = 0.08 if deg in (0, 180) else 0.0
        p = polar(R - 0.02, a, (H + 1.47) / 2)
        p = (p[0] - math.copysign(off, p[0]) if deg in (0, 180) else p[0], p[1] + off, p[2])
        box(f"Post{deg}", (0.16, 0.18, H - 1.47), p, M["darkwood"], rot=(0, 0, a))
        # pegged joints
        for zz in (1.58, H - 0.3):
            sphere(f"Peg{deg}_{zz}", 0.018, polar(R - 0.115, a, zz), M["darkwood"], segs=8)
    for d0, d1 in zip(posts, posts[1:]):
        if d1 - d0 > 30 or d0 == 0 or 100 < (d0 + d1) / 2 < 150:
            continue   # door, window and chimney bays stay clear
        mid = wall_angle((d0 + d1) / 2)
        span = R * wall_angle(d1 - d0) - 0.16
        hh = H - 1.65
        tilt = math.atan2(span, hh) * (1 if (d0 // 22) % 2 else -1)
        box(f"Brace{d0}", (0.12, 0.12, math.hypot(span, hh) - 0.1),
            polar(R - 0.01, mid, (H + 1.47) / 2), M["darkwood"], rot=(tilt, 0, mid))
    # rafters over the cut, each on a carved bracket
    for deg in range(0, 181, 15):
        a = wall_angle(min(max(deg, 1.5), 178.5))
        box(f"Rafter{deg}", (1.2, 0.16, 0.2), polar(R - 0.5, a, H + 0.1), M["darkwood"],
            rot=(0, 0, a))
        box(f"RafterBracket{deg}", (0.36, 0.12, 0.14), polar(R - 0.26, a, H - 0.07),
            M["darkwood"], rot=(0, math.radians(-30), a))
    shell("RafterPlate", R - 0.85, R - 1.05, H + 0.2, H + 0.32, M["darkwood"], arc=ARC, segs=128)
    # stone end faces of the cut
    for a in ARC:
        p = polar(R + WALL / 2, a, H / 2)
        box(f"CutFace{a:.2f}", (WALL + 0.06, 0.08, H), (p[0], -0.04, p[2]), M["stone"], bev=0.02)


def arch_slab(name, w, h, thick, material, loc, rz, segs=24):
    """Round-headed slab (door leaf, opening) standing in its local XZ plane:
    width w, straight sides h, semicircular head, thickness along local Y."""
    outline = [(-w / 2, 0.0), (w / 2, 0.0)]
    outline += [(w / 2 * math.cos(math.pi * k / segs), h + w / 2 * math.sin(math.pi * k / segs))
                for k in range(segs + 1)]
    verts = [(px, dy, pz) for dy in (-thick / 2, thick / 2) for px, pz in outline]
    n = len(outline)
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    o = mesh_obj(name, verts, faces, material, loc, (0, 0, rz), smooth_angle=0)
    bevel(o, 0.006, 2)
    return o


def build_door(M):
    """Oak door with strap hinges in a timber frame; the office's way in."""
    a = DOOR_A
    rz = a + math.pi / 2          # local X along the wall, local +Y into the room
    t = Vector((-math.sin(a), math.cos(a), 0))
    n = Vector((-math.cos(a), -math.sin(a), 0))
    base = Vector(polar(R, a))

    def L(px, py, pz):
        return tuple(base + t * px + n * py + Vector((0, 0, pz)))

    w, h = 1.1, 1.85              # leaf width and straight height; head radius w / 2
    # dark reveal behind the leaf and a stone threshold
    arch_slab("DoorReveal", w + 0.06, h, 0.04, mat("Reveal", (0.01, 0.008, 0.006), 1),
              L(0, -0.05, 0.08), rz)
    box("DoorThreshold", (w + 0.5, 0.42, 0.1), L(0, 0.12, 0.09), M["stone"], rot=(0, 0, rz),
        bev=0.02)
    # leaf of vertical boards, slightly proud of the wall
    leaf_m = noisy_mat("DoorOak", (0.13, 0.07, 0.03), (0.26, 0.15, 0.07), 5, 0.6,
                       stretch=(10, 1, 1))
    arch_slab("DoorLeaf", w, h, 0.07, leaf_m, L(0, 0.02, 0.14), rz)
    for k in range(1, 6):
        px = -w / 2 + k * w / 6
        top = h + math.sqrt(max((w / 2) ** 2 - px ** 2, 0)) - 0.03
        box(f"DoorSeam{k}", (0.008, 0.01, top), L(px, 0.058, 0.14 + top / 2),
            mat("DoorSeamMat", (0.02, 0.012, 0.008), 1), rot=(0, 0, rz), bev=0)
    # iron strap hinges with split ends, nail heads and a ring pull
    for zz in (0.45, 1.6):
        box(f"DoorStrap{zz}", (w * 0.86, 0.012, 0.07), L(-w * 0.07, 0.062, 0.14 + zz), M["iron"],
            rot=(0, 0, rz), bev=0.004)
        for sgn in (-1, 1):
            box(f"DoorStrapFork{zz}{sgn}", (0.14, 0.012, 0.03),
                L(w * 0.42 - 0.02, 0.062, 0.14 + zz + sgn * 0.03), M["iron"],
                rot=(sgn * math.radians(-25), 0, rz), bev=0.003)
        for k in range(6):
            sphere(f"DoorNail{zz}_{k}", 0.012, L(-w / 2 + 0.08 + k * 0.15, 0.07, 0.14 + zz),
                   M["iron"], segs=8)
        cyl(f"DoorPintle{zz}", 0.025, 0.12, L(-w / 2 - 0.02, 0.06, 0.14 + zz), M["iron"], verts=10)
    box("DoorLockPlate", (0.1, 0.012, 0.18), L(w * 0.36, 0.065, 1.15), M["iron"], rot=(0, 0, rz),
        bev=0.004)
    box("DoorKeyhole", (0.015, 0.014, 0.04), L(w * 0.36, 0.068, 1.1), mat("Reveal", (0, 0, 0), 1),
        rot=(0, 0, rz), bev=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.011,
                                     location=L(w * 0.36, 0.08, 1.2), rotation=(math.pi / 2, 0, rz))
    bpy.context.object.name = "DoorRing"
    bpy.ops.object.shade_smooth()
    assign(bpy.context.object, M["iron"])
    sphere("DoorRingBoss", 0.025, L(w * 0.36, 0.075, 1.27), M["iron"], segs=10)
    # timber frame: jambs, round head, lintel up to the low beam, stone stop blocks
    for sx in (-1, 1):
        box(f"DoorJamb{sx}", (0.16, 0.2, h + 0.14), L(sx * (w / 2 + 0.08), 0.02, (h + 0.14) / 2 + 0.06),
            M["darkwood"], rot=(0, 0, rz), bev=0.012)
        box(f"DoorPlinthBlock{sx}", (0.22, 0.24, 0.3), L(sx * (w / 2 + 0.08), 0.03, 0.2), M["stone"],
            rot=(0, 0, rz), bev=0.02)
    shell("DoorHead", w / 2 + 0.16, w / 2, -0.1, 0.1, M["darkwood"], arc=(0, math.pi), segs=40,
          loc=L(0, 0.02, 0.14 + h), rot=(math.pi / 2, 0, rz))
    box("DoorLintel", (w + 0.6, 0.22, 0.2), L(0, 0.02, 0.14 + h + w / 2 + 0.24), M["darkwood"],
        rot=(0, 0, rz), bev=0.015)
    box("DoorKeystone", (0.16, 0.06, 0.22), L(0, 0.11, 0.14 + h + w / 2 + 0.06), M["darkwood"],
        rot=(0, 0, rz), bev=0.01)
    # carved Blackstaff sigil on the lintel
    box("DoorSigilStaff", (0.03, 0.02, 0.16), L(0, 0.14, 0.14 + h + w / 2 + 0.24), M["silver"],
        rot=(0, math.radians(20), rz), bev=0)
    # wall sconce beside the door
    sx = -(w / 2 + 0.45)
    box("SconcePlate", (0.12, 0.03, 0.22), L(sx, 0.0, 1.75), M["iron"], rot=(0, 0, rz), bev=0.005)
    box("SconceArm", (0.03, 0.18, 0.03), L(sx, 0.1, 1.72), M["iron"], rot=(0, 0, rz), bev=0)
    cyl("SconceCup", 0.05, 0.04, L(sx, 0.19, 1.74), M["iron"], verts=12)
    candle(M, "SconceCandle", L(sx, 0.19, 1.76), h=0.16, energy=30)


def build_window(M):
    """Arched lancet window behind the desk with diamond leading. The tower
    shows no windows from outside, so this one is an enchanted pane."""
    y = R - 0.02
    w, h, z0 = 1.5, 2.2, 1.0
    box("WinPane", (w, 0.02, h), (0, y + 0.02, z0 + h / 2), M["sky"], bev=0)
    shell("WinPaneArch", w / 2, 0, -0.01, 0.01, M["sky"], arc=(0, math.pi), segs=48,
          loc=(0, y + 0.02, z0 + h), rot=(math.pi / 2, 0, 0))
    # diamond lead cames
    B = Batch()
    step = 0.22
    top = z0 + h + w / 2
    for k in range(-14, 15):
        for sgn in (-1, 1):
            # line x = sgn * (z - z0) + k * step, clipped roughly to the opening
            L = math.sqrt(2) * (h + w / 2)
            cx = k * step
            B.box(M["iron"], (0.012, 0.01, L), (cx, y, z0 + (h + w / 2) / 2),
                  rx=0, ry=sgn * math.pi / 4)
    B.build("WinLeadRaw")
    # clip the leading to the arched opening with a boolean
    lead = bpy.data.objects["WinLeadRaw_Iron"]
    outline = [(-w / 2, z0), (w / 2, z0)]
    outline += [(w / 2 * math.cos(math.pi * k / 24), z0 + h + w / 2 * math.sin(math.pi * k / 24))
                for k in range(25)]
    verts = [(px, y + dy, pz) for dy in (-0.1, 0.1) for px, pz in outline]
    n = len(outline)
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    cutter = mesh_obj("WinCutter", verts, faces, M["iron"], smooth_angle=0)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    mod = lead.modifiers.new("clip", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.object = cutter
    mod.solver = "EXACT"
    # wooden frame, mullion and stone surround
    for sx in (-1, 1):
        box(f"WinJamb{sx}", (0.1, 0.14, h), (sx * (w / 2 + 0.05), y - 0.04, z0 + h / 2), M["darkwood"])
    shell("WinArchFrame", w / 2 + 0.1, w / 2, -0.07, 0.07, M["darkwood"], arc=(0, math.pi),
          segs=48, loc=(0, y - 0.04, z0 + h), rot=(math.pi / 2, 0, 0))
    box("WinMullion", (0.07, 0.1, h + w / 2 - 0.05), (0, y - 0.03, z0 + (h + w / 2) / 2), M["darkwood"])
    box("WinTransom", (w, 0.1, 0.07), (0, y - 0.03, z0 + h * 0.62), M["darkwood"])
    B = Batch()
    rnd = random.Random(31)
    n = 13
    for i in range(n):
        a = math.pi * i / (n - 1)
        r = w / 2 + 0.27
        B.box(M["blackstone"], (0.34 if i % 2 else 0.26, 0.18, 0.22),
              (r * math.cos(a), y - 0.06, z0 + h + r * math.sin(a)), ry=-a + math.pi / 2)
    for sx in (-1, 1):
        zz = z0
        while zz < z0 + h - 0.1:
            hh = rnd.uniform(0.28, 0.36)
            B.box(M["blackstone"], (0.34 if int(zz * 10) % 2 else 0.26, 0.18, hh - 0.02),
                  (sx * (w / 2 + 0.27), y - 0.06, zz + hh / 2))
            zz += hh
    B.build("WinSurround")
    box("WinSill", (w + 0.7, 0.4, 0.1), (0, y - 0.18, z0 - 0.05), M["stone"], bev=0.02)
    # potions and a candle on the sill
    for k in range(3):
        sphere(f"SillPotion{k}", 0.05, (-0.55 + k * 0.13, y - 0.2, z0 + 0.05), M["potions"][k], segs=12)
        cyl(f"SillPotionNeck{k}", 0.015, 0.06, (-0.55 + k * 0.13, y - 0.2, z0 + 0.12),
            M["potions"][k], verts=8)
    candle(M, "SillCandle", (0.55, y - 0.2, z0), h=0.16)
    # cool moonlight through the pane + a beam into the haze
    ld = bpy.data.lights.new("WinLight", "AREA")
    ld.energy = 60
    ld.size = 1.4
    ld.color = (0.5, 0.65, 1.0)
    o = bpy.data.objects.new("WinLight", ld)
    o.location = (0, y - 0.25, z0 + h / 2)
    o.rotation_euler = (math.radians(-90), 0, 0)
    bpy.context.collection.objects.link(o)
    ld = bpy.data.lights.new("WinBeam", "SPOT")
    ld.energy = 6000
    ld.color = (0.55, 0.7, 1.0)
    ld.spot_size = math.radians(30)
    ld.spot_blend = 0.4
    ld.shadow_soft_size = 0.05
    o = bpy.data.objects.new("WinBeam", ld)
    o.location = (0.3, y + 0.6, z0 + h + 0.5)
    aim = Vector((-0.6, 1.0, 0.0)) - o.location
    o.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(o)


# ---------------------------------------------------------------- furniture

def candle(M, name, loc, h=0.15, light=True, energy=6):
    x, y, z = loc
    cyl(name, 0.025, h, (x, y, z + h / 2), M["wax"], verts=12)
    sphere(name + "Flame", 0.018, (x, y, z + h + 0.025), M["flame"], scale=(1, 1, 1.8), segs=8)
    if light:
        point_light(name + "Light", (x, y, z + h + 0.08), energy, (1.0, 0.6, 0.25), radius=0.02)


def visitor_chair(M, name, loc, rz, cushion=None):
    """Homebase-style chair: backrest at local +y, the sitter faces local -y."""
    empty = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(empty)
    wood = M["wood"]
    parts = [box(name + "Seat", (0.45, 0.45, 0.05), (0, 0, 0.45), wood, bev=0.015)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(f"{name}Leg{sx}{sy}", 0.025, 0.45,
                             (sx * 0.19, sy * 0.19, 0.225), wood, verts=10))
        parts.append(box(f"{name}Stretch{sx}", (0.025, 0.36, 0.025), (sx * 0.19, 0, 0.13), wood))
    parts.append(box(name + "StretchF", (0.36, 0.025, 0.025), (0, -0.19, 0.18), wood))
    for sx in (-1, 1):
        parts.append(box(f"{name}Back{sx}", (0.05, 0.05, 0.55), (sx * 0.19, 0.2, 0.74),
                         wood, rot=(math.radians(-6), 0, 0)))
    parts.append(box(name + "BackRail", (0.43, 0.045, 0.12), (0, 0.23, 0.96), wood,
                     rot=(math.radians(-6), 0, 0), bev=0.015))
    for i in range(3):
        parts.append(box(f"{name}Spindle{i}", (0.025, 0.025, 0.4), ((i - 1) * 0.1, 0.21, 0.69),
                         wood, rot=(math.radians(-6), 0, 0)))
    if cushion:
        parts.append(box(name + "Cushion", (0.4, 0.4, 0.06), (0, 0, 0.5), cushion, bev=0.025))
    for p in parts:
        p.parent = empty
    empty.location = loc
    empty.rotation_euler = (0, 0, rz)
    return empty


def build_desk(M):
    """Heavy oak writing desk of the Blackstaff, facing the visitors."""
    cx, cy = 0.0, 2.45
    W, D, Ht = 2.3, 1.05, 0.78
    box("DeskTop", (W, D, 0.08), (cx, cy, Ht - 0.04), M["wood"], bev=0.02)
    box("DeskTopEdge", (W + 0.06, D + 0.06, 0.04), (cx, cy, Ht - 0.1), M["darkwood"], bev=0.012)
    box("DeskLeather", (W - 0.3, D - 0.25, 0.006), (cx, cy + 0.02, Ht + 0.003), M["leather"], bev=0)
    # pedestals with drawers, front panel toward the visitors
    for sx in (-1, 1):
        px = cx + sx * (W / 2 - 0.35)
        box(f"DeskPedestal{sx}", (0.62, D - 0.1, Ht - 0.2), (px, cy, (Ht - 0.2) / 2 + 0.06),
            M["darkwood"], bev=0.015)
        box(f"DeskPlinth{sx}", (0.68, D - 0.04, 0.08), (px, cy, 0.09), M["darkwood"], bev=0.015)
        for k in range(3):
            zz = 0.22 + k * 0.17
            box(f"Drawer{sx}{k}", (0.52, 0.02, 0.14), (px, cy + D / 2 - 0.04, zz), M["wood"],
                bev=0.008)
            box(f"DrawerPull{sx}{k}", (0.1, 0.02, 0.02), (px, cy + D / 2 - 0.02, zz), M["iron"],
                bev=0.003)
        # carved panel with iron studs on the visitors' side
        box(f"DeskFrontPanel{sx}", (0.5, 0.02, 0.45), (px, cy - D / 2 + 0.04, 0.4), M["wood"],
            bev=0.01)
        for dx in (-0.2, 0.2):
            for dz in (0.2, 0.6):
                sphere(f"DeskStud{sx}{dx}{dz}", 0.015, (px + dx, cy - D / 2 + 0.025, dz), M["iron"],
                       segs=8)
    box("DeskModesty", (W - 1.3, 0.04, 0.4), (cx, cy - D / 2 + 0.08, Ht - 0.32), M["darkwood"])
    box("DeskApron", (W - 0.1, 0.04, 0.1), (cx, cy - D / 2 + 0.05, Ht - 0.17), M["darkwood"])

    zt = Ht + 0.006

    def P(dx, dy, z):
        return (cx + dx, cy + dy, z)

    B = Batch()
    rnd = random.Random(5)
    for k in range(6):
        B.box(M["paper"], (0.21, 0.29, 0.002), P(0.55 + rnd.uniform(-0.02, 0.02), -0.05,
                                                 zt + 0.002 + k * 0.004),
              rz=rnd.uniform(-0.2, 0.2))
    for k in range(3):
        B.box(M["parchment"], (0.21, 0.29, 0.002), P(-0.35 + k * 0.08, -0.15, zt + 0.002 + k * 0.002),
              rz=rnd.uniform(-0.5, 0.5))
    for k in range(4):
        B.box(M["bookcols"][k], (0.24, 0.32, 0.05), P(0.9, 0.25, zt + 0.025 + k * 0.052),
              rz=rnd.uniform(-0.15, 0.15))
    B.build("DeskPapers")
    # open ledger in front of the chair
    for s in (-1, 1):
        box(f"Ledger{s}", (0.2, 0.29, 0.012), P(s * 0.105, 0.05, zt + 0.014), M["paper"],
            rot=(0, s * math.radians(-4), 0), bev=0.002)
    box("LedgerCover", (0.44, 0.31, 0.01), P(0, 0.05, zt + 0.005), M["leather"], bev=0.003)
    # inkwell, quill, seal
    cyl("Inkwell", 0.04, 0.06, P(0.3, 0.2, zt + 0.03), M["glass"], verts=16)
    cyl("InkwellInk", 0.032, 0.04, P(0.3, 0.2, zt + 0.022), M["ink"], verts=16)
    cyl("Quill", 0.004, 0.3, P(0.3, 0.2, zt + 0.17), M["paper"],
        rot=(math.radians(25), 0, math.radians(30)), verts=6)
    sphere("QuillVane", 0.03, P(0.33, 0.14, zt + 0.25), M["paper"], scale=(0.3, 1, 3.0), segs=10)
    cyl("SealHandle", 0.02, 0.09, P(0.4, -0.3, zt + 0.06), M["darkwood"], verts=10)
    cyl("SealBase", 0.03, 0.03, P(0.4, -0.3, zt + 0.015), M["brass"], verts=14)
    cyl("SealWax", 0.018, 0.12, P(0.5, -0.32, zt + 0.015), M["wax_red"],
        rot=(0, math.radians(90), 0.4), verts=8)
    # candlestick trio in a pewter dish
    cyl("CandleDish", 0.12, 0.02, P(-0.85, 0.2, zt + 0.01), M["silver"], verts=20)
    for k, (dx, dy) in enumerate([(-0.05, 0.04), (0.05, 0.04), (0.0, -0.05)]):
        candle(M, f"DeskCandle{k}", P(-0.85 + dx, 0.2 + dy, zt + 0.02), h=0.14 + 0.05 * k,
               light=(k == 0), energy=25)
    # crystal ball on a three-clawed iron stand
    cyl("OrbStand", 0.07, 0.08, P(-0.6, 0.3, zt + 0.04), M["iron"], verts=12)
    sphere("ScryingOrb", 0.1, P(-0.6, 0.3, zt + 0.18), M["crystal"], segs=24)
    point_light("OrbLight", P(-0.6, 0.3, zt + 0.2), 6, (0.4, 0.6, 1.0), radius=0.1)
    # hourglass
    for s in (-1, 1):
        cyl(f"HourglassCap{s}", 0.05, 0.015, P(-0.35, 0.3, zt + 0.1 + s * 0.09), M["darkwood"],
            verts=12)
        cone(f"HourglassBulb{s}", 0.04, 0.008, 0.085, P(-0.35, 0.3, zt + 0.1 + s * 0.045),
             M["glass"], rot=(0 if s < 0 else math.pi, 0, 0), verts=14)
    for k in range(3):
        sphere(f"HourglassPost{k}", 0.008, P(-0.35 + 0.045 * math.cos(k * 2.1),
                                             0.3 + 0.045 * math.sin(k * 2.1), zt + 0.1),
               M["darkwood"], scale=(1, 1, 11), segs=6)
    sphere("DeskSkull", 0.09, P(1.0, -0.25, zt + 0.08), mat("Bone", (0.85, 0.8, 0.68), 0.6),
           scale=(1, 1.1, 0.9))
    # the Blackstaff itself, leaning on the desk end
    x, y = cx + W / 2 + 0.12, cy - 0.1
    cyl("Blackstaff", 0.028, 2.0, (x, y, 1.0), M["staff"], rot=(0, math.radians(-6), 0), verts=12)
    for zz in (0.4, 1.0, 1.6):
        cyl(f"BlackstaffBand{zz}", 0.034, 0.03, (x - 0.105 * (zz - 1.0), y, zz), M["silver"],
            rot=(0, math.radians(-6), 0), verts=12)
    sphere("BlackstaffTip", 0.045, (x - 0.105, y, 1.99), M["arcane"], segs=12)


def chair(M, name, loc, rz, high=False, cushion=None):
    """Carved high-backed chair; backrest at local +y, the sitter faces local -y."""
    x, y, z = loc
    c, s = math.cos(rz), math.sin(rz)

    def L(px, py, pz):
        return (x + px * c - py * s, y + px * s + py * c, z + pz)

    wood = M["walnut"]
    seat_h = 0.46
    box(name + "Seat", (0.6, 0.54, 0.06), L(0, 0, seat_h - 0.03), wood, rot=(0, 0, rz), bev=0.01)
    box(name + "Apron", (0.58, 0.5, 0.1), L(0, 0, seat_h - 0.1), wood, rot=(0, 0, rz), bev=0.008)
    box(name + "Cushion", (0.52, 0.48, 0.08), L(0, -0.01, seat_h + 0.04), cushion or M["leather"],
        rot=(0, 0, rz), bev=0.035)
    for px in (-0.26, 0.26):
        lathe(f"{name}FrontLeg{px}", TURNED_LEG, L(px, -0.23, -0.04 + 0.04), wood, segs=16)
        box(f"{name}BackLeg{px}", (0.06, 0.06, seat_h - 0.05), L(px, 0.23, (seat_h - 0.05) / 2),
            wood, rot=(0, 0, rz), bev=0.008)
    box(name + "Stretcher", (0.5, 0.03, 0.04), L(0, -0.23, 0.12), wood, rot=(0, 0, rz), bev=0.005)
    back_h = 1.45 if high else 0.6
    for px in (-0.27, 0.27):
        box(f"{name}Stile{px}", (0.07, 0.07, back_h), L(px, 0.25, seat_h + back_h / 2), wood,
            rot=(0, 0, rz), bev=0.01)
        lathe(f"{name}Finial{px}", FINIAL, L(px, 0.25, seat_h + back_h), wood, segs=16)
    box(name + "BackPanel", (0.48, 0.04, back_h - 0.25), L(0, 0.26, seat_h + back_h / 2 + 0.02),
        wood, rot=(0, 0, rz), bev=0.006)
    box(name + "BackPad", (0.42, 0.05, back_h - 0.4), L(0, 0.225, seat_h + back_h / 2 + 0.02),
        cushion or M["leather"], rot=(0, 0, rz), bev=0.02)
    # tufting buttons
    for i in range(3):
        for j in range(5):
            sphere(f"{name}Tuft{i}{j}", 0.01, L(-0.12 + i * 0.12, 0.198,
                                                 seat_h + 0.35 + j * (back_h - 0.6) / 4),
                   M["silver"], segs=6)
    box(name + "TopRail", (0.6, 0.08, 0.1), L(0, 0.25, seat_h + back_h - 0.02), wood,
        rot=(0, 0, rz), bev=0.015)
    for px in (-0.31, 0.31):
        box(f"{name}Arm{px}", (0.07, 0.52, 0.045), L(px, -0.01, seat_h + 0.26), wood,
            rot=(0, 0, rz), bev=0.012)
        sphere(f"{name}ArmScroll{px}", 0.04, L(px, -0.27, seat_h + 0.26), wood, segs=12)
        lathe(f"{name}ArmPost{px}", [(0.02, 0.0), (0.028, 0.03), (0.016, 0.1), (0.026, 0.17),
                                     (0.02, 0.22)], L(px, -0.22, seat_h + 0.02), wood, segs=12)
    if high:
        # pointed crest with the Blackstaff's gem
        verts = [L(-0.3, 0.25, seat_h + back_h + 0.03), L(0.3, 0.25, seat_h + back_h + 0.03),
                 L(0.0, 0.25, seat_h + back_h + 0.3)]
        verts += [(vx + 0.02 * s, vy - 0.02 * c, vz) for vx, vy, vz in verts]
        verts = [(vx - 0.01 * s, vy + 0.01 * c, vz) for vx, vy, vz in verts]
        mesh_obj(name + "Crest", verts, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2),
                                         (2, 5, 3, 0)], wood, smooth_angle=0)
        sphere(name + "CrestGem", 0.035, L(0, 0.225, seat_h + back_h + 0.13), M["arcane"], segs=12)


def build_seating(M):
    chair(M, "BlackstaffChair", (0, 3.3, 0.05), 0.0, high=True, cushion=M["velvet"])
    visitor_chair(M, "VisitorChairL", (-0.7, 1.15, 0.05), math.pi + math.radians(12), M["velvet"])
    visitor_chair(M, "VisitorChairR", (0.7, 1.15, 0.05), math.pi - math.radians(18))
    shell("Rug", 2.3, 0, 0.05, 0.065, M["rug"], loc=(0, 2.25, 0), segs=96)
    bpy.context.object.scale = (1.3, 0.9, 1.0)


def build_bookshelves(M):
    """Curved shelves in the wall bays either side of the window."""
    B = Batch()
    rnd = random.Random(9)
    r_back, r_front = R - 0.14, R - 0.56
    bays = [(47, 72), (140, 156)]
    gilt = M["brass"]
    for b0, b1 in bays:
        a0, a1 = math.radians(b0), math.radians(b1)
        top = H - 0.55
        shell(f"ShelfBack{b0}", r_back, r_back - 0.03, 0.1, top, M["walnut"], arc=(a0, a1), segs=64)
        shell(f"ShelfPlinth{b0}", r_front + 0.02, r_back, 0.06, 0.24, M["walnut"],
              arc=(a0 - 0.01, a1 + 0.01), segs=64)
        shell(f"ShelfPlinthToe{b0}", r_front - 0.01, r_front - 0.03, 0.06, 0.1, M["walnut"],
              arc=(a0 - 0.01, a1 + 0.01), segs=64)
        shell(f"ShelfCrown{b0}", r_front - 0.06, r_back, top, top + 0.08, M["walnut"],
              arc=(a0 - 0.02, a1 + 0.02), segs=64, r_out_top=r_front - 0.1)
        shell(f"ShelfCrownCap{b0}", r_front - 0.11, r_back, top + 0.08, top + 0.12, M["walnut"],
              arc=(a0 - 0.025, a1 + 0.025), segs=64)
        levels = [0.24 + i * 0.47 for i in range(8)]
        ndiv = 2
        divs = [a0 + (a1 - a0) * k / ndiv for k in range(ndiv + 1)]
        for k, zz in enumerate(levels):
            shell(f"ShelfBoard{b0}_{k}", r_front, r_back, zz, zz + 0.03, M["walnut"],
                  arc=(a0, a1), segs=64)
            shell(f"ShelfLip{b0}_{k}", r_front + 0.005, r_front - 0.012, zz - 0.02, zz + 0.03,
                  M["walnut"], arc=(a0, a1), segs=64)
            if zz + 0.47 > top:
                break
            for d0, d1 in zip(divs, divs[1:]):
                a = d0 + 0.012
                while a < d1 - 0.015:
                    tw = rnd.uniform(0.025, 0.07)
                    th = rnd.uniform(0.26, 0.42)
                    td = rnd.uniform(0.2, 0.3)
                    rm = r_back - 0.03 - td / 2
                    da = tw / rm
                    if rnd.random() < 0.05:
                        a += da * 2.5
                        continue
                    lean = rnd.uniform(-0.15, 0.15) if rnd.random() < 0.12 else 0
                    am = a + da / 2
                    zc = zz + 0.03 + th / 2 - abs(lean) * 0.05
                    B.box(rnd.choice(M["bookcols"]), (td, tw, th), polar(rm, am, zc), rz=am, rx=lean)
                    # pages show as a pale inset strip on the fore-edge side
                    if tw > 0.04 and not lean:
                        for bz in (-0.36, 0.34):
                            B.box(gilt, (0.004, tw + 0.002, 0.008), polar(rm - td / 2, am, zc + bz * th),
                                  rz=am)
                    a += da * 1.03
        for a in divs:
            box(f"ShelfDiv{b0}_{a:.2f}", (r_back - r_front, 0.045, top - 0.1),
                polar((r_back + r_front) / 2, a, (top + 0.1) / 2), M["walnut"], rot=(0, 0, a), bev=0.008)
    B.build("Books", bev=0.003)


def build_pigeonholes(M):
    """Scroll cabinet of the office: registered petitions, licences, sealed writs."""
    a = math.radians(34)
    cx, cy, _ = polar(R - 0.4, a)
    rz = a - math.pi / 2          # local -Y (the open front) faces the room
    c, s = math.cos(rz), math.sin(rz)

    def L(px, py, pz):
        return (cx + px * c - py * s, cy + px * s + py * c, pz)

    w, d, h = 1.5, 0.5, 2.6
    box("Pigeonhole", (w, d, 0.06), L(0, 0, 0.6), M["oak"], rot=(0, 0, rz))
    box("PigeonholeBase", (w, d, 0.55), L(0, 0, 0.3), M["oak"], rot=(0, 0, rz))
    box("PigeonholeToe", (w + 0.06, d + 0.04, 0.1), L(0, 0, 0.07), M["darkwood"], rot=(0, 0, rz),
        bev=0.01)
    box("PigeonholeTop", (w + 0.1, d + 0.06, 0.08), L(0, 0, 0.6 + h), M["oak"], rot=(0, 0, rz))
    box("PigeonholeCornice", (w + 0.18, d + 0.1, 0.06), L(0, -0.02, 0.6 + h + 0.07), M["darkwood"],
        rot=(0, 0, rz), bev=0.015)
    for sx in (-1, 1):
        box(f"PigeonholeSide{sx}", (0.05, d + 0.02, h + 0.6), L(sx * (w / 2 + 0.025), 0, (h + 0.6) / 2),
            M["darkwood"], rot=(0, 0, rz), bev=0.01)
        # carved pilaster strips on the front edge of the sides
        box(f"PigeonholePilaster{sx}", (0.07, 0.03, h - 0.1), L(sx * (w / 2 + 0.03), -d / 2 - 0.01,
                                                                  0.6 + h / 2),
            M["oak"], rot=(0, 0, rz), bev=0.01)
    # drawer fronts with pulls and brass label frames
    for i in range(3):
        px = -w / 3 + i * w / 3
        box(f"CabDrawer{i}", (w / 3 - 0.04, 0.02, 0.42), L(px, -d / 2 - 0.005, 0.32), M["oak"],
            rot=(0, 0, rz), bev=0.01)
        box(f"CabLabel{i}", (0.12, 0.012, 0.06), L(px, -d / 2 - 0.02, 0.42), M["brass"],
            rot=(0, 0, rz), bev=0.003)
        box(f"CabLabelCard{i}", (0.1, 0.012, 0.045), L(px, -d / 2 - 0.022, 0.42), M["paper"],
            rot=(0, 0, rz), bev=0)
    B = Batch()
    rnd = random.Random(4)
    cols, rows = 6, 8
    cw, rh = w / cols, (h - 0.1) / rows
    for i in range(cols + 1):
        B.box(M["oak"], (0.025, d, h), L(-w / 2 + i * cw, 0, 0.6 + h / 2), rz=rz)
    for j in range(rows + 1):
        B.box(M["oak"], (w, d, 0.02), L(0, 0, 0.63 + j * rh), rz=rz)
    B.box(M["oak"], (w, 0.02, h), L(0, d / 2 - 0.01, 0.6 + h / 2), rz=rz)
    for i in range(cols):
        for j in range(rows):
            for k in range(rnd.randint(0, 4)):
                px = -w / 2 + (i + 0.5) * cw + rnd.uniform(-0.06, 0.06)
                pz = 0.65 + j * rh + 0.035 + (k // 2) * 0.05
                mat_ = M["parchment"] if rnd.random() < 0.8 else M["paper"]
                B.cyl(mat_, 0.022, d * 0.9, L(px, -0.03, pz), rz=rz, rx=math.pi / 2, segs=8)
                if rnd.random() < 0.3:
                    B.box(M["wax_red"], (0.03, 0.005, 0.03), L(px, -d / 2 + 0.02, pz), rz=rz)
    B.build("Scrolls", bev=0.002)
    for i in range(3):
        box(f"DrawerPull{i}", (0.12, 0.02, 0.03), L(-w / 3 + i * w / 3, -d / 2 - 0.025, 0.26),
            M["brass"], rot=(0, 0, rz), bev=0.004)


def build_fireplace(M):
    a = math.radians(124)
    cx, cy, _ = polar(R - 0.3, a)
    rz = a - math.pi / 2          # local -Y faces the room
    c, s = math.cos(rz), math.sin(rz)

    def L(px, py, pz):
        return (cx + px * c - py * s, cy + px * s + py * c, pz)

    box("Hearth", (2.1, 0.9, 0.1), L(0, -0.2, 0.1), M["stone"], rot=(0, 0, rz), bev=0.02)
    box("HearthEdge", (2.16, 0.06, 0.12), L(0, -0.64, 0.1), M["blackstone"], rot=(0, 0, rz),
        bev=0.02)
    box("FPBack", (1.2, 0.05, 1.2), L(0, 0.3, 0.7), mat("Soot", (0.02, 0.018, 0.016), 1),
        rot=(0, 0, rz), bev=0)
    # jambs, lintel and chimney breast as individually dressed stones
    B = Batch()
    rnd = random.Random(14)
    for sx in (-1, 1):
        zz = 0.15
        k = 0
        while zz < 1.3:
            hh = rnd.uniform(0.22, 0.3)
            ww = 0.36 if k % 2 else 0.3
            B.box(M["stone"], (ww, 0.5, hh - 0.015), L(sx * (0.72 + (ww - 0.3) / 2), -0.05, zz + hh / 2),
                  rz=rz)
            zz += hh
            k += 1
    # flat arch over the opening: wedge-cut voussoirs and a keystone
    for k in range(7):
        px = -0.6 + k * 0.2
        lean = math.radians(-px * 22)
        B.box(M["blackstone"] if k == 3 else M["stone"], (0.19, 0.5, 0.36 if k == 3 else 0.3),
              L(px, -0.06 if k == 3 else -0.05, 1.47 if k == 3 else 1.44), rz=rz, ry=lean)
    # chimney breast above the mantel, coursed and staggered
    rowz = 1.86
    row = 0
    while rowz < H - 0.25:
        hh = 0.28
        px = -0.8 + (0.0 if row % 2 else 0.17)
        while px < 0.8:
            ww = min(rnd.uniform(0.3, 0.45), 0.8 - px)
            if ww > 0.08:
                B.box(M["stone"], (ww - 0.015, 0.36, hh - 0.015),
                      L(px + ww / 2, 0.12 + rnd.uniform(-0.01, 0.01), rowz + hh / 2), rz=rz)
            px += ww
        rowz += hh
        row += 1
        if row == 1:
            # a string course where the breast steps back
            box("FPString", (1.72, 0.42, 0.08), L(0, 0.1, rowz), M["blackstone"], rot=(0, 0, rz),
                bev=0.015)
    B.build("FPStones", bev=0.02)
    # mantel shelf on carved corbels with a moulded edge
    box("FPMantel", (2.3, 0.62, 0.09), L(0, -0.06, 1.72), M["darkwood"], rot=(0, 0, rz), bev=0.02)
    box("FPMantelBead", (2.24, 0.05, 0.05), L(0, -0.37, 1.66), M["darkwood"], rot=(0, 0, rz),
        bev=0.02)
    box("FPMantelFrieze", (2.0, 0.08, 0.12), L(0, -0.3, 1.6), M["darkwood"], rot=(0, 0, rz),
        bev=0.01)
    for sx in (-1, 1):
        for k, (dy, dz, sz) in enumerate([(-0.25, 1.6, 0.14), (-0.33, 1.52, 0.1)]):
            box(f"FPCorbel{sx}{k}", (0.16, 0.12 + 0.08 * k, sz), L(sx * 0.95, dy + 0.04 * k, dz),
                M["darkwood"], rot=(0, 0, rz), bev=0.012)
        sphere(f"FPCorbelBoss{sx}", 0.03, L(sx * 0.95, -0.42, 1.52), M["darkwood"], segs=10)
    # andirons, logs and fire
    for sx in (-1, 1):
        box(f"Andiron{sx}", (0.04, 0.4, 0.04), L(sx * 0.3, 0.0, 0.2), M["iron"], rot=(0, 0, rz),
            bev=0)
    for i, (dx, tilt) in enumerate([(-0.12, 0.25), (0.12, -0.25), (0.0, 0.0)]):
        cyl(f"Log{i}", 0.06, 0.7, L(dx, 0.05, 0.27 + (0.08 if i == 2 else 0)), M["oak"],
            rot=(0, math.pi / 2, rz + tilt), verts=10)
    rnd = random.Random(2)
    for i in range(9):
        hh = 0.25 + rnd.uniform(0, 0.25)
        f = sphere(f"Flame{i}", 0.08, L(rnd.uniform(-0.25, 0.25), 0.05, 0.35 + hh / 2), M["fire"],
                   scale=(0.8, 0.8, hh / 0.16), segs=10)
        f.rotation_euler = (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0)
    for i in range(10):
        sphere(f"Ember{i}", 0.025, L(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.1, 0.15), 0.18),
               M["ember"], segs=8)
    point_light("FireLight", L(0, -0.6, 0.6), 700, (1.0, 0.45, 0.15), radius=0.3)
    # portrait of the first Blackstaff above the mantel
    box("PortraitFrame", (1.0, 0.06, 1.25), L(0, -0.1, 2.75), M["brass"], rot=(0, 0, rz), bev=0.02)
    box("PortraitCanvas", (0.86, 0.02, 1.1), L(0, -0.13, 2.75), M["canvas"], rot=(0, 0, rz), bev=0)
    sphere("PortraitFigure", 0.2, L(0, -0.145, 2.65), mat("PortraitRobe", (0.01, 0.01, 0.012), 0.6),
           scale=(1.0, 0.1, 1.6), segs=16)
    sphere("PortraitHead", 0.09, L(0, -0.145, 2.98), mat("PortraitSkin", (0.35, 0.22, 0.14), 0.6),
           scale=(1.0, 0.2, 1.2), segs=12)
    # mantel objects
    for k, px in enumerate((-0.8, 0.8)):
        cyl(f"MantelCandle{k}", 0.025, 0.25, L(px, -0.05, 1.8), M["wax"], verts=10)
        sphere(f"MantelFlame{k}", 0.016, L(px, -0.05, 1.95), M["flame"], scale=(1, 1, 1.8), segs=8)
    sphere("MantelSkull", 0.09, L(-0.45, -0.05, 1.75), mat("Bone", (0.85, 0.8, 0.68), 0.6),
           scale=(1, 1.1, 0.9))
    for k in range(5):
        sphere(f"MantelPotion{k}", 0.045, L(0.2 + k * 0.1, -0.05, 1.72), M["potions"][k], segs=10)


def build_map_table(M):
    cx, cy = 3.0, 1.45
    cyl("MapTableTop", 0.85, 0.06, (cx, cy, 0.86), M["oak"], verts=48)
    cyl("MapTableRim", 0.88, 0.04, (cx, cy, 0.84), M["brass"], verts=48)
    cyl("MapTableStem", 0.1, 0.75, (cx, cy, 0.45), M["oak"], verts=16)
    for i in range(3):
        a = 2 * math.pi * i / 3
        box(f"MapTableFoot{i}", (0.55, 0.08, 0.08), (cx + 0.25 * math.cos(a), cy + 0.25 * math.sin(a),
                                                       0.1), M["oak"], rot=(0, math.radians(-12), a))
    box("CityMapSheet", (1.1, 0.8, 0.004), (cx, cy, 0.892), M["map"], rot=(0, 0, 0.2), bev=0)
    rnd = random.Random(8)
    for i in range(7):
        x, y = cx + rnd.uniform(-0.4, 0.4), cy + rnd.uniform(-0.3, 0.3)
        cone(f"MapPin{i}", 0.02, 0, 0.06, (x, y, 0.92), rnd.choice((M["wax_red"], M["arcane"],
                                                                     M["silver"])), verts=8)
    # floating illusion of the city above the table
    for i in range(14):
        x, y = cx + rnd.uniform(-0.35, 0.35), cy + rnd.uniform(-0.25, 0.25)
        hh = rnd.uniform(0.04, 0.18)
        box(f"IllusionTower{i}", (0.05, 0.05, hh), (x, y, 1.35 + hh / 2), M["arcane_cyan"], bev=0)
    shell("IllusionDisc", 0.5, 0.48, 1.34, 1.345, M["arcane_cyan"], loc=(cx, cy, 0), segs=48)
    point_light("IllusionLight", (cx, cy, 1.5), 15, (0.3, 0.75, 1.0), radius=0.2)


def build_stair(M):
    """Stone spiral stair climbing to the folded floors above."""
    cx, cy, _ = polar(3.85, math.radians(166))
    cyl("StairNewel", 0.16, H + 0.3, (cx, cy, (H + 0.3) / 2), M["stone"], verts=16)
    B = Batch()
    n = 22
    for i in range(n):
        a = math.radians(-60) + i * math.radians(20)
        z = (i + 1) * (H / n)
        x, y, _ = polar(0.58, a)
        B.box(M["blackstone"], (0.9, 0.36, H / n), (cx + x, cy + y, z - H / n / 2), rz=a)
        B.box(M["darkwood"], (0.92, 0.38, 0.04), (cx + x, cy + y, z + 0.02), rz=a)
        rx, ry, _ = polar(0.98, a)
        B.box(M["darkwood"], (0.05, 0.05, 0.9), (cx + rx, cy + ry, z + 0.47), rz=a)
    B.build("Stair")
    pts = []
    for i in range(n * 4 + 1):
        t = i / 4
        a = math.radians(-60) + t * math.radians(20)
        pts.append(Vector(polar(0.98, a, (t + 1) * (H / n) + 0.92)) + Vector((cx, cy, 0)))
    cu = bpy.data.curves.new("Handrail", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.03
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (*v, 1)
    o = bpy.data.objects.new("Handrail", cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(M["darkwood"])


def build_flying_books(M):
    rnd = random.Random(12)
    for i in range(4):
        a = math.radians(rnd.uniform(40, 140))
        px, py, _ = polar(R - 1.4, a)
        box(f"FlyBook{i}", (0.22, 0.16, 0.05), (px, py, rnd.uniform(2.6, 3.6)),
            rnd.choice(M["bookcols"]), rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4),
                                             rnd.uniform(0, 6)), bev=0.008)


def build_chandelier(M):
    """Wrought-iron wheel chandelier with candles, hung from the rafters."""
    cx, cy, z = 0, 2.3, 3.5
    shell("ChandelierWheel", 0.9, 0.84, z - 0.03, z + 0.03, M["iron"], loc=(cx, cy, 0), segs=64)
    shell("ChandelierHub", 0.12, 0.0, z - 0.06, z + 0.06, M["iron"], loc=(cx, cy, 0), segs=16)
    for i in range(6):
        a = 2 * math.pi * i / 6
        box(f"ChandelierSpoke{i}", (0.78, 0.025, 0.025), (cx + 0.45 * math.cos(a),
                                                          cy + 0.45 * math.sin(a), z),
            M["iron"], rot=(0, 0, a), bev=0)
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        p0 = Vector((cx + 0.87 * math.cos(a), cy + 0.87 * math.sin(a), z))
        p1 = Vector((cx, cy, H + 0.1))
        mid = (p0 + p1) / 2
        d = p1 - p0
        o = cyl(f"ChandelierChain{i}", 0.008, d.length, tuple(mid), M["iron"], verts=6)
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    for i in range(10):
        a = 2 * math.pi * i / 10
        px, py = cx + 0.87 * math.cos(a), cy + 0.87 * math.sin(a)
        cyl(f"ChandelierCup{i}", 0.04, 0.03, (px, py, z + 0.045), M["iron"], verts=10)
        candle(M, f"ChandelierCandle{i}", (px, py, z + 0.06), h=0.12 + 0.04 * (i % 3), light=False)
    point_light("ChandelierLight", (cx, cy, z + 0.2), 380, (1.0, 0.6, 0.28), radius=0.9)


def build_props(M):
    # potted plants flanking the window
    pot = [(0.0, 0.0), (0.15, 0.0), (0.17, 0.03), (0.2, 0.3), (0.23, 0.33), (0.23, 0.38),
           (0.2, 0.38), (0.19, 0.34)]
    for k, deg in enumerate((76, 104)):
        x, y, _ = polar(R - 0.45, math.radians(deg))
        lathe(f"Pot{k}", pot, (x, y, 0.05), M["clay"], segs=28)
        shell(f"Soil{k}", 0.19, 0, 0.36, 0.37, mat("Soil", (0.05, 0.03, 0.02), 1), loc=(x, y, 0),
              segs=28)
        for j in range(5):
            sphere(f"Plant{k}_{j}", 0.18, (x + random.uniform(-0.12, 0.12), y + random.uniform(-0.12, 0.12),
                                           0.6 + random.uniform(0, 0.4)), M["leaf"],
                   scale=(1, 1, 1.4), segs=14)


def build_atmosphere():
    """Light haze inside the room so the window casts a visible beam."""
    shell("Haze", R - 0.05, 0, 0.1, H - 0.05, haze_mat(), segs=64)
    bpy.context.object.visible_shadow = False


def haze_mat():
    m = bpy.data.materials.new("HazeMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.02
    pv.inputs["Anisotropy"].default_value = 0.35
    pv.inputs["Color"].default_value = (0.9, 0.85, 0.8, 1)
    nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
    return m


# ---------------------------------------------------------------- world + camera

def setup_world_and_camera(samples, shot="wide"):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.018, 1)
    bg.inputs["Strength"].default_value = 1.0

    ld = bpy.data.lights.new("Fill", "AREA")
    ld.energy = 650
    ld.size = 6
    ld.color = (0.7, 0.72, 1.0)
    fill = bpy.data.objects.new("Fill", ld)
    fill.location = (6, -9, 8)
    fill.rotation_euler = (Vector((0, 1, 1)) - fill.location).to_track_quat("-Z", "Y").to_euler()
    fill.visible_glossy = False
    scene.collection.objects.link(fill)

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    if shot == "close":
        cam_data.lens = 32
        cam.location = (1.3, -1.2, 1.55)
        target = Vector((-0.2, 2.6, 1.05))
    else:
        cam_data.lens = 30
        cam.location = (2.6, -8.6, 4.6)
        target = Vector((0, 2.3, 1.55))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    if shot == "top":
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = 2 * (R + WALL) + 1.2
        cam_data.clip_end = 60
        cam.location = (0, R / 2 - 0.2, 20)
        cam.rotation_euler = (0, 0, 0)
        scene.render.resolution_x, scene.render.resolution_y = 1400, 820
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.volume_bounces = 0
    scene.cycles.volume_step_rate = 4.0
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.6


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = None
    samples = 128
    blend_out = None
    shot = "wide"
    res = 100
    for i, a in enumerate(argv):
        if a == "--render":
            out = argv[i + 1]
        elif a == "--samples":
            samples = int(argv[i + 1])
        elif a == "--shot":
            shot = argv[i + 1]
        elif a == "--save":
            blend_out = argv[i + 1]
        elif a == "--res":
            res = int(argv[i + 1])

    reset()
    M = build_materials()
    build_room(M)
    build_window(M)
    build_door(M)
    build_desk(M)
    build_seating(M)
    build_bookshelves(M)
    build_pigeonholes(M)
    build_fireplace(M)
    build_map_table(M)
    build_stair(M)
    build_flying_books(M)
    build_chandelier(M)
    build_props(M)
    build_atmosphere()
    setup_world_and_camera(samples, shot)
    bpy.context.scene.render.resolution_percentage = res

    if blend_out:
        bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    if out:
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)


main()
