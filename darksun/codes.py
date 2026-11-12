"""Tabele kodow ras, klas, plci i charakteru (blok postaci RDFF).

Zrodla: tabele tekstow karty postaci w DSUN.EXE (MALE, FEMALE; HUMAN..THRI-KREEN;
CLERIC..THIEF; LAWFUL GOOD..CHAOTIC EVIL) oraz imiona postaci (np. "Psionicist", "Templar",
"Wild Mul", "Elven Leader"). Pewnosc: "pewne" = EXE i imiona zgodne, "prawdop." = jedno zrodlo
lub kilka imion, "?" = zgadywanie. Kody klas wewnetrznych nie odpowiadaja wprost kolejnosci
z EXE (tam tylko 8 klas gracza); 9-12 zgadzaja sie z kolejnoscia Fighter, Gladiator,
Preserver, Psionicist.
"""

RACES = {
    0: ("brak/zywiolak", "?"),
    1: ("czlowiek", "pewne"),
    2: ("krasnolud", "pewne"),
    3: ("elf", "pewne"),
    4: ("polelf", "pewne"),
    5: ("pololbrzym", "pewne"),
    6: ("nizolek", "pewne"),
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
    1: ("kaplan/druid powietrza", "prawdop."),
    2: ("kaplan/druid ziemi", "?"),
    3: ("kaplan/druid ognia", "?"),
    4: ("kaplan/druid wody", "prawdop."),
    5: ("druid?", "?"),
    6: ("druid", "pewne"),
    7: ("druid?", "?"),
    9: ("wojownik", "pewne"),
    10: ("gladiator", "pewne"),
    11: ("zachowawca (preserver)", "pewne"),
    12: ("psionik", "pewne"),
    13: ("?", "?"),
    15: ("tropiciel", "pewne"),
    17: ("zlodziej", "prawdop."),
    18: ("skalacz (defiler)", "pewne"),
    19: ("templariusz", "pewne"),
}

GENDERS = {0: "brak", 1: "m", 2: "k"}  # EXE: MALE, FEMALE; wyjatek w danych: "Chief Daughter" ma 1

ALIGNMENTS = {0: "brak", 1: "LG", 2: "LN", 3: "LE", 4: "NG", 5: "TN", 6: "NE", 7: "CG", 8: "CN", 9: "CE"}
# EXE: LAWFUL GOOD .. CHAOTIC EVIL; numeracja od 1 zgodna z danymi (nieumarli 9 = CE, zwierzeta 5 = TN)


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
