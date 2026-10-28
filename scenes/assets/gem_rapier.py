"""Slender rapier with a clear crystal blade lit from within and a gilded hilt, after
the designer's reference art: the blade rises from a faceted vase-and-lozenge crystal
set in a thin gold ring on a heavy bell-shaped guard (bevelled rim, drawn to a point
at the back, its underside sloping down into a ringed neck); the knuckle bow runs
from the guard's front rim and ends in a curl; the grip is gently spindle-shaped,
fullest just under the guard; the pommel is a faceted gold arrowhead.

    r = gem_rapier.build("Rapier", loc=(0, 0, 1.25))
    r.rotation_euler = (math.radians(180), 0, 0)   # point down, e.g. hung on a wall

Origin is at the pommel tip; the blade points up along local +z, flat side facing -y.
"""
import math

import bpy

from assets.lib import as_material, curve, group, lathe, mat, mesh_obj, point_light, torus


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


def core_mat(name, colors, strength):
    """Pure emission for the glowing core, its colour drifting along the blade through `colors`."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 1, 1.4)          # about one colour cycle along the blade
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_profile = "SIN"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 1.0
    wave.inputs["Distortion"].default_value = 2.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].color = (*colors[0], 1)
    cr.elements[1].color = (*colors[-1], 1)
    for k, c in enumerate(colors[1:-1], 1):
        cr.elements.new(k / (len(colors) - 1)).color = (*c, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
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


def crystal(name, sections, tip, glass, core, inset=0.45):
    """A clear faceted prism with a smaller glowing copy of itself inside."""
    outer = prism(name, sections, glass, tip=tip)
    z0 = sections[0][0]
    inner = prism(name + "Core", [(z + (0.004 if i == 0 else 0), w * inset, t * inset)
                                  for i, (z, w, t) in enumerate(sections)], core, tip=tip - (tip - z0) * 0.03)
    return [outer, inner]


def bell_guard(name, profile, point, reach, material, segs=96):
    """Turned guard from a (radius, z) profile listed from the neck outward and up to the
    top centre; the rim is drawn out toward -x into a point (`point` = extra length at the
    tip, as a fraction; only radii beyond `reach` are stretched)."""
    n = len(profile)
    verts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        pull = point * max(0.0, -math.cos(a)) ** 10
        for r, z in profile:
            k = 1 + pull * max(0.0, (r - reach) / (profile_max(profile) - reach)) ** 1.5
            verts.append((r * k * math.cos(a), r * k * math.sin(a), z))
    for i in range(segs):
        j = (i + 1) % segs
        for p in range(n - 1):
            faces.append((i * n + p, i * n + p + 1, j * n + p + 1, j * n + p))
    faces.append(tuple(i * n for i in range(segs)))                 # cap at the neck end
    return mesh_obj(name, verts, faces, material, smooth_angle=30)


def profile_max(profile):
    return max(r for r, _ in profile)


def build(name="Rapier", loc=(0, 0, 0), rot_z=0.0, *, length=1.25, width=0.03, blade=(0.95, 0.97, 1.0),
          glow=((0.45, 0.8, 1.0), (0.75, 0.6, 1.0), (1.0, 0.6, 0.85), (0.5, 0.85, 1.0)), hilt="gold",
          light=True):
    """length: pommel tip to blade tip. width: blade width just above the crystal base.
    blade: glass tint (r, g, b) or a material. glow: colours the core drifts through along the
    blade, or a material. hilt: material, palette key or (r, g, b)."""
    hilt = as_material(hilt, name + "Hilt", 0.3)
    glass = blade if isinstance(blade, bpy.types.Material) else glass_mat(name + "Glass", blade)
    core = glow if isinstance(glow, bpy.types.Material) else core_mat(name + "Core", glow, 6.0)

    pom, grip_top = 0.09, 0.3            # grip runs from the pommel cuff up to the collar
    guard = 0.378                        # top face of the guard
    g = guard + 0.003                    # top of the thin ring the crystal stands in
    base = g + 0.1                       # where the crystal base gives way to the blade
    hw = width / 2
    parts = []

    # blade: straight, narrowing steadily from the crystal base to the point
    ln = length - base
    parts += crystal(name + "Blade", [(base - 0.01, hw, hw * 0.38), (base + ln * 0.6, hw * 0.8, hw * 0.32),
                                      (base + ln * 0.9, hw * 0.45, hw * 0.24)], length, glass, core)
    # crystal base: a vase flaring to sharp shoulders, a waist, then a lozenge running into the blade
    parts += crystal(name + "CrystalBase", [
        (g, hw * 0.65, hw * 0.5), (g + 0.014, hw * 0.85, hw * 0.6), (g + 0.026, hw * 1.6, hw * 0.85),
        (g + 0.031, hw * 1.65, hw * 0.85), (g + 0.04, hw * 0.75, hw * 0.5), (g + 0.046, hw * 0.75, hw * 0.5),
        (g + 0.068, hw * 1.25, hw * 0.65), (base - 0.006, hw * 1.0, hw * 0.42)], base + 0.01, glass, core, 0.5)
    # the thin ring the crystal stands in
    parts.append(lathe(name + "Ring", [(0.0, guard - 0.001), (0.0135, guard - 0.001), (0.0135, g),
                                       (0.0, g)], (0, 0, 0), hilt, segs=32))

    # guard: a heavy bell opening downward; flat top, bevelled rim drawn to a point at the back,
    # the underside sloping in to a ringed neck that stands on a pale band at the top of the grip
    neck0, neck1 = grip_top + 0.013, guard - 0.04
    parts.append(bell_guard(name + "Guard", [
        (0.0145, neck1), (0.018, guard - 0.034), (0.03, guard - 0.028), (0.05, guard - 0.021),
        (0.06, guard - 0.017), (0.0645, guard - 0.0135), (0.067, guard - 0.009), (0.067, guard - 0.005),
        (0.064, guard - 0.001), (0.06, guard), (0.0, guard)], 0.4, 0.03, hilt))
    parts.append(lathe(name + "Neck", [(0.0, neck0), (0.016, neck0), (0.0135, neck0 + 0.005),
                                       (0.0128, neck1 - 0.004), (0.0145, neck1 + 0.001), (0.0, neck1 + 0.001)],
                       (0, 0, 0), hilt, segs=32))
    for k in range(3):
        parts.append(torus(f"{name}NeckRing{k}", 0.0134, 0.0014, (0, 0, neck0 + 0.006 + k * 0.0045), hilt,
                           major_segments=32, minor_segments=6))
    band = mat("PaleSilver", (0.82, 0.84, 0.88), 0.3, 0.4)
    parts.append(lathe(name + "Collar", [(0.0, grip_top - 0.002), (0.0175, grip_top - 0.002),
                                         (0.0185, grip_top + 0.005), (0.0175, grip_top + 0.013),
                                         (0.0, grip_top + 0.013)], (0, 0, 0), band, segs=32))

    # knuckle bow: a thick band out of the guard's front rim, sweeping out and down past the grip
    # and ending in a curl
    parts.append(curve(name + "Bow", [(0.054, 0, guard - 0.007), (0.075, 0, guard - 0.008), (0.097, 0, guard - 0.02),
                                      (0.108, 0, guard - 0.055), (0.112, 0, 0.27), (0.1, 0, 0.2), (0.07, 0, 0.14),
                                      (0.045, 0, 0.11), (0.032, 0, 0.1), (0.03, 0, 0.088), (0.04, 0, 0.082),
                                      (0.047, 0, 0.092), (0.041, 0, 0.1)], 0.0072, hilt, taper=0.45))

    # grip: a long gold rod, gently spindle-shaped, fullest a little below the collar and
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
