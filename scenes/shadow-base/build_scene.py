"""Build an exterior diorama of the Shadow party's compound in Blender.

Main hall, training yard, a five-room dormitory, watchtower, gate and props,
in the same stylised diorama look as scenes/homebase.

Run with:  python3 scenes/shadow-base/build_scene.py [--render out.png] [--samples N]
           [--shot wide|close|top|pergola] [--time day|night] [--res percent]
           [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    scenes/blender.sh scenes/shadow-base/build_scene.py --render out.png
"""
import math
import random
import sys

import bpy
from mathutils import Euler, Vector

random.seed(11)

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


def noisy_mat(name, c1, c2, scale=8.0, rough=0.7, stretch=(1, 1, 1)):
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
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
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


def cone(name, r1, r2, depth, loc, material, rot=(0, 0, 0), verts=16, smooth=True):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    if smooth:
        bpy.ops.object.shade_smooth()
    return assign(o, material)


def torus(name, R, r, loc, material, rot=(0, 0, 0), segs=48):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=segs,
                                     location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return assign(o, material)


def mesh(name, verts, faces, material, solid=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    if solid:
        mod = o.modifiers.new("solid", "SOLIDIFY")
        mod.thickness = solid
        mod.offset = 1
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


def group(name, parts, loc=(0, 0, 0), rz=0.0, parent=None):
    """Parent parts (built in local coords) to a new empty and place it."""
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    for p in parts:
        p.parent = e
    e.location = loc
    e.rotation_euler = (0, 0, rz)
    if parent:
        e.parent = parent
    return e


# ---------------------------------------------------------------- materials

PARTY = [(0.70, 0.08, 0.10), (0.05, 0.50, 0.55), (0.90, 0.65, 0.12),
         (0.45, 0.15, 0.70), (0.12, 0.48, 0.18)]   # one door colour per member


def build_materials():
    M = {}
    M["stone"] = noisy_mat("Stone", (0.30, 0.29, 0.28), (0.44, 0.43, 0.41), 6, 0.9)
    M["flag"] = noisy_mat("Flagstone", (0.46, 0.44, 0.40), (0.56, 0.54, 0.50), 5, 0.9)
    M["wood"] = noisy_mat("Wood", (0.36, 0.21, 0.10), (0.46, 0.29, 0.15),
                          5, 0.6, stretch=(1, 1, 10))
    M["darkwood"] = noisy_mat("DarkWood", (0.14, 0.08, 0.04), (0.20, 0.12, 0.06),
                              5, 0.55, stretch=(1, 1, 10))
    M["log"] = noisy_mat("Log", (0.26, 0.17, 0.09), (0.36, 0.25, 0.14),
                         4, 0.8, stretch=(1, 1, 6))
    M["plaster"] = noisy_mat("Plaster", (0.78, 0.72, 0.60), (0.85, 0.80, 0.69), 3, 0.95)
    M["slate"] = noisy_mat("Slate", (0.17, 0.22, 0.31), (0.22, 0.27, 0.36), 9, 0.6)
    M["slate2"] = noisy_mat("Slate2", (0.13, 0.17, 0.25), (0.17, 0.21, 0.29), 9, 0.6)
    M["slate3"] = noisy_mat("Slate3", (0.24, 0.29, 0.38), (0.29, 0.34, 0.43), 9, 0.6)
    M["ridge"] = mat("Ridge", (0.10, 0.12, 0.17), 0.5)
    M["grass"] = noisy_mat("Grass", (0.15, 0.34, 0.07), (0.21, 0.42, 0.10), 3, 0.95)
    M["dirt"] = noisy_mat("Dirt", (0.50, 0.38, 0.24), (0.58, 0.45, 0.30), 6, 1.0)
    M["leaf"] = noisy_mat("Leaf", (0.12, 0.30, 0.07), (0.19, 0.40, 0.11), 4, 0.9)
    M["pine"] = noisy_mat("Pine", (0.05, 0.20, 0.11), (0.08, 0.26, 0.14), 4, 0.9)
    M["straw"] = noisy_mat("Straw", (0.70, 0.55, 0.22), (0.82, 0.67, 0.32), 9, 0.95,
                           stretch=(1, 1, 8))
    M["burlap"] = noisy_mat("Burlap", (0.55, 0.43, 0.27), (0.63, 0.51, 0.33), 30, 1.0)
    M["iron"] = mat("Iron", (0.12, 0.12, 0.13), 0.45, 1.0)
    M["steel"] = mat("Steel", (0.7, 0.72, 0.75), 0.25, 1.0)
    M["silver"] = mat("Silver", (0.85, 0.87, 0.92), 0.2, 1.0)
    M["brass"] = mat("Brass", (0.8, 0.55, 0.25), 0.35, 1.0)
    M["rope"] = mat("Rope", (0.55, 0.42, 0.25), 0.9)
    M["red"] = mat("RedPaint", (0.6, 0.05, 0.05), 0.7)
    M["white"] = mat("WhitePaint", (0.85, 0.82, 0.75), 0.8)
    M["shadow"] = mat("ShadowCloth", (0.035, 0.02, 0.06), 0.9)        # party colour
    M["shadow_trim"] = mat("ShadowTrim", (0.34, 0.16, 0.60), 0.8)
    M["void"] = mat("Void", (0.0, 0.0, 0.0), 1.0)
    M["window"] = mat("WindowWarm", (1.0, 0.6, 0.25), 0.5,
                      emit=(1.0, 0.55, 0.2), emit_strength=4.0)
    M["flame"] = mat("Flame", (1, 0.6, 0.2), 1, emit=(1.0, 0.5, 0.15), emit_strength=12)
    M["fire"] = mat("Fire", (0, 0, 0), 1, emit=(1.0, 0.16, 0.0), emit_strength=2.5)
    M["firecore"] = mat("FireCore", (0, 0, 0), 1, emit=(1.0, 0.42, 0.03), emit_strength=4)
    M["ember"] = mat("Ember", (0.1, 0.02, 0.0), 1, emit=(1.0, 0.18, 0.02), emit_strength=8)
    M["shadowfire"] = mat("ShadowFire", (0, 0, 0), 1, emit=(0.55, 0.25, 1.0), emit_strength=6)
    M["water"] = mat("Water", (0.08, 0.20, 0.30), 0.05)
    M["tuft"] = mat("GrassTuft", (0.20, 0.42, 0.09), 0.9)
    M["hedge"] = noisy_mat("Hedge", (0.08, 0.25, 0.06), (0.13, 0.33, 0.09), 5, 0.9)
    M["leaf_violet"] = noisy_mat("LeafViolet", (0.30, 0.09, 0.34), (0.42, 0.15, 0.44), 9, 0.85)
    M["soil"] = noisy_mat("Soil", (0.17, 0.10, 0.05), (0.23, 0.14, 0.08), 12, 1.0)
    M["wisteria"] = mat("Wisteria", (0.42, 0.22, 0.75), 0.7)
    M["wisteria2"] = mat("Wisteria2", (0.62, 0.45, 0.88), 0.7)
    M["bloom_red"] = mat("BloomRed", (0.75, 0.08, 0.12), 0.6)
    M["bloom_yellow"] = mat("BloomYellow", (0.95, 0.75, 0.15), 0.6)
    M["bloom_white"] = mat("BloomWhite", (0.9, 0.88, 0.82), 0.6)
    M["bloom_blue"] = mat("BloomBlue", (0.2, 0.35, 0.85), 0.6)
    M["globe"] = mat("Driftglobe", (1.0, 0.9, 0.7), 0.2, emit=(1.0, 0.85, 0.6), emit_strength=18)
    M["bulb"] = mat("Bulb", (1.0, 0.8, 0.5), 0.3, emit=(1.0, 0.75, 0.4), emit_strength=10)
    M["foam"] = mat("Foam", (0.95, 0.9, 0.75), 0.9)
    M["wax"] = mat("Wax", (0.95, 0.9, 0.75), 0.5)
    M["leather"] = mat("Leather", (0.35, 0.16, 0.06), 0.6)
    M["party"] = [mat(f"Party{i}", c, 0.6) for i, c in enumerate(PARTY)]
    return M


# ---------------------------------------------------------------- layout
#
# Plinth spans x 0..W, y 0..D. Camera looks from +x/-y, so tall things sit at the
# back (+y) and left (-x); the front and right edges only get a low fence.

W, D = 14.0, 12.0
HALL = (6.9, 9.3)          # hall centre; front wall faces -y
DORM = (2.1, 4.6)          # dormitory centre; front wall faces +x
YARD = (8.2, 13.4, 0.8, 6.8)
GATE_X = 6.9


def build_ground(M):
    box("Plinth", (W + 0.4, D + 0.4, 0.5), (W / 2, D / 2, -0.25), M["stone"], bev=0.05)
    box("PlinthLip", (W + 0.5, D + 0.5, 0.08), (W / 2, D / 2, -0.46), M["darkwood"], bev=0.02)
    box("Grass", (W, D, 0.08), (W / 2, D / 2, 0.04), M["grass"], bev=0.02)
    x0, x1, y0, y1 = YARD
    box("Yard", (x1 - x0, y1 - y0, 0.04), ((x0 + x1) / 2, (y0 + y1) / 2, 0.08), M["dirt"], bev=0.03)
    cyl("Campground", 1.6, 0.03, (5.0, 3.6, 0.09), M["dirt"], verts=32)
    # flagstone path from the gate to the hall door, plus a branch to the dorm
    pts = [(GATE_X + random.uniform(-0.35, 0.35), y) for y in [0.3 + 0.42 * k for k in range(17)]]
    pts += [(3.7 + 0.42 * k, 4.6 + random.uniform(-0.2, 0.2)) for k in range(7)]
    for i, (x, y) in enumerate(pts):
        for j in range(2 if y < 7 and x > 6 else 1):
            dx = (j - 0.5) * 0.5 if x > 6 else 0
            cyl(f"Flag{i}_{j}", random.uniform(0.17, 0.24), 0.04,
                (x + dx, y + random.uniform(-0.05, 0.05), 0.09), M["flag"],
                rot=(0, 0, random.uniform(0, 1)), verts=6, smooth=False)


def free_spot(x, y):
    """True where grass tufts may grow (not on paths, yard or buildings)."""
    blocked = [(0.6, 3.8, 1.2, 8.0), (3.4, 10.4, 7.0, 11.5), YARD, (6.2, 7.6, 0, 7.4),
               (3.7, 6.3, 2.3, 4.9), (10.4, 13.7, 7.9, 11.7), (3.6, 6.3, 5.4, 6.8)]
    return not any(a <= x <= b and c <= y <= d for a, b, c, d in blocked)


def build_grass(M):
    tuft = M["tuft"]
    n = 0
    while n < 140:
        x, y = random.uniform(0.5, W - 0.4), random.uniform(0.4, D - 0.5)
        if not free_spot(x, y):
            continue
        for k in range(3):
            cone(f"Tuft{n}_{k}", 0.025, 0.0, random.uniform(0.12, 0.22),
                 (x + random.uniform(-0.05, 0.05), y + random.uniform(-0.05, 0.05), 0.15),
                 tuft, rot=(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0), verts=4,
                 smooth=False)
        n += 1


# ---------------------------------------------------------------- building kit

def gable_prism(name, L, W_, h, z0, material):
    """Closed triangular prism (ridge along local x) that fills the gable ends."""
    v = [(-L / 2, -W_ / 2, z0), (L / 2, -W_ / 2, z0), (L / 2, W_ / 2, z0), (-L / 2, W_ / 2, z0),
         (-L / 2, 0, z0 + h), (L / 2, 0, z0 + h)]
    f = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    return mesh(name, v, f, material)


def shingles(M, name, Lo, a, ze, ang, length, tw=0.3, step=0.19):
    """All roof tiles of both slopes as one mesh: staggered rows of slightly jittered
    tiles, each tile picking one of three slate tones."""
    verts, faces, mats = [], [], []
    corners = [(sx * 0.5, sy * 0.5, sz * 0.5) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    rows = int(length / step)
    for side in (-1, 1):
        for k in range(rows):
            s = (k + 0.6) * step
            y = side * (a - s * math.cos(ang))
            z = ze + s * math.sin(ang)
            ny, nz = side * math.sin(ang), math.cos(ang)
            off = 0.1
            n = int(2 * Lo / tw)
            shift = 0.5 * tw if k % 2 else 0.0
            for i in range(n + 1):
                x = -Lo + shift + i * tw
                x0, x1 = max(x - tw / 2, -Lo), min(x + tw / 2, Lo)
                if x1 - x0 < 0.05:
                    continue
                rot = Euler((-side * (ang + 0.07) + random.uniform(-0.02, 0.02), 0,
                             random.uniform(-0.03, 0.03))).to_matrix()
                size = Vector((x1 - x0 - 0.02, 0.3, 0.035))
                c = Vector(((x0 + x1) / 2, y + ny * off, z + nz * off + random.uniform(-0.005, 0.005)))
                base = len(verts)
                for cx, cy, cz in corners:
                    verts.append(c + rot @ Vector((cx * size.x, cy * size.y, cz * size.z)))
                faces += [tuple(base + q for q in quad) for quad in quads]
                mats += [random.choice((0, 0, 1, 2))] * 6
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in (M["slate"], M["slate2"], M["slate3"]):
        me.materials.append(m)
    for f, mi in zip(me.polygons, mats):
        f.material_index = mi
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    bevel(o, 0.008, 2)
    return o


def roof(M, name, L, W_, H, h, ov=0.4):
    """Slate roof with overlapping shingle rows; ridge along local x at height H + h."""
    parts = []
    a = W_ / 2 + ov
    slope = h / (W_ / 2)
    ze = H - ov * slope
    Lo = L / 2 + ov
    top = H + h
    v = [(-Lo, -a, ze), (Lo, -a, ze), (Lo, 0, top), (-Lo, 0, top), (-Lo, a, ze), (Lo, a, ze)]
    parts.append(mesh(name + "Deck", v, [(0, 1, 2, 3), (3, 2, 5, 4)], M["darkwood"], solid=0.08))
    length = math.hypot(a, top - ze)
    ang = math.atan2(top - ze, a)
    parts.append(shingles(M, name + "Tiles", Lo, a, ze, ang, length))
    parts.append(cyl(name + "Ridge", 0.1, 2 * Lo + 0.1, (0, 0, top + 0.1), M["ridge"],
                     rot=(0, math.pi / 2, 0), verts=16))
    # bargeboards along the gable edges
    for sx in (-1, 1):
        for side in (-1, 1):
            parts.append(box(f"{name}Barge{sx}{side}", (0.08, length + 0.1, 0.16),
                             (sx * (Lo + 0.02), side * a / 2, (ze + top) / 2 + 0.05),
                             M["darkwood"], rot=(-side * ang, 0, 0)))
    return parts


def window(M, name, w, h, shutters=True, light=8.0):
    """Lit window built facing local -y with its glass centred on the origin."""
    p = [box(name + "Glass", (w, 0.06, h), (0, 0, 0), M["window"], bev=0),
         box(name + "MullV", (0.04, 0.09, h), (0, -0.01, 0), M["darkwood"], bev=0.005),
         box(name + "MullH", (w, 0.09, 0.04), (0, -0.01, 0), M["darkwood"], bev=0.005),
         box(name + "Sill", (w + 0.2, 0.18, 0.06), (0, -0.07, -h / 2 - 0.04), M["darkwood"]),
         box(name + "Lintel", (w + 0.16, 0.12, 0.09), (0, -0.04, h / 2 + 0.05), M["darkwood"])]
    for sx in (-1, 1):
        p.append(box(f"{name}Side{sx}", (0.07, 0.1, h + 0.05), (sx * (w / 2 + 0.03), -0.03, 0),
                     M["darkwood"]))
        if shutters:
            p.append(box(f"{name}Shutter{sx}", (w / 2, 0.04, h + 0.02),
                         (sx * (w * 0.75 + 0.08), -0.13, 0), M["shadow_trim"],
                         rot=(0, 0, sx * math.radians(-25)), bev=0.008))
    if light:
        p.append(point_light(name + "Light", (0, -0.45, 0), light, (1.0, 0.6, 0.3), radius=0.2))
    return p


def door(M, name, w, h, paint, arch=True):
    """Plank door facing local -y; origin at the bottom centre of the doorway."""
    p = [box(name + "Leaf", (w, 0.08, h), (0, -0.02, h / 2), paint, bev=0.01)]
    for k in range(int(w / 0.18)):
        x = -w / 2 + (k + 0.5) * w / int(w / 0.18)
        p.append(box(f"{name}Seam{k}", (0.012, 0.09, h - 0.05), (x, -0.025, h / 2),
                     M["darkwood"], bev=0))
    for z in (0.3, h - 0.35):
        p.append(box(f"{name}Hinge{z:.1f}", (w * 0.8, 0.1, 0.05), (-w * 0.1, -0.03, z), M["iron"], bev=0.004))
    p.append(torus(name + "Ring", 0.045, 0.01, (w * 0.3, -0.08, h * 0.48), M["iron"],
                   rot=(math.pi / 2, 0, 0), segs=16))
    for sx in (-1, 1):
        p.append(box(f"{name}Jamb{sx}", (0.12, 0.14, h + 0.1), (sx * (w / 2 + 0.06), -0.03, h / 2),
                     M["darkwood"]))
    p.append(box(name + "Head", (w + 0.36, 0.16, 0.14), (0, -0.04, h + 0.07), M["darkwood"]))
    p.append(box(name + "Step", (w + 0.4, 0.4, 0.12), (0, -0.25, 0.06), M["flag"], bev=0.02))
    if arch:
        p.append(cyl(name + "Arch", w / 2, 0.08, (0, -0.02, h), paint, rot=(math.pi / 2, 0, 0), verts=24))
    return p


def lantern(M, name, loc, energy=40, color=(1.0, 0.62, 0.28)):
    x, y, z = loc
    p = [box(name + "Cap", (0.16, 0.16, 0.04), (x, y, z + 0.12), M["iron"], bev=0.005),
         cone(name + "Top", 0.1, 0.0, 0.08, (x, y, z + 0.18), M["iron"], verts=4, smooth=False),
         box(name + "Base", (0.14, 0.14, 0.03), (x, y, z - 0.11), M["iron"], bev=0.004),
         box(name + "Glow", (0.1, 0.1, 0.18), (x, y, z), M["flame"], bev=0.01)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(box(f"{name}Bar{sx}{sy}", (0.015, 0.015, 0.22), (x + sx * 0.065, y + sy * 0.065, z),
                         M["iron"], bev=0))
    p.append(point_light(name + "Light", (x, y, z), energy, color, radius=0.08))
    return p


def timber_face(M, name, width, H, stone_h, panels, braces=(), stones=True, gable=0.0):
    """Timber framing for one wall, built in face-local coords (outside is -y)."""
    p = []
    b = 0.14
    for i in range(panels + 1):
        x = -width / 2 + i * width / panels
        p.append(box(f"{name}Post{i}", (b, 0.12, H - stone_h), (x, -0.03, (H + stone_h) / 2), M["darkwood"]))
    p.append(box(name + "Sill", (width + 0.1, 0.14, b), (0, -0.04, stone_h + 0.05), M["darkwood"]))
    p.append(box(name + "Plate", (width + 0.1, 0.14, b), (0, -0.04, H), M["darkwood"]))
    pw = width / panels
    for i, sgn in braces:
        x0 = -width / 2 + i * pw
        ln = math.hypot(pw, H - stone_h)
        ang = math.atan2(H - stone_h, pw)
        p.append(box(f"{name}Brace{i}", (ln - 0.1, 0.1, b * 0.8), (x0 + pw / 2, -0.02, (H + stone_h) / 2),
                     M["darkwood"], rot=(0, -sgn * ang, 0)))
    if gable:
        p.append(box(name + "King", (b, 0.12, gable), (0, -0.03, H + gable / 2), M["darkwood"]))
        for sx in (-1, 1):
            ln = math.hypot(width / 4, gable / 2)
            p.append(box(f"{name}GBrace{sx}", (ln, 0.1, b * 0.8), (sx * width / 8, -0.02, H + gable / 4),
                         M["darkwood"], rot=(0, sx * math.atan2(gable / 2, width / 4), 0)))
    if stones:
        n = int(width / 0.3)
        for row in range(3):
            z = 0.2 + row * (stone_h - 0.15) / 3
            for k in range(n):
                x = -width / 2 + 0.15 + k * (width - 0.2) / n + (0.13 if row % 2 else 0)
                if x > width / 2 - 0.12:
                    continue
                p.append(box(f"{name}Stone{row}_{k}", (0.27, 0.06, 0.24),
                             (x + random.uniform(-0.02, 0.02), -0.01, z), M["stone"],
                             rot=(0, random.uniform(-0.06, 0.06), 0), bev=0.035))
    return p


def house(M, name, L, W_, H, roof_h, loc, rz, faces, stone_h=0.9):
    """Timber-framed house on a stone base. faces maps 'front'/'right'/'back'/'left' to
    dicts with panels, braces, windows [(x, z, w, h)] and doors [(x, w, h, paint)]."""
    root = group(name, [], loc, rz)
    body = [box(name + "Base", (L, W_, stone_h), (0, 0, stone_h / 2 + 0.08), M["stone"], bev=0.03),
            box(name + "Wall", (L - 0.06, W_ - 0.06, H - stone_h), (0, 0, (H + stone_h) / 2), M["plaster"], bev=0),
            gable_prism(name + "Gable", L - 0.06, W_ - 0.06, roof_h, H, M["plaster"])]
    body += roof(M, name + "Roof", L, W_, H, roof_h)
    for o in body:
        o.parent = root
    frames = {"front": ((0, -W_ / 2), 0, L, False), "right": ((L / 2, 0), math.pi / 2, W_, True),
              "back": ((0, W_ / 2), math.pi, L, False), "left": ((-L / 2, 0), -math.pi / 2, W_, True)}
    for key, cfg in faces.items():
        (fx, fy), frz, width, is_gable = frames[key]
        fname = name + key.capitalize()
        p = timber_face(M, fname, width, H, stone_h, cfg.get("panels", 3), cfg.get("braces", ()),
                        gable=roof_h if is_gable else 0.0)
        face = group(fname, p, (fx, fy, 0), frz, parent=root)
        for i, (x, z, w, h) in enumerate(cfg.get("windows", [])):
            group(f"{fname}Win{i}", window(M, f"{fname}Win{i}", w, h, light=cfg.get("light", 8.0)),
                  (x, -0.04, z), parent=face)
        for i, (x, w, h, paint) in enumerate(cfg.get("doors", [])):
            group(f"{fname}Door{i}", door(M, f"{fname}Door{i}", w, h, paint), (x, -0.06, 0.08), parent=face)
    return root


# ---------------------------------------------------------------- shadow emblem

def emblem(M, name, r):
    """Eclipse sigil in the local xz plane facing -y: black sun, silver corona and rays."""
    rot = (math.pi / 2, 0, 0)
    p = [cyl(name + "Corona", r * 0.62, 0.01, (0, 0, 0), M["silver"], rot=rot, verts=40, smooth=False),
         cyl(name + "Sun", r * 0.55, 0.012, (r * 0.08, -0.004, r * 0.05), M["void"], rot=rot, verts=40,
             smooth=False),
         torus(name + "Ring", r * 0.8, r * 0.035, (0, 0, 0), M["silver"], rot=rot)]
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        ln = r * (0.28 if k % 2 else 0.18)
        rr = r * 0.8 + ln / 2 + r * 0.05
        p.append(box(f"{name}Ray{k}", (r * 0.05, 0.008, ln), (rr * math.cos(a), 0, rr * math.sin(a)),
                     M["silver"], rot=(0, math.pi / 2 - a, 0), bev=0))
    # a dagger driven down through the eclipse
    p.append(box(name + "Blade", (r * 0.1, 0.01, r * 1.4), (0, -0.012, -r * 0.2), M["silver"], bev=0))
    p.append(box(name + "Guard", (r * 0.5, 0.012, r * 0.07), (0, -0.014, r * 0.55), M["silver"], bev=0))
    p.append(box(name + "Grip", (r * 0.07, 0.012, r * 0.3), (0, -0.014, r * 0.75), M["shadow_trim"], bev=0))
    p.append(sphere(name + "Pommel", r * 0.06, (0, -0.014, r * 0.93), M["silver"], segs=8))
    return p


def banner(M, name, w, h, rod=True):
    """Swallowtail banner hanging from its top edge at the origin, facing -y."""
    notch = w * 0.3
    outline = [(-w / 2, 0), (w / 2, 0), (w / 2, -h), (0, -h + notch), (-w / 2, -h)]
    p = [mesh(name + "Trim", [(x * 1.06, 0, z * 1.03 + 0.0) for x, z in outline], [range(5)], M["shadow_trim"]),
         mesh(name + "Cloth", [(x, -0.004, z - 0.01) for x, z in outline], [range(5)], M["shadow"])]
    e = group(name + "Sigil", emblem(M, name + "Sigil", w * 0.32), (0, -0.01, -h * 0.4))
    p.append(e)
    if rod:
        p.append(box(name + "Rod", (w + 0.2, 0.04, 0.04), (0, 0, 0.02), M["iron"], bev=0.005))
        for sx in (-1, 1):
            p.append(sphere(f"{name}Finial{sx}", 0.035, (sx * (w / 2 + 0.11), 0, 0.02), M["brass"], segs=8))
    return p


# ---------------------------------------------------------------- buildings

def build_hall(M):
    L, Wd, H = 6.0, 3.8, 3.4
    pw = L / 5
    front = {"panels": 5, "light": 12,
             "windows": [(-2 * pw, 1.95, 0.6, 1.0), (-pw, 1.95, 0.6, 1.0),
                         (pw, 1.95, 0.6, 1.0), (2 * pw, 1.95, 0.6, 1.0)],
             "doors": [(0, 0.95, 2.0, M["darkwood"])]}
    side = {"panels": 3, "braces": [(0, 1), (2, -1)], "windows": [(0, 1.95, 0.6, 1.0)], "light": 12}
    root = house(M, "Hall", L, Wd, H, 2.4, (*HALL, 0), 0, {"front": front, "right": side, "left": side,
                                                         "back": {"panels": 5}})
    cx, cy = HALL
    fy = cy - Wd / 2
    # porch roof over the door on two posts
    for sx in (-1, 1):
        cyl(f"PorchPost{sx}", 0.07, 2.6, (cx + sx * 0.85, fy - 1.0, 1.38), M["darkwood"], verts=8)
        lantern(M, f"PorchLantern{sx}", (cx + sx * 0.85, fy - 1.12, 2.15), energy=35)
    porch = roof(M, "Porch", 2.0, 1.2, 2.7, 0.5, ov=0.15)
    group("PorchRoof", porch, (cx, fy - 0.55, 0))
    box("PorchBeam", (2.0, 0.12, 0.14), (cx, fy - 1.0, 2.68), M["darkwood"])
    # crest over the porch and banners flanking the door
    group("HallCrest", emblem(M, "HallCrest", 0.42), (cx, fy - 0.08, 3.85))
    for sx in (-1, 1):
        group(f"HallBanner{sx}", banner(M, f"HallBanner{sx}", 0.55, 1.5), (cx + sx * 1.8, fy - 0.12, 3.05))
    # chimney on the right gable
    chx = cx + L / 2 + 0.25
    box("Chimney", (0.6, 0.9, 6.2), (chx, cy + 0.4, 3.1), M["stone"], bev=0.04)
    box("ChimneyCap", (0.75, 1.05, 0.15), (chx, cy + 0.4, 6.25), M["stone"], bev=0.03)
    # firewood stacked against the left gable
    for k in range(18):
        row, col = divmod(k, 6)
        cyl(f"Firewood{k}", 0.09, 0.8, (cx - L / 2 - 0.25 - row * 0.0, cy - 1.2 + col * 0.19 + (0.09 if row % 2 else 0),
                                       0.17 + row * 0.16), M["log"], rot=(0, math.pi / 2, 0), verts=8)
    return root


def build_dorm(M):
    L, Wd, H = 6.5, 2.6, 2.7
    pw = L / 5
    doors, wins = [], []
    for i in range(5):
        x = -L / 2 + (i + 0.5) * pw
        doors.append((x - 0.22, 0.62, 1.8, M["party"][i]))
        wins.append((x + 0.38, 1.6, 0.3, 0.55))
    front = {"panels": 5, "windows": wins, "doors": doors, "light": 5}
    side = {"panels": 2, "braces": [(0, 1), (1, -1)], "windows": [(0, 1.6, 0.4, 0.6)], "light": 5}
    root = house(M, "Dorm", L, Wd, H, 1.6, (*DORM, 0), math.pi / 2,
                 {"front": front, "right": side, "left": side, "back": {"panels": 5}}, stone_h=0.7)
    # per-room touches in dorm-local coords: colour pennant, number plaque, lantern
    for i in range(5):
        x = -L / 2 + (i + 0.5) * pw
        p = [box(f"DormPlaque{i}", (0.22, 0.03, 0.16), (x - 0.22, -Wd / 2 - 0.14, 2.22), M["party"][i], bev=0.01)]
        for k in range(i + 1):
            p.append(sphere(f"DormPip{i}_{k}", 0.014, (x - 0.22 - 0.075 + k * 0.0375 * (1 if i else 0) + (0.075 if i == 0 else 0),
                                                       -Wd / 2 - 0.16, 2.22), M["silver"], segs=6))
        p += lantern(M, f"DormLantern{i}", (x + 0.12, -Wd / 2 - 0.25, 2.05), energy=10)
        p.append(box(f"DormBracket{i}", (0.03, 0.25, 0.03), (x + 0.12, -Wd / 2 - 0.13, 2.3), M["iron"], bev=0))
        p.append(box(f"DormMat{i}", (0.6, 0.4, 0.02), (x - 0.22, -Wd / 2 - 0.55, 0.1), M["party"][i], bev=0.005))
        group(f"DormRoom{i}", p, (*DORM, 0), math.pi / 2)
    # little stovepipes on the roof, one per room
    for i in range(5):
        y = DORM[1] - L / 2 + (i + 0.5) * pw
        cyl(f"Stovepipe{i}", 0.07, 0.7, (DORM[0] - 0.5, y + 0.3, H + 1.3), M["iron"], verts=10)
        cone(f"StovepipeCap{i}", 0.13, 0.0, 0.1, (DORM[0] - 0.5, y + 0.3, H + 1.7), M["iron"], verts=10)
    return root


def fire(M, name, loc, r, outer, core, color, energy):
    x, y, z = loc
    for i in range(8):
        hgt = r * (1.6 + random.uniform(0, 1.6))
        f = sphere(f"{name}Flame{i}", r * 0.5, (x + random.uniform(-r, r) * 0.5, y + random.uniform(-r, r) * 0.5,
                                                z + hgt / 2), outer, scale=(0.8, 0.8, hgt / r), segs=10)
        f.rotation_euler = (random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), 0)
        if i < 3:
            sphere(f"{name}Core{i}", r * 0.3, (f.location.x, f.location.y, z + hgt * 0.4), core,
                   scale=(1, 1, hgt / r * 0.9), segs=8)
    point_light(name + "Light", (x, y, z + r * 3), energy, color, radius=r * 1.5)


# ---------------------------------------------------------------- walls & gate

def build_walls(M):
    # pointed palisade along the back and left edges
    k = 0
    for axis, n, fixed in (("x", 54, D - 0.2), ("y", 46, 0.2)):
        for i in range(n):
            t = 0.25 + i * 0.255
            if axis == "x":
                x, y = t, fixed
            else:
                x, y = fixed, t
            h = 2.2 + random.uniform(-0.15, 0.15)
            cyl(f"Stake{k}", 0.13, h, (x, y, h / 2 + 0.05), M["log"], verts=10)
            cone(f"StakeTip{k}", 0.13, 0.0, 0.3, (x, y, h + 0.2), M["log"], verts=10)
            k += 1
    box("PalisadeRailB", (W - 0.3, 0.1, 0.14), (W / 2, D - 0.36, 1.6), M["darkwood"])
    box("PalisadeRailL", (0.1, D - 0.3, 0.14), (0.36, D / 2, 1.6), M["darkwood"])
    # walkway lanterns on the palisade
    for i, (x, y) in enumerate(((3.5, D - 0.45), (9.5, D - 0.45), (0.45, 9.0))):
        lantern(M, f"WallLantern{i}", (x, y, 1.9), energy=25)

    # low rail fence along the front and right edges, with a gap for the gate
    def fence(name, a, b, fixed, axis):
        n = max(1, int(round((b - a) / 1.1)))
        for i in range(n + 1):
            t = a + i * (b - a) / n
            loc = (t, fixed) if axis == "x" else (fixed, t)
            box(f"{name}Post{i}", (0.12, 0.12, 0.85), (*loc, 0.48), M["log"], bev=0.02)
        for z in (0.45, 0.75):
            mid = (a + b) / 2
            size = (b - a, 0.06, 0.08) if axis == "x" else (0.06, b - a, 0.08)
            loc = (mid, fixed) if axis == "x" else (fixed, mid)
            box(f"{name}Rail{z}", size, (*loc, z), M["wood"], rot=(0, 0, random.uniform(-0.01, 0.01)))
    fence("FenceFL", 0.2, GATE_X - 1.45, 0.2, "x")
    fence("FenceFR", GATE_X + 1.45, W - 0.2, 0.2, "x")
    fence("FenceR", 0.2, D - 0.2, W - 0.2, "y")

    # gate: two heavy posts, a crossbeam and the hanging name board
    gx, gy = GATE_X, 0.2
    for sx in (-1, 1):
        box(f"GatePost{sx}", (0.32, 0.32, 3.4), (gx + sx * 1.3, gy, 1.75), M["log"], bev=0.03)
        cone(f"GatePostCap{sx}", 0.26, 0.0, 0.3, (gx + sx * 1.3, gy, 3.6), M["darkwood"], verts=4,
             rot=(0, 0, math.pi / 4), smooth=False)
        lantern(M, f"GateLantern{sx}", (gx + sx * 1.3, gy - 0.32, 2.4), energy=45)
        box(f"GateBracket{sx}", (0.03, 0.2, 0.03), (gx + sx * 1.3, gy - 0.2, 2.62), M["iron"], bev=0)
        group(f"GateBanner{sx}", banner(M, f"GateBanner{sx}", 0.42, 1.25), (gx + sx * 1.3, gy - 0.2, 3.3))
    box("GateBeam", (3.2, 0.26, 0.26), (gx, gy, 3.2), M["log"], bev=0.03)
    for sx in (-1, 1):
        cyl(f"SignChain{sx}", 0.012, 0.3, (gx + sx * 0.95, gy - 0.05, 2.95), M["iron"], verts=6)
    box("SignBoard", (2.2, 0.08, 0.45), (gx, gy - 0.05, 2.62), M["darkwood"], bev=0.02)
    box("SignBorder", (2.28, 0.06, 0.53), (gx, gy - 0.02, 2.62), M["shadow_trim"], bev=0.02)
    text("SignText", "THE SHADOW", (gx, gy - 0.1, 2.54), 0.28, M["silver"])
    # gate leaves swung open into the compound
    for sx in (-1, 1):
        leaf = [box(f"GateLeaf{sx}", (1.1, 0.08, 1.7), (sx * -0.55, 0, 0.95), M["wood"], bev=0.01)]
        for z in (0.4, 1.5):
            leaf.append(box(f"GateLeafBand{sx}{z}", (1.1, 0.1, 0.07), (sx * -0.55, 0, z), M["iron"], bev=0.005))
        group(f"GateLeafRig{sx}", leaf, (gx + sx * 1.13, gy + 0.05, 0.05), -sx * math.radians(70))


def text(name, body, loc, size, material, rz=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = 0.012
    cu.align_x = "CENTER"
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (math.pi / 2, 0, rz)
    o.data.materials.append(material)
    return o


# ---------------------------------------------------------------- training yard

def dummy(M, name, loc, rz):
    p = [cyl(name + "Post", 0.06, 1.7, (0, 0, 0.85), M["log"], verts=10),
         box(name + "Arms", (0.9, 0.07, 0.07), (0, 0, 1.3), M["log"]),
         sphere(name + "Body", 0.24, (0, 0, 1.1), M["burlap"], scale=(1, 0.75, 1.35), segs=14),
         sphere(name + "Head", 0.14, (0, 0, 1.62), M["burlap"], segs=12),
         cyl(name + "Belt", 0.2, 0.05, (0, 0, 0.95), M["rope"], verts=14),
         box(name + "Foot", (0.6, 0.1, 0.08), (0, 0, 0.12), M["log"]),
         box(name + "Foot2", (0.1, 0.6, 0.08), (0, 0, 0.12), M["log"])]
    for sx in (-1, 1):
        p.append(sphere(f"{name}Straw{sx}", 0.06, (sx * 0.47, 0, 1.3), M["straw"], scale=(1.4, 1, 1), segs=8))
    # target cross painted on the chest
    p.append(box(name + "MarkV", (0.03, 0.02, 0.22), (0, -0.18, 1.12), M["red"], bev=0))
    p.append(box(name + "MarkH", (0.22, 0.02, 0.03), (0, -0.18, 1.12), M["red"], bev=0))
    return group(name, p, loc, rz)


def archery_target(M, name, loc, rz):
    p = []
    for k, (r, key) in enumerate(((0.45, "straw"), (0.38, "white"), (0.27, "red"), (0.17, "white"),
                                  (0.08, "red"))):
        p.append(cyl(f"{name}Ring{k}", r, 0.12 if k == 0 else 0.01, (0, -0.06 - 0.008 * k if k else 0, 1.05),
                     M[key], rot=(math.pi / 2 - 0.15, 0, 0), verts=32))
    for k, (dx, dz) in enumerate(((0.05, 0.08), (-0.15, -0.05), (0.2, 0.2))):
        p.append(cyl(f"{name}Arrow{k}", 0.008, 0.6, (dx, -0.3, 1.05 + dz), M["wood"],
                     rot=(math.pi / 2 - 0.25, 0, 0.1 * k), verts=6))
    for sx in (-1, 1):
        p.append(box(f"{name}Leg{sx}", (0.06, 0.06, 1.5), (sx * 0.3, 0.05, 0.75), M["log"], rot=(-0.15, 0, 0)))
    p.append(box(name + "Prop", (0.06, 0.06, 1.4), (0, 0.4, 0.65), M["log"], rot=(0.4, 0, 0)))
    return group(name, p, loc, rz)


def barrel(M, name, loc, r=0.25, h=0.6):
    x, y, z = loc
    cyl(name, r, h, (x, y, z + h / 2), M["wood"], verts=16)
    for dz in (0.1, h - 0.1):
        cyl(f"{name}Band{dz:.1f}", r + 0.01, 0.04, (x, y, z + dz), M["iron"], verts=16)
    cyl(name + "Lid", r - 0.02, 0.02, (x, y, z + h), M["darkwood"], verts=16)


def crate(M, name, loc, s=0.45, rz=0.0):
    box(name, (s, s, s), (loc[0], loc[1], loc[2] + s / 2), M["wood"], rot=(0, 0, rz), bev=0.02)
    box(name + "Slat", (s + 0.01, s + 0.01, 0.06), (loc[0], loc[1], loc[2] + s / 2), M["darkwood"],
        rot=(0, 0, rz), bev=0.01)


def build_yard(M):
    # sparring ring: posts with rope strung between them
    rx, ry, rr = 10.4, 3.9, 1.4
    n = 8
    for k in range(n):
        a = k * 2 * math.pi / n
        cyl(f"RingPost{k}", 0.06, 0.95, (rx + rr * math.cos(a), ry + rr * math.sin(a), 0.55), M["log"], verts=8)
    for z in (0.55, 0.9):
        torus(f"RingRope{z}", rr, 0.015, (rx, ry, z), M["rope"], segs=8)
    # crossed practice swords dropped in the ring
    for k, ang in enumerate((0.5, -0.4)):
        g = [box(f"PracticeBlade{k}", (0.8, 0.06, 0.02), (0.2, 0, 0), M["wood"], bev=0.005),
             box(f"PracticeGuard{k}", (0.04, 0.2, 0.03), (-0.2, 0, 0), M["darkwood"], bev=0.005),
             cyl(f"PracticeGrip{k}", 0.018, 0.18, (-0.31, 0, 0), M["rope"], rot=(0, math.pi / 2, 0), verts=8)]
        group(f"PracticeSword{k}", g, (rx + 0.2, ry - 0.2 + 0.15 * k, 0.12), ang)
    # dummies along the right fence, facing the ring
    for i, y in enumerate((2.0, 3.4, 4.8)):
        dummy(M, f"Dummy{i}", (12.75, y, 0.1), math.radians(-90 + random.uniform(-15, 15)))
    # archery lane at the back of the yard
    for i, x in enumerate((9.3, 11.5)):
        archery_target(M, f"Target{i}", (x, 6.3, 0.1), random.uniform(-0.15, 0.15))
    # weapon rack by the front fence
    wx, wy = 9.5, 1.15
    box("YardRackBase", (1.6, 0.35, 0.1), (wx, wy, 0.15), M["darkwood"])
    box("YardRackTop", (1.6, 0.12, 0.1), (wx, wy + 0.08, 1.25), M["darkwood"])
    for sx in (-1, 1):
        box(f"YardRackPost{sx}", (0.1, 0.1, 1.2), (wx + sx * 0.8, wy + 0.08, 0.7), M["darkwood"])
    for k in range(5):
        x = wx - 0.6 + k * 0.3
        if k % 2:
            cyl(f"Spear{k}", 0.02, 2.0, (x, wy + 0.02, 1.1), M["wood"], rot=(-0.06, 0, 0), verts=8)
            cone(f"SpearHead{k}", 0.04, 0.0, 0.2, (x, wy - 0.04, 2.2), M["steel"], verts=4, smooth=False)
        else:
            box(f"RackBlade{k}", (0.06, 0.015, 0.85), (x, wy + 0.0, 0.62), M["steel"], bev=0.003)
            box(f"RackGuard{k}", (0.2, 0.04, 0.04), (x, wy, 1.08), M["brass"], bev=0.004)
            cyl(f"RackGrip{k}", 0.016, 0.16, (x, wy, 1.18), M["darkwood"], verts=8)
    # round shield leaning on the rack
    cyl("YardShield", 0.32, 0.05, (wx + 1.05, wy - 0.05, 0.42), M["shadow_trim"], rot=(1.3, 0, 0.2), verts=32)
    cyl("YardShieldBoss", 0.08, 0.08, (wx + 1.05, wy - 0.08, 0.43), M["iron"], rot=(1.3, 0, 0.2), verts=16)
    # benches, barrels, hay
    box("YardBench", (0.35, 1.6, 0.08), (8.55, 3.9, 0.5), M["wood"])
    for sy in (-1, 1):
        box(f"YardBenchLeg{sy}", (0.3, 0.08, 0.42), (8.55, 3.9 + sy * 0.65, 0.29), M["darkwood"])
    barrel(M, "YardBarrel0", (8.5, 1.35, 0.1))
    barrel(M, "YardBarrel1", (8.65, 1.9, 0.1), r=0.22, h=0.55)
    cyl("WaterTrough", 0.3, 1.2, (12.9, 6.3, 0.35), M["wood"], rot=(math.pi / 2, 0, math.pi / 2), verts=12)
    for k in range(3):
        box(f"Hay{k}", (0.7, 0.45, 0.4), (13.0 - 0.1 * k, 1.0 + 0.0 * k, 0.3 + 0.4 * (k == 2)), M["straw"],
            rot=(0, 0, 0.1 * k), bev=0.05) if k < 2 else None
    box("Hay2", (0.7, 0.45, 0.4), (12.95, 1.0, 0.7), M["straw"], rot=(0, 0, 0.3), bev=0.05)
    # torch posts at the yard corners
    for i, (x, y) in enumerate(((8.4, 6.6), (13.2, 6.7), (13.2, 1.0))):
        cyl(f"Torch{i}", 0.05, 1.8, (x, y, 1.0), M["log"], verts=8)
        cone(f"TorchCup{i}", 0.09, 0.05, 0.14, (x, y, 1.95), M["iron"], rot=(math.pi, 0, 0), verts=10)
        fire(M, f"Torch{i}Fire", (x, y, 2.0), 0.06, M["fire"], M["firecore"], (1.0, 0.5, 0.18), 60)


# ---------------------------------------------------------------- props

def pine(M, name, loc, h):
    x, y, _ = loc
    cyl(name + "Trunk", 0.12, h * 0.3, (x, y, h * 0.15), M["log"], verts=8)
    for k in range(3):
        r = h * (0.28 - 0.07 * k)
        cone(f"{name}Tier{k}", r, 0.0, h * 0.42, (x, y, h * (0.32 + 0.2 * k) + h * 0.18), M["pine"],
             rot=(0, 0, random.uniform(0, 1)), verts=8, smooth=False)


def blob(name, r, loc, material, squash=1.0, strength=0.3):
    """Lumpy foliage: an icosphere pushed around by a cloud texture."""
    tex = bpy.data.textures.get("LeafNoise") or bpy.data.textures.new("LeafNoise", "CLOUDS")
    tex.noise_scale = 0.3
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale.z = squash
    d = o.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = strength
    d.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth()
    return assign(o, material)


def leafy(M, name, loc, h, r=1.0, leaf=None):
    x, y, _ = loc
    cone(name + "Trunk", 0.16, 0.07, h * 0.65, (x, y, h * 0.32), M["log"], verts=10)
    for k in range(4):
        off = (0, 0, 0) if k == 0 else (random.uniform(-0.45, 0.45) * r, random.uniform(-0.45, 0.45) * r,
                                        random.uniform(-0.25, 0.35) * r)
        blob(f"{name}Crown{k}", r * random.uniform(0.6, 0.85),
             (x + off[0], y + off[1], h * 0.75 + off[2]), leaf or M["leaf"], strength=0.35 * r)


def bush(M, name, loc, r=0.35, leaf=None, bloom=None):
    x, y, _ = loc
    blob(name, r, (x, y, 0.08 + r * 0.55), leaf or M["hedge"], squash=0.75, strength=0.12)
    if bloom:
        for k in range(6):
            a = random.uniform(0, 2 * math.pi)
            sphere(f"{name}Bloom{k}", 0.04, (x + r * 0.8 * math.cos(a), y + r * 0.8 * math.sin(a),
                                              0.08 + r * random.uniform(0.6, 1.0)), bloom, segs=6)


def flowers(M, name, cx, cy, rx, ry, n, cols, z=0.08):
    """Scatter n little flowers (leaf tuft + bloom) inside an ellipse."""
    for k in range(n):
        a, d = random.uniform(0, 2 * math.pi), math.sqrt(random.random())
        x, y = cx + rx * d * math.cos(a), cy + ry * d * math.sin(a)
        hgt = random.uniform(0.12, 0.26)
        cone(f"{name}Stem{k}", 0.04, 0.0, hgt, (x, y, z + hgt / 2), M["tuft"], verts=5, smooth=False)
        sphere(f"{name}Bloom{k}", random.uniform(0.03, 0.045), (x, y, z + hgt), random.choice(cols), segs=6)


def flower_bed(M, name, cx, cy, sx, sy, cols, n=None):
    """Raised bed with a stone kerb, dark soil and flowers."""
    box(name + "Kerb", (sx, sy, 0.22), (cx, cy, 0.15), M["flag"], bev=0.03)
    box(name + "Soil", (sx - 0.1, sy - 0.1, 0.04), (cx, cy, 0.25), M["soil"], bev=0)
    flowers(M, name, cx, cy, sx / 2 - 0.08, sy / 2 - 0.08, n or int(sx * sy * 22), cols, z=0.26)


def driftglobe(M, name, loc, h=2.3, post=True, color=(1.0, 0.82, 0.6), energy=55):
    """Waterdeep street light: a glowing globe hovering over an iron cradle."""
    x, y, z = loc
    if post:
        cyl(name + "Post", 0.05, h, (x, y, z + h / 2), M["iron"], verts=10)
        cyl(name + "Foot", 0.13, 0.14, (x, y, z + 0.07), M["iron"], verts=10)
        torus(name + "Cradle", 0.14, 0.014, (x, y, z + h + 0.02), M["iron"], segs=24)
        z = z + h + 0.22
    sphere(name + "Globe", 0.1, (x, y, z), M["globe"], segs=16)
    point_light(name + "Light", (x, y, z), energy, color, radius=0.1)


def build_courtyard(M):
    """Back-right corner: patio under a wisteria pergola with a long feasting table."""
    px, py = 12.15, 9.75
    box("Patio", (3.0, 3.6, 0.04), (px, py, 0.09), M["flag"], bev=0.02)
    for i in range(6):
        for j in range(7):
            box(f"PatioTile{i}_{j}", (0.46, 0.48, 0.02), (px - 1.25 + i * 0.5, py - 1.5 + j * 0.5, 0.115),
                M["flag"] if (i + j) % 3 else M["stone"], rot=(0, 0, random.uniform(-0.03, 0.03)), bev=0.015)
    # pergola: six posts, two long beams, cross slats
    for sx in (-1, 1):
        for k in range(3):
            box(f"PergolaPost{sx}{k}", (0.14, 0.14, 2.5), (px + sx * 1.25, py - 1.5 + k * 1.5, 1.35), M["wood"])
        box(f"PergolaBeam{sx}", (0.12, 3.8, 0.2), (px + sx * 1.25, py, 2.65), M["wood"])
    for k in range(9):
        box(f"PergolaSlat{k}", (3.0, 0.07, 0.12), (px, py - 1.8 + k * 0.45, 2.81), M["wood"])
    # wisteria and vines along the top, with violet blossoms hanging down
    for k in range(10):
        blob(f"Vine{k}", random.uniform(0.35, 0.5),
             (px + random.uniform(-1.3, 1.3), py + random.uniform(-1.7, 1.7), 2.95), M["leaf"],
             squash=0.45, strength=0.18)
    for k in range(34):
        x, y = px + random.uniform(-1.4, 1.4), py + random.uniform(-1.8, 1.8)
        ln = random.uniform(0.25, 0.5)
        cone(f"Wisteria{k}", 0.07, 0.01, ln, (x, y, 2.75 - ln / 2), random.choice((M["wisteria"], M["wisteria2"])),
             rot=(math.pi, 0, 0), verts=7)
    for sx in (-1, 1):
        for k in (0, 2):
            for j in range(3):
                blob(f"PostVine{sx}{k}{j}", 0.13, (px + sx * 1.25, py - 1.5 + k * 1.5, 0.6 + j * 0.7),
                     M["leaf"], strength=0.06)
    # feasting table with benches, food and drink
    box("FeastTop", (1.0, 2.8, 0.08), (px, py, 0.86), M["wood"], bev=0.02)
    for sy in (-1, 1):
        box(f"FeastTrestle{sy}", (0.8, 0.1, 0.74), (px, py + sy * 1.1, 0.48), M["darkwood"])
    box("FeastRunner", (0.35, 2.6, 0.01), (px, py, 0.905), M["shadow_trim"], bev=0)
    for sx in (-1, 1):
        box(f"FeastBench{sx}", (0.32, 2.5, 0.07), (px + sx * 0.8, py, 0.5), M["wood"], bev=0.015)
        for sy in (-1, 1):
            box(f"FeastBenchLeg{sx}{sy}", (0.28, 0.07, 0.38), (px + sx * 0.8, py + sy * 1.0, 0.3), M["darkwood"])
    for k in range(6):
        sx, y = (-1, 1)[k % 2], py - 1.0 + (k // 2) * 1.0
        cyl(f"Plate{k}", 0.12, 0.02, (px + sx * 0.3, y, 0.91), M["white"], verts=20)
        tank = (px + sx * 0.3 + 0.1, y + 0.2, 0.9)
        cyl(f"Tankard{k}", 0.045, 0.12, (tank[0], tank[1], tank[2] + 0.06), M["wood"], verts=12)
        cyl(f"TankardFoam{k}", 0.042, 0.01, (tank[0], tank[1], tank[2] + 0.125), M["foam"], verts=12)
    sphere("Bread", 0.13, (px, py - 0.3, 0.97), M["straw"], scale=(1.4, 1, 0.7), segs=12)
    sphere("Roast", 0.14, (px, py + 0.4, 0.98), M["leather"], scale=(1.5, 1, 0.8), segs=12)
    for k, c in enumerate((M["red"], M["party"][2], M["tuft"])):
        sphere(f"Fruit{k}", 0.045, (px + 0.08 * (k - 1), py + 0.05, 0.95), c, segs=8)
    for k, y in enumerate((py - 0.9, py + 1.0)):
        cyl(f"FeastCandle{k}", 0.025, 0.16, (px, y, 0.99), M["wax"], verts=10)
        sphere(f"FeastCandleFlame{k}", 0.02, (px, y, 1.1), M["flame"], scale=(1, 1, 1.8), segs=8)
        point_light(f"FeastCandleLight{k}", (px, y, 1.2), 10, (1.0, 0.6, 0.25), radius=0.03)
    # festoon of tiny glowing bulbs sagging between the pergola posts
    for sx in (-1, 1):
        for k in range(16):
            t = k / 15
            y = py - 1.8 + t * 3.6
            z = 2.5 - 0.25 * math.sin(math.pi * ((t * 2) % 1.0))
            sphere(f"Bulb{sx}{k}", 0.03, (px + sx * 1.25, y, z), M["bulb"], segs=6)
        point_light(f"FestoonLight{sx}", (px + sx * 1.1, py, 2.3), 45, (1.0, 0.75, 0.45), radius=0.8)
    # dice game on an upturned barrel beside the patio
    bx, by = 10.75, 8.3
    barrel(M, "DiceBarrel", (bx, by, 0.08), r=0.28, h=0.75)
    for k in range(3):
        box(f"Die{k}", (0.05, 0.05, 0.05), (bx - 0.08 + 0.07 * k, by + 0.03 * k, 0.86), M["white"],
            rot=(0, 0, random.uniform(0, 1)), bev=0.008)
    for k in range(4):
        box(f"Card{k}", (0.07, 0.1, 0.004), (bx + 0.1 - 0.03 * k, by - 0.1, 0.84), M["white"],
            rot=(0, 0, 0.3 * k), bev=0)
    for k in range(5):
        cyl(f"BetCoin{k}", 0.025, 0.008, (bx - 0.12, by - 0.1, 0.835 + 0.008 * k), M["brass"], verts=10)
    for k, a in enumerate((0.4, 2.6)):
        cyl(f"Stool{k}", 0.17, 0.45, (bx + 0.6 * math.cos(a), by + 0.6 * math.sin(a), 0.31), M["wood"], verts=12)
    # violet-leaved ornamental maple: a quiet nod to the party colours
    leafy(M, "ShadowMaple", (13.15, 7.6, 0), 3.4, r=0.95, leaf=M["leaf_violet"])
    flowers(M, "MapleBed", 13.15, 7.6, 0.55, 0.55, 18, [M["bloom_white"], M["wisteria"]])
    for i, (x, y) in enumerate(((10.75, 11.3), (13.5, 11.3))):
        driftglobe(M, f"PatioGlobe{i}", (x, y, 0.08))


def build_garden(M):
    warm = [M["bloom_red"], M["bloom_yellow"], M["bloom_white"]]
    cool = [M["wisteria"], M["bloom_white"], M["bloom_blue"]]
    # beds along the hall front, either side of the porch
    hx, hy = HALL
    flower_bed(M, "BedHallL", hx - 2.0, hy - 2.3, 1.6, 0.45, warm)
    flower_bed(M, "BedHallR", hx + 2.0, hy - 2.3, 1.6, 0.45, cool)
    # beds and tufts along the main path
    for i, y in enumerate((1.6, 4.0)):
        flowers(M, f"PathL{i}", GATE_X - 1.2, y, 0.25, 0.7, 14, warm)
        flowers(M, f"PathR{i}", GATE_X + 1.2, y, 0.25, 0.7, 14, cool)
    # shrubs along the palisade and fences
    for i, x in enumerate((4.3, 5.4, 9.5, 10.4)):
        bush(M, f"BackBush{i}", (x, D - 0.7, 0), r=random.uniform(0.35, 0.5),
             bloom=random.choice((None, M["bloom_red"], M["wisteria"])))
    for i, y in enumerate((0.9, 8.4, 9.6, 10.8)):
        bush(M, f"LeftBush{i}", (0.8, y, 0), r=random.uniform(0.3, 0.45),
             bloom=None if i % 2 else M["bloom_yellow"])
    for i, x in enumerate((1.0, 2.0, 3.0, 4.0, 5.2)):
        bush(M, f"FrontBush{i}", (x, 0.6, 0), r=random.uniform(0.25, 0.35),
             bloom=random.choice((M["bloom_red"], M["bloom_white"], M["wisteria"])))
    for i, y in enumerate((7.4, 8.2)):
        bush(M, f"RightBush{i}", (13.5, y + 1.2 * (i == 1), 0), r=0.32)
    # trees, mostly in the back-left corner behind the dorm
    leafy(M, "OakA", (1.5, 9.0, 0), 3.6, r=1.1)
    leafy(M, "OakB", (2.9, 10.7, 0), 3.2, r=0.95)
    pine(M, "PineA", (1.2, 10.9, 0), 4.4)
    leafy(M, "Birch", (10.4, 11.1, 0), 3.0, r=0.8)
    flowers(M, "OakMeadow", 2.4, 9.8, 1.0, 1.4, 40, warm + cool)
    # herb bed for the party cook
    flower_bed(M, "Herbs", 3.0, 8.35, 1.0, 0.5, [M["tuft"], M["bloom_white"]], n=14)
    # window boxes under the hall's front windows
    pw = 6.0 / 5
    for i, dx in enumerate((-2 * pw, -pw, pw, 2 * pw)):
        x = hx + dx
        box(f"WinBox{i}", (0.7, 0.2, 0.16), (x, hy - 1.9 - 0.2, 1.33), M["darkwood"], bev=0.01)
        flowers(M, f"WinBox{i}", x, hy - 2.1, 0.3, 0.06, 7, warm if i < 2 else cool, z=1.38)
    # floating driftglobes over the yard and lamp posts along the path
    for i, (x, y, z) in enumerate(((9.6, 3.0, 3.0), (11.6, 5.0, 3.2))):
        driftglobe(M, f"YardGlobe{i}", (x, y, z), post=False, energy=90)
    for i, (x, y) in enumerate(((GATE_X - 0.85, 2.6), (GATE_X + 0.85, 2.6), (GATE_X - 0.85, 5.3),
                                (GATE_X + 0.85, 5.3), (3.9, 5.3))):
        driftglobe(M, f"PathGlobe{i}", (x, y, 0.08))


def build_props(M):
    # campfire with log benches between the dorm and the path
    cx, cy = 5.0, 3.6
    for k in range(9):
        a = k * 2 * math.pi / 9
        sphere(f"FireStone{k}", 0.11, (cx + 0.38 * math.cos(a), cy + 0.38 * math.sin(a), 0.12), M["stone"],
               scale=(1, 1, 0.7), segs=8)
    for k in range(3):
        cyl(f"FireLog{k}", 0.06, 0.55, (cx, cy, 0.17), M["log"], rot=(math.pi / 2, 0, k * math.pi / 3), verts=8)
    for k in range(8):
        sphere(f"FireEmber{k}", 0.03, (cx + random.uniform(-0.2, 0.2), cy + random.uniform(-0.2, 0.2), 0.13),
               M["ember"], segs=6)
    fire(M, "Campfire", (cx, cy, 0.18), 0.13, M["fire"], M["firecore"], (1.0, 0.45, 0.15), 260)
    for k, a in enumerate((0.3, 2.4, 4.3)):
        cyl(f"LogBench{k}", 0.17, 1.1, (cx + 1.1 * math.cos(a), cy + 1.1 * math.sin(a), 0.24), M["log"],
            rot=(math.pi / 2, 0, a), verts=12)
    # a pot on a tripod over the fire
    for k in range(3):
        a = k * 2 * math.pi / 3
        cyl(f"Tripod{k}", 0.02, 1.3, (cx + 0.25 * math.cos(a), cy + 0.25 * math.sin(a), 0.65), M["iron"],
            rot=(0.35 * math.sin(a), -0.35 * math.cos(a), 0), verts=6)
    sphere("Pot", 0.15, (cx, cy, 0.78), M["iron"], scale=(1, 1, 0.8), segs=14)

    # well in front of the hall's left wing
    wx, wy = 4.8, 6.2
    cyl("WellRing", 0.55, 0.75, (wx, wy, 0.45), M["stone"], verts=16)
    cyl("WellWater", 0.45, 0.02, (wx, wy, 0.78), M["water"], verts=24)
    cyl("WellLip", 0.58, 0.08, (wx, wy, 0.84), M["flag"], verts=16)
    for sx in (-1, 1):
        box(f"WellPost{sx}", (0.1, 0.1, 1.5), (wx + sx * 0.5, wy, 1.5), M["darkwood"])
    cyl("WellAxle", 0.06, 1.1, (wx, wy, 1.8), M["log"], rot=(0, math.pi / 2, 0), verts=10)
    cyl("WellRope", 0.008, 0.6, (wx, wy, 1.45), M["rope"], verts=6)
    cyl("WellBucket", 0.1, 0.16, (wx, wy, 1.1), M["wood"], verts=12)
    group("WellRoof", roof(M, "WellRoof", 1.0, 1.0, 2.15, 0.45, ov=0.15), (wx, wy, 0))
    for k in range(3):
        barrel(M, f"DormBarrel{k}", (3.7, 1.2 + 0.5 * k, 0.08), r=0.2, h=0.5)


# ---------------------------------------------------------------- scene setup

def set_emission(material, strength, base=None):
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Strength"].default_value = strength
    if base:
        bsdf.inputs["Base Color"].default_value = (*base, 1)


def apply_daylight(M):
    """Daytime: dim every small light and turn lit windows back into glass."""
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.data.type == "POINT":
            o.data.energy *= 0.08
    set_emission(M["window"], 0.2, base=(0.22, 0.30, 0.38))
    set_emission(M["globe"], 2.5)
    set_emission(M["bulb"], 2.0)


def setup_world_and_camera(samples, shot="wide", time="day"):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    # sky gradient: also the backdrop behind the diorama
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    night = time == "night"
    ramp.color_ramp.elements[0].color = (0.018, 0.02, 0.04, 1) if night else (0.62, 0.72, 0.86, 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.004, 0.005, 0.014, 1) if night else (0.30, 0.48, 0.78, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0 if night else 0.8

    def aimed(name, kind, loc, energy, color, size, target=(W / 2, D / 2, 0)):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        if kind == "SUN":
            ld.angle = math.radians(size)
        else:
            ld.size = size
        o = bpy.data.objects.new(name, ld)
        o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(o)
        return o

    if night:
        # moon from the front-left so the hall facade catches it; violet rim from behind
        # so roofs and trees separate from the sky; soft fill from the camera side
        aimed("Moon", "SUN", (-8, -14, 18), 1.2, (0.6, 0.7, 1.0), 2)
        aimed("Rim", "AREA", (8, 32, 14), 4000, (0.55, 0.45, 1.0), 14)
        aimed("Fill", "AREA", (26, -16, 20), 2200, (0.65, 0.7, 1.0), 15)
    else:
        # late-morning sun from the front-left, cool bounce from the camera side
        aimed("Sun", "SUN", (-9, -13, 20), 4.0, (1.0, 0.95, 0.87), 2)
        aimed("Fill", "AREA", (26, -16, 20), 1200, (0.75, 0.85, 1.0), 15)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 35
    cam_data.clip_end = 200
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    if shot == "pergola":
        # low view in under the wisteria from beyond the right fence, showing posts,
        # beams, slats and the feasting table
        cam_data.lens = 22
        cam.location = (16.2, 8.4, 2.0)
        target = Vector((12.0, 10.0, 1.35))
    elif shot == "close":
        # eye-level from the yard toward the hall door
        cam_data.lens = 28
        cam.location = (11.8, 1.6, 2.0)
        target = Vector((6.4, 7.6, 1.9))
    else:
        cam.location = (21.5, -9.5, 13.5)
        target = Vector((6.8, 5.4, 1.2))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    if shot == "top":
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = W + 1.2
        cam.location = (W / 2, D / 2, 30)
        cam.rotation_euler = (0, 0, 0)
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    if shot == "top":
        scene.render.resolution_x, scene.render.resolution_y = 1400, 1200
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = None
    samples = 64
    blend_out = None
    shot = "wide"
    time = "day"
    res = 100
    for i, a in enumerate(argv):
        if a == "--render":
            out = argv[i + 1]
        elif a == "--samples":
            samples = int(argv[i + 1])
        elif a == "--shot":
            shot = argv[i + 1]
        elif a == "--time":
            time = argv[i + 1]
        elif a == "--save":
            blend_out = argv[i + 1]
        elif a == "--res":
            res = int(argv[i + 1])

    reset()
    M = build_materials()
    build_ground(M)
    build_grass(M)
    build_hall(M)
    build_dorm(M)
    build_walls(M)
    build_yard(M)
    build_props(M)
    build_courtyard(M)
    build_garden(M)
    if time == "day":
        apply_daylight(M)
    setup_world_and_camera(samples, shot, time)
    bpy.context.scene.render.resolution_percentage = res

    if blend_out:
        bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    if out:
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)


main()
