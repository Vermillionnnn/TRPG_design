"""Glowing summoning circle: three rings, a hexagram and runes, with a column of light.

    summoning_circle.build("Circle", loc=(0.72, 1.25, 0))

Origin is at the centre on the floor. The rings and runes hang off <name>Rings and
the hexagram off <name>Hex, so a scene can spin them in opposite directions.
Lights are <name>Beam (spot shining up) and <name>Light.
"""
import math

import bpy
from mathutils import Vector

from assets.lib import as_material, assign, box, group, point_light


def shaft_material():
    """Emission that fades out with height, mixed with transparency (object z -0.9..0.9)."""
    m = bpy.data.materials.get("ShaftMat")
    if m:
        return m
    m = bpy.data.materials.new("ShaftMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["From Min"].default_value = -0.9
    mapr.inputs["From Max"].default_value = 0.9
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.3, 0.75, 1.0, 1)
    mult = nt.nodes.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mult.inputs[0])
    nt.links.new(mult.outputs["Value"], em.inputs["Strength"])
    nt.links.new(em.outputs["Emission"], add.inputs[0])
    nt.links.new(tr.outputs["BSDF"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    return m


def build(name="SummoningCircle", loc=(0, 0, 0), rot_z=0.0, *, glow="arcane_cyan", beam=True):
    """glow: material, palette key or (r, g, b) for the lines. beam adds the lights and light shaft."""
    glow = as_material(glow, name + "Glow", 0.3)
    rings = []
    for i, (rr, w) in enumerate([(0.47, 0.012), (0.40, 0.008), (0.19, 0.007)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=w,
                                         major_segments=64, location=(0, 0, 0.078))
        o = bpy.context.object
        o.name = f"{name}Ring{i}"
        o.scale.z = 0.3
        rings.append(assign(o, glow))
    # rune glyphs between the two outer rings
    for k in range(16):
        a = k * 2 * math.pi / 16
        rings.append(box(f"{name}Rune{k}", (0.03, 0.011, 0.005),
                         (0.435 * math.cos(a), 0.435 * math.sin(a), 0.076), glow,
                         rot=(0, 0, a + (math.pi / 4 if k % 2 else 0)), bev=0))
    # hexagram: two triangles of thin glowing bars
    hexa, R = [], 0.40
    for t in range(2):
        for k in range(3):
            a1 = math.radians(90 + t * 60 + k * 120)
            a2 = math.radians(90 + t * 60 + (k + 1) * 120)
            p1 = Vector((R * math.cos(a1), R * math.sin(a1), 0.075))
            p2 = Vector((R * math.cos(a2), R * math.sin(a2), 0.075))
            ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
            hexa.append(box(f"{name}Bar{t}{k}", ((p2 - p1).length, 0.012, 0.006), (p1 + p2) / 2,
                            glow, rot=(0, 0, ang), bev=0))
    parts = [group(name + "Rings", rings), group(name + "Hex", hexa)]

    if beam:
        # column of light rising out of the circle (visible through haze)
        ld = bpy.data.lights.new(name + "Beam", "SPOT")
        ld.energy = 450
        ld.color = (0.3, 0.75, 1.0)
        ld.spot_size = math.radians(36)
        ld.spot_blend = 0.6
        ld.shadow_soft_size = 0.3
        spot = bpy.data.objects.new(name + "Beam", ld)
        spot.location = (0, 0, 0.02)
        spot.rotation_euler = (math.pi, 0, 0)          # spots shine down -Z; flip to shine up
        bpy.context.collection.objects.link(spot)
        parts.append(spot)
        parts.append(point_light(name + "Light", (0, 0, 0.3), 15, (0.3, 0.7, 1.0), radius=0.3))
        # visible shaft: open cylinder whose glow fades out with height
        bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=1.8, vertices=48, end_fill_type="NOTHING",
                                            location=(0, 0, 0.95))
        shaft = bpy.context.object
        shaft.name = name + "Shaft"
        bpy.ops.object.shade_smooth()
        assign(shaft, shaft_material())
        shaft.visible_shadow = False
        parts.append(shaft)
    return group(name, parts, loc, rot_z)
