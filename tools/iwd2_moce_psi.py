"""Moce psioniczne z wlasnymi nazwami (komponent 11 paczki 2).

Od test53 psion, dziki talent i wojownik psioniczny rzucaja najblizsze czary gry (kolumny LISTSPLL PSION, PSYWAR).
Tu kazda moc dostaje kopie czaru gry (SPWI<krag>70..) z nazwa mocy i opisem: naglowek mocy (tra) + "w IWD2 dziala
jak czar <nazwa z gry>" + opis czaru z gry - nazwe i opis czaru wzoru instalator czyta z TLK (READ_STRREF), wiec
w repozytorium nie ma tekstow gry. Wiersze LISTSPLL: nowa moc z kregiem w PSION / PSYWAR, czar wzoru traci te kolumny.

  python tools/iwd2_moce_psi.py          # dopisuje tra (@1300+) i blok komponentu 11 w tp2
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from iwd2_psionika_t53 import PSION, PSYWAR  # noqa: E402

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = R + "/mod/darksun_rasy"
PL = {
    "Mind Thrust": "Pchnięcie umysłu", "Force Screen": "Ekran mocy", "Inertial Armor": "Pancerz inercyjny",
    "Psionic Charm": "Psioniczne zauroczenie", "Demoralize": "Demoralizacja", "Hypnotism": "Hipnoza",
    "Energy Ray": "Promień energii", "Entangling Ectoplasm": "Oplatająca ektoplazma", "Crystal Shard": "Kryształowy odłamek",
    "Precognition": "Prekognicja", "Ego Whip": "Bicz ego", "Concealing Amorpha": "Skrywająca amorfa",
    "Cloud Mind": "Zamglenie umysłu", "Energy Stun": "Ogłuszenie energią", "Swarm of Crystals": "Rój kryształów",
    "Thought Shield": "Tarcza myśli", "Id Insinuation": "Podszept id", "Energy Bolt": "Grom energii",
    "Dispel Psionics": "Rozproszenie psioniki", "Body Adjustment": "Regulacja ciała", "Psionic Blast": "Wybuch psioniczny",
    "Hostile Empathic Transfer": "Wrogi przekaz empatyczny", "Energy Burst": "Rozbłysk energii",
    "Energy Ball": "Kula energii", "Psionic Dominate": "Psioniczna dominacja",
    "Psionic Freedom of Movement": "Psioniczna swoboda ruchów", "Inertial Barrier": "Bariera inercyjna",
    "Mental Barrier": "Bariera mentalna", "Death Urge": "Pragnienie śmierci", "Psychic Crush": "Psychiczne zmiażdżenie",
    "Power Resistance": "Odporność na moce", "Tower of Iron Will": "Wieża żelaznej woli",
    "Ectoplasmic Shambler": "Ektoplazmatyczny włóczęga", "Psionic Hold Monster": "Psioniczne unieruchomienie potwora",
    "Disintegrate": "Dezintegracja", "Breath of the Black Dragon": "Oddech czarnego smoka",
    "Temporal Acceleration": "Przyspieszenie czasu", "Psionic Finger of Death": "Psioniczny palec śmierci",
    "Insanity": "Obłęd", "Decerebrate": "Odmóżdżenie", "Energy Conversion": "Przemiana energii",
    "Mass Cloud Mind": "Masowe zamglenie umysłu", "Psionic Mind Blank": "Psioniczna pustka umysłu",
    "Iron Body": "Żelazne ciało", "Ultrablast": "Ultrawybuch", "Microcosm": "Mikrokosmos", "Tornado Blast": "Wybuch tornada",
    "Psionic Mass Dominate": "Masowa psioniczna dominacja", "Offensive Precognition": "Prekognicja ofensywna",
    "Expansion": "Rozrost", "Vigor": "Wigor", "Defensive Precognition": "Prekognicja obronna",
    "Animal Affinity": "Zwierzęca więź", "Thicken Skin": "Pogrubienie skóry", "Body Purification": "Oczyszczenie ciała",
    "Hustle": "Pośpiech", "Steadfast Perception": "Niezłomna percepcja", "Prowess": "Biegłość",
    "Weapon of Energy": "Broń z energii", "Adapt Body": "Przystosowanie ciała",
    "Righteous Wrath of the Faithful": "Słuszny gniew wiernych", "Metamorphosis": "Metamorfoza",
}
TRA0 = 1300


def moce():
    """lista: (nazwa, czar wzor, krag psiona, krag wojownika) w kolejnosci kregow"""
    d = {}
    for kol, lista in (("PSION", PSION), ("PSYWAR", PSYWAR)):
        for lv, xs in lista.items():
            for n, r in xs:
                m = d.setdefault(n, {"wzor": r, "PSION": 0, "PSYWAR": 0})
                assert m["wzor"] == r, n
                m[kol] = lv
    out = sorted(d.items(), key=lambda kv: (min(x for x in (kv[1]["PSION"], kv[1]["PSYWAR"]) if x), kv[0]))
    licz, wynik = {}, []
    for n, m in out:
        lv = min(x for x in (m["PSION"], m["PSYWAR"]) if x)
        i = licz.get(lv, 70)
        licz[lv] = i + 1
        assert i < 90
        wynik.append((n, m["wzor"], m["PSION"], m["PSYWAR"], f"SPWI{lv}{i}"))
    return wynik


def main():
    M_ = moce()
    tra = {"en": {TRA0: "In IWD2 this power works like the spell"}, "pl": {TRA0: "W IWD2 ta moc działa jak czar"}}
    for i, (n, w, ps, pw, res) in enumerate(M_):
        k = TRA0 + 1 + 2 * i
        lv_en = ", ".join(x for x in (f"Psion/Wilder {ps}" if ps else "", f"Psychic Warrior {pw}" if pw else "") if x)
        lv_pl = ", ".join(x for x in (f"Psion/Dziki talent {ps}" if ps else "", f"Wojownik psioniczny {pw}" if pw else "") if x)
        tra["en"][k], tra["en"][k + 1] = n, f"{n}\n(Psionic power)\nLevel: {lv_en}"
        tra["pl"][k], tra["pl"][k + 1] = PL[n], f"{PL[n]}\n(Moc psioniczna)\nPoziom: {lv_pl}"
    for lang, fn, enc in (("en", "english.tra", "cp1252"), ("pl", "polish.tra", "cp1250")):
        f = M + "/darksun_rasy/tra/" + fn
        s = open(f, "rb").read().decode(enc)
        for k, v in tra[lang].items():
            pat = re.compile(r"^@" + str(k) + r" = ~[^~]*~\n?", re.M)
            s = pat.sub("", s)
        s = s.rstrip("\n") + "\n" + "".join(f"@{k} = ~{v}~\n" for k, v in sorted(tra[lang].items()))
        open(f, "wb").write(s.encode(enc))
    blk = '''
// test62: moce psioniczne z wlasnymi nazwami i opisami (tools/iwd2_moce_psi.py). Kopia czaru gry (SPWI<krag>70..),
// opis = naglowek mocy + "dziala jak czar <nazwa z gry>" + opis czaru z gry (z TLK przy instalacji).
BEGIN ~TEST: moce psioniczne - wlasne nazwy i opisy mocy psiona, dzikiego talentu i wojownika psionicznego~ DESIGNATED 11
  REQUIRE_PREDICATE (GAME_IS ~iwd2~) ~Ten komponent dziala tylko w Icewind Dale 2.~
  REQUIRE_COMPONENT ~setup-darksun_rasy.tp2~ ~5~ ~Wymaga komponentu 5 (listy mocy PSION i PSYWAR w LISTSPLL).~
  DEFINE_PATCH_FUNCTION ds_moc_wiersz
    STR_VAR res = ~~ wzor = ~~ psion = ~0~ psywar = ~0~
  BEGIN
    COUNT_2DA_COLS ds_nc
    READ_2DA_ENTRIES_NOW ds_h (ds_nc - 1)
    COUNT_2DA_ROWS ds_nc ds_nr
    SET ds_kp = 0 - 1
    SET ds_kw = 0 - 1
    SET ds_kr = 0 - 1
    FOR (ds_c = 0; ds_c < (ds_nc - 1); ++ds_c) BEGIN
      READ_2DA_ENTRY_FORMER ds_h 0 ds_c ds_k
      PATCH_IF (~%ds_k%~ STRING_EQUAL_CASE ~PSION~) BEGIN SET ds_kp = ds_c + 1 END
      PATCH_IF (~%ds_k%~ STRING_EQUAL_CASE ~PSYWAR~) BEGIN SET ds_kw = ds_c + 1 END
      PATCH_IF (~%ds_k%~ STRING_EQUAL_CASE ~SPELL_RES_REF~) BEGIN SET ds_kr = ds_c + 1 END
    END
    PATCH_IF (ds_kr > 0) BEGIN
      FOR (ds_i = 0; ds_i < ds_nr; ++ds_i) BEGIN       // czar wzoru: bez kolumn mocy
        READ_2DA_ENTRY ds_i ds_kr ds_nc ds_v
        PATCH_IF (~%ds_v%~ STRING_EQUAL_CASE ~%wzor%~) BEGIN
          PATCH_IF (ds_kp > 0) BEGIN SET_2DA_ENTRY ds_i ds_kp ds_nc ~0~ END
          PATCH_IF (ds_kw > 0) BEGIN SET_2DA_ENTRY ds_i ds_kw ds_nc ~0~ END
        END
      END
    END
    PATCH_IF (INDEX_BUFFER (~%res%~) < 0) BEGIN
      TEXT_SPRINT ds_l ~%ds_nr%~
      FOR (ds_c = 0; ds_c < (ds_nc - 1); ++ds_c) BEGIN
        READ_2DA_ENTRY_FORMER ds_h 0 ds_c ds_k
        TEXT_SPRINT ds_v ~0~
        PATCH_IF (~%ds_k%~ STRING_EQUAL_CASE ~PSION~) BEGIN TEXT_SPRINT ds_v ~%psion%~ END
        PATCH_IF (~%ds_k%~ STRING_EQUAL_CASE ~PSYWAR~) BEGIN TEXT_SPRINT ds_v ~%psywar%~ END
        PATCH_IF (~%ds_k%~ STRING_EQUAL_CASE ~SPELL_RES_REF~) BEGIN TEXT_SPRINT ds_v ~%res%~ END
        TEXT_SPRINT ds_l ~%ds_l% %ds_v%~
      END
      INSERT_2DA_ROW ds_nr ds_nc ~%ds_l%~
    END
  END
'''
    for i, (n, w, ps, pw, res) in enumerate(M_):
        k = TRA0 + 1 + 2 * i
        blk += f'''  COPY_EXISTING ~{w}.SPL~ ~override/{res}.SPL~   // {n}
    READ_STRREF 0x08 ds_nz
    READ_STRREF 0x50 ds_op
    SPRINT ds_jak @{TRA0}
    SPRINT ds_t @{k + 1}
    SAY 0x08 @{k}
    WRITE_LONG 0x34 {min(x for x in (ps, pw) if x)}
    SAY_EVALUATED 0x50 ~%ds_t%%WNL%%WNL%%ds_jak% %ds_nz%.%WNL%%WNL%%ds_op%~
'''
    blk += "  COPY_EXISTING ~LISTSPLL.2DA~ ~override~\n"
    for n, w, ps, pw, res in M_:
        blk += f"    LPF ds_moc_wiersz STR_VAR res = ~{res}~ wzor = ~{w}~ psion = ~{ps}~ psywar = ~{pw}~ END\n"
    blk += "  BUT_ONLY\n"
    f = M + "/setup-darksun_rasy.tp2"
    s = open(f).read()
    i = s.find("\n// test62: moce psioniczne")
    if i >= 0:
        j = s.find("\nBEGIN ~", i + 10)
        s = s[:i] + (s[j:] if j >= 0 else "\n")
    s = s.rstrip("\n") + "\n" + blk
    open(f, "w").write(s)
    for m in M_:
        print(*m)


if __name__ == "__main__":
    main()
