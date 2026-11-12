"""MOS V1 / MOSC V1 (docs/MOS file format.html): odczyt, zapis MOSC, minimapa z obrazu obszaru.

Z docs: nagłówek 0x18 B (sig, ver, szer., wys., kolumny, wiersze, rozmiar bloku 64,
offset palet); palety 256 x RGBAQUAD na blok; tablica offsetów kafli (dword, względem
początku danych pikseli); bloki brzegowe mają tylko tyle pikseli, ile potrzeba;
MOSC = 12 B nagłówka (sig, ver, długość po dekompresji) + zlib. Skala minimapy z docs:
dla IWD "32/4" (obraz obszaru / 8).
OBSERWACJA (nie docs): dane pikseli to 1 B indeksu na piksel; IWD2 przechowuje
minimapy jako MOSC.
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

from PIL import Image

HEADER_SIZE = 0x18
BLOCK = 64
IWD_MINIMAP_DIV = 8          # docs: 32/4


class MosFormatError(ValueError):
    """Plik nie jest MOS/MOSC V1 zgodnym ze specyfikacją."""


@dataclass
class Mos:
    width: int
    height: int
    cols: int
    rows: int
    palettes: list[bytes]    # 1024 B (BGRA) na blok
    blocks: list[bytes]      # indeksy pikseli bloku (w*h)

    def block_size(self, n: int) -> tuple[int, int]:
        c, r = n % self.cols, n // self.cols
        return (min(BLOCK, self.width - c * BLOCK), min(BLOCK, self.height - r * BLOCK))

    def to_image(self) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height))
        for n, (pal, px) in enumerate(zip(self.palettes, self.blocks)):
            bw, bh = self.block_size(n)
            rgb = [(pal[i * 4 + 2], pal[i * 4 + 1], pal[i * 4]) for i in range(256)]
            t = Image.new("RGB", (bw, bh))
            t.putdata([rgb[i] for i in px])
            img.paste(t, ((n % self.cols) * BLOCK, (n // self.cols) * BLOCK))
        return img


def read_mos(data: bytes, *, name: str = "MOS") -> Mos:
    if data[:4] == b"MOSC":
        if data[4:8] != b"V1  " or len(data) < 12:
            raise MosFormatError(f"{name}: zły nagłówek MOSC {data[:8]!r}")
        n = struct.unpack_from("<I", data, 8)[0]
        try:
            data = zlib.decompress(data[12:])
        except zlib.error as e:
            raise MosFormatError(f"{name}: błąd zlib: {e}") from None
        if len(data) != n:
            raise MosFormatError(f"{name}: długość po dekompresji {len(data)} != {n}")
    if data[:4] != b"MOS " or data[4:8] != b"V1  ":
        raise MosFormatError(f"{name}: podpis/wersja {data[:8]!r} (oczekiwano 'MOS V1  ')")
    if len(data) < HEADER_SIZE:
        raise MosFormatError(f"{name}: plik krótszy niż nagłówek")
    w, h, cols, rows, bs, pal_off = struct.unpack_from("<HHHHII", data, 8)
    if bs != BLOCK:
        raise MosFormatError(f"{name}: rozmiar bloku {bs}, oczekiwano {BLOCK}")
    if cols != -(-w // BLOCK) or rows != -(-h // BLOCK):
        raise MosFormatError(f"{name}: {cols}x{rows} bloków nie pasuje do {w}x{h}")
    n = cols * rows
    off_tab = pal_off + n * 1024
    pix0 = off_tab + n * 4
    if pix0 > len(data):
        raise MosFormatError(f"{name}: tablice wykraczają poza plik")
    pals = [data[pal_off + i * 1024: pal_off + (i + 1) * 1024] for i in range(n)]
    m = Mos(w, h, cols, rows, pals, [])
    for i in range(n):
        o = struct.unpack_from("<I", data, off_tab + i * 4)[0]
        bw, bh = m.block_size(i)
        blk = data[pix0 + o: pix0 + o + bw * bh]
        if len(blk) != bw * bh:
            raise MosFormatError(f"{name}: blok {i} poza plikiem")
        m.blocks.append(blk)
    return m


def write_mos(m: Mos, *, compressed: bool = True) -> bytes:
    n = m.cols * m.rows
    out = bytearray(b"MOS V1  ")
    out += struct.pack("<HHHHII", m.width, m.height, m.cols, m.rows, BLOCK, HEADER_SIZE)
    for p in m.palettes:
        out += p
    off = 0
    for b in m.blocks:
        out += struct.pack("<I", off)
        off += len(b)
    for b in m.blocks:
        out += b
    assert len(m.palettes) == len(m.blocks) == n
    if not compressed:
        return bytes(out)
    return b"MOSC" + b"V1  " + struct.pack("<I", len(out)) + zlib.compress(bytes(out), 9)


def build_minimap(area: Image.Image, div: int = IWD_MINIMAP_DIV) -> Mos:
    """Minimapa: obraz obszaru / div, bloki 64x64, każdy kwantyzowany do 256 kolorów."""
    w, h = max(1, area.width // div), max(1, area.height // div)
    small = area.resize((w, h), Image.BOX)
    cols, rows = -(-w // BLOCK), -(-h // BLOCK)
    pals, blocks = [], []
    for r in range(rows):
        for c in range(cols):
            tile = small.crop((c * BLOCK, r * BLOCK, min(w, (c + 1) * BLOCK), min(h, (r + 1) * BLOCK)))
            q = tile.quantize(256, method=Image.MEDIANCUT, dither=Image.NONE)
            flat = q.getpalette() or []
            flat = (flat + [0] * 768)[:768]
            pal = bytearray()
            for i in range(256):
                pal += bytes((flat[i * 3 + 2], flat[i * 3 + 1], flat[i * 3], 0))
            pals.append(bytes(pal))
            blocks.append(bytes(q.tobytes()))
    return Mos(w, h, cols, rows, pals, blocks)
