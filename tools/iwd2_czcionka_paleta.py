"""Przekolorowuje palete czcionki BAM: gradient od czerni do zadanego koloru tla.

Czcionka tytulow (YSTONEBI) ma palete od czerni do bieli, wiec wygladzone
krawedzie liter wychodza jasnoszare na ciemnym drewnie. Po przekolorowaniu
najjasniejsze odcienie przechodza w kolor deski i krawedzie sie z nia zlewaja.
Indeks przezroczystosci zostaje bez zmian.

Uzycie:
  python tools/iwd2_czcionka_paleta.py WEJ.BAM WYJ.BAM --tlo 65,47,20
"""
import argparse
import struct
import zlib

import numpy as np


def przekoloruj(dane, tlo):
    if dane[:4] == b"BAMC":
        dane = zlib.decompress(dane[12:])
    dane = bytearray(dane)
    _, _, _, tr, _, po, _ = struct.unpack_from("<8sHBBIII", dane, 0)
    pal = np.frombuffer(bytes(dane[po:po + 1024]), np.uint8).reshape(256, 4).copy()
    jasnosc = pal[:, :3].astype(np.float32).max(1) / 255
    bgr_tla = np.array(tlo[::-1], np.float32)
    for i in range(256):
        if i == tr:
            continue
        pal[i, :3] = np.round(bgr_tla * jasnosc[i]).astype(np.uint8)
    dane[po:po + 1024] = pal.tobytes()
    return bytes(dane)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wej")
    ap.add_argument("wyj")
    ap.add_argument("--tlo", default="65,47,20")
    a = ap.parse_args()
    tlo = tuple(int(v) for v in a.tlo.split(","))
    open(a.wyj, "wb").write(przekoloruj(open(a.wej, "rb").read(), tlo))


if __name__ == "__main__":
    main()
