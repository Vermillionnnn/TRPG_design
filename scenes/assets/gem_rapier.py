"""Slender rapier with a clear crystal blade full of coloured sparks and a gilded hilt,
after the designer's reference art and a front-view sketch fitted over it. The blade rises
from a faceted vase-and-lozenge crystal set in a thin gold ring on a heavy guard: a narrow
flat top whose sides bulge out to a sharp round rim, then a frustum narrowing straight into
the grip. The grip is wire-wrapped at the top, channelled lengthwise below, fullest a little
below the wraps and tapering down
to the pommel: a fluted gold knob belted with sapphires above a gold cage round a crystal drop. The knuckle bow is a flat band whose upper edge carries on the guard's
curve; it swings far out, slants back in, thinning, then widens again to meet the grip's
lower part and winds into a tightening spiral.

    r = gem_rapier.build("Rapier", loc=(0, 0, 2.31))
    r.rotation_euler = (math.radians(180), 0, 0)   # point down, e.g. hung on a wall

Origin is at the pommel tip; the blade points up along local +z, flat side facing -y.
"""
import math
import random

import bpy

from mathutils import Vector

from assets.lib import ICO_F, ICO_V, Batch, as_material, curve, group, lathe, mat, mesh_obj, point_light, \
    sphere, torus


def glass_mat(name, tint):
    """Clear, nearly colourless crystal: full transmission, thin-film iridescence and dispersion."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    inputs = m.node_tree.nodes["Principled BSDF"].inputs
    inputs["Base Color"].default_value = (*tint, 1)
    inputs["Roughness"].default_value = 0.02
    inputs["Transmission Weight"].default_value = 1.0
    inputs["IOR"].default_value = 1.6
    for key, value in (("Thin Film Thickness", 400.0), ("Thin Film IOR", 1.4), ("Dispersion", 0.5)):
        if key in inputs:
            inputs[key].default_value = value
    return m


def prism(name, sections, material, tip=None, bottom=None):
    """Faceted bar along z with a flattened-hexagon cross-section.
    sections: (z, half_width, half_thickness) bottom to top; tip / bottom: z of a closing point."""
    ring = [(1, 0), (0.5, 1), (-0.5, 1), (-1, 0), (-0.5, -1), (0.5, -1)]
    verts, faces = [], []
    for z, w, t in sections:
        verts += [(w * a, t * b, z) for a, b in ring]
    n = len(ring)
    for s in range(len(sections) - 1):
        for i in range(n):
            j = (i + 1) % n
            faces.append((s * n + i, s * n + j, (s + 1) * n + j, (s + 1) * n + i))
    top = (len(sections) - 1) * n
    if tip is None:
        faces.append(tuple(top + i for i in range(n)))
    else:
        verts.append((0, 0, tip))
        faces += [(top + i, top + (i + 1) % n, len(verts) - 1) for i in range(n)]
    if bottom is None:
        faces.append(tuple(reversed(range(n))))
    else:
        verts.append((0, 0, bottom))
        faces += [((i + 1) % n, i, len(verts) - 1) for i in range(n)]
    return mesh_obj(name, verts, faces, material, smooth_angle=0)


def sparks(sections, tip, count, rng, inner=(0.4, 0.25)):
    """Positions of `count` sparks inside a prism given as for prism(), masked to an inner
    elliptical core (`inner` = fractions of the half width / half thickness) so that none
    sits against the glass."""
    pts = sections + [(tip, 0.0, 0.0)]
    z0, z1 = pts[0][0], tip
    out = []
    for _ in range(count):
        z = rng.uniform(z0, z1 - (z1 - z0) * 0.04)
        for (za, wa, ta), (zb, wb, tb) in zip(pts, pts[1:]):
            if za <= z <= zb:
                f = (z - za) / (zb - za)
                w, t = wa + (wb - wa) * f, ta + (tb - ta) * f
                break
        a, r = rng.uniform(0, 2 * math.pi), rng.random() ** 0.5
        out.append((r * math.cos(a) * inner[0] * w, r * math.sin(a) * inner[1] * t, z))
    return out


def icosphere(subdiv=2):
    """Unit icosphere: (verts as Vectors, triangle faces)."""
    verts = [Vector(v).normalized() for v in ICO_V]
    faces = list(ICO_F)
    for _ in range(subdiv):
        cache, split = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                cache[key] = len(verts)
                verts.append(((verts[a] + verts[b]) / 2).normalized())
            return cache[key]
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            split += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = split
    return verts, faces


def halo_mat(name, color, strength, spread=4.5):
    """Soft additive glow on a ball-normal shell. Brightness falls off like a Gaussian from the
    centre, exp(-spread * rho^2), shifted so it reaches exactly nothing at the rim; with spread
    4.5 it is a third of the peak halfway out. It only adds light, so the shell never hides
    what is behind it."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    L = nt.links.new

    def op(kind, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = kind
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            elif v is not None:
                L(v, n.inputs[i])
        return n.outputs["Value"]

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")      # cos of the angle to the view = sqrt(1 - rho^2)
    dot.operation = "DOT_PRODUCT"
    L(geo.outputs["Normal"], dot.inputs[0])
    L(geo.outputs["Incoming"], dot.inputs[1])
    cos = op("ABSOLUTE", dot.outputs["Value"])
    rho2 = op("SUBTRACT", 1.0, op("MULTIPLY", cos, cos))   # squared distance from the centre, as seen
    floor = math.exp(-spread)
    glow = op("EXPONENT", op("MULTIPLY", rho2, -spread))
    amount = op("MULTIPLY", op("MAXIMUM", op("SUBTRACT", glow, floor), 0.0), strength / (1 - floor))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    L(amount, em.inputs["Strength"])
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    L(clear.outputs["BSDF"], add.inputs[0])
    L(em.outputs["Emission"], add.inputs[1])
    L(add.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    return m


def glow_points(name, points, colors, size, rng, halo_share=0.35):
    """A small saturated core at each point, and around about `halo_share` of them a wide,
    flattened soft halo (all of them would melt into one haze); merged into one mesh per colour
    for the cores and one per colour for the halos. The halos are see-through shells, so a
    scene showing them needs plenty of transparent bounces (rapier_scene.py uses 64)."""
    cores = [mat(f"Spark{k}", c, 0.5, emit=c, emit_strength=2.5) for k, c in enumerate(colors)]
    halos = [halo_mat(f"SparkHalo{k}", c, 0.45) for k, c in enumerate(colors)]
    hv, hf = icosphere(2)
    batch, shells = Batch(), {}
    for x, y, z in points:
        k = rng.randrange(len(colors))
        s = size * rng.uniform(0.6, 1.2)
        batch.ball(cores[k], s * 0.4, (x, y, z))
        if rng.random() > halo_share:
            continue
        verts, faces = shells.setdefault(k, ([], []))
        o = len(verts)
        verts += [(x + v.x * s * 7.2, y + v.y * s * 1.2, z + v.z * s * 7.2) for v in hv]
        faces += [tuple(o + i for i in f) for f in hf]
    objs = batch.build(name + "Core", smooth=True)
    for k, (verts, faces) in shells.items():
        # flattened shells, but with the normals of a round ball, so the glow fades evenly
        # from the centre to the rim instead of staying flat across a squashed face
        me = bpy.data.meshes.new(f"{name}Halo{k}")
        me.from_pydata(verts, [], faces)
        me.shade_smooth()
        me.normals_split_custom_set_from_vertices([tuple(v) for _ in range(len(verts) // len(hv)) for v in hv])
        o = bpy.data.objects.new(me.name, me)
        bpy.context.collection.objects.link(o)
        me.materials.append(halos[k])
        objs.append(o)
    return objs


# ---------------------------------------------------------------- hilt, front view in mm
# Drawn in the x-z plane with y measured DOWN from the guard top (as in the sketch fitted over
# the reference); build() turns these into metres.

TOP, RIM, RIM_Y = 34.0, 71.0, 18.5      # guard: flat-top half width, rim half width, rim depth
GUARD_Y = 41.0                          # guard bottom, where it meets the grip
EXP = 1.54                              # how much the guard's upper sides bulge
K = RIM_Y / (RIM - TOP) ** EXP
# grip radius by depth: right under the guard, swelling a little below it, tapering to the pommel
GRIP = [(GUARD_Y, 15), (60, 19), (95, 22.5), (130, 23), (180, 21), (250, 18), (320, 15), (376, 13)]
WRAPS = (48, 54, 60, 66)                # wire wraps at the top of the grip
POMMEL_Y = 376.0                        # top of the pommel cuff
HILT = 497.0                            # guard top to pommel tip


def guard_profile(x):
    """Depth of the guard's upper surface at |x| (and, past the rim, the bow's upper edge) and its slope."""
    t = max(0.0, x - TOP)
    return K * t ** EXP, K * EXP * t ** (EXP - 1)


def grip_radius(y):
    for (y0, r0), (y1, r1) in zip(GRIP, GRIP[1:]):
        if y0 <= y <= y1:
            return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    return GRIP[-1][1]


def catmull(pts, res=12):
    """Smooth path through pts (Catmull-Rom), res samples per span."""
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = ext[i:i + 4]
        for k in range(res):
            t = k / res
            out.append(tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    return out + [pts[-1]]


def smooth(f):
    f = min(1.0, max(0.0, f))
    return f * f * (3 - 2 * f)


def bow_path():
    """Centreline of the knuckle bow and its half width at each sample, in mm."""
    w0 = 8.5                            # half width where the bow leaves the guard

    def inside(x):                      # w0 below the guard curve, so the band's upper edge runs along it
        y, sl = guard_profile(x)
        nl = math.hypot(sl, 1)
        return (x - sl / nl * w0, y + w0 / nl)

    centre, r0, r1, turn = (44, 347), 24.5, 4.0, 450   # spiral: centre, start / end radius, degrees
    spiral = []
    for k in range(0, turn + 1, 30):
        a = math.radians(180 - k)       # start beside the grip, wind down, right, up, ...
        r = r0 * (r1 / r0) ** (k / turn)
        spiral.append((centre[0] + r * math.cos(a), centre[1] + r * math.sin(a)))
    pts = [inside(48), inside(58), inside(68), inside(82), (97, 62), (110, 95), (114, 120), (111, 145),
           (103, 172), (91, 200), (76, 232), (59, 264), (41.5, 293), (29, 316), (21.5, 333)] + spiral
    path = catmull(pts)
    length = [0.0]
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        length.append(length[-1] + math.hypot(xb - xa, yb - ya))
    s_guard = length[4 * 12]            # end of the stretch along the guard curve
    s_thin = length[min(range(len(path)), key=lambda i: math.dist(path[i], (69, 245)))]
    s_join = length[15 * 12]            # where the band meets the grip and the spiral begins
    thin, join, end = 2.6, 6.44, 3.6

    def half_width(s):
        if s < s_thin:
            return w0 + (thin - w0) * smooth((s - s_guard) / (s_thin - s_guard))
        if s < s_join:
            return thin + (join - thin) * smooth((s - s_thin) / (s_join - s_thin))
        return end + (join - end) * math.exp(-(s - s_join) / 22)

    return path, [half_width(s) for s in length]


def band(name, path, breadth, thick, top, material, ring=16):
    """Flat band swept along `path` (mm, front view, y down from `top` in metres). Its cross-section
    is an ellipse, breadth[i] across the path in the front plane and thick[i] in depth (half sizes, mm)."""
    verts, faces = [], []
    for i, (x, y) in enumerate(path):
        xa, ya = path[max(i - 1, 0)]
        xb, yb = path[min(i + 1, len(path) - 1)]
        tl = math.hypot(xb - xa, yb - ya) or 1
        nx, ny = (yb - ya) / tl, -(xb - xa) / tl     # in-plane normal to the path
        a, b = breadth[i], thick[i]
        for k in range(ring):
            c, sn = math.cos(2 * math.pi * k / ring), math.sin(2 * math.pi * k / ring)
            verts.append(((x + nx * a * c) / 1000, b * sn / 1000, top - (y + ny * a * c) / 1000))
    for i in range(len(path) - 1):
        for k in range(ring):
            j = (k + 1) % ring
            faces.append((i * ring + k, i * ring + j, (i + 1) * ring + j, (i + 1) * ring + k))
    faces += [tuple(reversed(range(ring))), tuple((len(path) - 1) * ring + k for k in range(ring))]
    return mesh_obj(name, verts, faces, material, smooth_angle=70)


def turned(name, profile, top, material, segs=64, rot=(0, 0, 0)):
    """lathe() from a (radius, depth) profile in mm listed top to bottom, depth measured down from `top`."""
    return lathe(name, [(r / 1000, top - y / 1000) for r, y in reversed(profile)], (0, 0, 0), material,
                 segs=segs, rot=rot)


def grooved_grip(name, profile, top, material, grooves=8, y0=76.0, y1=366.0, half=1.6, depth=1.2,
                 segs=192, step=2.0):
    """The grip: turned from a (radius, depth) profile in mm listed top to bottom, with `grooves`
    rounded lengthwise channels (half width `half`, `depth` deep, in mm) cut between depths y0 and
    y1, fading in and out at their ends. The channels sit between the knuckle bow's plane and
    its neighbours, so none runs under the bow where it meets the grip."""
    ys, rs = [y for _, y in profile], [r for r, _ in profile]

    def radius(y):
        for k in range(len(ys) - 1):
            if ys[k] <= y <= ys[k + 1]:
                return rs[k] + (rs[k + 1] - rs[k]) * (y - ys[k]) / (ys[k + 1] - ys[k])
        return rs[-1]

    rows = [ys[0] + step * k for k in range(int((ys[-1] - ys[0]) / step) + 1)]
    pitch = 2 * math.pi / grooves
    verts = [(0, 0, top - (ys[0] - 0.5) / 1000)]
    for y in rows:
        r0 = radius(y)
        fade = smooth((y - y0) / 12) * smooth((y1 - y) / 12)
        for i in range(segs):
            a = 2 * math.pi * i / segs
            d = abs(((a - pitch / 2) % pitch) - pitch / 2) * r0       # arc distance to the nearest channel
            cut = depth * fade * max(0.0, 1 - (d / half) ** 2) ** 0.5   # round-bottomed channel
            r = r0 - cut
            verts.append((r * math.cos(a) / 1000, r * math.sin(a) / 1000, top - y / 1000))
    verts.append((0, 0, top - (ys[-1] + 0.5) / 1000))
    faces = [(0, 1 + (i + 1) % segs, 1 + i) for i in range(segs)]
    for k in range(len(rows) - 1):
        o = 1 + k * segs
        faces += [(o + i, o + segs + i, o + segs + (i + 1) % segs, o + (i + 1) % segs) for i in range(segs)]
    last = 1 + (len(rows) - 1) * segs
    faces += [(last + (i + 1) % segs, last + i, len(verts) - 1) for i in range(segs)]
    return mesh_obj(name, verts, faces, material, smooth_angle=50)


def fluted(name, profile, top, material, flutes=12, depth=0.1, segs=96):
    """turned(), its surface grooved lengthwise by `flutes` rounded flutes."""
    verts, faces = [], []
    n = len(profile)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        k = 1 - depth * (0.5 + 0.5 * math.cos(flutes * a))
        verts += [(r * k * math.cos(a) / 1000, r * k * math.sin(a) / 1000, top - y / 1000) for r, y in profile]
    for i in range(segs):
        j = (i + 1) % segs
        for p in range(n - 1):
            faces.append((i * n + p, j * n + p, j * n + p + 1, i * n + p + 1))
    faces += [tuple(i * n for i in range(segs)), tuple(i * n + n - 1 for i in reversed(range(segs)))]
    return mesh_obj(name, verts, faces, material, smooth_angle=60)


def faceted(name, profile, top, material, segs=8):
    """turned() with flat facets: a cut stone. The profile must start and end on the axis."""
    verts = [(0, 0, top - profile[0][1] / 1000)]
    rings = profile[1:-1]
    for r, y in rings:
        verts += [(r * math.cos(2 * math.pi * i / segs) / 1000, r * math.sin(2 * math.pi * i / segs) / 1000,
                   top - y / 1000) for i in range(segs)]
    verts.append((0, 0, top - profile[-1][1] / 1000))
    faces = [(0, 1 + (i + 1) % segs, 1 + i) for i in range(segs)]
    for k in range(len(rings) - 1):
        o = 1 + k * segs
        faces += [(o + i, o + (i + 1) % segs, o + segs + (i + 1) % segs, o + segs + i) for i in range(segs)]
    last = 1 + (len(rings) - 1) * segs
    faces += [(last + i, last + (i + 1) % segs, len(verts) - 1) for i in range(segs)]
    return mesh_obj(name, verts, faces, material, smooth_angle=0)


def build(name="Rapier", loc=(0, 0, 0), rot_z=0.0, *, length=2.31, width=0.036, blade=(0.95, 0.97, 1.0),
          sparkle=((0.02, 0.12, 1.0), (0.0, 0.75, 1.0), (1.0, 0.04, 0.45), (1.0, 0.3, 0.0),
                   (0.08, 1.0, 0.12), (0.45, 0.05, 1.0)), sparks_count=None, hilt="gold", light=True, rng=None):
    """length: pommel tip to blade tip. width: blade width just above the crystal base.
    blade: glass tint (r, g, b) or a material. sparkle: colours of the glowing specks inside
    the crystal; sparks_count: how many (default about 230 per metre of blade). hilt: material, palette key or (r, g, b). rng: random source."""
    rng = rng or random.Random(5)
    hilt = as_material(hilt, name + "Hilt", 0.3)
    glass = blade if isinstance(blade, bpy.types.Material) else glass_mat(name + "Glass", blade)

    guard = HILT / 1000                  # top face of the guard
    g = guard + 0.003                    # top of the thin ring the crystal stands in
    c = width / 0.03                     # the crystal base grows with the blade
    base = g + 0.1 * c                   # where the crystal base gives way to the blade
    hw = width / 2
    parts = []

    # blade: narrowing steadily by about a third along its length, then a short triangular point
    ln = length - base
    point = width * 1.6
    blade_sec = [(base - 0.01, hw, hw * 0.38), (base + ln * 0.5, hw * 0.82, hw * 0.34),
                 (length - point, hw * 0.65, hw * 0.3)]
    parts.append(prism(name + "Blade", blade_sec, glass, tip=length))
    # crystal base: a vase flaring to sharp shoulders, a waist, then a lozenge running into the blade
    base_sec = [(g + dz * c, hw * w, hw * t) for dz, w, t in [
        (0, 0.65, 0.5), (0.014, 0.85, 0.6), (0.026, 1.6, 0.85), (0.031, 1.65, 0.85), (0.04, 0.75, 0.5),
        (0.046, 0.75, 0.5), (0.068, 1.25, 0.65), (0.094, 1.0, 0.42)]]
    parts.append(prism(name + "CrystalBase", base_sec, glass, tip=base + 0.01 * c))
    # coloured sparks deep inside both crystals, each a small saturated core in a soft halo
    # (saturated colours at a modest strength, so the tone mapping keeps them coloured, not white)
    count = sparks_count or round(230 * ln)
    pts = sparks(blade_sec, length, count, rng) + sparks(base_sec, base + 0.01 * c, 43, rng)
    parts += glow_points(name + "Sparks", pts, sparkle, 0.0018, rng)
    # the thin ring the crystal stands in
    parts.append(turned(name + "Ring", [(0, -3), (14.5 * c / 1.2, -3), (14.5 * c / 1.2, 1), (0, 1)], guard, hilt, segs=32))

    # guard: a narrow flat top whose sides bulge out to a sharp round rim (a narrow band, lightly
    # chamfered), then a frustum narrowing straight into the grip
    upper = [(TOP + (RIM - TOP) * k / 12, guard_profile(TOP + (RIM - TOP) * k / 12)[0]) for k in range(12)]
    parts.append(turned(name + "Guard", [(0, 0)] + upper + [(RIM - 0.3, RIM_Y - 0.6), (RIM, RIM_Y),
                                         (RIM - 0.3, RIM_Y + 0.6), (15.5, GUARD_Y), (0, GUARD_Y)],
                        guard, hilt, segs=96))

    # grip: one turned piece from the guard to the pommel, wire-wrapped at the top, with recessed
    # lengthwise channels below the wraps (offset half a pitch so the bow's join lands between two)
    prof = catmull([(r, y) for y, r in GRIP], res=4)
    grip_o = grooved_grip(name + "Grip", [(r, y) for r, y in prof], guard, hilt)
    grip_o.rotation_euler = (0, 0, math.pi / 8)
    parts.append(grip_o)
    for k, y in enumerate(WRAPS):
        parts.append(torus(f"{name}Wrap{k}", grip_radius(y) / 1000, 0.0012, (0, 0, guard - y / 1000), hilt,
                           major_segments=48, minor_segments=8))

    # knuckle bow: breadth from the sketch; its depth follows the breadth so it reads as a flat band
    path, breadth = bow_path()
    parts.append(band(name + "Bow", path, breadth, [min(5.5, max(3.0, 0.75 * w)) for w in breadth], guard, hilt))

    # pommel, the counterweight: a beaded collar, a fluted pear-shaped knob with a belt of small
    # sapphires round its widest part, then a calyx whose prongs make a cage round a crystal drop
    # (the blade's glass and sparks) and close on a turned finial at the tip
    P = POMMEL_Y
    parts.append(turned(name + "PommelCollar", [(0, P - 1), (14.5, P - 1), (16.5, P + 1.5), (14.5, P + 4),
                                                (16.5, P + 6.5), (15, P + 9), (0, P + 9)], guard, hilt, segs=48))
    parts.append(fluted(name + "PommelKnob", [(0, P + 8), (14, P + 8), (17, P + 14), (21, P + 22), (23.5, P + 31),
                                              (22.5, P + 39), (18, P + 46), (13, P + 52), (0, P + 52)], guard, hilt))
    belt = P + 31
    parts.append(turned(name + "PommelBelt", [(0, belt - 4), (23.8, belt - 4), (24.6, belt - 2.5), (24.6, belt + 2.5),
                                              (23.8, belt + 4), (0, belt + 4)], guard, hilt, segs=64))
    sapphire = mat("Sapphire", (0.05, 0.12, 0.8), 0.05, emit=(0.1, 0.25, 1.0), emit_strength=1.0)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        c, sn = math.cos(a), math.sin(a)
        z = guard - belt / 1000
        gem_o = sphere(f"{name}PommelGem{k}", 0.0028, (0.0252 * c, 0.0252 * sn, z), sapphire,
                       scale=(0.6, 1, 1), segs=16)
        gem_o.rotation_euler = (0, 0, a)
        parts.append(gem_o)
        parts.append(torus(f"{name}PommelBezel{k}", 0.0031, 0.0008, (0.0249 * c, 0.0249 * sn, z), hilt,
                           rot=(math.pi / 2, 0, a + math.pi / 2), major_segments=24, minor_segments=6))
    cal = P + 51
    parts.append(turned(name + "PommelCalyx", [(0, cal), (13.5, cal), (15.5, cal + 3), (14, cal + 6),
                                               (9, cal + 8), (0, cal + 8)], guard, hilt, segs=48))
    drop = [(0, cal + 5), (8, cal + 6), (11.5, cal + 15), (10.5, cal + 24), (0, cal + 52)]
    parts.append(faceted(name + "PommelCrystal", drop, guard, glass, segs=8))
    tip = cal + 51                       # the finial the prongs close on
    for k in range(6):
        a = k * math.pi / 3
        c, sn = math.cos(a), math.sin(a)
        ring = [(14.5, cal + 5), (14.2, cal + 14), (12.6, cal + 25), (9, cal + 38), (5, tip - 1)]
        parts.append(curve(f"{name}PommelProng{k}", [(r * c / 1000, r * sn / 1000, guard - y / 1000) for r, y in ring],
                           0.0017, hilt, taper=0.7))
    parts.append(turned(name + "PommelFinial", [(0, tip - 3), (5, tip - 2), (7, tip + 2), (5.5, tip + 6),
                                                (2.6, tip + 8.5), (3.8, tip + 10.5), (2.4, tip + 13), (0, HILT)],
                        guard, hilt, segs=32))
    drop_pts = []                        # a few sparks deep inside the drop too
    for _ in range(24):
        y = rng.uniform(cal + 10, cal + 34)
        r = 4.5 * (1 - max(0.0, y - cal - 18) / 24) * rng.random() ** 0.5
        a = rng.uniform(0, 2 * math.pi)
        drop_pts.append((r * math.cos(a) / 1000, r * math.sin(a) / 1000, guard - y / 1000))
    parts += glow_points(name + "PommelSparks", drop_pts, sparkle, 0.0013, rng)

    if light:
        parts.append(point_light(name + "Light", (0, -0.08, base + ln * 0.3), 3, (0.5, 0.6, 1.0), radius=0.1))
    return group(name, parts, loc, rot_z)
