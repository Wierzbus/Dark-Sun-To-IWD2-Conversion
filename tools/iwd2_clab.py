"""Tablice zdolnosci CLABDSnn (format CLAB IWD2: wiersze ABILITYn x kolumny = poziom klasy 1..30).

Wpisy: GA_<SPL> zdolnosc do uzycia (kazdy wpis = jedno uzycie dziennie wiecej), AP_<SPL> efekt staly,
FA_%fa_NNN% tekst na karcie postaci (strref z tra, instalator podstawia przez EVALUATE_BUFFER).
Na jednym poziomie kilka wpisow - kolejne wiersze ABILITYn.

  python tools/iwd2_clab.py --out mod/darksun_rasy/darksun_rasy/2da
"""
import argparse
import os

KLASY = {
    # --- nowe klasy bazowe (test41, zdolnosci dodane w test43) ---
    "CLABDS16": [  # Samurai
        (2, "FA_%fa_404%"), (3, "GA_DSKIAI"), (3, "FA_%fa_405%"), (6, "GA_SPIN172"), (6, "FA_%fa_406%"),
        (8, "GA_DSKIAI"), (11, "AP_DSSAIJ"), (11, "FA_%fa_407%"), (14, "GA_DSKIAI"), (14, "GA_SPIN172"),
    ],
    "CLABDS17": [  # Swashbuckler
        (2, "AP_DSSWREF"), (2, "FA_%fa_414%"), (3, "AP_DSSWDMG"), (3, "FA_%fa_415%"), (5, "AP_DSDDAC"),
        (5, "FA_%fa_416%"), (7, "FA_%fa_417%"), (10, "AP_DSDDAC"), (11, "AP_DSSWREF"), (11, "GA_DSSWLCK"),
        (15, "AP_DSDDAC"), (17, "AP_DSSWWIL"), (20, "AP_DSSWREF"), (20, "AP_DSDDAC"),
    ],
    "CLABDS19": [  # Ninja
        (1, "FA_%fa_434%"), (2, "GA_SPIN191"), (2, "FA_%fa_435%"), (3, "GA_SPIN231"), (4, "FA_%fa_436%"),
        (6, "GA_SPIN191"), (6, "GA_SPIN194"), (10, "GA_SPIN191"), (12, "GA_SPIN194"), (14, "GA_SPIN191"),
        (14, "GA_SPIN211"),
    ],
    "CLABDS20": [  # Scout
        (1, "AP_DSSCSK"), (1, "FA_%fa_444%"), (2, "AP_DSSCFRT"), (2, "FA_%fa_445%"), (3, "AP_DSBBNMV"),
        (3, "FA_%fa_446%"), (5, "AP_DSSCSK"), (6, "FA_%fa_447%"), (9, "AP_DSSCSK"), (10, "GA_SPIN200"),
        (11, "AP_DSSCFRT"), (11, "AP_DSBBNMV"), (13, "AP_DSSCSK"), (14, "GA_SPIN191"), (17, "AP_DSSCSK"),
        (18, "GA_SPIN191"),
    ],
    "CLABDS23": [  # Favored Soul
        (3, "AP_DSFSWF"), (3, "FA_%fa_474%"), (5, "AP_DSFSRFI"), (10, "AP_DSFSREL"), (15, "AP_DSFSRAC"),
        (17, "AP_DSDDDR"),
    ],
    # --- klasy prestizowe test43 ---
    "CLABDS24": [  # Inquisitor (Church Inquisitor, CD)
        (1, "GA_SPIN120"), (1, "AP_DSINCHM"), (1, "FA_%fa_484%"), (3, "GA_SPIN200"), (5, "GA_SPIN120"),
        (7, "GA_SPIN200"), (10, "GA_SPIN200"),
    ],
    "CLABDS25": [  # Blighter (CD)
        (1, "GA_SPIN189"), (1, "FA_%fa_494%"), (4, "GA_SPIN189"), (6, "GA_SPIN174"), (7, "GA_SPIN189"),
        (10, "GA_SPIN189"), (10, "GA_SPIN174"),
    ],
    "CLABDS26": [  # Stormlord (CD)
        (1, "AP_DSFSREL"), (1, "FA_%fa_504%"), (2, "GA_SPIN263"), (5, "AP_DSFSREL"), (5, "GA_SPIN263"),
        (8, "GA_SPIN263"), (9, "AP_DSFSREL"),
    ],
    "CLABDS27": [  # Ravager (CW)
        (1, "GA_SPIN270"), (1, "FA_%fa_514%"), (3, "GA_SPIN217"), (4, "GA_SPIN270"), (5, "AP_DSSWDMG"),
        (6, "GA_SPIN217"), (7, "GA_SPIN270"), (9, "GA_SPIN217"), (10, "GA_SPIN270"),
    ],
    "CLABDS28": [  # Hunter of the Dead (CW)
        (1, "GA_SPIN152"), (2, "GA_SPIN970"), (3, "GA_SPIN152"), (4, "AP_DSHDLD"), (5, "GA_SPIN203"),
        (5, "GA_SPIN152"), (6, "GA_SPIN970"), (7, "GA_SPIN152"), (9, "GA_SPIN203"), (9, "GA_SPIN152"),
        (10, "FA_%fa_524%"),
    ],
    "CLABDS29": [  # Dervish (CW)
        (1, "AP_DSDDAC"), (1, "GA_DSDERW"), (3, "AP_DSBBNMV"), (3, "GA_DSDERW"), (4, "AP_DSDDAC"),
        (5, "GA_DSDERW"), (5, "FA_%fa_534%"), (7, "AP_DSDDAC"), (7, "GA_DSDERW"), (9, "GA_DSDERW"),
        (10, "AP_DSDDAC"),
    ],
    "CLABDS30": [  # Purple Dragon Knight (CW, Faerun)
        (1, "GA_SPIN136"), (2, "GA_SPIN209"), (3, "GA_SPIN136"), (4, "GA_SPIN172"), (4, "GA_SPIN209"),
        (5, "GA_SPIN136"), (5, "FA_%fa_544%"),
    ],
    "CLABDS31": [  # Warpriest (CD)
        (1, "GA_SPIN198"), (2, "GA_SPIN209"), (3, "GA_SPIN198"), (4, "GA_SPIN208"), (5, "GA_SPIN217"),
        (6, "GA_SPIN209"), (7, "GA_SPIN208"), (8, "FA_%fa_554%"), (9, "GA_SPIN217"), (10, "GA_SPIN208"),
    ],
    # --- klasy potworow test45 (podklasy wojownika ukryte przed graczem), cechy typu na 1. poziomie ---
    "CLABDS32": [(1, "AP_DSMNUND")],   # MON_UNDEAD
    "CLABDS33": [(1, "AP_DSMNDV")],    # MON_OUTSIDER
    "CLABDS34": [(1, "AP_DSMNELE")],   # MON_ELEM_FW
    "CLABDS35": [(1, "AP_DSMNELE")],   # MON_ELEM_FA
    "CLABDS36": [(1, "FA_%fa_644%")],  # MON_GIANT
    "CLABDS37": [(1, "AP_DSMNDV")],    # MON_MONHUMAN
    "CLABDS38": [(1, "FA_%fa_664%")],  # MON_ANIMAL
    "CLABDS39": [(1, "AP_DSMNVER")],   # MON_VERMIN
    "CLABDS40": [(1, "AP_DSMNDRA")],   # MON_DRAGON
    "CLABDS41": [(1, "AP_DSMNDV")],    # MON_ABERRATION
    "CLABDS42": [(1, "AP_DSMNCON")],   # MON_CONSTRUCT
    "CLABDS43": [(1, "AP_DSMNDV")],    # MON_MAGBEAST
    "CLABDS44": [(1, "AP_DSMNOOZ")],   # MON_OOZE
    "CLABDS45": [(1, "AP_DSMNOOZ")],   # MON_PLANT
    "CLABDS46": [(1, "FA_%fa_744%")],  # MON_FEY
}


def clab(wpisy):
    wiersze = []
    for poz, w in wpisy:
        for r in wiersze:
            if r[poz - 1] == "****":
                r[poz - 1] = w
                break
        else:
            r = ["****"] * 30
            r[poz - 1] = w
            wiersze.append(r)
    out = ["2DA V1.0", "****", "          " + "  ".join(str(i) for i in range(1, 31))]
    for i, r in enumerate(wiersze, 1):
        out.append(f"ABILITY{i}  " + "  ".join(r))
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    for n, w in KLASY.items():
        with open(os.path.join(a.out, n + ".2DA"), "w", newline="") as f:
            f.write(clab(w))
        print(n, len(w))


if __name__ == "__main__":
    main()
