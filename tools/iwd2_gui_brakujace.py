"""Odtwarza brakujace grafiki GUI 1920x1080 (prefiksy Y*/Z*) z oryginalow gry.

Ekrany CHU w wersji 1920 odwoluja sie do kopii grafik o nazwach z prefiksem Y (skala x1,8) albo Z
(okno GUIW10, skala x1,4). Dla kazdej brakujacej nazwy skrypt:
- szuka tej samej kontrolki (okno, id) w oryginalnym CHU gry i bierze stamtad oryginalny zasob,
- liczy skale z rozmiaru kontrolki (nowa / oryginalna), osobno w poziomie i w pionie (mediana),
- powieksza BAM (wszystkie klatki i srodki) albo MOS (tlo okna).
Przezroczystosc: kolor krawedzi rozlany na tlo przed filtrem (bez zielonych obwodek), maska
przezroczystosci skalowana osobno i progowana, czysta zielen tylko na indeksie przezroczystym
(BAM) albo na indeksie 0 palety kafla (MOS).

  python tools/iwd2_gui_brakujace.py --gra KATALOG_GRY --chu KATALOG_Z_CHU_1920 --out WYNIK
"""
import argparse
import collections
import glob
import os
import re
import struct
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from iwd2_ikony import czytaj_bam, powieksz, zapisz_bam  # noqa: E402
from iwd2_poszerz_tla import czytaj_mos, zapisz_mos, usun_zielona_obwodke, ZIELEN  # noqa: E402
from inventory.resource_reader import GameResources  # noqa: E402


def chu(d):
    nw, co, wo = struct.unpack_from("<III", d, 8)
    okna = {}
    for w in range(nw):
        rec = d[wo + w * 28:wo + w * 28 + 28]
        wid, _, _, ww, wh = struct.unpack_from("<HHHHH", rec, 0)
        nc, = struct.unpack_from("<H", rec, 14)
        fc, = struct.unpack_from("<H", rec, 24)
        tlo = rec[16:24].split(b"\0")[0].decode("latin1").upper()
        k = {}
        for c in range(fc, fc + nc):
            off, ln = struct.unpack_from("<II", d, co + c * 8)
            k[struct.unpack_from("<I", d, off)[0]] = d[off:off + ln]
        okna[wid] = (ww, wh, tlo, k)
    return okna


def mapa(chu_dir, gra, jest):
    """nazwa -> (oryginal, typ, kx, ky)"""
    wyn = collections.defaultdict(list)
    for f in glob.glob(os.path.join(chu_dir, "*.CHU")):
        nazwa = os.path.splitext(os.path.basename(f))[0]
        try:
            orig = gra.read(nazwa, "CHU")
        except Exception:
            continue
        o, n = chu(orig), chu(open(f, "rb").read())
        for wid, (ww, wh, tlo, k) in n.items():
            if wid not in o:
                continue
            ow, oh, otlo, ok = o[wid]
            if tlo and tlo not in jest and ow and oh:
                wyn[tlo].append((otlo, "MOS", ww / ow, wh / oh))
            for cid, cd in k.items():
                if cid not in ok:
                    continue
                od = ok[cid]
                cw, ch = struct.unpack_from("<HH", cd, 8)
                ow2, oh2 = struct.unpack_from("<HH", od, 8)
                if not (ow2 and oh2):
                    continue
                for m in re.finditer(rb"[A-Za-z0-9_]{4,8}", cd[0x0E:]):
                    s = m.group().decode().upper()
                    if s in jest:
                        continue
                    p = m.start() + 0x0E
                    oryg = od[p:p + 8].split(b"\0")[0].decode("latin1").upper()
                    if oryg and oryg != s:
                        wyn[s].append((oryg, "BAM", cw / ow2, ch / oh2))
    out = {}
    for s, lst in wyn.items():
        oryg = collections.Counter(x[0] for x in lst).most_common(1)[0][0]
        l2 = [x for x in lst if x[0] == oryg]
        out[s] = (oryg, l2[0][1], float(np.median([x[2] for x in l2])), float(np.median([x[3] for x in l2])))
    return out


def skaluj_bam(dane, kx, ky):
    ramki, nc, cykle, lut = czytaj_bam(dane)
    klatki = []
    for rgba, cx, cy in ramki:
        h, w = rgba.shape[:2]
        cel = (max(1, round(w * kx)), max(1, round(h * ky)))
        rgb, maska, _ = powieksz(rgba, *cel)
        klatki.append((rgb, maska, round(cx * kx), round(cy * ky)))
    return zapisz_bam(klatki, nc, cykle, lut)


def skaluj_mos(dane, kx, ky):
    rgb = czytaj_mos(dane)
    h, w = rgb.shape[:2]
    przez = (rgb == ZIELEN).all(2)
    src = rgb
    if przez.any() and not przez.all():
        _, (iy, ix) = ndimage.distance_transform_edt(przez, return_indices=True)
        src = rgb[iy, ix]
    cel = (round(w * kx), round(h * ky))
    out = np.asarray(Image.fromarray(np.ascontiguousarray(src)).resize(cel, Image.LANCZOS)).copy()
    if przez.any():
        m = np.asarray(Image.fromarray((przez * 255).astype(np.uint8)).resize(cel, Image.BILINEAR)) >= 128
        out[m] = ZIELEN
        # brak domieszki zieleni w kolorach nieprzezroczystych
        g = (out == ZIELEN).all(2)
        out[~g & (out[..., 1] == 255) & (out[..., 0] == 0) & (out[..., 2] == 0)] = (0, 254, 0)
        out, _ = usun_zielona_obwodke(out)
    return zapisz_mos(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gra", required=True)
    ap.add_argument("--chu", required=True, help="katalog z CHU 1920 i innymi grafikami paczki")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    gra = GameResources(a.gra, override_dirs=[])  # tylko oryginaly z BIF
    jest = {os.path.splitext(f)[0].upper() for f in os.listdir(a.chu)}
    jest |= {n for n, _ in gra.iter_resources()}
    os.makedirs(a.out, exist_ok=True)
    for s, (oryg, typ, kx, ky) in sorted(mapa(a.chu, gra, jest).items()):
        try:
            dane = gra.read(oryg, typ)
        except Exception:
            dane = None
        if not dane:
            print(f"{s}: brak oryginalu {oryg}.{typ} - pomijam")
            continue
        nowe = skaluj_bam(dane, kx, ky) if typ == "BAM" else skaluj_mos(dane, kx, ky)
        open(os.path.join(a.out, f"{s}.{typ}"), "wb").write(nowe)
        print(f"{s}.{typ} <- {oryg} x{kx:.2f}/{ky:.2f}")


if __name__ == "__main__":
    main()
