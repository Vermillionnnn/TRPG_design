"""Showcase of three weapons on a dark studio backdrop: the crystal rapier,
the vine-wrapped staff and the magic lute (all from scenes/assets).

Run with:  python3 scenes/weapons/build_scene.py [--render out.png] [--samples N]
           [--shot all|rapier|staff|lute] [--res percent] [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P scenes/weapons/build_scene.py -- --render out.png

Units are metres. The pieces float side by side along X above a round plinth,
facing -Y toward the camera.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from assets import gem_rapier, magic_lute, vine_staff  # noqa: E402
from assets.lib import lathe, mat, noisy_mat, reset  # noqa: E402

LIFT = 0.12       # gap between the plinth and the bottom of each piece
PLINTH = 0.08     # plinth height

# shot: (camera location, look-at point, focal length, resolution)
SHOTS = {
    "all": ((0.0, -4.6, 1.25), (0.05, 0.0, 1.0), 50, (1600, 1200)),
    "rapier": ((-0.32, -0.92, 0.66), (-0.5, 0.0, 0.52), 50, (1000, 1200)),
    "staff": ((0.06, -0.66, 2.0), (0.0, 0.0, 1.8), 60, (1000, 1200)),
    "lute": ((0.95, -1.35, 0.85), (0.62, 0.0, 0.58), 50, (1000, 1200)),
}


def build_props():
    base = PLINTH + LIFT
    rapier = gem_rapier.build("Rapier", loc=(-0.55, 0, base))
    rapier.rotation_euler = (0, math.radians(10), 0)
    vine_staff.build("Staff", loc=(0, 0, base))
    lute = magic_lute.build("Lute", loc=(0.62, 0, base))
    lute.rotation_euler = (0, math.radians(8), math.radians(-40))


def build_plinth():
    stone = noisy_mat("PlinthStone", (0.02, 0.02, 0.03), (0.06, 0.06, 0.08), 7, 0.8)
    trim = mat("PlinthTrim", (0.8, 0.6, 0.3), 0.3, 1.0)
    lathe("Plinth", [(0.0, 0.0), (1.3, 0.0), (1.3, PLINTH - 0.02), (1.25, PLINTH), (0.0, PLINTH)],
          (0, 0, 0), stone, segs=96)
    lathe("PlinthTrim", [(1.302, PLINTH - 0.03), (1.315, PLINTH - 0.025), (1.315, PLINTH - 0.015),
                         (1.302, PLINTH - 0.01)], (0, 0, 0), trim, segs=96)


def setup_world_and_camera(samples, shot):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 1.0
    # vertical gradient: deep navy at the floor, a little lighter overhead
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.004, 0.005, 0.012, 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.03, 0.04, 0.08, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])

    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    bpy.context.object.data.materials.append(mat("Floor", (0.01, 0.012, 0.02), 0.5))

    # key from the front left, cool rim from behind, soft fill from the right
    for name, kind, energy, loc, color, size in [
            ("Key", "AREA", 110, (-2.5, -3.0, 3.2), (1.0, 0.95, 0.88), 2.0),
            ("Rim", "AREA", 260, (1.5, 2.8, 2.6), (0.55, 0.65, 1.0), 2.5),
            ("Fill", "AREA", 30, (3.2, -1.8, 1.2), (0.9, 0.85, 1.0), 2.0)]:
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        ld.size = size
        o = bpy.data.objects.new(name, ld)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(o)

    cam_loc, target, lens, (rx, ry) = SHOTS[shot]
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.transmission_bounces = 16
    scene.cycles.max_bounces = 16
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out, samples, shot, res, blend_out = None, 128, "all", 100, None
    for i, a in enumerate(argv):
        if a == "--render":
            out = argv[i + 1]
        elif a == "--samples":
            samples = int(argv[i + 1])
        elif a == "--shot":
            shot = argv[i + 1]
        elif a == "--res":
            res = int(argv[i + 1])
        elif a == "--save":
            blend_out = argv[i + 1]

    reset()
    build_plinth()
    build_props()
    setup_world_and_camera(samples, shot)
    bpy.context.scene.render.resolution_percentage = res
    if blend_out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend_out))
    if out:
        bpy.context.scene.render.filepath = os.path.abspath(out)
        bpy.ops.render.render(write_still=True)


main()
