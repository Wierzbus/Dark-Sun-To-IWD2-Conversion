"""Nowe czary z Podrecznika Gracza 3.5 jako SPL IWD2 (komponent 10 paczki 2).

Kazdy czar powstaje z czaru gry o podobnym wygladzie (`wzor`): z wzoru zostaja naglowek (ikona, szkola, flagi),
pierwszy naglowek rozszerzony (cel, zasieg, pocisk, czas rzucania) i efekty czysto wizualne (VFX, dzwiek); efekty
mechaniczne wzoru wypadaja, a na ich miejsce wchodza efekty z tabeli ponizej. Czar ma 30 naglowkow rozszerzonych
(poziom rzucajacego 1..30), w kazdym czas trwania i wartosci liczone dla tego poziomu.

Czas gry IE: runda = 6 s, minuta D&D = 60 s, 10 minut i godzina = 300 s (godzina gry IE).
Pola efektu: 0x1C liczba kosci, 0x20 scianki, 0x24 rzut obronny (4 Wytrwalosc, 8 Refleks, 0x10 Wola), 0x28 premia.

  python tools/iwd2_czary_phb.py --gra "<katalog IWD2>" --out mod/darksun_rasy/darksun_rasy/spl \
      --tabela mod/darksun_rasy/darksun_rasy/2da/DSCZARY.2DA
"""
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory.resource_reader import GameResources  # noqa: E402

RUNDA, MINUTA, GODZINA = 6, 60, 300
WIZUALNE = {290, 174, 215, 141}          # efekty wzoru, ktore zostaja (grafika / dzwiek)
WOLA, REFLEKS, WYTRWALOSC = 0x10, 0x08, 0x04
OGIEN = 0x0008 << 16


def czas(rodzaj, n=1):
    """funkcja poziom -> sekundy"""
    if rodzaj == "rundy":
        return lambda lv: RUNDA * n * lv
    if rodzaj == "minuty":
        return lambda lv: MINUTA * n * lv
    if rodzaj == "godziny":
        return lambda lv: GODZINA * n * lv
    return lambda lv: n                  # stale (sekundy)


def ef(op, p1=0, p2=0, rzut=0, premia=0, kosci=0, scianki=0, timing=0):
    """opis efektu; p1 moze byc funkcja poziomu"""
    return dict(op=op, p1=p1, p2=p2, rzut=rzut, premia=premia, kosci=kosci, scianki=scianki, timing=timing)


# res, typ (1 czarodziej, 2 kaplan), poziom czaru, wzor, klasy (LISTSPLL), czas, efekty
CZARY = [
    dict(res="SPWI160", typ=1, poz=1, wzor="SPPR114", klasy=dict(BRD=1, CLR=1, SOR=1, WIZ=1), czas=czas("stale", 12),
         nazwa="Cause Fear",
         efekty=[ef(24, rzut=WOLA)]),
    dict(res="SPWI161", typ=1, poz=1, wzor="SPWI104", klasy=dict(BRD=1), czas=czas("stale", RUNDA),
         nazwa="Lesser Confusion",
         efekty=[ef(128, rzut=WOLA)]),
    dict(res="SPWI162", typ=1, poz=1, wzor="SPWI214", klasy=dict(SOR=1, WIZ=1), czas=czas("minuty"),
         nazwa="Enlarge Person",
         efekty=[ef(44, 2), ef(15, -2), ef(0, -1), ef(54, -1)]),
    dict(res="SPWI163", typ=1, poz=1, wzor="SPWI223", klasy=dict(SOR=1, WIZ=1), czas=czas("minuty"),
         nazwa="Reduce Person",
         efekty=[ef(15, 2), ef(44, -2), ef(0, 1), ef(54, 1)]),
    dict(res="SPWI164", typ=1, poz=1, wzor="SPWI102", klasy=dict(BRD=1, SOR=1, WIZ=1), czas=czas("minuty"),
         nazwa="Expeditious Retreat",
         efekty=[ef(126, 200, 2)]),
    dict(res="SPWI165", typ=1, poz=1, wzor="SPWI214", klasy=dict(CLR=1, PAL=1, SOR=1, WIZ=1), czas=czas("minuty"),
         nazwa="Magic Weapon",
         efekty=[ef(54, 1), ef(73, 1)]),
    dict(res="SPWI166", typ=1, poz=1, wzor="SPWI209", klasy=dict(SOR=1, WIZ=1), czas=czas("stale", RUNDA),
         nazwa="True Strike",
         efekty=[ef(54, 20)]),
    dict(res="SPWI167", typ=1, poz=2, wzor="SPWI104", klasy=dict(BRD=1, SOR=2, WIZ=2), czas=czas("rundy"),
         nazwa="Tasha's Hideous Laughter",
         efekty=[ef(109, rzut=WOLA)]),
    dict(res="SPPR160", typ=2, poz=1, wzor="SPPR215", klasy=dict(CLR=1, PAL=1), czas=czas("stale", MINUTA),
         nazwa="Divine Favor",
         efekty=[ef(54, lambda lv: max(1, min(3, lv // 3))), ef(73, lambda lv: max(1, min(3, lv // 3)))]),
    dict(res="SPPR161", typ=2, poz=1, wzor="SPPR115", klasy=dict(CLR=1), czas=czas("minuty"),
         nazwa="Shield of Faith",
         efekty=[ef(0, lambda lv: 2 + min(3, lv // 6), 2)]),
    dict(res="SPPR162", typ=2, poz=1, wzor="SPPR202", klasy=dict(DRD=1, RGR=1), czas=czas("godziny"),
         nazwa="Longstrider",
         efekty=[ef(126, 133, 2)]),
    dict(res="SPPR163", typ=2, poz=1, wzor="SPWI303", klasy=dict(DRD=1), czas=czas("stale", 0),
         nazwa="Produce Flame",
         efekty=[ef(12, lambda lv: min(lv, 5), OGIEN, kosci=1, scianki=6, timing=1)]),
]
KLASY = ["BRD", "CLR", "DRD", "PAL", "RGR", "SOR", "WIZ"]


def efekt_bin(e, lv, t, cel):
    p1 = e["p1"](lv) if callable(e["p1"]) else e["p1"]
    b = bytearray(0x30)
    struct.pack_into("<HBBiIBBI", b, 0, e["op"], cel, 1, p1, e["p2"], e["timing"], 1, 0 if e["timing"] == 1 else t)
    b[0x12] = 100
    struct.pack_into("<IIIi", b, 0x1C, e["kosci"], e["scianki"], e["rzut"], e["premia"])
    return bytes(b)


def wizualny(wz, t, rzut):
    b = bytearray(wz)
    if b[0x0C] in (0, 2):                # timing: na czas -> czas czaru
        struct.pack_into("<I", b, 0x0E, t)
    struct.pack_into("<Ii", b, 0x24, rzut, 0)   # grafika tylko gdy cel nie obronil sie
    return bytes(b)


def zbuduj(gr, c):
    d = gr.read(c["wzor"].lower(), 0x3EE)
    assert d[:8] == b"SPL V2.0", c["wzor"]
    eo, ec = struct.unpack_from("<IH", d, 0x64)
    fo, = struct.unpack_from("<I", d, 0x6A)
    ext0 = bytearray(d[eo:eo + 0x28])
    fc, fi = struct.unpack_from("<HH", ext0, 0x1E)
    wz = [d[fo + (fi + j) * 0x30:fo + (fi + j) * 0x30 + 0x30] for j in range(fc)]
    wiz = [w for w in wz if struct.unpack_from("<H", w, 0)[0] in WIZUALNE]
    mech = [w for w in wz if struct.unpack_from("<H", w, 0)[0] not in WIZUALNE]
    cel = mech[0][2] if mech else 2
    h = bytearray(d[:0x82])
    struct.pack_into("<i", h, 0x08, -1)  # nazwa - wpisuje instalator
    struct.pack_into("<i", h, 0x0C, -1)
    struct.pack_into("<i", h, 0x50, -1)  # opis
    struct.pack_into("<i", h, 0x54, -1)
    struct.pack_into("<H", h, 0x1C, c["typ"])
    struct.pack_into("<I", h, 0x34, c["poz"])
    struct.pack_into("<IH", h, 0x6E, 0, 0)  # bez efektow rzucania
    naglowki, efekty = [], []
    for lv in range(1, 31):
        t = c["czas"](lv)
        fx = [efekt_bin(e, lv, t, cel) for e in c["efekty"]] + [wizualny(w, t, c["efekty"][0]["rzut"]) for w in wiz]
        x = bytearray(ext0)
        struct.pack_into("<H", x, 0x10, lv)
        struct.pack_into("<HH", x, 0x1E, len(fx), len(efekty))
        naglowki.append(bytes(x))
        efekty += fx
    struct.pack_into("<IH", h, 0x64, 0x82, len(naglowki))
    struct.pack_into("<I", h, 0x6A, 0x82 + 0x28 * len(naglowki))
    return bytes(h) + b"".join(naglowki) + b"".join(efekty)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tabela", required=True)
    a = ap.parse_args()
    gr = GameResources(a.gra)
    os.makedirs(a.out, exist_ok=True)
    w = ["2DA V1.0", "0", "                " + "".join(k.ljust(5) for k in KLASY) + "TRA"]
    for i, c in enumerate(CZARY):
        open(os.path.join(a.out, c["res"] + ".SPL"), "wb").write(zbuduj(gr, c))
        w.append(c["res"].ljust(16) + "".join(str(c["klasy"].get(k, 0)).ljust(5) for k in KLASY) + str(1201 + 2 * i))
        print(c["res"], c["nazwa"], "wzor", c["wzor"])
    open(a.tabela, "w").write("\n".join(w) + "\n")


if __name__ == "__main__":
    main()
