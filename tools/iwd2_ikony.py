"""Skaluje ikony IWD2 (BAM) do GUI 1920x1080.

Obejmuje:
- ikony przedmiotow i czarow: BAM, ktorego pierwsza klatka ma ok. 32x32
  (srodek bliski 0,0): klatki do 40 px x1,5 (32 -> 48), pozostale
  (duza ikona opisu) x1,8; srodki klatek skalowane tak samo,
- ikony akcji GUIBTACT (38x38) -> 53x53 (pole paska gry).
Gra centruje ikone w polu wedlug rozmiaru klatki, wiec srodek 0,0 zostaje.

Paleta: indeks 0 = przezroczysta zielen, 255 kolorow wspolnych dla klatek.
Zapis BAM V1 bez kompresji klatek (RLE wylaczone).

Uzycie:
  python tools/iwd2_ikony.py --gra KATALOG_GRY [--override KATALOG] --out WYNIK
--override: pliki z Override maja pierwszenstwo przed BIF-ami.
"""
import argparse
import os
import struct
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory.resource_reader import GameResources  # noqa: E402

MALA, AKCJA = 48, 53
# ikony z modow w Override, ktore maja oryginalny rozmiar 32x32 i tez trzeba je powiekszyc
Z_OVERRIDE = {"SPPR801B", "SPPR801C"}
ZIELEN = (0, 255, 0)


def czytaj_bam(dane):
    if dane[:4] == b"BAMC":
        dane = zlib.decompress(dane[12:])
    sig, nf, nc, tr, fo, po, lo = struct.unpack_from("<8sHBBIII", dane, 0)
    if sig != b"BAM V1  ":
        raise ValueError("nie BAM V1")
    pal = np.frombuffer(dane, np.uint8, 1024, po).reshape(256, 4)
    ramki = []
    for i in range(nf):
        w, h, cx, cy, off = struct.unpack_from("<HHhhI", dane, fo + 12 * i)
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
        idx = np.frombuffer(bytes(px[: w * h]), np.uint8).reshape(h, w)
        rgba = np.zeros((h, w, 4), np.uint8)
        rgba[..., :3] = pal[idx][..., 2::-1]
        rgba[..., 3] = np.where(idx == tr, 0, 255)
        ramki.append((rgba, cx, cy))
    cykle = dane[fo + 12 * nf: fo + 12 * nf + 4 * nc]
    nlut = max([c + i for i, c in (struct.unpack_from("<HH", cykle, 4 * k) for k in range(nc))] + [0])
    lut = dane[lo: lo + 2 * nlut]
    return ramki, nc, cykle, lut


def skala_ramki(w, h, cx, cy):
    """Mnoznik skali klatki ikony: mala ikona 32x32 (srodek 0,0) -> 48 px,
    pozostale klatki (duza ikona opisu) -> x1,8 jak okna GUI."""
    if w <= 40 and h <= 40:
        return MALA / 32
    return 1.8


def powieksz(rgba, cel_w, cel_h):
    img = Image.fromarray(rgba, "RGBA")
    # premultiplied, zeby przezroczyste tlo nie farbowalo krawedzi
    a = rgba[..., 3:4].astype(np.float32) / 255
    pm = np.concatenate([(rgba[..., :3] * a).astype(np.uint8), rgba[..., 3:4]], 2)
    big = np.asarray(Image.fromarray(pm, "RGBA").resize((cel_w, cel_h), Image.LANCZOS)).astype(np.float32)
    alfa = big[..., 3:4]
    rgb = np.where(alfa > 0, np.clip(big[..., :3] * 255 / np.maximum(alfa, 1), 0, 255), 0).astype(np.uint8)
    maska = big[..., 3] >= 128
    return rgb, maska, img


def zapisz_bam(klatki, nc, cykle, lut):
    """klatki: lista (rgb, maska, cx, cy)."""
    kolory = np.concatenate([rgb[m] for rgb, m, _, _ in klatki] or [np.zeros((1, 3), np.uint8)])
    kolory = kolory[~(kolory == ZIELEN).all(1)]  # zielen zarezerwowana
    if len(kolory) == 0:
        kolory = np.zeros((1, 3), np.uint8)
    probka = Image.fromarray(kolory.reshape(1, -1, 3))
    q = probka.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal_rgb = np.array(q.getpalette()[:765], np.uint8).reshape(-1, 3)
    pal_rgb = np.vstack([pal_rgb, np.zeros((255 - len(pal_rgb), 3), np.uint8)])
    paleta = np.zeros((256, 4), np.uint8)
    paleta[0, :3] = ZIELEN[2], ZIELEN[1], ZIELEN[0]
    paleta[1:, 0] = pal_rgb[:, 2]
    paleta[1:, 1] = pal_rgb[:, 1]
    paleta[1:, 2] = pal_rgb[:, 0]
    pal_img = Image.new("P", (1, 1))
    # 256. kolor = kopia pierwszego, zeby wybor indeksu 255 nie dawal obcej barwy
    pal_img.putpalette(pal_rgb.flatten().tolist() + pal_rgb[0].tolist())
    nf = len(klatki)
    fo = 24
    co = fo + 12 * nf
    po = co + len(cykle)
    lo = po + 1024
    do = lo + len(lut)
    ramki_b, dane_b = b"", b""
    for rgb, maska, cx, cy in klatki:
        h, w = maska.shape
        idx = np.asarray(Image.fromarray(rgb).quantize(palette=pal_img, dither=Image.Dither.NONE)).astype(np.uint16)
        idx[idx == 255] = 0
        idx += 1
        idx[~maska] = 0
        ramki_b += struct.pack("<HHhhI", w, h, cx, cy, (do + len(dane_b)) | 0x80000000)
        dane_b += idx.astype(np.uint8).tobytes()
    nag = struct.pack("<8sHBBIII", b"BAM V1  ", nf, nc, 0, fo, po, lo)
    return nag + ramki_b + cykle + paleta.tobytes() + lut + dane_b


def przeskaluj(dane, akcja=False):
    ramki, nc, cykle, lut = czytaj_bam(dane)
    if not ramki:
        return None
    pierwsza = ramki[0]
    h0, w0 = pierwsza[0].shape[:2]
    if not akcja and not (24 <= w0 <= 40 and 24 <= h0 <= 40 and abs(pierwsza[1]) <= 8 and abs(pierwsza[2]) <= 8):
        return None  # nie ikona przedmiotu/czaru
    klatki = []
    for rgba, cx, cy in ramki:
        h, w = rgba.shape[:2]
        k = AKCJA / 38 if akcja else skala_ramki(w, h, cx, cy)
        cel = (max(1, round(w * k)), max(1, round(h * k)))
        rgb, maska, _ = powieksz(rgba, *cel)
        klatki.append((rgb, maska, round(cx * k), round(cy * k)))
    return zapisz_bam(klatki, nc, cykle, lut)


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
    nazwy = sorted({n.upper() for (n, t) in g.key_index if t == 0x3E8}
                   | {f[:-4] for f in ov if f.endswith(".BAM")})
    ile, pominiete = 0, 0
    for n in nazwy:
        if n + ".BAM" in ov and n not in Z_OVERRIDE:
            continue  # plik z Override (np. juz przeskalowane GUI) zostaje bez zmian
        try:
            dane = open(ov[n + ".BAM"], "rb").read() if n + ".BAM" in ov else g.read(n, 0x3E8)
            if not dane:
                raise ValueError
        except Exception:
            pominiete += 1
            continue
        try:
            nowy = przeskaluj(dane, akcja=(n == "GUIBTACT"))
        except ValueError:
            continue
        if nowy is None:
            continue
        open(os.path.join(a.out, n + ".BAM"), "wb").write(nowy)
        ile += 1
    print("przeskalowane:", ile, "nieczytelne:", pominiete)


if __name__ == "__main__":
    main()
