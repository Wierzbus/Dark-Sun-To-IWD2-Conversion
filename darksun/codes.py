"""Przyblizone tabele kodow ras i klas (blok postaci RDFF).

Ustalone na imionach postaci (np. "Psionicist", "Templar", "Wild Mul", "Elven Leader")
oraz na kolejnosci ras z podrecznika Dark Sun. Pewnosc: "pewne" = potwierdzone imionami,
"prawdop." = zgodne z kolejnoscia lub kilkoma imionami, "?" = zgadywanie.
"""

RACES = {
    0: ("brak/zywiolak", "?"),
    1: ("czlowiek", "pewne"),
    2: ("krasnolud", "prawdop."),
    3: ("elf", "pewne"),
    4: ("polelf", "prawdop."),
    5: ("pololbrzym", "prawdop."),
    6: ("nizolek", "prawdop."),
    7: ("mul", "pewne"),
    8: ("thri-kreen", "pewne"),
    9: ("nieumarly", "pewne"),
    10: ("pajeczak/kreen-podobny", "?"),
    11: ("mastyrial", "prawdop."),
    12: ("zwierze/potwor", "prawdop."),
    13: ("smokowaty (wywerna)", "prawdop."),
    14: ("istota pozaplanarna/zywiolak", "prawdop."),
}

CLASSES = {
    0: ("brak (potwor)", "pewne"),
    1: ("kaplan powietrza", "prawdop."),
    2: ("kaplan ziemi", "?"),
    3: ("kaplan ognia", "?"),
    4: ("kaplan wody", "prawdop."),
    5: ("druid?", "?"),
    6: ("druid", "pewne"),
    7: ("druid?", "?"),
    9: ("wojownik", "pewne"),
    10: ("gladiator", "pewne"),
    11: ("zachowawca (preserver)", "prawdop."),
    12: ("psionik", "pewne"),
    13: ("?", "?"),
    15: ("tropiciel", "pewne"),
    17: ("zlodziej", "prawdop."),
    18: ("skalacz (defiler)", "pewne"),
    19: ("templariusz", "pewne"),
}

GENDERS = {0: "brak?", 1: "m?", 2: "k?"}  # "Chief Daughter" ma kod 1, wiec niepewne


def race_name(code: int) -> str:
    n, p = RACES.get(code, (f"kod {code}", "?"))
    return n if p == "pewne" else f"{n} ({p})"


def class_names(classes, levels) -> str:
    parts = []
    for c, lv in zip(classes, levels):
        if c == 0 and parts:
            continue
        n, p = CLASSES.get(c, (f"kod {c}", "?"))
        parts.append((n if p == "pewne" else f"{n} ({p})") + (f" {lv}" if lv else ""))
    return " / ".join(parts)
