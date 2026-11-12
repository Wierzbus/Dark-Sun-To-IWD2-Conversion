"""Powiazanie tekstow skryptow z obiektami (postaciami, przedmiotami) przez wyzwalacze GPL.

Wyzwalacz rozmowy/ogledzin/uzycia/podniesienia/ataku/braku rozkazow ma parametry
(adres, numer_skryptu, obiekt); `uzycie z` ma (obiekt1, obiekt2, adres, numer_skryptu).
Obiekt to -id (id = numer rekordu RDFF/OJFF). Od adresu obsługi zbieramy teksty
osiagalne w obrebie skryptu (bez wywolan global sub).
Rola tekstu: print string z pierwszym parametrem 0x73 = wypowiedz, 0x62 = narracja,
menu = opcja gracza, log = log.
"""
from __future__ import annotations

from .gff import Gff
from .gpl import TRIGGERS, disassemble, literal, reachable

ROLES = {0x73: "wypowiedz", 0x62: "narracja"}


def _texts(ins):
    out = []
    for x in ins:
        if x.opcode == 0x4F and len(x.params) == 2:
            role = ROLES.get(literal(x.params[0]), "tekst")
            out += [(x.offset, role, t.value) for t in x.params[1] if t.kind == "str"]
        elif x.opcode == 0x48:
            title = [t.value for t in x.params[0] if t.kind == "str"]
            out += [(x.offset, "menu", s) for s in title]
            for j in range(1, len(x.params), 3):
                out += [(x.offset, "opcja", t.value) for t in x.params[j] if t.kind == "str"]
        elif x.opcode == 0x2C:
            out += [(x.offset, "log", t.value) for t in x.params[0] if t.kind == "str"]
    return out


def triggers(gpl: Gff) -> list[dict]:
    scripts = {}
    for tag in ("GPL", "MAS"):
        for sid, b in gpl.items(tag):
            scripts[(tag, sid)] = disassemble(b)[0]
    out = []
    for (tag, sid), ins in scripts.items():
        for x in ins:
            if x.opcode not in TRIGGERS:
                continue
            v = [literal(p) for p in x.params]
            if x.opcode == 0x70:
                objs, addr, target = [v[0], v[1]], v[2], v[3]
            else:
                objs, addr, target = [v[2]], v[0], v[1]
            out.append({"wyzwalacz": TRIGGERS[x.opcode], "zrodlo": f"{tag}{sid}@{x.offset}",
                        "obiekty": [-o for o in objs if isinstance(o, int) and o < 0],
                        "skrypt": f"GPL{target}" if target is not None else "", "adres": addr})
    # teksty osiagalne od adresu obslugi (skrypt docelowy to GPL o numerze `target`)
    for t in out:
        ins = scripts.get(("GPL", int(t["skrypt"][3:]))) if t["skrypt"] else None
        t["teksty"] = _texts(reachable(ins, t["adres"])) if ins and t["adres"] is not None else []
    return out


def script_texts(gpl: Gff) -> dict:
    """Teksty kazdego skryptu (wszystkie instrukcje), do zestawien bez wyzwalaczy."""
    return {f"{tag}{sid}": _texts(disassemble(b)[0]) for tag in ("GPL", "MAS") for sid, b in gpl.items(tag)}


def join(texts) -> str:
    """Skleja kawalki w czytelny tekst: kolejne wypowiedzi/narracja w jednej linii,
    menu i opcje gracza w osobnych liniach (opcje z prefiksem '> ')."""
    lines, cur, prev = [], "", None
    for _, role, s in texts:
        if role in ("opcja", "menu"):
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(("> " if role == "opcja" else "") + s.strip())
        elif (prev == role or not cur) and not (cur and cur.rstrip()[-1:] in ".!?'\"" and cur.endswith(("!", ".", "?", "'", '"'))):
            cur += s
        else:
            lines.append(cur)
            cur = s
        prev = role
    if cur:
        lines.append(cur)
    return "\n".join(x.rstrip() for x in lines)
