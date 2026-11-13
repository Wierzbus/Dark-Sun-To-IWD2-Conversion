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
# dodatki.asm (test19) w martwym kodzie dawnej piesci mnicha 0x723430..0x7237A1
ORG2, KONIEC2 = 0x723430, 0x7237A1
HAKI2 = [
    (0x585D55, "jmp", "sneak_klasa", 2),     # atak z zaskoczenia: klasy z DSKLASY (SNEAK_ATTACK)
    (0x73BC76, "jmp", "wrog_klasa", 22),     # preferowany wrog (atak): klasy z DSKLASY (FAVORED_ENEMY)
    (0x73BCD0, "call", "wrog_atak", 0),      # preferowany wrog: premia do ataku z DSWROG.2DA
    (0x73DD34, "jmp", "wrog_obr", 20),       # preferowany wrog: premia do obrazen z DSWROG.2DA
    (0x4A48CF, "call", "aura", 0),           # aura paladyna (efekt 0x4A4xxx): klasy z DSKLASY (AURA_COURAGE)
    (0x6F8EF4, "call", "aura", 0),           # aura paladyna (aktualizacja co runde)
]
# tablica skokow klikniecia klasy (0x61C1A8, indeks = klasa - 1): 0x61C0A5 = okno 52
KLASY_OKNO52 = [1, 2, 4, 5, 8, 10]          # barbarzynca, bard, druid, wojownik, tropiciel, zaklinacz
DANE = [
    (0x61CEF4, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy zmianie bostwa
    (0x615CFE, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy przycisku Gotowe
]


def nasm(src, org=ORG, defs=None):
    with tempfile.TemporaryDirectory() as t:
        b, l = os.path.join(t, "o.bin"), os.path.join(t, "o.lst")
        d = [f"-D{k}=0x{v:X}" for k, v in (defs or {}).items()]
        subprocess.run(["nasm", "-f", "bin", *d, "-l", l, "-o", b, src], check=True, cwd=os.path.dirname(src))
        dane = open(b, "rb").read()
        lst = open(l).read().splitlines()
    etykiety = {}
    for i, w in enumerate(lst):
        m = re.match(r"\s*\d+\s+([a-z_0-9]+):\s*$", w)
        if m:
            for k in lst[i + 1:i + 8]:
                mm = re.match(r"\s*\d+\s+([0-9A-F]{8})\s", k)
                if mm:
                    etykiety[m.group(1)] = org + int(mm.group(1), 16)
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
    oczek = {0x585D55: "8b068bceff5010", 0x73BCD0: "e88babe0ff", 0x4A48CF: "e8bc30faff", 0x6F8EF4: "e897ead4ff",
             0x73BC76: "8a0dac7c8400", 0x73DD34: "33c0a0ac7c8400"}
    for adr, h in oczek.items():
        assert d[adr - BASE:adr - BASE + len(h) // 2].hex() == h, hex(adr)
    kod2, et2 = nasm(os.path.join(ASM, "dodatki.asm"), ORG2,
                     {k: et[k] for k in ("zdolnosc", "liczba", "tabela2da", "sneak_poziom")})
    if ORG2 + len(kod2) > KONIEC2:
        sys.exit("dodatki.asm wychodzi poza 0x7237A1")
    d[ORG2 - BASE:ORG2 - BASE + len(kod2)] = kod2
    et.update(et2)
    for adr, rodzaj, lab, nop in HAKI + HAKI2:
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
    # barbarzynca: szybkosc x1.2 bez ciezkiej zbroi (0x72E2DC..0x72E31E) wylaczona - premia z CLAB (AP_DSBBNMV),
    # a ciezkie zbroje nakladaja barbarzyncy kare DSBBNARM.EFF (opcode 177 w efektach zalozenia ITM)
    assert d[0x72E2F6 - BASE:0x72E2F8 - BASE] == b"\x74\x26", "0x72E2F6: oczekiwano je short"
    d[0x72E2F6 - BASE] = 0xEB
    s = sekcje(d)
    struct.pack_into("<I", d, s[".text"] + 8, max(0x446000, struct.unpack_from("<I", d, s[".text"] + 8)[0]))
    struct.pack_into("<I", d, s[".data"] + 8, max(0x176000, struct.unpack_from("<I", d, s[".data"] + 8)[0]))
    open(a.out, "wb").write(d)
    for k in ("klasa_wiersz", "clab", "szukaj_klase"):
        print(k, hex(et[k]))
    print("koniec podklasy.asm", hex(ORG + len(kod)), "dodatki.asm", hex(ORG2 + len(kod2)))
    print("zapisano", a.out)


if __name__ == "__main__":
    main()
