"""Postac Dark Sun (wiersz creatures.csv) -> CRE V2.2 (IWD2), wersja robocza do testu obszaru.

To NIE jest pelny konwerter z przewodnika CRE (docs/ds_cre_guide.md, BGtoIWD2 entities/cre_rules.py):
statystyki, atuty, umiejetnosci i czary licza sie tam z tabel IWD2. Tu powstaje poprawny strukturalnie
CRE z danymi wprost z Dark Sun, zeby rozstawic postacie i sprawdzic obszar, dialogi i skrypty.
Uklad pol jak w cre_rules.convert (BGtoIWD2) i IESDP CRE V2.2 (0x274 skrypt Override, 0x626 dialog).
Zasady (propozycja z ds_cre_guide.md, decyzje wlasciciela otwarte):
  klasa: wojownik/gladiator -> FIGHTER, kaplan/templariusz -> CLERIC, mag -> WIZARD, zlodziej -> ROGUE,
         potwor bez klasy -> FIGHTER z poziomem z bloku postaci;
  rasa: czlowiek HUMAN, elf ELF, polelf HALF_ELF, krasnolud DWARF, niziolek HALFLING, mul i pololbrzym HALFORC,
        nieumarly i potwory: NO_RACE + GENERAL wg kategorii;
  HP z Dark Sun; KP: humanoid 10 (pancerz z ekwipunku), potwor 20 - KP 2E; BAB i rzuty wg zasad 3E dla klasy;
  strona: allegiance 2 i 4 -> NEUTRAL (2 = wrogie w Dark Sun, wrogosc wlacza skrypt po ataku).
"""
from __future__ import annotations

import ast
import struct

NONE = 0xFFFFFFFF
EMPTY = 0xFFFF
CLASS_ID = {"BARBARIAN": 1, "BARD": 2, "CLERIC": 3, "DRUID": 4, "FIGHTER": 5, "MONK": 6, "PALADIN": 7, "RANGER": 8,
            "ROGUE": 9, "SORCERER": 10, "WIZARD": 11}
# rasa Dark Sun (napis z creatures.csv) -> (RACE.IDS IWD2, przesuniecie animacji 0x60xx, GENERAL.IDS)
RASA = {"czlowiek": (1, 0, 1), "elf": (2, 1, 1), "polelf": (3, 1, 1), "krasnolud": (4, 2, 1), "nizolek": (5, 3, 1),
        "mul": (7, 5, 1), "pololbrzym": (7, 5, 5), "thri-kreen": (255, None, 255), "nieumarly": (255, None, 4)}
KLASA = [("kaplan", "CLERIC", 0x6000), ("templ", "CLERIC", 0x6000), ("mag", "WIZARD", 0x6200),
         ("zlodziej", "ROGUE", 0x6300), ("wojownik", "FIGHTER", 0x6100), ("gladiator", "FIGHTER", 0x6100),
         ("tropiciel", "RANGER", 0x6100), ("druid", "DRUID", 0x6000), ("psionik", "SORCERER", 0x6200)]
# potwory po nazwie (ANIMATE.IDS IWD2)
ANIM_POTWOROW = [("zombie", 0xE338), ("stalker", 0x7F0A), ("spider", 0xC100), ("wolf", 0x7B00)]
ALIGN = {"LG": 0x11, "LN": 0x12, "LE": 0x13, "NG": 0x21, "TN": 0x22, "NE": 0x23, "CG": 0x31, "CN": 0x32, "CE": 0x33}
DOBRY_FORT = {"FIGHTER", "CLERIC", "BARBARIAN", "PALADIN", "RANGER", "DRUID", "MONK"}
DOBRY_REF = {"ROGUE", "RANGER", "MONK", "BARD"}
DOBRY_WILL = {"CLERIC", "DRUID", "WIZARD", "SORCERER", "MONK", "BARD"}
BAB_PELNY = {"FIGHTER", "BARBARIAN", "PALADIN", "RANGER"}
BAB_SREDNI = {"CLERIC", "DRUID", "ROGUE", "MONK", "BARD"}


def _lista(s: str) -> list[int]:
    try:
        return list(ast.literal_eval(s))
    except (ValueError, SyntaxError):
        return []


def klasa_i_poziom(w: dict) -> tuple[str, int, int]:
    """(klasa IWD2, poziom, baza animacji)"""
    opis = w["klasy"].lower()
    poziom = max([int(t) for t in opis.split() if t.isdigit()] or [1])
    for slowo, klasa, anim in KLASA:
        if slowo in opis:
            return klasa, max(1, poziom), anim
    return "FIGHTER", max(1, poziom), 0x6100


def animacja(w: dict, anim_baza: int) -> tuple[int, int, int]:
    """(animacja, RACE, GENERAL)"""
    nazwa = w["name"].lower()
    rasa = w["rasa"].split(" ")[0]
    for slowo, a in ANIM_POTWOROW:
        if slowo in nazwa:
            return a, RASA.get(rasa, (255, None, 255))[0], RASA.get(rasa, (255, None, 2))[2] if rasa in RASA else 2
    r, przes, gen = RASA.get(rasa, (255, None, 255))
    if przes is None:
        return 0x6100, r, gen          # brak animacji w IWD2: czlowiek-wojownik (do tabeli ds_anim_map)
    kobieta = 0x10 if w["plec"] == "k" else 0
    return anim_baza + przes + kobieta, r, gen


def zbuduj(w: dict, *, dialog: str = "", skrypt: str = "") -> bytes:
    klasa, lv, abaza = klasa_i_poziom(w)
    anim, rasa, gen = animacja(w, abaza)
    staty = (_lista(w["stats"]) + [12] * 6)[:6]
    hp = max(1, int(w["hp"] or 1))
    d = bytearray(0x62E)
    d[0:8] = b"CRE V2.2"
    struct.pack_into("<II", d, 0x08, NONE, NONE)        # imie: SAY przy instalacji
    struct.pack_into("<I", d, 0x14, 25 * lv * lv)          # XP za zabicie: 25 x poziom^2 (propozycja)
    struct.pack_into("<I", d, 0x18, lv)
    struct.pack_into("<HH", d, 0x24, hp, hp)
    struct.pack_into("<I", d, 0x28, anim)
    d[0x2C:0x33] = bytes([0x1A, 0x1C, 0x1E, 0x11, 0x1B, 0x0C, 0x0C])  # kolory: zgaszone braz/skora
    d[0x33] = 1
    for off in (0x34, 0x3C):
        d[off:off + 8] = b"None\0\0\0\0"
    humanoid = gen in (1, 5)
    ac2e = int(w["ac"] or 10)
    struct.pack_into("<h", d, 0x46, 10 if humanoid else max(10, 20 - ac2e))
    bab = lv if klasa in BAB_PELNY else (lv * 3) // 4 if klasa in BAB_SREDNI else lv // 2
    d[0x50], d[0x51] = bab, 1 + max(0, (bab - 1) // 5)
    dobry = lambda lv_: 2 + lv_ // 2
    slaby = lambda lv_: lv_ // 3
    d[0x52] = dobry(lv) if klasa in DOBRY_FORT else slaby(lv)
    d[0x53] = dobry(lv) if klasa in DOBRY_REF else slaby(lv)
    d[0x54] = dobry(lv) if klasa in DOBRY_WILL else slaby(lv)
    struct.pack_into("<64i", d, 0xAC, *([-1] * 64))         # dzwieki: brak
    d[0x8A] = lv
    d[0x8A + CLASS_ID[klasa]] = lv
    d[0x266:0x26C] = bytes(min(max(s, 3), 25) for s in staty)
    for off in (0x274, 0x27C, 0x284, 0x28C, 0x294, 0x1AC, 0x1B4):
        d[off:off + 8] = b"None\0\0\0\0"
    if skrypt:
        d[0x274:0x27C] = skrypt.upper().encode("latin-1").ljust(8, b"\0")   # Override
    d[0x384] = 128                                           # EA: NEUTRAL
    d[0x385] = gen
    d[0x386] = rasa
    d[0x387] = CLASS_ID[klasa]
    d[0x389] = 2 if w["plec"] == "k" else 1
    d[0x38F] = ALIGN.get(w["charakter"], 0x22)
    struct.pack_into("<HH", d, 0x3B4, CLASS_ID[klasa], 1 << (CLASS_ID[klasa] - 1))
    koniec = 0x62E
    for off in range(0x3BA, 0x5FA, 4):                       # listy czarow 7x9, liczniki, domeny: puste
        struct.pack_into("<I", d, off, koniec if off < 0x4B6 or 0x5B2 <= off < 0x5D6 else 0)
    for off in (0x5FA, 0x602, 0x60A):                        # zdolnosci, piesni, ksztalty: puste
        struct.pack_into("<II", d, off, koniec, 0)
    sloty = struct.pack("<50H", *([EMPTY] * 50)) + bytes(4)
    struct.pack_into("<I", d, 0x612, koniec)                 # sloty
    struct.pack_into("<II", d, 0x616, koniec, 0)             # przedmioty
    struct.pack_into("<II", d, 0x61E, koniec + len(sloty), 0)  # efekty
    d[0x626:0x62E] = (dialog.upper().encode("latin-1") if dialog else b"None").ljust(8, b"\0")
    return bytes(d) + sloty
