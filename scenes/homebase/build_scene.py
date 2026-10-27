"""Build a small diorama of a D&D party's homebase in Blender.

Run with:  python3 scenes/homebase/build_scene.py [--render out.png] [--samples N]
           [--shot wide|close|top] [--anim frames_dir [--step N]] [--res percent] [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P scenes/homebase/build_scene.py -- --render out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from assets import (alembic, banner, bookshelf, candle, cauldron, chair, chest,  # noqa: E402
                    crystal_ball, desk, fireplace, miniature, mortar, open_book, potion,
                    round_table, rug, shield, staff, summoning_circle, sword, tankard, vial_rack,
                    weapon_rack, window, wizard_hat)
from assets.lib import (assign, box, cone, cyl, keyframe, mat, palette,  # noqa: E402
                        point_light, reset, sphere, wave)

random.seed(7)

# ---------------------------------------------------------------- room

ROOM = 4.0      # room is ROOM x ROOM, corner at (0,0); open toward +x/+y... flipped below
WALL_H = 3.0


def build_room(M):
    # Base plinth (diorama style) + floor
    box("Plinth", (ROOM + 0.3, ROOM + 0.3, 0.4), (ROOM / 2, ROOM / 2, -0.2),
        M["stone"], bev=0.04)
    for i in range(10):
        w = ROOM / 10
        box(f"Plank{i}", (w - 0.01, ROOM, 0.05),
            (w * i + w / 2, ROOM / 2, 0.025), M["floor"], bev=0.006)

    # Back walls: stone lower half, timber-framed plaster above
    # wall along x at y = ROOM (back), wall along y at x = 0 (left)
    t = 0.25
    box("WallBackStone", (ROOM + t, t, 1.0), (ROOM / 2 - t / 2, ROOM + t / 2, 0.5),
        M["stone"], bev=0.03)
    box("WallLeftStone", (t, ROOM, 1.0), (-t / 2, ROOM / 2, 0.5), M["stone"], bev=0.03)
    box("WallBackPlaster", (ROOM + t, t * 0.8, WALL_H - 1.0),
        (ROOM / 2 - t / 2, ROOM + t / 2, 1.0 + (WALL_H - 1.0) / 2), M["plaster"], bev=0)
    box("WallLeftPlaster", (t * 0.8, ROOM, WALL_H - 1.0),
        (-t / 2, ROOM / 2, 1.0 + (WALL_H - 1.0) / 2), M["plaster"], bev=0)

    # Individual stones along the base to break up the band
    for i in range(14):
        x = 0.15 + i * 0.29 + random.uniform(-0.03, 0.03)
        for row in range(3):
            z = 0.17 + row * 0.32
            box(f"StoneB{i}_{row}", (0.27, 0.06, 0.28),
                (x + (0.14 if row % 2 else 0), ROOM - 0.005, z),
                M["stone"], rot=(0, random.uniform(-0.05, 0.05), 0), bev=0.04)
            box(f"StoneL{i}_{row}", (0.06, 0.27, 0.28),
                (0.005, x + (0.14 if row % 2 else 0), z),
                M["stone"], rot=(random.uniform(-0.05, 0.05), 0, 0), bev=0.04)

    # Timber framing on plaster
    beam = 0.14
    for x in (0.0, 1.35, 2.7, ROOM):
        box(f"PostB{x}", (beam, beam, WALL_H - 1.0), (x, ROOM - 0.02, 2.0), M["darkwood"])
    for y in (0.0, 1.35, 2.7):
        box(f"PostL{y}", (beam, beam, WALL_H - 1.0), (0.02, y, 2.0), M["darkwood"])
    box("BeamBackLow", (ROOM, beam, beam), (ROOM / 2, ROOM - 0.02, 1.05), M["darkwood"])
    box("BeamBackTop", (ROOM, beam, beam), (ROOM / 2, ROOM - 0.02, WALL_H), M["darkwood"])
    box("BeamLeftLow", (beam, ROOM, beam), (0.02, ROOM / 2, 1.05), M["darkwood"])
    box("BeamLeftTop", (beam, ROOM, beam), (0.02, ROOM / 2, WALL_H), M["darkwood"])
    # diagonal braces
    box("BraceB", (beam * 0.8, beam * 0.8, 2.1), (2.025, ROOM - 0.02, 2.0),
        M["darkwood"], rot=(0, math.radians(38), 0))
    box("BraceL", (beam * 0.8, beam * 0.8, 2.1), (0.02, 0.675, 2.0),
        M["darkwood"], rot=(math.radians(-38), 0, 0))
    # Ceiling beams sticking out (cutaway look)
    for i in range(5):
        y = 0.4 + i * 0.85
        box(f"RafterL{i}", (0.5, 0.14, 0.16), (0.05, y, WALL_H + 0.12), M["darkwood"])
        box(f"RafterB{i}", (0.14, 0.5, 0.16), (y, ROOM - 0.05, WALL_H + 0.12), M["darkwood"])


def build_window(M):
    # Arched window on back wall, upper right, with potions on the sill
    cx, z = 3.35, 1.95
    window.build("Window", (cx, ROOM - 0.05, z))
    for i, key in enumerate(["glass_potion_r", "glass_potion_b", "glass_potion_g"]):
        potion.build(f"SillPotion{i}", (cx - 0.2 + i * 0.2, ROOM - 0.14, z - 0.39), liquid=M[key])


def build_fireplace(M):
    # Stone fireplace on the left wall
    y0 = 2.55
    fireplace.build("Fireplace", (0, y0, 0), math.radians(90), rng=random)
    # mantel trinkets: skull-ish trophy, candles, crystal
    sphere("MantelSkull", 0.09, (0.32, y0 - 0.45, 1.53), mat("Bone", (0.85, 0.8, 0.68), 0.6),
           scale=(1, 1, 0.9))
    for i, dy in enumerate((-0.15, 0.25)):
        candle.build(f"MantelCandle{i}", (0.3, y0 + dy, 1.45), height=0.12 + 0.05 * i, light=False)
    cone("MantelCrystal", 0.06, 0.0, 0.22, (0.3, y0 + 0.55, 1.56), M["crystal"], verts=6)
    point_light("CrystalLight", (0.45, y0 + 0.55, 1.6), 6, (0.6, 0.35, 1.0), radius=0.05)
    # mounted trophy shield above the mantel, crossed staves behind it
    shield.build("TrophyShield", (0.43, y0, 1.7), math.radians(90), color=M["blue"],
                 boss=M["brass"], rim=M["brass"])
    for s in (-1, 1):
        cyl(f"TrophyStaff{s}", 0.018, 1.0, (0.42, y0, 2.0), M["darkwood"],
            rot=(math.radians(40 * s), 0, 0), verts=8)
        sphere(f"TrophyStaffOrb{s}", 0.035,
               (0.42, y0 - s * 0.5 * math.sin(math.radians(40)), 2.0 + 0.5 * math.cos(math.radians(40))),
               M["arcane_cyan"], segs=10)


def build_table(M):
    cx, cy = 2.3, 1.7
    round_table.build("Table", (cx, cy, 0.05))

    # Map spread on the table, slightly curled corners via a subdivided plane
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, cy, 0.825))
    m = bpy.context.object
    m.name = "Map"
    m.scale = (0.9, 0.65, 1)
    m.rotation_euler = (0, 0, math.radians(12))
    bpy.ops.object.transform_apply(scale=True)
    assign(m, map_material())
    # dice
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.045,
                                          location=(cx + 0.45, cy - 0.45, 0.865))
    assign(bpy.context.object, mat("DiceRed", (0.7, 0.02, 0.05), 0.2))
    bpy.context.object.name = "D20"
    for i in range(3):
        box(f"D6_{i}", (0.05, 0.05, 0.05),
            (cx + 0.55 + i * 0.07, cy - 0.3 + i * 0.03, 0.85),
            mat("DiceIvory", (0.9, 0.88, 0.8), 0.3),
            rot=(0, 0, random.uniform(0, 1)), bev=0.008)
    # miniatures on the map
    for i, (dx, dy, key) in enumerate([(-0.2, 0.1, "red"), (-0.1, 0.18, "blue"),
                                       (-0.15, -0.05, "green"), (0.2, -0.1, "darkwood")]):
        miniature.build(f"Mini{i}", (cx + dx, cy + dy, 0.83), color=M[key])
    # a dragon-ish mini: bigger red cone cluster
    cone("DragonMini", 0.06, 0.0, 0.12, (cx + 0.3, cy + 0.2, 0.89), M["red"], verts=6)
    for i, (dx, dy) in enumerate([(0.62, 0.1), (-0.4, 0.5)]):
        tankard.build(f"Tankard{i}", (cx + dx, cy + dy, 0.82))
    candle.build("TableCandleA", (cx - 0.05, cy - 0.55, 0.82), height=0.18)
    candle.build("TableCandleB", (cx + 0.1, cy - 0.6, 0.82), height=0.12)
    candle.build("TableCandleC", (cx - 0.6, cy + 0.05, 0.82), height=0.15)
    # chairs
    # (angle around table, distance, extra twist) - a couple pulled out / turned for life
    for i, (a, d, tw, cush) in enumerate([(160, 1.0, 0, "purple"), (235, 1.12, 15, None),
                                          (305, 1.05, -10, "blue"), (15, 1.0, 5, "green"),
                                          (90, 1.18, 20, None)]):
        r = math.radians(a)
        chair.build(f"Chair{i}", (cx + math.cos(r) * d, cy + math.sin(r) * d, 0.05),
                    r - math.radians(90) + math.radians(tw), cushion=cush)


def map_material():
    m = bpy.data.materials.new("MapMat")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.95
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # land vs sea via noise
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.5
    nz.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (0.55, 0.55, 0.45, 1)   # sea
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (0.82, 0.68, 0.45, 1)   # land
    e = ramp.color_ramp.elements.new(0.48)
    e.color = (0.25, 0.12, 0.06, 1)                              # coastline ink
    e2 = ramp.color_ramp.elements.new(0.62)
    e2.color = (0.62, 0.62, 0.38, 1)                             # forests
    # edge burn via gradient from center
    nt.links.new(tc.outputs["UV"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def build_bookshelf(M):
    x0, y = 0.5, ROOM - 0.25
    w = 1.3
    levels = [z + 0.05 for z in bookshelf.LEVELS]
    bookshelf.build("Bookshelf", (x0 + w / 2, y, 0.05), width=w, rng=random)
    # shelf 1 has potions & a scroll instead of some books
    z = levels[1]
    for i, key in enumerate(["glass_potion_g", "glass_potion_r", "glass_potion_b"]):
        sphere(f"ShelfPotion{i}", 0.06, (x0 + w - 0.3 + i * 0.1, y - 0.05, z + 0.08), M[key])
    # top shelf skull and scroll
    sphere("ShelfSkull", 0.08, (x0 + 0.3, y - 0.03, levels[-2] + 0.1), mat("Bone", (0.85, 0.8, 0.68), 0.6))
    cyl("ShelfScroll", 0.04, 0.4, (x0 + 0.8, y - 0.05, levels[-2] + 0.06), M["parchment"],
        rot=(0, math.radians(90), 0.2), verts=12)


def build_weapon_rack(M):
    # Rack against the right side of the back wall, beside the window
    x0, y = 2.35, ROOM - 0.2
    weapon_rack.build("Rack", (x0 + 0.45, y, 0.05))
    # swords point-down: tip sits in the slot block, hilt above the rail
    for nm, dx, ln in (("RackSwordA", 0.15, 1.0), ("RackSwordB", 0.35, 0.9)):
        s = sword.build(nm, (x0 + dx, y - 0.04, 0.2 + 0.76 * ln), length=ln)
        s.rotation_euler = (math.radians(180 - 3), 0, 0)
    # two staves leaning back on the rail
    for nm, dx, ln, kw in (("Staff", 0.6, 1.6, {}),
                           ("Staff2", 0.82, 1.5, {"head": "orb", "radius": 0.024, "wood": M["darkwood"]})):
        s = staff.build(nm, (x0 + dx, y - 0.1, 0.15), length=ln, **kw)
        s.rotation_euler = (math.radians(-5), 0, 0)
    # shield leaning against the rack, face tipped up a little
    sh = shield.build("LeanShield", color=M["red"])
    sh.rotation_euler = (math.radians(-15), 0, math.radians(-10))
    sh.location = Vector((x0 + 1.1, y - 0.15, 0.36)) - sh.rotation_euler.to_matrix() @ Vector((0, 0, 0.3))
    # bow hanging on the wall above
    bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.015,
                                     location=(1.6 + 0.05, ROOM - 0.08, 2.3),
                                     rotation=(math.radians(90), 0, 0))
    bow = bpy.context.object
    bow.name = "Bow"
    bow.scale = (0.35, 1, 1)
    assign(bow, M["wood"])
    # cut the torus in half with a boolean-free trick: just let the back half hide in the wall
    cyl("BowString", 0.003, 0.9, (1.65 - 0.0, ROOM - 0.08, 2.3), M["parchment"], verts=6)


def build_props(M):
    # Treasure chest front-right, lid open, with coins spilling out onto the floor
    cx, cy = 1.05, 0.42
    chest.build("Chest", (cx, cy, 0.05), math.radians(12), rng=random)
    for i in range(18):
        cyl(f"SpillCoin{i}", 0.03, 0.008,
            (cx + 0.55 + random.uniform(-0.2, 0.3), cy - 0.05 + random.uniform(-0.2, 0.2), 0.055),
            M["gold"], rot=(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), 0), verts=12)
    point_light("ChestGlow", (cx, cy - 0.1, 0.75), 8, (1.0, 0.75, 0.3), radius=0.1)

    build_alchemy_desk(M)

    rug.build("Rug", (2.3, 1.7, 0.05))

    banner.build("Banner", (0, 0.45, 2.3), math.radians(90))

    cx, cy = 2.3, 1.7
    # Floating candles spread through the room (no chandelier - this is a wizard house).
    # Jittered grid so they never bunch up; each candle hangs off an empty for bobbing.
    spots = [(0.7 + i * 0.95 + random.uniform(-0.2, 0.2), 0.7 + j * 0.95 + random.uniform(-0.2, 0.2))
             for i in range(4) for j in range(4)]
    random.shuffle(spots)
    for i, (x, y) in enumerate(spots[:12]):
        z = 1.9 + random.uniform(0, 0.75)
        rig = bpy.data.objects.new(f"FloatRig{i}", None)
        bpy.context.collection.objects.link(rig)
        candle.build(f"FloatCandle{i}", height=random.uniform(0.1, 0.2), light=(i % 3 == 0)).parent = rig
        rig.location = (x, y, z)
    point_light("FloatCandleLight", (cx, cy, 2.3), 30, (1.0, 0.65, 0.3), radius=0.6)


def build_magic(M):
    """Arcane touches for a wizard-heavy party."""
    # --- Summoning circle on the floor where the bedroll used to be
    mx, my = 0.72, 1.25
    summoning_circle.build("Circle", (mx, my, 0))

    # --- Crystal ball on a brass stand, and an open glowing spellbook on the table
    cx, cy = 2.3, 1.7
    crystal_ball.build("Orb", (cx - 0.5, cy - 0.35, 0.82))
    sx, sy = cx + 0.15, cy - 0.5
    open_book.build("Spellbook", (sx, sy, 0.835), math.radians(-15), cover=M["purple"])
    for k in range(5):
        sphere(f"SpellGlyph{k}", 0.012, (sx + random.uniform(-0.12, 0.12),
                                         sy + random.uniform(-0.1, 0.1), 0.92 + k * 0.05),
               M["arcane_cyan"], segs=6)

    # --- Floating books drifting off the bookshelf
    for k, (x, y, z, rz) in enumerate([(0.9, 3.05, 1.75, 0.4), (1.4, 3.0, 2.2, -0.3),
                                       (1.75, 3.15, 1.6, 0.9)]):
        rig = bpy.data.objects.new(f"FlyBookRig{k}", None)
        bpy.context.collection.objects.link(rig)
        open_book.build(f"FlyBook{k}", width=0.13, depth=0.18, thickness=0.012, angle=25,
                        cover=M["bookcols"][k]).parent = rig
        rig.location = (x, y, z)
        rig.rotation_euler = (0, 0, rz)
    point_light("FlyBookGlow", (1.35, 2.9, 1.9), 6, (0.4, 0.75, 1.0), radius=0.3)

    # --- Bubbling cauldron in the back-right
    cauldron.build("Cauldron", (3.55, 3.0, 0.05), rng=random)

    # --- Wizard hat set down on the table
    wizard_hat.build("WizardHat", (cx + 0.42, cy + 0.42, 0.83))

    # --- Floating arcane motes
    for k in range(45):
        if k < 20:
            a = random.uniform(0, 2 * math.pi)
            r = random.uniform(0.1, 0.6)
            loc = (mx + r * math.cos(a), my + r * math.sin(a), random.uniform(0.15, 1.6))
        else:
            loc = (random.uniform(0.3, 3.8), random.uniform(0.3, 3.7), random.uniform(1.0, 2.8))
        sphere(f"Mote{k}", random.uniform(0.006, 0.014), loc,
               random.choice([M["arcane_cyan"], M["arcane_purple"]]), segs=6)


def build_alchemy_desk(M):
    """Small alchemy desk against the left wall, under the banner."""
    x, y, h = 0.3, 0.45, 0.78
    desk.build("Desk", (x, y, 0), math.radians(90), height=h)
    # books and a crate on the low shelf
    for i in range(4):
        box(f"DeskShelfBook{i}", (0.25, 0.05, 0.2), (x + 0.02, y - 0.25 + i * 0.06, 0.32),
            M["bookcols"][i], rot=(0.08 * (i % 2), 0, 0), bev=0.004)
    box("DeskCrate", (0.3, 0.3, 0.2), (x, y + 0.2, 0.31), M["wood"], bev=0.01)
    t = h + 0.025
    alembic.build("Alembic", (x, y + 0.22, t))
    vial_rack.build("VialRack", (x + 0.08, y - 0.22, t), math.radians(90))
    mortar.build("Mortar", (x - 0.12, y - 0.05, t))
    # open scroll, skull candle
    box("DeskScroll", (0.2, 0.28, 0.004), (x - 0.06, y - 0.2, t), M["parchment"],
        rot=(0, 0, 0.3), bev=0)
    cyl("DeskScrollRoll", 0.02, 0.2, (x - 0.04, y - 0.33, t + 0.02), M["parchment"],
        rot=(0, math.radians(90), 0.3), verts=10)
    sphere("DeskSkull", 0.065, (x - 0.1, y + 0.3, t + 0.06), mat("Bone", (0.85, 0.8, 0.68), 0.6))
    candle.build("DeskCandle", (x - 0.1, y + 0.3, t + 0.11), height=0.08)
    point_light("AlembicGlow", (x + 0.15, y + 0.1, t + 0.25), 4, (0.6, 0.3, 1.0), radius=0.05)


def build_atmosphere():
    """Light haze inside the room so the window and the summoning circle cast visible beams."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(ROOM / 2, ROOM / 2, WALL_H / 2 + 0.03))
    vol = bpy.context.object
    vol.name = "Haze"
    vol.scale = (ROOM - 0.04, ROOM - 0.04, WALL_H - 0.06)
    m = bpy.data.materials.new("HazeMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.032
    pv.inputs["Anisotropy"].default_value = 0.35
    pv.inputs["Color"].default_value = (0.9, 0.85, 0.8, 1)
    nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
    assign(vol, m)
    vol.visible_shadow = False

    # moonlight shafting in through the window
    cx, z = 3.35, 1.95
    ld = bpy.data.lights.new("WindowBeam", "SPOT")
    ld.energy = 3000
    ld.color = (0.55, 0.7, 1.0)
    ld.spot_size = math.radians(34)
    ld.spot_blend = 0.35
    ld.shadow_soft_size = 0.05
    o = bpy.data.objects.new("WindowBeam", ld)
    o.location = (cx, ROOM - 0.12, z + 0.1)
    aim = Vector((2.9, 2.2, 0.05)) - o.location
    o.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(o)


# ---------------------------------------------------------------- animation

FPS = 24
FRAMES = 48           # 2 s loop; lib.keyframe defaults to the same fps and length


def animate():
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAMES
    obs = bpy.data.objects

    for o in obs:
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
            keyframe(o, "scale", lambda t, b=base, ph=ph:
                     (b.x, b.y, b.z * (1 + 0.15 * wave(t, 6, ph))))
        elif n.startswith(("FloatRig", "FlyBookRig")):
            base = o.location.copy()
            amp = 0.04 if n.startswith("FloatRig") else 0.06
            keyframe(o, "location", lambda t, b=base, ph=ph, a=amp:
                     (b.x, b.y, b.z + a * wave(t, 1, ph)))
            if n.startswith("FlyBookRig"):
                r0 = o.rotation_euler.copy()
                keyframe(o, "rotation_euler", lambda t, r=r0, ph=ph:
                         (r.x + 0.08 * wave(t, 1, ph + 1), r.y, r.z + 0.1 * wave(t, 1, ph)))
        elif n.startswith("Mote"):
            base = o.location.copy()
            keyframe(o, "location", lambda t, b=base, ph=ph:
                     (b.x + 0.03 * wave(t, 1, ph), b.y + 0.03 * wave(t, 1, ph + 2),
                      b.z + 0.06 * wave(t, 1, ph + 4)))
        elif "Bubble" in n or n.startswith("SpellGlyph"):
            base = o.location.copy()
            span = 0.35 if "Bubble" in n else 0.25
            off = rnd.random()
            keyframe(o, "location", lambda t, b=base, s=span, off=off:
                     (b.x, b.y, b.z + s * ((t / 2 + off) % 1.0)))
        elif n == "CircleRings":
            keyframe(o, "rotation_euler", lambda t: (0, 0, math.radians(45) * t / 2))
        elif n == "CircleHex":
            keyframe(o, "rotation_euler", lambda t: (0, 0, -math.radians(60) * t / 2))

    def pulse(name, depth, k, ph=0.0):
        ld = obs[name].data
        base = ld.energy
        keyframe(None, "energy", lambda t: base * (1 + depth * wave(t, k, ph)), target=ld)

    pulse("FireplaceLight", 0.15, 5)
    pulse("CircleBeam", 0.2, 2)
    pulse("CircleLight", 0.25, 2)
    pulse("OrbLight", 0.35, 1)
    pulse("CauldronGlow", 0.2, 3)


# ---------------------------------------------------------------- scene setup

def setup_world_and_camera(samples, shot="wide"):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.012, 0.012, 0.02, 1)
    bg.inputs["Strength"].default_value = 1.0

    # soft fill so shadows aren't pitch black
    ld = bpy.data.lights.new("Fill", "AREA")
    ld.energy = 35
    ld.size = 4
    ld.color = (0.75, 0.75, 1.0)
    fill = bpy.data.objects.new("Fill", ld)
    fill.location = (6, -3, 5)
    fill.rotation_euler = (math.radians(55), 0, math.radians(60))
    scene.collection.objects.link(fill)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 35
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    if shot == "close":
        # eye-level view across the table toward the fireplace and summoning circle
        cam_data.lens = 30
        cam.location = (4.3, -0.4, 1.75)
        target = Vector((1.5, 2.0, 0.95))
    else:
        cam.location = (7.6, -4.2, 4.6)
        target = Vector((1.8, 2.0, 1.1))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    if shot == "top":
        # orthographic plan view straight down onto the diorama
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ROOM + 0.9
        cam_data.clip_end = 50
        cam.location = (ROOM / 2 - 0.1, ROOM / 2 + 0.05, 12)
        cam.rotation_euler = (0, 0, 0)
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.volume_bounces = 0
    scene.cycles.volume_step_rate = 4.0
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    if shot == "top":
        scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = None
    samples = 64
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
    M = palette()
    build_room(M)
    build_window(M)
    build_fireplace(M)
    build_table(M)
    build_bookshelf(M)
    build_weapon_rack(M)
    build_props(M)
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
