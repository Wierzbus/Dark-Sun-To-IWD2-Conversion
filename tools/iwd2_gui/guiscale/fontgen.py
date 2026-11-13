"""Czcionka BAM (255 klatek, cykl i = znak i+1; indeks 0 = przezroczysty, 17..255 = pokrycie) z fontu TTF.

Uklad: wszystkie glify stoja na wspolnej linii bazowej (rendering w naturalnych proporcjach TTF, wielkosc dobrana tak,
by wysokosc wersalika = wysokosc wersalika oryginalu * s). Poziomo: szerokosc ramki = round(w*s), a krok znaku (advance,
zakladamy w - cx jak w oryginale) = round((w-cx)*s), wiec odstepy w tekscie zostaja proporcjonalne do oryginalu.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from guiscale.bamio import Bam, Frame

SS = 4          # supersampling


def _cap_height_px(ttf: str, size: float) -> float:
    f = ImageFont.truetype(ttf, 400)
    bb = f.getbbox("H", anchor="ls")
    return (-bb[1]) * size / 400.0


def scale_font(orig: Bam, ttf: str, s: float) -> Bam:
    hcyc = orig.cycles[ord("H") - 1]
    cap_orig = orig.frames[hcyc[0]].cy                          # wysokosc wersalika nad linia bazowa w oryginale
    size = 400.0 * (cap_orig * s) / _cap_height_px(ttf, 400)
    font = ImageFont.truetype(ttf, size * SS)
    base = 60                                                   # wiersz linii bazowej na obrazie 1x
    frames: list[Frame] = []
    for cyc in orig.cycles:
        f = orig.frames[cyc[0]]
        code = len(frames) + 1
        nw = max(1, round(f.w * s))
        adv = round((f.w - f.cx) * s)
        ncx = nw - adv
        ch = bytes([code]).decode("cp1252", errors="replace") if code >= 32 else ""
        pix, nh, ncy = bytes(nw), 1, 1
        if ch.strip() and any(f.pix):
            cw = int(size * 3) + 20
            big = Image.new("L", (cw * SS, 120 * SS), 0)
            ImageDraw.Draw(big).text((10 * SS, base * SS), ch, font=font, fill=255, anchor="ls")
            im = big.resize((cw, 120), Image.Resampling.BOX)
            bb = im.point(lambda v: 255 if v > 24 else 0).getbbox()
            if bb:
                x0, y0, x1, y1 = bb
                glyph = im.crop((x0, y0, x1, y1))
                if glyph.width != nw:                            # dopasowanie szerokosci do ramki oryginalu * s
                    glyph = glyph.resize((nw, glyph.height), Image.Resampling.LANCZOS)
                nh, ncy = glyph.height, base - y0
                pix = bytes(0 if c < 12 else 17 + round((c / 255) * 238) for c in glyph.tobytes())
        else:
            nh, ncy = max(1, round(f.h * s)), round(f.cy * s)
            pix = bytes(nw * nh)
        frames.append(Frame(nw, nh, ncx, ncy, pix))
    return Bam(frames, [[i] for i in range(len(frames))], orig.palette, orig.transp)
