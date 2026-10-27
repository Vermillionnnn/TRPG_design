"""Cluster of glowing hexagonal crystals growing out of a rock, for magic gardens and caves.

    crystal_cluster.build("Crystals", loc=(2, 9, 0.08), glow="arcane_cyan")

Origin is under the rock.
"""
import math
import random

from assets.lib import as_material, blob, cone, cyl, group, material, point_light


def build(name="Crystals", loc=(0, 0, 0), rot_z=0.0, *, size=1.0, count=6, glow="arcane_cyan",
          light=True, rng=None):
    """size scales the whole cluster; count: number of crystals. glow: material, palette key
    or (r, g, b). rng: random source."""
    rng = rng or random.Random(6)
    glow = as_material(glow, name + "Glow", 0.1)
    s = size
    parts = [blob(name + "Rock", 0.18 * s, (0, 0, 0.04 * s), material("stone"), squash=0.5, strength=0.06 * s)]
    for k in range(count):
        a = k * 2 * math.pi / count + rng.uniform(-0.3, 0.3)
        tilt = 0.0 if k == 0 else rng.uniform(0.25, 0.6)
        ln = (0.42 if k == 0 else rng.uniform(0.16, 0.32)) * s
        r = (0.05 if k == 0 else rng.uniform(0.025, 0.04)) * s
        d = 0 if k == 0 else 0.06 * s
        ox, oy = d * math.cos(a), d * math.sin(a)
        # shaft centre and tip, along the tilted axis (an XYZ euler that turns +z onto it)
        ux, uy, uz = math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt)
        rot = (-math.asin(uy), math.atan2(ux, uz), 0)
        parts.append(cyl(f"{name}Shaft{k}", r, ln, (ox + ux * ln / 2, oy + uy * ln / 2, 0.03 * s + uz * ln / 2),
                         glow, rot=rot, verts=6, smooth=False))
        tl = r * 1.6
        parts.append(cone(f"{name}Tip{k}", r, 0.0, tl, (ox + ux * (ln + tl / 2), oy + uy * (ln + tl / 2),
                                                       0.03 * s + uz * (ln + tl / 2)),
                          glow, rot=rot, verts=6, smooth=False))
    if light:
        parts.append(point_light(name + "Light", (0, 0, 0.35 * s), 8, (0.4, 0.8, 1.0), radius=0.15))
    return group(name, parts, loc, rot_z)
