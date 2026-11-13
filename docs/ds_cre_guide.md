# Konwersja postaci Dark Sun → CRE IWD2: propozycja zmian w przewodniku CRE z BG1

Punkt wyjścia: przewodnik CRE z BGtoIWD2 (gałąź `aktualizacja-reguly-cre-gui`). Składa się z `entities/cre_rules.py`, tabel `out/cre_guide/*.csv` i zakładki `guide` w `docs/cre_conversion_guide_uzupelniony.xlsx`. Konwerter liczy CRE V2.2 od zera z reguł i tabel 2DA IWD2. Kroki z zakładki `guide` (3–27) zostają, zmienia się **wejście**: zamiast CRE V1.0 z BG1 są rekordy RDFF Dark Sun (blok walki 58 B + blok postaci 71 B, `docs/darksun_formaty.md`, `build/darksun/creatures.csv`).
Zasada bez zmian: reguły i tabele wiedzy, nadpisania właściciela nad regułami, raport `*_unresolved.csv`.

## 1. Wejście: pola CRE BG1 → pola Dark Sun
| Krok / pole przewodnika | BG1 (CRE V1.0) | Dark Sun (RDFF) | Zmiana |
|---|---|---|---|
| imię | strref | walka `name[18]` | SAY z tekstu |
| rasa (krok 3) | RACE.IDS | postać `race` 1–8, 9 nieumarły, 12 potwór, 14 pozaplanarny | nowa tabela `ds_race_map.csv` (niżej) |
| klasa i poziomy (kroki 3–5) | CLASS.IDS + 3 poziomy | `real_class[3]`, `level[3]`; kody 1–20 | nowa tabela `ds_class_map.csv` |
| klasa z animacji (krok 5) | nazwa animacji | brak; ikona walki `icon` | krok pominięty; klasa zawsze z `real_class` |
| cechy (krok 8) | CRE | `stats[6]` (te same w obu blokach) | 1:1, szablon `general_templates` tylko dla potworów bez cech |
| charakter | ALIGNMEN.IDS | `alignment` 1–9 (LG…CE), 0 brak | 1→0x11, 2→0x12, 3→0x13, 4→0x21, 5→0x22, 6→0x23, 7→0x31, 8→0x32, 9→0x33; 0 → wg strony (`allegiance`) |
| strona (EA) | EA.IDS | `allegiance` 1 / 2 / 4 | propozycja: 1 → drużyna/sprzymierzeniec, 2 → wróg, 4 → neutralny; do potwierdzenia na kilku postaciach |
| HP (krok 13) | CRE | `hp`, `base_hp`, `high_hp` | HP liczone regułą IWD2 (kość klasy + CON); HP Dark Sun tylko jako kontrola (tolerancja 30% jak w BG1) |
| KP | AC 2E | `ac` / `base_ac` (2E, malejąco) | KP IWD2 = 20 − KP 2E; pancerz naturalny = KP IWD2 − 10 − ZRĘ − pancerz z ekwipunku |
| BAB (krok 15) | THAC0 | `thac0` | BAB z tabel klas IWD2; kontrola: 20 − THAC0 |
| rzuty (krok 16) | 5 rzutów 2E | `saving_throw[5]` | z tabel IWD2 (bez zmian); wartości 2E tylko do raportu |
| ataki naturalne | przedmiot | `num_attacks`, `num_dice/sides/bonuses` | potwór bez broni: wygenerowany ITM ataku naturalnego (`DSATKnn`) z tych kości |
| odporność na magię | CRE | `magic_resistance` | 1:1 (procent) |
| rozmiar | — | `size` (0, 1, 8, 9, 17) | do rozpoznania; wpływa na wybór animacji potwora |
| ekwipunek (krok 23) | sloty CRE | bloki przedmiotów RDFF: `load_action` 2 założony, 4 plecak | ITM wg `docs/ds_itm_reguly.md`; sloty z `placement` |
| czary (kroki 11, 27) | znane i zapamiętane | `spell_group` (11 grup) | grupa → lista czarów IWD2 (tabela `ds_spell_groups.csv`, do zbudowania z `spells.csv`) |
| psionika | — | `psp`, `base_psp`, `psi_group` | **nowe**: moce psioniczne jako zdolności wrodzone (SPIN) z liczbą użyć z PSP; psionik → zdolności specjalne |
| XP za zabicie | CRE | brak (jest `current_xp` postaci) | z MONCRATE (krok 18) jak dla BG1 |
| skrypty (`script_map`) | BCS | wyzwalacze GPL: rozmowa, oględziny, atak | Override: BAF wygenerowany z wyzwalaczy GPL; dialog: DLG z `dialogs.csv` |
| dźwięki | soundset | `sound_fx`, `attack_sound` | soundset IWD2 wg rasy i płci (tabela) |
| portret | BMP | PORT (GPLDATA, 112) | portrety L/M/S z PORT, tylko postacie z dialogiem |

## 2. Nowe tabele w `out/ds_guide/` (propozycja)
**`ds_class_map.csv`** (kody klas z DSUN.EXE; propozycja do decyzji):
| DS | klasa | IWD2 | kit / uwagi |
|---|---|---|---|
| 1–4 | kapłan (sfera żywiołu) | CLERIC | `CLERIC_DS` (kapłan żywiołu; dziś ziemia, inne sfery jako kolejne kity) |
| 5–8 | druid | DRUID | — |
| 9 | wojownik | FIGHTER | — |
| 10 | gladiator | BARBARIAN | `BARBARIAN_DS` albo FIGHTER; decyzja właściciela |
| 11 | zachowawca (preserver) | WIZARD | — |
| 12, 20 | psionik | SORCERER | psionika jako zdolności wrodzone; CHA zamiast INT/WIS |
| 13–16 | tropiciel | RANGER | — |
| 17 | złodziej | ROGUE | — |
| 18 | mag NPC (np. defiler) | WIZARD | przyszły kit splugawiacza |
| 19 | kapłan NPC (templariusz) | PALADIN | `PALADIN_DS` (Zakon templariuszy) albo CLERIC |
| 0 | brak (potwór) | — | ścieżka potworów (krok 11, `general_templates`) |

**`ds_race_map.csv`**: 1 człowiek → HUMAN, 2 krasnolud → DWARF, 3 elf → ELF, 4 półelf → HALF_ELF, 5 półolbrzym → HALF_ORC (brak olbrzymów w IWD2; większa animacja), 6 niziołek → HALFLING, 7 mul → HALF_ORC + podrasa MUL (komponent 1 `darksun_rasy`), 8 thri-kreen → potwór (osobna animacja owada). 9, 12, 14 → potwory po nazwie (MONSTER, UNDEAD…), szablon `general_templates` wg kategorii.

**`ds_anim_map.csv`**: animacja IWD2 dla (rasa, płeć, klasa) postaci i dla potworów po nazwie. Odpowiada `anim_map.csv` / `anim_bam_map.csv` z BG1. Dark Sun nie ma animacji postaci w formacie IE, więc tabela jest ręczną wiedzą.

## 3. Zmiany w krokach przewodnika
- **Krok 3 (klasa):** `real_class` zamiast CLASS.IDS. Multiklasa Dark Sun (do 3 klas) → poziomy w kilku klasach IWD2, z poziomem efektywnym wg tej samej formuły co dla BG1.
- **Krok 5 (klasa z animacji):** usunięty.
- **Krok 8 (cechy):** cechy zawsze z Dark Sun (Athas ma wysokie cechy; brak przycinania do 18 poza wartością CRE).
- **Krok 11 (czary bez klasy):** dla psioników i potworów z `psi_group` zamiast czarów moce psioniczne.
- **Krok 13 (HP):** reguła IWD2; raport różnicy względem `hp` Dark Sun.
- **Krok 19–20 (odporności):** `special_defense` jest zawsze 0. `special_attack` (31, 13, 5, 19…) → efekty broni naturalnej (trucizna, paraliż); tabela kodów do rozpoznania.
- **Krok 23 (ekwipunek):** z bloków przedmiotów RDFF, nie z wzorca IWD2.
- **Krok 27 (czary):** grupy czarów Dark Sun → czary IWD2 po nazwie (dopasowanie po nazwie i kręgu, jak w BG1).
- **Nowy krok P (psionika):** `psi_group` → zestaw SPIN, liczba użyć z PSP (np. 1 użycie / 10 PSP).
- **Skrypty:** `script_map.csv` bez zmian co do slotów. Override wypełnia BAF z wyzwalaczy GPL (atak → `HostileTo`, brak rozkazów → stanie), Dialog = DLG z `dialogs.csv`.

## 4. Do decyzji właściciela
1. Gladiator: BARBARIAN_DS czy FIGHTER.
2. Templariusz (19): PALADIN_DS czy CLERIC.
3. Psionika: zdolności wrodzone (propozycja) czy czary zaklinacza.
4. Półolbrzym: HALF_ORC czy nowa podrasa / potwór.
5. Znaczenie `allegiance` 1/2/4 (propozycja w tabeli).
