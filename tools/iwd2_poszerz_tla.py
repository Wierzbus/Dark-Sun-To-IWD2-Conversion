"""Poszerza pelnoekranowe tla GUI IWD2 z 1440 do 1920 px (dla trybu 1920x1080).

Okna w plikach CHU z Override, ktore maja x=240, w=1440, h=1080 i tlo MOS,
dostaja x=0, w=1920; ich kontrolki przesuwaja sie o +240. Tla MOS sa
dopelniane czarnymi pasami po 240 px z obu stron i zapisywane jako MOS V1
bez kompresji (kafle 64x64, paleta na kafel).

Uzycie:
  python tools/iwd2_poszerz_tla.py --override "D:/Gry/Icewind Dale 2/Override" --out wynik
Skrypt nie zmienia plikow w --override; wynik trafia do --out.
"""
import argparse
import os
import struct
import zlib

import numpy as np
from PIL import Image

STARE_X, STARA_W, NOWA_W, H = 240, 1440, 1920, 1080
PAD = (NOWA_W - STARA_W) // 2
ZIELEN = np.array([0, 255, 0], np.uint8)
# tla podokien z przezroczystoscia, ktorym skalowanie rozmylo zielone krawedzie
TLA_Z_ZIELENIA = ("YGUIGDB YGUICRAC YGUISEX YGUIABB YGUIFEAT YGUIFEA1 YGUISPL2 "
                  "YGUICLST YGUICEXP YGUIAPB YGUIHSB").split()


def czytaj_mos(dane):
    if dane[:4] == b"MOSC":
        dane = zlib.decompress(dane[12:])
    sig, w, h, cols, rows, bs, poff = struct.unpack_from("<8sHHHHII", dane, 0)
    if sig != b"MOS V1  ":
        raise ValueError("nie MOS V1")
    n = cols * rows
    palety = [np.frombuffer(dane, np.uint8, 1024, poff + i * 1024).reshape(256, 4)
              for i in range(n)]
    offs = struct.unpack_from("<%dI" % n, dane, poff + n * 1024)
    pix0 = poff + n * 1024 + n * 4
    rgb = np.zeros((h, w, 3), np.uint8)
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            tw, th = min(bs, w - c * bs), min(bs, h - r * bs)
            idx = np.frombuffer(dane, np.uint8, tw * th, pix0 + offs[i]).reshape(th, tw)
            bgr = palety[i][idx]
            rgb[r * bs:r * bs + th, c * bs:c * bs + tw] = bgr[..., 2::-1]
    return rgb


def kafel_do_palety(t):
    """Zwraca (paleta 256x4 BGRA, indeksy) dla kafla RGB; kwantyzuje gdy >256 kolorow."""
    h, w, _ = t.shape
    plaskie = t.reshape(-1, 3)
    kolory, inv = np.unique(plaskie, axis=0, return_inverse=True)
    if len(kolory) > 256:
        img = Image.fromarray(t).quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        idx = np.asarray(img, np.uint8).copy()
        pal = np.array(img.getpalette()[:765], np.uint8).reshape(-1, 3)
        kolory = np.zeros((256, 3), np.uint8)
        kolory[:len(pal)] = pal
        # czysta zielen to przezroczystosc - musi przetrwac kwantyzacje bez zmian
        kolory[255] = ZIELEN
        idx[(t == ZIELEN).all(2)] = 255
    else:
        idx = inv.reshape(h, w).astype(np.uint8)
    paleta = np.zeros((256, 4), np.uint8)
    paleta[:len(kolory), 0] = kolory[:, 2]
    paleta[:len(kolory), 1] = kolory[:, 1]
    paleta[:len(kolory), 2] = kolory[:, 0]
    return paleta, idx


def zapisz_mos(rgb, bs=64):
    h, w, _ = rgb.shape
    cols, rows = -(-w // bs), -(-h // bs)
    n = cols * rows
    palety, piksele, offs, poz = [], [], [], 0
    for r in range(rows):
        for c in range(cols):
            pal, idx = kafel_do_palety(np.ascontiguousarray(rgb[r * bs:(r + 1) * bs, c * bs:(c + 1) * bs]))
            palety.append(pal.tobytes())
            piksele.append(idx.tobytes())
            offs.append(poz)
            poz += idx.size
    nag = struct.pack("<8sHHHHII", b"MOS V1  ", w, h, cols, rows, bs, 24)
    return nag + b"".join(palety) + struct.pack("<%dI" % n, *offs) + b"".join(piksele)


def poszerz_rgb(rgb):
    out = np.zeros((rgb.shape[0], NOWA_W, 3), np.uint8)
    out[:, PAD:PAD + rgb.shape[1]] = rgb
    return out


def usun_zielona_obwodke(rgb, promien=2, prog=30):
    """Piksele z domieszka zieleni tuz przy przezroczystym (0,255,0) staja sie przezroczyste."""
    czysta = (rgb == ZIELEN).all(2)
    blisko = czysta.copy()
    for _ in range(promien):
        b = blisko
        blisko = b.copy()
        blisko[1:] |= b[:-1]
        blisko[:-1] |= b[1:]
        blisko[:, 1:] |= b[:, :-1]
        blisko[:, :-1] |= b[:, 1:]
    a = rgb.astype(int)
    nadmiar = a[..., 1] - np.maximum(a[..., 0], a[..., 2])
    maska = blisko & ~czysta & (nadmiar > prog)
    out = rgb.copy()
    out[maska] = ZIELEN
    return out, int(maska.sum())


def poszerz_chu(dane):
    """Zwraca (nowe dane, lista nazw tel) dla okien pelnoekranowych 1440x1080 w x=240."""
    dane = bytearray(dane)
    _, nwin, octl, owin = struct.unpack_from("<8sIII", dane, 0)
    tla = []
    for i in range(nwin):
        o = owin + i * 28
        wid, _, x, y, w, h, bgf, nc, bg, first, _ = struct.unpack_from("<HHHHHHHH8sHH", dane, o)
        nazwa = bg.split(b"\0")[0].decode("latin-1").upper()
        if not (x == STARE_X and w == STARA_W and h == H and bgf and nazwa):
            continue
        struct.pack_into("<H", dane, o + 4, 0)
        struct.pack_into("<H", dane, o + 8, NOWA_W)
        for k in range(first, first + nc):
            coff, _ = struct.unpack_from("<II", dane, octl + k * 8)
            cx = struct.unpack_from("<H", dane, coff + 4)[0]
            struct.pack_into("<H", dane, coff + 4, cx + PAD)
        tla.append(nazwa)
    return bytes(dane), tla


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--override", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pliki = {f.upper(): f for f in os.listdir(a.override)}
    wszystkie_tla = set()
    for nazwa in sorted(pliki):
        if not nazwa.endswith(".CHU") or nazwa == "GUIW10.CHU":
            continue
        dane = open(os.path.join(a.override, pliki[nazwa]), "rb").read()
        nowe, tla = poszerz_chu(dane)
        if tla:
            open(os.path.join(a.out, nazwa), "wb").write(nowe)
            wszystkie_tla.update(tla)
            print(nazwa, "okna poszerzone, tla:", ", ".join(tla))
    for t in sorted(wszystkie_tla):
        f = pliki.get(t + ".MOS")
        if not f:
            print("BRAK", t + ".MOS")
            continue
        rgb = czytaj_mos(open(os.path.join(a.override, f), "rb").read())
        if rgb.shape[1] != STARA_W:
            print("POMIJAM", t, rgb.shape)
            continue
        open(os.path.join(a.out, t + ".MOS"), "wb").write(zapisz_mos(poszerz_rgb(rgb)))
        print(t + ".MOS", rgb.shape[1], "->", NOWA_W)
    for t in TLA_Z_ZIELENIA:
        f = pliki.get(t + ".MOS")
        if not f:
            continue
        rgb, n = usun_zielona_obwodke(czytaj_mos(open(os.path.join(a.override, f), "rb").read()))
        open(os.path.join(a.out, t + ".MOS"), "wb").write(zapisz_mos(rgb))
        print(t + ".MOS", "oczyszczone piksele:", n)


if __name__ == "__main__":
    main()
