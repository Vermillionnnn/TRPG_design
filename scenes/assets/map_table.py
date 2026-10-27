"""Round tripod table with a city map pinned to it and a floating, glowing
illusion of the city above the map.

    map_table.build("MapTable", loc=(3.0, 1.45, 0))

Origin is on the floor under the table centre. The illusion (towers, ring and
light) hangs under an empty called <name>IllusionRig, so a scene can spin it.
"""
import math
import random

import bpy

from assets.lib import as_material, box, cone, cyl, group, material, point_light, shell


def map_mat():
    """Parchment with inked district lines and a blue harbour."""
    m = bpy.data.materials.get("CityMap")
    if m:
        return m
    m = bpy.data.materials.new("CityMap")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 9
    ink = nt.nodes.new("ShaderNodeMath")
    ink.operation = "LESS_THAN"
    ink.inputs[1].default_value = 0.025
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    nt.links.new(vo.outputs["Distance"], ink.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    sea = nt.nodes.new("ShaderNodeMath")
    sea.operation = "GREATER_THAN"
    sea.inputs[1].default_value = 0.35
    nt.links.new(sep.outputs["X"], sea.inputs[0])
    paper = nt.nodes.new("ShaderNodeMix")
    paper.data_type = "RGBA"
    paper.inputs["A"].default_value = (0.78, 0.66, 0.44, 1)
    paper.inputs["B"].default_value = (0.25, 0.38, 0.45, 1)
    nt.links.new(sea.outputs[0], paper.inputs["Factor"])
    lines = nt.nodes.new("ShaderNodeMix")
    lines.data_type = "RGBA"
    lines.inputs["B"].default_value = (0.15, 0.07, 0.04, 1)
    nt.links.new(ink.outputs[0], lines.inputs["Factor"])
    nt.links.new(paper.outputs["Result"], lines.inputs["A"])
    nt.links.new(lines.outputs["Result"], bsdf.inputs["Base Color"])
    return m


def build(name="MapTable", loc=(0, 0, 0), rot_z=0.0, *, radius=0.85, height=0.89, wood="wood",
          illusion=True, glow="arcane_cyan", rng=None):
    rng = rng or random.Random(8)
    wood = as_material(wood, name + "Wood", 0.6)
    h = height
    p = [cyl(name + "Top", radius, 0.06, (0, 0, h - 0.03), wood, verts=48),
         cyl(name + "Rim", radius + 0.03, 0.04, (0, 0, h - 0.05), material("brass"), verts=48),
         cyl(name + "Stem", 0.1, h - 0.14, (0, 0, (h - 0.14) / 2 + 0.07), wood, verts=16)]
    for i in range(3):
        a = 2 * math.pi * i / 3
        p.append(box(f"{name}Foot{i}", (0.55, 0.08, 0.08), (0.25 * math.cos(a), 0.25 * math.sin(a), 0.1),
                     wood, rot=(0, math.radians(-12), a)))
    p.append(box(name + "Map", (1.3 * radius, 0.94 * radius, 0.004), (0, 0, h + 0.002), map_mat(),
                 rot=(0, 0, 0.2), bev=0))
    pins = (material("seal_wax"), material("arcane_purple"), material("pewter"))
    for i in range(7):
        p.append(cone(f"{name}Pin{i}", 0.02, 0, 0.06, (rng.uniform(-0.47, 0.47) * radius,
                                                       rng.uniform(-0.35, 0.35) * radius, h + 0.03),
                      rng.choice(pins), verts=8))
    if illusion:
        glow = as_material(glow, name + "Glow", 0.3)
        rig = bpy.data.objects.new(name + "IllusionRig", None)
        bpy.context.collection.objects.link(rig)
        rig.location = (0, 0, h + 0.46)
        parts = [shell(name + "IllusionRing", 0.5, 0.48, -0.005, 0.0, glow, segs=48)]
        for i in range(14):
            hh = rng.uniform(0.04, 0.18)
            parts.append(box(f"{name}IllusionTower{i}", (0.05, 0.05, hh),
                             (rng.uniform(-0.35, 0.35), rng.uniform(-0.25, 0.25), hh / 2), glow, bev=0))
        parts.append(point_light(name + "IllusionLight", (0, 0, 0.15), 15, (0.3, 0.75, 1.0), radius=0.2))
        for o in parts:
            o.parent = rig
        p.append(rig)
    return group(name, p, loc, rot_z)
