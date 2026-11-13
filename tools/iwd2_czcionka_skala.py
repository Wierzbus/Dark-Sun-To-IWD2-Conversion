"""Powieksza czcionke BAM IWD2 z zachowaniem palety (gra koloruje tekst przez palete).

Klatki: kolory z palety -> RGB, krawedz rozlana na tlo, LANCZOS, maska przezroczystosci osobno
(prog 50%), kazdy piksel wraca do najblizszego koloru palety uzywanego przez oryginal.
Zapis BAM V1 bez kompresji, paleta, cykle i tablica wyszukiwania bez zmian.

  python tools/iwd2_czcionka_skala.py --gra KATALOG --zrodlo NORMAL --nazwa YNORMAL --skala 1.8 --out KATALOG
"""
import argparse
import os
import struct
import sys
import zlib

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory.resource_reader import GameResources  # noqa: E402


def czytaj(d):
    if d[:4] == b"BAMC":
        d = zlib.decompress(d[12:])
    sig, nf, nc, tr, fo, po, lo = struct.unpack_from("<8sHBBIII", d, 0)
    fr = []
    for i in range(nf):
        w, h, cx, cy, off = struct.unpack_from("<HHhhI", d, fo + 12 * i)
        rle = not (off & 0x80000000)
        p = off & 0x7FFFFFFF
        px = bytearray()
        while len(px) < w * h:
            b = d[p]
            p += 1
            if rle and b == tr:
                px += bytes([tr]) * (d[p] + 1)
                p += 1
            else:
                px.append(b)
        fr.append((np.frombuffer(bytes(px[:w * h]), np.uint8).reshape(h, w), cx, cy))
    cyk = d[fo + 12 * nf: fo + 12 * nf + 4 * nc]
    nl = max([a + b for a, b in (struct.unpack_from("<HH", cyk, 4 * k) for k in range(nc))] + [0])
    return nf, nc, tr, fr, cyk, d[po:po + 1024], d[lo:lo + 2 * nl]


def skaluj(d, k):
    nf, nc, tr, fr, cyk, pal, lut = czytaj(d)
    p = np.frombuffer(pal, np.uint8).reshape(256, 4)[:, 2::-1].astype(np.float32)  # RGB
    uzyte = sorted({int(v) for idx, _, _ in fr for v in np.unique(idx)} - {tr})
    paleta_uz = p[uzyte] if uzyte else p[[tr]]
    fo = 24
    co = fo + 12 * nf
    po = co + len(cyk)
    lo = po + 1024
    do = lo + len(lut)
    rb, db = b"", b""
    for idx, cx, cy in fr:
        h, w = idx.shape
        nw, nh = max(1, round(w * k)), max(1, round(h * k))
        if w == 0 or h == 0:
            n = np.full((nh, nw), tr, np.uint8)
        else:
            maska = idx != tr
            rgb = p[idx]
            if maska.any() and not maska.all():
                _, (iy, ix) = ndimage.distance_transform_edt(~maska, return_indices=True)
                rgb = rgb[iy, ix]
            r = np.asarray(Image.fromarray(rgb.astype(np.uint8)).resize((nw, nh), Image.LANCZOS)).astype(np.float32)
            m = np.asarray(Image.fromarray((maska * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)) >= 128
            odl = ((r[:, :, None, :] - paleta_uz[None, None]) ** 2).sum(-1)
            n = np.array(uzyte, np.uint8)[odl.argmin(-1)] if uzyte else np.full((nh, nw), tr, np.uint8)
            n[~m] = tr
        rb += struct.pack("<HHhhI", nw, nh, round(cx * k), round(cy * k), (do + len(db)) | 0x80000000)
        db += n.astype(np.uint8).tobytes()
    return struct.pack("<8sHBBIII", b"BAM V1  ", nf, nc, tr, fo, po, lo) + rb + cyk + pal + lut + db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--zrodlo", required=True)
    ap.add_argument("--nazwa", required=True)
    ap.add_argument("--skala", type=float, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    g = GameResources(a.gra, override_dirs=[])
    open(os.path.join(a.out, a.nazwa + ".BAM"), "wb").write(skaluj(g.read(a.zrodlo, "BAM"), a.skala))


if __name__ == "__main__":
    main()
