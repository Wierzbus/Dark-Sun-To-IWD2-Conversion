"""Proste SPL V2.0 (IWD2) z listy efektow - zdolnosci pasywne nadawane przez CLAB (prefiks AP_).

Uklad jak w plikach gry (np. SPIN236): naglowek 0x82 B (0x72 jak V1 + 16 B IWD2), jeden naglowek
rozszerzony 0x28 B (forma 1, miejsce 4 = zdolnosc wrodzona, cel 5 = rzucajacy), efekty po 0x30 B.
CLAB z AP_ stosuje efekty od razu (0x722D50 -> 0x722FDA), wiec efekty maja tryb 9 (trwaly).

  python tools/iwd2_spl.py --out mod/darksun_rasy/darksun_rasy/spl
"""
import argparse
import os
import struct

NONE = 0xFFFFFFFF


def efekt(op, *, p1=0, p2=0, timing=9, res=b"", cel=1, czas=0):
    e = bytearray(0x30)
    struct.pack_into("<HBBiIBBI", e, 0, op, cel, 0, p1, p2, timing, 0, czas)
    e[0x12] = 100                                  # prawdopodobienstwo gorne
    e[0x14:0x1C] = res.ljust(8, b"\0")
    return bytes(e)


def spl(efekty: list[bytes], typ=4) -> bytes:
    h = bytearray(0x82)
    h[0:8] = b"SPL V2.0"
    struct.pack_into("<II", h, 0x08, NONE, NONE)    # nazwa: brak (zdolnosc nie pokazywana w menu)
    struct.pack_into("<H", h, 0x1C, typ)           # 4 = zdolnosc wrodzona
    struct.pack_into("<I", h, 0x34, 1)             # poziom
    struct.pack_into("<II", h, 0x50, NONE, NONE)   # opis
    ext = bytearray(0x28)
    ext[0], ext[2] = 1, 4                          # forma, miejsce: wrodzona
    ext[0x0C] = 5                                  # cel: rzucajacy
    struct.pack_into("<HH", ext, 0x0E, 0, 1)       # zasieg, poziom
    struct.pack_into("<HH", ext, 0x1E, len(efekty), 0)
    struct.pack_into("<H", ext, 0x22, 0)
    struct.pack_into("<H", ext, 0x26, 1)           # pocisk: brak
    struct.pack_into("<IH", h, 0x64, 0x82, 1)
    struct.pack_into("<IHH", h, 0x6A, 0x82 + 0x28, 0, 0)
    return bytes(h) + bytes(ext) + b"".join(efekty)


# Zdolnosci zaszyte w IWD2.exe, przeniesione do CLAB (docs/iwd2_exe_rasy_klasy.md, sekcja 9).
ZDOLNOSCI = {
    # paladyn od 2. poziomu: odpornosc na czar Emotion: Fear (SPWI420); w exe 0x4A3A5A..0x4A3A84
    "DSPALEMF": [efekt(206, res=b"SPWI420")],
    # druid od 9. poziomu: odpornosc na trucizne (opcode 101 Immunity to effect, 25 Poison); w exe 0x4A795E
    "DSDRVEN": [efekt(101, p2=25)],
    # barbarzynca od 1. poziomu: +2 do szybkosci ruchu (opcode 126, p2=0 = dodaj); w exe x1.2 w 0x72E2DC..0x72E31E
    "DSBBNMV": [efekt(126, p1=2, p2=0)],
}


def eff(op, *, p1=0, p2=0, timing=2, res=b"", cel=1, czas=0) -> bytes:
    """EFF V2.0 (0x110 B) - zasob dla opcode 177 (Use EFF file) itp."""
    e = bytearray(0x110)
    e[0:8] = e[8:16] = b"EFF V2.0"
    struct.pack_into("<IIIiIII", e, 0x10, op, cel, 0, p1, p2, timing, czas)
    struct.pack_into("<HH", e, 0x2C, 100, 0)       # prawdopodobienstwo
    e[0x30:0x38] = res.ljust(8, b"\0")
    return bytes(e)


# Efekty (EFF) dla przedmiotow.
EFEKTY = {
    # barbarzynca w ciezkiej zbroi: -2 do szybkosci (znosi DSBBNMV); naklada go opcode 177 z ciezkich zbroi
    "DSBBNARM": eff(126, p1=-2, p2=0, timing=2),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for n, ef in ZDOLNOSCI.items():
        open(os.path.join(a.out, n + ".SPL"), "wb").write(spl(ef))
        print(n, len(ef), "efekt(y)")
    for n, b in EFEKTY.items():
        open(os.path.join(a.out, n + ".EFF"), "wb").write(b)
        print(n, "EFF")


if __name__ == "__main__":
    main()
