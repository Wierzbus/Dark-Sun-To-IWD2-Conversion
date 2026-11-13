"""Propozycja konwersji przedmiotow Dark Sun -> ITM IWD2 (V2.0) regulami.

Wejscie: items.csv z `python -m darksun.extract` (rekord przedmiotu RDFF + typ IT1R w kolumnach it_*).
Wyjscie (bez plikow gry, tylko plan):
  ds_itm_plan.csv        - jeden wiersz na przedmiot RDFF: regula, typ IWD2, parametry, ikona
  ds_itm_unresolved.csv  - przedmioty, ktorych reguly nie rozstrzygaja (do decyzji wlasciciela)

Zasada jak w BGtoIWD2 (docs/zasady_konwersji_i_zgodnosci.md): bez list wyjatkow, kazda regula
zapisuje, co zastosowala. Generator ITM (entities/itm.py z BGtoIWD2) bierze szablon IWD2 tego
samego typu (najblizsza mediana wagi) i nadpisuje parametry policzone tu.

Kolejnosc regul (pierwsza pasujaca wygrywa):
  R0 OBIEKT    - miejsce 0 i flagi IT1R != 0 (drzwi, skrzynie, zaslony, sejfy, zwloki...) -> nie ITM;
                 w ARE jako drzwi / pojemnik / punkt informacji (`are_rola`).
  R1 PANCERZ   - flaga 0x80 i miejsce 1/3/10/6 (tulow, ramiona, nogi, glowa) -> pancerz / karwasze /
                 buty / helm; KP z base_ac.
  R2 TARCZA    - weapon_type 4 -> tarcza (wielkosc z base_ac).
  R3 BRON      - miejsce 5 i weapon_type 1/17 -> bron biala; typ wg slowa w nazwie IT1R, potem wg kosci i wagi.
  R4 DYSTANS   - miejsce 12 (weapon_type 2 proca, 10 luk, 18 chatkcha = bron rzucana).
  R5 AMUNICJA  - miejsce 11 -> strzaly.
  R6 UBIOR     - miejsca 2 pas, 4 buty, 7 szyja, 8 plaszcz, 9 pierscien.
  R7 RZECZ     - miejsce 0, flagi 0: zwoj, rozdzka, ksiazka, klucz, klejnot, jedzenie, inne (slowa w nazwie).
"""
import argparse
import csv
import os
import re

# Kody typow ITM (IESDP; IWD2 = BG + typy pancerzy 0x3C-0x44 i tarcz 0x2F/0x31/0x35, por. BGtoIWD2 entities/itm_map.py)
TYP = {
    "rozne": 0x00, "amulet": 0x01, "pancerz": 0x02, "pas": 0x03, "buty": 0x04, "strzaly": 0x05,
    "karwasze": 0x06, "helm": 0x07, "klucz": 0x08, "mikstura": 0x09, "pierscien": 0x0A, "zwoj": 0x0B,
    "tarcza": 0x0C, "kule": 0x0E, "luk": 0x0F, "sztylet": 0x10, "bulawa": 0x11, "proca": 0x12,
    "maly_miecz": 0x13, "duzy_miecz": 0x14, "mlot": 0x15, "morgensztern": 0x16, "cep": 0x17,
    "rzutki": 0x18, "topor": 0x19, "kostur": 0x1A, "kusza": 0x1B, "piesci": 0x1C, "wlocznia": 0x1D,
    "halabarda": 0x1E, "belty": 0x1F, "plaszcz": 0x20, "klejnot": 0x22, "rozdzka": 0x23,
    "ksiazka": 0x25, "maczuga": 0x2C,
}

# R3: slowa w nazwie typu IT1R / nazwie przedmiotu -> typ broni (najpierw nazwa)
SLOWA_BRONI = [
    (r"dagger|knife|blade$|hornblade|swiftbite", "sztylet"),
    (r"great axe|axe", "topor"),
    (r"long sword|sword|dragonsbane|draketooth|bloodwrath|dark flame", "duzy_miecz"),
    (r"quarterstaff|staff", "kostur"),
    (r"club|shillelagh|soulcrusher", "maczuga"),
    (r"mace", "bulawa"),
    (r"hammer|pick", "mlot"),
    (r"polearm|hook|gythka|cahulak", "halabarda"),
    (r"glove", "piesci"),
]
# R7: rzeczy noszone w plecaku
SLOWA_RZECZY = [
    (r"scroll", "zwoj"), (r"wand|rod", "rozdzka"), (r"book|journal|tome", "ksiazka"),
    (r"key", "klucz"), (r"gem|tear|eye$|crystal|stone$", "klejnot"), (r"potion|bottle|elixir", "mikstura"),
    (r"banana|grain|grape|lemon|pear|guava|apple|orange|lime|corn|fruit|meat|bread", "rozne"),
]
# R0: rola obiektu w ARE
SLOWA_OBIEKTOW = [
    (r"door|gate|portcul", "drzwi"),
    (r"chest|bag|wardrobe|safe|pot|crate|barrel|body|skeleton|nest|haystack|drain", "pojemnik"),
]


def dopasuj(nazwa, reguly, domyslnie=None):
    n = (nazwa or "").lower()
    for wzor, wynik in reguly:
        if re.search(wzor, n):
            return wynik
    return domyslnie


def i(x, d=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return d


def bron_z_parametrow(dice, sides, waga):
    """Gdy nazwa nic nie mowi: kosci i waga (waga IT1R w 1/10 funta)."""
    if sides <= 4 and waga <= 10:
        return "sztylet"
    if sides >= 10 and waga >= 100:
        return "halabarda"
    if sides >= 10:
        return "topor"
    if sides == 8:
        return "duzy_miecz" if waga >= 30 else "maly_miecz"
    return "bulawa"


def regula(w):
    pl, fl, wt = i(w["it_placement"], -1), i(w["it_flags"]), i(w["it_weapon_type"])
    typ_nazwa = w.get("it_nazwa_typu") or ""
    nazwa = w["name"] or typ_nazwa
    dice, sides, waga, ac = i(w["it_dice"]), i(w["it_sides"]), i(w["it_weight"]), i(w["it_base_ac"])
    wynik = {"regula": "", "typ": "", "are_rola": "", "kp": "", "obrazenia": "", "uwagi": ""}
    if pl < 0:
        wynik["regula"] = "BRAK_IT1R"
        return wynik
    if pl == 0 and fl != 0:
        wynik.update(regula="R0_OBIEKT", are_rola=dopasuj(nazwa, SLOWA_OBIEKTOW, "punkt_informacji"))
        return wynik
    if fl & 0x80 and pl in (1, 3, 10, 6):
        typ = {1: "pancerz", 3: "karwasze", 10: "buty", 6: "helm"}[pl]
        wynik.update(regula="R1_PANCERZ", typ=typ, kp=ac)
        if pl in (3, 10):
            wynik["uwagi"] = "czesc zbroi Dark Sun (ramiona/nogi); KP jako premia przedmiotu"
        return wynik
    if wt == 4:
        wynik.update(regula="R2_TARCZA", typ="tarcza", kp=ac)
        return wynik
    if pl == 5 and wt in (1, 17):
        typ = dopasuj(typ_nazwa, SLOWA_BRONI) or dopasuj(nazwa, SLOWA_BRONI) or bron_z_parametrow(dice, sides, waga)
        if typ == "sztylet" and sides >= 6:
            typ = "maly_miecz"  # ostrze nazwane jak sztylet, ale z koscia d6+ (Hornblade, Swiftbite)
        wynik.update(regula="R3_BRON", typ=typ, obrazenia=f"{dice}d{sides}{i(w['it_mod']):+d}")
        return wynik
    if pl == 12:
        typ = {2: "proca", 10: "luk", 18: "rzutki"}.get(wt)
        wynik.update(regula="R4_DYSTANS", typ=typ or "", obrazenia=f"{dice}d{sides}{i(w['it_mod']):+d}")
        if wt == 18:
            wynik["uwagi"] = "chatkcha: bron rzucana, wraca do rzucajacego (efekt do decyzji)"
        return wynik
    if pl == 11:
        wynik.update(regula="R5_AMUNICJA", typ="strzaly", obrazenia=f"{dice}d{sides}{i(w['it_mod']):+d}")
        return wynik
    if pl in (2, 4, 7, 8, 9):
        wynik.update(regula="R6_UBIOR", typ={2: "pas", 4: "buty", 7: "amulet", 8: "plaszcz", 9: "pierscien"}[pl])
        return wynik
    if pl == 5:
        wynik.update(regula="R7_RZECZ", typ=dopasuj(nazwa, SLOWA_RZECZY, "rozne"),
                     uwagi="miejsce dlon bez broni (np. kula, ksiega)")
        return wynik
    if pl == 0:
        wynik.update(regula="R7_RZECZ", typ=dopasuj(nazwa, SLOWA_RZECZY, "rozne"))
        return wynik
    wynik["regula"] = "NIEROZSTRZYGNIETE"
    return wynik


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ds", required=True, help="katalog z items.csv (i item_types.csv, names.csv)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(os.path.join(a.ds, "items.csv"), encoding="utf-8") as f:
        wiersze = list(csv.DictReader(f, delimiter=";"))
    # nazwa typu IT1R = najczestsza nazwa przedmiotow tego typu (IT1R nie ma wlasnej nazwy)
    licz = {}
    for w in wiersze:
        if w["name"]:
            licz.setdefault(w["item_index"], {}).setdefault(w["name"], 0)
            licz[w["item_index"]][w["name"]] += 1
    nazwa_typu = {k: max(v, key=v.get) for k, v in licz.items()}
    os.makedirs(a.out, exist_ok=True)
    kol = ["rdff_id", "owner_name", "name", "item_index", "it_nazwa_typu", "regula", "typ", "typ_kod",
           "are_rola", "obrazenia", "kp", "premia", "waga_funty", "cena", "ladunki", "ikona", "ikona_ziemi", "uwagi"]
    plan, nier = [], []
    for w in wiersze:
        w["it_nazwa_typu"] = nazwa_typu.get(w["item_index"], "")
        r = regula(w)
        bmp = i(w["bmp_id"], -1)
        wiersz = {
            "rdff_id": w["rdff_id"], "owner_name": w["owner_name"], "name": w["name"], "item_index": w["item_index"],
            "it_nazwa_typu": w["it_nazwa_typu"], **r,
            "typ_kod": f"0x{TYP[r['typ']]:02X}" if r["typ"] in TYP else "",
            "premia": i(w["bonus"]) + i(w["it_mod"]) if r["regula"].startswith(("R1", "R2")) else i(w["bonus"]),
            "waga_funty": round(i(w["it_weight"]) / 10, 1) if w["it_weight"] else "",
            "cena": w["value"], "ladunki": w["charges"] if r["typ"] in ("rozdzka", "zwoj") else "",
            "ikona": f"DSI{bmp:04d}" if bmp >= 0 and r["regula"] != "R0_OBIEKT" else "",
            "ikona_ziemi": f"DSG{bmp:04d}" if bmp >= 0 and r["regula"] != "R0_OBIEKT" else "",
        }
        plan.append(wiersz)
        if r["regula"] in ("NIEROZSTRZYGNIETE", "BRAK_IT1R") or (r["regula"].startswith("R") and not r["typ"] and r["regula"] != "R0_OBIEKT"):
            nier.append(wiersz)
    for nazwa, dane in (("ds_itm_plan.csv", plan), ("ds_itm_unresolved.csv", nier)):
        with open(os.path.join(a.out, nazwa), "w", encoding="utf-8", newline="") as f:
            wr = csv.DictWriter(f, kol, delimiter=";")
            wr.writeheader()
            wr.writerows(dane)
    from collections import Counter
    print(Counter(p["regula"] for p in plan).most_common())
    print(Counter(p["typ"] for p in plan if p["typ"]).most_common())
    print("nierozstrzygniete:", len(nier))


if __name__ == "__main__":
    main()
