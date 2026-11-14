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
# rasy.asm (test20) w nowej sekcji PE .dsras (adres 0xA21000, 4 KB) na koncu pliku
SEKCJA_NAZWA, SEKCJA_RVA, SEKCJA_ROZM = b".dsras", 0x621000, 0x2000
ORG3 = BASE + SEKCJA_RVA
DANE3 = 0xA22000                             # zmienne kodu ras (druga strona sekcji)
# (adres, oryginalne bajty, rodzaj, etykieta, nop)
HAKI3 = [
    (0x71E996, "33c08a8766090000", "jmp", "rasa_awans", 3),      # awans: tablica RLAB rasy + SR_LEVEL
    (0x722862, "8b54245681e2ff000000", "jmp", "wzrok", 5),       # widzenie w ciemnosci z DSRASY
    (0x722DE3, None, "call", "poziom", 0),                       # procedura CLAB: poziom postaci dla klasy 12
    (0x73BC10, "807e2605c7442414000000007538", "jmp", "miot_atak", 9),   # bron miotana (atak)
    (0x73CA66, "8a462633ff3c057530", "jmp", "miot_info", 4),     # bron miotana (informacja)
    (0x73C8C0, "5556578b7c2410", "jmp", "wrogowie", 2),          # wrogowie rasy / olbrzymy
]
# progresja klas (test21): PW 0x542CB0, rzuty obronne 0x542610, premia do ataku 0x546B60 - tablice z DSKLPROG.2DA
HP_MIEJSCA = [(0x542D30, "8d8f34030000", "hp_ecx"), (0x542D90, "8d9710030000", "hp_edx"),
              (0x542DDA, "8d8f58030000", "hp_ecx"), (0x542E24, "8d877c030000", "hp_eax"),
              (0x542E6E, "8d97c4030000", "hp_edx")]
SV_MIEJSCA = [0x542677, 0x5426C3, 0x54270F, 0x54275B, 0x5427A7, 0x5427F3, 0x54283F, 0x54288B, 0x5428D7, 0x542923,
              0x54296F]                    # klasy 1..11, "lea ecx, [edi+SAVExxx]"
BAB_BLOKI = [(1, 0x546BC6, 0x546BF7), (2, 0x546C17, 0x546C48), (3, 0x546C68, 0x546C99), (4, 0x546CB9, 0x546CEA),
             (5, 0x546D0A, 0x546D3B), (7, 0x546D5B, 0x546D8C), (8, 0x546DAC, 0x546DDD), (9, 0x546DFF, 0x546E30),
             (10, 0x546E52, 0x546E83), (11, 0x546EA5, 0x546ED6)]   # (klasa, poczatek odczytu, "push eax" po nim)
# test22: postac dla rzutow (0x5429B0) i PW (0x542FA0) - podklasa z postaci (+0x80C); (adres call, cel, etykieta)
CTX_WYWOLANIA = [(a, 0x5429B0, "ctx_sv_ebp") for a in (0x5D8F3A, 0x5D8F5B, 0x5D8F7C, 0x5D8FAB, 0x5D8FD4, 0x5D8FFD)] + \
                [(a, 0x5429B0, "ctx_sv_esi") for a in (0x612A1E, 0x612A3F, 0x612A60, 0x737A05, 0x737A20, 0x737A3B,
                                                       0x737DB8, 0x737DD3, 0x737DEE)] + \
                [(0x5D908F, 0x542FA0, "ctx_hp_ebp"), (0x6129EB, 0x542FA0, "ctx_hp_esi")]
# test24: listy czarow podklas - miejsca liczace adres listy klasy z 0x5CA5D0 (adres call, etykieta haka z postacia)
LISTY_KLAS = [(0x4BCA66, "lk_esp70"),                          # efekt nauki czaru czarodzieja (cel efektu)
              (0x5D9BAB, "lk_espa4"), (0x5D9C50, "lk_espa4"),  # ekran wyboru czarow barda / zaklinacza
              (0x5E14B0, "lk_esp94"), (0x5E152B, "lk_esp94"),  # j.w. (druga funkcja ekranu)
              (0x60EFD2, "lk_esp90"), (0x60F092, "lk_esp90"),  # ekran czarow kreatora (klasa z postaci +0x3E3E)
              (0x61827A, "lk_esp1c"), (0x618496, "lk_esp1c"),  # nauka czarow czarodzieja przy awansie
              (0x618D5F, "lk_esp60"), (0x618DBB, "lk_esp60"),  # j.w. (0x618D10)
              (0x71EABB, "lk_ebp")]                            # awans: czary kaplana / druida / paladyna / tropiciela
POZIOM_CZARU = [0x4ED086, 0x629996, 0x62B3A8, 0x716728]        # call 0x5CAC30 (poziom czaru klasy)
# premia za bron miotana czytana z MIOT zamiast 0x84EAA8 (operand instrukcji mov)
MIOT_OPERANDY = [0x73BC4E, 0x73CA9B]


def dodaj_sekcje(d):
    """Dopisuje sekcje .dsras (RWX) na koncu pliku; zwraca offset w pliku. Gdy juz jest - zwraca jej offset."""
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    sh = pe + 24 + opt
    for i in range(n):
        if bytes(d[sh + 40 * i:sh + 40 * i + 8]).rstrip(b"\0") == SEKCJA_NAZWA:
            return struct.unpack_from("<I", d, sh + 40 * i + 20)[0]
    o = sh + 40 * n
    assert not any(d[o:o + 40]), "brak miejsca na naglowek sekcji"
    ost = sh + 40 * (n - 1)
    assert struct.unpack_from("<I", d, ost + 12)[0] + 0x6000 <= SEKCJA_RVA, "RVA sekcji zajete"
    raw = len(d)
    assert raw % 0x1000 == 0
    d[o:o + 40] = SEKCJA_NAZWA.ljust(8, b"\0") + struct.pack("<IIIIIIHHI", SEKCJA_ROZM, SEKCJA_RVA, SEKCJA_ROZM, raw,
                                                               0, 0, 0, 0, 0xE0000060)
    struct.pack_into("<H", d, pe + 6, n + 1)
    struct.pack_into("<I", d, pe + 24 + 56, SEKCJA_RVA + SEKCJA_ROZM)    # SizeOfImage
    d += b"\0" * SEKCJA_ROZM
    return raw


# tablica skokow klikniecia klasy (0x61C1A8, indeks = klasa - 1): 0x61C0A5 = okno 52
KLASY_OKNO52 = [1, 2, 4, 5, 8, 10]          # barbarzynca, bard, druid, wojownik, tropiciel, zaklinacz
DANE = [
    # operand imm32 (instrukcje: 0x61CEF4 mov ecx, 0xFF8000 / 0x615CFE and eax, 0xFF8000). Do test19 wlacznie
    # zapis szedl pod adres instrukcji i niszczyl jej kod (blad poprawiony w test20).
    (0x61CEF5, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy zmianie bostwa
    (0x615CFF, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy przycisku Gotowe
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
    kod3, et3 = nasm(os.path.join(ASM, "rasy.asm"), ORG3, {k: et[k] for k in ("clab", "komorka", "tabela2da")})
    if ORG3 + len(kod3) > DANE3:
        sys.exit("rasy.asm wchodzi na zmienne 0xA22000")
    raw3 = dodaj_sekcje(d)
    d[raw3:raw3 + len(kod3)] = kod3
    kod2, et2 = nasm(os.path.join(ASM, "dodatki.asm"), ORG2,
                     {k: et[k] for k in ("zdolnosc", "liczba", "tabela2da", "sneak_poziom")})
    if ORG2 + len(kod2) > KONIEC2:
        sys.exit("dodatki.asm wychodzi poza 0x7237A1")
    d[ORG2 - BASE:ORG2 - BASE + len(kod2)] = kod2
    et.update(et2)
    for adr, h, rodzaj, lab, nop in HAKI3:
        if h:
            assert d[adr - BASE:adr - BASE + len(h) // 2].hex().startswith(h[:len(h) // 2 * 2]), hex(adr)
    assert d[0x722DE3 - BASE] == 0xE8 and struct.unpack_from("<i", d, 0x722DE4 - BASE)[0] + 0x722DE8 == 0x447990
    for adr in MIOT_OPERANDY:
        assert struct.unpack_from("<I", d, adr - BASE)[0] == 0x84EAA8, hex(adr)
        struct.pack_into("<I", d, adr - BASE, et3["miot_wart"])
    et.update(et3)
    for adr, h, lab in HP_MIEJSCA:
        o = adr - BASE
        assert d[o:o + 6].hex() == h, hex(adr)
        d[o:o + 6] = b"\xE8" + struct.pack("<i", et[lab] - (adr + 5)) + b"\x90"
    # barbarzynca: bez wymuszonej kosci 12 (tablica HPBARB z DSKLPROG albo domyslnie)
    assert d[0x542D50 - BASE:0x542D58 - BASE].hex() == "c744241c0c000000"
    d[0x542D54 - BASE] = 0
    for k, adr in enumerate(SV_MIEJSCA, 1):
        o = adr - BASE
        assert d[o:o + 2].hex() == "8d8f" and d[o + 4:o + 6] == b"\0\0", hex(adr)
        d[o:o + 6] = b"\xE8" + struct.pack("<i", et[f"sv_{k}"] - (adr + 5)) + b"\x90"
    for k, a0, a1 in BAB_BLOKI:
        o = a0 - BASE
        assert d[o:o + 3].hex() == "0fbf8e" and d[a1 - BASE - 2:a1 - BASE].hex() == "8b00", hex(a0)
        kod_b = bytes([0x6A, k]) + b"\xE8" + struct.pack("<i", et["bab_tab"] - (a0 + 7)) + bytes([0xEB, a1 - (a0 + 9)])
        d[o:a1 - BASE] = kod_b + b"\x90" * (a1 - a0 - len(kod_b))
    for adr, cel, lab in CTX_WYWOLANIA:
        o = adr - BASE
        assert d[o] == 0xE8 and struct.unpack_from("<i", d, o + 1)[0] + adr + 5 == cel, hex(adr)
        struct.pack_into("<i", d, o + 1, et[lab] - (adr + 5))
    # test23: domeny bostwa podklasy kaplana DS (hak 0x5CA910, maski kitu w wywolaniach listy domen)
    o = 0x5CA910 - BASE
    assert d[o:o + 6].hex() == "8b4424048b00"
    d[o:o + 6] = b"\xE9" + struct.pack("<i", et["domena"] - 0x5CA915) + b"\x90"
    for adr, h in ((0x5E62E6, "81e600 80ff00"), (0x60B85B, "250080ff00")):
        o = adr - BASE
        h = h.replace(" ", "")
        assert d[o:o + len(h) // 2].hex() == h, hex(adr)
        struct.pack_into("<I", d, o + len(h) // 2 - 4, 0xFFFF8000)
    for adr, lab in LISTY_KLAS:
        o = adr - BASE
        assert d[o] == 0xE8 and struct.unpack_from("<i", d, o + 1)[0] + adr + 5 == 0x5CA5D0, hex(adr)
        struct.pack_into("<i", d, o + 1, et[lab] - (adr + 5))
    for adr in POZIOM_CZARU:
        o = adr - BASE
        assert d[o] == 0xE8 and struct.unpack_from("<i", d, o + 1)[0] + adr + 5 == 0x5CAC30, hex(adr)
        struct.pack_into("<i", d, o + 1, et["poziom_czaru"] - (adr + 5))
    o = 0x546F37 - BASE
    assert d[o:o + 6].hex() == "8d8ec4180000"
    d[o:o + 6] = b"\xE8" + struct.pack("<i", et["bab_mnich"] - 0x546F3C) + b"\x90"
    haki = [(a, r, l, n) for a, r, l, n in HAKI if a != 0x546030] + [(0x546030, "jmp", "clab_rasa", 4)]
    for adr, rodzaj, lab, nop in haki + HAKI2 + [(a, r, l, n) for a, _, r, l, n in HAKI3]:
        o = adr - BASE
        op = 0xE9 if rodzaj == "jmp" else 0xE8
        d[o:o + 5] = bytes([op]) + struct.pack("<i", et[lab] - (adr + 5))
        d[o + 5:o + 5 + nop] = b"\x90" * nop
    for k in KLASY_OKNO52:
        struct.pack_into("<I", d, 0x61C1A8 - BASE + 4 * (k - 1), 0x61C0A5)
    assert d[0x61CEF4 - BASE] == 0xB9 and d[0x615CFE - BASE] == 0x25, "maska bostw: oczekiwano mov ecx / and eax"
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
    print("koniec podklasy.asm", hex(ORG + len(kod)), "dodatki.asm", hex(ORG2 + len(kod2)), "rasy.asm", hex(ORG3 + len(kod3)))
    print("zapisano", a.out)


if __name__ == "__main__":
    main()
