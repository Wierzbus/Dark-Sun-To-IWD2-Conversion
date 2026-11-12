"""Usuwa jasna obwodke z przeskalowanej czcionki BAM (np. YSTONEBI - tytuly GUI).

Skalowanie wygladzilo czarne glify na bialym tle, wiec krawedzie liter maja
jasnoszare piksele, widoczne w grze jako biala obwodka. Piksele jasniejsze
od progu staja sie przezroczyste. Ramki zapisywane sa bez RLE (BAM V1).

Uzycie:
  python tools/iwd2_czcionka_obwodka.py WEJ.BAM WYJ.BAM [--prog 120]
"""
import argparse
import struct
import zlib

import numpy as np


def czytaj_bam(dane):
    if dane[:4] == b"BAMC":
        dane = zlib.decompress(dane[12:])
    sig, nf, nc, tr, fo, po, lo = struct.unpack_from("<8sHBBIII", dane, 0)
    if sig != b"BAM V1  ":
        raise ValueError("nie BAM V1")
    pal = np.frombuffer(dane, np.uint8, 1024, po).reshape(256, 4)
    ramki = []
    for i in range(nf):
        w, h, _, _, off = struct.unpack_from("<HHhhI", dane, fo + 12 * i)
        rle = not (off & 0x80000000)
        p = off & 0x7FFFFFFF
        px = bytearray()
        while len(px) < w * h:
            b = dane[p]
            p += 1
            if rle and b == tr:
                px += bytes([tr]) * (dane[p] + 1)
                p += 1
            else:
                px.append(b)
        ramki.append(np.frombuffer(bytes(px[:w * h]), np.uint8).reshape(h, w))
    return dane, nf, tr, fo, pal, ramki


def usun_obwodke(dane, prog=120):
    dane, nf, tr, fo, pal, ramki = czytaj_bam(dane)
    jasnosc = pal[:, :3].astype(int).max(1)
    jasne = jasnosc >= prog
    jasne[tr] = False
    out = bytearray(dane)
    zmienione = 0
    for i, r in enumerate(ramki):
        r = r.copy()
        m = jasne[r]
        zmienione += int(m.sum())
        r[m] = tr
        struct.pack_into("<I", out, fo + 12 * i + 8, len(out) | 0x80000000)
        out += r.tobytes()
    return bytes(out), zmienione


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wej")
    ap.add_argument("wyj")
    ap.add_argument("--prog", type=int, default=120)
    a = ap.parse_args()
    nowe, n = usun_obwodke(open(a.wej, "rb").read(), a.prog)
    open(a.wyj, "wb").write(nowe)
    print("przezroczyste piksele:", n)


if __name__ == "__main__":
    main()
