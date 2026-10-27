"""Round-headed window with diamond leading, a wooden frame with mullion and
transom, a basalt surround, a stone sill and a glowing night sky behind the
glass. Optional moonlight: a soft area light and a spot beam into the room.

    lancet_window.build("Window", loc=(0, 4.98, 0))

Origin is on the floor at the wall face under the middle of the window; the
room is toward local -y. The lights are <name>Light and <name>Beam.
"""
import math
import random

import bpy
from mathutils import Vector

from assets.lib import Batch, arch_outline, box, group, material, mesh_obj, shell


def sky_mat():
    """Night sky with stars: a vertical gradient plus thresholded Voronoi dots."""
    m = bpy.data.materials.get("ScryingSky")
    if m:
        return m
    m = bpy.data.materials.new("ScryingSky")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.25, 0.3, 0.6, 1)
    ramp.color_ramp.elements[1].color = (0.02, 0.03, 0.12, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 90
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "LESS_THAN"
    st.inputs[1].default_value = 0.035
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    nt.links.new(vo.outputs["Distance"], st.inputs[0])
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    nt.links.new(st.outputs[0], add.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], add.inputs["A"])
    add.inputs["B"].default_value = (1, 1, 1, 1)
    nt.links.new(add.outputs["Result"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.6
    return m


def build(name="LancetWindow", loc=(0, 0, 0), rot_z=0.0, *, width=1.5, height=2.2, sill=1.0,
          light=True, rng=None):
    """height is the straight part of the opening; sill is its height above the floor."""
    rng = rng or random.Random(31)
    w, h, z0 = width, height, sill
    wood, iron, basalt = material("darkwood"), material("iron"), material("blackstone")
    p = [box(name + "Pane", (w, 0.02, h), (0, 0.02, z0 + h / 2), sky_mat(), bev=0),
         shell(name + "PaneHead", w / 2, 0, -0.01, 0.01, sky_mat(), arc=(0, math.pi), segs=48,
               loc=(0, 0.02, z0 + h), rot=(math.pi / 2, 0, 0))]
    # diamond lead cames, clipped to the opening by a hidden cutter
    B = Batch()
    span = h + w / 2
    for k in range(-14, 15):
        for sgn in (-1, 1):
            B.box(iron, (0.012, 0.01, math.sqrt(2) * span), (k * 0.22, 0, z0 + span / 2),
                  ry=sgn * math.pi / 4)
    lead = B.build(name + "Lead")[0]
    outline = [(x, z0 + z) for x, z in arch_outline(w, h)]
    verts = [(x, dy, z) for dy in (-0.1, 0.1) for x, z in outline]
    n = len(outline)
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    cutter = mesh_obj(name + "LeadCutter", verts, faces, iron, smooth_angle=0)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    mod = lead.modifiers.new("clip", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.object = cutter
    mod.solver = "EXACT"
    p += [lead, cutter]
    # frame, mullion, transom
    for sx in (-1, 1):
        p.append(box(f"{name}Jamb{sx}", (0.1, 0.14, h), (sx * (w / 2 + 0.05), -0.04, z0 + h / 2), wood))
    p += [shell(name + "HeadFrame", w / 2 + 0.1, w / 2, -0.07, 0.07, wood, arc=(0, math.pi), segs=48,
                loc=(0, -0.04, z0 + h), rot=(math.pi / 2, 0, 0)),
          box(name + "Mullion", (0.07, 0.1, span - 0.05), (0, -0.03, z0 + span / 2), wood),
          box(name + "Transom", (w, 0.1, 0.07), (0, -0.03, z0 + h * 0.62), wood)]
    # basalt voussoirs round the head and quoins down the sides
    B = Batch()
    for i in range(13):
        a = math.pi * i / 12
        r = w / 2 + 0.27
        B.box(basalt, (0.34 if i % 2 else 0.26, 0.18, 0.22),
              (r * math.cos(a), -0.06, z0 + h + r * math.sin(a)), ry=-a + math.pi / 2)
    for sx in (-1, 1):
        zz = z0
        while zz < z0 + h - 0.1:
            hh = rng.uniform(0.28, 0.36)
            B.box(basalt, (0.34 if int(zz * 10) % 2 else 0.26, 0.18, hh - 0.02),
                  (sx * (w / 2 + 0.27), -0.06, zz + hh / 2))
            zz += hh
    p += B.build(name + "Surround", bev=0.02)
    p.append(box(name + "Sill", (w + 0.7, 0.4, 0.1), (0, -0.18, z0 - 0.05), material("stone"), bev=0.02))
    if light:
        ld = bpy.data.lights.new(name + "Light", "AREA")
        ld.energy = 60
        ld.size = w - 0.1
        ld.color = (0.5, 0.65, 1.0)
        o = bpy.data.objects.new(name + "Light", ld)
        o.location = (0, -0.25, z0 + h / 2)
        o.rotation_euler = (math.radians(-90), 0, 0)
        bpy.context.collection.objects.link(o)
        ld = bpy.data.lights.new(name + "Beam", "SPOT")
        ld.energy = 6000
        ld.color = (0.55, 0.7, 1.0)
        ld.spot_size = math.radians(30)
        ld.spot_blend = 0.4
        ld.shadow_soft_size = 0.05
        b = bpy.data.objects.new(name + "Beam", ld)
        b.location = (0.3, 0.6, z0 + h + 0.5)
        b.rotation_euler = (Vector((-0.6, -4.0, 0.0)) - b.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(b)
        p += [o, b]
    return group(name, p, loc, rot_z)
