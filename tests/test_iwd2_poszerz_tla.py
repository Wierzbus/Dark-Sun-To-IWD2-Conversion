import struct

import numpy as np

from tools.iwd2_poszerz_tla import czytaj_mos, poszerz_chu, poszerz_rgb, zapisz_mos


def test_mos_roundtrip_i_poszerzenie():
    rng = np.random.default_rng(1)
    rgb = rng.integers(0, 256, (70, 1440, 3), dtype=np.uint8)
    rgb[:, :, :] //= 64  # malo kolorow -> bez kwantyzacji
    wynik = czytaj_mos(zapisz_mos(poszerz_rgb(rgb)))
    assert wynik.shape == (70, 1920, 3)
    assert (wynik[:, 240:1680] == rgb).all()
    assert wynik[:, :240].max() == 0 and wynik[:, 1680:].max() == 0


def _chu(okna):
    owin = 20
    octl = owin + 28 * len(okna)
    kontrolki, okna_b, nr = [], b"", 0
    for x, w, h, xs in okna:
        okna_b += struct.pack("<HHHHHHHH8sHH", 0, 0, x, 0, w, h, 1, len(xs), b"TLO", nr, 0)
        kontrolki += xs
        nr += len(xs)
    cdane = octl + 8 * len(kontrolki)
    tab, ciala = b"", b""
    for i, cx in enumerate(kontrolki):
        tab += struct.pack("<II", cdane + 14 * i, 14)
        ciala += struct.pack("<IHHHHBB", i, cx, 0, 10, 10, 0, 0)
    return struct.pack("<8sIII", b"CHUIV1  ", len(okna), octl, owin) + okna_b + tab + ciala


def test_chu_poszerza_tylko_pelnoekranowe():
    dane, tla = poszerz_chu(_chu([(240, 1440, 1080, [10, 20]), (240, 1440, 779, [5])]))
    assert tla == ["TLO"]
    assert struct.unpack_from("<HHH", dane, 20 + 4)[::2] == (0, 1920)
    assert struct.unpack_from("<HHH", dane, 48 + 4)[::2] == (240, 1440)
    octl = 20 + 56
    xs = [struct.unpack_from("<H", dane, struct.unpack_from("<I", dane, octl + 8 * i)[0] + 4)[0] for i in range(3)]
    assert xs == [250, 260, 5]


def test_zielona_obwodka_i_zachowanie_zieleni():
    from tools.iwd2_poszerz_tla import ZIELEN, usun_zielona_obwodke
    rng = np.random.default_rng(2)
    rgb = rng.integers(0, 120, (64, 64, 3), dtype=np.uint8)  # >256 kolorow, bez zielonego nadmiaru
    rgb[..., 1] = rgb[..., [0, 2]].min(2)
    rgb[:, :20] = ZIELEN
    rgb[:, 20] = (60, 200, 60)  # rozmyta krawedz
    out, n = usun_zielona_obwodke(rgb)
    assert n == 64 and (out[:, :21] == ZIELEN).all() and (out[:, 22:] == rgb[:, 22:]).all()
    wynik = czytaj_mos(zapisz_mos(out))
    assert ((wynik == ZIELEN).all(2) == (out == ZIELEN).all(2)).all()


def test_czcionka_bez_jasnej_obwodki():
    from tools.iwd2_czcionka_obwodka import czytaj_bam, usun_obwodke
    pal = np.zeros((256, 4), np.uint8)
    pal[0] = (0, 255, 0, 0)
    pal[1] = (250, 250, 250, 0)
    pal[2] = (10, 10, 10, 0)
    ramka = np.array([[0, 1, 2, 2, 1, 0]], np.uint8)
    nag = struct.pack("<8sHBBIII", b"BAM V1  ", 1, 1, 0, 24, 40, 1064)
    fr = struct.pack("<HHhhI", 6, 1, 0, 0, 1066 | 0x80000000) + struct.pack("<HH", 1, 0)
    dane = nag + fr + pal.tobytes() + struct.pack("<H", 0) + ramka.tobytes()
    nowe, n = usun_obwodke(dane)
    assert n == 2
    assert czytaj_bam(nowe)[5][0].tolist() == [[0, 0, 2, 2, 0, 0]]


def test_zielen_na_pozycji_zero_palety():
    from tools.iwd2_poszerz_tla import ZIELEN, kafel_do_palety
    for n in (10, 400):
        rng = np.random.default_rng(n)
        t = rng.integers(0, 120, (64, 64, 3), dtype=np.uint8)
        if n == 10:
            t //= 40
        t[5:9, 5:9] = ZIELEN
        pal, idx = kafel_do_palety(t)
        assert tuple(pal[0, :3]) == (0, 255, 0)
        odt = pal[idx][..., 2::-1]
        assert ((odt == ZIELEN).all(2) == (t == ZIELEN).all(2)).all()
        if n == 10:
            assert (odt == t).all()
