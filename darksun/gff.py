"""Kontenery GFF (SSI, Dark Sun: Shattered Lands).

Naglowek (28 B): magic 'GFFI', u32 wersja (0x00030000), u32 data_location,
u32 toc_location, u32 toc_length, u32 file_flags, u32 data0.
Spis (TOC): u32, u32, u16 liczba_typow, potem dla kazdego typu: 4 znaki tagu, u32 licznik.
- licznik bez bitu 31: licznik * (u32 id, u32 offset, u32 dlugosc)
- licznik z bitem 31 (segmentowany): u32 liczba_wpisow, u32 seg_loc_id, u32 liczba_segmentow,
  segmenty (u32 pierwsze_id, u32 ile); tabela (offset, dlugosc) lezy w zasobie typu GFFI
  o id = seg_loc_id: u32 n, potem n * (u32 offset, u32 dlugosc).
Ustalone na plikach gry; zgodne dla wszystkich 42 plikow GFF z instalacji.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    id: int
    offset: int
    length: int


class Gff:
    def __init__(self, data: bytes):
        self.data = data
        self.types: dict[str, list[Entry]] = _read_toc(data)

    @classmethod
    def open(cls, path) -> "Gff":
        with open(path, "rb") as f:
            return cls(f.read())

    def tags(self) -> list[str]:
        return list(self.types)

    def entries(self, tag: str) -> list[Entry]:
        return self.types.get(tag.ljust(4), [])

    def get(self, tag: str, rid: int) -> bytes:
        for e in self.entries(tag):
            if e.id == rid:
                return self.data[e.offset:e.offset + e.length]
        raise KeyError((tag, rid))

    def items(self, tag: str):
        for e in self.entries(tag):
            yield e.id, self.data[e.offset:e.offset + e.length]


def _read_toc(d: bytes) -> dict[str, list[Entry]]:
    magic, _ver, _dl, tl, tlen, _fl, _d0 = struct.unpack_from("<4sIIIIII", d, 0)
    if magic != b"GFFI":
        raise ValueError(f"to nie jest plik GFF (magic {magic!r})")
    t = d[tl:tl + tlen]
    _a, _b, ntypes = struct.unpack_from("<IIH", t, 0)
    p = 10
    out: dict[str, list[Entry]] = {}
    seg: list[tuple[str, list[int], int]] = []
    for _ in range(ntypes):
        tag_b, cnt = struct.unpack_from("<4sI", t, p)
        p += 8
        tag = tag_b.decode("latin-1")
        if cnt & 0x80000000:
            _n, seg_loc_id, nseg = struct.unpack_from("<III", t, p)
            p += 12
            ids: list[int] = []
            for _ in range(nseg):
                first, num = struct.unpack_from("<II", t, p)
                p += 8
                ids.extend(range(first, first + num))
            seg.append((tag, ids, seg_loc_id))
            out[tag] = []
        else:
            out[tag] = [Entry(*struct.unpack_from("<III", t, p + 12 * i)) for i in range(cnt)]
            p += 12 * cnt
    gffi = {e.id: e for e in out.get("GFFI", [])}
    for tag, ids, sl in seg:
        loc = gffi[sl].offset
        n = struct.unpack_from("<I", d, loc)[0]
        tab = [struct.unpack_from("<II", d, loc + 4 + 8 * i) for i in range(n)]
        out[tag] = [Entry(ids[i], a, b) for i, (a, b) in enumerate(tab) if i < len(ids)]
    return out
