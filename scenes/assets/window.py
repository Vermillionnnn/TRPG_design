"""Wall window: glowing night-sky pane, cross frame, sill, and an optional moonlight.

    window.build("Window", loc=(3.35, 3.95, 1.95))

Origin is at the centre of the pane, which lies in the wall; the room side is -y.
"""
import math

import bpy

from assets.lib import box, group, material


def build(name="Window", loc=(0, 0, 0), rot_z=0.0, *, width=0.55, height=0.75, light=True):
    """width / height of the glass in metres. light adds a cool area light shining into the room."""
    dark = material("darkwood")
    parts = [box(name + "Glass", (width, 0.05, height), (0, 0, 0), material("window"), bev=0),
             box(name + "FrameV", (0.05, 0.08, height + 0.05), (0, -0.03, 0), dark),
             box(name + "FrameH", (width + 0.05, 0.08, 0.05), (0, -0.03, 0), dark)]
    for sx in (-1, 1):
        parts.append(box(f"{name}Side{sx}", (0.06, 0.1, height + 0.1), (sx * (width / 2 + 0.025), -0.03, 0), dark))
    parts.append(box(name + "Sill", (width + 0.2, 0.2, 0.06), (0, -0.07, -(height / 2 + 0.045)), dark))
    parts.append(box(name + "Top", (width + 0.15, 0.1, 0.06), (0, -0.03, height / 2 + 0.045), dark))
    if light:
        ld = bpy.data.lights.new(name + "Moon", "AREA")
        ld.energy = 30
        ld.color = (0.5, 0.65, 1.0)
        ld.size = 0.6
        o = bpy.data.objects.new(name + "Moon", ld)
        o.location = (0, -0.15, 0)
        o.rotation_euler = (math.radians(-70), 0, 0)
        bpy.context.collection.objects.link(o)
        parts.append(o)
    return group(name, parts, loc, rot_z)
