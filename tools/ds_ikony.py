"""Ikony przedmiotow Dark Sun -> BAM-y ikon IWD2 (GUI 800x600 i GUI 1920x1080).

Wejscie: items.csv i katalog icons/ z `python -m darksun.extract` (PNG RGBA,
paleta RESOURCE.GFF PAL 1000). Ikona przedmiotu = grafika BMP z kolumny bmp_id.

Wyjscie dla kazdej uzytej grafiki (nazwa z numeru BMP, 7 znakow):
  DSI####.BAM  ikona przedmiotu jak w IWD2: klatka 0 = mala ikona w polu
               32x32 (srodek przesuwa ja na srodek pola), klatka 1 = duza ikona
               opisu w polu 64x64; cykl 0 -> klatka 1, cykl 1 -> klatka 0
               (uklad jak IBOOT01/IHELM01).
  DSG####.BAM  ikona na ziemi: jedna klatka w polu 32x32.
Katalogi: <out>/800x600 i <out>/1920x1080 (pola x1,5 -> 48 i x1,8 -> 115,
jak tools/iwd2_ikony.py dla ikon gry).

Skalowanie: grafiki Dark Sun sa male (czesto 7-16 px), wiec najpierw
powiekszenie calkowitokrotne metoda najblizszego sasiada (ostre piksele),
potem Lanczos z rozlaniem koloru do rozmiaru wpasowanego w pole.

Uzycie:
  python tools/ds_ikony.py --ds build/darksun --out build/ds_ikony
"""
import argparse
import csv
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from iwd2_ikony import powieksz, zapisz_bam  # noqa: E402

# (pole malej ikony, pole duzej ikony)
WARIANTY = {"800x600": (32, 64), "1920x1080": (48, 115)}
# ile maksymalnie wypelniamy pole (margines jak w ikonach gry)
WYPELNIENIE = 0.94


def wpasuj(rgba, pole):
    """Skaluje RGBA tak, by miescilo sie w kwadracie pole x pole."""
    h, w = rgba.shape[:2]
    k = min(pole * WYPELNIENIE / w, pole * WYPELNIENIE / h)
    ki = int(math.floor(k)) if k >= 2 else 1
    if ki > 1:
        rgba = np.asarray(Image.fromarray(rgba, "RGBA").resize((w * ki, h * ki), Image.NEAREST))
    cw, ch = max(1, round(w * k)), max(1, round(h * k))
    if (cw, ch) == (rgba.shape[1], rgba.shape[0]):
        return rgba[..., :3].copy(), rgba[..., 3] >= 128
    rgb, maska, _ = powieksz(np.ascontiguousarray(rgba), cw, ch)
    return np.ascontiguousarray(rgb), maska


def przytnij(rgba):
    a = rgba[..., 3] >= 128
    if not a.any():
        return rgba
    ys, xs = np.where(a)
    return rgba[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]


def bam_przedmiotu(rgba, mala, duza):
    rgb_m, m_m = wpasuj(rgba, mala)
    rgb_d, m_d = wpasuj(rgba, duza)
    hm, wm = m_m.shape
    hd, wd = m_d.shape
    klatki = [
        # mala: srodek ujemny = przesuniecie na srodek pola (jak IHELM01: 32x21, cy -5)
        (rgb_m, m_m, -((mala - wm) // 2), -((mala - hm) // 2)),
        # duza: srodek w polowie klatki (jak IBOOT01: 64x64, 33,33)
        (rgb_d, m_d, wd // 2 + 1, hd // 2 + 1),
    ]
    cykle = bytes([1, 0, 0, 0, 1, 0, 1, 0])  # (1 klatka, lut 0), (1 klatka, lut 1)
    lut = bytes([1, 0, 0, 0])  # cykl 0 -> klatka 1, cykl 1 -> klatka 0
    return zapisz_bam(klatki, 2, cykle, lut)


def bam_ziemi(rgba, mala):
    rgb, m = wpasuj(rgba, mala)
    h, w = m.shape
    return zapisz_bam([(rgb, m, -((mala - w) // 2), -((mala - h) // 2))], 1, bytes([1, 0, 0, 0]), bytes([0, 0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ds", required=True, help="katalog z items.csv i icons/")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(os.path.join(a.ds, "items.csv"), encoding="utf-8") as f:
        wiersze = list(csv.DictReader(f, delimiter=";"))
    bmp = sorted({int(w["bmp_id"]) for w in wiersze if w.get("icon_file")})
    spis = []
    for wariant, (mala, duza) in WARIANTY.items():
        os.makedirs(os.path.join(a.out, wariant), exist_ok=True)
    for b in bmp:
        sciezka = os.path.join(a.ds, "icons", f"BMP_{b:04d}.png")
        if not os.path.exists(sciezka):
            continue
        rgba = przytnij(np.asarray(Image.open(sciezka).convert("RGBA")))
        for wariant, (mala, duza) in WARIANTY.items():
            k = os.path.join(a.out, wariant)
            with open(os.path.join(k, f"DSI{b:04d}.BAM"), "wb") as f:
                f.write(bam_przedmiotu(rgba, mala, duza))
            with open(os.path.join(k, f"DSG{b:04d}.BAM"), "wb") as f:
                f.write(bam_ziemi(rgba, mala))
        spis.append((b, rgba.shape[1], rgba.shape[0]))
    with open(os.path.join(a.out, "spis.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["bmp_id", "szer", "wys", "ikona", "ziemia"])
        for b, sz, wy in spis:
            w.writerow([b, sz, wy, f"DSI{b:04d}", f"DSG{b:04d}"])
    print(f"ikony: {len(spis)} grafik x {len(WARIANTY)} warianty")


if __name__ == "__main__":
    main()
