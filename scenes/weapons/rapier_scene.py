"""The crystal rapier on its own, lying level with the blade pointing right and the
knuckle bow hanging below, floating in front of a dark teal backdrop.

Run with:  python3 scenes/weapons/rapier_scene.py [--render out.png] [--samples N]
           [--shot full|hilt|pommel] [--res percent] [--save out.blend]
Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P scenes/weapons/rapier_scene.py -- --render out.png

Units are metres. The sword lies along +X centred on the origin, flat side to -Y
(the camera). Lighting is a studio set of long strip softboxes: one overhead to
run a clean highlight down the gold and the glass, two behind for the blade's edges,
a low cool fill, and a small warm spot on the hilt.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from assets import gem_rapier  # noqa: E402
from assets.lib import reset  # noqa: E402

LENGTH = 1.745                     # the asset's default length
HILT_X = -LENGTH / 2               # pommel tip; the guard sits HILT mm to its right

# shot: (camera location, look-at point, focal length, resolution)
SHOTS = {
    "full": ((0.0, -4.6, 0.3), (0.0, 0.0, -0.02), 85, (2400, 1000)),
    "hilt": ((-0.42, -1.05, 0.22), (-0.6, 0.0, -0.03), 60, (1600, 1000)),
    "pommel": ((-0.72, -0.42, 0.1), (-0.83, 0.0, -0.01), 60, (1200, 1000)),
}

# backdrop: a soft lighter pool behind the sword fading to near black at the frame edges
POOL = (0.045, 0.11, 0.12)
EDGE = (0.004, 0.012, 0.016)


def build_sword():
    r = gem_rapier.build("Rapier", loc=(HILT_X, 0, 0))
    r.rotation_euler = (0, math.radians(90), 0)      # blade to +X, knuckle bow below


def backdrop(world):
    """The camera sees a radial vignette; everything else is lit by a dim neutral world."""
    world.use_nodes = True
    nt = world.node_tree
    out = nt.nodes["World Output"]
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    centre = nt.nodes.new("ShaderNodeVectorMath")
    centre.operation = "SUBTRACT"
    centre.inputs[1].default_value = (0.5, 0.5, 0)
    squash = nt.nodes.new("ShaderNodeVectorMath")     # wider than tall, to suit the long frame
    squash.operation = "MULTIPLY"
    squash.inputs[1].default_value = (1.0, 1.6, 0)
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*POOL, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*EDGE, 1)
    nt.links.new(tc.outputs["Window"], centre.inputs[0])
    nt.links.new(centre.outputs["Vector"], squash.inputs[0])
    nt.links.new(squash.outputs["Vector"], dist.inputs[0])
    nt.links.new(dist.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    ambient = nt.nodes.new("ShaderNodeBackground")
    ambient.inputs["Color"].default_value = (0.05, 0.06, 0.07, 1)
    ambient.inputs["Strength"].default_value = 0.5
    path = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(ambient.outputs["Background"], mix.inputs[1])
    nt.links.new(bg.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def strip(scene, name, loc, target, energy, color, size, size_y, camera_visible=False):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size, size_y
    ld.energy = energy
    ld.color = color
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = camera_visible
    scene.collection.objects.link(o)
    return o


def setup_world_and_camera(samples, shot):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    backdrop(world)

    # long softboxes lying along the sword (their long side along X)
    strip(scene, "Top", (0.0, -0.25, 1.4), (0.0, 0.0, 0.0), 110, (1.0, 0.97, 0.92), 2.6, 0.5)
    strip(scene, "RimHigh", (0.0, 1.3, 0.75), (0.0, 0.0, 0.0), 220, (0.75, 0.9, 1.0), 2.6, 0.25)
    strip(scene, "RimLow", (0.0, 1.2, -0.65), (0.0, 0.0, 0.0), 140, (0.85, 0.75, 1.0), 2.6, 0.25)
    strip(scene, "Fill", (0.0, -2.2, -0.6), (0.0, 0.0, 0.0), 60, (0.7, 0.85, 1.0), 2.6, 0.8)
    spot = bpy.data.lights.new("HiltSpot", "SPOT")    # warm accent on the gold hilt
    spot.energy = 45
    spot.color = (1.0, 0.8, 0.55)
    spot.spot_size = math.radians(28)
    spot.spot_blend = 0.6
    spot.shadow_soft_size = 0.15
    so = bpy.data.objects.new("HiltSpot", spot)
    so.location = (-0.9, -1.4, 0.9)
    so.rotation_euler = (Vector((HILT_X + 0.3, 0, 0)) - so.location).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(so)

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
    out, samples, shot, res, blend_out = None, 128, "full", 100, None
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
    build_sword()
    setup_world_and_camera(samples, shot)
    bpy.context.scene.render.resolution_percentage = res
    if blend_out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend_out))
    if out:
        bpy.context.scene.render.filepath = os.path.abspath(out)
        bpy.ops.render.render(write_still=True)


main()
