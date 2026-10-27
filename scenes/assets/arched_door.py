"""Round-headed oak plank door in a timber frame: strap hinges with split ends,
nail heads, lock plate and ring pull, stone threshold and stop blocks, a carved
staff sigil on the lintel and (optionally) a candle sconce beside it.

    arched_door.build("Door", loc=(4.9, 0.97, 0), rot_z=math.radians(11.25) - math.pi / 2)

Origin is on the floor at the wall face under the middle of the door; the
room is toward local -y. The sconce candle's light is <name>SconceCandleLight.
"""
import math

from assets import candle
from assets.lib import (arch_slab, as_material, box, cyl, group, mat, material, noisy_mat,
                        point_light, shell, sphere, torus)


def build(name="ArchedDoor", loc=(0, 0, 0), rot_z=0.0, *, width=1.1, height=1.85, frame="darkwood",
          sigil="pewter", sconce=True):
    """height is the straight part of the leaf; the head adds width / 2 above it."""
    w, h = width, height
    frame = as_material(frame, name + "Frame", 0.55)
    iron, stone = material("iron"), material("stone")
    leaf = noisy_mat("DoorOak", (0.13, 0.07, 0.03), (0.26, 0.15, 0.07), 5, 0.6, stretch=(10, 1, 1))
    seam = mat("DoorSeam", (0.02, 0.012, 0.008), 1)
    reveal = mat("Reveal", (0.01, 0.008, 0.006), 1)
    p = [arch_slab(name + "Reveal", w + 0.06, h, 0.04, reveal, (0, 0.05, 0.08)),
         box(name + "Threshold", (w + 0.5, 0.42, 0.1), (0, -0.12, 0.09), stone, bev=0.02),
         arch_slab(name + "Leaf", w, h, 0.07, leaf, (0, -0.02, 0.14))]
    for k in range(1, 6):
        px = -w / 2 + k * w / 6
        top = h + math.sqrt(max((w / 2) ** 2 - px ** 2, 0)) - 0.03
        p.append(box(f"{name}Seam{k}", (0.008, 0.01, top), (px, -0.058, 0.14 + top / 2), seam, bev=0))
    # strap hinges with forked ends, nails and pintles
    for zz in (0.45, 1.6):
        p.append(box(f"{name}Strap{zz}", (w * 0.86, 0.012, 0.07), (-w * 0.07, -0.062, 0.14 + zz), iron,
                     bev=0.004))
        for sgn in (-1, 1):
            p.append(box(f"{name}StrapFork{zz}{sgn}", (0.14, 0.012, 0.03),
                         (w * 0.42 - 0.02, -0.062, 0.14 + zz + sgn * 0.03), iron,
                         rot=(0, sgn * math.radians(25), 0), bev=0.003))
        for k in range(6):
            p.append(sphere(f"{name}Nail{zz}_{k}", 0.012, (-w / 2 + 0.08 + k * 0.15, -0.07, 0.14 + zz),
                            iron, segs=8))
        p.append(cyl(f"{name}Pintle{zz}", 0.025, 0.12, (-w / 2 - 0.02, -0.06, 0.14 + zz), iron, verts=10))
    # lock plate, keyhole and ring pull
    p += [box(name + "LockPlate", (0.1, 0.012, 0.18), (w * 0.36, -0.065, 1.15), iron, bev=0.004),
          box(name + "Keyhole", (0.015, 0.014, 0.04), (w * 0.36, -0.068, 1.1), mat("Keyhole", (0, 0, 0), 1),
              bev=0),
          torus(name + "Ring", 0.07, 0.011, (w * 0.36, -0.08, 1.2), iron, rot=(math.pi / 2, 0, 0)),
          sphere(name + "RingBoss", 0.025, (w * 0.36, -0.075, 1.27), iron, segs=10)]
    # timber frame: jambs, round head, lintel and keystone, stone stop blocks
    for sx in (-1, 1):
        p.append(box(f"{name}Jamb{sx}", (0.16, 0.2, h + 0.14), (sx * (w / 2 + 0.08), -0.02, (h + 0.14) / 2 + 0.06),
                     frame, bev=0.012))
        p.append(box(f"{name}StopBlock{sx}", (0.22, 0.24, 0.3), (sx * (w / 2 + 0.08), -0.03, 0.2), stone,
                     bev=0.02))
    top = 0.14 + h + w / 2
    p += [shell(name + "Head", w / 2 + 0.16, w / 2, -0.1, 0.1, frame, arc=(0, math.pi), segs=40,
                loc=(0, -0.02, 0.14 + h), rot=(math.pi / 2, 0, 0)),
          box(name + "Lintel", (w + 0.6, 0.22, 0.2), (0, -0.02, top + 0.24), frame, bev=0.015),
          box(name + "Keystone", (0.16, 0.06, 0.22), (0, -0.11, top + 0.06), frame, bev=0.01)]
    if sigil:
        p.append(box(name + "Sigil", (0.03, 0.02, 0.16), (0, -0.14, top + 0.24),
                     as_material(sigil, name + "SigilMat", 0.4), rot=(0, math.radians(20), 0), bev=0))
    if sconce:
        sx = -(w / 2 + 0.45)
        p += [box(name + "SconcePlate", (0.12, 0.03, 0.22), (sx, 0.0, 1.75), iron, bev=0.005),
              box(name + "SconceArm", (0.03, 0.18, 0.03), (sx, -0.1, 1.72), iron, bev=0),
              cyl(name + "SconceCup", 0.05, 0.04, (sx, -0.19, 1.74), iron, verts=12),
              candle.build(name + "SconceCandle", (sx, -0.19, 1.76), height=0.16, light=False),
              point_light(name + "SconceCandleLight", (sx, -0.19, 2.0), 30, (1.0, 0.6, 0.25), radius=0.02)]
    return group(name, p, loc, rot_z)
