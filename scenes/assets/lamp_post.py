"""Wrought-iron street lamp: stone footing, turned iron post with collars, a finial, and
scrolled shepherd's-crook arms each hanging a lantern (flame or arcane glow).

    lamp_post.build("Lamp", loc=(2, 3, 0))                         # two arms, warm flame
    lamp_post.build("Lamp", loc=(2, 3, 0), arms=1, glow="arcane_cyan", color=(0.4, 0.8, 1.0))

Origin is under the footing; with one arm the lantern hangs toward local -y.
"""
import math

from assets import lantern
from assets.lib import box, curve, group, lathe, material, sphere


def build(name="LampPost", loc=(0, 0, 0), rot_z=0.0, *, height=2.4, arms=2, glow="flame",
          color=(1.0, 0.62, 0.28), energy=35):
    """height of the post (m); arms: 1 or 2 lanterns; glow / color / energy go to each lantern."""
    iron, h = material("iron"), height
    parts = [box(name + "Footing", (0.3, 0.3, 0.18), (0, 0, 0.09), material("stone"), bev=0.03),
             lathe(name + "Post", [(0.09, 0.18), (0.09, 0.26), (0.06, 0.32), (0.045, 0.45), (0.035, h - 0.25),
                                   (0.055, h - 0.2), (0.055, h - 0.14), (0.035, h - 0.1), (0.035, h + 0.02),
                                   (0.05, h + 0.06), (0.0, h + 0.12)], (0, 0, 0), iron, segs=16),
             sphere(name + "Knob", 0.035, (0, 0, h + 0.15), iron, segs=10),
             lathe(name + "Finial", [(0.0, h + 0.17), (0.02, h + 0.2), (0.0, h + 0.34)], (0, 0, 0), iron,
                   segs=8)]
    for k in range(arms):
        d = -1 if (k == 0) else 1           # first arm toward -y, second toward +y
        # crook: out from the post, curling down at the tip, with a little scroll underneath
        arm = [(0, 0, h - 0.18), (0, d * 0.2, h - 0.12), (0, d * 0.42, h - 0.06), (0, d * 0.55, h - 0.12),
               (0, d * 0.56, h - 0.22)]
        parts.append(curve(f"{name}Arm{k}", arm, 0.016, iron))
        scroll = [(0, d * 0.04, h - 0.42)]
        for j in range(9):
            a = j / 8 * 1.6 * math.pi
            r = 0.09 * (1 - j / 12)
            scroll.append((0, d * (0.14 + r * math.sin(a)), h - 0.3 + r * math.cos(a) - 0.04))
        parts.append(curve(f"{name}Scroll{k}", scroll, 0.01, iron))
        parts.append(lantern.build(f"{name}Lantern{k}", (0, d * 0.56, h - 0.58), energy=energy, color=color,
                                   glow=glow))
    return group(name, parts, loc, rot_z)
