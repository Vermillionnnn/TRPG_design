"""Treasure chest: hollow box with iron bands, a hinged lid and a heap of gold.

    chest.build("Chest", loc=(1, 0.4, 0.05), rot_z=0.2, lid_angle=105)

Origin is on the floor under the chest centre; the lock is on the front (-y)
and the lid hinges along the back top edge.
"""
import math
import random

import bpy

from assets.lib import box, cyl, group, mat, material, sphere

W, D, H, T = 0.7, 0.45, 0.35, 0.04


def build(name="Chest", loc=(0, 0, 0), rot_z=0.0, *, lid_angle=105.0, gold=True, coins=45, rng=None):
    """lid_angle: 0 is closed, ~105 is open just past vertical (degrees).
    gold: fill with a gold mound, `coins` loose coins and two gems.
    rng: a random.Random (or the random module) for the coin scatter; default seed 0.
    """
    rng = rng or random.Random(0)
    wood, iron, brass = material("wood"), material("iron"), material("brass")
    inner = mat("ChestInner", (0.08, 0.04, 0.02), 0.8)
    parts = [
        box(name + "Floor", (W, D, T), (0, 0, T / 2), inner),
        box(name + "Front", (W, T, H), (0, -D / 2 + T / 2, H / 2), wood),
        box(name + "Back", (W, T, H), (0, D / 2 - T / 2, H / 2), wood),
        box(name + "SideL", (T, D - 2 * T, H), (-W / 2 + T / 2, 0, H / 2), wood),
        box(name + "SideR", (T, D - 2 * T, H), (W / 2 - T / 2, 0, H / 2), wood),
        box(name + "Lock", (0.08, 0.02, 0.1), (0, -D / 2 - 0.01, H - 0.08), brass, bev=0.005),
    ]
    # iron bands wrapping front, back and sides
    for i, d in enumerate((-0.22, 0.22)):
        parts.append(box(f"{name}BandF{i}", (0.05, 0.012, H + 0.01), (d, -D / 2 - 0.006, H / 2), iron, bev=0.003))
        parts.append(box(f"{name}BandB{i}", (0.05, 0.012, H + 0.01), (d, D / 2 + 0.006, H / 2), iron, bev=0.003))
    for sx in (-1, 1):
        parts.append(box(f"{name}BandS{sx}", (0.012, D + 0.02, 0.05), (sx * (W / 2 + 0.006), 0, H - 0.06), iron, bev=0.003))
    if gold:
        # a flattened mound with loose coins on top, below the rim
        g = material("gold")
        parts.append(sphere(name + "GoldMound", 0.3, (0, 0, H - 0.12), g, scale=(1.05, 0.62, 0.3), segs=20))
        for i in range(coins):
            x = rng.uniform(-0.27, 0.27)
            y = rng.uniform(-0.15, 0.15)
            z = H - 0.12 + 0.09 * max(0.0, 1 - (x / 0.32) ** 2 - (y / 0.2) ** 2) ** 0.5 + 0.005
            parts.append(cyl(f"{name}Coin{i}", 0.03, 0.008, (x, y, z), g,
                             rot=(rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0), verts=12))
        parts.append(sphere(name + "Gem", 0.05, (0.1, 0.0, H - 0.01), material("glass_potion_r"), segs=10))
        parts.append(sphere(name + "Gem2", 0.04, (-0.15, 0.05, H - 0.03), material("glass_potion_b"), segs=10))
    root = group(name, parts, loc, rot_z)

    hinge = bpy.data.objects.new(name + "Hinge", None)
    bpy.context.collection.objects.link(hinge)
    hinge.parent = root
    hinge.location = (0, D / 2, H)
    lid = [box(name + "Lid", (W, D, 0.06), (0, -D / 2, 0.03), wood),
           box(name + "LidInner", (W - 0.06, D - 0.06, 0.01), (0, -D / 2, -0.001), inner, bev=0)]
    for i, d in enumerate((-0.22, 0.22)):
        lid.append(box(f"{name}LidBand{i}", (0.05, D + 0.01, 0.012), (d, -D / 2, 0.066), iron, bev=0.003))
    for p in lid:
        p.parent = hinge
    hinge.rotation_euler = (math.radians(-lid_angle), 0, 0)
    return root
