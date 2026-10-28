"""Slender rapier with a stained-glass crystal blade and a gilded hilt, after the
designer's reference art: the blade rises from a faceted vase-and-lozenge crystal
on a round guard plate drawn to a point at the back; a fan of slanting ribs under the
plate closes onto a ringed neck above a gently spindle-shaped gold grip with a
sapphire ring; the knuckle bow runs from the plate's front rim and ends in a curl;
the pommel is a faceted gold arrowhead.

    r = gem_rapier.build("Rapier", loc=(0, 0, 1.25))
    r.rotation_euler = (math.radians(180), 0, 0)   # point down, e.g. hung on a wall

Origin is at the pommel tip; the blade points up along local +z, flat side facing -y.
"""
import math

import bpy

from assets.lib import as_material, curve, group, lathe, mat, material, mesh_obj, point_light, sphere, torus


def crystal_mat(name, tint):
    """Glass like a stained-glass window: cells of blue, cyan, pink, orange and green
    that glow faintly, dark blue lead lines between them, thin-film iridescence and dispersion."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    inputs = bsdf.inputs
    inputs["Roughness"].default_value = 0.05
    inputs["Transmission Weight"].default_value = 0.85
    inputs["IOR"].default_value = 1.6
    for key, value in (("Thin Film Thickness", 250.0), ("Thin Film IOR", 1.5), ("Dispersion", 0.3)):
        if key in inputs:
            inputs[key].default_value = value
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (28, 28, 7)         # cells longer along the blade
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Randomness"].default_value = 0.9
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    cells = [(0.1, 0.3, 1.0), (0.3, 0.85, 1.0), (1.0, 0.35, 0.7), (1.0, 0.45, 0.1),
             (0.85, 0.9, 1.0), (0.35, 1.0, 0.4), (0.5, 0.25, 1.0), (0.15, 0.45, 0.95)]
    ramp.color_ramp.elements[0].color = (*cells[0], 1)
    ramp.color_ramp.elements[1].position = 7 / 8
    ramp.color_ramp.elements[1].color = (*cells[7], 1)
    for k in range(1, 7):
        ramp.color_ramp.elements.new(k / 8).color = (*cells[k], 1)
    tinted = nt.nodes.new("ShaderNodeMix")
    tinted.data_type = "RGBA"
    tinted.inputs["Factor"].default_value = 0.95
    tinted.inputs["A"].default_value = (*tint, 1)
    # dark blue lead lines along the cell edges; they do not glow
    edge = nt.nodes.new("ShaderNodeTexVoronoi")
    edge.feature = "DISTANCE_TO_EDGE"
    edge.inputs["Randomness"].default_value = 0.9
    lead = nt.nodes.new("ShaderNodeMath")
    lead.operation = "LESS_THAN"
    lead.inputs[1].default_value = 0.04
    leaded = nt.nodes.new("ShaderNodeMix")
    leaded.data_type = "RGBA"
    leaded.inputs["B"].default_value = (0.02, 0.05, 0.3, 1)
    glow = nt.nodes.new("ShaderNodeMix")
    glow.data_type = "RGBA"
    glow.inputs["B"].default_value = (0, 0, 0, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], vor.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], edge.inputs["Vector"])
    nt.links.new(vor.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Red"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], tinted.inputs["B"])
    nt.links.new(edge.outputs["Distance"], lead.inputs[0])
    nt.links.new(lead.outputs["Value"], leaded.inputs["Factor"])
    nt.links.new(tinted.outputs["Result"], leaded.inputs["A"])
    nt.links.new(leaded.outputs["Result"], inputs["Base Color"])
    nt.links.new(lead.outputs["Value"], glow.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], glow.inputs["A"])
    nt.links.new(glow.outputs["Result"], inputs["Emission Color"])
    inputs["Emission Strength"].default_value = 0.25
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


def guard_plate(name, radius, point, thick, top, material, segs=96, rings=8):
    """Round guard plate whose rim draws out into a point at the back (-x); top face at z = top,
    dipping slightly toward the rim."""
    verts, faces = [(0, 0, top), (0, 0, top - thick)], []
    for k in range(1, rings + 1):
        f = k / rings
        for i in range(segs):
            a = 2 * math.pi * i / segs
            r = radius * (1 + point * max(0.0, -math.cos(a)) ** 10) * f
            z = top - 0.0015 * f * f
            verts += [(r * math.cos(a), r * math.sin(a), z), (r * math.cos(a), r * math.sin(a), z - thick * (1 - 0.6 * f))]
    def v(k, i, bottom):
        return 2 + 2 * ((k - 1) * segs + i % segs) + bottom
    for i in range(segs):
        faces += [(0, v(1, i, 0), v(1, i + 1, 0)), (1, v(1, i + 1, 1), v(1, i, 1))]
        for k in range(1, rings):
            faces.append((v(k, i, 0), v(k + 1, i, 0), v(k + 1, i + 1, 0), v(k, i + 1, 0)))
            faces.append((v(k, i, 1), v(k, i + 1, 1), v(k + 1, i + 1, 1), v(k + 1, i, 1)))
        faces.append((v(rings, i, 0), v(rings, i, 1), v(rings, i + 1, 1), v(rings, i + 1, 0)))
    return mesh_obj(name, verts, faces, material, smooth_angle=50)


def build(name="Rapier", loc=(0, 0, 0), rot_z=0.0, *, length=1.25, width=0.03, blade=(0.85, 0.92, 1.0),
          gem="sapphire", hilt="gold", light=True):
    """length: pommel tip to blade tip. width: blade width just above the crystal base.
    blade: glass tint (r, g, b) or a material. gem / hilt: material, palette key or (r, g, b);
    "sapphire" is this asset's own deep-blue stone."""
    if gem == "sapphire":
        gem = mat("Sapphire", (0.05, 0.12, 0.8), 0.05, emit=(0.1, 0.25, 1.0), emit_strength=1.5)
    gem = as_material(gem, name + "Gem", 0.1)
    hilt = as_material(hilt, name + "Hilt", 0.3)
    glass = blade if isinstance(blade, bpy.types.Material) else crystal_mat(name + "Crystal", blade)

    pom, grip_top = 0.09, 0.3            # grip runs from the pommel cuff up to the collar
    guard = 0.358                        # top face of the disc
    base = guard + 0.105                 # where the crystal base gives way to the blade
    hw = width / 2
    parts = []

    # blade: straight, narrowing steadily from the crystal base to the point
    ln = length - base
    parts.append(prism(name + "Blade", [(base - 0.01, hw, hw * 0.38), (base + ln * 0.6, hw * 0.8, hw * 0.32),
                                        (base + ln * 0.9, hw * 0.45, hw * 0.24)], glass, tip=length))
    # crystal base: a vase flaring to sharp shoulders, a waist, then a lozenge running into the blade
    g = guard + 0.006
    parts.append(prism(name + "CrystalBase", [
        (g, hw * 0.65, hw * 0.5), (g + 0.014, hw * 0.85, hw * 0.6), (g + 0.026, hw * 1.6, hw * 0.85),
        (g + 0.031, hw * 1.65, hw * 0.85), (g + 0.04, hw * 0.75, hw * 0.5), (g + 0.046, hw * 0.75, hw * 0.5),
        (g + 0.068, hw * 1.25, hw * 0.65), (base - 0.006, hw * 1.0, hw * 0.42)], glass, tip=base + 0.01))
    parts.append(lathe(name + "Ferrule", [(0.0, guard - 0.001), (0.019, guard - 0.001), (0.019, guard + 0.004),
                                          (0.016, g + 0.001), (0.0, g + 0.001)], (0, 0, 0), hilt, segs=32))

    # guard: a round plate drawn out to a point at the back; under it a fan of slanting ribs, like an
    # umbrella frame, closes onto a narrow ringed neck that stands on a pale band at the top of the grip
    thick = 0.005
    parts.append(guard_plate(name + "Guard", 0.062, 0.4, thick, guard, hilt))
    rib_top, neck_top = guard - thick + 0.001, guard - 0.026
    parts.append(lathe(name + "RibHub", [(0.0, neck_top), (0.014, neck_top), (0.034, rib_top - 0.002),
                                         (0.0, rib_top - 0.002)], (0, 0, 0), hilt, segs=32))
    for k in range(14):
        a = 2 * math.pi * k / 14
        parts.append(curve(f"{name}Rib{k}", [(0.014 * math.cos(a), 0.014 * math.sin(a), neck_top + 0.001),
                                             (0.03 * math.cos(a + 0.2), 0.03 * math.sin(a + 0.2), rib_top - 0.008),
                                             (0.046 * math.cos(a + 0.35), 0.046 * math.sin(a + 0.35), rib_top)],
                           0.0022, hilt, taper=1.3))
    neck0 = grip_top + 0.013
    parts.append(lathe(name + "Neck", [(0.0, neck0), (0.0165, neck0), (0.0135, neck0 + 0.006),
                                       (0.0125, neck_top - 0.008), (0.015, neck_top), (0.0, neck_top)],
                       (0, 0, 0), hilt, segs=32))
    for k in range(3):
        parts.append(torus(f"{name}NeckRing{k}", 0.0138, 0.0015, (0, 0, neck0 + 0.004 + k * 0.0045), hilt,
                           major_segments=32, minor_segments=6))
    band = mat("PaleSilver", (0.82, 0.84, 0.88), 0.3, 0.4)
    parts.append(lathe(name + "Collar", [(0.0, grip_top - 0.002), (0.0175, grip_top - 0.002),
                                         (0.0185, grip_top + 0.005), (0.0175, grip_top + 0.013),
                                         (0.0, grip_top + 0.013)], (0, 0, 0), band, segs=32))

    # knuckle bow: a thick band out of the plate's front rim, sweeping out and down past the grip
    # and ending in a curl
    parts.append(curve(name + "Bow", [(0.05, 0, guard - 0.003), (0.072, 0, guard - 0.004), (0.095, 0, guard - 0.016),
                                      (0.108, 0, guard - 0.05), (0.112, 0, 0.27), (0.1, 0, 0.2), (0.07, 0, 0.14),
                                      (0.045, 0, 0.11), (0.032, 0, 0.1), (0.03, 0, 0.088), (0.04, 0, 0.082),
                                      (0.047, 0, 0.092), (0.041, 0, 0.1)], 0.0068, hilt, taper=0.45))

    # grip: a long gold rod, gently spindle-shaped, with a gem ring where the forefinger sits
    parts.append(lathe(name + "Grip", [(0.0, pom), (0.0115, pom), (0.0135, pom + 0.03), (0.016, pom + 0.07),
                                       (0.0175, 0.2), (0.0168, 0.25), (0.015, grip_top - 0.01),
                                       (0.0145, grip_top), (0.0, grip_top)], (0, 0, 0), hilt, segs=32))
    rz = grip_top - 0.045
    parts.append(torus(name + "GemRing", 0.0182, 0.0035, (0, 0, rz), hilt, major_segments=40, minor_segments=10))
    parts.append(torus(name + "GemBezel", 0.0055, 0.0018, (0, -0.0215, rz), hilt, rot=(math.radians(90), 0, 0),
                       major_segments=20, minor_segments=6))
    parts.append(sphere(name + "GripGem", 0.0055, (0, -0.022, rz), gem, scale=(1, 0.65, 1), segs=14))

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
