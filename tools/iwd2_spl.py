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


def spl(efekty: list[bytes], typ=4, ikona=b"") -> bytes:
    h = bytearray(0x82)
    h[0:8] = b"SPL V2.0"
    struct.pack_into("<II", h, 0x08, NONE, NONE)    # nazwa: brak (zdolnosc nie pokazywana w menu)
    struct.pack_into("<H", h, 0x1C, typ)           # 4 = zdolnosc wrodzona
    struct.pack_into("<I", h, 0x34, 1)             # poziom
    struct.pack_into("<II", h, 0x50, NONE, NONE)   # opis
    h[0x3A:0x42] = ikona.ljust(8, b"\0")          # ikona w menu (zdolnosc GA_; nazwe wpisuje instalator pod 0x08)
    ext = bytearray(0x28)
    ext[0], ext[2] = 1, 4                          # forma, miejsce: wrodzona
    ext[4:12] = ikona.ljust(8, b"\0")
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
    # test33 Dwarven Defender: premia do KP +1 (opcode 0; CLAB na 1/4/7/10 = +4 lacznie)
    "DSDDAC": [efekt(0, p1=1, p2=0)],
    # test33 Dwarven Defender: redukcja obrazen 3/- (opcode 436, p1 = wartosc; CLAB na 6 i 10) - do sprawdzenia w grze
    "DSDDDR": [efekt(436, p1=3, p2=0)],
    # test41 Swashbuckler: Grace +1 Refleks (34; CLAB na 2/11/20), Insightful Strike +2 obrazen (73), unik: DSDDAC
    "DSSWREF": [efekt(34, p1=1, p2=0)],
    "DSSWDMG": [efekt(73, p1=2, p2=0)],
    # test41 Scout: Skirmish +1 KP i +1 obrazen (CLAB na 1/5/9/13/17), Battle Fortitude +1 Wytrwalosc (33)
    "DSSCSK": [efekt(0, p1=1, p2=0), efekt(73, p1=1, p2=0)],
    "DSSCFRT": [efekt(33, p1=1, p2=0)],
    # test41 Favored Soul: odpornosc 10 na ogien (30), elektrycznosc (29), kwas (27)
    "DSFSRFI": [efekt(30, p1=10, p2=0)],
    "DSFSREL": [efekt(29, p1=10, p2=0)],
    "DSFSRAC": [efekt(27, p1=10, p2=0)],
    # test43 Samurai: Iaijutsu Master (11) +1 do ataku (54) i obrazen (73); Swashbuckler: Slippery Mind (17) +2 Wola (35)
    "DSSAIJ": [efekt(54, p1=1, p2=0), efekt(73, p1=1, p2=0)],
    "DSSWWIL": [efekt(35, p1=2, p2=0)],
    # test51 pololbrzym (DS 3.5): pancerz naturalny +2 i rozmiar duzy -1 KP = +1 KP; rozmiar duzy -1 do trafienia
    "DSHGNT": [efekt(0, p1=1, p2=0), efekt(54, p1=-1, p2=0)],
    # test43 Favored Soul: Deity's Weapon Focus (3) +1 do ataku
    "DSFSWF": [efekt(54, p1=1, p2=0)],
    # test43 Inquisitor: odpornosc na zauroczenie i dominacje (opcode 101 Immunity to effect, 5 Charm)
    "DSINCHM": [efekt(101, p2=5)],
    # test43 Hunter of the Dead: Spurn Death's Touch - odpornosc na wysysanie poziomow (101, 216 Level drain)
    "DSHDLD": [efekt(101, p2=216)],
    # test45 klasy potworow (CLAB 1. poziom): odpornosci typu jak w przedmiotach gry (00CIDEAD: opcode 261 na efekt -
    # 24 strach, 25 trucizna, 39 sen, 3 szal, 5 zauroczenie, 109 paraliz, 45 ogluszenie, 78 choroba, 128 zamet,
    # 134 skamienienie, 55 smierc) i widzenie w ciemnosci (63). test46: opcode 261 zamiast 101, jak w grze.
    "DSMNUND": [efekt(261, p2=x) for x in (24, 25, 39, 3, 5, 109, 45, 78, 128, 134, 55)] + [efekt(101, p2=93), efekt(63)],
    "DSMNCON": [efekt(261, p2=x) for x in (24, 25, 39, 3, 5, 109, 45, 78, 128, 134, 55)] + [efekt(63)],
    "DSMNOOZ": [efekt(261, p2=x) for x in (24, 25, 39, 3, 5, 109, 45, 128)],
    "DSMNELE": [efekt(261, p2=x) for x in (25, 39, 109, 45)] + [efekt(63)],
    "DSMNVER": [efekt(261, p2=x) for x in (24, 3, 5, 128)] + [efekt(63)],
    "DSMNDRA": [efekt(261, p2=x) for x in (39, 109)] + [efekt(63)],
    "DSMNDV": [efekt(63)],
}

# Zdolnosci do uzycia (GA_ w CLAB): czas w sekundach (runda = 6 s), nazwe wpisuje instalator (strref pod 0x08).
UZYWANE = {
    # test41 Samurai: Kiai Smite - +3 do ataku (54) i obrazen (73) na 1 runde
    "DSKIAI": (b"SPIN152B", [efekt(54, p1=3, timing=0, czas=6), efekt(73, p1=3, timing=0, czas=6)]),
    # test41 Knight: Fighting Challenge - +1 do ataku, obrazen i Woli (35) na 1 minute
    "DSKNCH": (b"SPWI402B", [efekt(54, p1=1, timing=0, czas=60), efekt(73, p1=1, timing=0, czas=60),
                             efekt(35, p1=1, timing=0, czas=60)]),
    # test43 Dervish: Dervish Dance - +2 do ataku, obrazen i KP (0) na 1 minute
    "DSDERW": (b"SPIN234B", [efekt(54, p1=2, timing=0, czas=60), efekt(73, p1=2, timing=0, czas=60),
                             efekt(0, p1=2, timing=0, czas=60)]),
    # test43 Swashbuckler: Lucky - +4 do wszystkich rzutow obronnych (33/34/35) na 1 runde
    # test50 Gladiator (DS 3.5): Combat Stance - +2 KP na 5 rund (30 s)
    "DSGLSTN": (b"SPIN234B", [efekt(0, p1=2, p2=0, timing=0, czas=30)]),
    "DSSWLCK": (b"SPWI209B", [efekt(33, p1=4, timing=0, czas=6), efekt(34, p1=4, timing=0, czas=6),
                              efekt(35, p1=4, timing=0, czas=6)]),
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
    # test44 Scout w ciezkiej zbroi: -1 KP i -1 obrazen na kazdy stopien Skirmish (znosi DSSCSK); naklada je opcode 177
    # z ciezkich zbroi z IDS 9 = podklasa SCOUT i minimalnym poziomem lotrzyka 1/5/9/13/17 (kity.asm ids_kit)
    "DSSCAC": eff(0, p1=-1, p2=0, timing=2),
    "DSSCDM": eff(73, p1=-1, p2=0, timing=2),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for n, (ik, ef) in UZYWANE.items():
        with open(os.path.join(a.out, n + ".SPL"), "wb") as f:
            f.write(spl(ef, ikona=ik))
    for n, ef in ZDOLNOSCI.items():
        open(os.path.join(a.out, n + ".SPL"), "wb").write(spl(ef))
        print(n, len(ef), "efekt(y)")
    for n, b in EFEKTY.items():
        open(os.path.join(a.out, n + ".EFF"), "wb").write(b)
        print(n, "EFF")


if __name__ == "__main__":
    main()
