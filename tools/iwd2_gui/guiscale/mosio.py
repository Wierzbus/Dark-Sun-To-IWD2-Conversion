"""MOS V1 / MOSC: odczyt do RGB (PIL) i zapis (bloki 64x64, paleta na blok)."""
from __future__ import annotations

import struct
import zlib

from PIL import Image


def read_mos(data: bytes) -> Image.Image:
    if data[:4] == b"MOSC":
        data = zlib.decompress(data[12:])
    if data[:8] != b"MOS V1  ":
        raise ValueError("to nie MOS V1")
    w, h, cols, rows, bs, po = struct.unpack_from("<HHHHII", data, 8)
    n = cols * rows
    offs = struct.unpack_from(f"<{n}I", data, po + 1024 * n)
    base = po + 1024 * n + 4 * n
    img = Image.new("RGB", (w, h))
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            bw, bh = min(bs, w - c * bs), min(bs, h - r * bs)
            pal = data[po + 1024 * i: po + 1024 * (i + 1)]
            flat = [x for k in range(256) for x in (pal[4 * k + 2], pal[4 * k + 1], pal[4 * k])]
            blk = Image.frombytes("P", (bw, bh), bytes(data[base + offs[i]: base + offs[i] + bw * bh]))
            blk.putpalette(flat)
            img.paste(blk.convert("RGB"), (c * bs, r * bs))
    return img


def write_mos(img: Image.Image, bs: int = 64) -> bytes:
    img = img.convert("RGB")
    w, h = img.size
    cols, rows = -(-w // bs), -(-h // bs)
    pals, blobs, offs, pos = [], [], [], 0
    for r in range(rows):
        for c in range(cols):
            blk = img.crop((c * bs, r * bs, min(w, (c + 1) * bs), min(h, (r + 1) * bs)))
            q = blk.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            p = (q.getpalette() or [])[:768]
            p += [0] * (768 - len(p))
            pals.append(b"".join(bytes((p[3 * k + 2], p[3 * k + 1], p[3 * k], 0)) for k in range(256)))
            px = q.tobytes()
            offs.append(pos)
            blobs.append(px)
            pos += len(px)
    hdr = b"MOS V1  " + struct.pack("<HHHHII", w, h, cols, rows, bs, 24)
    return hdr + b"".join(pals) + struct.pack(f"<{len(offs)}I", *offs) + b"".join(blobs)
