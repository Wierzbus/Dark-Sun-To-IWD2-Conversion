"""Buduje zestaw testowych tabel 2DA do override (test20-test27 paczki 2): listy czarow i domeny podklas DS,
progresja podklas z DSKLPROG, cechy i zdolnosci rasy z DSRASY/DSRWROG/RLAB.

  python tools/ds_testy_2da.py --listspll LISTSPLL.2DA --listdomn LISTDOMN.2DA --out testy_2da

LISTSPLL / LISTDOMN = oryginalne tabele gry (wyciagniete z instalacji, np. tools/wyciagnij_rasy.py) - wynik zawiera
dane gry, wiec katalog wyjsciowy trzymamy poza Gitem. Opis testow: CZYTAJ_TESTY.txt w katalogu wyjsciowym.
"""
import argparse
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
TAB = os.path.join(ROOT, "mod", "darksun_rasy", "darksun_rasy", "2da")

# kolumny list podklas DS w LISTSPLL: (nazwa, kolumna klasy bazowej, zmiany {czar: poziom})
LISTY = [
    ("CLR_DS", "CLR", {"SPPR101": 0, "SPWI112": 1, "SPWI304": 3}),   # bez Bless; Magic Missile 1, Fireball 3
    ("DRD_DS", "DRD", {"SPPR105": 0, "SPWI103": 1}),                 # bez Entangle; Burning Hands 1
    ("SOR_DS", "SOR", {"SPWI112": 0, "SPPR103": 1}),                 # bez Magic Missile; Cure Light Wounds 1
    ("BRD_DS", "BRD", {"SPWI112": 1}),                               # Magic Missile 1
    ("WIZ_DS", "WIZ", {"SPWI112": 0, "SPWI304": 2}),                 # bez Magic Missile; Fireball 2
]
# domeny kaplana DS (LISTDOMN kolumna CDS): zywiol ognia i ziemi, po jednym czarze na poziom
DOMENA = {"SPPR113": 1, "SPWI217": 2, "SPPR306": 3, "SPWI427": 4, "SPPR503": 5,
          "SPPR705": 6, "SPPR719": 7, "SPPR702": 8, "SPPR901": 9}
# DSKLPROG: wiersz -> zmiany kolumn
PROG = {
    "FIGHTER_DS": {"HP": "HPBARB"},
    "SORCERER_DS": {"BAB": "BAATFGT", "SAVE": "SAVEWAR", "SPELLS": "SOR_DS"},
    "CLERIC_DS": {"DOMAIN": "CDS", "SPELLS": "CLR_DS"},
    "DRUID_DS": {"SPELLS": "DRD_DS"},
    "BARD_DS": {"SPELLS": "BRD_DS"},
    "ROGUE_DS": {"HP": "HPWAR", "BAB": "BAATFGT"},
    "WIZARD_DS": {"SPELLS": "WIZ_DS"},
    "CLERIC_DS2": {"DOMAIN": "CTE"},
}


def czytaj(p):
    w = open(p, encoding="latin-1").read().splitlines()
    kol = w[2].split()
    wiersze = [l.split() for l in w[3:] if len(l.split()) == len(kol) + 1]
    return w[1].strip(), kol, wiersze


def pisz(p, domyslna, kol, wiersze):
    with open(p, "w", encoding="latin-1", newline="\r\n") as f:
        f.write("2DA V1.0\n%s\n\t%s\n" % (domyslna, "\t".join(kol)))
        for r in wiersze:
            f.write("\t".join(r) + "\n")


def lista_klas(src, out):
    d, kol, wiersze = czytaj(src)
    kol = [k for k in kol if k not in [n for n, _, _ in LISTY]]
    wiersze = [r[:len(kol) + 1] for r in wiersze]
    res = kol.index("SPELL_RES_REF") + 1
    for nazwa, baza, zmiany in LISTY:
        b = kol.index(baza) + 1
        for r in wiersze:
            r.append(str(zmiany.get(r[res].upper(), r[b])))
        kol.append(nazwa)
    pisz(out, d, kol, wiersze)


def domeny(src, out):
    d, kol, wiersze = czytaj(src)
    kol = [k for k in kol if k != "CDS"]
    wiersze = [r[:len(kol) + 1] for r in wiersze]
    res = kol.index("DOMAIN_RESREF") + 1
    for r in wiersze:
        r.append(str(DOMENA.get(r[res].upper(), 0)))
    kol.append("CDS")
    pisz(out, d, kol, wiersze)


def klprog(out):
    w = open(os.path.join(TAB, "DSKLPROG.2DA")).read().splitlines()
    kol = w[2].split()
    linie = w[:3]
    for l in w[3:]:
        f = l.split()
        if not f:
            continue
        for k, v in PROG.get(f[0], {}).items():
            f[kol.index(k) + 1] = v
        linie.append(f[0].ljust(14) + "".join(x.ljust(10) for x in f[1:]).rstrip())
    open(out, "w", newline="\r\n").write("\n".join(linie) + "\n")


def rasy(out_dir):
    w = open(os.path.join(TAB, "DSRASY.2DA")).read().splitlines()
    w = [("HUMAN                  RLTSTHUM  1          0        2      1" if l.split()[:1] == ["HUMAN"] else l)
         for l in w]
    open(os.path.join(out_dir, "DSRASY.2DA"), "w", newline="\r\n").write("\n".join(w) + "\n")
    w = open(os.path.join(TAB, "DSRWROG.2DA")).read().splitlines()
    w = [("HUMAN                  2     0          160 155 0   0   0   0" if l.split()[:1] == ["HUMAN"] else l)
         for l in w]
    open(os.path.join(out_dir, "DSRWROG.2DA"), "w", newline="\r\n").write("\n".join(w) + "\n")
    kol = "  ".join(str(i) for i in range(1, 31))
    puste = ["****"] * 30
    a1 = ["GA_SPIN267"] + puste[1:]
    a2 = ["****", "GA_SPIN264"] + puste[2:]
    open(os.path.join(out_dir, "RLTSTHUM.2DA"), "w", newline="\r\n").write(
        "2DA V1.0\n****\n          %s\nABILITY1  %s\nABILITY2  %s\n" % (kol, "  ".join(a1), "  ".join(a2)))


CZYTAJ = r"""TESTOWE TABELE 2DA - paczka 2 (test20-test33)

Wymaga: paczka 2 test33 zainstalowana (komponenty 0-5; 6 = kody do awansu), gra z IWD2_<W>_DS.exe.
Przed skopiowaniem zrob kopie override\DSKLPROG.2DA, LISTSPLL.2DA, LISTDOMN.2DA, DSRASY.2DA, DSRWROG.2DA.
Skopiuj zawartosc katalogu klasy\ (i opcjonalnie rasy\) do override. Tabele sa czytane przy starcie gry.
Wszystkie testy na NOWYCH postaciach (kreator) - istniejace postacie nie dostana list z minionych poziomow.

KLASY (katalog klasy\: DSKLPROG.2DA, LISTSPLL.2DA, LISTDOMN.2DA)

1. Kaplan DS (CLERIC_DS) - lista czarow CLR_DS i domena CDS
   - lista: jak kaplan, ale BEZ Bless (SPPR101), Z Magic Missile (SPWI112) na 1. i Fireball (SPWI304) na 3. poziomie
   - domena (jeden czar na poziom): 1 Sunscorch, 2 Aganazzar's Scorcher, 3 Protection From Fire, 4 Fire Shield (Red),
     5 Flame Strike, 6 Fire Storm, 7 Tremor, 8 Planar Ally: Earth Elemental, 9 Elemental Legion
   Sprawdz: w ksiedze / zapamietywaniu 1. poziomu jest Magic Missile, nie ma Bless; czar domeny 1. poziomu = Sunscorch.
   Zapamietaj i rzuc Magic Missile (poziom czaru musi sie zgadzac - 1). Awansuj do 5. poziomu: Fireball w 3. kregu,
   Protection From Fire jako domena 3. kregu.
   Porownaj: zwykly kaplan (np. Tempusa) ma Bless, nie ma Magic Missile.

2. Druid DS (DRUID_DS) - lista DRD_DS: bez Entangle (SPPR105), z Burning Hands (SPWI103) na 1. poziomie.
   Sprawdz ksiege 1. poziomu nowego druida DS i zwyklego druida.

3. Zaklinacz DS (SORCERER_DS) - lista SOR_DS: bez Magic Missile, z Cure Light Wounds (SPPR103) na 1. poziomie.
   Sprawdz: ekran wyboru znanych czarow w kreatorze - nie ma Magic Missile, jest Cure Light Wounds; wybierz go i rzuc.
   Do tego progresja: premia do ataku jak wojownik (BAATFGT: +1 na 1. poziomie zamiast +0) i rzuty obronne
   wojownika (SAVEWAR: Wytrwalosc +2, Wola +0 zamiast Wola +2) - karta postaci.

4. Bard DS (BARD_DS) - lista BRD_DS: Magic Missile na 1. poziomie (zwykly bard go nie ma).
   Bard dostaje czary 1. kregu od 2. poziomu - sprawdz ekran wyboru czarow przy awansie na 2. poziom.

5. Wojownik DS (FIGHTER_DS) - kosc PW k12 (HPBARB) zamiast k10. Sprawdz PW przy kolejnych awansach
   (srednio wiecej niz zwykly wojownik; maksimum na poziom 12 + premia z Kondycji).

6. Lotrzyk DS (ROGUE_DS, Athasian Rogue) - kosc PW k10 (HPWAR) i premia do ataku wojownika (BAATFGT, +1 na 1. poziomie).
   Sprawdz karte postaci (premia do ataku) i PW przy awansach; porownaj ze zwyklym lotrzykiem (k6, +0).

7. Czarodziej DS (WIZARD_DS, Preserver) - lista WIZ_DS: bez Magic Missile, Fireball (SPWI304) na 2. poziomie.
   Sprawdz: ksiega nowego Preservera w kreatorze - nie ma Magic Missile; na 3. poziomie postaci (czary 2. kregu)
   mozna wybrac Fireball. Zwykly czarodziej ma Magic Missile, Fireball dopiero w 3. kregu.

8. Kaplan DS 2 (CLERIC_DS2, Fire Cleric) - domena Tempusa (CTE) zamiast domeny CDS kaplana DS (Earth Cleric).
   Sprawdz: czary domeny 1. poziomu Fire Clerica = jak kaplan Tempusa; Earth Cleric (CLERIC_DS) = Sunscorch.

9. Wieloklasowosc (test26/27): kazda klasa ma wlasna podklase DS i jej progresje.
   Np. gladiator (FIGHTER_DS, k12) z charakterem nie-praworzadnym -> przy awansie dobiera lotrzyka, w oknie podklas
   wybiera Athasian Rogue. Sprawdz: karta postaci - "Gladiator: n" i "Athasian Rogue: 1" w sekcji Levels;
   PW za poziom lotrzyka k10, za poziom gladiatora k12; premia do ataku rosnie jak u wojownika w obu klasach.
   Praworzadna postac nie dobierze barbarzyncy ani barda (ALIGNMNT - reguly gry).

RASY (katalog rasy\: DSRASY.2DA, DSRWROG.2DA, RLTSTHUM.2DA) - test20 na czlowieku
10. Czlowiek: widzenie w ciemnosci, +2 do trafienia bronia miotana i proca, odpornosc na magie +1 na poziom postaci,
   +2 do trafienia przeciw orkom (160) i goblinom (155); zdolnosci: 1. poziom Ilmater's Endurance (GA_SPIN267),
   2. poziom Tempus' Strength (GA_SPIN264).
   Sprawdz: nowy czlowiek - zdolnosci wrodzone na 1. poziomie, po awansie druga; odpornosc na magie na karcie rosnie.

Jesli gra sie wysypie: zapisz komunikat (plik i linia asercji) i ktory ekran / akcja.
Przywrocenie: skopiuj kopie tabel z powrotem do override.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listspll", required=True)
    ap.add_argument("--listdomn", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    k, r = os.path.join(a.out, "klasy"), os.path.join(a.out, "rasy")
    os.makedirs(k, exist_ok=True)
    os.makedirs(r, exist_ok=True)
    lista_klas(a.listspll, os.path.join(k, "LISTSPLL.2DA"))
    domeny(a.listdomn, os.path.join(k, "LISTDOMN.2DA"))
    klprog(os.path.join(k, "DSKLPROG.2DA"))
    rasy(r)
    open(os.path.join(a.out, "CZYTAJ_TESTY.txt"), "w", newline="\r\n").write(CZYTAJ)
    print("zapisano", a.out)


if __name__ == "__main__":
    main()
