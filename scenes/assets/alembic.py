"""Alchemist's alembic: round flask over a burner, a brass tube down to a small receiver.

    alembic.build("Alembic", loc=(0.3, 0.67, 0.805))

Origin is under the flask (on the burner); the receiver sits toward local -y.
"""
import math

from assets.lib import as_material, cyl, group, material, sphere


def build(name="Alembic", loc=(0, 0, 0), rot_z=0.0, *, flask="arcane_purple", receiver="arcane_green"):
    """flask / receiver: material, palette key or (r, g, b) for the glowing contents."""
    flask = as_material(flask, name + "FlaskGlass", 0.1)
    brass = material("brass")
    parts = [sphere(name + "Flask", 0.08, (0, 0, 0.08), flask, segs=16),
             cyl(name + "Neck", 0.018, 0.12, (0, 0, 0.2), flask, verts=10),
             cyl(name + "Tube", 0.008, 0.25, (0, -0.12, 0.22), brass, rot=(math.radians(-60), 0, 0), verts=8),
             sphere(name + "Receiver", 0.05, (0, -0.24, 0.05), as_material(receiver, name + "ReceiverGlass", 0.1),
                    segs=12),
             cyl(name + "Burner", 0.04, 0.04, (0, 0, 0), brass, verts=12)]
    return group(name, parts, loc, rot_z)
