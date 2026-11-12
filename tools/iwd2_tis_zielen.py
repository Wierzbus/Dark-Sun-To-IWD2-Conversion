"""Usuwa widoczna zielen (0,255,0) z kafli drzwi (secondary tiles) obszaru IWD2.

W obszarach przeniesionych z BG zamkniete warianty drzwi maja zielone piksele
oznaczajace "pokaz kafel podstawowy". IWD2 rysuje je jako zielen. Narzedzie
wkleja w te miejsca piksele z kafla podstawowego tej samej komorki i zapisuje
kafel z nowa paleta (zielen, jesli zostanie, na pozycji 0).

Uzycie:
  python tools/iwd2_tis_zielen.py OBSZAR.WED OBSZAR.TIS WYNIK.TIS
"""
import argparse
import struct

import numpy as np

from iwd2_poszerz_tla import ZIELEN, kafel_do_palety


def kafel_rgb(tis, i, ho, tl):
    pal = np.frombuffer(tis, np.uint8, 1024, ho + i * tl).reshape(256, 4)
    px = np.frombuffer(tis, np.uint8, 4096, ho + i * tl + 1024).reshape(64, 64)
    return pal[px][..., 2::-1].copy()


def napraw(wed, tis):
    tis = bytearray(tis)
    _, n, tl, ho, dim = struct.unpack_from("<8sIIII", tis, 0)
    if tl != 5120 or dim != 64:
        raise ValueError("obslugiwany tylko TIS z paletami 64x64")
    _, _, oo, _, _ = struct.unpack_from("<IIIII", wed, 8)
    w, h, _, _, _, tmo, tio = struct.unpack_from("<HH8sHHII", wed, oo)
    naprawione = []
    for c in range(w * h):
        start, _, sec = struct.unpack_from("<HHh", wed, tmo + 10 * c)
        if sec < 0:
            continue
        drzwi = kafel_rgb(tis, sec, ho, tl)
        maska = (drzwi == ZIELEN).all(2)
        if not maska.any():
            continue
        prim = struct.unpack_from("<H", wed, tio + 2 * start)[0]
        drzwi[maska] = kafel_rgb(tis, prim, ho, tl)[maska]
        pal, idx = kafel_do_palety(drzwi)
        o = ho + sec * tl
        tis[o:o + 1024] = pal.tobytes()
        tis[o + 1024:o + 5120] = idx.astype(np.uint8).tobytes()
        naprawione.append((c % w, c // w, sec, prim, int(maska.sum())))
    return bytes(tis), naprawione


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wed")
    ap.add_argument("tis")
    ap.add_argument("wynik")
    a = ap.parse_args()
    nowy, lista = napraw(open(a.wed, "rb").read(), open(a.tis, "rb").read())
    open(a.wynik, "wb").write(nowy)
    for x, y, sec, prim, ile in lista:
        print(f"komorka ({x},{y}) kafel drzwi {sec} <- kafel {prim}: {ile} px")


if __name__ == "__main__":
    main()
