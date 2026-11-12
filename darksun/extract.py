"""Wydobycie postaci i przedmiotow z Dark Sun: Shattered Lands do CSV/JSON.

Uzycie: python -m darksun.extract --game KATALOG_GRY [--out build/darksun]
KATALOG_GRY zawiera SEGOBJEX.GFF i GPLDATA.GFF. Wyniki zawieraja teksty gry,
dlatego zapisywane sa poza Gitem (build/ jest w .gitignore).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter

from .gff import Gff
from .records import (T_CHAR, T_COMBAT, T_ITEM, Character, Combat, Item, ItemType,
                      as_row, name_table, rdff_blocks)

NO_NAME = 9999


def load(game_dir: str) -> dict:
    seg = Gff.open(os.path.join(game_dir, "SEGOBJEX.GFF"))
    gpl = Gff.open(os.path.join(game_dir, "GPLDATA.GFF"))
    names = name_table(gpl.get("NAME", 1))
    types = ItemType.table(gpl.get("IT1R", 1))

    def nm(i):
        return names[i]["name"] if 0 <= i < len(names) else ""

    creatures, items, issues = [], [], Counter()
    for rid, raw in seg.items("RDFF"):
        blocks = rdff_blocks(raw)
        combat = [b for b in blocks if b.type == T_COMBAT]
        chars = [b for b in blocks if b.type == T_CHAR]
        owner = None
        if combat:
            c = Combat.parse(combat[0].data)
            row = {"rdff_id": rid, **as_row(c)}
            if chars:
                row.update({f"ch_{k}": v for k, v in as_row(Character.parse(chars[0].data)).items()})
            else:
                issues["walka bez bloku postaci"] += 1
            creatures.append(row)
            owner = rid
        for b in blocks:
            if b.type != T_ITEM:
                continue
            it = Item.parse(b.data)
            if not 0 <= it.item_index < len(types):
                issues["item_index poza IT1R"] += 1
            items.append({"rdff_id": rid, "owner": owner, "load_action": b.load_action,
                          **as_row(it), "name": nm(it.name_idx) if it.name_idx != NO_NAME else ""})
    return {"names": names, "item_types": [as_row(t) for t in types],
            "creatures": creatures, "items": items, "issues": dict(issues)}


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
    o = ap.parse_args(argv)
    data = load(o.game)
    os.makedirs(o.out, exist_ok=True)
    for key in ("names", "item_types", "creatures", "items"):
        write_csv(os.path.join(o.out, f"{key}.csv"), data[key])
    with open(os.path.join(o.out, "darksun_data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in data.items() if isinstance(v, list)}, "problemy:", data["issues"] or "brak")


if __name__ == "__main__":
    main()
