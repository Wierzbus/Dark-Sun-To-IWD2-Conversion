"""Male portrety HUD (*_S.BMP 42x42 = kadr twarzy z *_L.BMP 210x330) generowane ostrzej wprost z duzych (Lanczos), rozmiar round(42*s).

Kadr twarzy dobierany dopasowaniem (min. blad po zmniejszeniu do 42x42) - oryginalny kadr nie jest zapisany w danych.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import numpy as np
from PIL import Image


def _bmp(im: Image.Image) -> bytes:
    b = io.BytesIO()
    im.convert("RGB").save(b, "BMP")
    return b.getvalue()


def find_crop(L: Image.Image, S: Image.Image):
    s = np.asarray(S.convert("RGB"), np.float32)
    best = (1e18, None)
    Lw, Lh = L.size
    for k in range(70, 150, 4):
        for y in range(0, min(Lh - k, 70) + 1, 4):
            for x in range(0, Lw - k + 1, 4):
                c = np.asarray(L.crop((x, y, x + k, y + k)).resize((42, 42), Image.Resampling.BILINEAR), np.float32)
                e = float(((c - s) ** 2).mean())
                if e < best[0]:
                    best = (e, (x, y, k))
    x0, y0, k0 = best[1]
    for k in range(max(40, k0 - 4), k0 + 5):
        for y in range(max(0, y0 - 4), y0 + 5):
            for x in range(max(0, x0 - 4), x0 + 5):
                if x + k > Lw or y + k > Lh:
                    continue
                c = np.asarray(L.crop((x, y, x + k, y + k)).resize((42, 42), Image.Resampling.BILINEAR), np.float32)
                e = float(((c - s) ** 2).mean())
                if e < best[0]:
                    best = (e, (x, y, k))
    return best


def build(game, s: float, out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    log = []
    n = max(1, round(42 * s))
    for name, t in game.iter_resources():
        if t not in (1, "BMP") or not re.search(r"_s$", name, re.I):
            continue
        base = name[:-2]
        try:
            S = Image.open(io.BytesIO(game.read(name, "BMP")))
            L = Image.open(io.BytesIO(game.read(base + "_l", "BMP"))).convert("RGB")
        except Exception:
            continue
        if S.size != (42, 42) or L.size != (210, 330):
            continue
        e, (x, y, k) = find_crop(L, S)
        big = L.crop((x, y, x + k, y + k)).resize((n, n), Image.Resampling.LANCZOS)
        (out / f"{name.upper()}.BMP").write_bytes(_bmp(big))
        log.append(f"{name.upper()}.BMP {n}x{n} (kadr {x},{y},{k}; blad {e:.0f})")
    return log


def build_large(game, s: float, out: Path) -> list[str]:
    """Duze portrety *_L.BMP 210x330 -> round(210*s) x round(330*s): Lanczos + lekkie wyostrzenie (bez nowych detali)."""
    from PIL import ImageFilter
    out.mkdir(parents=True, exist_ok=True)
    log = []
    nw, nh = round(210 * s), round(330 * s)
    for name, t in game.iter_resources():
        if t not in (1, "BMP") or not re.search(r"_l$", name, re.I):
            continue
        try:
            L = Image.open(io.BytesIO(game.read(name, "BMP"))).convert("RGB")
        except Exception:
            continue
        if L.size != (210, 330):
            continue
        big = L.resize((nw, nh), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
        (out / f"{name.upper()}.BMP").write_bytes(_bmp(big))
        log.append(f"{name.upper()}.BMP {nw}x{nh}")
    return log
