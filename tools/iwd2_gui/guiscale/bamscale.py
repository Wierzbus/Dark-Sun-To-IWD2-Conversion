"""Skalowanie zwyklej grafiki BAM o czynnik s (Lanczos na RGBA z premultiplikacja, wspolna paleta 255 kolorow, alfa binarna)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from guiscale.bamio import Bam, Frame


def _to_rgba(f: Frame, pal: list[int], tr: int) -> Image.Image:
    arr = np.zeros((f.h, f.w, 4), np.uint8)
    p = np.frombuffer(f.pix, np.uint8).reshape(f.h, f.w) if f.w * f.h else np.zeros((0, 0), np.uint8)
    lut = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255, 255] for c in pal], np.uint8)
    lut[tr, 3] = 0
    if f.w * f.h:
        arr[:] = lut[p]
    return Image.fromarray(arr, "RGBA")


def scale_bam(b: Bam, s: float) -> Bam:
    # paleta w pliku: dword LE = B,G,R,A -> (c>>16)&255 = R tylko gdy zapis 0x00RRGGBB; plik trzyma B,G,R,A => dword = A<<24|R<<16|G<<8|B
    scaled: list[Image.Image] = []
    for f in b.frames:
        im = _to_rgba(f, b.palette, b.transp)
        nw, nh = max(1, round(f.w * s)), max(1, round(f.h * s))
        a = np.asarray(im, np.float32)
        al = a[..., 3:4] / 255.0
        pm = Image.fromarray((np.concatenate([a[..., :3] * al, a[..., 3:4]], axis=2)).clip(0, 255).astype(np.uint8), "RGBA")
        r = np.asarray(pm.resize((nw, nh), Image.Resampling.LANCZOS), np.float32)
        ra = r[..., 3:4] / 255.0
        rgb = np.where(ra > 0.02, r[..., :3] / np.maximum(ra, 0.02), 0).clip(0, 255)
        out = np.concatenate([rgb, (ra > 0.5) * 255.0], axis=2).astype(np.uint8)
        scaled.append(Image.fromarray(out, "RGBA"))
    # wspolna paleta: mozaika opaque pikseli
    px = [np.asarray(i).reshape(-1, 4) for i in scaled]
    allp = np.concatenate(px) if px else np.zeros((0, 4), np.uint8)
    opaque = allp[allp[:, 3] > 0][:, :3]
    pal = [0x0000FF00] + [0] * 255
    if len(opaque):
        n = int(min(len(opaque), 400000))
        sel = opaque[np.linspace(0, len(opaque) - 1, n).astype(int)]
        side = int(np.ceil(np.sqrt(n)))
        mosaic = np.zeros((side * side, 3), np.uint8)
        mosaic[:n] = sel
        q = Image.fromarray(mosaic.reshape(side, side, 3), "RGB").quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pp = (q.getpalette() or [])[:765]
        pp += [0] * (765 - len(pp))
        for k in range(255):
            pal[k + 1] = (pp[3 * k + 2]) | (pp[3 * k + 1] << 8) | (pp[3 * k] << 16)     # B | G<<8 | R<<16 (bajty B,G,R,0)
        palimg = Image.new("P", (1, 1))
        palimg.putpalette(pp + pp[-3:])
    frames = []
    for f, im in zip(b.frames, scaled):
        arr = np.asarray(im)
        h, w = arr.shape[:2]
        if len(opaque):
            q = Image.fromarray(arr[..., :3], "RGB").quantize(palette=palimg, dither=Image.Dither.NONE)
            idx = np.minimum(np.asarray(q, np.uint8).astype(np.int32) + 1, 255)
        else:
            idx = np.zeros((h, w), np.int32)
        idx[arr[..., 3] == 0] = 0
        frames.append(Frame(w, h, round(f.cx * s), round(f.cy * s), idx.astype(np.uint8).tobytes()))
    return Bam(frames, b.cycles, pal, 0)
