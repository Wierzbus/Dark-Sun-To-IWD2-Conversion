"""Komplet GUI IWD2 dla dowolnej rozdzielczosci W x H (paczka 1 "upscale").

  python tools/iwd2_gui/buduj.py --gra "D:/Gry/Icewind Dale 2" --szer 2560 --wys 1440 \
      --ttf Classica-Bold.ttf --out WYNIK

Skale: ekrany (Y*) H/600, pasek gry GUIW10 (Z*) 1,4*H/1080, ikony 48*H/1080. Dla 1920x1080 wynik odpowiada
paczce 1 przetestowanej w grze 2026-11-13. Czyta tylko pliki gry z BIF (bez Override); IWD2.exe nie jest zmieniany.

Wynik:
  WYNIK/IWD2_<W>.exe           kopia exe z latkami (do testow bez instalatora)
  WYNIK/upscale_exe.tpa        te same latki jako makra WeiDU (ds_upscale_sprawdz / ds_upscale_zapisz)
  WYNIK/override/gui|ikony|portrety
Widok swiata wiekszy niz monitor: zbuduj dla wiekszej rozdzielczosci (np. 2560x1440 na monitorze 1920x1080)
i pozwol DDrawCompat zmniejszyc obraz - GUI ma wtedy na ekranie ten sam rozmiar, a swiata widac wiecej.
"""
from __future__ import annotations

import argparse
import os
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

TU = Path(__file__).resolve().parent
NARZ = TU.parent
sys.path.insert(0, str(TU))
sys.path.insert(0, str(NARZ))
sys.path.insert(0, str(NARZ.parent))

from hires_patch import patch_exe, _pole_portretu  # noqa: E402
from guiscale.hudscale import build as build_hud  # noqa: E402
from guiscale.screens import build_screens  # noqa: E402
from guiscale.exe_skala import zastosuj  # noqa: E402
from inventory.resource_reader import GameResources  # noqa: E402
import iwd2_napraw_gui  # noqa: E402
import iwd2_pas_portretow  # noqa: E402
import iwd2_gui_brakujace  # noqa: E402
import iwd2_ekran_ladowania  # noqa: E402
import iwd2_ikony  # noqa: E402
import iwd2_portrety  # noqa: E402
from iwd2_czcionka_ttf import generuj as czcionka  # noqa: E402
from iwd2_poszerz_tla import czytaj_mos, zapisz_mos  # noqa: E402
from iwd2_paczki_exe import przebiegi, tpa  # noqa: E402

# czcionki z TTF: (wysokosc ramki, wersalik) dla 1080; dla innych wysokosci x H/1080
CZCIONKI = {"NORMAL": (18, 11), "ZNORMAL": (18, 11), "YNORMAL": (22, 14), "TOOLFONT": (16, 10), "YTOOLFON": (21, 13),
            "INFOFONT": (16, 10), "NUMFONT": (16, 10), "REALMS": (23, 15), "REALMS2": (23, 15), "YREALMS": (26, 17),
            "STONEBIG": (23, 15), "YSTONEBI": (41, 27), "STONESML": (16, 10), "STONESM2": (16, 10), "STONESM3": (16, 10)}
# pasy po bokach paska gry: szerokosc skrajnego panelu (lewy, prawy) w 1080, rozciagana na czarne pasy
PASY = {"ZGACTN11": (155, 155), "ZGCOMM11": (155, 140), "ZGCOMM12": (155, 140), "ZGMWDMMB": (159, 159),
        "ZGMWDSLB": (159, 159), "ZGUCONTB": (155, 155), "ZGUDEATH": (155, 155), "ZGUWBTP3": (159, 159)}
# z generatora nie trafiaja do paczki (menu 640x480, ramka STON10, portrety robi iwd2_portrety)
POMIN_CHU = {"GUIBASE", "GUIMG", "GUIPR", "GUITEST", "START"}
# do katalogu gui z wyniku narzedzia ikon (elementy GUI, nie ikony przedmiotow)
IKONY_DO_GUI = {"COLGRAD", "GUIBTBUT", "STORTINT", "STORTIN2", "STORTIN3", "STORTIN4"}


def okna(d):
    nw, co, wo = struct.unpack_from("<III", d, 8)
    for i in range(nw):
        o = wo + 28 * i
        wid, _, x, y, w, h = struct.unpack_from("<HHHHHH", d, o)
        nc, fc = struct.unpack_from("<H", d, o + 14)[0], struct.unpack_from("<H", d, o + 24)[0]
        k = [struct.unpack_from("<I", d, co + 8 * c)[0] for c in range(fc, fc + nc)]
        yield wid, x, w, d[o + 16:o + 24].rstrip(b"\0").decode("latin1"), k


def x_okna(d, wid):
    return next(x for i, x, _, _, _ in okna(d) if i == wid)


def suwaki(d, s):
    """Suwaki (typ 2) z oryginalna grafika GUISLDR: grafika Y*, pozycje galki, skok i obszar x s."""
    d = bytearray(d)
    nazwy = set()
    for _, _, _, _, k in okna(bytes(d)):
        for off in k:
            if d[off + 12] != 2:
                continue
            for p in (0x0E, 0x16):
                n = bytes(d[off + p:off + p + 8]).rstrip(b"\0").decode("latin1").upper()
                if n and n[0] not in "YZ":
                    nowa = ("Y" + n if len(n) < 8 else "Y" + n[1:])[:8]
                    d[off + p:off + p + 8] = nowa.encode().ljust(8, b"\0")
                    nazwy.add((n, nowa, p == 0x0E))
            for p in (0x24, 0x26, 0x28, 0x2C, 0x2E, 0x30, 0x32):
                v = struct.unpack_from("<H", d, off + p)[0]
                struct.pack_into("<H", d, off + p, round(v * s))
    return bytes(d), nazwy


def kontrolka(d, wid, cid, typ=None):
    for i, _, _, _, k in okna(d):
        if i != wid:
            continue
        for off in k:
            if struct.unpack_from("<I", d, off)[0] & 0xFFFF == cid and (typ is None or d[off + 12] == typ):
                return off
    raise SystemExit(f"STOP: brak kontrolki {cid} w oknie {wid}.")


def pasy_boczne(rgb, hud_l, hud_r, el, er):
    out = rgb.copy()
    h = rgb.shape[0]
    if hud_l > 0:
        out[:, :hud_l] = np.asarray(Image.fromarray(np.ascontiguousarray(rgb[:, hud_l:hud_l + el])).resize((hud_l, h), Image.LANCZOS))
    if hud_r < rgb.shape[1]:
        out[:, hud_r:] = np.asarray(Image.fromarray(np.ascontiguousarray(rgb[:, hud_r - er:hud_r]))
                                    .resize((rgb.shape[1] - hud_r, h), Image.LANCZOS))
    return out


def min_etykiety(gui: Path) -> dict:
    """Najnizsza etykieta (typ 6) dla kazdej czcionki we wszystkich CHU."""
    m = {}
    for f in gui.glob("*.CHU"):
        d = f.read_bytes()
        for _, _, _, _, k in okna(d):
            for off in k:
                if d[off + 12] == 6:
                    n = d[off + 0x12:off + 0x1A].rstrip(b"\0").decode("latin1").upper()
                    h = struct.unpack_from("<H", d, off + 10)[0]
                    m[n] = min(m.get(n, 9999), h)
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gra", required=True)
    ap.add_argument("--szer", type=int, required=True)
    ap.add_argument("--wys", type=int, required=True)
    ap.add_argument("--ttf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    W, H = a.szer, a.wys
    if W < 1024 or H < 768 or W < H:
        raise SystemExit("Minimum 1024x768, ekran poziomy.")
    r, S, Z = H / 1080.0, H / 600.0, 1.4 * H / 1080.0
    gra = Path(a.gra)
    out = Path(a.out)
    gui, ikony, portrety = out / "override" / "gui", out / "override" / "ikony", out / "override" / "portrety"
    for p in (gui, ikony, portrety):
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True)
    g = GameResources(str(gra), override_dirs=[])
    orig = (gra / "IWD2.exe").read_bytes()
    tmp = Path(tempfile.mkdtemp(prefix="iwd2gui_"))
    gen, nap = tmp / "gen", tmp / "nap"
    gen.mkdir()

    print(f"== {W}x{H}: ekrany x{S:.3f}, pasek gry x{Z:.3f}")
    exe = out / f"IWD2_{W}.exe"
    patch_exe(gra / "IWD2.exe", exe, W, H, "stock", Z)
    build_hud(g, W, H, Z, a.ttf, gen)
    build_screens(g, W, H, S, a.ttf, gen)
    for f in gen.iterdir():
        if f.suffix.upper() == ".BMP" or f.stem.upper() in POMIN_CHU:
            f.unlink()
    g10_gen = (gen / "GUIW10.CHU").read_bytes()
    hud_l, hud_w = next((x, w) for i, x, w, _, _ in okna(g10_gen) if i == 1)
    y_l = x_okna((gen / "GUIINV.CHU").read_bytes(), 1)

    # exe
    d = bytearray(exe.read_bytes())
    pole = _pole_portretu(g10_gen)
    zastosuj(d, orig, W, H, pole)
    exe.write_bytes(bytes(d))
    runs = przebiegi(orig, bytes(d))
    (out / "upscale_exe.tpa").write_text(tpa("ds_upscale", orig, bytes(d), runs,
                                             f"Paczka 1: IWD2.exe GOG 2.01 -> {W}x{H} (GUI, ekran ladowania, portrety, ikony)"))
    print(f"exe: {len(runs)} miejsc, pole portretu {pole}")

    # okna na cala szerokosc, tla pol tekstowych, zielone obwodki
    iwd2_napraw_gui.napraw(str(gen), str(nap), W)
    for f in gen.iterdir():
        shutil.copy2(f, gui / f.name)
    for f in nap.iterdir():
        shutil.copy2(f, gui / f.name)

    # pas portretow ekranow postaci
    u = iwd2_pas_portretow.uklad(W, H, hud_l, y_l, (gui / "GUIW10.CHU").read_bytes())
    yg, zg = czytaj_mos((gui / "YGACTN10.MOS").read_bytes()), czytaj_mos((gui / "ZGACTN11.MOS").read_bytes())
    dy = (yg.shape[0] - zg.shape[0]) // 2
    (gui / "YGACTN10.MOS").write_bytes(zapisz_mos(iwd2_pas_portretow.pas(yg, zg, u)))
    for f in gui.glob("*.CHU"):
        f.write_bytes(iwd2_pas_portretow.popraw_chu(f.read_bytes(), u, dy))

    # suwaki
    nowe_sl = set()
    for f in gui.glob("*.CHU"):
        if f.stem.upper() == "GUIW10":
            continue
        nd, nz = suwaki(f.read_bytes(), S)
        if nz:
            f.write_bytes(nd)
            nowe_sl |= nz
    for stara, nowa, jest_mos in sorted(nowe_sl):
        typ = "MOS" if jest_mos else "BAM"
        dane = g.read(stara, typ)
        nowe = iwd2_gui_brakujace.skaluj_mos(dane, S, S) if jest_mos else iwd2_gui_brakujace.skaluj_bam(dane, S, S)
        (gui / f"{nowa}.{typ}").write_bytes(nowe)
        print(f"suwak {nowa}.{typ} <- {stara}")

    # Continue (okno 9 GUIW10) do gory, waga w ekwipunku (GUIINV okno 2, etykieta 66) o 3 px wyzej
    p = gui / "GUIW10.CHU"
    d = bytearray(p.read_bytes())
    off = kontrolka(bytes(d), 9, 0)
    y, h = struct.unpack_from("<HH", d, off + 6)[0], struct.unpack_from("<H", d, off + 10)[0]
    struct.pack_into("<H", d, off + 6, 0)
    struct.pack_into("<H", d, off + 10, h - y)
    p.write_bytes(bytes(d))
    p = gui / "GUIINV.CHU"
    d = bytearray(p.read_bytes())
    off = kontrolka(bytes(d), 2, 66, 6)
    struct.pack_into("<H", d, off + 6, struct.unpack_from("<H", d, off + 6)[0] - round(3 * r))
    p.write_bytes(bytes(d))

    # pasy po bokach paska gry
    hud_r = hud_l + hud_w
    for n, (el, er) in PASY.items():
        p = gui / f"{n}.MOS"
        rgb = czytaj_mos(p.read_bytes())
        if rgb.shape[1] == W:
            p.write_bytes(zapisz_mos(pasy_boczne(rgb, hud_l, hud_r, round(el * r), round(er * r))))

    # brakujace kopie Y*/Z*
    jest = {f.stem.upper() for f in gui.iterdir()} | {n for n, _ in g.iter_resources()}
    for s, (oryg, typ, kx, ky) in sorted(iwd2_gui_brakujace.mapa(str(gui), g, jest).items()):
        try:
            dane = g.read(oryg, typ)
        except Exception:
            dane = None
        if not dane:
            print(f"brak oryginalu {oryg}.{typ} dla {s} - pomijam")
            continue
        nowe = iwd2_gui_brakujace.skaluj_bam(dane, kx, ky) if typ == "BAM" else iwd2_gui_brakujace.skaluj_mos(dane, kx, ky)
        (gui / f"{s}.{typ}").write_bytes(nowe)

    # czcionki z TTF (ramka nie wyzsza niz najnizsza etykieta - 3 px), YSTATES2 = oryginalna STATES2
    lim = min_etykiety(gui)
    for n, (hh, vv) in CZCIONKI.items():
        wys, wer = round(hh * r), round(vv * r)
        if n in lim and wys > lim[n] - 3:
            print(f"czcionka {n}: {wys} -> {lim[n] - 3} (etykieta {lim[n]})")
            wer = round(wer * (lim[n] - 3) / wys)
            wys = lim[n] - 3
        (gui / f"{n}.BAM").write_bytes(czcionka(a.ttf, wys, wer))
    (gui / "YSTATES2.BAM").write_bytes(g.read("STATES2", "BAM"))

    # ekran ladowania, ikony, portrety
    iwd2_ekran_ladowania.buduj(g, str(gui), W, H)
    iwd2_ikony.buduj(g, str(ikony), H, dodatkowe=("COLGRAD",))
    for n in IKONY_DO_GUI:
        if (ikony / f"{n}.BAM").exists():
            shutil.move(str(ikony / f"{n}.BAM"), str(gui / f"{n}.BAM"))
    iwd2_portrety.buduj(g, str(portrety), (pole - 4, pole - 4), (round(210 * S), round(330 * S)))

    shutil.rmtree(tmp)
    print(f"\nGotowe: {exe.name}, upscale_exe.tpa, override: gui {len(list(gui.iterdir()))}, "
          f"ikony {len(list(ikony.iterdir()))}, portrety {len(list(portrety.iterdir()))}")
    print(f"W icewind2.ini: Resolution={W}")


if __name__ == "__main__":
    main()
