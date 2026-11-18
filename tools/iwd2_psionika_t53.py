"""test53: psionika jako podklasy zaklinacza (psion, wilder, psychic warrior) + klasa prestizowa Psiologist.
Moce psioniczne (Expanded Psionics Handbook / Dark Sun 3.5e) -> najblizsze czary IWD2 (kolumny LISTSPLL PSION, PSYWAR).
Uruchamiany raz na repozytorium; dopisuje do plikow paczki i tp2 (sprawdza, czy juz dopisane)."""
import re, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = R + '/mod/darksun_rasy'
# moc (opis) -> resref czaru IWD2 : krag mocy
PSION = {1: [('Mind Thrust', 'SPWI112'), ('Force Screen', 'SPWI114'), ('Inertial Armor', 'SPWI102'), ('Psionic Charm', 'SPWI104'),
             ('Demoralize', 'SPPR114'), ('Hypnotism', 'SPWI116'), ('Energy Ray', 'SPWI103'), ('Entangling Ectoplasm', 'SPWI101'),
             ('Crystal Shard', 'SPWI118'), ('Precognition', 'SPWI209')],
         2: [('Ego Whip', 'SPWI226'), ('Concealing Amorpha', 'SPWI201'), ('Cloud Mind', 'SPWI206'), ('Energy Stun', 'SPWI227'),
             ('Swarm of Crystals', 'SPWI220'), ('Thought Shield', 'SPPR219'), ('Id Insinuation', 'SPWI205')],
         3: [('Energy Bolt', 'SPWI308'), ('Dispel Psionics', 'SPWI302'), ('Body Adjustment', 'SPPR401'), ('Psionic Blast', 'SPWI306'),
             ('Hostile Empathic Transfer', 'SPWI314'), ('Energy Burst', 'SPWI304')],
         4: [('Energy Ball', 'SPWI404'), ('Psionic Dominate', 'SPWI507'), ('Psionic Freedom of Movement', 'SPPR403'),
             ('Inertial Barrier', 'SPWI408'), ('Mental Barrier', 'SPWI406'), ('Death Urge', 'SPWI401')],
         5: [('Psychic Crush', 'SPPR515'), ('Power Resistance', 'SPPR519'), ('Tower of Iron Will', 'SPPR716'),
             ('Ectoplasmic Shambler', 'SPWI503'), ('Psionic Hold Monster', 'SPWI508')],
         6: [('Disintegrate', 'SPWI607'), ('Breath of the Black Dragon', 'SPWI605'), ('Temporal Acceleration', 'SPWI623')],
         7: [('Psionic Finger of Death', 'SPWI702'), ('Insanity', 'SPWI509'), ('Decerebrate', 'SPWI705'),
             ('Energy Conversion', 'SPWI712'), ('Mass Cloud Mind', 'SPWI709')],
         8: [('Psionic Mind Blank', 'SPWI804'), ('Iron Body', 'SPWI807'), ('Ultrablast', 'SPWI805')],
         9: [('Microcosm', 'SPWI903'), ('Tornado Blast', 'SPWI908'), ('Psionic Mass Dominate', 'SPWI911')]}
PSYWAR = {1: [('Inertial Armor', 'SPWI102'), ('Force Screen', 'SPWI114'), ('Offensive Precognition', 'SPPR215'),
              ('Expansion', 'SPWI214'), ('Vigor', 'SPPR115'), ('Defensive Precognition', 'SPWI209')],
          2: [('Animal Affinity', 'SPWI223'), ('Concealing Amorpha', 'SPWI201'), ('Thicken Skin', 'SPPR202'), ('Body Purification', 'SPPR212')],
          3: [('Hustle', 'SPWI305'), ('Body Adjustment', 'SPPR401'), ('Steadfast Perception', 'SPWI203'), ('Prowess', 'SPPR312')],
          4: [('Inertial Barrier', 'SPWI408'), ('Psionic Freedom of Movement', 'SPPR403'), ('Weapon of Energy', 'SPPR206')],
          5: [('Adapt Body', 'SPWI712'), ('Righteous Wrath of the Faithful', 'SPPR507')],
          6: [('Metamorphosis', 'SPWI616'), ('Breath of the Black Dragon', 'SPWI605')]}

def lista(d):
    return ' '.join(f'{r}:{lv}' for lv, xs in d.items() for _, r in xs)

KITY = [  # (nr, nazwa, CLAB, tra, DSKLPROG, pkt/2, SKILCOST wzor, featclas rows)
    (69, 'WILDER', 'CLABDS69', 1071, ('HPROG', 'BAATMAG', 'SAVEWIZ', '*', 'PSION'), 2, 'SOR', []),
    (70, 'PSY_WARRIOR', 'CLABDS70', 1081, ('HPPRS', 'BAATNFG', 'SAVEWAR', '*', 'PSYWAR'), 1, 'FTR', [0, 1, 4, 7, 10, 13, 16, 19]),
    (71, 'PSIOLOGIST', 'CLABDS71', 1091, ('HPWIZ', 'BAATMAG', 'SAVEWIZ', '*', '*'), 1, 'SOR', []),
]
TXT = {
 'en': {271: 'psion', 272: 'Psion', 273: "PSION: On Athas the power of the mind is as common as magic is feared. Psions train the Way to bend matter and thought with will alone.\n\nSorcerer subclass (Dark Sun 3.5e / Expanded Psionics Handbook). Hit Die: d4. Base attack bonus: 1/2. Good saving throws: Will. Skill points: 2 per level.\n\nPowers: psion power list - psionic powers represented by the nearest spells of the game (e.g. Mind Thrust = Magic Missile, Inertial Armor = Mage Armor, Energy Bolt = Lightning Bolt), cast like sorcerer spells.",
        274: 'Psion: power points, disciplines and augmenting powers - powers are cast like sorcerer spells.',
        1071: 'wilder', 1072: 'Wilder', 1073: "WILDER: Psionic talents who never trained in the Way; their power erupts from raw emotion.\n\nSorcerer subclass (Dark Sun 3.5e / Expanded Psionics Handbook). Hit Die: d6. Base attack bonus: 1/2. Good saving throws: Will. Skill points: 4 per level.\n\nPowers: psion power list (nearest spells of the game), cast like sorcerer spells.",
        1074: 'Wilder: Wild Surge, Psychic Enervation, Elude Touch, Volatile Mind - description only.',
        1081: 'psychic warrior', 1082: 'Psychic Warrior', 1083: "PSYCHIC WARRIOR: Warriors who turn the power of the mind on their own bodies, enhancing speed, strength and perception in battle.\n\nSorcerer subclass (Dark Sun 3.5e / Expanded Psionics Handbook). Hit Die: d8. Base attack bonus: 3/4. Good saving throws: Fortitude. Skill points: 2 per level. Bonus feats at 1st, 2nd and every 3 levels.\n\nPowers: psychic warrior power list (powers of levels 1-6 as the nearest spells of the game: Inertial Armor, Expansion, Thicken Skin, Hustle, Inertial Barrier...).",
        1084: 'Psychic Warrior: power points and augmenting powers - powers are cast like sorcerer spells.',
        1091: 'psiologist', 1092: 'Psiologist', 1093: "PSIOLOGIST (prestige class, Dark Sun 3.5e): Scholars of the Way who study psionics in the academies of Athas.\n\nRequirements: sorcerer level 10 (5th-level powers); lawful. Hit Die: d4. Base attack bonus: 1/2. Good saving throws: Will. Each level adds +1 level of sorcerer spellcasting (powers).",
        1094: 'Psiologist: Psiologism, Psionic Acumen, Psionic Rationalization, Forethought - description only.'},
 'pl': {271: 'psion', 272: 'Psion', 273: "PSION: Na Athasie moc umysłu jest równie powszechna, jak magia jest znienawidzona. Psioni ćwiczą Drogę, by naginać materię i myśli samą wolą.\n\nPodklasa zaklinacza (Dark Sun 3.5e / Expanded Psionics Handbook). Kość wytrzymałości: k4. Bazowa premia do ataku: 1/2. Dobre rzuty obronne: Wola. Punkty umiejętności: 2 na poziom.\n\nMoce: lista mocy psiona – moce psioniczne jako najbliższe czary gry (np. Pchnięcie umysłu = Magiczny pocisk, Pancerz inercyjny = Zbroja maga, Grom energii = Błyskawica), rzucane jak czary zaklinacza.",
        274: 'Psion: punkty mocy, dyscypliny i wzmacnianie mocy – moce rzucane jak czary zaklinacza.',
        1071: 'dziki talent', 1072: 'Dziki talent', 1073: "DZIKI TALENT: Psionicy, którzy nigdy nie ćwiczyli Drogi; ich moc wybucha z surowych emocji.\n\nPodklasa zaklinacza (Dark Sun 3.5e / Expanded Psionics Handbook). Kość wytrzymałości: k6. Bazowa premia do ataku: 1/2. Dobre rzuty obronne: Wola. Punkty umiejętności: 4 na poziom.\n\nMoce: lista mocy psiona (najbliższe czary gry), rzucane jak czary zaklinacza.",
        1074: 'Dziki talent: Dziki przypływ, Psychiczne wyczerpanie, Unik przed dotykiem, Niestały umysł – tylko opis.',
        1081: 'wojownik psioniczny', 1082: 'Wojownik psioniczny', 1083: "WOJOWNIK PSIONICZNY: Wojownicy, którzy kierują moc umysłu na własne ciało, wzmacniając w walce szybkość, siłę i zmysły.\n\nPodklasa zaklinacza (Dark Sun 3.5e / Expanded Psionics Handbook). Kość wytrzymałości: k8. Bazowa premia do ataku: 3/4. Dobre rzuty obronne: Wytrwałość. Punkty umiejętności: 2 na poziom. Premiowe atuty na 1., 2. i co 3 poziomy.\n\nMoce: lista mocy wojownika psionicznego (moce 1.–6. kręgu jako najbliższe czary gry: Pancerz inercyjny, Powiększenie, Pogrubienie skóry, Pośpiech, Bariera inercyjna...).",
        1084: 'Wojownik psioniczny: punkty mocy i wzmacnianie mocy – moce rzucane jak czary zaklinacza.',
        1091: 'psiolog', 1092: 'Psiolog', 1093: "PSIOLOG (klasa prestiżowa, Dark Sun 3.5e): Badacze Drogi, którzy zgłębiają psionikę w akademiach Athasu.\n\nWymagania: 10. poziom zaklinacza (moce 5. kręgu); charakter praworządny. Kość wytrzymałości: k4. Bazowa premia do ataku: 1/2. Dobre rzuty obronne: Wola. Każdy poziom dodaje +1 poziom czarów (mocy) zaklinacza.",
        1094: 'Psiolog: Psiologizm, Bystrość psioniczna, Racjonalizacja, Przezorność – tylko opis.'}}

def main():
    # --- tra
    for lang, fn, enc in (('en', 'english.tra', 'cp1252'), ('pl', 'polish.tra', 'cp1250')):
        f = M + '/darksun_rasy/tra/' + fn
        s = open(f, 'rb').read().decode(enc)
        nl = '\r\n' if '\r\n' in s else '\n'
        for k, v in TXT[lang].items():
            v = v.replace('\n', nl)
            pat = re.compile(r'^@' + str(k) + r' = ~[^~]*~', re.M)
            if pat.search(s): s = pat.sub(lambda m: f'@{k} = ~{v}~', s, count=1)
            else: s = s.rstrip('\r\n') + nl + f'@{k} = ~{v}~' + nl
        b = s.encode(enc)
        open(f, 'wb').write(b)
    # --- DSKLPROG
    f = M + '/darksun_rasy/2da/DSKLPROG.2DA'; s = open(f, newline='').read()
    s = re.sub(r'(?m)^SORCERER_DS\s.*$', 'SORCERER_DS   HPWIZ     BAATMAG   SAVEWIZ   *         PSION', s)
    for nr, n, c, t, pr, *_ in KITY:
        if not re.search(r'(?m)^' + n + r'\s', s):
            s = s.rstrip('\n') + '\n' + f'{n:<16}' + ''.join(f'{x:<10}' for x in pr).rstrip() + '\n'
    open(f, 'w', newline='').write(s)
    # --- DSPREST: psiolog
    f = M + '/darksun_rasy/2da/DSPREST.2DA'; s = open(f, newline='').read()
    if not re.search(r'(?m)^PSIOLOGIST\s', s):
        s = s.rstrip('\n') + '\n' + f"{'PSIOLOGIST':<16}{0:<7}{0:<5}{10:<7}{10:<13}{'*':<12}{10:<11}{0:<6}{0:<7}{0:<7}{0:<7}{0:<8}{0:<7}{0:<8}{0:<7}{0:<3}10" + '\n'
    open(f, 'w', newline='').write(s)
    # --- CLAB (FA)
    for nr, n, c, t, *_ in KITY + [(7, 'SORCERER_DS', 'CLABDS08', 271)]:
        fa = t + 3
        r = '2DA V1.0\n****\n          ' + '  '.join(str(i) for i in range(1, 31)) + f'\nABILITY1  FA_%fa_{fa}%  ' + '  '.join(['****'] * 29) + '\n'
        open(M + f'/darksun_rasy/2da/{c}.2DA', 'w', newline='').write(r)
    # --- tp2
    f = M + '/setup-darksun_rasy.tp2'; s = open(f, encoding='latin1').read()
    if 'PSY_WARRIOR' in s: return
    def ins(a, b):
        nonlocal s
        assert s.count(a) == 1, a[:60]
        s = s.replace(a, a + b)
    ins('    68, 1, SHADOW_ADEPT   , CLABDS68, 45 => 1061\n', '    // test53: psionika - podklasy zaklinacza (lista mocy = najblizsze czary gry) i klasa prestizowa Psiologist\n' +
        ''.join(f"    {nr}, {10 if nr < 71 else 1}, {n:<15}, {c}, {nr + 1:02X} => {t}\n" for nr, n, c, t, *_ in KITY))
    s = s.replace('  OUTER_SET ds_n_kitow = 69', '  OUTER_SET ds_n_kitow = 72')
    ins('  OUTER_SET $ds_str(~1063~) = RESOLVE_STR_REF(@1063)\n', '  // test53\n' + ''.join(f"  OUTER_SET $ds_str(~{t + j}~) = RESOLVE_STR_REF(@{t + j})\n" for _, _, _, t, *_ in KITY for j in range(3)))
    ins('  APPEND ~ALIGNMNT.2DA~ ~SHADOW_ADEPT\t1\t1\t1\t1\t1\t1\t1\t1\t1~ UNLESS ~SHADOW_ADEPT~\n',
        '  APPEND ~ALIGNMNT.2DA~ ~WILDER\t1\t1\t1\t1\t1\t1\t1\t1\t1~ UNLESS ~WILDER~\n'
        '  APPEND ~ALIGNMNT.2DA~ ~PSY_WARRIOR\t1\t1\t1\t1\t1\t1\t1\t1\t1~ UNLESS ~PSY_WARRIOR~\n'
        '  APPEND ~ALIGNMNT.2DA~ ~PSIOLOGIST\t1\t1\t1\t0\t0\t0\t0\t0\t0~ UNLESS ~PSIOLOGIST~\n')
    ins('        LPF ds_wiersz_kitu STR_VAR wiersz = ~SHADOW_ADEPT~ wzor = ~BARBARIAN~ END\n',
        '        LPF ds_wiersz_kitu STR_VAR wiersz = ~WILDER~ wzor = ~SORCERER~ END\n'
        '        LPF ds_wiersz_kitu STR_VAR wiersz = ~PSY_WARRIOR~ wzor = ~SORCERER~ END\n'
        '        LPF ds_wiersz_kitu STR_VAR wiersz = ~PSIOLOGIST~ wzor = ~BARBARIAN~ END\n')
    fc = '    // test53: psionika\n'
    for nr, n, c, t, pr, sp, sk, feat in KITY:
        fc += f"    LPF ds_kolumna_zera STR_VAR kol = ~{n}~ wzor = ~{'BARBARIAN' if nr == 71 else 'SORCERER'}~ END\n" + ''.join(f"    LPF ds_kol_wart INT_VAR wiersz = {r} wart = 1 END\n" for r in feat)
    ins('    LPF ds_kolumna_zera STR_VAR kol = ~SHADOW_ADEPT~ wzor = ~BARBARIAN~ END\n', fc)
    sp = '    // test53: psionika (wartosc = punkty / 2)\n' + ''.join(f"    LPF ds_kolumna_kitu STR_VAR kol = ~{n}~ wzor = ~{'BBN' if nr == 71 else 'SOR'}~ END\n    LPF ds_kol_wart INT_VAR wiersz = 0 wart = {p2} END\n" for nr, n, c, t, pr, p2, *_ in KITY)
    sp += "    LPF ds_kolumna_kitu STR_VAR kol = ~SORCERER_DS~ wzor = ~SOR~ END\n    LPF ds_kol_wart INT_VAR wiersz = 0 wart = 1 END\n"
    ins('    LPF ds_kolumna_kitu STR_VAR kol = ~SHADOW_ADEPT~ wzor = ~BBN~ END\n    LPF ds_kol_wart INT_VAR wiersz = 0 wart = 1 END\n', sp)
    sc = '    // test53: psionika - wojownik psioniczny: umiejetnosci wojownika + Koncentracja\n' + ''.join(f"    LPF ds_kolumna_kitu STR_VAR kol = ~{n}~ wzor = ~{sk}~ END\n" for nr, n, c, t, pr, p2, sk, f_ in KITY)
    sc += '    LPF ds_kolumna_kitu STR_VAR kol = ~PSY_WARRIOR~ wzor = ~FTR~ END\n'
    ins('    LPF ds_kolumna_kitu STR_VAR kol = ~SHADOW_ADEPT~ wzor = ~WIZ~ END\n', sc)
    s = s.replace("    LPF ds_kolumna_kitu STR_VAR kol = ~PSY_WARRIOR~ wzor = ~FTR~ END\n    LPF ds_kolumna_kitu STR_VAR kol = ~PSIOLOGIST~ wzor = ~SOR~ END\n    LPF ds_kolumna_kitu STR_VAR kol = ~PSY_WARRIOR~ wzor = ~FTR~ END\n",
                  "    LPF ds_kolumna_kitu STR_VAR kol = ~PSY_WARRIOR~ wzor = ~FTR~ END\n    LPF ds_kol_wart INT_VAR wiersz = 3 wart = 1 END\n    LPF ds_kolumna_kitu STR_VAR kol = ~PSIOLOGIST~ wzor = ~SOR~ END\n")
    ins('  OUTER_SET fa_1064 = RESOLVE_STR_REF(@1064)\n', '  OUTER_SET fa_274 = RESOLVE_STR_REF(@274)\n' + ''.join(f"  OUTER_SET fa_{t + 3} = RESOLVE_STR_REF(@{t + 3})\n" for _, _, _, t, *_ in KITY))
    a = '~CLABDS67~ ~CLABDS68~ BEGIN'
    assert s.count(a) == 1
    s = s.replace(a, '~CLABDS67~ ~CLABDS68~\n                       ~CLABDS69~ ~CLABDS70~ ~CLABDS71~ ~CLABDS08~ BEGIN')
    # CLABDS08 byl kopiowany bez EVALUATE_BUFFER - teraz w petli z EVALUATE_BUFFER
    s = s.replace("  COPY ~darksun_rasy/2da/CLABDS08.2DA~ ~override~        // psionik: Spell Shield (GA_SPIN243)\n",
                  "  // CLABDS08 (psion, test53) - w petli tablic z tekstami FA (EVALUATE_BUFFER)\n")
    # LISTSPLL
    blk = ''
    for kol, d, opis in (('PSION', PSION, 'psion i wilder'), ('PSYWAR', PSYWAR, 'wojownik psioniczny')):
        blk += f'''  // test53: kolumna {kol} ({opis}) - moce psioniczne jako najblizsze czary gry (tools/iwd2_psionika_t53.py)
  OUTER_TEXT_SPRINT ds_psi ~ {lista(d)} ~
  COPY_EXISTING ~LISTSPLL.2DA~ ~override~
    PATCH_IF (INDEX_BUFFER (~{kol}~) < 0) BEGIN
      LPF ds_kolumna_kitu STR_VAR kol = ~{kol}~ wzor = ~SOR~ END
      COUNT_2DA_COLS ds_nc
      COUNT_2DA_ROWS ds_nc ds_nr
      FOR (ds_i = 0; ds_i < ds_nr; ++ds_i) BEGIN
        READ_2DA_ENTRY ds_i 8 ds_nc ds_res
        SET ds_lv = 0
        FOR (ds_k = 1; ds_k < 10; ++ds_k) BEGIN
          PATCH_IF (INDEX (~ %ds_res%:%ds_k% ~ ~%ds_psi%~) >= 0) BEGIN SET ds_lv = ds_k END
        END
        SET_2DA_ENTRY ds_i (ds_nc - 1) ds_nc ~%ds_lv%~
      END
    END
  BUT_ONLY
'''
    a = '  // test47: kolumna ADEPT'
    assert s.count(a) == 1
    s = s.replace(a, blk + a)
    s = s.replace('VERSION ~test53-2026-11-18~', 'VERSION ~test53-2026-11-18~')
    open(f, 'w', encoding='latin1').write(s)

if __name__ == '__main__':
    main()
    print('ok')
