"""Etap 1 upscale'u GUI: HUD z GUIW10.CHU skalowany o czynnik s (tla MOS, przyciski BAM, czcionka z TTF).

Wynik (kopie z NOWYMI nazwami, oryginalne zasoby nietkniete): GUIW10.CHU + Z*.MOS + Z*.BAM -> IWD2\\override.
"""
from __future__ import annotations

import io
import struct
from pathlib import Path

from PIL import Image

from guiscale.bamio import read_bam, write_bam
from guiscale.bamscale import scale_bam
from guiscale.fontgen import scale_font
from guiscale.mosio import read_mos, write_mos

FONT_BAMS = {"NORMAL"}


ENGINE_BAMS = [f'form{c}' for c in '0123456789ab'] + ['stonform']


def _rs(b: bytes) -> str:
    return b.split(b"\0")[0].decode("latin-1")


def _put(buf: bytearray, off: int, name: str) -> None:
    buf[off:off + 8] = name.encode("latin-1").ljust(8, b"\0")


def build(game, w: int, h: int, s: float, ttf: str, out: Path) -> list[str]:
    log: list[str] = []
    out.mkdir(parents=True, exist_ok=True)
    existing = {n.upper() for n, _t in game.iter_resources()}
    newname: dict[tuple[str, str], str] = {}

    missing: set[str] = set()

    def nn(kind: str, name: str) -> str:
        key = (kind, name.upper())
        if not name:
            return name
        if key not in newname:
            try:
                game.read(name, kind)
            except Exception:
                missing.add(f"{kind} {name}")
                return name                                   # brak zasobu lokalnie - referencja bez zmian
        if key not in newname:
            cand = ("Z" + name.upper())[:8]
            i = 0
            while cand in existing or cand in newname.values():
                i += 1
                cand = ("Z" + name.upper())[:7 - len(str(i))] + str(i) if False else ("Z" + name.upper())[:8 - len(str(i))] + str(i)
            newname[key] = cand
        return newname[key]

    chu = bytearray(game.read("guiw10", "CHU"))
    if chu[:8] != b"CHUIV1  ":
        raise SystemExit("STOP: to nie jest CHU V1.")
    nwin, coff, woff = struct.unpack_from("<III", chu, 8)
    R = lambda v: int(round(v * s))
    dx, dy = (w - R(1024)) // 2, h - R(768)
    mos_todo: dict[str, str] = {}
    bam_todo: dict[str, str] = {}
    font_todo: dict[str, str] = {}
    caret_todo: dict[str, str] = {}
    for i in range(nwin):
        wo = woff + 28 * i
        wid, _u, x, y, ww, hh, bgf, nc = struct.unpack_from("<HHHHHHHH", chu, wo)
        struct.pack_into("<HHHH", chu, wo + 4, dx + R(x), dy + R(y), R(ww), R(hh))
        if bgf:
            m = _rs(bytes(chu[wo + 0x10:wo + 0x18]))
            mos_todo[m] = nn("MOS", m)
            _put(chu, wo + 0x10, mos_todo[m])
        first = struct.unpack_from("<H", chu, wo + 0x18)[0]
        for c in range(nc):
            off, ln = struct.unpack_from("<II", chu, coff + 8 * (first + c))
            cx, cy, cw, ch, ty = struct.unpack_from("<HHHHB", chu, off + 4)
            struct.pack_into("<HHHH", chu, off + 4, R(cx), R(cy), R(cw), R(ch))
            if ty in (0, 7):                                   # przycisk / pasek przewijania: BAM @14
                b = _rs(bytes(chu[off + 14:off + 22]))
                bam_todo[b] = nn("BAM", b)
                _put(chu, off + 14, bam_todo[b])
            elif ty == 5:                                      # pole tekstowe: dwie czcionki @14, @22
                for p in (14, 22):
                    f = _rs(bytes(chu[off + p:off + p + 8]))
                    font_todo[f] = nn("BAM", f)
                    _put(chu, off + p, font_todo[f])
            elif ty == 6:                                      # etykieta: czcionka @18
                f = _rs(bytes(chu[off + 18:off + 26]))
                font_todo[f] = nn("BAM", f)
                _put(chu, off + 18, font_todo[f])
            elif ty == 3:                                      # pole edycji: kursor @38, czcionka @58
                k = _rs(bytes(chu[off + 38:off + 46]))
                caret_todo[k] = nn("BAM", k)
                _put(chu, off + 38, caret_todo[k])
                f = _rs(bytes(chu[off + 58:off + 66]))
                font_todo[f] = nn("BAM", f)
                _put(chu, off + 58, font_todo[f])
                tx, ty2 = struct.unpack_from("<HH", chu, off + 14 + 22 + 0) if False else (0, 0)
    (out / "GUIW10.CHU").write_bytes(bytes(chu))
    log.append(f"GUIW10.CHU: {nwin} okien, skala {s}, blok {R(1024)}x{R(768)} na ({dx},{dy})")
    for src, dst in mos_todo.items():
        if src == dst:
            continue
        img = read_mos(game.read(src, "MOS"))
        big = img.resize((max(1, R(img.width)), max(1, R(img.height))), Image.Resampling.LANCZOS)
        (out / f"{dst}.MOS").write_bytes(write_mos(big))
        log.append(f"MOS {src} {img.size} -> {dst} {big.size}")
    for m in sorted(missing):
        log.append(f"UWAGA: {m} nieodczytany - referencja bez zmian")
    for src, dst in {**bam_todo, **caret_todo}.items():
        if src == dst:
            continue
        b = read_bam(game.read(src, "BAM"))
        (out / f"{dst}.BAM").write_bytes(write_bam(scale_bam(b, s)))
        log.append(f"BAM {src} ({len(b.frames)} kl.) -> {dst}")
    for src, dst in font_todo.items():
        if src == dst:
            continue
        b = read_bam(game.read(src, "BAM"))
        (out / f"{dst}.BAM").write_bytes(write_bam(scale_font(b, ttf, s)))
        log.append(f"FONT {src} -> {dst} ({ttf.split('/')[-1]})")
    # BAM-y ladowane przez silnik po nazwie (nie z CHU) - nadpisanie pod ta sama nazwa
    for n in ENGINE_BAMS:
        try:
            b = read_bam(game.read(n, "BAM"))
        except Exception as e:
            log.append(f"UWAGA: {n}.BAM nieodczytany ({e})")
            continue
        (out / f"{n.upper()}.BAM").write_bytes(write_bam(scale_bam(b, s)))
        log.append(f"BAM (nazwa silnika) {n} ({len(b.frames)} kl.) skala {s}")
    return log
