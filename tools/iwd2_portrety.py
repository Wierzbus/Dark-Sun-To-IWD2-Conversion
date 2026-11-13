"""Portrety IWD2 dla GUI 1920x1080.

Male (_S): 60x60 w ramce 64 px (obraz od +2, jak w oryginale 42 w 44), wymaga
latki exe z prostokatami portretow 64/60 px. Zrodlem jest wersja z Override
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

MALY = (60, 60)
DUZY = (378, 594)


def buduj(g, out, maly=MALY, duzy=DUZY, override=None, tylko_male=False):
    """maly: obraz w polu portretu (bok pola - 4), duzy: 210x330 x wys/600."""
    os.makedirs(out, exist_ok=True)
    ov = {}
    if override:
        ov = {f.upper(): os.path.join(override, f) for f in os.listdir(override)}
    bmp = sorted(n.upper() for (n, t) in g.key_index if t == 1)
    portrety = [n for n in bmp if n.endswith(("_S", "_L")) or n in ("NOPORTSM", "NOPORTLG")]
    for n in portrety:
        oryg = Image.open(io.BytesIO(g.read(n, 1))).convert("RGB")
        jest_maly = n.endswith("_S") or n == "NOPORTSM"
        if tylko_male and not jest_maly:
            continue
        if jest_maly and oryg.size != (42, 42) or not jest_maly and oryg.size != (210, 330):
            continue  # nie portret postaci
        zrodlo = oryg
        if jest_maly and n + ".BMP" in ov:
            zrodlo = Image.open(ov[n + ".BMP"]).convert("RGB")
        cel = maly if jest_maly else duzy
        zrodlo.resize(cel, Image.LANCZOS).save(os.path.join(out, n + ".BMP"), "BMP")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--override")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tylko-male", action="store_true")
    a = ap.parse_args()
    buduj(GameResources(a.gra, override_dirs=[]), a.out, override=a.override, tylko_male=a.tylko_male)


if __name__ == "__main__":
    main()
