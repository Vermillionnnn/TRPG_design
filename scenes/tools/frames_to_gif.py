"""Turn a folder of rendered PNG frames into a looping GIF, using only what
ships with Blender (numpy + the image loader), so it runs where ffmpeg/PIL
are not installed:

    scenes/blender.sh scenes/tools/frames_to_gif.py out/frames out/loop.gif --fps 8

Options: --fps N (default 8), --colors N (default 255; one more index is kept
for transparency), --dither 0|1 (default 1, ordered 4x4 Bayer).

One palette is shared by all frames (median cut over samples from every
frame). After the first frame, pixels that did not change are written as
transparent and each frame is cropped to the changed area, which keeps the
file small for mostly-still scenes.
"""
import os
import struct
import sys

import bpy
import numpy as np

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5


def load(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    rgb = px.reshape(h, w, 4)[::-1, :, :3]         # Blender rows run bottom-up
    return np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)


def median_cut(samples, n):
    boxes = [samples]
    while len(boxes) < n:
        i = max(range(len(boxes)), key=lambda k: np.ptp(boxes[k], axis=0).max() if len(boxes[k]) > 1 else -1)
        b = boxes[i]
        if len(b) < 2:
            break
        ch = int(np.argmax(np.ptp(b, axis=0)))
        b = b[b[:, ch].argsort()]
        boxes[i:i + 1] = [b[:len(b) // 2], b[len(b) // 2:]]
    return np.array([b.mean(axis=0) for b in boxes]).astype(np.uint8)


def quantize(frame, palette, dither):
    f = frame.astype(np.float32)
    if dither:
        h, w, _ = f.shape
        f += np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w, None] * 12
    # nearest palette entry through a 5-bit-per-channel lookup table
    q = np.clip(f, 0, 255).astype(np.int32) >> 3
    keys = (q[..., 0] << 10) | (q[..., 1] << 5) | q[..., 2]
    grid = np.stack(np.meshgrid(np.arange(32), np.arange(32), np.arange(32), indexing="ij"), -1)
    centres = grid.reshape(-1, 3).astype(np.float32) * 8 + 4
    lut = np.empty(32768, np.uint8)
    pal = palette.astype(np.float32)
    for s in range(0, 32768, 4096):
        d = ((centres[s:s + 4096, None, :] - pal[None]) ** 2).sum(-1)
        lut[s:s + 4096] = d.argmin(1)
    return lut[keys]


def lzw(indices, min_size=8):
    """GIF-flavoured LZW of a flat sequence of palette indices."""
    clear, eoi = 1 << min_size, (1 << min_size) + 1
    out = bytearray()
    acc = nbits = 0

    def emit(code, size):
        nonlocal acc, nbits
        acc |= code << nbits
        nbits += size
        while nbits >= 8:
            out.append(acc & 0xFF)
            acc >>= 8
            nbits -= 8

    size, nxt, table = min_size + 1, eoi + 1, {}
    emit(clear, size)
    data = indices.tobytes()
    w = data[0]
    for k in data[1:]:
        key = (w << 8) | k
        code = table.get(key)
        if code is not None:
            w = code
            continue
        emit(w, size)
        if nxt < 4096:
            table[key] = nxt
            nxt += 1
            if nxt > (1 << size) and size < 12:
                size += 1
        else:
            emit(clear, size)
            size, nxt, table = min_size + 1, eoi + 1, {}
        w = k
    emit(w, size)
    emit(eoi, size)
    if nbits:
        out.append(acc & 0xFF)
    return bytes(out)


def blocks(data):
    return b"".join(bytes([len(data[i:i + 255])]) + data[i:i + 255] for i in range(0, len(data), 255)) + b"\0"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    src, dst = argv[0], argv[1]
    fps, colors, dither = 8, 255, 1
    for i, a in enumerate(argv):
        if a == "--fps":
            fps = int(argv[i + 1])
        elif a == "--colors":
            colors = int(argv[i + 1])
        elif a == "--dither":
            dither = int(argv[i + 1])
    names = sorted(f for f in os.listdir(src) if f.lower().endswith(".png"))
    frames = [load(os.path.abspath(os.path.join(src, f))) for f in names]
    h, w, _ = frames[0].shape
    rng = np.random.default_rng(0)
    samples = np.concatenate([f.reshape(-1, 3)[rng.choice(w * h, 20000, replace=False)] for f in frames])
    palette = median_cut(samples, colors)
    transparent = len(palette)
    table = np.zeros((256, 3), np.uint8)
    table[:len(palette)] = palette

    gif = bytearray(b"GIF89a" + struct.pack("<HHBBB", w, h, 0xF7, 0, 0) + table.tobytes())
    gif += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"       # loop forever
    delay = round(100 / fps)
    prev = None
    for f in frames:
        idx = quantize(f, palette, dither)
        x0, y0, x1, y1 = 0, 0, w, h
        if prev is not None:
            changed = idx != prev
            if changed.any():
                ys, xs = np.nonzero(changed)
                x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            else:
                x0, y0, x1, y1 = 0, 0, 1, 1
            out = np.where(changed, idx, transparent).astype(np.uint8)[y0:y1, x0:x1]
            prev = np.where(changed, idx, prev)
        else:
            out = idx
            prev = idx
        gif += b"\x21\xF9\x04" + struct.pack("<BHBB", 0x05 if prev is not None else 0x04, delay, transparent, 0)
        gif += b"\x2C" + struct.pack("<HHHHB", x0, y0, x1 - x0, y1 - y0, 0)
        gif += b"\x08" + blocks(lzw(np.ascontiguousarray(out).ravel()))
    gif += b"\x3B"
    with open(dst, "wb") as fh:
        fh.write(gif)
    print(f"wrote {dst}: {len(frames)} frames, {w}x{h}, {fps} fps, {len(gif) / 1e6:.1f} MB")


main()
