"""Czcionka BAM dla IWD2 z fontu TTF, w ukladzie sprawdzonym w grze (mod "IWD2 Better Fonts", Nexus 5):
255 klatek po jednym cyklu (cykl i = znak cp1252 i+1), wszystkie klatki tej samej wysokosci H z linia bazowa
na cy, cx = 0, szerokosc = krok znaku. Paleta: jasna rampa (indeks 0 = przezroczysty, 255 = pelne pokrycie = biel),
piksel = pokrycie 0..255 (gra koloruje tekst wg indeksu). Zapis BAM V1 bez kompresji.

  python tools/iwd2_czcionka_ttf.py --ttf Klaudia.ttf --wys 18 --out ZNORMAL.BAM
  --wys      wysokosc ramki (linia tekstu) w px; NORMAL w modzie z Nexusa: 18 (oryginal 13)
  --wersalik wysokosc wersalika w px (domyslnie 0,62 * wys)
"""
import argparse
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SS = 4  # nadprobkowanie


def generuj(ttf, wys, wersalik=None, prog=8, odstep=1):
    wersalik = wersalik or round(0.62 * wys)
    # rozmiar fontu tak, by wysokosc "H" = wersalik
    f400 = ImageFont.truetype(ttf, 400)
    hb = f400.getbbox("H", anchor="ls")
    rozmiar = 400 * wersalik / (-hb[1])
    font = ImageFont.truetype(ttf, rozmiar * SS)
    asc, desc = font.getmetrics()
    # linia bazowa: tak, by zmiescily sie wydluzenia dolne
    dol = min(wys - wersalik - 1, round(desc / SS) + 1)
    cy = wys - max(1, dol)
    klatki = []
    for kod in range(1, 256):
        ch = bytes([kod]).decode("cp1252", errors="replace") if kod >= 32 else ""
        if ch == "�" or not ch:
            klatki.append((1, np.zeros((wys, 1), np.uint8)))
            continue
        krok = font.getlength(ch) / SS
        w = max(1, round(krok) + odstep)
        img = Image.new("L", (w * SS + 8 * SS, wys * SS), 0)
        ImageDraw.Draw(img).text((0, cy * SS), ch, font=font, fill=255, anchor="ls")
        img = img.resize((w + 8, wys), Image.Resampling.BOX)
        a = np.asarray(img)[:, :w].copy()
        a[a < prog] = 0
        klatki.append((w, a))
    # Paleta: indeks = pokrycie, jasna rampa (255 = biel). Czcionki kolorowane przez gre (NORMAL, TOOLFONT...)
    # i tak dostaja palete z koloru tekstu; tam, gdzie gra rysuje paleta z pliku (tytuly, nazwy), tekst jest
    # jasny zamiast czarnego.
    pal = np.zeros((256, 4), np.uint8)
    for i in range(256):
        pal[i, :3] = i
    nf = 255
    fo = 24
    co = fo + 12 * nf
    po = co + 4 * nf
    lo = po + 1024
    do = lo + 2 * nf
    rb, db = b"", b""
    for w, a in klatki:
        rb += struct.pack("<HHhhI", w, wys, 0, cy, (do + len(db)) | 0x80000000)
        db += a.tobytes()
    cykle = b"".join(struct.pack("<HH", 1, i) for i in range(nf))
    lut = b"".join(struct.pack("<H", i) for i in range(nf))
    nag = struct.pack("<8sHBBIII", b"BAM V1  ", nf, nf, 0, fo, po, lo)
    return nag + rb + cykle + pal.tobytes() + lut + db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf", required=True)
    ap.add_argument("--wys", type=int, required=True)
    ap.add_argument("--wersalik", type=int)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    open(a.out, "wb").write(generuj(a.ttf, a.wys, a.wersalik))


if __name__ == "__main__":
    main()
