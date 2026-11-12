"""Wyciaga z instalacji IWD2 pliki ras, podras, klas i kitow (podklas) i pakuje je do zipa.

Uzycie (z katalogu repozytorium, np. w Anaconda Prompt):
    python tools\\wyciagnij_rasy.py --game-dir "D:\\Gry\\Icewind Dale 2"
    python tools\\wyciagnij_rasy.py --game-dir "D:\\Gry\\Icewind Dale 2" --out rasy.zip --tlk

Bierze (najpierw override, potem BIF wg chitin.key):
- pliki z listy WYMAGANE (podrasy, klasy, kity, czary wrodzone, kreator postaci),
- kazdy plik 2DA/IDS, ktorego nazwa pasuje do WZORCE (rasy, podrasy, klasy, kity, kreator),
- wszystkie ekrany GUI (CHU) zaczynajace sie od GUICG (kreator postaci),
- opcjonalnie (--tlk) dialog.tlk, potrzebny do nazw i opisow ras.
W zipie jest tez SPIS.txt: skad pochodzi kazdy plik i czego nie znaleziono.
Skrypt tylko czyta instalacje; niczego w niej nie zmienia.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inventory.resource_reader import GameResources, normalize_type, type_label  # noqa: E402

WYMAGANE = [
    "SRLIST.2DA", "ABRACEAD.2DA", "ABRACERQ.2DA", "SUBRACE.IDS", "RACE.IDS", "LISTINNT.2DA",
    "GUICG.CHU", "RACETEXT.2DA", "RACETHAC.2DA", "RACECOLR.2DA",
    # klasy i kity (czesc nazw to przypuszczenia; brakujace trafia do SPIS.txt)
    "KITLIST.2DA", "KITTABLE.2DA", "KIT.IDS", "CLASS.IDS", "CLASSES.2DA", "CLASTEXT.2DA", "HELP02.2DA",
    "LISTSPLL.2DA", "LISTDOMN.2DA", "LISTKNOW.2DA", "LISTSHAP.2DA", "FEATS.2DA", "SKILLS.2DA",
    "XPLEVEL.2DA", "HPCLASS.2DA", "ALIGNMNT.2DA", "ALIGNS.2DA",
]
WZORCE = ["*RACE*", "SR*", "SPCH*", "AB*", "CLAB*", "CHARGEN*", "*SUBR*", "PORTRAIT*", "*ANIM*",
          "KIT*", "K_*", "CLAS*", "CLS*", "MXSP*", "SKILL*", "FEAT*", "LIST*", "HP*", "XP*", "BAAT*",
          "SAVE*", "ALIGN*", "HELP*", "SPL*", "DOMAIN*", "DEIT*", "SCHOOL*", "*SPEC*"]
TYPY_WZORCOW = ("2DA", "IDS")


def wybierz(gr: GameResources) -> tuple[list[tuple[str, int]], list[str]]:
    chcemy: dict[tuple[str, int], None] = {}
    brak = []
    for f in WYMAGANE:
        name, ext = f.rsplit(".", 1)
        k = (name.lower(), normalize_type(ext))
        if gr.exists(*k):
            chcemy[k] = None
        else:
            brak.append(f)
    for name, rtype in gr.iter_resources():
        label = type_label(rtype)
        if label in TYPY_WZORCOW and any(fnmatch.fnmatch(name.upper(), w) for w in WZORCE):
            chcemy[(name, rtype)] = None
        elif label == "CHU" and name.upper().startswith("GUICG"):
            chcemy[(name, rtype)] = None
    return sorted(chcemy), brak


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--game-dir", required=True, help="katalog instalacji IWD2 (z chitin.key)")
    ap.add_argument("--out", default="iwd2_rasy.zip", help="plik zip wyniku")
    ap.add_argument("--tlk", action="store_true", help="dolacz dialog.tlk (kilka MB)")
    o = ap.parse_args(argv)

    with GameResources(o.game_dir) as gr:
        zasoby, brak = wybierz(gr)
        spis = [f"Instalacja: {o.game_dir}", ""]
        with zipfile.ZipFile(o.out, "w", zipfile.ZIP_DEFLATED) as z:
            for name, rtype in zasoby:
                fn = f"{name.upper()}.{type_label(rtype)}"
                try:
                    data = gr.read(name, rtype)
                except Exception as e:  # uszkodzony lub brakujacy BIF: zapisz w spisie i jedz dalej
                    spis.append(f"BLAD   {fn}: {e}")
                    continue
                z.writestr(fn, data)
                spis.append(f"{len(data):8d} B  {fn}  <- {gr.source(name, rtype)}")
            if o.tlk:
                tlk = next((p for p in Path(o.game_dir).iterdir() if p.name.lower() == "dialog.tlk"), None)
                if tlk:
                    z.write(tlk, "dialog.tlk")
                    spis.append(f"{tlk.stat().st_size:8d} B  dialog.tlk  <- {tlk}")
                else:
                    brak.append("dialog.tlk")
            spis += ["", "Nie znaleziono: " + (", ".join(brak) if brak else "nic")]
            if gr.warnings:
                spis += ["", "Ostrzezenia czytnika:"] + gr.warnings
            z.writestr("SPIS.txt", "\n".join(spis) + "\n")
    print(f"Zapisano {o.out}: {len(zasoby)} plikow" + (f"; brak: {', '.join(brak)}" if brak else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
