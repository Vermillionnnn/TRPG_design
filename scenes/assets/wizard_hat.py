"""Pointed wizard hat with a gold band and little gold stars, as if set down on a table.

    wizard_hat.build("Hat", loc=(2.7, 2.1, 0.83), color=(0.4, 0.05, 0.1))

Origin is at the centre of the brim.
"""
import math

from assets.lib import cone, cyl, group, mat, material, sphere

COLOR = (0.12, 0.08, 0.55)


def build(name="WizardHat", loc=(0, 0, 0), rot_z=0.0, *, color=COLOR, height=0.48, brim=0.24):
    """color: (r, g, b) felt colour. height of the cone and brim radius in metres."""
    felt = mat("HatBlue" if tuple(color) == COLOR else name + "Felt", tuple(color), 0.8)
    gold = material("gold")
    parts = [cyl(name + "Brim", brim, 0.015, (0, 0, 0), felt, verts=32),
             cone(name + "Cone", 0.14, 0.01, height, (0.03, -0.03, height / 2 - 0.01), felt,
                  rot=(math.radians(-12), math.radians(14), 0), verts=24),
             cyl(name + "Band", 0.135, 0.035, (0, 0, 0.03), gold, verts=24)]
    for k in range(4):
        a = k * 1.6
        parts.append(sphere(f"{name}Star{k}", 0.012, (0.09 * math.cos(a), 0.09 * math.sin(a) - 0.02,
                                                      0.12 + k * 0.07), gold, segs=6))
    return group(name, parts, loc, rot_z)
