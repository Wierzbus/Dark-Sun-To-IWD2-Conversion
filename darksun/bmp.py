"""Grafiki BMP z kontenerow GFF Dark Sun (ikony przedmiotow, sprite'y) i palety PAL.

Zasob: u32 rozmiar, u16 liczba_klatek, liczba_klatek * u32 offset klatki.
Klatka: u16 szerokosc, u16 wysokosc, potem wiersze:
  u8 y (0xFF = koniec klatki), dalej odcinki:
  u8 x, u8 flagi (bit 0x80 = ostatni odcinek wiersza), u8 n (liczba pikseli), u8 a (dlugosc strumienia),
  a bajtow strumienia: bajt sterujacy c, potem dane:
    c parzyste -> c/2 + 1 pikseli dosłownie,
    c nieparzyste -> nastepny bajt powtorzony (c + 1)/2 razy;
  az do zdekodowania n pikseli. Piksele spoza odcinkow sa przezroczyste.
Paleta PAL: 768 B, 256 * RGB w skali 0..63 (VGA).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass
class Frame:
    width: int
    height: int
    pixels: dict  # (x, y) -> indeks koloru


def decode_frames(b: bytes) -> list[Frame]:
    _size, nf = struct.unpack_from("<IH", b, 0)
    offs = struct.unpack_from(f"<{nf}I", b, 6)
    return [_decode_frame(b, o) for o in offs]


def _decode_frame(b: bytes, o: int) -> Frame:
    w, h = struct.unpack_from("<HH", b, o)
    p = o + 4
    px: dict = {}
    while True:
        y = b[p]
        p += 1
        if y == 0xFF:
            return Frame(w, h, px)
        while True:
            x, fl, n, a = b[p:p + 4]
            p += 4
            stream, p = b[p:p + a], p + a
            row = _unpack(stream)
            if len(row) != n:
                raise ValueError(f"odcinek y={y} x={x}: {len(row)} pikseli zamiast {n}")
            for k, c in enumerate(row):
                px[(x + k, y)] = c
            if fl & 0x80:
                break


def _unpack(s: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(s):
        c = s[i]
        i += 1
        if c & 1:
            out += bytes([s[i]]) * ((c + 1) // 2)
            i += 1
        else:
            k = c // 2 + 1
            out += s[i:i + k]
            i += k
    return bytes(out)


def palette(pal: bytes) -> list[tuple]:
    if len(pal) != 768:
        raise ValueError("paleta musi miec 768 B")
    return [tuple(min(255, v * 255 // 63) for v in pal[i * 3:i * 3 + 3]) for i in range(256)]


def frame_to_image(fr: Frame, pal: list[tuple]):
    from PIL import Image
    img = Image.new("RGBA", (max(fr.width, 1), max(fr.height, 1)), (0, 0, 0, 0))
    for (x, y), c in fr.pixels.items():
        if 0 <= x < img.width and 0 <= y < img.height:
            img.putpixel((x, y), pal[c] + (255,))
    return img
