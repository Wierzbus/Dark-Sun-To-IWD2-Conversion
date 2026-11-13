"""Regiony Dark Sun (RGNxx.GFF): mapa kafelkow i jej obraz.

Zawartosc RGNxx.GFF (ustalone na plikach gry):
  TILE n  - kafelek 16x16 w formacie BMP (darksun/bmp.py), id 1..254
  RMAP    - 128 x 98 bajtow: numer kafelka w polu mapy (wierszami)
  GMAP    - 128 x 98 bajtow: znaczniki pola (0x40 i inne; znaczenie do ustalenia, m.in. przechodnosc)
  ETAB    - tabela obiektow regionu (rozmieszczenie postaci i przedmiotow)
Paleta regionu: GPLDATA.GFF, PAL o id = numer regionu (np. RGN2D -> PAL 45).
"""
from __future__ import annotations

import os

from .bmp import decode_frames, frame_to_image, palette
from .gff import Gff

SZER, WYS, KAFEL = 128, 98, 16


class Region:
    def __init__(self, game_dir: str, numer: int):
        self.numer = numer
        self.gff = Gff.open(os.path.join(game_dir, f"RGN{numer:02X}.GFF"))
        gpl = Gff.open(os.path.join(game_dir, "GPLDATA.GFF"))
        self.paleta = palette(gpl.get("PAL ", numer)[:768])
        self.rmap = _jedyny(self.gff, "RMAP")
        self.gmap = _jedyny(self.gff, "GMAP")
        self.etab = _jedyny(self.gff, "ETAB")
        self.kafle = {rid: decode_frames(d)[0] for rid, d in self.gff.items("TILE")}

    def obraz(self):
        from PIL import Image
        im = Image.new("RGB", (SZER * KAFEL, WYS * KAFEL))
        cache = {}
        for i, tid in enumerate(self.rmap[: SZER * WYS]):
            fr = self.kafle.get(tid)
            if fr is None:
                continue
            if tid not in cache:
                cache[tid] = frame_to_image(fr, self.paleta).convert("RGB")
            im.paste(cache[tid], ((i % SZER) * KAFEL, (i // SZER) * KAFEL))
        return im


def _jedyny(g: Gff, tag: str) -> bytes:
    e = g.entries(tag)
    return g.get(tag, e[0].id) if e else b""
