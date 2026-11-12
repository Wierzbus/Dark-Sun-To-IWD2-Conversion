"""Naprawia przeskalowane GUI IWD2 (1920x1080) - przebieg od oryginalow.

1. Okna CHU szerokosci 1440 w x=240 (oraz 1434 w x=243 w GUIW10) dostaja
   x=0, w=1920; kontrolki przesuwaja sie o lewy margines. Tla MOS sa
   dopelniane: w wierszach, ktorych skrajny piksel jest przezroczysty
   (0,255,0), margines tez jest przezroczysty, w pozostalych czarny.
2. Kazdy MOS z przezroczystoscia: rozmyte zielone obwodki -> przezroczyste,
   zielen zawsze na pozycji 0 palety kafla.
3. Pola tekstowe (kontrolki typu 3): nowe tlo wyciete z tla okna w rozmiarze
   pola (stare tla mialy 16 px wysokosci i przycinaly tekst).

Uzycie:
  python tools/iwd2_napraw_gui.py --oryginaly KATALOG --out WYNIK [--klucz-gry KATALOG_GRY]
--oryginaly: CHU i MOS z Override przed zmianami. Wynik zawiera tylko pliki zmienione.
"""
import argparse
import os
import struct

import numpy as np

from iwd2_poszerz_tla import ZIELEN, czytaj_mos, usun_zielona_obwodke, zapisz_mos

NOWA_W = 1920
KANDYDACI = {(240, 1440), (243, 1434)}


def okna_chu(dane):
    _, nwin, octl, owin = struct.unpack_from("<8sIII", dane, 0)
    for i in range(nwin):
        o = owin + i * 28
        wid, _, x, y, w, h, bgf, nc, bg, first, _ = struct.unpack_from("<HHHHHHHH8sHH", dane, o)
        kontrolki = []
        for k in range(first, first + nc):
            coff, clen = struct.unpack_from("<II", dane, octl + k * 8)
            kontrolki.append((coff, clen))
        yield dict(o=o, id=wid, x=x, y=y, w=w, h=h, bgf=bgf,
                   bg=bg.split(b"\0")[0].decode("latin-1").upper(), kontrolki=kontrolki)


def poszerz_rgb(rgb, lewy, prawy):
    h = rgb.shape[0]
    out = np.zeros((h, rgb.shape[1] + lewy + prawy, 3), np.uint8)
    out[:, lewy:lewy + rgb.shape[1]] = rgb
    przez_l = (rgb[:, 0] == ZIELEN).all(1)
    przez_p = (rgb[:, -1] == ZIELEN).all(1)
    out[przez_l, :lewy] = ZIELEN
    out[przez_p, lewy + rgb.shape[1]:] = ZIELEN
    return out


def nazwa_pola(stara, zajete, prefiks):
    kand = (prefiks + stara[1:])[:8]
    i = 0
    while kand in zajete:
        i += 1
        kand = (prefiks + stara[1:])[:7 - len(str(i))] + "_" + str(i)
    zajete.add(kand)
    return kand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oryginaly", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pliki = {f.upper(): f for f in os.listdir(a.oryginaly)}
    czytaj = lambda n: open(os.path.join(a.oryginaly, pliki[n]), "rb").read()

    # --- MOS: wczytanie i czyszczenie zieleni
    mos = {}
    zmienione_mos = set()
    for n in pliki:
        if n.endswith(".MOS"):
            rgb = czytaj_mos(czytaj(n))
            if (rgb == ZIELEN).all(2).any():
                rgb, ile = usun_zielona_obwodke(rgb)
                zmienione_mos.add(n[:-4])
            mos[n[:-4]] = rgb

    # --- CHU: poszerzanie okien
    chu = {n: bytearray(czytaj(n)) for n in pliki if n.endswith(".CHU")}
    poszerz_tlo = {}  # nazwa MOS -> (lewy, prawy, szer_oryg)
    for n, d in chu.items():
        for okno in okna_chu(bytes(d)):
            if (okno["x"], okno["w"]) not in KANDYDACI:
                continue
            lewy = okno["x"]
            prawy = NOWA_W - okno["x"] - okno["w"]
            struct.pack_into("<H", d, okno["o"] + 4, 0)
            struct.pack_into("<H", d, okno["o"] + 8, NOWA_W)
            for coff, _ in okno["kontrolki"]:
                cx = struct.unpack_from("<H", d, coff + 4)[0]
                struct.pack_into("<H", d, coff + 4, cx + lewy)
            if okno["bgf"] and okno["bg"]:
                prev = poszerz_tlo.setdefault(okno["bg"], (lewy, prawy, okno["w"]))
                if prev != (lewy, prawy, okno["w"]):
                    print("UWAGA: rozne poszerzenia dla", okno["bg"])
    for t, (lewy, prawy, w) in poszerz_tlo.items():
        if t not in mos:
            print("BRAK tla", t)
            continue
        if mos[t].shape[1] != w:
            print("POMIJAM tlo o innej szerokosci", t, mos[t].shape)
            continue
        mos[t] = poszerz_rgb(mos[t], lewy, prawy)
        zmienione_mos.add(t)

    # sprawdz, czy poszerzone tlo nie jest uzywane przez okno nieposzerzone
    for n, d in chu.items():
        for okno in okna_chu(bytes(d)):
            if okno["bg"] in poszerz_tlo and okno["w"] != NOWA_W:
                print("UWAGA: tlo", okno["bg"], "uzywane tez w", n, okno["id"], "o szer.", okno["w"])

    # --- pola tekstowe
    zajete = set(mos) | {n[:-4] for n in pliki}
    nowe_pola = {}
    for n, d in chu.items():
        for okno in okna_chu(bytes(d)):
            tlo = mos.get(okno["bg"]) if okno["bgf"] else None
            for coff, clen in okno["kontrolki"]:
                cid, cx, cy, cw, ch, typ = struct.unpack_from("<IHHHHB", d, coff)
                if typ != 3:
                    continue
                stare = [bytes(d[coff + 14 + 8 * j: coff + 22 + 8 * j]).split(b"\0")[0].decode("latin-1").upper()
                         for j in range(3)]
                if tlo is None or not any(stare):
                    print("pole bez tla okna:", n, okno["id"], cid & 0xFFFF)
                    continue
                wyc = tlo[cy:cy + ch, cx:cx + cw]
                if wyc.shape[:2] != (ch, cw):
                    print("pole poza tlem:", n, okno["id"], cid & 0xFFFF)
                    continue
                klucz = (okno["bg"], cx, cy, cw, ch)
                if klucz not in nowe_pola:
                    prefiks = "Z" if n == "GUIW10.CHU" else "Y"
                    nowe_pola[klucz] = nazwa_pola(next(s for s in stare if s), zajete, prefiks)
                    mos[nowe_pola[klucz]] = np.ascontiguousarray(wyc)
                    zmienione_mos.add(nowe_pola[klucz])
                nowa = nowe_pola[klucz].encode().ljust(8, b"\0")
                for j in range(3):
                    if stare[j]:
                        d[coff + 14 + 8 * j: coff + 22 + 8 * j] = nowa
                print("pole", n, okno["id"], cid & 0xFFFF, (cw, ch), stare, "->", nowe_pola[klucz])

    for n, d in chu.items():
        if bytes(d) != czytaj(n):
            open(os.path.join(a.out, n), "wb").write(bytes(d))
    for t in sorted(zmienione_mos):
        open(os.path.join(a.out, t + ".MOS"), "wb").write(zapisz_mos(mos[t]))
    print("zmienione CHU:", sum(1 for n, d in chu.items() if bytes(d) != czytaj(n)),
          "MOS:", len(zmienione_mos))


if __name__ == "__main__":
    main()
