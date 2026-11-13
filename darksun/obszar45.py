"""Region Dark Sun -> obraz obszaru w rzucie ukosnym 45 stopni (jak AR9021).

Rzut i rysowanie scian jak w tools/rotuj_plan.py (AR9021): plan traktowany jako widok
ze skroceniem K = 0.75, obrot o THETA wokol srodka, ponowne skrocenie K, sciany wyciagane
w gore o HW pikseli (gorna powierzchnia = cegla, pas od dolu = lico muru), gleboko w murze czern.
Roznica: sciany i przeszkody nie sa zgadywane z kolorow zrzutu, tylko brane z danych regionu:
  GMAP bit 0x80 - mur, bit 0x40 - pole nieprzechodnie (mur, woda, przeszkody),
  RMAP - kafelki: podloga (najczestszy kafel przechodni), cegla (gora muru), lico (dolny wiersz muru).
Obiekty z ETAB (OJFF + BMP z SEGOBJEX) sa wklejane jako sprite'y w punkcie stopy (srodek dolu)
po przeliczeniu do rzutu; postacie (RDFF z blokiem walki) zostaja na liste aktorow ARE.
"""
from __future__ import annotations

import struct
from collections import Counter
from dataclasses import dataclass

import cv2
import numpy as np

from .bmp import decode_frames, frame_to_image
from .gff import Gff
from .region import KAFEL, SZER, WYS, Region

K, HW, DEPTH = 0.75, 32, 40


class Rzut:
    """Przeliczenie wspolrzednych planu (piksele regionu) na obraz w rzucie 45 stopni."""

    def __init__(self, W: int, H: int, theta: float = 45.0):
        self.W, self.H = W, H
        th = np.deg2rad(theta)
        self.c, self.s = float(np.cos(th)), float(np.sin(th))
        self.cx, self.cy = W / 2, H / (2 * K)
        hw, hh = W / 2, H / (2 * K)
        ext_x = abs(hw * self.c) + abs(hh * self.s)
        ext_y = abs(hw * self.s) + abs(hh * self.c)
        self.W2 = int(2 * ext_x) + 40
        self.H2 = int(2 * ext_y * K) + 40 + HW
        self.cx2, self.cy2 = self.W2 / 2, (self.H2 + HW) / 2

    def punkt(self, x: float, y: float) -> tuple[int, int]:
        qx, qy = x - self.cx, y / K - self.cy
        nx = self.c * qx - self.s * qy + self.cx2
        ny = K * (self.s * qx + self.c * qy) + self.cy2
        return int(round(nx)), int(round(ny))

    def mapy(self):
        """Dla kazdego piksela wyniku: wspolrzedne planu (ox, oy) i (Px, Py) w ukladzie bez skrocenia."""
        yy, xx = np.mgrid[0:self.H2, 0:self.W2].astype(np.float32)
        px = xx - self.cx2
        py = (yy - self.cy2) / K
        Px = self.c * px + self.s * py + self.cx
        Py = -self.s * px + self.c * py + self.cy
        return Px.astype(np.float32), (Py * K).astype(np.float32), Px, Py


@dataclass
class Obiekt:
    rid: int        # id rekordu (OJFF/RDFF), dodatni
    x: int          # lewy gorny rog sprite'a na planie
    y: int
    z: int
    flagi: int
    bmp: int        # id grafiki BMP (SEGOBJEX) albo -1


def obiekty(region: Region, seg: Gff) -> list[Obiekt]:
    oj = {k: struct.unpack("<8h", d) for k, d in seg.items("OJFF")}
    out = []
    e = region.etab
    for i in range(0, len(e) - 7, 8):
        x, y, z, f, idx = struct.unpack_from("<HHBBh", e, i)
        o = oj.get(-idx)
        out.append(Obiekt(-idx, x, y, z, f, o[6] if o else -1))
    return out


def plan(region: Region):
    """Maski i tekstury planu z danych regionu (piksele 2048 x 1568)."""
    T = np.frombuffer(region.rmap[:SZER * WYS], np.uint8).reshape(WYS, SZER)
    G = np.frombuffer(region.gmap[:SZER * WYS], np.uint8).reshape(WYS, SZER)
    mur = (G & 0x80) > 0
    blok = (G & 0x40) > 0
    pod = np.zeros_like(mur)
    pod[:-1] = mur[1:]
    # slad muru: bez dolnego wiersza (to lico narysowane w rzucie Dark Sun), pojedyncze wiersze zostaja
    nad = np.zeros_like(mur)
    nad[1:] = mur[:-1]
    slad = mur & (pod | ~nad)
    podloga_kafel = Counter(T[~blok].tolist()).most_common(1)[0][0]
    cegla_kafel = Counter(T[mur & pod].tolist()).most_common(1)[0][0]
    lico_kafle = [k for k, _ in Counter(T[mur & ~pod].tolist()).most_common(4)]
    cien_kafel = Counter(T[~blok & nad].tolist()).most_common(1)[0][0]

    def kafel(tid):
        return np.asarray(frame_to_image(region.kafle[tid], region.paleta).convert("RGB"))

    obraz = np.asarray(region.obraz())
    # zdobienia podlogi (basen, plyty): pola nie-murowe z kaflem innym niz podloga i jej cien
    zdob = ~mur & ~np.isin(T, [podloga_kafel, cien_kafel])
    up = lambda m: np.kron(m.astype(np.uint8), np.ones((KAFEL, KAFEL), np.uint8)).astype(bool)
    return {
        "obraz": obraz, "slad": up(slad), "blok": up(blok & ~mur), "zdob": up(zdob),
        "PODLOGA": kafel(podloga_kafel), "CEGLA": kafel(cegla_kafel),
        "LICO": np.concatenate([kafel(k) for k in lico_kafle], 1),
        "kafle": {"podloga": podloga_kafel, "cegla": cegla_kafel, "lico": lico_kafle, "cien": cien_kafel},
    }


def renderuj(pl: dict, rz: Rzut, sprite_y: list[tuple[np.ndarray, int, int]]):
    """sprite_y: (RGBA, x punktu stopy na planie, y punktu stopy). Zwraca obraz, Fn (mur), dm (przeszkody), prostokaty sprite'ow."""
    W2, H2 = rz.W2, rz.H2
    ox, oy, Px, Py = rz.mapy()
    H, W = pl["slad"].shape
    inrect = (ox >= 0) & (ox < W - 1) & (oy >= 0) & (oy < H - 1)

    def samp(a):
        return cv2.remap(a.astype(np.float32), ox, oy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) > 0.5

    Fn = samp(pl["slad"])
    Fn = cv2.medianBlur((Fn * 255).astype(np.uint8), 5) > 127
    Fn |= ~inrect
    dm = samp(pl["blok"]) & ~Fn
    zd = samp(pl["zdob"]) & ~Fn
    P = pl["PODLOGA"]
    ground = P[Py.astype(int) % P.shape[0], Px.astype(int) % P.shape[1]].copy()
    rgb = cv2.remap(pl["obraz"], ox, oy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    ground[zd] = rgb[zd]
    # cien muru (jak AR9021)
    sh = np.zeros_like(Fn)
    for t in np.linspace(0, 1, 12):
        M = np.float32([[1, 0, int(22 * t)], [0, 1, int(24 * t)]])
        sh |= cv2.warpAffine(Fn.astype(np.uint8), M, (W2, H2)) > 0
    sh &= ~Fn
    g = ground.astype(np.float32)
    g[sh] *= np.array([0.80, 0.64, 0.68], np.float32)
    ground = g.clip(0, 255).astype(np.uint8)
    # mury kolumnami: gora = cegla (do glebokosci DEPTH, dalej czern), dolne HW wierszy = lico
    B = pl["CEGLA"]
    brickg = B[Py.astype(int) % B.shape[0], Px.astype(int) % B.shape[1]].copy()
    dist = cv2.distanceTransform(Fn.astype(np.uint8), cv2.DIST_L2, 5)
    brickg[dist > DEPTH] = 0
    FACE = np.repeat(np.repeat(pl["LICO"], 2, 0), 2, 1)  # lico 16 px -> HW 32 px
    fh, fw = FACE.shape[:2]
    wall = np.zeros((H2, W2, 3), np.uint8)
    key = np.full((H2, W2), -1, np.int32)
    has = np.zeros((H2, W2), bool)
    for x in range(W2):
        d = np.diff(np.concatenate([[0], Fn[:, x].astype(np.int8), [0]]))
        st, en = np.where(d == 1)[0], np.where(d == -1)[0] - 1
        for a_, e_ in zip(st, en):
            t0, t1 = max(a_ - HW, 0), e_ - HW
            if t1 >= t0:
                ys = np.arange(t0, t1 + 1)
                wall[ys, x] = brickg[ys + HW, x]
                key[ys, x] = np.maximum(key[ys, x], e_)
                has[ys, x] = True
            if e_ >= H2 - 1:
                continue
            ys = np.arange(max(e_ - HW + 1, 0), e_ + 1)
            v = np.clip(ys - (e_ - HW + 1), 0, fh - 1)
            wall[ys, x] = FACE[v, x % fw]
            key[ys, x] = np.maximum(key[ys, x], e_)
            has[ys, x] = True
    spr = np.zeros((H2, W2, 3), np.uint8)
    sa = np.zeros((H2, W2), bool)
    sk = np.full((H2, W2), -1, np.int32)
    prects = []
    for rgba, gx, gy in sorted(sprite_y, key=lambda t: t[2]):
        nx, ny = rz.punkt(gx, gy)
        bh, bw = rgba.shape[:2]
        X0, Y0 = nx - bw // 2, ny - bh + 1
        if X0 < 0 or Y0 < 0 or X0 + bw > W2 or Y0 + bh > H2 or Fn[min(ny, H2 - 1), nx]:
            continue
        mm = rgba[..., 3] > 0
        reg = spr[Y0:Y0 + bh, X0:X0 + bw]
        reg[mm] = rgba[..., :3][mm]
        sa[Y0:Y0 + bh, X0:X0 + bw] |= mm
        k2 = sk[Y0:Y0 + bh, X0:X0 + bw]
        k2[mm] = ny
        prects.append((X0, Y0, bw, bh, ny))
    out = ground.copy()
    w_ = has & ~(sa & (sk > key))
    out[w_] = wall[w_]
    s_only = sa & ~(has & (key >= sk))
    out[s_only] = spr[s_only]
    out[Fn & ~has] = 0  # pas przy dolnej krawedzi kadru (gora muru przesunieta o HW) - czern jak poza murami
    return out, Fn, dm, prects


def sprite(seg_bmp: dict, bmp_id: int, paleta) -> np.ndarray | None:
    d = seg_bmp.get(bmp_id)
    if d is None:
        return None
    fr = decode_frames(d)[0]
    return np.asarray(frame_to_image(fr, paleta).convert("RGBA"))
