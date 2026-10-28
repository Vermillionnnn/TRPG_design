"""The crystal rapier on its own, lying level with the blade pointing right and the
knuckle bow hanging below, floating in front of a dark wine-red backdrop.

Run with:  python3 scenes/weapons/rapier_scene.py [--render out.png] [--samples N]
           [--shot full|hilt|pommel] [--length metres] [--res percent] [--save out.blend]
           [--anim frames_dir [--frames N]]   (one turn about the blade's axis in N frames,
                                               default 96, to play at 8 fps)
Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P scenes/weapons/rapier_scene.py -- --render out.png

Units are metres. The sword (default length unless --length) lies along +X centred on the origin, flat side to -Y
(the camera). Lighting is a warm studio set of long strip softboxes: one overhead to
run a clean highlight down the gold and the glass, amber and rose rims behind for the
blade's edges, a low fill, and a small amber spot on the hilt.
"""
import inspect
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from assets import gem_rapier  # noqa: E402
from assets.lib import reset  # noqa: E402

# backdrop: a soft wine-red pool behind the sword fading to near black at the frame edges
POOL = (0.13, 0.012, 0.03)
EDGE = (0.012, 0.0015, 0.004)


def shots(length):
    """shot: (camera location, look-at point, focal length, resolution). The sword lies centred
    on the origin, so the pommel tip is at x = -length / 2."""
    p = -length / 2
    d = length * 1.12 * 85 / 36             # frames the whole sword with a little margin
    return {
        "full": ((0.0, -d, d * 0.065), (0.0, 0.0, -0.02), 85, (2400, 1000)),
        "hilt": ((p + 0.52, -1.15, 0.24), (p + 0.34, 0.0, -0.03), 60, (2400, 1500)),
        "pommel": ((p + 0.15, -0.42, 0.1), (p + 0.04, 0.0, -0.01), 60, (1200, 1000)),
    }


SPIN_FRAMES = 96                   # the spin: one full turn in 96 held poses ...
SPIN_FPS = 8                       # ... shown at 8 fps (12 s a turn), like stop motion


def build_sword(length, spin=0):
    """The sword hangs from an empty at the origin; with spin = N frames, the empty turns about
    the blade's own axis (+X), 360 / N degrees a frame, back to the start on the loop."""
    pivot = bpy.data.objects.new("Spin", None)
    bpy.context.collection.objects.link(pivot)
    r = gem_rapier.build("Rapier", loc=(-length / 2, 0, 0), length=length, light=False)
    r.rotation_euler = (0, math.radians(90), 0)      # blade to +X, knuckle bow below
    r.parent = pivot
    if spin:
        scene = bpy.context.scene
        scene.frame_start, scene.frame_end = 1, spin
        scene.render.fps = SPIN_FPS
        for f in range(spin):
            pivot.rotation_euler = (2 * math.pi * f / spin, 0, 0)
            pivot.keyframe_insert("rotation_euler", frame=f + 1)


def backdrop(world):
    """What each kind of ray sees: the camera sees a radial wine-red vignette and light passing
    through the glass the vignette's middle colour, so the clear blade shows the backdrop; reflections see a warm
    studio sky with a bright band overhead, for the facets and the gold to catch; diffuse light
    gets a dim neutral fill."""
    world.use_nodes = True
    nt = world.node_tree
    L = nt.links.new
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
    L(tc.outputs["Window"], centre.inputs[0])
    L(centre.outputs["Vector"], squash.inputs[0])
    L(squash.outputs["Vector"], dist.inputs[0])
    L(dist.outputs["Value"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], bg.inputs["Color"])

    # studio sky for reflections, by height of the ray direction (-1 straight down .. 1 straight up)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Generated"], sep.inputs["Vector"])
    up = nt.nodes.new("ShaderNodeMapRange")
    up.inputs["From Min"].default_value = -1.0
    L(sep.outputs["Z"], up.inputs["Value"])
    sky = nt.nodes.new("ShaderNodeValToRGB")
    cr = sky.color_ramp
    cr.elements[0].color = (0.004, 0.001, 0.002, 1)
    cr.elements[1].color = (1.2, 0.9, 0.66, 1)
    # bands at the heights the blade's facets reflect: bright overhead for the upper facets,
    # a dim rose glow low down for the lower ones (glass only reflects about a tenth at this angle)
    for pos, col in ((0.03, (0.05, 0.012, 0.02)), (0.08, (0.9, 0.35, 0.3)), (0.14, (0.05, 0.012, 0.02)),
                     (0.45, (0.03, 0.006, 0.01)), (0.6, (0.12, 0.05, 0.04)), (0.78, (1.0, 0.7, 0.5)),
                     (0.86, (8.0, 6.3, 4.8)), (0.94, (5.0, 3.9, 2.9))):
        cr.elements.new(pos).color = (*col, 1)
    L(up.outputs["Result"], sky.inputs["Fac"])
    studio = nt.nodes.new("ShaderNodeBackground")
    L(sky.outputs["Color"], studio.inputs["Color"])
    ambient = nt.nodes.new("ShaderNodeBackground")
    ambient.inputs["Color"].default_value = (0.07, 0.05, 0.045, 1)
    ambient.inputs["Strength"].default_value = 0.5
    behind = nt.nodes.new("ShaderNodeBackground")    # seen through the glass: the vignette's middle
    behind.inputs["Color"].default_value = (*POOL, 1)

    path = nt.nodes.new("ShaderNodeLightPath")

    def pick(fac, no, yes):
        m = nt.nodes.new("ShaderNodeMixShader")
        L(path.outputs[fac], m.inputs["Fac"])
        L(no, m.inputs[1])
        L(yes, m.inputs[2])
        return m.outputs["Shader"]
    shader = pick("Is Glossy Ray", ambient.outputs["Background"], studio.outputs["Background"])
    shader = pick("Is Transmission Ray", shader, behind.outputs["Background"])
    shader = pick("Is Camera Ray", shader, bg.outputs["Background"])
    L(shader, out.inputs["Surface"])


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


def setup_world_and_camera(samples, shot, length):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    backdrop(world)

    # long softboxes lying along the sword (their long side along X), as long as the sword
    k = length / 1.745                # light output grows with the sword
    w = 1.5 * length
    strip(scene, "Top", (0.0, -0.25, 1.4), (0.0, 0.0, 0.0), 110 * k, (1.0, 0.86, 0.68), w, 0.5)
    strip(scene, "RimHigh", (0.0, 1.3, 0.75), (0.0, 0.0, 0.0), 220 * k, (1.0, 0.72, 0.45), w, 0.25)
    strip(scene, "RimLow", (0.0, 1.2, -0.65), (0.0, 0.0, 0.0), 140 * k, (1.0, 0.6, 0.55), w, 0.25)
    strip(scene, "Fill", (0.0, -2.2, -0.6), (0.0, 0.0, 0.0), 60 * k, (1.0, 0.82, 0.7), w, 0.8)
    spot = bpy.data.lights.new("HiltSpot", "SPOT")    # warm accent on the gold hilt
    spot.energy = 45
    spot.color = (1.0, 0.7, 0.4)
    spot.spot_size = math.radians(28)
    spot.spot_blend = 0.6
    spot.shadow_soft_size = 0.15
    so = bpy.data.objects.new("HiltSpot", spot)
    so.location = (-length / 2 - 0.03, -1.4, 0.9)
    so.rotation_euler = (Vector((-length / 2 + 0.3, 0, 0)) - so.location).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(so)

    cam_loc, target, lens, (rx, ry) = shots(length)[shot]
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
    out, samples, shot, res, blend_out, anim, frames = None, 128, "full", 100, None, None, SPIN_FRAMES
    length = inspect.signature(gem_rapier.build).parameters["length"].default
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
        elif a == "--length":
            length = float(argv[i + 1])
        elif a == "--anim":
            anim = argv[i + 1]
        elif a == "--frames":
            frames = int(argv[i + 1])

    reset()
    build_sword(length, spin=frames if anim else 0)
    setup_world_and_camera(samples, shot, length)
    bpy.context.scene.render.resolution_percentage = res
    if blend_out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend_out))
    if out:
        bpy.context.scene.render.filepath = os.path.abspath(out)
        bpy.ops.render.render(write_still=True)
    if anim:
        os.makedirs(anim, exist_ok=True)
        bpy.context.scene.render.filepath = os.path.join(os.path.abspath(anim), "frame_####")
        bpy.ops.render.render(animation=True)


main()
