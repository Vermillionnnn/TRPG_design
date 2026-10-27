"""Plain wooden crate with a dark slat band around the middle.

    crate.build("Crate", loc=(1, 2, 0), rot_z=0.3, size=0.4)

Origin is under the crate.
"""
from assets.lib import box, group, material


def build(name="Crate", loc=(0, 0, 0), rot_z=0.0, *, size=0.45):
    """size: edge length in metres."""
    s = size
    parts = [box(name + "Body", (s, s, s), (0, 0, s / 2), material("wood"), bev=0.02),
             box(name + "Slat", (s + 0.01, s + 0.01, 0.06), (0, 0, s / 2), material("darkwood"), bev=0.01)]
    return group(name, parts, loc, rot_z)
