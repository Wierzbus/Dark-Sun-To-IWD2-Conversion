"""Region Dark Sun -> obszar IWD2 w rzucie 45 stopni (jak AR9021), z postaciami, dialogami i skryptami.

  python tools/ds_obszar.py --game "D:/Gry/Dark Sun/dsun1" --ds build/darksun --region 0x29 --name AR9022

Kroki:
 1. darksun.obszar45: plan z RMAP/GMAP, obrot 45 stopni, mury z GMAP, obiekty ETAB jako sprite'y
    -> build/ds_obszar/AR9022/zrodlo: obraz.png, sciany.png, SR/HT/LM.BMP (palety jak AR9021)
 2. geometry.image_area -> mod/iwd2_nowe_lokacje/build/AR9022: TIS, WED, ARE, MOS, BMP, install.tph
 3. aktorzy w ARE (postacie z ETAB, polozenie przeliczone do rzutu), CRE (darksun.cre_iwd2),
    dialogi .D z tekstow rozmowy (dialogs.csv) i skrypty BAF (wrogosc po ataku, okrzyki z GPL)
 4. install.tph uzupelniony o CRE (SAY imion), kompilacje D i BAF
Wszystko w katalogach build (teksty i grafika z gry nie trafiaja do Gita).
Region 0x29 = cele niewolnikow pod arena Draj (Legcrusher, Kurzak, Scar, Merzol): pierwszy obszar gry.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from darksun import obszar45 as O  # noqa: E402
from darksun.cre_iwd2 import zbuduj  # noqa: E402
from darksun.gff import Gff  # noqa: E402
from darksun.region import Region  # noqa: E402
from geometry import image_area as IA  # noqa: E402
from geometry import maps as M  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ACTOR = 0x110
CW, CH = 16, 12


def mapy(out_img: np.ndarray, Fn: np.ndarray, dm: np.ndarray, prects, dest: str, wall_h: int = 32):
    """SR/HT/LM i sciany.png jak tools/mapy_z_rotacji.py; palety z map AR9021 (nie z BG1)."""
    H, W = Fn.shape
    tw, th = -(-W // 64), -(-H // 64)
    PW, PH = tw * 64, th * 64
    blocked = np.pad(Fn, ((0, PH - H), (0, PW - W)), constant_values=True)
    obst = np.zeros((PH, PW), bool)
    obst[:H, :W] |= dm
    for X0, Y0, bw, bh, ny in prects:
        obst[max(ny - 10, 0):ny + 1, max(X0, 0):X0 + bw] = True

    def cells(m):
        return m.reshape(PH // CH, CH, PW // CW, CW).mean(axis=(1, 3))
    SR = np.where(cells(blocked) > 0.4, 0, np.where(cells(obst) > 0.3, 8, 1)).astype(np.uint8)
    wz = os.path.join(ROOT, "areas_custom", "AR9021")
    rd = lambda k: M.read_bmp(open(os.path.join(wz, k + ".BMP"), "rb").read(), name=k)
    psr, pht, lm = rd("SR").palette, rd("HT").palette, rd("LM")
    white = lm.palette.index((255, 255, 255))
    h, w = SR.shape
    os.makedirs(dest, exist_ok=True)
    open(os.path.join(dest, "SR.BMP"), "wb").write(M.write_bmp(M.Bmp(w, h, 4, psr, bytes(SR.flatten()))))
    open(os.path.join(dest, "HT.BMP"), "wb").write(M.write_bmp(M.Bmp(w, h, 4, pht, bytes([7]) * (w * h))))
    open(os.path.join(dest, "LM.BMP"), "wb").write(M.write_bmp(M.Bmp(w, h, 8, lm.palette, bytes([white]) * (w * h))))
    Image.fromarray(out_img).save(os.path.join(dest, "obraz.png"))
    sil = np.zeros_like(blocked)
    for d in range(wall_h + 1):
        sil[:PH - d] |= blocked[d:]
    Image.fromarray((sil * 255).astype(np.uint8)).save(os.path.join(dest, "sciany.png"))
    return SR


def wolne_pole(SR: np.ndarray, x: int, y: int) -> tuple[int, int]:
    """Najblizszy przechodni punkt mapy SR (postac nie moze stac w murze)."""
    cx, cy = x // CW, y // CH
    if 0 <= cy < SR.shape[0] and 0 <= cx < SR.shape[1] and SR[cy, cx] == 1:
        return x, y
    ys, xs = np.where(SR == 1)
    i = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
    return int(xs[i] * CW + CW // 2), int(ys[i] * CH + CH // 2)


def aktor(nazwa: str, x: int, y: int, cre: str, dialog: str, skrypt: str) -> bytes:
    a = bytearray(ACTOR)
    a[0:32] = nazwa.encode("latin-1", "replace")[:31].ljust(32, b"\0")
    struct.pack_into("<HHHH", a, 0x20, x, y, x, y)
    struct.pack_into("<I", a, 0x28, 1)              # bit 0: CRE nie dolaczony (wczytaj z pliku)
    a[0x2E] = ord(cre[0])
    a[0x2F] = 0x07                                  # IWD2: bit 0 = aktor obecny na kazdym poziomie trudnosci obszaru
    struct.pack_into("<I", a, 0x38, 0xFFFFFFFF)     # bez czasu usuniecia
    struct.pack_into("<I", a, 0x40, 0x00FFFFFF)     # obecny o kazdej godzinie
    if dialog:
        a[0x48:0x50] = dialog.encode("latin-1").ljust(8, b"\0")
    if skrypt:
        a[0x50:0x58] = skrypt.encode("latin-1").ljust(8, b"\0")
    a[0x80:0x88] = cre.encode("latin-1").ljust(8, b"\0")
    return bytes(a)


def dopisz_aktorow(are: bytes, aktorzy: list[bytes]) -> bytes:
    off = len(are)
    d = bytearray(are) + b"".join(aktorzy)
    struct.pack_into("<IH", d, 0x64, off, len(aktorzy))
    return bytes(d)


def tylda(t: str) -> str:
    t = t.replace("\r", "")
    return f"~{t}~" if "~" not in t else f"%{t}%"


def dialog_d(nazwa: str, tekst: str) -> str:
    """Tekst rozmowy z GPL -> dialog WeiDU (szkic liniowy: kolejne wypowiedzi NPC, opcje gracza jako odpowiedzi).
    Skrypt GPL nie podaje w tym wydobyciu warunkow galezi, wiec kazda odpowiedz prowadzi do nastepnej wypowiedzi."""
    bloki: list[tuple[str, list[str]]] = []
    for linia in tekst.split("\n"):
        linia = linia.strip()
        if not linia:
            continue
        if linia.startswith(">"):
            if bloki:
                bloki[-1][1].append(linia[1:].strip())
        else:
            bloki.append((linia, []))
    out = [f"BEGIN ~{nazwa}~", ""]
    for i, (npc, opcje) in enumerate(bloki):
        war = "~True()~" if i == 0 else "~~"
        out.append(f"IF {war} THEN BEGIN {i}")
        out.append(f"  SAY {tylda(npc)}")
        cel = f"GOTO {i + 1}" if i + 1 < len(bloki) else "EXIT"
        if opcje:
            for o in opcje:
                koniec = re.search(r"\b(goodbye|farewell|bye|leave)\b", o, re.I)
                out.append(f"  IF ~~ THEN REPLY {tylda(o)} {'EXIT' if koniec else cel}")
        else:
            out.append(f"  IF ~~ THEN {cel}")
        out.append("END")
        out.append("")
    return "\n".join(out)


def skrypt_baf(wrogi: bool, okrzyki: list[str]) -> str:
    """Override: wrogi w Dark Sun (allegiance 2) staje sie wrogiem po ataku; okrzyk z GPL (wyzwalacz atak)."""
    out = []
    if okrzyki:
        out += ["IF", "  AttackedBy([ANYONE],DEFAULT)", "  Global(\"DS_OKRZYK\",\"LOCALS\",0)", "THEN",
                "  RESPONSE #100", "    SetGlobal(\"DS_OKRZYK\",\"LOCALS\",1)",
                f"    DisplayStringHead(Myself,%OKRZYK%)", "END", ""]
    if wrogi:
        out += ["IF", "  AttackedBy([PC],DEFAULT)", "  !Allegiance(Myself,ENEMY)", "THEN",
                "  RESPONSE #100", "    Enemy()", "END", ""]
    out += ["IF", "  Allegiance(Myself,ENEMY)", "  See(NearestEnemyOf(Myself))", "THEN",
            "  RESPONSE #100", "    AttackReevaluate(NearestEnemyOf(Myself),30)", "END", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True, help="katalog Dark Sun (dsun1)")
    ap.add_argument("--ds", required=True, help="wynik darksun.extract (creatures.csv, dialogs.csv)")
    ap.add_argument("--region", default="0x29")
    ap.add_argument("--name", default="AR9022")
    ap.add_argument("--okrzyki", action="store_true",
                    help="okrzyk w walce z tekstu wyzwalacza 'atak' (wydobycie bywa przypadkowe, domyslnie wylaczone)")
    ap.add_argument("--build", default=os.path.join(ROOT, "build", "ds_obszar"))
    ap.add_argument("--mod-build", default=os.path.join(ROOT, "mod", "iwd2_nowe_lokacje", "build"))
    a = ap.parse_args()
    nr = int(a.region, 0)
    reg = Region(a.game, nr)
    seg = Gff.open(os.path.join(a.game, "SEGOBJEX.GFF"))
    bm = dict(seg.items("BMP "))
    with open(os.path.join(a.ds, "creatures.csv"), encoding="utf-8") as f:
        postacie = {int(w["rdff_id"]): w for w in csv.DictReader(f, delimiter=";")}
    with open(os.path.join(a.ds, "dialogs.csv"), encoding="utf-8") as f:
        dialogi = list(csv.DictReader(f, delimiter=";"))
    rozmowa = {int(d["obiekt"]): d["tekst"] for d in dialogi if d["wyzwalacz"] == "rozmowa" and d["tekst"]}
    # okrzyk w walce: pierwsze zdanie tekstu wyzwalacza "atak" (wydobycie skleja kilka okrzykow w jeden tekst)
    atak = {int(d["obiekt"]): re.split(r"(?<=[.!?])\s", d["tekst"].split("\n")[0])[0]
            for d in dialogi if d["wyzwalacz"] == "atak" and d["tekst"]} if a.okrzyki else {}

    # 1. obraz
    pl = O.plan(reg)
    rz = O.Rzut(reg.obraz().width, reg.obraz().height)
    obj = O.obiekty(reg, seg)
    sprite = []
    for o in obj:
        if o.rid in postacie or o.bmp < 0:
            continue
        s = O.sprite(bm, o.bmp, reg.paleta)
        if s is not None:
            sprite.append((s, o.x + s.shape[1] / 2, o.y + s.shape[0] - 1))
    out, Fn, dm, prects = O.renderuj(pl, rz, sprite)
    zr = os.path.join(a.build, a.name, "zrodlo")
    SR = mapy(out, Fn, dm, prects, zr)

    # 2. TIS/WED/ARE
    info = IA.build_area(zr, a.name, a.mod_build)
    dest = os.path.join(a.mod_build, a.name)

    # 3. postacie
    pref = f"DS{nr:02X}"
    cre_dir = os.path.join(dest, "postacie")
    os.makedirs(cre_dir, exist_ok=True)
    aktorzy, spis, tph = [], [], []
    zrobione = set()
    for o in obj:
        w = postacie.get(o.rid)
        if not w:
            continue
        s = O.sprite(bm, o.bmp, reg.paleta) if o.bmp >= 0 else None
        sw, sh = (s.shape[1], s.shape[0]) if s is not None else (16, 32)
        x, y = rz.punkt(o.x + sw / 2, o.y + sh - 1)
        x, y = wolne_pole(SR, x, y)
        cre = f"{pref}{o.rid:04d}"[:8]
        dlg = f"DD{nr:02X}{o.rid:04d}"[:8] if o.rid in rozmowa else ""
        bcs = f"DB{nr:02X}{o.rid:04d}"[:8]
        if o.rid not in zrobione:
            zrobione.add(o.rid)
            wrogi = w["allegiance"] == "2"
            open(os.path.join(cre_dir, cre + ".CRE"), "wb").write(zbuduj(w, dialog=dlg, skrypt=bcs))
            okrzyk = atak.get(o.rid, "")
            open(os.path.join(cre_dir, bcs + ".BAF"), "w", encoding="cp1252", errors="replace").write(
                skrypt_baf(wrogi, [okrzyk] if okrzyk else []))
            if dlg:
                open(os.path.join(cre_dir, dlg + ".D"), "w", encoding="cp1252", errors="replace").write(
                    dialog_d(dlg, rozmowa[o.rid]))
            imie = w["name"].replace("\x04", "").strip()
            tph.append(f"COPY ~iwd2_nowe_lokacje/build/{a.name}/postacie/{cre}.CRE~ ~override~\n"
                       f"  SAY 0x08 {tylda(imie)}\n  SAY 0x0C {tylda(imie)}")
            if okrzyk:
                tph.append(f"OUTER_SET \"OKRZYK\" = RESOLVE_STR_REF({tylda(okrzyk)})\n"
                           f"COMPILE EVALUATE_BUFFER ~iwd2_nowe_lokacje/build/{a.name}/postacie/{bcs}.BAF~")
            else:
                tph.append(f"COMPILE ~iwd2_nowe_lokacje/build/{a.name}/postacie/{bcs}.BAF~")
            if dlg:
                tph.append(f"COMPILE ~iwd2_nowe_lokacje/build/{a.name}/postacie/{dlg}.D~")
        aktorzy.append(aktor(w["name"].replace("\x04", "").strip(), x, y, cre, dlg, ""))
        spis.append({"rdff_id": o.rid, "imie": w["name"].strip(), "ds_xy": [o.x, o.y], "are_xy": [x, y],
                     "cre": cre, "dialog": dlg, "skrypt": bcs, "allegiance": w["allegiance"], "klasy": w["klasy"]})
    are_p = os.path.join(dest, f"{a.name}.ARE")
    are = dopisz_aktorow(open(are_p, "rb").read(), aktorzy)
    open(are_p, "wb").write(are)
    with open(os.path.join(dest, "install.tph"), "a", encoding="cp1252", errors="replace") as f:
        f.write("\n// postacie Dark Sun (tools/ds_obszar.py)\n" + "\n".join(tph) + "\n")
    with open(os.path.join(a.build, a.name, "aktorzy.json"), "w", encoding="utf-8") as f:
        json.dump({"region": f"RGN{nr:02X}", "obszar": a.name, "rozmiar": [rz.W2, rz.H2], "aktorzy": spis,
                   "kafle": pl["kafle"], "info": {k: str(v) for k, v in info.items()}}, f, ensure_ascii=False, indent=1)
    print(info)
    print(f"aktorzy: {len(aktorzy)}, CRE: {len(zrobione)}, dialogi: {sum(1 for r in zrobione if r in rozmowa)}")


if __name__ == "__main__":
    main()
