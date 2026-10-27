"""Build an exterior diorama of the Shadow party's compound in Blender.

Main hall, training yard, a five-room dormitory, grapevine patio, gate and props,
in the same stylised diorama look as scenes/homebase.

Run with:  python3 scenes/shadow-base/build_scene.py [--render out.png] [--samples N]
           [--shot wide|close|top|pergola] [--time day|night] [--backdrop sky|paper]
           [--anim frames_dir [--step N]] [--res percent] [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    scenes/blender.sh scenes/shadow-base/build_scene.py --render out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scenes/

import bpy  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

from assets import (barrel, bush, candle, cauldron, crate, crystal_ball, crystal_cluster, driftglobe,  # noqa: E402
                    flower_bed, flower_patch, fountain, lamp_post, lantern, open_book, pergola,
                    shadow_emblem, staff, tree, weapon_rack)
from assets.lib import (Batch, assign, bevel, box, cone, cyl, keyframe, mat, noisy_mat,  # noqa: E402
                        palette, point_light, reset, sphere, wave)
from assets.lib import shell as lib_shell  # noqa: E402

random.seed(11)

# ---------------------------------------------------------------- helpers

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


def plank_mat(name, c1, c2, board=0.16):
    """Horizontal weatherboards: dark seams every `board` metres along z, noisy grain between."""
    m = noisy_mat(name, c1, c2, 5, 0.7, stretch=(1, 1, 12))
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "PINGPONG"
    fr.inputs[1].default_value = board / 2
    seam = nt.nodes.new("ShaderNodeMapRange")
    seam.inputs["From Min"].default_value = 0.0
    seam.inputs["From Max"].default_value = 0.012
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    a_col, b_col = mix.inputs[6], mix.inputs[7]      # the colour A / B sockets
    ramp_out = bsdf.inputs["Base Color"].links[0].from_socket
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], fr.inputs[0])
    nt.links.new(fr.outputs[0], seam.inputs["Value"])
    nt.links.new(seam.outputs["Result"], mix.inputs[0])
    a_col.default_value = (0.08, 0.05, 0.03, 1)
    nt.links.new(ramp_out, b_col)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return m


def build_materials():
    # scene-tuned (brighter, daylight) versions of palette materials; made before
    # palette() so that assets looking them up by name get these as well
    M = {
        "stone": noisy_mat("Stone", (0.30, 0.29, 0.28), (0.44, 0.43, 0.41), 6, 0.9),
        "wood": noisy_mat("Wood", (0.36, 0.21, 0.10), (0.46, 0.29, 0.15), 5, 0.6, stretch=(1, 1, 10)),
        "darkwood": noisy_mat("DarkWood", (0.07, 0.04, 0.02), (0.11, 0.065, 0.035), 5, 0.55, stretch=(1, 1, 10)),
        "plaster": noisy_mat("Plaster", (0.78, 0.72, 0.60), (0.85, 0.80, 0.69), 3, 0.95),
        "leather": mat("Leather", (0.35, 0.16, 0.06), 0.6),
        # warmer, slightly yellow greens for a sunny summer day
        "leaf": noisy_mat("Leaf", (0.20, 0.34, 0.07), (0.28, 0.43, 0.10), 4, 0.9),
        "leaf_light": noisy_mat("LeafLight", (0.30, 0.46, 0.10), (0.40, 0.55, 0.14), 4, 0.85),
        "hedge": noisy_mat("Hedge", (0.15, 0.28, 0.06), (0.21, 0.36, 0.08), 5, 0.9),
        "pine": noisy_mat("Pine", (0.09, 0.22, 0.09), (0.13, 0.28, 0.11), 4, 0.9),
        "tuft": mat("GrassTuft", (0.30, 0.46, 0.09), 0.9),
    }
    M = {**palette(), **M}
    M["red"], M["white"] = M["red_paint"], M["white_paint"]
    # weathered cedar shakes for the roofs, a few patches of moss
    # roofs and framing are kept dark so the lighter wall boards read against them
    M["shake"] = noisy_mat("Shake", (0.13, 0.075, 0.04), (0.19, 0.11, 0.06), 6, 0.8, stretch=(1, 6, 1))
    M["shake2"] = noisy_mat("Shake2", (0.08, 0.05, 0.03), (0.12, 0.07, 0.04), 6, 0.8, stretch=(1, 6, 1))
    M["shake3"] = noisy_mat("Shake3", (0.20, 0.13, 0.08), (0.26, 0.17, 0.10), 6, 0.85, stretch=(1, 6, 1))
    M["moss"] = noisy_mat("Moss", (0.035, 0.06, 0.02), (0.06, 0.09, 0.03), 10, 0.95)
    M["planks"] = plank_mat("WallPlanks", (0.56, 0.40, 0.23), (0.68, 0.51, 0.31))
    M["grass"] = noisy_mat("Grass", (0.24, 0.38, 0.07), (0.31, 0.45, 0.10), 3, 0.95)
    M["dirt"] = noisy_mat("Dirt", (0.50, 0.38, 0.24), (0.58, 0.45, 0.30), 6, 1.0)
    M["shadow"] = mat("ShadowCloth", (0.03, 0.03, 0.04), 0.9)        # party colour
    M["window"] = mat("WindowWarm", (1.0, 0.6, 0.25), 0.5, emit=(1.0, 0.55, 0.2), emit_strength=1.2)
    M["firecore"] = mat("FireCore", (0, 0, 0), 1, emit=(1.0, 0.42, 0.03), emit_strength=4)
    M["water"] = mat("Water", (0.08, 0.20, 0.30), 0.05)
    M["bulb"] = mat("Bulb", (1.0, 0.8, 0.5), 0.3, emit=(1.0, 0.75, 0.4), emit_strength=10)
    M["foam"] = mat("Foam", (0.95, 0.9, 0.75), 0.9)
    M["party"] = [mat(f"Party{i}", c, 0.6) for i, c in enumerate(PARTY)]
    return M


# ---------------------------------------------------------------- layout
#
# Plinth spans x 0..W, y 0..D. Camera looks from +x/-y, so tall things sit at the
# back (+y) and left (-x); the front and right edges only get a low fence.

W, D = 14.0, 12.0
HALL = (6.9, 9.3)          # hall centre; front wall faces -y
DORM = (2.1, 4.6)          # dormitory centre; front wall faces +x
FIRE = (10.5, 3.9)         # bonfire in the right-front quarter; FIRE_DIRT is the trodden earth round it
FIRE_DIRT = [(10.5, 3.9, 2.0), (9.4, 3.1, 1.1), (11.5, 5.0, 1.0), (11.6, 2.7, 0.9)]
GATE_X = 6.9
PLAZA, PLAZA_R = (5.2, 3.0), 1.05   # fountain plaza beside the gate path, facing the dorm


def build_ground(M):
    box("Plinth", (W + 0.4, D + 0.4, 0.5), (W / 2, D / 2, -0.25), M["stone"], bev=0.05)
    box("PlinthLip", (W + 0.5, D + 0.5, 0.08), (W / 2, D / 2, -0.46), M["darkwood"], bev=0.02)
    box("Grass", (W, D, 0.08), (W / 2, D / 2, 0.04), M["grass"], bev=0.02)
    # trodden earth around the bonfire, ragged at the edges where the grass creeps in
    for i, (x, y, r) in enumerate(FIRE_DIRT):
        cyl(f"FireDirt{i}", r, 0.03, (x, y, 0.08 + 0.002 * i), M["dirt"], verts=40)
    # round paved plaza for the fountain: kerb ring and concentric courses of setts
    px, py = PLAZA
    cyl("Plaza", PLAZA_R, 0.04, (px, py, 0.09), M["flag"], verts=64)
    box_ring = Batch()
    for ring, (r, n) in enumerate(((PLAZA_R - 0.17, 26), (PLAZA_R - 0.38, 20))):
        for k in range(n):
            a = (k + 0.5 * ring) * 2 * math.pi / n
            box_ring.box(M["stone"] if (k + ring) % 4 == 0 else M["flag"], (0.18, 2 * math.pi * r / n - 0.03, 0.02),
                         (px + r * math.cos(a), py + r * math.sin(a), 0.115), rz=a)
    for o in box_ring.build("PlazaSetts"):
        bevel(o, 0.01, 2)
    lib_shell("PlazaKerb", PLAZA_R + 0.06, PLAZA_R - 0.06, 0.08, 0.15, M["stone"], segs=64, loc=(px, py, 0))
    # flagstone path from the gate to the hall door, plus a branch to the dorm
    pts = [(GATE_X + random.uniform(-0.35, 0.35), y) for y in [0.3 + 0.42 * k for k in range(17)]]
    pts += [(3.7 + 0.42 * k, 4.6 + random.uniform(-0.2, 0.2)) for k in range(7)]
    for i, (x, y) in enumerate(pts):
        if math.hypot(x - px, y - py) < PLAZA_R + 0.15:
            continue
        for j in range(2 if y < 7 and x > 6 else 1):
            dx = (j - 0.5) * 0.5 if x > 6 else 0
            cyl(f"Flag{i}_{j}", random.uniform(0.17, 0.24), 0.04,
                (x + dx, y + random.uniform(-0.05, 0.05), 0.09), M["flag"],
                rot=(0, 0, random.uniform(0, 1)), verts=6, smooth=False)


def free_spot(x, y):
    """True where grass tufts may grow (not on paths, yard or buildings)."""
    if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in FIRE_DIRT):
        return False
    blocked = [(0.6, 3.8, 1.2, 8.0), (3.4, 10.4, 7.0, 11.5), (6.2, 7.6, 0, 7.4),
               (4.0, 6.4, 1.8, 4.2), (10.4, 13.7, 7.9, 11.7), (4.3, 5.8, 4.9, 6.4)]
    return not any(a <= x <= b and c <= y <= d for a, b, c, d in blocked)


def build_grass(M):
    tuft = M["tuft"]
    n = 0
    while n < 200:
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


def shingles(M, name, Lo, a, ze, ang, length, step=0.15):
    """All roof shakes of both slopes as one mesh: rows of split-wood shakes of uneven
    width and length, a little tilted and jittered, in three weathered tones plus moss."""
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
            x = -Lo + random.uniform(0, 0.12)
            while x < Lo - 0.04:
                tw = random.uniform(0.12, 0.26)
                x0, x1 = x, min(x + tw, Lo)
                x = x1 + 0.012
                rot = Euler((-side * (ang + 0.09) + random.uniform(-0.04, 0.04), random.uniform(-0.03, 0.03),
                             random.uniform(-0.05, 0.05))).to_matrix()
                ln = random.uniform(0.24, 0.32)
                size = Vector((x1 - x0, ln, random.uniform(0.025, 0.04)))
                c = Vector(((x0 + x1) / 2, y + ny * 0.1 - side * random.uniform(-0.02, 0.02) * math.cos(ang),
                            z + nz * 0.1 + random.uniform(-0.008, 0.008)))
                base = len(verts)
                for cx, cy, cz in corners:
                    verts.append(c + rot @ Vector((cx * size.x, cy * size.y, cz * size.z)))
                faces += [tuple(base + q for q in quad) for quad in quads]
                mats += [random.choices((0, 1, 2, 3), (6, 3, 1.2, 0.25))[0]] * 6
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in (M["shake"], M["shake2"], M["shake3"], M["moss"]):
        me.materials.append(m)
    for f, mi in zip(me.polygons, mats):
        f.material_index = mi
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    bevel(o, 0.006, 1)
    return o


def roof(M, name, L, W_, H, h, ov=0.4):
    """Wooden shake roof; ridge along local x at height H + h, capped by two ridge boards."""
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
    # ridge cap: two boards meeting at the apex
    for side in (-1, 1):
        parts.append(box(f"{name}Ridge{side}", (2 * Lo + 0.12, 0.24, 0.05),
                         (0, side * 0.09 * math.cos(ang), top + 0.14 - 0.09 * math.sin(ang)),
                         M["darkwood"], rot=(-side * ang, 0, 0), bev=0.01))
    # bargeboards along the gable edges
    for sx in (-1, 1):
        for side in (-1, 1):
            parts.append(box(f"{name}Barge{sx}{side}", (0.08, length + 0.1, 0.16),
                             (sx * (Lo + 0.02), side * a / 2, (ze + top) / 2 + 0.05),
                             M["darkwood"], rot=(-side * ang, 0, 0)))
    return parts


def window(M, name, w, h, shutters=False, light=8.0):
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


def door(M, name, w, h, paint, arch=False):
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
            box(name + "Wall", (L - 0.06, W_ - 0.06, H - stone_h), (0, 0, (H + stone_h) / 2), M["planks"], bev=0),
            gable_prism(name + "Gable", L - 0.06, W_ - 0.06, roof_h, H, M["planks"])]
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

def banner(M, name, w, h, rod=True):
    """Swallowtail banner hanging from its top edge at the origin, facing -y."""
    notch = w * 0.3
    outline = [(-w / 2, 0), (w / 2, 0), (w / 2, -h), (0, -h + notch), (-w / 2, -h)]
    p = [mesh(name + "Trim", [(x * 1.06, 0, z * 1.03 + 0.0) for x, z in outline], [range(5)], M["shadow_trim"]),
         mesh(name + "Cloth", [(x, -0.004, z - 0.01) for x, z in outline], [range(5)], M["shadow"])]
    p.append(shadow_emblem.build(name + "Sigil", (0, -0.01, -h * 0.4), radius=w * 0.32))
    if rod:
        p.append(box(name + "Rod", (w + 0.2, 0.04, 0.04), (0, 0, 0.02), M["iron"], bev=0.005))
        for sx in (-1, 1):
            p.append(sphere(f"{name}Finial{sx}", 0.035, (sx * (w / 2 + 0.11), 0, 0.02), M["brass"], segs=8))
    return p


# ---------------------------------------------------------------- buildings

def build_hall(M):
    L, Wd, H = 6.0, 3.8, 3.4
    pw = L / 5
    front = {"panels": 5, "light": 4,
             "windows": [(-2 * pw, 1.95, 0.6, 1.0), (-pw, 1.95, 0.6, 1.0),
                         (pw, 1.95, 0.6, 1.0), (2 * pw, 1.95, 0.6, 1.0)],
             "doors": [(0, 0.95, 2.0, M["darkwood"])]}
    side = {"panels": 3, "braces": [(0, 1), (2, -1)], "windows": [(0, 1.95, 0.6, 1.0)], "light": 4}
    root = house(M, "Hall", L, Wd, H, 2.4, (*HALL, 0), 0, {"front": front, "right": side, "left": side,
                                                         "back": {"panels": 5}})
    cx, cy = HALL
    fy = cy - Wd / 2
    # gabled porch over the door on two posts; its ridge runs back into the main roof
    py = fy - 1.3
    for sx in (-1, 1):
        cyl(f"PorchPost{sx}", 0.07, 2.6, (cx + sx * 0.85, py, 1.38), M["darkwood"], verts=8)
        lantern.build(f"PorchLantern{sx}", (cx + sx * 0.85, py - 0.12, 2.15 - lantern.BASE), energy=35)
    porch = roof(M, "Porch", 1.6, 2.0, 2.7, 0.9, ov=0.15)
    group("PorchRoof", porch, (cx, fy - 0.55, 0), math.pi / 2)
    box("PorchBeam", (2.0, 0.12, 0.14), (cx, py, 2.68), M["darkwood"])
    # boarded gable over the porch front, with the party crest on it
    tri = mesh("PorchGable", [(cx - 0.95, py, 2.72), (cx + 0.95, py, 2.72), (cx, py, 3.58)], [(0, 1, 2)],
               M["planks"], solid=0.06)
    tri.modifiers["solid"].offset = 0
    shadow_emblem.build("HallCrest", (cx, py - 0.05, 3.05), radius=0.26)
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
        doors.append((x - 0.22, 0.62, 1.8, M["wood"]))
        wins.append((x + 0.38, 1.6, 0.3, 0.55))
    front = {"panels": 5, "windows": wins, "doors": doors, "light": 2}
    side = {"panels": 2, "braces": [(0, 1), (1, -1)], "windows": [(0, 1.6, 0.4, 0.6)], "light": 2}
    root = house(M, "Dorm", L, Wd, H, 1.6, (*DORM, 0), math.pi / 2,
                 {"front": front, "right": side, "left": side, "back": {"panels": 5}}, stone_h=0.7)
    # per-room touches in dorm-local coords: colour pennant, number plaque, lantern
    for i in range(5):
        x = -L / 2 + (i + 0.5) * pw
        p = [box(f"DormPlaque{i}", (0.22, 0.03, 0.16), (x - 0.22, -Wd / 2 - 0.14, 2.22), M["party"][i], bev=0.01)]
        for k in range(i + 1):
            p.append(sphere(f"DormPip{i}_{k}", 0.014, (x - 0.22 - 0.075 + k * 0.0375 * (1 if i else 0) + (0.075 if i == 0 else 0),
                                                       -Wd / 2 - 0.16, 2.22), M["silver"], segs=6))
        p.append(lantern.build(f"DormLantern{i}", (x + 0.12, -Wd / 2 - 0.25, 2.05 - lantern.BASE), energy=10))
        p.append(box(f"DormBracket{i}", (0.03, 0.25, 0.03), (x + 0.12, -Wd / 2 - 0.13, 2.3), M["iron"], bev=0))
        p.append(box(f"DormMat{i}", (0.6, 0.4, 0.02), (x - 0.22, -Wd / 2 - 0.55, 0.1), M["burlap"], bev=0.005))
        group(f"DormRoom{i}", p, (*DORM, 0), math.pi / 2)
    # one stone chimney against the front gable
    chy = DORM[1] - L / 2 - 0.2
    box("DormChimney", (0.55, 0.45, H + 2.3), (DORM[0] - 0.45, chy, (H + 2.3) / 2 + 0.05), M["stone"], bev=0.04)
    box("DormChimneyCap", (0.68, 0.58, 0.12), (DORM[0] - 0.45, chy, H + 2.38), M["stone"], bev=0.03)
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
        lantern.build(f"WallLantern{i}", (x, y, 1.9 - lantern.BASE), energy=25)

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
    # the right fence stops short of the patio, which opens onto the lane over a low kerb
    fence("FenceR", 0.2, 7.9, W - 0.2, "y")
    box("PatioKerb", (0.2, D - 0.2 - 7.9, 0.3), (W - 0.2, (D - 0.2 + 7.9) / 2, 0.2), M["flag"], bev=0.03)

    # gate: two heavy posts, a crossbeam and the hanging name board
    gx, gy = GATE_X, 0.2
    for sx in (-1, 1):
        box(f"GatePost{sx}", (0.32, 0.32, 3.4), (gx + sx * 1.3, gy, 1.75), M["log"], bev=0.03)
        cone(f"GatePostCap{sx}", 0.26, 0.0, 0.3, (gx + sx * 1.3, gy, 3.6), M["darkwood"], verts=4,
             rot=(0, 0, math.pi / 4), smooth=False)
        lantern.build(f"GateLantern{sx}", (gx + sx * 1.3, gy - 0.32, 2.4 - lantern.BASE), energy=45)
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

def tripod(M, name, loc, foot=0.6, apex=1.45):
    """Three iron legs from the ground meeting at an apex, with a pot hung on a chain."""
    x, y, z = loc
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.3
        fx, fy = x + foot * math.cos(a), y + foot * math.sin(a)
        d = Vector((x - fx, y - fy, apex))
        u = d.normalized()
        cyl(f"{name}Leg{k}", 0.02, d.length + 0.08, (fx + d.x / 2, fy + d.y / 2, z + apex / 2), M["iron"],
            rot=(-math.asin(u.y), math.atan2(u.x, u.z), 0), verts=6)
    torus(name + "Lash", 0.035, 0.012, (x, y, z + apex - 0.04), M["rope"], segs=12)
    cyl(name + "Chain", 0.008, apex - 0.62, (x, y, z + (apex + 0.62) / 2), M["iron"], verts=6)
    sphere(name + "Pot", 0.17, (x, y, z + 0.5), M["iron"], scale=(1, 1, 0.8), segs=14)
    torus(name + "PotRim", 0.15, 0.015, (x, y, z + 0.6), M["iron"], segs=24)


def woodpile(M, name, x, y0, y1, rows=4):
    """Split logs stacked against the fence (running along y) under a little shake roof."""
    n = int((y1 - y0) / 0.17)
    for r in range(rows):
        for k in range(n - (r % 2)):
            y = y0 + 0.085 + k * 0.17 + (0.085 if r % 2 else 0)
            cyl(f"{name}Log{r}_{k}", 0.08 + random.uniform(-0.01, 0.01), 0.55, (x, y, 0.17 + r * 0.15),
                M["log"], rot=(0, math.pi / 2, random.uniform(-0.1, 0.1)), verts=8)
    for sy, y in ((0, y0 - 0.05), (1, y1 + 0.05)):
        box(f"{name}Post{sy}", (0.08, 0.08, 1.15), (x + 0.2, y, 0.65), M["darkwood"])
        box(f"{name}PostF{sy}", (0.08, 0.08, 0.95), (x - 0.3, y, 0.55), M["darkwood"])
    box(name + "Roof", (0.85, y1 - y0 + 0.35, 0.05), (x - 0.05, (y0 + y1) / 2, 1.12), M["shake2"],
        rot=(0, -0.25, 0))


def build_yard(M):
    """Lived-in yard round the bonfire: log benches and a pot on a tripod, a woodpile with a
    chopping block, barrels and crates, the party's lectern, staff rack and scrying orb, and
    grass, trees and wild flowers creeping back in round the trodden earth."""
    cx, cy = FIRE
    cyl("FireGround", 1.0, 0.02, (cx, cy, 0.1), M["soil"], verts=32)
    for k in range(11):
        a = k * 2 * math.pi / 11
        sphere(f"FireStone{k}", 0.13, (cx + 0.5 * math.cos(a), cy + 0.5 * math.sin(a), 0.14), M["stone"],
               scale=(1, 1, 0.7), segs=8)
    for k in range(4):
        cyl(f"FireLog{k}", 0.07, 0.7, (cx, cy, 0.19), M["log"], rot=(math.pi / 2, 0, k * math.pi / 4), verts=8)
    for k in range(10):
        sphere(f"FireEmber{k}", 0.035, (cx + random.uniform(-0.25, 0.25), cy + random.uniform(-0.25, 0.25), 0.15),
               M["ember"], segs=6)
    fire(M, "Bonfire", (cx, cy, 0.2), 0.17, M["fire"], M["firecore"], (1.0, 0.45, 0.15), 320)
    tripod(M, "Tripod", (cx, cy, 0.1))
    for k, a in enumerate((0.35, 1.9, 3.3, 4.85)):
        cyl(f"LogBench{k}", 0.17, 1.2, (cx + 1.45 * math.cos(a), cy + 1.45 * math.sin(a), 0.26), M["log"],
            rot=(math.pi / 2, 0, a), verts=12)
    # woodpile against the right fence, chopping block with an axe and a few split logs
    woodpile(M, "Woodpile", 13.2, 2.4, 4.4)
    bx, by = 12.45, 2.35
    cyl("ChopBlock", 0.24, 0.45, (bx, by, 0.3), M["log"], verts=14)
    cyl("ChopBlockTop", 0.22, 0.01, (bx, by, 0.53), M["straw"], verts=14)
    axe = [cyl("AxeHandle", 0.02, 0.75, (0, 0, 0.3), M["wood"], verts=8),
           box("AxeHead", (0.16, 0.03, 0.1), (0.06, 0, 0.0), M["steel"], bev=0.005)]
    g = group("Axe", axe, (bx + 0.05, by - 0.02, 0.55))
    g.rotation_euler = (0.0, -0.55, 0.4)
    for k in range(5):
        a = random.uniform(0, 2 * math.pi)
        cyl(f"Split{k}", 0.06, 0.4, (bx + 0.55 * math.cos(a), by + 0.55 * math.sin(a), 0.14), M["log"],
            rot=(math.pi / 2, 0, random.uniform(0, math.pi)), verts=6, smooth=False)
    # barrels and crates by the front fence
    for i, (x, y, r, h) in enumerate(((8.55, 1.3, 0.25, 0.6), (8.7, 1.85, 0.22, 0.55), (9.1, 1.2, 0.23, 0.6))):
        barrel.build(f"YardBarrel{i}", (x, y, 0.08), radius=r, height=h)
    crate.build("YardCrate0", (9.65, 1.25, 0.08), 0.2, size=0.5)
    crate.build("YardCrate1", (9.62, 1.27, 0.58), -0.15, size=0.4)
    crate.build("YardCrate2", (10.2, 1.15, 0.08), 0.5, size=0.38)
    sphere("GrainSack", 0.2, (9.3, 1.75, 0.25), M["burlap"], scale=(1, 0.8, 1.2), segs=12)
    # the party's things at the back: lectern with a spellbook, staff rack, scrying orb
    lx, ly = 9.0, 6.25
    box("LecternFoot", (0.45, 0.35, 0.06), (lx, ly, 0.11), M["darkwood"])
    box("LecternPost", (0.1, 0.1, 0.95), (lx, ly, 0.6), M["darkwood"])
    box("LecternTop", (0.5, 0.38, 0.04), (lx, ly, 1.1), M["darkwood"], rot=(0.35, 0, 0))
    book = open_book.build("YardSpellbook", (lx, ly - 0.01, 1.135), cover=M["shadow_trim"])
    book.rotation_euler = (0.35, 0, 0)
    wx, wy = 10.35, 6.35
    weapon_rack.build("StaffRack", (wx, wy, 0.08), width=1.5)
    for k, head in enumerate(("crystal", "orb", "crystal", "orb", "crystal")):
        st = staff.build(f"RackStaff{k}", (wx - 0.6 + k * 0.3, wy - 0.03, 0.26), head=head, length=1.55,
                         glow="arcane_cyan" if head == "orb" else None, light=False)
        st.rotation_euler = (math.radians(4), 0, 0)
    sx_, sy_ = 11.75, 6.3
    cyl("ScryPillar", 0.14, 0.85, (sx_, sy_, 0.5), M["flag"], verts=16)
    cyl("ScryCap", 0.2, 0.06, (sx_, sy_, 0.95), M["flag"], verts=16)
    crystal_ball.build("ScryingOrb", (sx_, sy_, 0.98), radius=0.12, glass="arcane_cyan",
                       light_color=(0.4, 0.8, 1.0))
    cyl("WaterTrough", 0.3, 1.2, (12.9, 6.3, 0.35), M["wood"], rot=(math.pi / 2, 0, math.pi / 2), verts=12)
    pot = cauldron.build("YardCauldron", (12.2, 1.35, 0.08), brew=(1.0, 0.72, 0.18), rng=random)
    pot.scale = (1.6, 1.6, 1.6)
    # trees, shrubs and wild flowers round the edge of the trodden earth
    tree.build("YardBirch", (8.6, 5.2, 0), height=2.9, crown=0.7, rng=random)
    # only low shrubs at the front corner, so nothing blocks the view into the yard
    for i, (x, y) in enumerate(((13.35, 4.75), (8.45, 2.6), (12.6, 0.6), (13.25, 1.0), (13.3, 1.7))):
        bush.build(f"YardBush{i}", (x, y, 0.08), radius=random.uniform(0.28, 0.38),
                   bloom=random.choice((None, "bloom_yellow", "bloom_white")), rng=random)
    wild = ["bloom_white", "bloom_yellow", "bloom_blue", "bloom_pink", "bloom_red"]
    for i, (x, y, rx, ry) in enumerate(((12.4, 5.9, 0.5, 0.3), (8.55, 4.4, 0.3, 0.5), (11.0, 1.0, 0.5, 0.25),
                                        (12.7, 4.6, 0.3, 0.3), (8.5, 6.0, 0.3, 0.3))):
        flower_patch.build(f"YardFlowers{i}", (x, y, 0.08), rx=rx, ry=ry, count=int(60 * rx * ry) + 6,
                           colors=wild, rng=random)
    # torch posts at the back corners
    for i, (x, y) in enumerate(((8.4, 6.75), (13.25, 6.8))):
        cyl(f"Torch{i}", 0.05, 1.8, (x, y, 1.0), M["log"], verts=8)
        cone(f"TorchCup{i}", 0.09, 0.05, 0.14, (x, y, 1.95), M["iron"], rot=(math.pi, 0, 0), verts=10)
        fire(M, f"Torch{i}Fire", (x, y, 2.0), 0.06, M["fire"], M["firecore"], (1.0, 0.5, 0.18), 60)


# ---------------------------------------------------------------- props

def build_courtyard(M):
    """Back-right corner: patio under a grapevine pergola with a long feasting table."""
    px, py = 12.15, 9.75
    box("Patio", (3.0, 3.6, 0.04), (px, py, 0.09), M["flag"], bev=0.02)
    for i in range(6):
        for j in range(7):
            box(f"PatioTile{i}_{j}", (0.46, 0.48, 0.02), (px - 1.25 + i * 0.5, py - 1.5 + j * 0.5, 0.115),
                M["flag"] if (i + j) % 3 else M["stone"], rot=(0, 0, random.uniform(-0.03, 0.03)), bev=0.015)
    pergola.build("Pergola", (px, py, 0.1))
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
    barrel.build("DiceBarrel", (bx, by, 0.08), radius=0.28, height=0.75)
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
    # apple tree in front of the patio, clear of the pergola beams; flowers around its foot
    tree.build("AppleTree", (12.35, 6.95, 0), height=2.6, crown=0.6, clumps=7, lumpy=True, fruit="apple",
               rng=random)
    flower_patch.build("AppleBed", (12.35, 6.95, 0.08), rx=0.35, ry=0.3, count=12,
                       colors=["bloom_white", "bloom_pink", "bloom_yellow"], rng=random)
    # enchanted candles floating over the feast, as in the homebase
    for k in range(7):
        candle.build(f"FloatCandle{k}", (px + random.uniform(-0.35, 0.35), py - 1.2 + k * 0.4,
                                          random.uniform(1.55, 1.95)), height=random.uniform(0.1, 0.18))


def build_garden(M):
    warm = ["bloom_red", "bloom_yellow", "bloom_white", "bloom_orange"]
    cool = ["bloom_blue", "bloom_white", "bloom_pink"]
    # beds along the hall front, either side of the porch
    hx, hy = HALL
    flower_bed.build("BedHallL", (hx - 2.0, hy - 2.3, 0.08), width=1.6, depth=0.45, colors=warm, rng=random)
    flower_bed.build("BedHallR", (hx + 2.0, hy - 2.3, 0.08), width=1.6, depth=0.45, colors=cool, rng=random)
    # flowers along the path to the hall
    for i, (x, colors) in enumerate(((GATE_X - 0.9, warm), (GATE_X + 0.9, cool))):
        flower_patch.build(f"HallPath{i}", (x, 5.75, 0.08), rx=0.22, ry=0.45, count=12, colors=colors, rng=random)
    # shrubs along the palisade and fences
    for i, x in enumerate((4.3, 5.4, 9.5, 10.4)):
        bush.build(f"BackBush{i}", (x, D - 0.7, 0.08), radius=random.uniform(0.35, 0.5),
                   bloom=random.choice((None, "bloom_red", "bloom_pink")), rng=random)
    for i, y in enumerate((0.9, 8.4, 9.6, 10.8)):
        bush.build(f"LeftBush{i}", (0.8, y, 0.08), radius=random.uniform(0.3, 0.45),
                   bloom=None if i % 2 else "bloom_yellow", rng=random)
    for i, x in enumerate((1.0, 2.0, 3.0, 4.0, 5.2)):
        bush.build(f"FrontBush{i}", (x, 0.6, 0.08), radius=random.uniform(0.25, 0.35),
                   bloom=random.choice(("bloom_red", "bloom_white", "bloom_pink")), rng=random)
    # trees, mostly in the back-left corner behind the dorm
    tree.build("OakA", (1.5, 9.0, 0), height=3.6, crown=1.1, rng=random)
    tree.build("OakB", (2.9, 10.7, 0), height=3.2, crown=0.95, rng=random)
    tree.build("PineA", (1.2, 10.9, 0), kind="pine", height=4.4, rng=random)
    tree.build("Birch", (10.4, 11.1, 0), height=3.0, crown=0.8, rng=random)
    flower_patch.build("OakMeadow", (2.4, 9.8, 0.08), rx=1.0, ry=1.4, count=45, colors=warm + cool, rng=random)
    # the party's crystal garden: arcane crystals pushing up through the meadow
    for i, (x, y, s) in enumerate(((2.2, 9.6, 1.0), (3.3, 9.5, 0.7), (1.9, 10.3, 0.8), (3.6, 10.2, 0.6))):
        crystal_cluster.build(f"Crystals{i}", (x, y, 0.08), random.uniform(0, 6), size=s, rng=random,
                              light=i < 2)
    # herb bed for the party cook
    flower_bed.build("Herbs", (3.0, 8.35, 0.08), width=1.0, depth=0.5, colors=["tuft", "bloom_white"], count=14,
                     rng=random)
    # window boxes under the hall's front windows
    pw = 6.0 / 5
    for i, dx in enumerate((-2 * pw, -pw, pw, 2 * pw)):
        x = hx + dx
        box(f"WinBox{i}", (0.7, 0.2, 0.16), (x, hy - 1.9 - 0.2, 1.33), M["darkwood"], bev=0.01)
        flower_patch.build(f"WinBox{i}Flowers", (x, hy - 2.1, 1.38), rx=0.3, ry=0.06, count=7,
                           colors=warm if i < 2 else cool, size=0.8, rng=random)
    # floating driftglobes over the yard; wrought-iron lamps by the plaza and along the path
    for i, (x, y, z) in enumerate(((9.6, 3.0, 3.0), (11.6, 5.0, 3.2))):
        driftglobe.build(f"YardGlobe{i}", (x, y, z), post=False, energy=90)
    for i, y in enumerate((1.6, 3.4, 5.0)):
        lamp_post.build(f"PathLamp{i}", (GATE_X + 0.85, y, 0.08), -math.pi / 2, arms=1, energy=90)


def build_props(M):
    # tiered fountain on its own little plaza beside the gate path
    px, py = PLAZA
    fountain.build("Fountain", (px, py, 0.11), radius=0.72)

    # well out on the lawn between the fountain and the hall, clear of both paths
    wx, wy = 5.05, 5.65
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
        barrel.build(f"DormBarrel{k}", (3.62, 1.2 + 0.5 * k, 0.08), radius=0.2, height=0.5)


# ---------------------------------------------------------------- scene setup

# ---------------------------------------------------------------- animation

FPS = 24
FRAMES = 48           # 2 s loop; lib.keyframe defaults to the same fps and length


def animate():
    """Loop the living bits over 2 s: flickering fires, bobbing candles and driftglobes,
    the fountain orb and its ring, rising cauldron bubbles and breathing magic lights."""
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAMES
    obs = bpy.data.objects

    for o in list(obs):
        n = o.name
        # seeded by name, so adding objects to the scene does not reshuffle everyone's phase
        rnd = random.Random(n)
        ph = rnd.uniform(0, 2 * math.pi)
        if "Flame" in n and o.type == "MESH" and "Candle" not in n:
            base = o.scale.copy()
            k = rnd.choice((3, 4, 5))
            keyframe(o, "scale", lambda t, b=base, k=k, ph=ph:
                     (b.x, b.y, b.z * (1 + 0.18 * wave(t, k, ph) + 0.07 * wave(t, 9, ph * 2))))
        elif n.endswith("Flame") and "Candle" in n:
            base = o.scale.copy()
            keyframe(o, "scale", lambda t, b=base, ph=ph: (b.x, b.y, b.z * (1 + 0.15 * wave(t, 6, ph))))
        elif o.type == "EMPTY" and n.startswith(("FloatCandle", "YardGlobe")) and not o.parent:
            base = o.location.copy()
            amp = 0.04 if n.startswith("FloatCandle") else 0.08
            keyframe(o, "location", lambda t, b=base, ph=ph, a=amp: (b.x, b.y, b.z + a * wave(t, 1, ph)))
        elif n in ("FountainOrb", "FountainOrbLight"):
            base = o.location.copy()
            keyframe(o, "location", lambda t, b=base: (b.x, b.y, b.z + 0.04 * wave(t, 1)))
        elif n == "FountainOrbRing":
            r0 = o.rotation_euler.copy()
            keyframe(o, "rotation_euler", lambda t, r=r0: (r.x, r.y, r.z + math.pi * t))
        elif "CauldronBubble" in n:
            base = o.location.copy()
            off = rnd.random()
            keyframe(o, "location", lambda t, b=base, off=off: (b.x, b.y, b.z + 0.3 * ((t / 2 + off) % 1.0)))

    def pulse(name, depth, k, ph=0.0):
        if name not in obs:
            return
        ld = obs[name].data
        base = ld.energy
        keyframe(None, "energy", lambda t: base * (1 + depth * wave(t, k, ph)), target=ld)

    for name, depth, k in (("BonfireLight", 0.2, 5), ("Torch0FireLight", 0.2, 4), ("Torch1FireLight", 0.2, 3),
                           ("FountainOrbLight", 0.3, 1), ("ScryingOrbLight", 0.35, 1),
                           ("YardCauldronGlow", 0.25, 3), ("Crystals0Light", 0.3, 1), ("Crystals1Light", 0.3, 2)):
        pulse(name, depth, k, random.Random(name).uniform(0, 6))


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


def paper_backdrop(world, color=(0.97, 0.94, 0.88), strength=1.5):
    """Show a flat off-white backdrop to the camera while the sky keeps lighting the scene
    (strength above 1 so AgX does not dull it to grey)."""
    nt = world.node_tree
    out = nt.nodes["World Output"]
    sky = out.inputs["Surface"].links[0].from_node
    paper = nt.nodes.new("ShaderNodeBackground")
    paper.inputs["Color"].default_value = (*color, 1)
    paper.inputs["Strength"].default_value = strength
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(sky.outputs["Background"], mix.inputs[1])
    nt.links.new(paper.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def setup_world_and_camera(samples, shot="wide", time="day", backdrop="sky"):
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
    if backdrop == "paper":
        paper_backdrop(world)

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
        # moon from the front-left so the hall facade catches it; cool rim from behind
        # so roofs and trees separate from the sky; soft fill from the camera side
        aimed("Moon", "SUN", (-8, -14, 18), 1.2, (0.6, 0.7, 1.0), 2)
        aimed("Rim", "AREA", (8, 32, 14), 4000, (0.5, 0.6, 1.0), 14)
        aimed("Fill", "AREA", (26, -16, 20), 2200, (0.65, 0.7, 1.0), 15)
    else:
        # late-morning sun from the front-left, cool bounce from the camera side
        aimed("Sun", "SUN", (-9, -13, 20), 4.0, (1.0, 0.91, 0.76), 2)
        aimed("Fill", "AREA", (26, -16, 20), 1200, (0.75, 0.85, 1.0), 15)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 35
    cam_data.clip_end = 200
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    if shot == "pergola":
        # low view in under the vine from the lane past the patio kerb, showing posts,
        # beams, slats, the vine stems and the feasting table
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
    anim_dir = None
    step = 1
    backdrop = "sky"
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
        elif a == "--anim":
            anim_dir = argv[i + 1]
        elif a == "--step":
            step = int(argv[i + 1])
        elif a == "--backdrop":
            backdrop = argv[i + 1]

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
    animate()
    setup_world_and_camera(samples, shot, time, backdrop)
    bpy.context.scene.render.resolution_percentage = res

    if blend_out:
        bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    if out:
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
    if anim_dir:
        # step > 1 renders every Nth frame for a choppier, stop-motion look at lower cost
        bpy.context.scene.frame_step = step
        bpy.context.scene.render.filepath = anim_dir.rstrip("/") + "/frame_"
        bpy.ops.render.render(animation=True)


main()
