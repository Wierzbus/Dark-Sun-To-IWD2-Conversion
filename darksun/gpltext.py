"""Teksty w skryptach GPL/MAS (GPLDATA.GFF).

Napis w kodzie bajtowym: bajty 0x92 0x05, potem znaki 7-bitowe upakowane od najstarszego
bitu, zakonczone kodem 3; dlugosc zaokraglona do pelnych bajtow. Znak 9 = tabulator.
Przed napisem stoi zwykle `4f 00 xx` (xx = numer bufora tekstu, np. 0x73, 0x62).
Dlugie teksty sa dzielone na kawalki: kolejny kawalek tego samego bufora stoi bezposrednio
po poprzednim (`4f 00 xx 92 05 ...`) - takie kawalki sa sklejane.
Kody sterujace bajtowego kodu GPL (warunki, wybory dialogowe) nie sa jeszcze rozpoznane.
"""
from __future__ import annotations

from dataclasses import dataclass

MARK = b"\x92\x05"
END = 3


@dataclass
class Text:
    offset: int        # offset znacznika 0x92 w skrypcie
    end: int           # pierwszy bajt po napisie
    buffer: int | None # xx z `4f 00 xx`, jesli wystepuje
    text: str
    parts: int = 1


def decode7(b: bytes, p: int) -> tuple[str, int]:
    out = bytearray()
    bit = 0
    while True:
        v = 0
        for _ in range(7):
            byte = b[p + (bit >> 3)]
            v = (v << 1) | ((byte >> (7 - (bit & 7))) & 1)
            bit += 1
        if v == END:
            return out.decode("latin-1"), p + ((bit + 7) >> 3)
        if v == 0 or (v < 32 and v != 9):
            raise ValueError("niedozwolony znak w napisie")
        out.append(v)


def scan(b: bytes) -> list[Text]:
    """Wszystkie napisy w skrypcie, po kolei; falszywe trafienia znacznika sa pomijane."""
    out, p = [], 0
    while True:
        k = b.find(MARK, p)
        if k < 0:
            return out
        try:
            s, e = decode7(b, k + 2)
        except (ValueError, IndexError):
            p = k + 1
            continue
        buf = b[k - 1] if k >= 3 and b[k - 3] == 0x4F and b[k - 2] == 0x00 else None
        out.append(Text(k, e, buf, s))
        p = e


def merged(b: bytes) -> list[Text]:
    """Napisy ze sklejonymi kawalkami dlugich tekstow."""
    out: list[Text] = []
    for t in scan(b):
        prev = out[-1] if out else None
        if prev and t.buffer is not None and t.buffer == prev.buffer and t.offset - prev.end == 3:
            prev.text += t.text
            prev.end = t.end
            prev.parts += 1
        else:
            out.append(t)
    return out


def pack7(s: str) -> bytes:
    """Odwrotnosc decode7 (do testow i ewentualnej edycji tekstow)."""
    bits = "".join(format(ord(c), "07b") for c in s) + format(END, "07b")
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
