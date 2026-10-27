"""Iron cauldron on three legs with a glowing brew, rising bubbles and a light.

    cauldron.build("Cauldron", loc=(3.5, 3, 0.05), brew=(0.2, 0.9, 0.3))

Origin is on the floor under the cauldron. Bubbles are named <name>Bubble<k>
so a scene can animate them.
"""
import math
import random

from assets.lib import cyl, group, mat, material, point_light, sphere, torus

BREW = (0.45, 0.05, 1.0)


def build(name="Cauldron", loc=(0, 0, 0), rot_z=0.0, *, brew=BREW, bubbles=9, light=True, rng=None):
    """brew: (r, g, b) glow colour of the potion. rng: random source for bubbles (default seed 0)."""
    rng = rng or random.Random(0)
    iron = material("iron")
    if tuple(brew) == BREW:
        liquid = mat("CauldronPurple", (0.35, 0.05, 0.8), 0.2, emit=BREW, emit_strength=1.8)
        glow = (0.65, 0.25, 1.0)
    else:
        liquid = mat(name + "Brew", tuple(brew), 0.2, emit=tuple(brew), emit_strength=1.8)
        glow = tuple(brew)
    parts = [sphere(name + "Pot", 0.3, (0, 0, 0.31), iron, scale=(1, 1, 0.8), segs=24),
             torus(name + "Rim", 0.25, 0.03, (0, 0, 0.51), iron),
             cyl(name + "Liquid", 0.24, 0.02, (0, 0, 0.5), liquid, verts=32)]
    for k in range(3):
        a = k * 2 * math.pi / 3
        parts.append(cyl(f"{name}Leg{k}", 0.025, 0.15, (0.2 * math.cos(a), 0.2 * math.sin(a), 0.05),
                         iron, verts=8))
    for k in range(bubbles):
        parts.append(sphere(f"{name}Bubble{k}", rng.uniform(0.02, 0.045),
                            (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15),
                             0.53 + rng.uniform(0, 0.35) * (k % 3)), liquid, segs=10))
    if light:
        parts.append(point_light(name + "Glow", (0, 0, 0.75), 20, glow, radius=0.15))
    return group(name, parts, loc, rot_z)
