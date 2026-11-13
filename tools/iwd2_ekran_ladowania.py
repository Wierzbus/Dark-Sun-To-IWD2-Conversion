"""Grafiki ekranu ladowania IWD2 (domyslnie 1920x1080; --szer/--wys, skala wys/600 jak latka exe).

- tla GTRSCRN i GPROGBAR (800x600): x1,8 -> 1440x1080, dopelnione czarnymi
  pasami po 240 px do 1920x1080 (exe rysuje tlo od (0,0) na calym ekranie),
- obrazy obszarow LOAD*, pasek i czaszki postepu GTRSP*/GTRBP*: x1,8,
- animacja czaszki SKULANIM (BAM): x1,8.
Czysta zielen (0,255,0) w MOS zostaje przezroczysta.

Uzycie:
  python tools/iwd2_ekran_ladowania.py --gra KATALOG_GRY --out WYNIK
"""
import argparse
import os
import sys
import zlib

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory.resource_reader import GameResources  # noqa: E402
from iwd2_poszerz_tla import czytaj_mos, zapisz_mos, ZIELEN  # noqa: E402
from iwd2_ikony import czytaj_bam, powieksz, zapisz_bam  # noqa: E402

SKALA = 1.8
EKRAN_W = 1920
TLA = ["GTRSCRN", "GPROGBAR"]
MOS = (["GTRSPBAR", "GTRSPBG", "GTRSPCAP", "GTRSPSK", "GTRSPSK2",
        "GTRBPBAR", "GTRBPBG", "GTRBPCAP", "GTRBPSK", "GTRBPSK2"]
       + ["LOAD%d" % n for n in (1000, 2000, 3000, 4000, 4100, 5000, 5100, 5200,
                                 5300, 6000, 6050, 6100, 6200, 6300)])
BAM = ["SKULANIM"]


def skaluj_rgb(rgb, skala=SKALA):
    h, w, _ = rgb.shape
    cel = (max(1, round(w * skala)), max(1, round(h * skala)))
    zielen = (rgb == ZIELEN).all(2)
    if zielen.any() and not zielen.all():
        _, (iy, ix) = ndimage.distance_transform_edt(zielen, return_indices=True)
        rgb = rgb[iy, ix]
    out = np.asarray(Image.fromarray(np.ascontiguousarray(rgb)).resize(cel, Image.LANCZOS)).copy()
    if zielen.any():
        m = Image.fromarray((zielen * 255).astype(np.uint8)).resize(cel, Image.BILINEAR)
        out[np.asarray(m) >= 128] = ZIELEN
    return out


def dopelnij(rgb, w=EKRAN_W):
    out = np.zeros((rgb.shape[0], w, 3), np.uint8)
    x = (w - rgb.shape[1]) // 2
    out[:, x:x + rgb.shape[1]] = rgb
    return out


def buduj(g, out, szer=EKRAN_W, wys=1080):
    """Grafiki ekranu ladowania dla szer x wys (skala wys/600)."""
    skala = wys / 600.0
    os.makedirs(out, exist_ok=True)
    for n in TLA + MOS:
        rgb = skaluj_rgb(czytaj_mos(g.read(n, 0x3EC)), skala)
        if n in TLA:
            rgb = dopelnij(rgb, szer)
        open(os.path.join(out, n + ".MOS"), "wb").write(zapisz_mos(rgb))
        print(n, rgb.shape[1], rgb.shape[0])
    for n in BAM:
        dane = g.read(n, 0x3E8)
        if dane[:4] == b"BAMC":
            dane = zlib.decompress(dane[12:])
        ramki, nc, cykle, lut = czytaj_bam(dane)
        klatki = []
        for rgba, cx, cy in ramki:
            h, w = rgba.shape[:2]
            rgb, maska, _ = powieksz(rgba, round(w * skala), round(h * skala))
            klatki.append((rgb, maska, round(cx * skala), round(cy * skala)))
        open(os.path.join(out, n + ".BAM"), "wb").write(zapisz_bam(klatki, nc, cykle, lut))
        print(n, len(klatki), "klatek")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--szer", type=int, default=1920)
    ap.add_argument("--wys", type=int, default=1080)
    a = ap.parse_args()
    buduj(GameResources(a.gra, override_dirs=[]), a.out, a.szer, a.wys)


if __name__ == "__main__":
    main()
