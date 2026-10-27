"""Shared bpy helpers for scene scripts and assets: primitives and materials.

Every helper creates objects in the active collection and returns them.
"""
import bpy


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
    m = bpy.data.materials.get(name)
    if m:
        return m
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


def cone(name, r1, r2, depth, loc, material, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    return assign(o, material)


def group(name, parts, loc=(0, 0, 0), rot_z=0.0):
    """Parent parts to a new empty called name, then place and turn the empty."""
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def torus(name, major, minor, loc, material, rot=(0, 0, 0), **kw):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=loc, rotation=rot, **kw)
    o = bpy.context.object
    o.name = name
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


# ---------------------------------------------------------------- materials

def palette():
    """The shared material palette by key; materials are created once and reused."""
    M = {}
    M["stone"] = noisy_mat("Stone", (0.10, 0.095, 0.09), (0.26, 0.24, 0.22), 6, 0.9)
    M["floor"] = noisy_mat("FloorPlanks", (0.22, 0.12, 0.06), (0.36, 0.21, 0.11),
                           4, 0.65, stretch=(1, 12, 1))
    M["wood"] = noisy_mat("Wood", (0.20, 0.10, 0.04), (0.38, 0.22, 0.10),
                          5, 0.6, stretch=(1, 1, 10))
    M["darkwood"] = noisy_mat("DarkWood", (0.07, 0.04, 0.02), (0.16, 0.09, 0.04),
                              5, 0.55, stretch=(1, 1, 10))
    M["plaster"] = noisy_mat("Plaster", (0.36, 0.29, 0.21), (0.50, 0.42, 0.31), 3, 0.95)
    M["iron"] = mat("Iron", (0.12, 0.12, 0.13), 0.45, 1.0)
    M["steel"] = mat("Steel", (0.7, 0.72, 0.75), 0.25, 1.0)
    M["gold"] = mat("Gold", (1.0, 0.72, 0.25), 0.25, 1.0)
    M["brass"] = mat("Brass", (0.8, 0.55, 0.25), 0.35, 1.0)
    M["parchment"] = mat("Parchment", (0.85, 0.74, 0.52), 0.9)
    M["ink"] = mat("Ink", (0.25, 0.08, 0.05), 0.9)
    M["red"] = mat("RedCloth", (0.45, 0.04, 0.05), 0.9)
    M["blue"] = mat("BlueCloth", (0.05, 0.10, 0.35), 0.9)
    M["green"] = mat("GreenCloth", (0.08, 0.25, 0.10), 0.9)
    M["rug"] = noisy_mat("Rug", (0.06, 0.05, 0.22), (0.20, 0.10, 0.35), 14, 1.0)
    M["leather"] = mat("Leather", (0.25, 0.12, 0.05), 0.7)
    M["wax"] = mat("Wax", (0.95, 0.9, 0.75), 0.5)
    M["flame"] = mat("Flame", (1, 0.6, 0.2), 1, emit=(1.0, 0.5, 0.15), emit_strength=12)
    M["fire"] = mat("Fire", (0, 0, 0), 1, emit=(1.0, 0.16, 0.0), emit_strength=2.5)
    M["ember"] = mat("Ember", (0.1, 0.02, 0.0), 1, emit=(1.0, 0.18, 0.02), emit_strength=8)
    M["glass_potion_r"] = mat("PotionRed", (0.9, 0.05, 0.1), 0.1,
                              emit=(0.9, 0.05, 0.1), emit_strength=1.5)
    M["glass_potion_b"] = mat("PotionBlue", (0.1, 0.3, 1.0), 0.1,
                              emit=(0.1, 0.4, 1.0), emit_strength=2.0)
    M["glass_potion_g"] = mat("PotionGreen", (0.2, 0.9, 0.2), 0.1,
                              emit=(0.2, 0.9, 0.3), emit_strength=1.5)
    M["crystal"] = mat("Crystal", (0.5, 0.3, 1.0), 0.1,
                       emit=(0.55, 0.3, 1.0), emit_strength=6)
    M["purple"] = mat("PurpleCloth", (0.22, 0.05, 0.35), 0.9)
    M["arcane_cyan"] = mat("ArcaneCyan", (0.3, 0.8, 1.0), 0.3,
                           emit=(0.2, 0.75, 1.0), emit_strength=10)
    M["arcane_purple"] = mat("ArcanePurple", (0.6, 0.3, 1.0), 0.2,
                             emit=(0.6, 0.25, 1.0), emit_strength=6)
    M["arcane_green"] = mat("ArcaneGreen", (0.3, 1.0, 0.3), 0.2,
                            emit=(0.25, 1.0, 0.2), emit_strength=4)
    M["window"] = mat("WindowGlow", (0.4, 0.55, 0.9), 0.5,
                      emit=(0.35, 0.5, 0.9), emit_strength=2.0)
    M["bookcols"] = [mat(f"Book{i}", c, 0.8) for i, c in enumerate([
        (0.4, 0.05, 0.05), (0.05, 0.2, 0.08), (0.08, 0.1, 0.35),
        (0.35, 0.25, 0.08), (0.25, 0.08, 0.25), (0.1, 0.08, 0.05)])]
    return M


def material(key):
    """One material from the palette, e.g. material("wood")."""
    return palette()[key]


def as_material(value, name, rough=0.9):
    """Accept a material, a palette key, or an (r, g, b) colour (made into a cloth-like material)."""
    if value is None or isinstance(value, bpy.types.Material):
        return value
    if isinstance(value, str):
        return material(value)
    return mat(name, tuple(value), rough)
