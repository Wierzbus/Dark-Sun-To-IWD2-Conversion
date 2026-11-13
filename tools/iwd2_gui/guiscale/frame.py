"""Ramka menu (STON10L/R/T/B) na caly ekran W x H.

Silnik liczy cztery prostokaty ramki z (W-800)/2 i (H-600)/2 (L,R pelnej wysokosci; T,B w srodku) i rysuje w nich obrazy
STON10L/R/T/B w natywnym rozmiarze, od lewego gornego rogu prostokata. Dla 1024x768 obrazy maja dokladnie rozmiar prostokatow;
dla wiekszego ekranu podkladamy obrazy rozmiaru prostokatow: oryginalna ozdobna ramka 1024x768 wysrodkowana na ekranie,
reszta wypelniona ciemnym kamieniem. Dzieki temu menu zaslania caly HUD/swiat (brak 'resztek GUI').
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from guiscale.mosio import read_mos, write_mos


def build_frame(game, w: int, h: int) -> dict[str, bytes]:
    l, r = read_mos(game.read("ston10l", "MOS")), read_mos(game.read("ston10r", "MOS"))
    t, b = read_mos(game.read("ston10t", "MOS")), read_mos(game.read("ston10b", "MOS"))
    block = Image.new("RGB", (1024, 768))
    block.paste(l, (0, 0)); block.paste(r, (912, 0)); block.paste(t, (112, 0)); block.paste(b, (112, 684))
    # tlo: ciemny kamien o kolorze/ziarnie z zewnetrznej krawedzi ramki
    edge = np.asarray(block.crop((0, 100, 6, 668)), np.float32).reshape(-1, 3)
    base = edge.mean(axis=0) * 0.55
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 5.0, (h, w, 1))
    bg = np.clip(base + noise, 0, 255).astype(np.uint8)
    canvas = Image.fromarray(bg, "RGB").filter(ImageFilter.GaussianBlur(0.7))
    x0, y0 = (w - 1024) // 2, (h - 768) // 2
    canvas.paste(block, (x0, y0))
    sw, sh = (w - 800) // 2, (h - 600) // 2
    pieces = {
        "STON10L": canvas.crop((0, 0, sw, h)),
        "STON10R": canvas.crop((sw + 800, 0, sw + 800 + sw, h)),
        "STON10T": canvas.crop((sw, 0, sw + 800, sh)),
        "STON10B": canvas.crop((sw, sh + 600, sw + 800, sh + 600 + sh)),
    }
    return {f"{k}.MOS": write_mos(v) for k, v in pieces.items()}
