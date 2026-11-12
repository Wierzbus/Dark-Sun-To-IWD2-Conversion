"""Rekordy RDFF (SEGOBJEX.GFF), tabela przedmiotow IT1R i tabela nazw NAME (GPLDATA.GFF).

Uklady ustalone na danych gry (niezalezne potwierdzenie brak). Pola oznaczone `u_`
maja nieustalone znaczenie; pola z komentarzem "?" maja znaczenie prawdopodobne.

RDFF: ciag blokow, naglowek 10 B <BBhhhh>: load_action, blocknum, type, index, from, len,
po nim `len` bajtow. load_action 0xFF konczy rekord.
  type 1 = przedmiot (21 B), 2 = walka (58 B), 4 = postac (71 B), 3 i 5 = znaczniki (0 B).
  load_action dla przedmiotu: 1 = samodzielny rekord, 2 = zalozony?, 4 = w plecaku?
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, asdict

HDR = struct.Struct("<BBhhhh")
T_ITEM, T_COMBAT, T_MARK3, T_CHAR, T_MARK5 = 1, 2, 3, 4, 5


@dataclass
class Block:
    load_action: int
    blocknum: int
    type: int
    index: int
    from_: int
    data: bytes


def rdff_blocks(b: bytes) -> list[Block]:
    out, p = [], 0
    while p + HDR.size <= len(b):
        la, bn, ty, ix, fr, ln = HDR.unpack_from(b, p)
        if la == 0xFF:
            return out
        out.append(Block(la, bn, ty, ix, fr, b[p + HDR.size:p + HDR.size + ln]))
        p += HDR.size + ln
    raise ValueError("rekord RDFF bez znacznika konca")


# --- przedmiot (blok typu 1) -------------------------------------------------------
ITEM = struct.Struct("<hHhHhhhHBBHb")  # 21 B


@dataclass
class Item:
    id: int
    quantity: int          # ? (strzaly: 24); dla czesci przedmiotow wartosci nieoczywiste
    next: int
    value: int             # ? cena
    pack_index: int
    item_index: int        # indeks rekordu IT1R
    icon: int
    charges: int           # ?
    special: int           # ?
    slot: int
    name_idx: int          # indeks w NAME; 9999 = brak nazwy
    bonus: int             # ? premia magiczna (+1 itd.)

    @classmethod
    def parse(cls, b: bytes) -> "Item":
        if len(b) != ITEM.size:
            raise ValueError(f"przedmiot: {len(b)} B zamiast {ITEM.size}")
        return cls(*ITEM.unpack(b))


# --- walka (blok typu 2) -----------------------------------------------------------
COMBAT = struct.Struct("<hhhhhhh8sBBhbBBBBbBB6s18s")  # 58 B


@dataclass
class Combat:
    hp: int
    psp: int
    char_index: int        # = index bloku postaci
    id: int
    ready_item_index: int
    weapon_index: int
    pack_index: int
    data_block: bytes
    special_attack: int
    special_defense: int
    icon: int
    ac: int
    move: int
    status: int
    allegiance: int
    data: int
    thac0: int
    priority: int
    flags: int
    stats: tuple           # STR, DEX, CON, INT, WIS, CHA
    name: str

    @classmethod
    def parse(cls, b: bytes) -> "Combat":
        if len(b) != COMBAT.size:
            raise ValueError(f"walka: {len(b)} B zamiast {COMBAT.size}")
        v = list(COMBAT.unpack(b))
        v[19] = tuple(v[19])
        v[20] = v[20].split(b"\0")[0].decode("latin-1")
        return cls(*v)


# --- postac (blok typu 4) ----------------------------------------------------------
CHAR = struct.Struct("<iihhhhh6sBBB6s3s3sbBBB3s3s3s3s5sBBB3sHHB")  # 71 B


@dataclass
class Character:
    current_xp: int
    high_xp: int
    base_hp: int
    high_hp: int
    base_psp: int
    u_14: int              # zwykle 2000
    u_16: int
    u_18: bytes
    race: int              # 1 = czlowiek?
    gender: int            # 1 = m, 2 = k, 0 = brak (potwory)?
    alignment: int
    stats: tuple           # jak w bloku walki
    real_class: tuple      # do 3 klas (multiklasa)
    level: tuple
    base_ac: int
    base_move: int
    magic_resistance: int
    num_blows: int         # ?
    num_attacks: tuple     # ?
    num_dice: tuple        # ?
    num_sides: tuple       # ?
    num_bonuses: tuple     # ?
    saving_throw: tuple    # ? paraliz, rozdzka, skamienienie, zionie, czar
    allegiance: int
    size: int
    spell_group: int
    high_level: tuple
    sound_fx: int
    attack_sound: int
    psi_group: int

    @classmethod
    def parse(cls, b: bytes) -> "Character":
        if len(b) != CHAR.size:
            raise ValueError(f"postac: {len(b)} B zamiast {CHAR.size}")
        v = list(CHAR.unpack(b))
        for k in (11, 12, 13, 18, 19, 20, 21, 22, 26):
            v[k] = tuple(v[k])
        return cls(*v)


# --- IT1R (GPLDATA.GFF, 20 B na rekord) --------------------------------------------
IT1R = struct.Struct("<bbHHHBBBBBBbBHbB")


@dataclass
class ItemType:
    index: int
    weapon_type: int       # ? 1 = wrecz, 2 = proca, 0x0a = luk, 0 = pancerz/inne
    damage_type: int
    u_2: int               # nieustalone (8..48 dla broni)
    weight: int            # ? w 1/10 funta
    base_hp: int           # ? wytrzymalosc (zwykle 250)
    material: int          # ? flagi
    placement: int         # miejsce noszenia: 1 tulow, 3 ramiona, 0x0a nogi, 5 dlon, 0x0b amunicja ...
    range: int             # ?
    num_attacks: int       # ?
    sides: int             # kosc obrazen: liczba scian
    dice: int              # liczba kosci
    mod: int               # premia do obrazen
    flags: int
    legal_class: int       # maska klas (0x1fff = wszystkie?)
    base_ac: int
    u_19: int

    @classmethod
    def table(cls, b: bytes) -> list["ItemType"]:
        if len(b) % IT1R.size:
            raise ValueError("IT1R: dlugosc nie jest wielokrotnoscia 20")
        return [cls(i, *IT1R.unpack_from(b, i * IT1R.size)) for i in range(len(b) // IT1R.size)]


# --- NAME (GPLDATA.GFF, 25 B na rekord) --------------------------------------------
NAME_SIZE = 25


def name_table(b: bytes) -> list[dict]:
    """Rekord: nazwa (22 B, zakonczona zerem; reszta to smieci), u16 ikona?, u8."""
    out = []
    for i in range(len(b) // NAME_SIZE):
        r = b[i * NAME_SIZE:(i + 1) * NAME_SIZE]
        icon, flag = struct.unpack_from("<hB", r, 22)
        out.append({"index": i, "name": r[:22].split(b"\0")[0].decode("latin-1"), "icon": icon, "u_24": flag})
    return out


def as_row(obj) -> dict:
    return {k: (list(v) if isinstance(v, tuple) else v.hex() if isinstance(v, bytes) else v)
            for k, v in asdict(obj).items()}
