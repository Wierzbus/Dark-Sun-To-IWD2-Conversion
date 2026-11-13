"""Etap 2: ekrany pelnoekranowe (800x600) skalowane o s (np. 1.8 dla 1080p), ze wspolnymi zasobami Y*.BAM/MOS.

Okna CHU: pozycja = (dx + R(x), dy + R(y)), rozmiary R(.); blok 800x600 wysrodkowany poziomo i przyklejony do gory/dolu (dy=h-R(600)).
Czcionki: te o ukladzie 'cykl i = znak i+1' (255 cykli) przez TTF; INITIALS (30 klatek) i reszta BAM zwyklym skalowaniem.
"""
from __future__ import annotations

import struct
from pathlib import Path

from guiscale.bamio import read_bam, write_bam
from guiscale.bamscale import scale_bam
from guiscale.fontgen import scale_font
from guiscale.mosio import read_mos, write_mos
from PIL import Image

SCREENS = ["guiinv", "guirec", "guimap", "guijrnl", "guiopt", "guispl", "guistore", "guisp", "guicg", "guichap",
           "guiconn", "guiload", "guisave", "guikeys", "guimp", "guiwmap", "guimovie"]
PREFIX = "Y"


def _rs(b: bytes) -> str:
    return b.split(b"\0")[0].decode("latin-1")


def _put(buf: bytearray, off: int, name: str) -> None:
    buf[off:off + 8] = name.encode("latin-1").ljust(8, b"\0")


MENUS = ["start", "guibase", "guimg", "guipr", "guitest"]          # uklad 640x480 (menu glowne, przejscia)


def build_screens(game, w: int, h: int, s: float, ttf: str, out: Path, screens=SCREENS, base=(800, 600), prefix=PREFIX) -> list[str]:
    log: list[str] = []
    out.mkdir(parents=True, exist_ok=True)
    existing = {n.upper() for n, _t in game.iter_resources()} | {p.stem.upper() for p in out.glob("*")}
    newname: dict[tuple[str, str], str] = {}
    kinds: dict[tuple[str, str], str] = {}                    # (kind,name) -> 'mos'|'bam'|'font'
    R = lambda v: int(round(v * s))
    dx, dy = (w - R(base[0])) // 2, h - R(base[1])

    def nn(kind: str, name: str, how: str) -> str:
        if not name:
            return name
        key = (kind, name.upper())
        if key in newname:
            return newname[key]
        try:
            game.read(name, kind)
        except Exception:
            log.append(f"UWAGA: {kind} {name} nieodczytany - referencja bez zmian")
            return name
        nb = (prefix + name.upper())[:8]
        cand, i = nb, 0
        while cand in existing or cand in newname.values():
            i += 1
            cand = nb[:8 - len(str(i))] + str(i)
        newname[key] = cand
        kinds[key] = how
        return cand

    for scr in screens:
        try:
            chu = bytearray(game.read(scr, "CHU"))
        except Exception as e:
            log.append(f"UWAGA: {scr}.CHU nieodczytany ({e})")
            continue
        nwin, coff, woff = struct.unpack_from("<III", chu, 8)
        for i in range(nwin):
            wo = woff + 28 * i
            _id, _u, x, y, ww, hh, bgf, nc = struct.unpack_from("<HHHHHHHH", chu, wo)
            struct.pack_into("<HHHH", chu, wo + 4, dx + R(x), dy + R(y), R(ww), R(hh))
            if bgf:
                m = _rs(bytes(chu[wo + 0x10:wo + 0x18]))
                _put(chu, wo + 0x10, nn("MOS", m, "mos"))
            first = struct.unpack_from("<H", chu, wo + 0x18)[0]
            for c in range(nc):
                off, _ln = struct.unpack_from("<II", chu, coff + 8 * (first + c))
                cx, cy, cw, ch, ty = struct.unpack_from("<HHHHB", chu, off + 4)
                struct.pack_into("<HHHH", chu, off + 4, R(cx), R(cy), R(cw), R(ch))
                if ty in (0, 7):
                    b = _rs(bytes(chu[off + 14:off + 22]))
                    _put(chu, off + 14, nn("BAM", b, "bam"))
                elif ty == 5:
                    for p in (14, 22):
                        f = _rs(bytes(chu[off + p:off + p + 8]))
                        _put(chu, off + p, nn("BAM", f, "font"))
                elif ty == 6:
                    f = _rs(bytes(chu[off + 18:off + 26]))
                    _put(chu, off + 18, nn("BAM", f, "font"))
                elif ty == 3:
                    k = _rs(bytes(chu[off + 38:off + 46]))
                    _put(chu, off + 38, nn("BAM", k, "bam"))
                    f = _rs(bytes(chu[off + 58:off + 66]))
                    _put(chu, off + 58, nn("BAM", f, "font"))
                # typ 2 (suwak) i inne: geometria skalowana, zasoby bez zmian
        (out / f"{scr.upper()}.CHU").write_bytes(bytes(chu))
        log.append(f"{scr.upper()}.CHU: {nwin} okien, skala {s}, blok {base[0]}x{base[1]} -> {R(base[0])}x{R(base[1])} na ({dx},{dy})")

    for (kind, src), dst in sorted(newname.items()):
        how = kinds[(kind, src)]
        try:
            if how == "mos":
                img = read_mos(game.read(src, "MOS"))
                big = img.resize((max(1, R(img.width)), max(1, R(img.height))), Image.Resampling.LANCZOS)
                (out / f"{dst}.MOS").write_bytes(write_mos(big))
            else:
                b = read_bam(game.read(src, "BAM"))
                if how == "font" and len(b.cycles) >= 255 and len(b.frames) > 100:
                    nb = scale_font(b, ttf, s)
                else:
                    nb = scale_bam(b, s)
                (out / f"{dst}.BAM").write_bytes(write_bam(nb))
            log.append(f"{how.upper()} {src} -> {dst}")
        except Exception as e:
            log.append(f"BLAD {how} {src}: {e!r} (referencja do {dst} zostanie bez pliku!)")
    return log
