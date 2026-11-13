"""Pas portretow ekranow postaci (YGACTN10, pola 83 px) przerobiony na pola 64 px
jak w pasku swiata (ZGACTN11), plus ustawienie kontrolek w CHU.

Do YGACTN10 (1920x108) od x=1140 wstawiany jest fragment ZGACTN11 x 1100..1517
(6 pol 64 px) i panel z plecionka (ZGACTN11 x 1517..1680, zwezony), w pionie +12 px;
gora i dol dopelnione kamieniem z ZGACTN11. W CHU okna z tlem YGACTN10:
portrety 0-5 -> pozycje ze swiata +40/+12, 64x64, przycisk ZGUIRSPO; paski HP
50-55 -> 63x6, ZGUIHITP.

Uzycie:
  python tools/iwd2_pas_portretow.py --yg YGACTN10.MOS --zg ZGACTN11.MOS --chu KATALOG_CHU --out WYNIK
"""
import argparse
import glob
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from iwd2_poszerz_tla import czytaj_mos, zapisz_mos  # noqa: E402

X0, DY, PRAWY = 1140, 12, 1680
PORTRETY_X = [1107, 1175, 1244, 1313, 1381, 1450]   # GUIW10, okno 1
HP_X = [1108, 1177, 1245, 1314, 1383, 1451]
PRZESUNIECIE = X0 - 1100


def uklad(szer=1920, wys=1080, hud_l=243, y_l=240, g10=None):
    """Wspolrzedne dla innej rozdzielczosci. Stale 1920x1080 przeliczane z r = wys/1080 wzgledem lewej krawedzi
    HUD (hud_l, okna GUIW10 przed poszerzeniem) i okien ekranow (y_l). g10: poszerzony GUIW10.CHU (pozycje portretow)."""
    r = wys / 1080.0
    zx = lambda x: hud_l + round((x - 243) * r)
    yx = lambda x: y_l + round((x - 240) * r)
    u = dict(zl=zx(1100), zm=zx(1517), zr=zx(1680), sx=zx(420), x0=yx(1140), prawy=yx(1680),
             k1=round(20 * r), k2=round(50 * r), port=None, hp=None)
    if g10 is not None:
        nw, co, wo = struct.unpack_from("<III", g10, 8)
        for w in range(nw):
            if struct.unpack_from("<H", g10, wo + 28 * w)[0] != 1:
                continue
            nc, fc = struct.unpack_from("<H", g10, wo + 28 * w + 14)[0], struct.unpack_from("<H", g10, wo + 28 * w + 24)[0]
            k = {}
            for c in range(fc, fc + nc):
                off = struct.unpack_from("<I", g10, co + 8 * c)[0]
                k[struct.unpack_from("<I", g10, off)[0] & 0xFFFF] = struct.unpack_from("<HHHH", g10, off + 4)
            u["port"] = [k[i] for i in range(6)]
            u["hp"] = [k[i] for i in range(50, 56)]
    return u


def pas(yg, zg, u=None):
    u = u or dict(zl=1100, zm=1517, zr=1680, sx=420, x0=X0, prawy=PRAWY, k1=20, k2=50)
    dy = (yg.shape[0] - zg.shape[0]) // 2
    yg = yg.copy()
    w = u["prawy"] - u["x0"]
    sloty = zg[:, u["zl"]:u["zm"]]
    panel = np.asarray(Image.fromarray(np.ascontiguousarray(zg[:, u["zm"]:u["zr"]]))
                       .resize((w - sloty.shape[1], zg.shape[0]), Image.LANCZOS))
    srodek = np.concatenate([sloty, panel], 1)
    dol = yg.shape[0] - dy - zg.shape[0]
    yg[:, u["x0"]:u["prawy"]] = np.concatenate([zg[u["k1"]:u["k1"] + dy, u["sx"]:u["sx"] + w], srodek,
                                                 zg[u["k2"]:u["k2"] + dol, u["sx"]:u["sx"] + w]], 0)
    return yg


def popraw_chu(d, u=None, dy=DY):
    d = bytearray(d)
    if u is None or u.get("port") is None:
        port = [(x, 6, 64, 64) for x in PORTRETY_X]
        hp = [(x, 73, 63, 6) for x in HP_X]
        przes = PRZESUNIECIE
    else:
        port, hp, przes = u["port"], u["hp"], u["x0"] - u["zl"]
    nw, co, wo = struct.unpack_from("<III", d, 8)
    for w in range(nw):
        bg, fc = struct.unpack_from("<8sH", d, wo + w * 28 + 16)
        nc = struct.unpack_from("<H", d, wo + w * 28 + 14)[0]
        if bg.rstrip(b"\0") != b"YGACTN10":
            continue
        for c in range(fc, fc + nc):
            off = struct.unpack_from("<I", d, co + c * 8)[0]
            cid = struct.unpack_from("<I", d, off)[0] & 0xFFFF
            if cid <= 5:
                x, y, cw, ch = port[cid]
                struct.pack_into("<HHHH", d, off + 4, x + przes, y + dy, cw, ch)
                d[off + 14:off + 22] = b"ZGUIRSPO"
            elif 50 <= cid <= 55:
                x, y, cw, ch = hp[cid - 50]
                struct.pack_into("<HHHH", d, off + 4, x + przes, y + dy, cw, ch)
                d[off + 14:off + 22] = b"ZGUIHITP"
    return bytes(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yg", required=True)
    ap.add_argument("--zg", required=True)
    ap.add_argument("--chu", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    yg = czytaj_mos(open(a.yg, "rb").read())
    zg = czytaj_mos(open(a.zg, "rb").read())
    open(os.path.join(a.out, "YGACTN10.MOS"), "wb").write(zapisz_mos(pas(yg, zg)))
    for p in glob.glob(os.path.join(a.chu, "*.CHU")):
        d = open(p, "rb").read()
        n = popraw_chu(d)
        if n != d:
            open(os.path.join(a.out, os.path.basename(p)), "wb").write(n)
            print(os.path.basename(p))


if __name__ == "__main__":
    main()
