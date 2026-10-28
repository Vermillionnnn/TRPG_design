"""Slender rapier with a clear crystal blade full of coloured sparks and a gilded hilt,
after the designer's reference art: the blade rises from a faceted vase-and-lozenge
crystal set in a thin gold ring on a heavy guard shaped like two stacked frustums (a
narrow flat top widening down to a sharp round rim, then
narrowing again into a ringed neck); the knuckle bow is a flat band carrying the
guard's top face out and down, looping once before it joins the pommel; the grip is gently spindle-shaped, fullest near its top; the pommel is
a faceted gold arrowhead.

    r = gem_rapier.build("Rapier", loc=(0, 0, 1.25))
    r.rotation_euler = (math.radians(180), 0, 0)   # point down, e.g. hung on a wall

Origin is at the pommel tip; the blade points up along local +z, flat side facing -y.
"""
import math
import random

import bpy

from assets.lib import Batch, as_material, curve, group, lathe, mat, mesh_obj, point_light, torus


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


def band(name, pts, half_breadth, half_thick, material, res=10, ring=16):
    """Flat band swept along a smooth path through pts, which lie in the x-z plane. Its
    cross-section is an ellipse: half_breadth(u) across the path within that plane, half_thick(u)
    along y, with u running 0..1 from the first point to the last."""
    def catmull(p0, p1, p2, p3, t):
        return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                            + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3))
    ext = [pts[0]] + list(pts) + [pts[-1]]
    path = [catmull(*ext[i:i + 4], k / res) for i in range(len(pts) - 1) for k in range(res)] + [pts[-1]]
    verts, faces = [], []
    for i, (x, z) in enumerate(path):
        u = i / (len(path) - 1)
        x0, z0 = path[max(i - 1, 0)]
        x1, z1 = path[min(i + 1, len(path) - 1)]
        tx, tz = x1 - x0, z1 - z0
        tl = math.hypot(tx, tz)
        nx, nz = tz / tl, -tx / tl                    # in-plane normal to the path
        a, b = half_breadth(u), half_thick(u)
        for k in range(ring):
            c, s = math.cos(2 * math.pi * k / ring), math.sin(2 * math.pi * k / ring)
            verts.append((x + nx * a * c, b * s, z + nz * a * c))
    for i in range(len(path) - 1):
        for k in range(ring):
            j = (k + 1) % ring
            faces.append((i * ring + k, i * ring + j, (i + 1) * ring + j, (i + 1) * ring + k))
    faces += [tuple(reversed(range(ring))), tuple((len(path) - 1) * ring + k for k in range(ring))]
    return mesh_obj(name, verts, faces, material, smooth_angle=70)


def bell_guard(name, profile, material, segs=96):
    """Turned guard from a (radius, z) profile listed from the neck outward and up to the
    top centre, open at the neck end."""
    n = len(profile)
    verts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        verts += [(r * math.cos(a), r * math.sin(a), z) for r, z in profile]
    for i in range(segs):
        j = (i + 1) % segs
        for p in range(n - 1):
            faces.append((i * n + p, i * n + p + 1, j * n + p + 1, j * n + p))
    faces.append(tuple(i * n for i in range(segs)))                 # cap at the neck end
    return mesh_obj(name, verts, faces, material, smooth_angle=30)


def build(name="Rapier", loc=(0, 0, 0), rot_z=0.0, *, length=1.25, width=0.03, blade=(0.95, 0.97, 1.0),
          sparkle=((0.2, 0.45, 1.0), (0.3, 0.9, 1.0), (1.0, 0.35, 0.7), (1.0, 0.55, 0.15),
                   (0.4, 1.0, 0.45), (0.65, 0.35, 1.0)), sparks_count=260, hilt="gold", light=True, rng=None):
    """length: pommel tip to blade tip. width: blade width just above the crystal base.
    blade: glass tint (r, g, b) or a material. sparkle: colours of the glowing specks inside
    the crystal; sparks_count: how many. hilt: material, palette key or (r, g, b). rng: random source."""
    rng = rng or random.Random(5)
    hilt = as_material(hilt, name + "Hilt", 0.3)
    glass = blade if isinstance(blade, bpy.types.Material) else glass_mat(name + "Glass", blade)
    specks = [mat(f"Spark{k}", c, 0.5, emit=c, emit_strength=4) for k, c in enumerate(sparkle)]

    pom, grip_top = 0.09, 0.3            # grip runs from the pommel cuff up to the neck
    guard = 0.378                        # top face of the guard
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
    parts.append(lathe(name + "Ring", [(0.0, guard - 0.001), (0.0135, guard - 0.001), (0.0135, g),
                                       (0.0, g)], (0, 0, 0), hilt, segs=32))

    # guard: two frustums base to base. The upper one widens from a narrow flat top down to a
    # sharp round rim, symmetric all round; the lower one narrows from the rim to a ringed neck.
    neck1 = guard - 0.041
    parts.append(bell_guard(name + "Guard", [
        (0.015, neck1), (0.02, guard - 0.036), (0.06, guard - 0.021), (0.066, guard - 0.0185),
        (0.068, guard - 0.017), (0.066, guard - 0.0155), (0.047, guard - 0.0015), (0.045, guard),
        (0.0, guard)], hilt))
    parts.append(lathe(name + "Neck", [(0.0, grip_top), (0.0152, grip_top), (0.0135, grip_top + 0.006),
                                       (0.0128, neck1 - 0.004), (0.0152, neck1 + 0.001), (0.0, neck1 + 0.001)],
                       (0, 0, 0), hilt, segs=32))
    for k in range(4):
        parts.append(torus(f"{name}NeckRing{k}", 0.0134, 0.0014, (0, 0, grip_top + 0.008 + k * 0.0065), hilt,
                           major_segments=32, minor_segments=6))

    # knuckle bow: a flat band growing out of the guard's front; its upper edge carries on the
    # slope of the guard's upper frustum and bends smoothly down past the grip, narrowing steadily,
    # turns one small loop and runs into the pommel cuff
    parts.append(band(name + "Bow", [
        (0.038, guard - 0.0095), (0.055, guard - 0.0158), (0.075, guard - 0.026), (0.092, guard - 0.041),
        (0.104, guard - 0.065), (0.11, 0.285), (0.106, 0.235), (0.092, 0.19),
        (0.072, 0.158), (0.06, 0.142)] + [
        (0.068 + 0.0105 * math.cos(a), 0.127 + 0.0105 * math.sin(a))      # the loop, turning clockwise
        for a in (math.radians(d) for d in (150, 105, 60, 15, -30, -75, -120, -165, -205))] + [
        (0.05, 0.114), (0.034, 0.101), (0.022, pom + 0.006), (0.012, pom + 0.001)],
        lambda u: 0.0036 + 0.0085 * max(0.0, 1 - u / 0.28) ** 1.6 + 0.0014 * (1 - u) + 0.002 * max(0.0, u - 0.94) / 0.06,
        lambda u: 0.0055 + 0.016 * max(0.0, 1 - u / 0.14) ** 2 - 0.0026 * u + 0.002 * max(0.0, u - 0.94) / 0.06, hilt))

    # grip: a long gold rod, gently spindle-shaped, fullest a little below the neck and
    # tapering slowly down to the pommel
    parts.append(lathe(name + "Grip", [(0.0, pom), (0.011, pom), (0.0122, pom + 0.04), (0.0142, 0.18),
                                       (0.0165, 0.235), (0.0172, 0.255), (0.0165, 0.28), (0.0152, grip_top),
                                       (0.0, grip_top)], (0, 0, 0), hilt, segs=32))

    # pommel: a cuff with curled prongs over two stacked faceted lozenges, the lower one a point
    parts.append(lathe(name + "PommelPoint", [(0.0, 0.0), (0.012, 0.022), (0.016, 0.03), (0.008, 0.042),
                                              (0.0, 0.042)], (0, 0, 0), hilt, segs=6))
    parts.append(lathe(name + "PommelLozenge", [(0.0, 0.04), (0.008, 0.04), (0.019, 0.058), (0.02, 0.064),
                                                (0.01, pom - 0.004), (0.0, pom - 0.004)], (0, 0, 0), hilt, segs=6,
                       rot=(0, 0, math.pi / 6)))
    parts.append(lathe(name + "PommelCuff", [(0.0, pom - 0.008), (0.0135, pom - 0.008), (0.0145, pom - 0.002),
                                             (0.013, pom + 0.006), (0.0, pom + 0.006)], (0, 0, 0), hilt, segs=24))
    for k in range(4):                   # prongs curling down over the lozenge's shoulders
        a = k * math.pi / 2 + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        parts.append(curve(f"{name}Prong{k}", [(0.013 * c, 0.013 * s, pom - 0.004), (0.022 * c, 0.022 * s, pom - 0.012),
                                               (0.025 * c, 0.025 * s, pom - 0.022), (0.019 * c, 0.019 * s, pom - 0.024)],
                           0.0022, hilt, taper=0.6))

    if light:
        parts.append(point_light(name + "Light", (0, -0.08, base + ln * 0.3), 3, (0.5, 0.6, 1.0), radius=0.1))
    return group(name, parts, loc, rot_z)
