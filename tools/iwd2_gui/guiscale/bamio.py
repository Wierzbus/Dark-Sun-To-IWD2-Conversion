"""BAM V1 / BAMC: odczyt i zapis (klatki 8-bit z paleta, RLE koloru przezroczystego)."""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field


@dataclass
class Frame:
    w: int
    h: int
    cx: int
    cy: int
    pix: bytes            # w*h indeksow palety (wiersze od gory)


@dataclass
class Bam:
    frames: list[Frame]
    cycles: list[list[int]]          # kazdy cykl = lista indeksow klatek
    palette: list[int]               # 256 x 0xAARRGGBB-bajty jak w pliku (B,G,R,A) zapisane jako dword LE
    transp: int = 0


def read_bam(data: bytes) -> Bam:
    if data[:4] == b"BAMC":
        data = zlib.decompress(data[12:])
    if data[:8] != b"BAM V1  ":
        raise ValueError("to nie BAM V1")
    fc, cc, tr, feo, po, flo = struct.unpack_from("<HBBIII", data, 8)
    pal = list(struct.unpack_from("<256I", data, po))
    lookup = struct.unpack_from(f"<{(len(data) - flo) // 2}H", data, flo)
    frames = []
    for i in range(fc):
        w, h, cx, cy, off = struct.unpack_from("<HHhhI", data, feo + 12 * i)
        raw = not (off & 0x80000000)
        off &= 0x7FFFFFFF
        n = w * h
        if raw:                                    # bit 31 = 0 -> skompresowane RLE
            out = bytearray()
            p = off
            while len(out) < n:
                b = data[p]; p += 1
                if b == tr:
                    cnt = data[p] + 1; p += 1
                    out += bytes([tr]) * cnt
                else:
                    out.append(b)
            pix = bytes(out[:n])
        else:
            pix = bytes(data[off:off + n])
        frames.append(Frame(w, h, cx, cy, pix))
    cycles = []
    for c in range(cc):
        n, idx = struct.unpack_from("<HH", data, feo + 12 * fc + 4 * c)
        cycles.append(list(lookup[idx:idx + n]))
    return Bam(frames, cycles, pal, tr)


def _rle(pix: bytes, tr: int) -> bytes:
    out = bytearray()
    i, n = 0, len(pix)
    while i < n:
        b = pix[i]
        if b == tr:
            j = i
            while j < n and pix[j] == tr and j - i < 256:
                j += 1
            out += bytes([tr, j - i - 1])
            i = j
        else:
            out.append(b)
            i += 1
    return bytes(out)


def write_bam(b: Bam, compress: bool = True) -> bytes:
    fc, cc = len(b.frames), len(b.cycles)
    feo = 24
    po = feo + 12 * fc + 4 * cc
    flo = po + 1024
    lookup = [i for c in b.cycles for i in c]
    data_off = flo + 2 * len(lookup)
    blob = bytearray()
    ents = bytearray()
    for f in b.frames:
        enc = _rle(f.pix, b.transp)
        ents += struct.pack("<HHhhI", f.w, f.h, f.cx, f.cy, data_off + len(blob))      # bit31=0 -> RLE
        blob += enc
    cyc = bytearray()
    pos = 0
    for c in b.cycles:
        cyc += struct.pack("<HH", len(c), pos)
        pos += len(c)
    out = (b"BAM V1  " + struct.pack("<HBBIII", fc, cc, b.transp, feo, po, flo) + bytes(ents) + bytes(cyc)
           + struct.pack("<256I", *b.palette) + struct.pack(f"<{len(lookup)}H", *lookup) + bytes(blob))
    if compress:
        return b"BAMCV1  " + struct.pack("<I", len(out)) + zlib.compress(out, 9)
    return out
