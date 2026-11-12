"""Szkielet ARE V9.1 (IWD2) z danych ARE V1.0 (BG1): tylko to, co potrzeba do wejścia na mapę.

Źródła: docs/ARE file format 91.html (nagłówek 0x12C, pola i offsety, sekcje song
entries 0x90 i rest interruptions 0xE4, entrance 0x68) oraz docs/ARE file format.html
(V1.0). Wartości domyślne pól bez źródła w BG zapisuje `assumptions()` do
out/are_skeleton_assumptions.md.

OBSERWACJE na plikach (nie z docs): w obu grach plik zawsze zawiera sekcje song entries
i rest interruptions, nawet w obszarze bez obiektów; puste tabele mają offset równy
miejscu, w którym by leżały; u IWD2 pole 'tiled object flags' i automap mają offset 0
gdy puste.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

HEADER_V91 = 0x12C
SONG_SIZE = 0x90
REST_SIZE = 0xE4
ENTRANCE_SIZE = 0x68

# Offsety nagłówka V9.1 (docs/ARE file format 91.html)
H_WED, H_SAVED, H_FLAGS = 0x08, 0x10, 0x14
H_NEIGH = (0x18, 0x24, 0x30, 0x3C)          # resref (8) + flags (4)
H_TYPE, H_RAIN, H_SNOW, H_FOG, H_LIGHT, H_WIND = 0x48, 0x4A, 0x4C, 0x4E, 0x50, 0x52
H_DIFF2, H_DIFF3, H_AVGLVL = 0x54, 0x55, 0x56
H_ACT_OFF, H_ACT_N, H_REG_N, H_REG_OFF = 0x64, 0x68, 0x6A, 0x6C
H_SPAWN_OFF, H_SPAWN_N, H_ENT_OFF, H_ENT_N = 0x70, 0x74, 0x78, 0x7C
H_CONT_OFF, H_CONT_N, H_ITEM_N, H_ITEM_OFF = 0x80, 0x84, 0x86, 0x88
H_VERT_OFF, H_VERT_N, H_AMB_N, H_AMB_OFF = 0x8C, 0x90, 0x92, 0x94
H_VAR_OFF, H_VAR_N, H_TOF_OFF, H_TOF_N = 0x98, 0x9C, 0xA0, 0xA2
H_SCRIPT, H_EXPL_SIZE, H_EXPL_OFF = 0xA4, 0xAC, 0xB0
H_DOOR_N, H_DOOR_OFF, H_ANIM_N, H_ANIM_OFF = 0xB4, 0xB8, 0xBC, 0xC0
H_TOBJ_N, H_TOBJ_OFF, H_SONG_OFF, H_REST_OFF = 0xC4, 0xC8, 0xCC, 0xD0
H_AUTO_OFF, H_AUTO_N = 0xD4, 0xD8

# Domyślna sekcja song entries: pierwsze dwa słowa (dzień, noc) = 0, bo docs: "0 is
# used to stop playing music"; pozostałe sloty = 0xFFFFFFFF (obserwacja: tak mają
# wszystkie nieużywane sloty w ARE obu gier); ambienty puste, głośność 100%
# (obserwacja: identyczny układ w BG1 ar0401/ar2215 i IWD2 ar1201).


def _song_default() -> bytes:
    b = bytearray(SONG_SIZE)
    struct.pack_into("<10I", b, 0, 0, 0, *([0xFFFFFFFF] * 8))
    struct.pack_into("<I", b, 0x38, 100)   # głośność ambientu dziennego
    struct.pack_into("<I", b, 0x4C, 100)   # głośność ambientu nocnego
    return bytes(b)


# Domyślna sekcja rest interruptions: OBSERWACJA - te same 0xE4 bajty w BG1 ar0401,
# BG1 ar2215 i IWD2 ar1201 (odczytane bajt w bajt z pliku).
_REST_HEX = (
    "00000000000000000000000000000000000000000000000000000000000000009627000096270000962700009627000096270000962700009627000096270000962700009627000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010001000000010001000a0001000a000a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
)


def _rest_default() -> bytes:
    b = bytes.fromhex(_REST_HEX)
    assert len(b) == REST_SIZE, len(b)
    return b


@dataclass
class SkeletonSource:
    """Pola brane z ARE BG1 (V1.0)."""
    area_flags_bit0: int = 0
    area_type: int = 0
    rain: int = 0
    snow: int = 0
    fog: int = 0
    lightning: int = 0
    wind: int = 0


def read_bg_source(data: bytes) -> SkeletonSource:
    """Czyta potrzebne pola z ARE V1.0 (offsety wg docs/ARE file format.html)."""
    if data[:4] != b"AREA" or data[4:8] != b"V1.0":
        raise ValueError(f"oczekiwano ARE V1.0, jest {data[:8]!r}")
    u16 = lambda o: struct.unpack_from("<H", data, o)[0]
    return SkeletonSource(
        area_flags_bit0=struct.unpack_from("<I", data, 0x14)[0] & 1,
        area_type=u16(0x48), rain=u16(0x4A), snow=u16(0x4C), fog=u16(0x4E),
        lightning=u16(0x50), wind=u16(0x52))


def build_are(wed_name: str, src: SkeletonSource, *, entrance: tuple[int, int] | None = None,
              entrance_name: str = "START") -> bytes:
    """ARE V9.1 bez obiektów. `entrance` (x, y) dodaje JEDNO wejście (opcja testowa;
    domyślnie wyłączona, bo zadanie zakłada puste tabele)."""
    if len(wed_name) > 8:
        raise ValueError("nazwa WED dłuższa niż 8 znaków")
    h = bytearray(HEADER_V91)
    h[0:8] = b"AREAV9.1"
    h[H_WED:H_WED + 8] = wed_name.upper().encode("latin-1").ljust(8, b"\0")
    struct.pack_into("<I", h, H_SAVED, 0)
    struct.pack_into("<I", h, H_FLAGS, src.area_flags_bit0 & 1)
    struct.pack_into("<H", h, H_TYPE, src.area_type)
    for off, v in ((H_RAIN, src.rain), (H_SNOW, src.snow), (H_FOG, src.fog),
                   (H_LIGHT, src.lightning), (H_WIND, src.wind)):
        struct.pack_into("<H", h, off, v)
    n_ent = 1 if entrance else 0
    cur = HEADER_V91
    for off in (H_ACT_OFF, H_REG_OFF, H_SPAWN_OFF):
        struct.pack_into("<I", h, off, cur)
    struct.pack_into("<I", h, H_ENT_OFF, cur)
    struct.pack_into("<I", h, H_ENT_N, n_ent)
    cur += n_ent * ENTRANCE_SIZE
    for off in (H_CONT_OFF, H_ITEM_OFF, H_AMB_OFF, H_VAR_OFF, H_DOOR_OFF, H_VERT_OFF,
                H_ANIM_OFF, H_TOBJ_OFF, H_EXPL_OFF):
        struct.pack_into("<I", h, off, cur)
    song_off = cur
    rest_off = cur + SONG_SIZE
    struct.pack_into("<I", h, H_SONG_OFF, song_off)
    struct.pack_into("<I", h, H_REST_OFF, rest_off)
    body = bytearray()
    if entrance:
        e = bytearray(ENTRANCE_SIZE)
        e[0:32] = entrance_name.encode("latin-1").ljust(32, b"\0")
        struct.pack_into("<HHH", e, 0x20, entrance[0], entrance[1], 0)
        body += e
    body += _song_default() + _rest_default()
    return bytes(h) + bytes(body)


def parse_skeleton(data: bytes) -> dict:
    """Odczyt kontrolny: nagłówek V9.1 + zgodność liczników/offsetów z długością pliku."""
    if len(data) < HEADER_V91 or data[:8] != b"AREAV9.1":
        raise ValueError("nie jest ARE V9.1")
    u32 = lambda o: struct.unpack_from("<I", data, o)[0]
    u16 = lambda o: struct.unpack_from("<H", data, o)[0]
    sections = {
        "actors": (u32(H_ACT_OFF), u16(H_ACT_N), 0x110),
        "regions": (u32(H_REG_OFF), u16(H_REG_N), 0xC4),
        "spawn": (u32(H_SPAWN_OFF), u32(H_SPAWN_N), 0xC8),
        "entrances": (u32(H_ENT_OFF), u32(H_ENT_N), ENTRANCE_SIZE),
        "containers": (u32(H_CONT_OFF), u16(H_CONT_N), 0xC0),
        "items": (u32(H_ITEM_OFF), u16(H_ITEM_N), 0x14),
        "vertices": (u32(H_VERT_OFF), u16(H_VERT_N), 4),
        "ambients": (u32(H_AMB_OFF), u16(H_AMB_N), 0xD4),
        "variables": (u32(H_VAR_OFF), u32(H_VAR_N), 0x54),
        "doors": (u32(H_DOOR_OFF), u32(H_DOOR_N), 0xC8),
        "animations": (u32(H_ANIM_OFF), u32(H_ANIM_N), 0x4C),
        "tiled_objects": (u32(H_TOBJ_OFF), u32(H_TOBJ_N), 0x6C),
    }
    errs = []
    for k, (off, n, size) in sections.items():
        if n and off + n * size > len(data):
            errs.append(f"{k}: {n}x0x{size:X} od 0x{off:X} wykracza poza plik")
    song, rest = u32(H_SONG_OFF), u32(H_REST_OFF)
    if song + SONG_SIZE > len(data) or rest + REST_SIZE > len(data):
        errs.append("song/rest poza plikiem")
    if rest + REST_SIZE != len(data):
        errs.append(f"plik ma {len(data)} B, a rest interruptions kończy się w {rest + REST_SIZE}")
    return {"wed": data[8:16].split(b"\0")[0].decode(), "flags": u32(H_FLAGS),
            "type": u16(H_TYPE), "script": data[H_SCRIPT:H_SCRIPT + 8].split(b"\0")[0].decode(),
            "counts": {k: v[1] for k, v in sections.items()}, "errors": errs,
            "size": len(data), "song_off": song, "rest_off": rest}


def assumptions(wed_name: str, src: SkeletonSource, entrance) -> list[tuple[str, str, str]]:
    """(pole, wartość, powód) - każde pole, któremu nadano wartość nie z BG."""
    r = []
    add = lambda f, v, why: r.append((f, v, why))
    add("0x04 wersja", "V9.1", "wymóg IWD2 (docs/ARE file format 91.html)")
    add("0x08 Area WED", wed_name.upper(), "nowa nazwa wg name_map.csv, nie nazwa BG")
    add("0x10 Last saved", "0", "brak odpowiednika; 0 we wszystkich ARE obu gier")
    add("0x14 flagi obszaru", str(src.area_flags_bit0 & 1),
        "przeniesiony tylko bit 0 (Save not allowed = Save disabled); bity 1-3 mają w IWD2 "
        "inne znaczenie (Rest disabled, Unknown, Lock battle music), BG1 ich nie używa")
    add("0x18-0x44 sąsiedzi N/E/S/W i ich flagi", "puste / 0",
        "obszary BG nie istnieją w IWD2")
    add("0x54 trudność 2, 0x55 trudność 3", "0 / 0",
        "pola nowe w IWD2, brak w BG1; 0/0 występuje w 19 z 115 ARE IWD2 (obserwacja)")
    add("0x56 średni poziom drużyny", "0", "pole nowe w IWD2; docs: ustawiane przez grę; w plikach IWD2 0")
    add("0x58 nieznane (12 B)", "0", "docs: unknown; w IWD2 zawsze 0")
    add("0xA4 skrypt obszaru", "puste", "wymóg zadania: skrypt nieprzypisany")
    add("liczniki obiektów (aktorzy, regiony, spawn, kontenery, przedmioty, wierzchołki, "
        "ambienty, zmienne, drzwi, animacje, tiled objects)", "0", "wymóg zadania")
    add("0x98.. offsety pustych tabel", "0x12C (miejsce, w którym tabela by leżała)",
        "obserwacja: tak zapisują puste tabele ARE obu gier")
    add("0xA0 tiled object flags offset, 0xD4/0xD8 automap", "0", "obserwacja: IWD2 zapisuje 0 dla pustych")
    add("explored bitmask", "rozmiar 0", "obserwacja: nieodwiedzone obszary mają rozmiar 0")
    add("entrances", "1 wejście (%s)" % (entrance,) if entrance else "0",
        "opcja testowa; domyślnie puste (wymóg zadania)")
    add("song entries (0x90 B)", "dzień=noc=0, reszta slotów 0xFFFFFFFF, głośności 100",
        "muzyka BG1 ma inne numery niż music.ids IWD2; docs: 0 zatrzymuje muzykę. "
        "Wymaga sprawdzenia w grze")
    add("rest interruptions (0xE4 B)", "blok domyślny",
        "obserwacja: te same bajty w BG1 ar0401/ar2215 i IWD2 ar1201")
    add("0x48 typ, 0x4A-0x52 pogoda", "z ARE BG1 (type=0x%X, rain=%d snow=%d fog=%d "
        "lightning=%d wind=%d)" % (src.area_type, src.rain, src.snow, src.fog, src.lightning,
                                   src.wind),
        "te same pola i bity w obu wersjach (docs); to jedyne pola brane z BG poza nazwą WED")
    return r
