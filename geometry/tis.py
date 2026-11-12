"""TIS (klasyczny, palette-based) - odczyt, kontrola, zapis.

Źródło: docs/TIS file format.html (nagłówek 0x18 B: 'TIS ', 'V1  ', liczba kafli,
długość kafla 0x1400, rozmiar nagłówka 0x18, wymiar kafla 64; kafel = paleta
256 x BGRA (1024 B) + 4096 B indeksów; indeks 0 = przezroczysty).

Obserwacja (nie z docs): tileset wyciągnięty z BIF przez GameResources nie ma
nagłówka (same kafle). Plik w override musi go mieć, więc zapis zawsze dopisuje.

Konwersja BG1 -> IWD2 dla klasycznego TIS = kopia kafli (ten sam format).
Wariant PVRZ (EE, długość kafla 12) jest poza zakresem -> TisFormatError.
"""
from __future__ import annotations

import struct

TILE_BYTES = 0x1400
PALETTE_BYTES = 1024
PIXELS = 64 * 64
HEADER_SIZE = 0x18
PVRZ_TILE_BYTES = 12


class TisFormatError(ValueError):
    """Plik nie jest klasycznym TIS zgodnym z docs/TIS file format.html."""


class Tis:
    """Zbiór kafli; `data` = count * 5120 B (palety i piksele)."""

    def __init__(self, data: bytes):
        if len(data) % TILE_BYTES:
            raise TisFormatError(
                f"dane kafli: {len(data)} B nie jest wielokrotnością {TILE_BYTES}")
        self.data = bytes(data)

    @property
    def count(self) -> int:
        return len(self.data) // TILE_BYTES

    def tile(self, i: int) -> bytes:
        if not 0 <= i < self.count:
            raise IndexError(f"kafel {i} poza zakresem 0..{self.count - 1}")
        return self.data[i * TILE_BYTES:(i + 1) * TILE_BYTES]

    def palette(self, i: int) -> list[tuple[int, int, int]]:
        t = self.tile(i)
        return [(t[k * 4 + 2], t[k * 4 + 1], t[k * 4]) for k in range(256)]

    def pixels(self, i: int) -> bytes:
        return self.tile(i)[PALETTE_BYTES:]

    def __eq__(self, other) -> bool:
        return isinstance(other, Tis) and other.data == self.data


def read_tis(data: bytes, *, name: str = "TIS") -> Tis:
    """Czyta TIS z nagłówkiem albo surowe kafle (z BIF). Błędy -> TisFormatError."""
    if data[:4] == b"TIS ":
        if len(data) < HEADER_SIZE:
            raise TisFormatError(f"{name}: plik krótszy niż nagłówek ({len(data)} B)")
        ver = data[4:8]
        if ver.rstrip(b" \0") != b"V1":
            raise TisFormatError(f"{name}: wersja {ver!r}, oczekiwano 'V1  '")
        count, tsize, hsize, dim = struct.unpack_from("<4I", data, 8)
        if tsize == PVRZ_TILE_BYTES:
            raise TisFormatError(
                f"{name}: TIS PVRZ (EE) - poza zakresem (klasyczny silnik: 5120 B)")
        if tsize != TILE_BYTES:
            raise TisFormatError(f"{name}: długość kafla {tsize}, oczekiwano {TILE_BYTES}")
        if hsize != HEADER_SIZE:
            raise TisFormatError(f"{name}: rozmiar nagłówka {hsize}, oczekiwano {HEADER_SIZE}")
        if dim != 64:
            raise TisFormatError(f"{name}: wymiar kafla {dim}, oczekiwano 64")
        need = HEADER_SIZE + count * TILE_BYTES
        if len(data) != need:
            raise TisFormatError(
                f"{name}: długość pliku {len(data)} != nagłówek+{count}*5120 = {need}")
        return Tis(data[HEADER_SIZE:])
    # brak nagłówka: tileset z BIF
    if not data or len(data) % TILE_BYTES:
        raise TisFormatError(
            f"{name}: brak podpisu 'TIS ' i długość {len(data)} B nie jest "
            f"wielokrotnością {TILE_BYTES} (nie jest to ani TIS, ani surowe kafle z BIF)")
    return Tis(data)


def write_tis(tis: Tis) -> bytes:
    return (b"TIS " + b"V1  "
            + struct.pack("<4I", tis.count, TILE_BYTES, HEADER_SIZE, 64) + tis.data)


def convert_tis(src: Tis) -> Tis:
    """BG1 -> IWD2 (klasyczny): ten sam format kafli, kopia."""
    return Tis(src.data)


def require_tiles(tis: Tis, max_index: int, *, name: str = "TIS") -> None:
    """Kontrola z WED: największy indeks z tabeli lookup musi mieścić się w TIS."""
    if max_index >= tis.count:
        raise TisFormatError(
            f"{name}: WED odwołuje się do kafla {max_index}, a TIS ma {tis.count} kafli")
