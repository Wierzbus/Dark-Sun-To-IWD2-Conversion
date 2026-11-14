# Jak dodać do IWD2 rasę, podrasę, podklasę i zdolności – przewodnik po tabelach (stan: test22, 2026-11-14)

Dotyczy exe z paczki 2 (`setup-darksun_rasy`, komponent 0: `IWD2_DS.exe` / `IWD2_<W>_DS.exe`). Szczegóły łatek:
`docs/iwd2_exe_rasy_klasy.md` (sekcje 7–11). Wszystkie tabele są w `override` (WeiDU), teksty przez `.tra` (`@numer`).
Zasada wspólna dla tabel `DS*` i `RL*`: **brak tabeli, wiersza, kolumny albo wartość `*` = zachowanie oryginalnej gry.**
Tabele są czytane przy pierwszym użyciu – po zmianie w `override` uruchom grę od nowa.

---------------------------------------------------------------------------------------------------------------------

## 0. Co jest możliwe, a co nie

| Co | Stan |
|---|---|
| Nowa **rasa bazowa** (8. przycisk w oknie ras) | **niemożliwe** bez dużej przebudowy: 7 ras w tablicach skoków exe, okno ras pełne |
| Nowa **podrasa** w miejscu już otwartym: `HALF_ORC_MUL` (mul), `HALF_ELF_DS` (półelf atasyjski) | **tylko tabele** (sekcja 1) |
| Nowa podrasa w innym miejscu (np. 3. podrasa gnoma) | tabele + **łatka exe** (sekcja 1.4) |
| Zdolności rasy (wrodzone czary, efekty, premie zależne od poziomu postaci) | **tylko tabele**: RLAB (sekcja 2) |
| Cechy walki rasy (widzenie w ciemności, wrogowie rasy, olbrzymy, broń miotana, odporność na magię) | **tylko tabele**: DSRASY, DSRWROG (sekcja 3) |
| Nowa **klasa bazowa** | **niemożliwe**: 11 klas na stałe w formacie CRE (osobny poziom każdej klasy) i w setkach miejsc exe |
| **Podklasa** (kit) | 8 miejsc w exe (bity `0x01000000`–`0x80000000`), **wszystkie zajęte** przez podklasy DS – zmiana podklasy = tabele + teksty (sekcja 4); zmiana nazwy wiersza albo klasy bazowej miejsca = przebudowa exe (`podklasy.asm`) |
| Zdolności klasy / podklasy wg poziomu | **tylko tabele**: CLAB (sekcja 5) |
| Progi zdolności klas (Unik, Uncanny Dodge, atak z zaskoczenia, ulubiony wróg, aura) | **tylko tabele**: DSKLASY, DSSNEAK, DSWROG (sekcja 6) |
| Kość PW, premia do ataku, rzuty obronne **klasy i podklasy** | **tylko tabele**: DSKLPROG (sekcja 7) – wiersz podklasy, a bez niego wiersz klasy bazowej |

---------------------------------------------------------------------------------------------------------------------

## 1. Nowa podrasa

Nazwa wiersza podrasy (np. `HALF_ORC_MUL`) łączy wszystkie tabele – exe zwraca ją z `GetRaceRow(rasa, podrasa)`.
Numer podrasy (ID) to 0 (czysta), 1, 2.

### 1.1 Wolne miejsca w exe (od paczki 2)
| Rasa (nr) | Podrasa | Nazwa wiersza | Napis na karcie postaci (strref w exe, wpisuje WeiDU) | Komponent |
|---|---|---|---|---|
| HALFORC (7) | 1 | `HALF_ORC_MUL` | `WRITE_LONG 0x144FE7` (instrukcja `mov eax, strref` pod 0x544FE6) | 1 |
| HALF_ELF (3) | 1 | `HALF_ELF_DS` | `WRITE_LONG 0x144EC7` (0x544EC6) | 3 |

### 1.2 Tabele podrasy – dopisz wiersz o nazwie podrasy
| Plik | Co dopisać | Uwagi |
|---|---|---|
| `SRLIST.2DA` | `<nr> <NAZWA> <LOWER> <MIXED> <HELP> <ID> <włosy> <skóra>` | `nr` = kolejny numer wiersza; LOWER/MIXED/HELP = strrefy (`RESOLVE_STR_REF(@...)`); ID = numer podrasy; palety np. `HAIRNORM SKINNORM` |
| `SR_<rasa>.2DA` (SR_HO, SR_HE, SR_D, SR_E, SR_G, SR_H, SR_HF) | `<kolejna etykieta> <nr wiersza SRLIST>` | lista przycisków w oknie podras (okno 54, przyciski 1–4) |
| `SUBRACE.IDS` | `0x000R000P NAZWA` | R = rasa, P = podrasa, np. `0x00070001 HALF_ORC_MUL` |
| `ABRACEAD.2DA` | modyfikatory cech: SIŁ ZRĘ KON INT MĄD CHA | |
| `ABRACERQ.2DA` | min/maks każdej cechy (12 kolumn) | |
| `RACESPAB.2DA` | plik czarów wrodzonych (`SPECIAL_ABILITIES_FILE`) albo `*` | plik 2DA: `SPELL NUM_PER_DAY` (np. SPCH_T) – stała liczba użyć, bez poziomów; zdolności zależne od poziomu → RLAB |
| `RACERSMD.2DA` | odporności (11 kolumn) | |
| `SAVERACE.2DA` | premie FORTITUDE REFLEX WILL | |
| `SKILLRAC.2DA` | premie do umiejętności | |
| `STRTXP.2DA` | startowe PD (zwykle 0) | |
| `DSRASY.2DA` | RLAB, DARKVISION, GIANT_AC, THROWN, SR_LEVEL | sekcja 3; bez wiersza – oryginał |
| `DSRWROG.2DA` | BONUS, ABERRATION, E1–E6 | sekcja 3; bez wiersza – brak premii przeciw wrogom |
| `RL<nazwa>.2DA` | tablica zdolności rasy | sekcja 2 (tylko gdy DSRASY wskazuje ją w RLAB) |

**Nie obsługiwane:** `FEATS.2DA` i `SKILLS.2DA` mają **kolumny** ras wybierane przez exe po numerze – nowa podrasa
dostaje wartości domyślne (bez rasowych atutów / premii z tych tabel).

### 1.3 Przykład WeiDU (jak w komponencie 1 – mul)
```
APPEND ~ABRACEAD.2DA~ ~HALF_ORC_MUL   2  0  2  -2  0  -2~ UNLESS ~HALF_ORC_MUL~
// DSRASY.2DA instaluje komponent 4 (wiersz HALF_ORC_MUL juz jest); dla nowej podrasy - dopisanie wiersza:
APPEND ~DSRASY.2DA~   ~NOWA_PODRASA   RLNOWA  1  0  0  0~ UNLESS ~NOWA_PODRASA~
COPY ~darksun_rasy/2da/RLNOWA.2DA~ ~override~
```
(SRLIST i SR_<rasa> – z wyszukaniem istniejącego wiersza, patrz komponent 1 / 3 w `setup-darksun_rasy.tp2`.)

### 1.4 Podrasa w nowym miejscu (wymaga exe)
Trzeba (wzór: `asm/halforc.asm`, `asm/halfelf.asm`, `tools/iwd2_podklasy_exe.py`):
1. `GetRaceRow` 0x541940 – gałąź rasy (tablica skoków 0x541BFC) zwraca nową nazwę dla nowego ID (zamiast asercji);
2. nazwa podrasy na karcie postaci – funkcja 0x544xxx (`mov eax, strref` + skok, jak 0x544FE6 / 0x544EC6);
3. przycisk rasy otwiera okno podras – tablica skoków 0x61C5xx/0x61C6xx (0x61C640 półelf, 0x61C644 półork → 0x61C562),
   jeśli rasa dotąd nie miała podras;
4. tabele z 1.2.
Cechy w 0x722820 (nadawanie cech rasy) nie wymagają już łatki: wiersz w `DSRASY` omija oryginalny wybór.

---------------------------------------------------------------------------------------------------------------------

## 2. Zdolności rasy wg poziomu – tablice RLAB

`DSRASY.2DA`, kolumna `RLAB` = nazwa tablicy (do 8 znaków), np. `RLMUL`. Format **taki jak CLAB**:
```
2DA V1.0
****
          1          2     3     ...   30
ABILITY1  GA_SPIN267 ****  ****  ...   ****
ABILITY2  ****       AP_DSXXX ****     ****
```
- Kolumny 1–30 = **poziom postaci** (suma poziomów wszystkich klas).
- Wpisy: `GA_<SPL>` – zdolność wrodzona (lista zdolności), `AP_<SPL>` – efekty czaru nałożone na stałe w chwili
  awansu, `FA_<strref>` – tylko tekst na karcie postaci. Nieznany prefiks jest pomijany.
- Exe nadaje wpisy przy tworzeniu postaci i przy każdym awansie (za każdy zdobyty poziom postaci), tą samą procedurą
  co CLAB klas (po 11 klasach). **Postacie już istniejące nie dostaną zdolności z poziomów, które już mają.**
- Pamięć podręczna: do 64 tablic wczytanych po nazwie (RLAB + progresje klas razem).

Pliki `SPL` dla `AP_`/`GA_` robi `tools/iwd2_spl.py` (wzór: `DSBBNMV.SPL`, `DSDRVEN.SPL`).

---------------------------------------------------------------------------------------------------------------------

## 3. Cechy walki ras – DSRASY.2DA i DSRWROG.2DA

### DSRASY.2DA (wiersze = nazwy ras i podras z GetRaceRow)
| Kolumna | Znaczenie | Oryginał gry |
|---|---|---|
| `RLAB` | tablica zdolności rasy (sekcja 2), `*` = brak | – |
| `DARKVISION` | 1 = widzenie w ciemności (flaga 0x20000 nadawana przy tworzeniu / awansie) | aasimar, tiefling, drow, wszystkie krasnoludy, gnom głębinowy, półork (też mul) |
| `GIANT_AC` | o tyle olbrzymy (RACE 153) i ogry (113) trafiają tę rasę gorzej | 4: krasnoludy, gnom (bez głębinowego) |
| `THROWN` | premia do trafienia bronią miotaną i procą | 1: niziołki |
| `SR_LEVEL` | przyrost odporności na magię na każdy poziom postaci | 1: drow, gnom głębinowy |
Gnom głębinowy zachowuje pozostałe zaszyte cechy (flaga 0x200000 i wartość +0x5E2) niezależnie od tabeli.

### DSRWROG.2DA (wiersze jak wyżej)
| Kolumna | Znaczenie |
|---|---|
| `BONUS` | premia do trafienia przeciw każdej rasie z E1–E6 |
| `ABERRATION` | premia do trafienia przeciw aberracjom (test exe 0x584AA0) |
| `E1`–`E6` | numery ras przeciwników z `RACE.IDS` (0 = brak), np. 111 HOBGOBLIN, 112 KOBOLD, 155 GOBLIN, 160 ORC, 180 BUGBEAR |
Oryginał: krasnoludy +1 przeciw 111/155/160/180 (złoty dodatkowo +1 przeciw aberracjom), gnomy +1 przeciw 111/112/155/180.
Brak całej tabeli DSRWROG = oryginalna funkcja gry.

---------------------------------------------------------------------------------------------------------------------

## 4. Podklasa (kit)

### 4.1 Miejsca w exe (tabela 0x846C00, 8 wpisów po 32 B; źródło `asm/podklasy.asm`)
| Wpis | Bit (`KIT.IDS`) | Wiersz | Klasa | CLAB | Gdzie w kreatorze |
|---|---|---|---|---|---|
| 0 | 0x01000000 | PALADIN_DS | 7 paladyn | CLABDS01 | okno 52, przycisk 4 (zakony) |
| 1 | 0x02000000 | BARBARIAN_DS | 1 barbarzyńca | CLABDS02 | okno 52, przycisk 2 (1 = bez podklasy) |
| 2 | 0x04000000 | CLERIC_DS | 3 kapłan | CLABDS03 | okno 12, przycisk 14 (bóstwa; GUICG.CHU – komponent 2 dodaje przycisk) |
| 3 | 0x08000000 | FIGHTER_DS | 5 wojownik | CLABDS04 | okno 52, przycisk 2 |
| 4 | 0x10000000 | RANGER_DS | 8 tropiciel | CLABDS05 | okno 52, przycisk 2 |
| 5 | 0x20000000 | DRUID_DS | 4 druid | CLABDS06 | okno 52, przycisk 2 |
| 6 | 0x40000000 | BARD_DS | 2 bard | CLABDS07 | okno 52, przycisk 2 |
| 7 | 0x80000000 | SORCERER_DS | 10 zaklinacz | CLABDS08 | okno 52, przycisk 2 |
Wpis: +0 bit, +4 strref etykiety przycisku (WeiDU), +8 nazwa wiersza (do 15 znaków), +0x17 klasa, +0x18 CLAB.
Za tabelą: 0x846D04 strref opisu nowego bóstwa, 0x846D08 + 4·klasa – strref etykiety „bez podklasy”.
Nazwa wiersza, klasa i CLAB są w asm – zmiana = przebudowa exe (`tools/iwd2_podklasy_exe.py`) i makr
(`tools/iwd2_paczki_exe.py`). Teksty zmienia się w `.tra` (tablica `ds_kity` w komponencie 2).

### 4.2 Tabele podklasy – wiersz o nazwie podklasy (np. `FIGHTER_DS`)
Komponent 2 kopiuje wiersz klasy bazowej (funkcja `ds_wiersz_kitu`), potem można go zmienić:
| Plik | Znaczenie | Czyta exe z kitem? |
|---|---|---|
| `KITLIST.2DA` | `NAZWA LOWER MIXED HELP` (strrefy; HELP = opis w kreatorze) | tak |
| `KIT.IDS` | `0x0N000000 NAZWA` | – |
| `ALIGNMNT.2DA` | dozwolone charaktery (L_G L_N L_E N_G N_N N_E C_G C_N C_E: 1/0) | tak |
| `CLSSRSMD.2DA` | odporności | tak |
| `ABCLASRQ.2DA` | wymagania cech | tak |
| `ABCLSMOD`, `CHPTXT2–7`, `CLASWEAP`, `DUALCLAS`, `ENCMOD`, `KITTABLE`, `LORE`, `PROFS`, `PROFSMAX`, `QSLOTS`, `SKILLCLS`, `STRTGOLD`, `THAC0`, `XPLEVEL` | jak klasa bazowa | **nie** (exe podaje kit 0) – wiersz dla porządku |
| `CLABDSnn.2DA` | zdolności podklasy (sekcja 5) | tak |
Nie obsługiwane: kolumny podklas w `FEATS`/`SKILLS` (bóstwa po indeksie) – nowy bit daje wartości domyślne.
Progresja PW / BAB / rzutów: wiersz podklasy w DSKLPROG, a bez niego klasa bazowa (sekcja 7).

---------------------------------------------------------------------------------------------------------------------

## 5. Zdolności klasy i podklasy – CLAB

Tablica wybierana przez exe: klasa bazowa → CLABBA01, CLABFI05 (barbarzyńca), CLABCL01–09 / CLABPR01 (kapłan wg bóstwa),
CLABDR01, CLABFI01, CLABMO01, CLABPA01, CLABRN01, CLABTH01, CLABSR01, CLABMA01; podklasa DS → CLABDSnn.
Format i prefiksy jak w sekcji 2, kolumny = **poziom klasy**. Dodatkowo `FI_<ITM>` w CLAB mnicha = przedmiot pięści
(najwyższa kolumna ≤ poziomowi). Funkcje WeiDU: `ds_clab_poziom` (wpis na poziom), `ds_clab_poziom1`.
Zdolności przeniesione z exe do CLAB: odporność paladyna na strach (`AP_DSPALEMF`, poziom 2), odporność druida na
truciznę (`AP_DSDRVEN`, poziom 9), szybkość barbarzyńcy (`AP_DSBBNMV`, poziom 1 + kara w ciężkiej zbroi `DSBBNARM.EFF`).

---------------------------------------------------------------------------------------------------------------------

## 6. Progi zdolności klas – DSKLASY, DSSNEAK, DSWROG

`DSKLASY.2DA`: wiersze = zdolności, kolumny = klasy bazowe `BBN BRD CLR DRD FTR MNK PAL RGR ROG SOR WIZ`,
wartość = minimalny poziom tej klasy (0 = brak). Podklasa dziedziczy kolumnę klasy bazowej.
| Wiersz | Zdolność | Oryginał |
|---|---|---|
| `EVASION` | Unik (udany rzut na Refleks = brak obrażeń; nie w średnim/ciężkim pancerzu) | mnich 1, łotrzyk 2 |
| `UNCANNY_DEX` | Uncanny Dodge: premia ZRĘ do KP wobec niewidocznego atakującego | barbarzyńca 2, łotrzyk 3 |
| `UNCANNY_FLANK` | Uncanny Dodge: brak ataku z zaskoczenia z flanki | barbarzyńca 5, łotrzyk 6 |
| `SNEAK_ATTACK` | atak z zaskoczenia (kości wg poziomu klasy dającej zdolność) | łotrzyk 1 |
| `FAVORED_ENEMY` | ulubiony wróg (premie z DSWROG) | tropiciel 1 |
| `AURA_COURAGE` | aura odwagi (sojusznicy w promieniu 100) | paladyn 2 |
`DSSNEAK.2DA`: wiersz = poziom: `DICE` (liczba kości), `SIDES` (ścianki, z 1. wiersza).
`DSWROG.2DA` (ulubiony wróg): wiersz = ranga 1–8, `ATTACK`, `DAMAGE` (oryginał: ranga i +4).

---------------------------------------------------------------------------------------------------------------------

## 7. Progresja klasy i podklasy – DSKLPROG.2DA (test21, podklasy od test22)

Wiersze = klasy bazowe `BARBARIAN BARD CLERIC DRUID FIGHTER MONK PALADIN RANGER ROGUE SORCERER WIZARD`
**oraz dowolne podklasy** – nazwa wiersza jak w KITLIST: podklasy DS (`PALADIN_DS` … `SORCERER_DS`, wpisane z wartościami
klasy bazowej) i kity gry (zakony mnicha i paladyna, bóstwa kapłana, szkoły czarodzieja). Kolejność wyboru:
wiersz podklasy postaci (tylko gdy podklasa należy do tej klasy) → wiersz klasy bazowej → tablica oryginalna.
Przykład – gladiator z kością k12 zamiast k10 wojownika: `FIGHTER_DS    HPBARB    BAATFGT   SAVEWAR`.
Postać wieloklasowa: tablica podklasy działa tylko dla klasy, do której podklasa należy; pozostałe klasy – swoje wiersze.
| Kolumna | Tablica | Format tablicy | Oryginał |
|---|---|---|---|
| `HP` | kość PW przy awansie | wiersz = poziom klasy 1–40: `SIDES ROLLS MODIFIER` (HPWAR, HPBARB, HPPRS, HPROG, HPMONK, HPWIZ) | barbarzyńca HPBARB (k12), wojownik/paladyn/tropiciel HPWAR (k10), kapłan/druid HPPRS (k8), mnich HPMONK (k8), bard/łotrzyk HPROG (k6), zaklinacz/czarodziej HPWIZ (k4) |
| `BAB` | premia do ataku | wiersz = poziom 1–40: `BASE_ATTACK NUM_ATTACKS` (BAATFGT, BAATNFG, BAATMAG) | barbarzyńca, wojownik, paladyn, tropiciel BAATFGT; bard, kapłan, druid, mnich (z bronią), łotrzyk BAATNFG; zaklinacz, czarodziej BAATMAG |
| `SAVE` | rzuty obronne | wiersz = poziom 1–30: `FORTITUDE REFLEX WILL` (SAVEWAR, SAVEPRS, SAVEROG, SAVEBRD, SAVEMONK, SAVEWIZ) | barbarzyńca, wojownik, paladyn, tropiciel SAVEWAR; bard SAVEBRD; kapłan, druid SAVEPRS; mnich SAVEMONK; łotrzyk SAVEROG; zaklinacz, czarodziej SAVEWIZ |
Można wpisać **własną tablicę** (np. `HPDS01`) – plik musi być w `override` i mieć te same kolumny. Wpis `*`, brak
wiersza albo nieudane wczytanie → tablica oryginalna. Mnich bez broni zawsze BAATMKU. Premia z Kondycji: `HPCONBON.2DA`
(bez zmian). Rzuty: suma po wszystkich klasach postaci (+ SAVERACE). Tabela jest czytana raz na uruchomienie gry.

---------------------------------------------------------------------------------------------------------------------

## 8. Lista kontrolna

**Nowa podrasa w otwartym miejscu (mul / półelf DS):** teksty w `.tra` → SRLIST, SR_<rasa>, SUBRACE.IDS, ABRACEAD,
ABRACERQ, RACESPAB, RACERSMD, SAVERACE, SKILLRAC, STRTXP → DSRASY (+ RL<nazwa>.2DA) → DSRWROG → strref nazwy na
karcie postaci w `*_DS.exe` → nowa postać w grze.

**Nowe zdolności istniejącej rasy:** DSRASY kolumna RLAB → `RL<nazwa>.2DA` (+ SPL dla `AP_`/`GA_`).

**Zmiana podklasy DS (jednego z 8 miejsc):** teksty (`ds_kity`, `.tra`) → KITLIST, ALIGNMNT, CLSSRSMD, ABCLASRQ →
CLABDSnn → (opcjonalnie) progi w DSKLASY dotyczą klasy bazowej.

**Inna progresja klasy albo podklasy:** DSKLPROG (wiersz klasy albo podklasy, kolumna HP / BAB / SAVE) → ewentualnie nowa tablica w `override`.

**Po zmianie exe (asm):** `tools/iwd2_podklasy_exe.py --base IWD2_1920x1080_test13.exe --out testNN.exe` →
`tools/iwd2_paczki_exe.py ... --rasy testNN.exe --out-rasy darksun_rasy/exe/rasy_exe.tpa` → przeinstalować komponent 0
paczki 2 (i komponenty wpisujące strrefy: 1, 2, 3).
