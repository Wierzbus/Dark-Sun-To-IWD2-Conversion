"""Pas portretow ekranow postaci (YGACTN10, pola 83 px) przerobiony na pola 64 px
jak w pasku swiata (ZGACTN11), plus ustawienie kontrolek w CHU.

Do YGACTN10 (1920x108) od x=1140 wstawiany jest fragment ZGACTN11 x 1100..1517
(6 pol 64 px) i panel z plecionka (ZGACTN11 x 1517..1680, zwezony), w pionie +12 px;
gora i dol dopelnione kamieniem z ZGACTN11. W CHU okna z tlem YGACTN10:
portrety 0-5 -> pozycje ze swiata +40/+12, 64x64, przycisk ZGUIRSPO; paski HP
50-55 -> 63x6, ZGUIHITP.

Uzycie:
  python tools/iwd2_pas_portretow.py --yg YGACTN10.MOS --zg ZGACTN11.MOS --chu KATALOG_CHU --out WYNIK
"""
import argparse
import glob
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from iwd2_poszerz_tla import czytaj_mos, zapisz_mos  # noqa: E402

X0, DY, PRAWY = 1140, 12, 1680
PORTRETY_X = [1107, 1175, 1244, 1313, 1381, 1450]   # GUIW10, okno 1
HP_X = [1108, 1177, 1245, 1314, 1383, 1451]
PRZESUNIECIE = X0 - 1100


def pas(yg, zg):
    yg = yg.copy()
    w = PRAWY - X0
    sloty = zg[:, 1100:1517]
    panel = np.asarray(Image.fromarray(np.ascontiguousarray(zg[:, 1517:1680]))
                       .resize((w - sloty.shape[1], zg.shape[0]), Image.LANCZOS))
    srodek = np.concatenate([sloty, panel], 1)
    yg[:, X0:PRAWY] = np.concatenate([zg[20:20 + DY, 420:420 + w], srodek, zg[50:50 + DY, 420:420 + w]], 0)
    return yg


def popraw_chu(d):
    d = bytearray(d)
    nw, co, wo = struct.unpack_from("<III", d, 8)
    for w in range(nw):
        bg, fc = struct.unpack_from("<8sH", d, wo + w * 28 + 16)
        nc = struct.unpack_from("<H", d, wo + w * 28 + 14)[0]
        if bg.rstrip(b"\0") != b"YGACTN10":
            continue
        for c in range(fc, fc + nc):
            off = struct.unpack_from("<I", d, co + c * 8)[0]
            cid = struct.unpack_from("<I", d, off)[0] & 0xFFFF
            if cid <= 5:
                struct.pack_into("<HHHH", d, off + 4, PORTRETY_X[cid] + PRZESUNIECIE, 6 + DY, 64, 64)
                d[off + 14:off + 22] = b"ZGUIRSPO"
            elif 50 <= cid <= 55:
                struct.pack_into("<HHHH", d, off + 4, HP_X[cid - 50] + PRZESUNIECIE, 73 + DY, 63, 6)
                d[off + 14:off + 22] = b"ZGUIHITP"
    return bytes(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yg", required=True)
    ap.add_argument("--zg", required=True)
    ap.add_argument("--chu", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    yg = czytaj_mos(open(a.yg, "rb").read())
    zg = czytaj_mos(open(a.zg, "rb").read())
    open(os.path.join(a.out, "YGACTN10.MOS"), "wb").write(zapisz_mos(pas(yg, zg)))
    for p in glob.glob(os.path.join(a.chu, "*.CHU")):
        d = open(p, "rb").read()
        n = popraw_chu(d)
        if n != d:
            open(os.path.join(a.out, os.path.basename(p)), "wb").write(n)
            print(os.path.basename(p))


if __name__ == "__main__":
    main()
