"""Powieksza czcionki, ktore gra wybiera w kodzie po nazwie (NORMAL, STONESML...).

Kontrolki w plikach CHU uzywaja juz powiekszonych czcionek Y.../Z...,
ale napisy rysowane przez kod (przyciski, liczby na portretach, podpowiedzi,
ekran ladowania) siegaja po oryginalne nazwy. Narzedzie zapisuje pod tymi
nazwami wersje powiekszone:
- jesli w Override jest gotowa wersja Y... (z moda skalujacego) - kopia,
- w przeciwnym razie skalowanie x1,8 z zachowaniem palety (gra koloruje
  tekst podmieniajac palete, wiec piksele dostaja najblizszy indeks
  z oryginalnej palety; srodki glifow skalowane tak samo).

Uzycie:
  python tools/iwd2_czcionki.py --gra KATALOG_GRY --override KATALOG --out WYNIK
"""
import argparse
import os
import shutil
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory.resource_reader import GameResources  # noqa: E402
from iwd2_czcionka_obwodka import czytaj_bam  # noqa: E402

SKALA = 1.8
# oryginal -> gotowa wersja w Override
GOTOWE = {"NORMAL": "YNORMAL", "TOOLFONT": "YTOOLFON", "REALMS": "YREALMS",
          "STONEBIG": "YSTONEBI", "INITIALS": "YINITIAL"}
DO_SKALOWANIA = ["STONESML", "STONESM2", "INFOFONT", "NUMFONT", "NUMBER", "NUMBER2", "NUMBER3"]


def skaluj_czcionke(dane, skala=SKALA):
    dane, nf, tr, fo, pal, ramki = czytaj_bam(dane)
    _, _, nc, _, _, po, lo = struct.unpack_from("<8sHBBIII", dane, 0)
    cykle = dane[fo + 12 * nf: fo + 12 * nf + 4 * nc]
    nlut = max([c + i for i, c in (struct.unpack_from("<HH", cykle, 4 * k) for k in range(nc))] + [0])
    lut = dane[lo: lo + 2 * nlut]
    rgb_pal = pal[:, 2::-1].astype(np.float32)
    uzyte = sorted({int(v) for r in ramki for v in np.unique(r)} - {tr})
    cand = np.array(uzyte or [1])
    nowe = []
    for i, r in enumerate(ramki):
        w0, h0, cx, cy, _ = struct.unpack_from("<HHhhI", dane, fo + 12 * i)
        w, h = max(1, round(w0 * skala)), max(1, round(h0 * skala))
        alfa = (r != tr).astype(np.float32)
        rgb = rgb_pal[r] * alfa[..., None]
        pm = np.dstack([rgb, alfa * 255]).clip(0, 255).astype(np.uint8)
        big = np.asarray(Image.fromarray(pm, "RGBA").resize((w, h), Image.LANCZOS)).astype(np.float32)
        a = big[..., 3]
        kolor = big[..., :3] * 255 / np.maximum(a, 1)[..., None]
        d = ((kolor[:, :, None, :] - rgb_pal[cand][None, None]) ** 2).sum(3)
        idx = cand[d.argmin(2)].astype(np.uint8)
        idx[a < 128] = tr
        nowe.append((idx, round(cx * skala), round(cy * skala)))
    nag = struct.pack("<8sHBBIII", b"BAM V1  ", nf, nc, tr, 24, 24 + 12 * nf + len(cykle),
                      24 + 12 * nf + len(cykle) + 1024)
    do = 24 + 12 * nf + len(cykle) + 1024 + len(lut)
    ramki_b, dane_b = b"", b""
    for idx, cx, cy in nowe:
        h, w = idx.shape
        ramki_b += struct.pack("<HHhhI", w, h, cx, cy, (do + len(dane_b)) | 0x80000000)
        dane_b += idx.tobytes()
    return nag + ramki_b + cykle + pal.tobytes() + lut + dane_b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--override", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ov = {f.upper(): os.path.join(a.override, f) for f in os.listdir(a.override)}
    for oryg, gotowa in GOTOWE.items():
        shutil.copyfile(ov[gotowa + ".BAM"], os.path.join(a.out, oryg + ".BAM"))
        print(oryg, "<-", gotowa)
    g = GameResources(a.gra, override_dirs=[])
    for n in DO_SKALOWANIA:
        open(os.path.join(a.out, n + ".BAM"), "wb").write(skaluj_czcionke(g.read(n, 0x3E8)))
        print(n, "x", SKALA)


if __name__ == "__main__":
    main()
