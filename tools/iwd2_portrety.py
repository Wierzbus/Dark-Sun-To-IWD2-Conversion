"""Portrety IWD2 dla GUI 1920x1080.

Male (_S): 64x64. Wymaga latki exe, ktora zmienia na sztywno zapisane
prostokaty portretow z 42/44 px na 64 px (pelna ramka, bez marginesu). Zrodlem jest wersja z Override
(jesli jest, np. 59x59 z modu skalujacego), inaczej oryginal z BIF.
Duze (_L): 210x330 -> 378x594 (1,8x), zrodlo: oryginal z BIF.

Uzycie:
  python tools/iwd2_portrety.py --gra KATALOG_GRY [--override KATALOG] --out WYNIK
"""
import argparse
import io
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory.resource_reader import GameResources  # noqa: E402

MALY = (64, 64)
DUZY = (378, 594)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--override")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    g = GameResources(a.gra, override_dirs=[])
    ov = {}
    if a.override:
        ov = {f.upper(): os.path.join(a.override, f) for f in os.listdir(a.override)}
    bmp = sorted(n.upper() for (n, t) in g.key_index if t == 1)
    portrety = [n for n in bmp if n.endswith(("_S", "_L")) or n in ("NOPORTSM", "NOPORTLG")]
    for n in portrety:
        oryg = Image.open(io.BytesIO(g.read(n, 1))).convert("RGB")
        maly = n.endswith("_S") or n == "NOPORTSM"
        if maly and oryg.size != (42, 42) or not maly and oryg.size != (210, 330):
            continue  # nie portret postaci
        zrodlo = oryg
        if maly and n + ".BMP" in ov:
            zrodlo = Image.open(ov[n + ".BMP"]).convert("RGB")
        cel = MALY if maly else DUZY
        zrodlo.resize(cel, Image.LANCZOS).save(os.path.join(a.out, n + ".BMP"), "BMP")
        print(n, zrodlo.size, "->", cel)


if __name__ == "__main__":
    main()
