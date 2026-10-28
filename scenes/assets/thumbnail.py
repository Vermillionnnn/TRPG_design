"""Render a thumbnail for one asset (or all of them) on a neutral studio backdrop.

    scenes/blender.sh scenes/assets/thumbnail.py chair
    scenes/blender.sh scenes/assets/thumbnail.py all
    scenes/blender.sh scenes/assets/thumbnail.py chair --set seat_height=0.6 --out out/tall.png

Options: --out PATH (default scenes/assets/<name>.png), --samples N (default 64),
--size PX (default 384), --set key=value (repeatable; passed to build()).
"""
import ast
import importlib
import math
import os
import sys

SCENES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCENES)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from assets.lib import mat, reset  # noqa: E402

ASSETS = os.path.join(SCENES, "assets")
NOT_ASSETS = {"__init__", "lib", "thumbnail"}
OWN_THUMBNAIL = {"gem_rapier"}       # thumbnail comes from the asset's showcase scene; "all" skips it


def asset_names():
    return sorted(f[:-3] for f in os.listdir(ASSETS)
                  if f.endswith(".py") and f[:-3] not in NOT_ASSETS | OWN_THUMBNAIL)


def bounds(root):
    pts = [o.matrix_world @ Vector(c) for o in [root, *root.children_recursive]
           if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def studio(lo, hi, samples, size):
    scene = bpy.context.scene
    center = (lo + hi) / 2
    radius = (hi - lo).length / 2

    # large floor plane; the grey world fills the background
    bpy.ops.mesh.primitive_plane_add(size=radius * 40, location=(center.x, center.y, lo.z))
    floor = bpy.context.object
    floor.data.materials.append(mat("Backdrop", (0.30, 0.29, 0.28), 0.8))
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.30, 0.29, 0.28, 1)
    bg.inputs["Strength"].default_value = 0.6

    for name, energy, rot in [("Key", 3.0, (50, 0, -40)), ("Rim", 2.0, (60, 0, 150))]:
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = energy
        ld.angle = math.radians(8)
        o = bpy.data.objects.new(name, ld)
        o.rotation_euler = [math.radians(a) for a in rot]
        scene.collection.objects.link(o)

    # three-quarter view from the front (-y) and a little above
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    d = radius / math.tan(cam_data.angle / 2) * 1.15
    direction = Vector((0.55, -1.0, 0.45)).normalized()
    cam.location = center + direction * d
    cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.view_settings.view_transform = "AgX"


def render(name, out, samples, size, params):
    reset()
    module = importlib.import_module("assets." + name)
    root = module.build(**params)
    bpy.context.view_layer.update()
    studio(*bounds(root), samples, size)
    bpy.context.scene.render.filepath = os.path.abspath(out)
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if not argv:
        sys.exit("usage: thumbnail.py NAME|all [--out PATH] [--samples N] [--size PX] [--set k=v]")
    target, out, samples, size, params = argv[0], None, 64, 384, {}
    for i, a in enumerate(argv):
        if a == "--out":
            out = argv[i + 1]
        elif a == "--samples":
            samples = int(argv[i + 1])
        elif a == "--size":
            size = int(argv[i + 1])
        elif a == "--set":
            k, v = argv[i + 1].split("=", 1)
            params[k] = ast.literal_eval(v)
    for name in asset_names() if target == "all" else [target]:
        render(name, out or os.path.join(ASSETS, name + ".png"), samples, size, params)


main()
