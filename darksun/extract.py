"""Wydobycie postaci i przedmiotow z Dark Sun: Shattered Lands do CSV/JSON oraz ikon do PNG.

Uzycie: python -m darksun.extract --game KATALOG_GRY [--out build/darksun] [--no-icons]
KATALOG_GRY zawiera SEGOBJEX.GFF, GPLDATA.GFF i RESOURCE.GFF. Wyniki zawieraja teksty
i grafiki gry, dlatego zapisywane sa poza Gitem (build/ jest w .gitignore).

items.csv: kazdy przedmiot z RDFF, a w kolejnych kolumnach (prefiks it_) dane typu z IT1R
wg item_index; bmp_id i icon_file to grafika z rekordu obiektu OJFF o id = |id przedmiotu|.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import struct
from collections import Counter

from .bmp import decode_frames, frame_to_image, palette
from .codes import GENDERS, class_names, race_name
from .gff import Gff
from .records import (T_CHAR, T_COMBAT, T_ITEM, Character, Combat, Item, ItemType,
                      as_row, name_table, rdff_blocks)

NO_NAME = 9999
ICON_PALETTE = ("RESOURCE.GFF", "PAL ", 1000)  # sprawdzone wizualnie na ikonach broni i pancerzy
OJFF_BMP = 6  # indeks pola (i16) z id grafiki BMP w 16-bajtowym rekordzie OJFF


def load(game_dir: str) -> dict:
    seg = Gff.open(os.path.join(game_dir, "SEGOBJEX.GFF"))
    gpl = Gff.open(os.path.join(game_dir, "GPLDATA.GFF"))
    names = name_table(gpl.get("NAME", 1))
    types = ItemType.table(gpl.get("IT1R", 1))
    type_rows = [as_row(t) for t in types]
    ojff = {rid: struct.unpack("<8h", b) for rid, b in seg.items("OJFF") if len(b) == 16}
    bmp_ids = {e.id for e in seg.entries("BMP")}

    def nm(i):
        return names[i]["name"] if 0 <= i < len(names) and i != NO_NAME else ""

    creatures, items, issues = [], [], Counter()
    for rid, raw in seg.items("RDFF"):
        blocks = rdff_blocks(raw)
        combat = [b for b in blocks if b.type == T_COMBAT]
        chars = [b for b in blocks if b.type == T_CHAR]
        owner = None
        if combat:
            c = Combat.parse(combat[0].data)
            row = {"rdff_id": rid, "name": c.name}
            if chars:
                h = Character.parse(chars[0].data)
                row.update({"rasa": race_name(h.race), "plec": GENDERS.get(h.gender, h.gender),
                            "klasy": class_names(h.real_class, h.level)})
            else:
                issues["walka bez bloku postaci"] += 1
            row.update(as_row(c))
            if chars:
                row.update({f"ch_{k}": v for k, v in as_row(h).items()})
            creatures.append(row)
            owner = rid
        for b in blocks:
            if b.type != T_ITEM:
                continue
            it = Item.parse(b.data)
            obj = ojff.get(abs(it.id))
            bmp = obj[OJFF_BMP] if obj and obj[OJFF_BMP] in bmp_ids else None
            if bmp is None:
                issues["przedmiot bez grafiki"] += 1
            row = {"rdff_id": rid, "owner": owner, "owner_name": creatures[-1]["name"] if owner else "",
                   "load_action": b.load_action, "name": nm(it.name_idx), **as_row(it),
                   "bmp_id": bmp, "icon_file": f"icons/BMP_{bmp:04d}.png" if bmp is not None else ""}
            if 0 <= it.item_index < len(types):
                row.update({f"it_{k}": v for k, v in type_rows[it.item_index].items() if k != "index"})
            else:
                issues["item_index poza IT1R"] += 1
            items.append(row)
    return {"names": names, "item_types": type_rows, "creatures": creatures, "items": items,
            "issues": dict(issues)}


def export_icons(game_dir: str, out_dir: str, bmp_ids) -> int:
    seg = Gff.open(os.path.join(game_dir, "SEGOBJEX.GFF"))
    f, tag, pid = ICON_PALETTE
    pal = palette(Gff.open(os.path.join(game_dir, f)).get(tag, pid))
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for bid in sorted(set(bmp_ids)):
        frames = decode_frames(seg.get("BMP", bid))
        frame_to_image(frames[0], pal).save(os.path.join(out_dir, f"BMP_{bid:04d}.png"))
        for k, fr in enumerate(frames[1:], start=1):
            frame_to_image(fr, pal).save(os.path.join(out_dir, f"BMP_{bid:04d}_{k}.png"))
        n += 1
    return n


def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, list) else v) for k, v in r.items()})


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--out", default="build/darksun")
    ap.add_argument("--no-icons", action="store_true")
    o = ap.parse_args(argv)
    data = load(o.game)
    os.makedirs(o.out, exist_ok=True)
    for key in ("names", "item_types", "creatures", "items"):
        write_csv(os.path.join(o.out, f"{key}.csv"), data[key])
    with open(os.path.join(o.out, "darksun_data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    msg = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    if not o.no_icons:
        msg["ikony"] = export_icons(o.game, os.path.join(o.out, "icons"),
                                    [i["bmp_id"] for i in data["items"] if i["bmp_id"] is not None])
    print(msg, "problemy:", data["issues"] or "brak")


if __name__ == "__main__":
    main()
