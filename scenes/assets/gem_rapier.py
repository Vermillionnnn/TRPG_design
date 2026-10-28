"""Slender rapier with a clear crystal blade full of coloured sparks and a gilded hilt,
after the designer's reference art and a front-view sketch fitted over it. The blade rises
from a faceted vase-and-lozenge crystal set in a thin gold ring on a heavy guard: a narrow
flat top whose sides bulge out to a sharp round rim, then a frustum narrowing straight into
the grip. The grip is wire-wrapped at the top, fullest a little below it and tapering down
to a faceted pommel. The knuckle bow is a flat band whose upper edge carries on the guard's
curve; it swings far out, slants back in, thinning, then widens again to meet the grip's
lower part and winds into a tightening spiral.

    r = gem_rapier.build("Rapier", loc=(0, 0, 1.37))
    r.rotation_euler = (math.radians(180), 0, 0)   # point down, e.g. hung on a wall

Origin is at the pommel tip; the blade points up along local +z, flat side facing -y.
"""
import math
import random

import bpy

from assets.lib import Batch, as_material, group, lathe, mat, mesh_obj, point_light, torus


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


def sparks(batch, sections, tip, materials, count, size, rng):
    """Scatter `count` tiny glowing balls inside a prism given as for prism()."""
    pts = sections + [(tip, 0.0, 0.0)]
    z0, z1 = pts[0][0], tip
    for _ in range(count):
        z = rng.uniform(z0, z1 - (z1 - z0) * 0.04)
        for (za, wa, ta), (zb, wb, tb) in zip(pts, pts[1:]):
            if za <= z <= zb:
                f = (z - za) / (zb - za)
                w, t = wa + (wb - wa) * f, ta + (tb - ta) * f
                break
        x, y = rng.uniform(-0.7, 0.7) * w, rng.uniform(-0.55, 0.55) * t
        batch.ball(rng.choice(materials), size * rng.uniform(0.5, 1.2), (x, y, z))


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


def build(name="Rapier", loc=(0, 0, 0), rot_z=0.0, *, length=1.37, width=0.03, blade=(0.95, 0.97, 1.0),
          sparkle=((0.2, 0.45, 1.0), (0.3, 0.9, 1.0), (1.0, 0.35, 0.7), (1.0, 0.55, 0.15),
                   (0.4, 1.0, 0.45), (0.65, 0.35, 1.0)), sparks_count=260, hilt="gold", light=True, rng=None):
    """length: pommel tip to blade tip. width: blade width just above the crystal base.
    blade: glass tint (r, g, b) or a material. sparkle: colours of the glowing specks inside
    the crystal; sparks_count: how many. hilt: material, palette key or (r, g, b). rng: random source."""
    rng = rng or random.Random(5)
    hilt = as_material(hilt, name + "Hilt", 0.3)
    glass = blade if isinstance(blade, bpy.types.Material) else glass_mat(name + "Glass", blade)
    specks = [mat(f"Spark{k}", c, 0.5, emit=c, emit_strength=4) for k, c in enumerate(sparkle)]

    guard = HILT / 1000                  # top face of the guard
    g = guard + 0.003                    # top of the thin ring the crystal stands in
    base = g + 0.1                       # where the crystal base gives way to the blade
    hw = width / 2
    parts = []

    # blade: straight, narrowing steadily from the crystal base to the point
    ln = length - base
    blade_sec = [(base - 0.01, hw, hw * 0.38), (base + ln * 0.6, hw * 0.8, hw * 0.32),
                 (base + ln * 0.9, hw * 0.45, hw * 0.24)]
    parts.append(prism(name + "Blade", blade_sec, glass, tip=length))
    # crystal base: a vase flaring to sharp shoulders, a waist, then a lozenge running into the blade
    base_sec = [(g, hw * 0.65, hw * 0.5), (g + 0.014, hw * 0.85, hw * 0.6), (g + 0.026, hw * 1.6, hw * 0.85),
                (g + 0.031, hw * 1.65, hw * 0.85), (g + 0.04, hw * 0.75, hw * 0.5), (g + 0.046, hw * 0.75, hw * 0.5),
                (g + 0.068, hw * 1.25, hw * 0.65), (base - 0.006, hw * 1.0, hw * 0.42)]
    parts.append(prism(name + "CrystalBase", base_sec, glass, tip=base + 0.01))
    # coloured sparks scattered through both crystals, a little denser in the base
    glints = Batch()
    sparks(glints, blade_sec, length, specks, sparks_count, 0.0018, rng)
    sparks(glints, base_sec, base + 0.01, specks, sparks_count // 6, 0.0018, rng)
    parts += glints.build(name + "Sparks", smooth=True)
    # the thin ring the crystal stands in
    parts.append(turned(name + "Ring", [(0, -3), (13.5, -3), (13.5, 1), (0, 1)], guard, hilt, segs=32))

    # guard: a narrow flat top whose sides bulge out to a sharp round rim (a narrow band, lightly
    # chamfered), then a frustum narrowing straight into the grip
    upper = [(TOP + (RIM - TOP) * k / 12, guard_profile(TOP + (RIM - TOP) * k / 12)[0]) for k in range(12)]
    parts.append(turned(name + "Guard", [(0, 0)] + upper + [(RIM - 0.3, RIM_Y - 0.6), (RIM, RIM_Y),
                                         (RIM - 0.3, RIM_Y + 0.6), (15.5, GUARD_Y), (0, GUARD_Y)],
                        guard, hilt, segs=96))

    # grip: one smooth turned piece from the guard to the pommel, with wire wraps at the top
    prof = catmull([(r, y) for y, r in GRIP], res=4)
    parts.append(turned(name + "Grip", [(0, GUARD_Y - 1)] + [(r, y) for r, y in prof] + [(0, POMMEL_Y)],
                        guard, hilt, segs=48))
    for k, y in enumerate(WRAPS):
        parts.append(torus(f"{name}Wrap{k}", grip_radius(y) / 1000, 0.0012, (0, 0, guard - y / 1000), hilt,
                           major_segments=48, minor_segments=8))

    # knuckle bow: breadth from the sketch; its depth follows the breadth so it reads as a flat band
    path, breadth = bow_path()
    parts.append(band(name + "Bow", path, breadth, [min(5.5, max(3.0, 0.75 * w)) for w in breadth], guard, hilt))

    # pommel: a cuff, then two stacked faceted lozenges, the lower one a long point
    parts.append(turned(name + "PommelCuff", [(0, POMMEL_Y - 1), (15, POMMEL_Y - 1), (15, 383), (0, 383)],
                        guard, hilt, segs=32))
    parts.append(turned(name + "PommelLozenge", [(0, 382), (21, 401), (15, 418), (0, 424)], guard, hilt, segs=6,
                        rot=(0, 0, math.pi / 6)))
    parts.append(turned(name + "PommelPoint", [(0, 421), (18, 442), (0, HILT)], guard, hilt, segs=6))

    if light:
        parts.append(point_light(name + "Light", (0, -0.08, base + ln * 0.3), 3, (0.5, 0.6, 1.0), radius=0.1))
    return group(name, parts, loc, rot_z)
