"""Zamienia lata exe na makra WeiDU (bajty do wpisania + kontrola oryginalu), zeby instalator sam tworzyl
kopie z IWD2.exe GOG 2.01 bez rozprowadzania gotowych exe.

  python tools/iwd2_paczki_exe.py --orig IWD2.exe --upscale IWD2_1920x1080_test13.exe \
      --rasy IWD2_1920x1080_test19.exe --out-upscale upscale_exe.tpa --out-rasy rasy_exe.tpa

Paczka 1 (upscale): roznice IWD2.exe -> test13 bez lat mula (te naleza do paczki 2).
Paczka 2 (rasy i klasy): roznice IWD2.exe -> test19 poza miejscami paczki 1. Miejsca obu paczek sie nie
pokrywaja, wiec paczke 2 mozna nalozyc na IWD2.exe albo na exe z paczki 1.
Wynik zawiera fragmenty kodu gry (kontrola oryginalu), wiec .tpa to plik budowany - poza Gitem.
"""
import argparse

BASE = 0x400000
# lata mula (darksun_rasy komponent 1) obecne juz w test13 - przenoszone do paczki 2
MUL = [(0x541BC4, 56), (0x542551, 13), (0x544FE6, 25), (0x61C644, 1), (0x7229C9, 1)]
# podglad postaci x2 (test12) daje w ekwipunku poszarpany obraz - haki wycofane (podglad w skali 1)
PODGLAD = [(0x61DE2D, 7), (0x61DF8F, 6), (0x62EBFF, 6), (0x62ED48, 6), (0x77F520, 6), (0x77F5F0, 6)]
# ramka zaznaczenia portretu: bok 64 (= pole) wypadal poza pole z prawej i z dolu -> 62 (oryginal: 44 przy polu 46)
# 0x704EBE: imul eax, ebp, 62; nop x5 / 0x704ED0: shl eax, 2 -> nop x3
RAMKA = [(0x704EBE, bytes.fromhex("6BC53E9090909090")), (0x704ED0, b"\x90\x90\x90")]


def przebiegi(a, b, przerwa=8):
    r, i, n = [], 0, len(a)
    while i < n:
        if a[i] != b[i]:
            j = ost = i
            while j < n and j - ost <= przerwa:
                if a[j] != b[j]:
                    ost = j
                j += 1
            r.append((i, ost + 1 - i))
            i = ost + 1
        else:
            i += 1
    return r


def tpa(nazwa, orig, cel, runs, opis):
    w = [f"// {opis}", "// Plik generowany: tools/iwd2_paczki_exe.py. Offsety w pliku (adres - 0x400000).", ""]
    w.append(f"DEFINE_PATCH_MACRO ~{nazwa}_sprawdz~ BEGIN")
    w.append(f"  SET {nazwa}_ok = (BUFFER_LENGTH = {len(orig)})")
    w.append(f"  SET {nazwa}_zrobione = 1")
    w.append(f"  PATCH_IF {nazwa}_ok BEGIN")
    for o, ln in runs:
        k = min(4, ln)
        if k == 4:
            v, nv, f = int.from_bytes(orig[o:o + 4], "little"), int.from_bytes(cel[o:o + 4], "little"), "LONG_AT"
        else:
            v, nv, f = orig[o], cel[o], "BYTE_AT"
        w.append(f"    PATCH_IF (({f} 0x{o:X}) != 0x{v:X}) BEGIN SET {nazwa}_ok = 0 END")
        w.append(f"    PATCH_IF (({f} 0x{o:X}) != 0x{nv:X}) BEGIN SET {nazwa}_zrobione = 0 END")
    w.append("  END")
    w.append("END")
    w.append("")
    w.append(f"DEFINE_PATCH_MACRO ~{nazwa}_zapisz~ BEGIN")
    for o, ln in runs:
        b = cel[o:o + ln]
        w.append(f"  // 0x{o + BASE:X} ({ln} B)")
        i = 0
        while i + 4 <= ln:
            w.append(f"  WRITE_LONG 0x{o + i:X} 0x{int.from_bytes(b[i:i + 4], 'little'):X}")
            i += 4
        while i < ln:
            w.append(f"  WRITE_BYTE 0x{o + i:X} 0x{b[i]:X}")
            i += 1
    w.append("END")
    return "\n".join(w) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", required=True)
    ap.add_argument("--upscale", required=True)
    ap.add_argument("--rasy", required=True)
    ap.add_argument("--out-upscale", required=True)
    ap.add_argument("--out-rasy", required=True)
    a = ap.parse_args()
    orig = open(a.orig, "rb").read()
    up = bytearray(open(a.upscale, "rb").read())
    rasy = open(a.rasy, "rb").read()
    assert len(orig) == len(up) == len(rasy) == 5029888
    for adr, ln in MUL:
        o = adr - BASE
        up[o:o + ln] = orig[o:o + ln]
    zaj = set()
    for o, ln in przebiegi(orig, up):          # miejsca paczki 1 (przed poprawkami) - poza paczka 2
        zaj.update(range(o, o + ln))
        assert rasy[o:o + ln] == up[o:o + ln], f"test19 rozni sie od paczki 1 w 0x{o + BASE:X}"
    for adr, ln in PODGLAD:
        o = adr - BASE
        up[o:o + ln] = orig[o:o + ln]
    for adr, b in RAMKA:
        o = adr - BASE
        assert up[o] in (0x89, 0xC1), hex(adr)
        up[o:o + len(b)] = b
    r1 = przebiegi(orig, up)
    r2 = []
    for o, ln in przebiegi(orig, rasy):
        bajty = [i for i in range(o, o + ln) if i not in zaj and orig[i] != rasy[i]]
        if bajty:
            assert not any(i in zaj for i in range(bajty[0], bajty[-1] + 1)), hex(o + BASE)
            r2.append((bajty[0], bajty[-1] + 1 - bajty[0]))
    open(a.out_upscale, "w").write(tpa("ds_upscale", orig, bytes(up), r1,
                                       "Paczka 1: IWD2.exe GOG 2.01 -> 1920x1080 (GUI, ekran ladowania, portrety, ikony)"))
    open(a.out_rasy, "w").write(tpa("ds_rasy", orig, rasy, r2,
                                    "Paczka 2: lata ras i klas (mul, polelf, podklasy, zdolnosci klas z 2DA)"))
    print("paczka 1:", len(r1), "miejsc,", sum(l for _, l in r1), "B")
    print("paczka 2:", len(r2), "miejsc,", sum(l for _, l in r2), "B")


if __name__ == "__main__":
    main()
