"""Mapy BMP lokacji: wyszukiwania (SR), wysokości (HT), światła (LM).

Źródła:
  * docs/BMP file format.html  - format pliku (BITMAPFILEHEADER/INFOHEADER,
    wiersze od dołu, dopełnione do 4 B, indeksy od zera).
  * docs/Notes and Conventions.html - silnik obsługuje BMP nieskompresowane,
    głębie 4, 8 i 24 bity.
  * docs/Search Maps.html - znaczenie indeksów 0..15 mapy wyszukiwania
    (UWAGA: strona opisuje tabelę "for BG2").
  * docs/Height Maps.html - paleta mapy wysokości: 4 bity, 16 odcieni szarości.
  * docs/ARE file format*.html - "AR0001SR/LM/HT.BMP".
Obserwacje na plikach (NIE z docs): nazwa BMP = nazwa WED + SR/LM/HT; SR i HT mają
4 bity, LM 8 bitów; wymiar = (W*64/16) x ceil(H*64/12), gdzie W,H = kafle.

ZAŁOŻENIA (zapisywane do raportów):
  A1. Tabela indeksów SR z docs (BG2) obowiązuje dla BG1 i IWD2: wszystkie
      indeksy w obu grach mieszczą się w 0..15 i palety są identyczne.
  A2. Mapowanie SR i HT = tożsamość (ten sam indeks), bo oba silniki używają tej
      samej palety; znaczenie wysokości nie jest w docs opisane indeks po indeksie.
      (Płaska mapa: BG1 = indeks 8, IWD2 zwykle 7 - patrz out/geometry_diff.md.)
  A3. LM: kolory z palety, bez mapowania indeksów.
Indeks bez ustalonego mapowania -> out/unmapped_indices.csv i MapConversionError.
"""
from __future__ import annotations

import csv
import struct
from dataclasses import dataclass, field
from pathlib import Path

# docs/Search Maps.html: wartość -> (opis, kolor, dźwięk kroków, chodzenie,
# przezroczystość dla fog of war, lot, pociski)
SEARCH_TABLE: dict[int, tuple[str, str, str, bool, bool, bool, bool]] = {
    0: ("Obstacle", "Black", "/", False, False, False, False),
    1: ("Sand", "Burgundy", "WAL_04", True, True, True, True),
    2: ("Wood", "Dark Green", "WAL_MT", True, True, True, True),
    3: ("Wood creaking", "Brown/Dark Yellow", "WAL_02", True, True, True, True),
    4: ("Stone echoey", "Dark Blue", "WAL_05", True, True, True, True),
    5: ("Grass", "Purple", "WAL_06", True, True, True, True),
    6: ("Water", "Turquoise", "WAL_01", True, True, True, True),
    7: ("Stone", "Light Gray", "WAL_03", True, True, True, True),
    8: ("Obstacle", "Dark Gray", "/", False, True, True, True),
    9: ("Wood creaking", "Red", "WAL_02", True, True, True, True),
    10: ("Wall", "Bright Green", "/", False, False, False, False),
    11: ("Water", "Yellow", "WAL_01", True, True, True, True),
    12: ("Water", "Blue", "/", False, True, True, True),
    13: ("Roof", "Magenta", "/", False, False, False, False),
    14: ("Worldmap exit", "Cyan", "/", False, True, True, True),
    15: ("Grass", "White", "WAL_04", True, True, True, True),
}

# Mapowania indeksów BG1 -> IWD2 (założenie A1/A2: tożsamość na 0..15).
INDEX_MAP: dict[str, dict[int, int]] = {
    "sr": {i: i for i in SEARCH_TABLE},
    "ht": {i: i for i in range(16)},
}

CELL_W = 16   # obserwacja, nie docs
CELL_H = 12
SUFFIX = {"sr": "SR", "lm": "LM", "ht": "HT"}
DEPTH = {"sr": 4, "ht": 4, "lm": 8}


class MapFormatError(ValueError):
    """BMP niezgodny z docs/BMP file format.html lub z oczekiwaniami mapy."""


class MapConversionError(ValueError):
    """Konwersja zatrzymana (rozmiar lub indeks bez mapowania)."""


@dataclass
class Bmp:
    width: int
    height: int
    bpp: int
    palette: list[tuple[int, int, int]]          # RGB, długość = liczba wpisów
    pixels: bytes                                 # w*h indeksów, wiersze od góry
    warnings: list[str] = field(default_factory=list)

    def __eq__(self, o) -> bool:
        return (isinstance(o, Bmp) and (self.width, self.height, self.bpp) ==
                (o.width, o.height, o.bpp) and self.palette == o.palette
                and self.pixels == o.pixels)


def _stride(w: int, bpp: int) -> int:
    return ((w * bpp + 31) // 32) * 4


def read_bmp(data: bytes, *, name: str = "BMP") -> Bmp:
    if len(data) < 54 or data[:2] != b"BM":
        raise MapFormatError(f"{name}: brak podpisu 'BM' lub plik krótszy niż 54 B")
    fsize, _r, off = struct.unpack_from("<III", data, 2)
    hs, w, h, planes, bpp, comp, isz, _xp, _yp, cu, _ci = struct.unpack_from(
        "<IiiHHIIiiII", data, 14)
    if hs != 40:
        raise MapFormatError(f"{name}: rozmiar InfoHeader {hs}, oczekiwano 40 "
                             "(BMP v5 to wariant EE - poza zakresem)")
    if planes != 1:
        raise MapFormatError(f"{name}: planes={planes}")
    if bpp not in (4, 8):
        raise MapFormatError(f"{name}: głębia {bpp} bit; obsługiwane 4 i 8")
    if comp != 0:
        raise MapFormatError(f"{name}: kompresja {comp}; obsługiwany tylko BI_RGB")
    if w <= 0 or h == 0:
        raise MapFormatError(f"{name}: wymiary {w}x{h}")
    top_down = h < 0
    h = abs(h)
    ncol = (off - 54) // 4
    if (off - 54) % 4 or not 1 <= ncol <= (1 << bpp):
        raise MapFormatError(f"{name}: DataOffset {off} daje {((off - 54) / 4)} wpisów palety")
    pal = [(data[54 + 4 * i + 2], data[54 + 4 * i + 1], data[54 + 4 * i])
           for i in range(ncol)]
    st = _stride(w, bpp)
    if len(data) < off + st * h:
        raise MapFormatError(f"{name}: dane obrazu krótsze niż {st}*{h} B")
    warn = []
    if fsize != len(data):
        warn.append(f"FileSize {fsize} != długość {len(data)}")
    rows = []
    for y in range(h):
        sy = y if top_down else h - 1 - y
        row = data[off + sy * st: off + (sy + 1) * st]
        if bpp == 4:
            px = bytearray()
            for b in row[:(w + 1) // 2]:
                px.append(b >> 4)
                px.append(b & 15)
            row = bytes(px[:w])
        else:
            row = bytes(row[:w])
        rows.append(row)
    return Bmp(w, h, bpp, pal, b"".join(rows), warn)


def write_bmp(b: Bmp) -> bytes:
    """Styl IWD2: INFOHEADER 40 B, wiersze od dołu, ColorsUsed=0 dla pełnej palety."""
    if b.bpp not in (4, 8):
        raise MapFormatError(f"głębia {b.bpp} nieobsługiwana")
    if len(b.pixels) != b.width * b.height:
        raise MapFormatError("liczba pikseli != width*height")
    ncol = len(b.palette)
    if not 1 <= ncol <= (1 << b.bpp):
        raise MapFormatError(f"paleta ma {ncol} wpisów")
    if b.pixels and max(b.pixels) >= ncol:
        raise MapFormatError(f"piksel {max(b.pixels)} poza paletą {ncol}")
    st = _stride(b.width, b.bpp)
    body = bytearray()
    for y in range(b.height - 1, -1, -1):
        row = b.pixels[y * b.width:(y + 1) * b.width]
        if b.bpp == 4:
            out = bytearray()
            for i in range(0, len(row), 2):
                hi = row[i]
                lo = row[i + 1] if i + 1 < len(row) else 0
                out.append((hi << 4) | lo)
        else:
            out = bytearray(row)
        out.extend(b"\0" * (st - len(out)))
        body += out
    pal = b"".join(bytes((bl, g, r_, 0)) for r_, g, bl in b.palette)
    off = 54 + len(pal)
    used = 0 if ncol == (1 << b.bpp) else ncol
    hdr = b"BM" + struct.pack("<III", off + len(body), 0, off)
    info = struct.pack("<IiiHHIIiiII", 40, b.width, b.height, 1, b.bpp, 0,
                       len(body), 2834, 2834, used, used)
    return hdr + info + pal + bytes(body)


def expected_size(tiles_w: int, tiles_h: int) -> tuple[int, int]:
    """Wymiar map SR/HT/LM dla obszaru tiles_w x tiles_h kafli (obserwacja)."""
    pw, ph = tiles_w * 64, tiles_h * 64
    return (pw + CELL_W - 1) // CELL_W, (ph + CELL_H - 1) // CELL_H


def index_stats(b: Bmp) -> dict[int, tuple[int, tuple[int, int]]]:
    """indeks -> (liczba pikseli, współrzędne (x, y) pierwszego wystąpienia;
    początek układu w lewym górnym rogu, wiersze skanowane od góry)."""
    cnt: dict[int, int] = {}
    first: dict[int, tuple[int, int]] = {}
    w = b.width
    for i, v in enumerate(b.pixels):
        if v in cnt:
            cnt[v] += 1
        else:
            cnt[v] = 1
            first[v] = (i % w, i // w)
    return {k: (cnt[k], first[k]) for k in sorted(cnt)}


def write_unmapped_csv(path: str | Path, rows: list[tuple[str, int, int, int, int]]) -> None:
    """rows: (plik, indeks, liczba pikseli, x, y)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["plik", "indeks", "liczba_pikseli", "x_pierwszego", "y_pierwszego"])
        w.writerows(rows)


def convert_map(kind: str, src: Bmp, tiles_w: int, tiles_h: int, *, name: str,
                unmapped: list | None = None) -> Bmp:
    """Konwertuje mapę BG1 -> IWD2. kind: 'sr' | 'ht' | 'lm'.

    Zatrzymuje się (MapConversionError) przy złym rozmiarze/głębi lub indeksie bez
    mapowania; wtedy wiersze trafiają do `unmapped` (do zapisu CSV)."""
    if kind not in DEPTH:
        raise ValueError(f"nieznany rodzaj mapy {kind!r}")
    if src.bpp != DEPTH[kind]:
        raise MapConversionError(
            f"{name}: głębia {src.bpp} bit, oczekiwano {DEPTH[kind]} dla {kind.upper()}")
    exp = expected_size(tiles_w, tiles_h)
    if (src.width, src.height) != exp:
        raise MapConversionError(
            f"{name}: wymiar {src.width}x{src.height} != {exp[0]}x{exp[1]} wynikający z WED "
            f"({tiles_w}x{tiles_h} kafli)")
    if kind == "lm":
        if src.pixels and max(src.pixels) >= len(src.palette):
            raise MapConversionError(f"{name}: indeks poza paletą")
        return Bmp(src.width, src.height, src.bpp, list(src.palette), src.pixels)
    table = INDEX_MAP[kind]
    stats = index_stats(src)
    bad = [(name, k, c, xy[0], xy[1]) for k, (c, xy) in stats.items()
           if k not in table or k >= len(src.palette)]
    if bad:
        if unmapped is not None:
            unmapped.extend(bad)
        raise MapConversionError(
            f"{name}: indeksy bez ustalonego mapowania: {[r[1] for r in bad]}")
    lut = bytes(table.get(i, 0) for i in range(256))
    return Bmp(src.width, src.height, src.bpp, list(src.palette),
               src.pixels.translate(lut))
