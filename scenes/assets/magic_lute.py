"""Magic lute: a pear-shaped body of alternating light and dark staves, spruce
soundboard with gold purfling, a glowing rune rosette, glowing strings, a
bent-back pegbox capped with a crystal, and a few glowing notes drifting beside it.

    lute = magic_lute.build("Lute", loc=(1, 2, 0.8))
    lute.rotation_euler = (math.radians(-70), 0, 0)   # lay it on its back on a table

Origin is under the bottom of the body; the neck points up along local +z and
the soundboard faces -y.
"""
import math

from mathutils import Vector

from assets.lib import Batch, as_material, box, curve, cyl, group, lathe, mat, material, mesh_obj, \
    noisy_mat, point_light, sphere, torus


def half_width(t, wide, neck):
    """Half width of the body outline at t = 0 (bottom) .. 1 (neck joint)."""
    if t < 0.36:
        return wide * math.sqrt(max(0.0, 1 - ((0.36 - t) / 0.36) ** 2))
    return neck + (wide - neck) * math.cos(math.pi / 2 * (t - 0.36) / 0.64) ** 1.4


def rod(name, a, b, r, material, verts=6):
    """Thin cylinder from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    return cyl(name, r, d.length, (a + b) / 2, material,
               rot=d.to_track_quat("Z", "Y").to_euler(), verts=verts, smooth=False)


def build(name="Lute", loc=(0, 0, 0), rot_z=0.0, *, body=0.48, width=0.34, glow="lute_glow",
          staves=("wood", "darkwood"), notes=3, light=True):
    """body: length of the body; width: its widest point. glow: material, palette key or
    (r, g, b) for the strings, rosette and notes ("lute_glow" is this asset's own soft cyan). staves: the two alternating back woods.
    notes: how many glowing notes float beside the body."""
    if glow == "lute_glow":
        glow = mat("LuteGlow", (0.5, 0.85, 1.0), 0.2, emit=(0.3, 0.75, 1.0), emit_strength=4)
    glow = as_material(glow, name + "Glow", 0.2)
    light_wood = as_material(staves[0], name + "StaveA", 0.6)
    dark_wood = as_material(staves[1], name + "StaveB", 0.6)
    spruce = noisy_mat("Spruce", (0.38, 0.23, 0.09), (0.55, 0.36, 0.16), 5, 0.5, stretch=(14, 1, 1), bump=0.05)
    gold = material("gold")
    ebony = material("darkwood")
    W, N, L = width / 2, 0.026, body
    parts = []

    # bowl: staves of a half-pear, alternating woods
    slices, count = 40, 11
    ts = [(1 - math.cos(math.pi * i / slices)) / 2 for i in range(slices + 1)]   # denser at both ends
    for parity, wood in ((0, light_wood), (1, dark_wood)):
        verts, faces = [], []
        for j in range(parity, count, 2):
            base = len(verts)
            for t in ts:
                w = half_width(t, W, N)
                d = w * (0.95 - 0.25 * t)
                for th in (math.pi * j / count, math.pi * (j + 1) / count):
                    verts.append((w * math.cos(th), d * math.sin(th), t * L))
            for i in range(slices):
                a = base + 2 * i
                faces.append((a, a + 2, a + 3, a + 1))
        parts.append(mesh_obj(f"{name}Bowl{parity}", verts, faces, wood, smooth_angle=60))

    # soundboard: a thin slab over the open face, gold purfling around its edge
    outline = [(half_width(t, W, N), t * L) for t in ts]
    outline = outline + [(-x, z) for x, z in reversed(outline[1:-1])]
    n = len(outline)
    sb = -0.006
    verts = [(x, y, z) for y in (sb, 0.0) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    parts.append(mesh_obj(name + "Soundboard", verts, faces, spruce, smooth_angle=0))
    rim = [(x * 0.94, sb - 0.001, z * 0.97 + 0.012) for x, z in outline]
    parts.append(curve(name + "Purfling", rim, 0.0025, gold, cyclic=True))

    # rosette: a dark sound hole with a glowing rune star, ringed in gold
    rz, rr = 0.62 * L, 0.052
    up = (math.radians(90), 0, 0)
    parts.append(cyl(name + "SoundHole", rr, 0.002, (0, sb - 0.001, rz), material("iron"), rot=up, verts=40))
    parts.append(torus(name + "RoseRing", rr + 0.004, 0.0035, (0, sb - 0.002, rz), gold, rot=up,
                       major_segments=48, minor_segments=8))
    parts.append(torus(name + "RoseRune", rr * 0.82, 0.0016, (0, sb - 0.003, rz), glow, rot=up,
                       major_segments=48, minor_segments=6))
    star = Batch()
    for k in range(6):                  # hexagram: two triangles of glowing bars
        a = math.pi / 2 + k * math.pi / 3
        p = Vector((rr * 0.78 * math.cos(a), 0, rr * 0.78 * math.sin(a)))
        q = Vector((rr * 0.78 * math.cos(a + 2 * math.pi / 3), 0, rr * 0.78 * math.sin(a + 2 * math.pi / 3)))
        mid, d = (p + q) / 2, q - p
        star.box(glow, (d.length, 0.002, 0.003), (mid.x, sb - 0.003, rz + mid.z), ry=-math.atan2(d.z, d.x))
    for k in range(12):                 # rune dots between the rings
        a = k * math.pi / 6 + math.pi / 12
        star.ball(glow, 0.0035, ((rr + 0.016) * math.cos(a), sb - 0.002, rz + (rr + 0.016) * math.sin(a)))
    parts += star.build(name + "Rose")

    # bridge low on the soundboard
    zb = 0.2 * L
    parts.append(box(name + "Bridge", (0.15, 0.01, 0.012), (0, sb - 0.005, zb), ebony, bev=0.003))

    # neck and fingerboard with gold frets
    zj, nl = L - 0.01, 0.3
    zn = zj + nl
    parts.append(box(name + "Neck", (0.054, 0.034, nl + 0.01), (0, 0.011, zj + nl / 2), dark_wood, bev=0.006))
    parts.append(box(name + "Fingerboard", (0.056, 0.004, nl + 0.04), (0, sb - 0.002, zj + nl / 2 - 0.02),
                     ebony, bev=0.0015))
    parts.append(box(name + "Nut", (0.056, 0.006, 0.006), (0, sb - 0.005, zn), material("parchment"), bev=0.001))
    scale = zn - zb
    frets = Batch()
    for k in range(1, 9):
        frets.box(gold, (0.056, 0.002, 0.0018), (0, sb - 0.0045, zn - scale * (1 - 2 ** (-k / 12))))
    parts += frets.build(name + "Frets")

    # pegbox bent back behind the neck, pegs through its cheeks, a crystal at its end
    bend = math.radians(68)
    axis = Vector((0, math.sin(bend), math.cos(bend)))
    side = Vector((1, 0, 0))
    root = Vector((0, 0.005, zn + 0.006))
    pl = 0.17
    parts.append(box(name + "Pegbox", (0.046, 0.026, pl), root + axis * pl / 2, dark_wood,
                     rot=(-bend, 0, 0), bev=0.005))
    pegs = []
    for k in range(6):
        p = root + axis * (0.025 + k * 0.024)
        s = 1 if k % 2 else -1
        pegs.append(p)
        parts.append(rod(f"{name}Peg{k}", p - side * 0.03 * s, p + side * 0.045 * s, 0.0035, ebony, verts=8))
        parts.append(sphere(f"{name}PegKnob{k}", 0.008, p + side * 0.05 * s, ebony, scale=(0.6, 1, 1.3), segs=10))
    tip = root + axis * (pl + 0.01)
    parts.append(lathe(name + "Finial", [(0.0, 0.0), (0.016, 0.0), (0.012, 0.012), (0.0, 0.016)],
                       tip, gold, segs=16, rot=(-bend, 0, 0)))
    gem = mat("LuteGem", (0.25, 0.5, 1.0), 0.05, emit=(0.12, 0.42, 1.0), emit_strength=5)
    parts.append(lathe(name + "Gem", [(0.0, 0.0), (0.012, 0.012), (0.009, 0.03), (0.0, 0.05)],
                       tip + axis * 0.014, gem, segs=6, rot=(-bend, 0, 0)))

    # strings: bridge to nut, then over the nut down into the pegbox
    for k in range(6):
        f = k / 5 - 0.5
        a = (f * 0.11, sb - 0.012, zb)
        b = (f * 0.042, sb - 0.008, zn)
        parts.append(rod(f"{name}String{k}", a, b, 0.0009, glow))
        parts.append(rod(f"{name}Tail{k}", b, pegs[k] + Vector((f * 0.03, 0, 0)), 0.0009, glow))

    # glowing notes drifting up beside the body
    spots = [(0.24, -0.04, 0.5), (0.32, -0.02, 0.7), (-0.25, -0.03, 0.62),
             (0.2, -0.05, 0.86), (-0.3, -0.02, 0.38)]
    marks = Batch()
    for k, (x, y, z) in enumerate(spots[:notes]):
        parts.append(sphere(f"{name}NoteHead{k}", 0.016, (x, y, z), glow, scale=(1.35, 0.5, 0.95), segs=16))
        parts[-1].rotation_euler = (0, -0.4, 0)
        sx = x + 0.019
        marks.box(glow, (0.0045, 0.0045, 0.075), (sx, y, z + 0.037))
        marks.box(glow, (0.028, 0.0045, 0.009), (sx + 0.011, y, z + 0.062), ry=0.75)
    if notes:
        parts += marks.build(name + "Notes")
    if light:
        parts.append(point_light(name + "Light", (0, -0.12, rz), 4, (0.4, 0.8, 1.0), radius=0.08))
    return group(name, parts, loc, rot_z)
