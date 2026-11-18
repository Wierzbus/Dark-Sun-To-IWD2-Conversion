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
SEKCJA_NAZWA, SEKCJA_RVA, SEKCJA_ROZM = b".dsras", 0x621000, 0xB000   # test54 0x9000, test56 0xB000 (atuty.asm od 0xA28000)
ORG3 = BASE + SEKCJA_RVA
DANE3 = 0xA22000                             # zmienne kodu ras (druga strona sekcji)
ORG4 = 0xA26000                              # kity.asm: tabela podklas 0xA23000 (255 wpisow), zmienne 0xA25000, kod 0xA26000
ORG5, DANE5 = 0xA28000, 0xA2A000             # atuty.asm: kod, dane (test56: tablice rang ekranow 192 dword, oczekujace, PREM)
# haki podklas (kity.asm) - zastepuja haki podklasy.asm o tych samych adresach; (adres, oczekiwane bajty, rodzaj, etykieta, nop)
HAKI4 = [
    (0x541DA0, "518b44240c", "jmp", "klasa_wiersz2", 0),         # GetClassRow: wiersz podklasy po (bit, klasa)
    (0x60D6C3, "0f848f000000", "jmp", "okno52", 8),              # okno 52: przyciski podklas klasy
    (0x60D753, "e983000000", "jmp", "paladyn52", 0),             # okno 52: podklasy paladyna od przycisku 4
    (0x60D7D2, "c644246003", "jmp", "mnich52", 0),               # okno 52: podklasy mnicha od przycisku 4
    (0x60D871, "8b5424448d42ff", "jmp", "podswietl", 2),         # zaznaczenie wybranej podklasy
    (0x621DBE, "89820c080000", "call", "klik52", 1),             # klikniecie w oknie 52
    (0x615C50, "8bad0c080000", "call", "gotowe52", 1),           # Gotowe: podklasa opcjonalna
    (0x61CD4A, "83f80b774f", "jmp", "getkit_k", 0),              # okno 12 kaplana: przyciski 14.. = podklasy
    (0x61CCCE, "83f80b774f", "jmp", "getkit_m", 0),              # okno 12 czarodzieja
    (0x61012E, "83ff0d0f8e0a", "jmp", "petla_k", 4),             # okno 12 kaplana: etykiety przyciskow podklas
    (0x61001B, "e932010000", "jmp", "petla_m", 0),               # okno 12 czarodzieja
    (0x61D031, "6a00686c638a00", "jmp", "pomoc12", 2),           # okno 12: opis podklasy
    (0x61C09E, "ff248da8c16100", "jmp", "okno_klasy", 2),        # klik klasy: okno 52, gdy klasa ma podklasy DS
    # test26: numer podklasy w bajcie klasy postaci (+0x8A8 + klasa - 1 = plik CRE 0x30C + klasa - 1)
    (0x61BF5D, "89b80c080000", "call", "klasa_zeruj", 1),        # kreator: klik klasy - kit 0, bajty zerowane
    (0x61CF0E, "898a0c080000", "call", "zapisz12", 1),           # kreator: klik w oknie 12 - bajt klasy
    (0x722D9C, "e8cf570000", "call", "kit_722", 0),              # procedura CLAB: kit z bajtu klasy
    (0x5D96DB, "8bbf0c080000", "call", "abclas_aw", 1),           # ABCLASRQ (awans): podklasa tej klasy
    (0x60BEFD, "8bbf0c080000", "call", "abclas_kr", 1),           # ABCLASRQ (kreator)
    (0x611EDE, "e88d661100", "call", "clss_kit", 0),              # CLSSRSMD (odpornosci)
    (0x62193F, "8bb60c080000", "call", "klist_kit", 1),           # opis KITLIST
    # test26: okno 6 ekranu awansu (GUIREC.CHU)
    (0x5E1020, "8a8606010000", "jmp", "okno6_czy", 1),           # okno 6 tez dla klas z podklasami DS
    (0x5DA8EB, "83ff040f8fd9000000", "jmp", "inne6", 4),         # przyciski gry tylko dla paladyna i mnicha
    (0x5DA9FB, "8b4c24246a00", "jmp", "okno6_po", 1),            # przyciski podklas DS
    (0x5ED5A0, "a1dcf68c00", "jmp", "getkit6", 0),               # GetKit okna 6
    (0x5ED913, "6a00686c638a00", "jmp", "pomoc6", 2),            # opis podklasy po kliknieciu
    (0x5E2089, "8a8e0601000033c0", "jmp", "gotowe6", 3),         # Gotowe okna 6
    (0x5E2E39, "8b8d460800008b857c0700000bc18b4c241089810c080000", "jmp", "kit_awans", 19),  # zatwierdzenie podklasy
    # test29: kolumny podklas w tabelach klas (kolumna o nazwie podklasy, np. BARBARIAN_F)
    (0x763D26, "8d4dff4a3bc8", "call", "featclas", 1),           # FEATCLAS: premiowe atuty przy awansie
    (0x763DBA, "8d41ff3bc2", "call", "skillpts", 0),             # SKILLPTS: punkty umiejetnosci
    # test30: slot 1 = klasy prestizowe (DSPREST.2DA)
    (0x5E8DB8, "8bf0f7de1bf6f7de", "jmp", "prest54", 3),         # okno 54 awansu: przycisk klasy 1 wg warunkow
    (0x7647C2, "3b7424187424", "jmp", "xp_kara", 1),             # kara PD za wieloklasowosc bez klasy 1
    (0x764764, "3bf5742c568bcb", "jmp", "xp_najw", 2),           # najwyzsza klasa (kara PD) bez klasy 1
    # test31: szal barbarzyncy z DSKLASY (GREATER_RAGE, TIRELESS_RAGE) zamiast poziomu klasy 1
    (0x4A5C71, "6a018d8b20090000e8121dfaff83f8140f8d09010000", "jmp", "szal_zmecz", 17),
    (0x71E66F, "6a018d8e20090000e81493d2ff83f80f7c1a6a018bcbe80693d2ff83f80f7d0c", "jmp", "szal_atut", 27),
    (0x5E5B1A, "6a018d8d20090000e8691ee6ff83f80f0f8c24060000", "jmp", "szal_awans", 17),
    # test34: czary klas prestizowych (DSPREST SPELLCLASS) - poziom klasy rzucajacej + poziomy klasy prestizowej
    (0x5432E3, "e8a846f0ff", "call", "cz_lvl", 0),               # 0x5431E0 miejsca na czary: bard
    (0x543372, "e81946f0ff", "call", "cz_lvl", 0),               # zaklinacz
    (0x54351B, "e87044f0ff", "call", "cz_lvl", 0),               # paladyn
    (0x5435A8, "e8e343f0ff", "call", "cz_lvl", 0),               # tropiciel
    (0x543637, "e85443f0ff", "call", "cz_lvl", 0),               # czarodziej
    (0x543400, "e84b45f0ff", "call", "cz_maska", 0),             # kaplan (maska 4)
    (0x54348E, "e8bd44f0ff", "call", "cz_maska", 0),             # druid (maska 8)
    (0x71EB3B, "e8508ed2ff", "call", "cz_lvl", 0),               # awans: najwyzszy krag czarow kaplana / druida
    (0x716806, "e88511d3ff", "call", "cz_lvl", 0),               # domeny kaplana: najwyzszy krag
    (0x5E62B1, "e8da16e6ff", "call", "cz_lvl", 0),               # awans kaplana: domeny
    # test35: poziom rzucajacego (0x75EA..: najwyzszy z ksiag; paladyn / tropiciel polowa od 4.)
    (0x75EB49, "e8428eceff", "call", "cz_lvl", 0),
    (0x75EB59, "e8328eceff", "call", "cz_lvl", 0),
    (0x75EB6E, "e81d8eceff", "call", "cz_lvl", 0),
    # test36: okno 8 awansu (wybor znanych czarow barda / zaklinacza) dla klasy prestizowej z SPELLCLASS 2 / 10
    (0x5D9A00, "e88bdfe6ff", "call", "cz_lvl", 0),               # okno 8: liczba znanych czarow barda
    (0x5D9ACF, "e8bcdee6ff", "call", "cz_lvl", 0),               # zaklinacza
    (0x5E12D3, "e8b866e6ff", "call", "cz_lvl", 0),               # czy pokazac okno 8: bard (stary poziom)
    (0x5E133D, "e84e66e6ff", "call", "cz_lvl", 0),               # bard (nowy)
    (0x5E13AF, "e8dc65e6ff", "call", "cz_lvl", 0),               # zaklinacz (stary)
    (0x5E141A, "e87165e6ff", "call", "cz_lvl", 0),               # zaklinacz (nowy)
    (0x5E126C, "8a8e0601000080f9028d9606010000", "jmp", "kw_a", 10),
    (0x5D99C9, "8d8506010000894424188a00", "jmp", "kw_b", 7),
    (0x5D9F04, "8a8506010000", "jmp", "kw_c", 1),
    (0x5DA005, "8d82060100008a00", "jmp", "kw_d", 3),
    (0x5E57F6, "8a86060100008dbe06010000", "jmp", "kw_e", 7),
    (0x5EC067, "8a8e06010000", "call", "kw_f", 1),
    # test37: kara PD bez innych klas niz ulubiona i prestizowa (asercja 0x447990(0) po wyborze klasy prestizowej)
    (0x76479A, "578bcbe8ee31ceff", "jmp", "xp_zero", 3),
    # test39: atuty Extra Rage i Heroic Inspiration - barbarzynca jako podklasa wojownika zamiast klasy 1
    (0x76345B, "80be27060000010f8295040000", "jmp", "at_szal", 8),
    (0x76355D, "8a8e27060000b8010000003ac87314", "jmp", "at_heroic", 10),
    # test40: okno 6 klasy prestizowej - strony po 8 klas, przycisk 2 = nastepna strona
    (0x5ED780, "8bcbe819feffff", "jmp", "klik6", 2),
    # test44: opcode 177 - typ IDS 9 = podklasa DS (Skirmish zwiadowcy znoszony przez ciezka zbroje)
    (0x4BE30E, "8b471c83c0fe83f806c68424ec00000002", "jmp", "ids_kit", 12),
    # test42: umiejetnosci klasowe podklas (SKILCOST.2DA - kolumna podklasy DS przed kolumna klasy)
    (0x764371, "0fbf85980d00008d4eff3bc87d290fbf959a0d0000395424247d1c85c97c188b54242485d27c100fafc203c18b8d900d00008d0481eb068d85940d00008b00", "jmp", "skc_a", 58),
    (0x541BC4, "8b74240c807c2414", "jmp", "ho_rasa", 0),   # test51: GetRaceRow polorka - podrasa 2 = pololbrzym
    (0x76445E, "0fbf85980d00003bf07d270fbf959a0d00008b4c24243bca7d1885f67c1485c97c100fafc18b8d900d000003c68d0481eb068d85940d00008b00", "jmp", "skc_b", 53),
    # test27: nazwa podklasy DS zamiast klasy (karta postaci, portrety, awans)
    (0x5442A7, "81e3ff0000008d43ff", "jmp", "nazwa_kl", 4),       # 0x544120: nazwa klasy z kitu
    (0x5DCB31, "518b4c2424", "jmp", "karta_kl", 0),               # karta postaci (Levels): kit z bajtu klasy
]
# maski szkol czarodzieja 0x7FC0 -> 0xFF007FC0 (bit podklasy DS przy kliknieciu w oknie 12 i przy Gotowe)
MASKI_MAG = [0x61CEE9, 0x615CED]
# (adres, oryginalne bajty, rodzaj, etykieta, nop)
HAKI3 = [
    (0x71E996, "33c08a8766090000", "jmp", "awans_atut", 3),      # awans: CLAB nowych atutow, tablica RLAB rasy + SR_LEVEL
    (0x722862, "8b54245681e2ff000000", "jmp", "wzrok", 5),       # widzenie w ciemnosci z DSRASY
    (0x722DE3, None, "call", "poziom_atut", 0),                  # procedura CLAB: klasa 12 - poziom postaci / 1 dla atutu
    (0x73BC10, "807e2605c7442414000000007538", "jmp", "miot_atak", 9),   # bron miotana (atak)
    (0x73CA66, "8a462633ff3c057530", "jmp", "miot_info", 4),     # bron miotana (informacja)
    (0x73C8C0, "5556578b7c2410", "jmp", "wrogowie", 2),          # wrogowie rasy / olbrzymy
    # test28: karta postaci - cechy rasy pod nazwa rasy, kosc PW i BAB klas w sekcji Levels
    (0x5DD219, "68f85c8c005657", "jmp", "karta_rasa", 2),
    (0x5DCB3C, "8b4424488b4c241025ff000000505168842b8b005657e8c9b0e4ff83c414", "jmp", "karta_lv", 25),
    (0x5DD537, "8b44244885c0740f", "jmp", "karta_cf", 3),            # zdolnosci wrodzone FA_ z CLAB / RLAB
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


DANE = [
    # operand imm32 (instrukcje: 0x61CEF4 mov ecx, 0xFF8000 / 0x615CFE and eax, 0xFF8000). Do test19 wlacznie
    # zapis szedl pod adres instrukcji i niszczyl jej kod (blad poprawiony w test20).
    (0x61CEF5, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy zmianie bostwa
    (0x615CFF, struct.pack("<I", 0xFFFF8000)),   # maska bostw przy przycisku Gotowe
]


# test54: nowe atuty. Gra ma 75 atutow (FEATS.IDS 0..74), postac trzyma je w 3 dwordach (+0x75C), wiec miesci 96.
# test55: liczba atutow = wiersze FEATS.2DA (feats_wczyt po wczytaniu tabeli, slowo 0x84EA66 w .rdata - zapisywalna).
ATUTY_ASERCJE = [0x762E26, 0x763156, 0x763206, 0x763A46, 0x7630A5, 0x765CE8]   # cmp reg, 0x4B (asercja numeru atutu)
# (adres, oryginalne bajty, rodzaj, etykieta, nop)
ATUTY_HAKI = [(0x765DC8, "83f84b89442410", "call", "karta_n", 2),     # lista atutow na karcie (0x765C50)
              (0x7630C3, "8d46fd83f8425e7727", "jmp", "ranga_max", 4),  # test56: maks. ranga atutu z DSATUTY
              (0x5E1250, "4683fe4b7c95", "call", "kreator_n", 1),     # atuty z kolumn klas/ras FEATS.2DA
              (0x734689, "578bcbe84f1ed1ff", "jmp", "atut_premie", 3)]  # ProcessEffectList: premie z DSATUTY
ATUTY_SIB = [(0x5DA2DE, "89848e50060000", 0), (0x5E8AD7, "39848e50060000", 0), (0x5F7156, "3984b750060000", 0),
             (0x60CD6C, "898497b2140000", 1), (0x60E689, "39848eb2140000", 1), (0x623447, "3984b3b2140000", 1)]
ATUTY_LEA = [(0x5E4311, "8dbd50060000", 0xBF, 0), (0x5F89D5, "8dab50060000", 0xBD, 0),
             (0x606C22, "8dbeb2140000", 0xBF, 1)]   # lea reg, [obiekt+tablica] -> mov reg, adres; nop


def atuty_exe(d, et5):
    tab = (DANE5, DANE5 + 0x300)
    for adr in ATUTY_ASERCJE:
        o = adr - BASE
        assert d[o] == 0x83 and d[o + 2] == 0x4B and d[o + 1] in (0xF8, 0xFD, 0xFE, 0xFF), hex(adr)
        d[o + 2] = 0xC0                            # test56: 192 atuty
    for adr, h, rodzaj, lab, nop in ATUTY_HAKI:
        o = adr - BASE
        assert d[o:o + len(h) // 2].hex() == h, hex(adr)
        d[o:o + 5] = bytes([0xE9 if rodzaj == "jmp" else 0xE8]) + struct.pack("<i", et5[lab] - (adr + 5))
        d[o + 5:o + 5 + nop] = b"\x90" * nop
    o = 0x53EFBA - BASE                            # Load FEATS.2DA w regulach -> feats_wczyt (liczba atutow)
    assert d[o] == 0xE8 and struct.unpack_from("<i", d, o + 1)[0] + 0x53EFBF == 0x402B70
    struct.pack_into("<i", d, o + 1, et5["feats_wczyt"] - 0x53EFBF)
    assert d[0x84EA66 - BASE:0x84EA68 - BASE].hex() == "4b00"   # domyslnie 75 (do wczytania FEATS.2DA)
    s = sekcje(d)                                  # .rdata zapisywalna (slowo 0x84EA66)
    ch = struct.unpack_from("<I", d, s[".rdata"] + 36)[0]
    struct.pack_into("<I", d, s[".rdata"] + 36, ch | 0x80000000)
    for adr, h, k in ATUTY_SIB:                    # [baza + idx*4 + disp] -> [idx*4 + adres]
        o = adr - BASE
        assert d[o:o + 7].hex() == h, hex(adr)
        d[o + 1] = 0x04
        d[o + 2] = (d[o + 2] & 0xF8) | 5
        struct.pack_into("<I", d, o + 3, tab[k])
    for adr, h, op, k in ATUTY_LEA:
        o = adr - BASE
        assert d[o:o + 6].hex() == h, hex(adr)
        d[o:o + 6] = bytes([op]) + struct.pack("<I", tab[k]) + b"\x90"
    o = 0x606C28 - BASE                            # rep stosd: zerowanie tablicy kreatora
    assert d[o:o + 5].hex() == "b94b000000"
    d[o + 1] = 0xC0
    o = 0x762897 - BASE                            # SetFeatRank: cmp edi, 0x4B; mov esi, ecx -> call atut_ustaw
    assert d[o:o + 5].hex() == "83ff4b8bf1"
    d[o:o + 5] = b"\xE8" + struct.pack("<i", et5["atut_ustaw"] - (0x762897 + 5))
    for adr, h, lab in ((0x762905, "8d47fd83f8420f874d040000", "ranga_zapis"),    # SetFeatRank: domyslnie
                         (0x762E64, "8d47fd83f8420f8761010000", "ranga_odczyt"),   # GetFeatRank: domyslnie 1
                         (0x763A66, "8d47fd83f8420f8745010000", "wybor_atut")):    # czy mozna wybrac
        o = adr - BASE                             # "lea eax, [edi-3]; cmp eax, 0x42; ja X" -> ja etykieta (test56)
        assert d[o:o + 12].hex() == h, hex(adr)
        struct.pack_into("<i", d, o + 8, et5[lab] - (adr + 12))
    o = 0x764668 - BASE                            # test58: klasa ulubiona polorka (i podras) / niziolka widmowego:
    assert d[o:o + 5].hex() == "bf01000000"        # barbarzynca (slot klasy 1 = klasy prestizowe) -> wojownik
    d[o + 1] = 5
    o = 0x763270 - BASE                            # warunki atutu: numer > 74 -> atut_wymog (zamiast "brak")
    assert d[o - 3:o + 6].hex() == "83fd4a0f8787060000"
    struct.pack_into("<i", d, o + 2, et5["atut_wymog"] - (0x763270 + 6))


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
    for adr, h, _, lab, _ in HAKI4:
        assert d[adr - BASE:adr - BASE + len(h) // 2].hex() == h, (hex(adr), lab)
    for adr in MASKI_MAG:
        assert struct.unpack_from("<I", d, adr - BASE)[0] == 0x7FC0, hex(adr)
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
    kod4, et4 = nasm(os.path.join(ASM, "kity.asm"), ORG4,
                     {"szukaj": et3["szukaj"], "wczytaj": et3["wczytaj"], "komorka": et["komorka"],
                      "tabela2da": et["tabela2da"], "tab_klasy": et["tab_klasy"], "liczba": et["liczba"],
                      "prog_kl": et["prog"], "lv_wart": et3["lv_wart"], "lv_kl": et3["lv_kl"],
                      "lv_poz": et3["lv_poz"]})
    if ORG4 + len(kod4) > ORG5:
        sys.exit("kity.asm wchodzi na atuty.asm (0xA28000)")
    assert kod4[:8] == b"DSKITY02" and et4["kit_synt"]
    assert et4["kol_kitu"] and kod4[0x1C] == 0xE9 and kod4[0x21] == 0xE9
    d[raw3 + (ORG4 - ORG3):raw3 + (ORG4 - ORG3) + len(kod4)] = kod4
    kod5, et5 = nasm(os.path.join(ASM, "atuty.asm"), ORG5,
                     {"szukaj": et3["szukaj"], "wczytaj": et3["wczytaj"], "komorka": et["komorka"],
                      "clab_rasa": et3["clab_rasa"], "poziom": et3["poziom"], "rasa_awans": et3["rasa_awans"],
                      "pr_bab": et4["pr_bab"]})
    if ORG5 + len(kod5) > DANE5:
        sys.exit("atuty.asm wchodzi na dane 0xA2A000")
    assert kod5[:8] == b"DSATUTY1"
    d[raw3 + (ORG5 - ORG3):raw3 + (ORG5 - ORG3) + len(kod5)] = kod5
    atuty_exe(d, et5)
    for adr in MASKI_MAG:
        struct.pack_into("<I", d, adr - BASE, 0xFF007FC0)
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
    et.update(et4)
    et.update(et5)
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
    zastapione = {a for a, *_ in HAKI4} | {0x6100F0}
    haki = [(a, r, l, n) for a, r, l, n in HAKI if a != 0x546030 and a not in zastapione] + \
        [(0x546030, "jmp", "clab_atut", 4)] + [(a, r, l, n) for a, _, r, l, n in HAKI4]
    for adr, rodzaj, lab, nop in haki + HAKI2 + [(a, r, l, n) for a, _, r, l, n in HAKI3]:
        o = adr - BASE
        op = 0xE9 if rodzaj == "jmp" else 0xE8
        d[o:o + 5] = bytes([op]) + struct.pack("<i", et[lab] - (adr + 5))
        d[o + 5:o + 5 + nop] = b"\x90" * nop
    # od test25 tablica skokow 0x61C1A8 zostaje oryginalna - o oknie 52 decyduje okno_klasy (kity.asm) wg tabeli podklas
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
    # test51 polorek: nazwa podrasy na karcie (0x544FE6): podrasa 1 -> strref mula (0x544FEB), 2 -> pololbrzym (0x544FF2);
    # strrefy wpisuje WeiDU (komponent 1)
    o = 0x544FE6 - BASE
    assert d[o] == 0xB8 and d[o + 5] == 0xE9, "0x544FE6: oczekiwano mov eax, strref; jmp 0x545009"
    mul = struct.unpack_from("<I", d, o + 1)[0]
    kod_ho = b"\x3C\x01\x75\x07" + b"\xB8" + struct.pack("<I", mul) + b"\xEB\x18" + b"\xB8" + struct.pack("<I", 0xFFFFFFFF) + b"\xEB\x11"
    assert 0x544FE6 + 4 + 5 + 2 == 0x544FF1 and 0x544FF1 + 7 + 0x11 == 0x545009 and 0x544FEF + 2 + 0x18 == 0x545009
    d[o:o + len(kod_ho)] = kod_ho
    d[o + len(kod_ho):0x544FFF - BASE] = b"\x90" * (0x544FFF - 0x544FE6 - len(kod_ho))
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
    # okno 52 (0x608F50, inicjalizacja): tytul tylko dla paladyna (7) i mnicha (6), inna klasa -> asercja
    # InfScreenCreateChar.cpp 1887 (barbarzynca, wojownik, tropiciel, druid, bard, zaklinacz od test16). Bez tytulu:
    # 0x609075 jmp short 0x60908E.
    o = 0x609075 - BASE
    assert d[o:o + 2].hex() == "6a00" and struct.unpack_from("<I", d, o + 13)[0] == 0x75F, "0x609075"
    d[o:o + 2] = bytes([0xEB, 0x60908E - 0x609077])
    s = sekcje(d)
    struct.pack_into("<I", d, s[".text"] + 8, max(0x446000, struct.unpack_from("<I", d, s[".text"] + 8)[0]))
    struct.pack_into("<I", d, s[".data"] + 8, max(0x176000, struct.unpack_from("<I", d, s[".data"] + 8)[0]))
    open(a.out, "wb").write(d)
    for k in ("klasa_wiersz", "clab", "szukaj_klase"):
        print(k, hex(et[k]))
    print("koniec podklasy.asm", hex(ORG + len(kod)), "dodatki.asm", hex(ORG2 + len(kod2)), "rasy.asm", hex(ORG3 + len(kod3)),
          "kity.asm", hex(ORG4 + len(kod4)))
    print("zapisano", a.out)


if __name__ == "__main__":
    main()
