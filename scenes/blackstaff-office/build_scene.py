"""Build a cutaway of the Blackstaff's office inside Blackstaff Tower (Waterdeep).

Run with:  python3 scenes/blackstaff-office/build_scene.py [--render out.png] [--samples N]
           [--shot wide|close|top] [--anim frames_dir [--step N]] [--res percent] [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P scenes/blackstaff-office/build_scene.py -- --render out.png

Units are metres. The semicircular office is centred on the origin and open
along the X axis (toward -Y) so the camera can look in. The room shell (walls,
floor, beams) is built here; furniture and props come from scenes/assets.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from assets import (arched_door, candle, chair, crystal_ball, curved_bookshelf,  # noqa: E402
                    great_fireplace, high_back_chair, hourglass, inkwell, lancet_window, map_table,
                    portrait, potion, scroll_cabinet, spiral_stair, wheel_chandelier, writing_desk)
from assets.lib import (Batch, box, cyl, keyframe, lathe, mat, noisy_mat, palette,  # noqa: E402
                        point_light, polar, reset, shell, sphere, wave)

random.seed(17)

R = 5.0           # inner radius of the round chamber
WALL = 0.5        # wall thickness
H = 4.6           # floor to the top beam
ARC = (0.0, math.pi)   # semicircular office: back half only, open along the X axis
DOOR_A = math.radians(11.25)                 # door centre, between the first two posts
DOOR_HALF = math.radians(8.4)                # half the angle taken by door + frame
FLOOR = 0.05      # top of the floor planks


def in_door(a):
    return abs(a - DOOR_A) < DOOR_HALF


def on_wall(r, deg):
    """loc and rot_z that put an asset (front -y) at radius r, facing the room centre."""
    a = math.radians(deg)
    return polar(r, a), a - math.pi / 2


def local(loc, rot_z, px, py, pz):
    """World point of (px, py, pz) in the frame of an asset placed at loc / rot_z."""
    c, s = math.cos(rot_z), math.sin(rot_z)
    return (loc[0] + px * c - py * s, loc[1] + px * s + py * c, loc[2] + pz)


# ---------------------------------------------------------------- materials

def build_materials():
    # the shared palette (stone, wood, darkwood, plaster, blackstone, velvet...)
    # keeps this scene in step with the homebase; office-only materials follow
    M = palette()
    M["planks"] = [noisy_mat(f"FloorPlanks{i}", tuple(c * k for c in (0.22, 0.12, 0.06)),
                             tuple(c * k for c in (0.36, 0.21, 0.11)), 4, 0.65, stretch=(12, 1, 1))
                   for i, k in enumerate((1.0, 0.85, 1.12))]
    M["staff"] = staff_mat()
    M["rug"] = rug_mat()
    M["crystal"] = mat("CrystalBall", (0.6, 0.75, 1.0), 0.05, emit=(0.35, 0.55, 1.0), emit_strength=3)
    M["arcane"] = mat("Arcane", (0.5, 0.3, 1.0), 0.2, emit=(0.55, 0.3, 1.0), emit_strength=10)
    M["mote"] = mat("Mote", (1, 1, 1), 1, emit=(0.75, 0.85, 1.0), emit_strength=6)
    M["leaf"] = noisy_mat("Leaf", (0.02, 0.07, 0.02), (0.08, 0.18, 0.05), 10, 0.7, bump=0.4)
    M["clay"] = mat("Clay", (0.35, 0.13, 0.06), 0.8)
    M["potions"] = [mat(f"Potion{i}", c, 0.1, emit=c, emit_strength=1.5) for i, c in enumerate([
        (0.9, 0.05, 0.1), (0.1, 0.35, 1.0), (0.2, 0.9, 0.3), (0.9, 0.6, 0.1), (0.6, 0.2, 0.9)])]
    M["office_books"] = [noisy_mat(f"OfficeBook{i}", tuple(x * 0.6 for x in c), c, 40, 0.65, bump=0.05)
                         for i, c in enumerate([
                             (0.40, 0.05, 0.05), (0.05, 0.20, 0.08), (0.08, 0.10, 0.35),
                             (0.35, 0.25, 0.08), (0.25, 0.08, 0.25), (0.12, 0.09, 0.06),
                             (0.02, 0.02, 0.025), (0.30, 0.15, 0.05)])]
    return M


def staff_mat():
    """Seamless, glassy black stone with a faint violet sheen, for the Blackstaff."""
    m = bpy.data.materials.new("PolishedBlackStone")
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
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Coat Weight"].default_value = 0.4
    bsdf.inputs["Coat Roughness"].default_value = 0.05
    bsdf.inputs["Coat Tint"].default_value = (0.75, 0.65, 1.0, 1)
    return m


def rug_mat():
    """Deep violet rug with a border and a faint medallion, from radial distance."""
    m = bpy.data.materials.new("OfficeRug")
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


# ---------------------------------------------------------------- room

def build_room(M):
    shell("Plinth", R + WALL + 0.3, 0, -0.5, 0.0, M["stone"], arc=ARC, segs=160, loc=(0, -0.3, 0))
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
            B.box(rnd.choice(M["planks"]), (pw - 0.008, ln - 0.008, 0.05), (x, y + ln / 2, 0.025))
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
            if not (in_door(mid) or in_door(a) or in_door(a + da)):
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
        a = math.radians(deg)
        p = polar(R - 0.02, a, (H + 1.47) / 2)
        if deg in (0, 180):
            p = (p[0] - math.copysign(0.08, p[0]), p[1] + 0.08, p[2])
        box(f"Post{deg}", (0.16, 0.18, H - 1.47), p, M["darkwood"], rot=(0, 0, a))
        # pegged joints
        for zz in (1.58, H - 0.3):
            sphere(f"Peg{deg}_{zz}", 0.018, polar(R - 0.115, a, zz), M["darkwood"], segs=8)
    for d0, d1 in zip(posts, posts[1:]):
        if d1 - d0 > 30 or d0 == 0 or 100 < (d0 + d1) / 2 < 150:
            continue   # door, window and chimney bays stay clear
        mid = math.radians((d0 + d1) / 2)
        span = R * math.radians(d1 - d0) - 0.16
        hh = H - 1.65
        tilt = math.atan2(span, hh) * (1 if (d0 // 22) % 2 else -1)
        box(f"Brace{d0}", (0.12, 0.12, math.hypot(span, hh) - 0.1),
            polar(R - 0.01, mid, (H + 1.47) / 2), M["darkwood"], rot=(tilt, 0, mid))
    # rafters over the cut, each on a carved bracket
    for deg in range(0, 181, 15):
        a = math.radians(min(max(deg, 1.5), 178.5))
        box(f"Rafter{deg}", (1.2, 0.16, 0.2), polar(R - 0.5, a, H + 0.1), M["darkwood"], rot=(0, 0, a))
        box(f"RafterBracket{deg}", (0.36, 0.12, 0.14), polar(R - 0.26, a, H - 0.07),
            M["darkwood"], rot=(0, math.radians(-30), a))
    shell("RafterPlate", R - 0.85, R - 1.05, H + 0.2, H + 0.32, M["darkwood"], arc=ARC, segs=128)
    # stone end faces of the cut
    for a in ARC:
        p = polar(R + WALL / 2, a, H / 2)
        box(f"CutFace{a:.2f}", (WALL + 0.06, 0.08, H), (p[0], -0.04, p[2]), M["stone"], bev=0.02)


# ---------------------------------------------------------------- walls: door, window, hearth, shelves

def build_walls(M):
    loc, rz = on_wall(R, math.degrees(DOOR_A))
    arched_door.build("Door", loc, rz)

    lancet_window.build("Window", (0, R - 0.02, 0))
    # potions and a candle on the sill (sill top at z = 1.0)
    for k in range(3):
        potion.build(f"SillPotion{k}", (-0.55 + k * 0.13, R - 0.22, 1.0), liquid=M["potions"][k])
    candle.build("SillCandle", (0.55, R - 0.22, 1.0), height=0.16)

    loc, rz = on_wall(R, 124)
    great_fireplace.build("Hearth", loc, rz, chimney_top=H - 0.25)
    # portrait of the first Blackstaff on the chimney breast, above the string course
    portrait.build("Portrait", local(loc, rz, 0, -0.42, 2.3), rz)
    # mantel dressing: candlesticks, a skull, a row of potions (mantel top z = 1.765)
    zm = 1.765
    for k, px in enumerate((-0.85, 0.85)):
        lathe(f"MantelStick{k}", [(0.045, 0.0), (0.045, 0.012), (0.015, 0.03), (0.012, 0.09),
                                  (0.03, 0.1), (0.022, 0.115)], local(loc, rz, px, -0.48, zm),
              M["brass"], segs=16)
        candle.build(f"MantelCandle{k}", local(loc, rz, px, -0.48, zm + 0.115), height=0.22, light=False)
    sphere("MantelSkull", 0.09, local(loc, rz, -0.45, -0.48, zm + 0.075), M["bone"], scale=(1, 1.1, 0.9))
    for k in range(5):
        potion.build(f"MantelPotion{k}", local(loc, rz, 0.15 + k * 0.11, -0.48, zm), radius=0.04,
                     liquid=M["potions"][k])

    r_shelf = R - 0.14
    for k, (b0, b1) in enumerate([(47, 72), (140, 156)]):
        loc, rz = on_wall(r_shelf, (b0 + b1) / 2)
        curved_bookshelf.build(f"Shelf{k}", loc, rz, radius=r_shelf, arc=b1 - b0, height=H - 0.55,
                               books=M["office_books"], rng=random.Random(9 + k))

    loc, rz = on_wall(R - 0.4, 34)
    scroll_cabinet.build("ScrollCabinet", loc, rz)


# ---------------------------------------------------------------- furniture and desk dressing

def build_desk(M):
    cx, cy = 0.0, 2.45
    writing_desk.build("Desk", (cx, cy, FLOOR))
    zt = FLOOR + 0.786

    def P(dx, dy, z=0.0):
        return (cx + dx, cy + dy, zt + z)

    B = Batch()
    rnd = random.Random(5)
    for k in range(6):
        B.box(M["paper"], (0.21, 0.29, 0.002), P(0.55 + rnd.uniform(-0.02, 0.02), -0.05, 0.002 + k * 0.004),
              rz=rnd.uniform(-0.2, 0.2))
    for k in range(3):
        B.box(M["old_parchment"], (0.21, 0.29, 0.002), P(-0.35 + k * 0.08, -0.15, 0.002 + k * 0.002),
              rz=rnd.uniform(-0.5, 0.5))
    for k in range(4):
        B.box(M["office_books"][k], (0.24, 0.32, 0.05), P(0.9, 0.25, 0.025 + k * 0.052),
              rz=rnd.uniform(-0.15, 0.15))
    B.build("DeskPapers")
    # open ledger in front of the chair
    for s in (-1, 1):
        box(f"Ledger{s}", (0.2, 0.29, 0.012), P(s * 0.105, 0.05, 0.014), M["paper"],
            rot=(0, s * math.radians(-4), 0), bev=0.002)
    box("LedgerCover", (0.44, 0.31, 0.01), P(0, 0.05, 0.005), M["desk_leather"], bev=0.003)
    inkwell.build("Inkwell", P(0.3, 0.2))
    hourglass.build("Hourglass", P(-0.35, 0.3))
    cyl("SealHandle", 0.02, 0.09, P(0.4, -0.3, 0.06), M["darkwood"], verts=10)
    cyl("SealBase", 0.03, 0.03, P(0.4, -0.3, 0.015), M["brass"], verts=14)
    cyl("SealWaxStick", 0.018, 0.12, P(0.5, -0.32, 0.015), M["seal_wax"], rot=(0, math.radians(90), 0.4),
        verts=8)
    # candle trio in a pewter dish
    cyl("CandleDish", 0.12, 0.02, P(-0.85, 0.2, 0.01), M["pewter"], verts=20)
    for k, (dx, dy) in enumerate([(-0.05, 0.04), (0.05, 0.04), (0.0, -0.05)]):
        candle.build(f"DeskCandle{k}", P(-0.85 + dx, 0.2 + dy, 0.02), height=0.14 + 0.05 * k, light=False)
    point_light("DeskCandleLight", P(-0.85, 0.2, 0.35), 25, (1.0, 0.6, 0.25), radius=0.03)
    crystal_ball.build("ScryingOrb", P(-0.6, 0.3), radius=0.1, glass=M["crystal"], light_color=(0.4, 0.6, 1.0))
    sphere("DeskSkull", 0.09, P(1.0, -0.25, 0.08), M["bone"], scale=(1, 1.1, 0.9))
    # the Blackstaff itself, leaning on the desk end
    x, y = cx + 1.27, cy - 0.1
    cyl("Blackstaff", 0.028, 2.0, (x, y, FLOOR + 1.0), M["staff"], rot=(0, math.radians(-6), 0), verts=12)
    for zz in (0.4, 1.0, 1.6):
        cyl(f"BlackstaffBand{zz}", 0.034, 0.03, (x - 0.105 * (zz - 1.0), y, FLOOR + zz), M["pewter"],
            rot=(0, math.radians(-6), 0), verts=12)
    sphere("BlackstaffTip", 0.045, (x - 0.105, y, FLOOR + 1.99), M["arcane"], segs=12)


def build_furniture(M):
    high_back_chair.build("BlackstaffChair", (0, 3.3, FLOOR))
    chair.build("VisitorChairL", (-0.7, 1.15, FLOOR), math.pi + math.radians(12), cushion=M["velvet"])
    chair.build("VisitorChairR", (0.7, 1.15, FLOOR), math.pi - math.radians(18))
    shell("Rug", 2.3, 0, FLOOR, FLOOR + 0.015, M["rug"], loc=(0, 2.25, 0), segs=96)
    bpy.context.object.scale = (1.3, 0.9, 1.0)
    map_table.build("MapTable", (3.0, 1.45, FLOOR))
    spiral_stair.build("Stair", polar(3.85, math.radians(166)), height=H)
    wheel_chandelier.build("Chandelier", (0, 2.3, H + 0.1), drop=1.2)
    # potted plants flanking the window
    pot = [(0.0, 0.0), (0.15, 0.0), (0.17, 0.03), (0.2, 0.3), (0.23, 0.33), (0.23, 0.38),
           (0.2, 0.38), (0.19, 0.34)]
    rnd = random.Random(3)
    for k, deg in enumerate((76, 104)):
        x, y, _ = polar(R - 0.45, math.radians(deg))
        lathe(f"Pot{k}", pot, (x, y, FLOOR), M["clay"], segs=28)
        shell(f"Soil{k}", 0.19, 0, 0.36, 0.37, mat("Soil", (0.05, 0.03, 0.02), 1), loc=(x, y, FLOOR), segs=28)
        for j in range(5):
            sphere(f"Plant{k}_{j}", 0.18, (x + rnd.uniform(-0.12, 0.12), y + rnd.uniform(-0.12, 0.12),
                                           0.6 + rnd.uniform(0, 0.4)), M["leaf"], scale=(1, 1, 1.4), segs=14)


def build_magic(M):
    """Books drifting near the shelves and dust motes in the moonbeam."""
    rnd = random.Random(12)
    for i in range(4):
        a = math.radians(rnd.uniform(40, 140))
        px, py, _ = polar(R - 1.4, a)
        box(f"FlyBook{i}", (0.22, 0.16, 0.05), (px, py, rnd.uniform(2.6, 3.6)), rnd.choice(M["office_books"]),
            rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0, 6)), bev=0.008)
    for i in range(24):
        t = rnd.random()
        # along the beam from the window head down toward the floor in front of the desk
        p = Vector((0.3, R + 0.6, 3.7)).lerp(Vector((-0.6, 1.0, 0.3)), 0.25 + 0.6 * t)
        p += Vector((rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), rnd.uniform(-0.3, 0.3)))
        sphere(f"Mote{i}", rnd.uniform(0.006, 0.012), tuple(p), M["mote"], segs=6)


def build_atmosphere():
    """Light haze inside the room so the window casts a visible beam."""
    m = bpy.data.materials.new("HazeMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.02
    pv.inputs["Anisotropy"].default_value = 0.35
    pv.inputs["Color"].default_value = (0.9, 0.85, 0.8, 1)
    nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
    shell("Haze", R - 0.05, 0, 0.1, H - 0.05, m, arc=ARC, segs=64)
    bpy.context.object.visible_shadow = False


# ---------------------------------------------------------------- animation

def animate():
    """Two-second loop: flames flicker, lights breathe, books and motes drift,
    the city illusion over the map table sways."""
    scene = bpy.context.scene
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 48
    obs = bpy.data.objects
    for o in obs:
        n = o.name
        # seeded by name, so adding objects does not reshuffle everyone's phase
        rnd = random.Random(n)
        ph = rnd.uniform(0, 2 * math.pi)
        if o.type != "MESH" and not n.endswith("IllusionRig"):
            continue
        if n.startswith("HearthFlame"):
            base = o.scale.copy()
            k = rnd.choice((3, 4, 5))
            keyframe(o, "scale", lambda t, b=base, k=k, ph=ph:
                     (b.x, b.y, b.z * (1 + 0.18 * wave(t, k, ph) + 0.07 * wave(t, 9, ph * 2))))
        elif n.endswith("Flame"):
            base = o.scale.copy()
            keyframe(o, "scale", lambda t, b=base, ph=ph: (b.x, b.y, b.z * (1 + 0.15 * wave(t, 6, ph))))
        elif n.startswith("FlyBook"):
            base, r0 = o.location.copy(), o.rotation_euler.copy()
            keyframe(o, "location", lambda t, b=base, ph=ph: (b.x, b.y, b.z + 0.06 * wave(t, 1, ph)))
            keyframe(o, "rotation_euler", lambda t, r=r0, ph=ph:
                     (r.x + 0.08 * wave(t, 1, ph + 1), r.y, r.z + 0.1 * wave(t, 1, ph)))
        elif n.startswith("Mote"):
            base = o.location.copy()
            keyframe(o, "location", lambda t, b=base, ph=ph:
                     (b.x + 0.04 * wave(t, 1, ph), b.y + 0.04 * wave(t, 1, ph + 2),
                      b.z + 0.08 * wave(t, 1, ph + 4)))
        elif n.endswith("IllusionRig"):
            base, r0 = o.location.copy(), o.rotation_euler.copy()
            keyframe(o, "rotation_euler", lambda t, r=r0: (r.x, r.y, r.z + 0.35 * wave(t, 1)))
            keyframe(o, "location", lambda t, b=base: (b.x, b.y, b.z + 0.03 * wave(t, 2)))

    def pulse(name, depth, k, ph=0.0):
        ld = obs[name].data
        base = ld.energy
        keyframe(None, "energy", lambda t: base * (1 + depth * wave(t, k, ph)), target=ld)

    pulse("HearthLight", 0.18, 5)
    pulse("ChandelierLight", 0.06, 3, 1.0)
    pulse("DeskCandleLight", 0.12, 6, 2.0)
    pulse("DoorSconceCandleLight", 0.12, 6, 0.5)
    pulse("ScryingOrbLight", 0.4, 1)
    pulse("MapTableIllusionLight", 0.3, 2)


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
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
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
    anim_dir = None
    res = 100
    step = 1
    for i, a in enumerate(argv):
        if a == "--render":
            out = argv[i + 1]
        elif a == "--samples":
            samples = int(argv[i + 1])
        elif a == "--shot":
            shot = argv[i + 1]
        elif a == "--save":
            blend_out = argv[i + 1]
        elif a == "--anim":
            anim_dir = argv[i + 1]
        elif a == "--step":
            step = int(argv[i + 1])
        elif a == "--res":
            res = int(argv[i + 1])

    reset()
    M = build_materials()
    build_room(M)
    build_walls(M)
    build_desk(M)
    build_furniture(M)
    build_magic(M)
    build_atmosphere()
    animate()
    setup_world_and_camera(samples, shot)
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
