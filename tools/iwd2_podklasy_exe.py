"""Wstawia kod podklas (mod/darksun_rasy/darksun_rasy/asm/podklasy.asm) i late polelfa do kopii IWD2.exe.

  python tools/iwd2_podklasy_exe.py --base IWD2_1920x1080_test15.exe --out IWD2_1920x1080_test16.exe

Kod podklas trafia w koniec .text (0x846900..0x847000); haki w kodzie gry dostaja adresy etykiet
z listingu nasm, wiec po zmianie asm wystarczy ponownie uruchomic skrypt.
Wymaga nasm. Plik bazowy musi miec .text o rozmiarze wirtualnym >= 0x446000 i .data >= 0x176000
(oba ustawia ten skrypt).
"""
import argparse
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASM = os.path.join(ROOT, "mod", "darksun_rasy", "darksun_rasy", "asm")
ORG = 0x846900
BASE = 0x400000

# (adres, rodzaj, etykieta, liczba nop po instrukcji)
HAKI = [
    (0x541DA0, "jmp", "klasa_wiersz", 0),
    (0x60D6C3, "jmp", "okno52", 8),
    (0x60D753, "jmp", "paladyn4", 0),
    (0x621DBE, "call", "klik", 1),
    (0x615C50, "call", "gotowe", 1),
    (0x61CD4A, "jmp", "k_getkit", 0),
    (0x61D031, "jmp", "k_help", 2),
    (0x6100F0, "jmp", "k_etykieta", 0),
    (0x61012E, "jmp", "k_petla", 4),
    (0x61001B, "jmp", "k_mag", 0),
    (0x546030, "jmp", "clab", 4),
    (0x723417, "jmp", "mnich", 20),          # piesc mnicha z CLAB (wpisy FI_)
    (0x585DA5, "jmp", "unik", 22),           # Evasion: progi z DSKLASY.2DA
    (0x73D95B, "jmp", "uncanny_flanka", 0),  # Uncanny Dodge (flanka): progi z DSKLASY.2DA
    (0x585D64, "jmp", "sneak_kosci", 0),     # atak z zaskoczenia: kosci z DSSNEAK.2DA
    (0x585D80, "jmp", "sneak_scianki", 0),   # atak z zaskoczenia: rozmiar kosci z DSSNEAK.2DA
]
# tablica skokow klikniecia klasy (0x61C1A8, indeks = klasa - 1): 0x61C0A5 = okno 52
KLASY_OKNO52 = [1, 2, 4, 5, 8, 10]          # barbarzynca, bard, druid, wojownik, tropiciel, zaklinacz
DANE = [
    (0x61CEF4, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy zmianie bostwa
    (0x615CFE, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy przycisku Gotowe
]


def nasm(src, org_check=None):
    with tempfile.TemporaryDirectory() as t:
        b, l = os.path.join(t, "o.bin"), os.path.join(t, "o.lst")
        subprocess.run(["nasm", "-f", "bin", "-l", l, "-o", b, src], check=True, cwd=os.path.dirname(src))
        dane = open(b, "rb").read()
        lst = open(l).read().splitlines()
    etykiety = {}
    for i, w in enumerate(lst):
        m = re.match(r"\s*\d+\s+([a-z_0-9]+):\s*$", w)
        if m:
            for k in lst[i + 1:i + 8]:
                mm = re.match(r"\s*\d+\s+([0-9A-F]{8})\s", k)
                if mm:
                    etykiety[m.group(1)] = ORG + int(mm.group(1), 16)
                    break
    return dane, etykiety


def sekcje(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, pe + 6)[0]
    o = pe + 24 + struct.unpack_from("<H", d, pe + 20)[0]
    return {bytes(d[o + 40 * i:o + 40 * i + 8]).rstrip(b"\0").decode(): o + 40 * i for i in range(n)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = bytearray(open(a.base, "rb").read())
    kod, et = nasm(os.path.join(ASM, "podklasy.asm"))
    if ORG + len(kod) > 0x847000:
        sys.exit("kod podklas wychodzi poza .text")
    d[ORG - BASE:ORG - BASE + len(kod)] = kod
    for adr, rodzaj, lab, nop in HAKI:
        o = adr - BASE
        op = 0xE9 if rodzaj == "jmp" else 0xE8
        d[o:o + 5] = bytes([op]) + struct.pack("<i", et[lab] - (adr + 5))
        d[o + 5:o + 5 + nop] = b"\x90" * nop
    for k in KLASY_OKNO52:
        struct.pack_into("<I", d, 0x61C1A8 - BASE + 4 * (k - 1), 0x61C0A5)
    for adr, b in DANE:
        d[adr - BASE:adr - BASE + len(b)] = b
    # polelf: GetRaceRow (0x541A42), nazwa rasy (0x544EC6), zdolnosci rasowe (0x7228E2), okno podras (0x61C640)
    pe, _ = nasm(os.path.join(ASM, "halfelf.asm"))
    d[0x541A42 - BASE:0x541A42 - BASE + len(pe)] = pe
    if len(pe) != 0x38:
        sys.exit(f"halfelf.asm: {len(pe)} B zamiast 56")
    d[0x544EC6 - BASE:0x544EC6 - BASE + 10] = b"\xB8" + struct.pack("<I", 0xFFFFFFFF) + b"\xE9" + struct.pack(
        "<i", 0x545009 - (0x544EC6 + 10))                # mov eax, STRREF (wpisuje WeiDU); jmp 0x545009
    assert d[0x7228E2 - BASE:0x7228E4 - BASE] == b"\x0F\x84", "0x7228E2: oczekiwano je rel32"
    rel = struct.unpack_from("<i", d, 0x7228E4 - BASE)[0]
    d[0x7228E2 - BASE:0x7228E8 - BASE] = b"\xE9" + struct.pack("<i", rel + 1) + b"\x90"
    struct.pack_into("<I", d, 0x61C640 - BASE, 0x61C562)  # przycisk polelfa -> okno podras (54)
    # zdolnosci klas przeniesione do CLAB (AP_ + SPL z tools/iwd2_spl.py):
    # paladyn >= 2: odpornosc na SPWI420 (Emotion: Fear) - warunek "poziom < 2" zawsze prawdziwy
    assert d[0x4A3A84 - BASE:0x4A3A86 - BASE] == b"\x0F\x8C", "0x4A3A84: oczekiwano jl rel32"
    rel = struct.unpack_from("<i", d, 0x4A3A86 - BASE)[0]
    d[0x4A3A84 - BASE:0x4A3A8A - BASE] = b"\xE9" + struct.pack("<i", rel + 1) + b"\x90"
    # Uncanny Dodge (ZRE do KP) 0x73BA1D: call uncanny_zre; jnz 0x73BA42; nop x7
    o = 0x73BA1D - BASE
    d[o:o + 5] = b"\xE8" + struct.pack("<i", et["uncanny_zre"] - 0x73BA22)
    d[o + 5:o + 11] = b"\x0F\x85" + struct.pack("<i", 0x73BA42 - 0x73BA28)
    d[o + 11:o + 18] = b"\x90" * 7
    # CLAB: nieznany prefiks (np. FI_ piesci mnicha) bez asercji - 0x723093: jmp 0x7230AF
    o = 0x723093 - BASE
    d[o:o + 5] = b"\xE9" + struct.pack("<i", 0x7230AF - 0x723098)
    # druid >= 9: odpornosc na trucizne naturalna w obsludze trucizny - warunek "poziom < 9" zawsze prawdziwy
    assert d[0x4A795E - BASE:0x4A7960 - BASE] == b"\x7C\x0D", "0x4A795E: oczekiwano jl short"
    d[0x4A795E - BASE] = 0xEB
    s = sekcje(d)
    struct.pack_into("<I", d, s[".text"] + 8, max(0x446000, struct.unpack_from("<I", d, s[".text"] + 8)[0]))
    struct.pack_into("<I", d, s[".data"] + 8, max(0x176000, struct.unpack_from("<I", d, s[".data"] + 8)[0]))
    open(a.out, "wb").write(d)
    for k in ("klasa_wiersz", "clab", "szukaj_klase"):
        print(k, hex(et[k]))
    print("zapisano", a.out)


if __name__ == "__main__":
    main()
