# IWD2.exe – rasy, podrasy, klasy i kity: mapa miejsc zaszytych w kodzie

Plik: IWD2.exe z instalacji GOG, wersja 2.01 (v2.01.1016), 5 029 888 B,
sha256 `18e01d21855f88702c062497aa25dfb42928671973d3b929e42206def2d9df2a`.
Układ PE: ImageBase 0x400000, offset w pliku = adres − 0x400000 dla wszystkich sekcji
(.text 0x401000, .rdata 0x847000, .data 0x8A5000). Narzędzie: `tools/iwd2_re.py` (objdump + Python).
Stan (test22, 2026-11-14): mul i półelf atasyjski (podrasy), 8 podklas DS, zdolności klas z 2DA (sekcje 8–9), zdolności
ras z tabel (sekcja 11), progresja klas i podklas z DSKLPROG (sekcje 12–13). Przewodnik dla autora tabel:
`docs/dodawanie_ras_i_klas.md`.

## 1. Co jest w danych (2DA/IDS/CHU)

- **Lista podras w kreatorze jest sterowana danymi**: `SRTABLE.2DA` → dla każdej rasy plik `SR_<rasa>.2DA`
  z numerami wierszy `SRLIST.2DA`; `SRLIST` ma nazwę wiersza, teksty (LOWER/MIXED/HELP), `ID` podrasy (0–2)
  i palety włosów/skóry. Półork (`SR_HO`) i półelf (`SR_HE`) mają po jednym wpisie (czysta rasa).
- `SUBRACE.IDS`: podrasa = rasa × 0x10000 + ID (np. 0x00010001 HUMAN_AASIMAR).
- Cechy ras i podras są w tabelach z wierszami po nazwie: `ABRACEAD` (modyfikatory), `ABRACERQ`, `RACESPAB`
  (plik czarów wrodzonych, np. SPCH_T), `RACERSMD` (odporności), `SAVERACE`, `SKILLRAC`.
- `SUBRACES.2DA` i `RACEXPMD.2DA` nie mają odwołań w EXE (prawdopodobnie nieużywane).
- **Kity to flagi bitowe** (`KIT.IDS`): 24 zajęte bity 0x1–0x800000 (paladyni 0x1–0x4, mnisi 0x8–0x20,
  szkoły 0x40–0x4000, bóstwa kapłanów 0x8000–0x800000). Wolne bity: 0x01000000–0x80000000 (8 sztuk).
- `KITTABLE` / `K_<klasa>_<rasa>.2DA`: **nieużywane w IWD2** (nazwa „KitTable” w EXE nigdy nie jest ładowana).

### Ekrany kreatora (GUICG.CHU)
| Okno | Tytuł | Przyciski wyboru | Zajęte |
|---|---|---|---|
| 8 | Race | 2–8 (7) | 7 |
| 54 | Subrace | 1–4 (4) | maks. 3 (czysta + 2) |
| 2 | Class | 2–12 (11) | 11 |
| 12 | Szkoła czarodzieja / bóstwo kapłana | 13, 2–9 (9); id 10 = pasek przewijania, 11 = opis | 9 (+ id 14 po łatce) |
| 52 | Zakon mnicha / paladyna (+ barbarzyńca po łatce) | 1–10 (10) | 3 |

## 2. Co jest zaszyte w kodzie

Wszystkie nazwy wierszy ras, podras, klas i kitów są globalnymi napisami (CString, konstruktor 0x7FCC88,
przypisanie 0x7FC98F) i każda jest użyta **dokładnie w jednej funkcji**:

### 0x541940 – nazwa wiersza rasy: `CString GetRaceRow(BYTE rasa, BYTE podrasa)`
- Konwencja: ukryty wskaźnik wyniku + 2 argumenty, `ret 0xC`.
- `rasa − 1` przez tablicę skoków 0x541BFC (7 wpisów); w każdej gałęzi podrasa 0/1/2 → napis.
- Wywołania: 11, w funkcjach 0x542610, 0x543140, 0x5D8B50, 0x5D9610, 0x609B30, 0x60BE30, 0x60D950,
  0x611C36, 0x626DD0, 0x722820.

### 0x541DA0 – nazwa wiersza klasy/kitu: `CString GetClassRow(BYTE klasa, DWORD kity)`
- `klasa − 1` przez tablicę skoków 0x5421C0 (11 klas).
- Kapłan: `kity & 0xFF8000` porównywane z bitami bóstw; brak dopasowania → „CLERIC”.
- Mnich: `kity & 0x38` (0x8/0x10/0x20); podobnie paladyn i czarodziej (szkoły).
- Wywołania: 11, w funkcjach 0x542FA0, 0x5438D0, 0x544A60, 0x546AA0, 0x5D9671, 0x5F55A4, 0x60BE30,
  0x60D2D1, 0x611C36, 0x621900, 0x6FE296.

### Ładowanie tabel
Nazwy plików tabel (SRList, SRTable, KitList, AbRaceAd, SaveRace, …) to także globalne napisy z jednym
użyciem każdy – funkcje ładujące w okolicy 0x53EF8B–0x5401A1. KITLIST → CRuleTables+0x1324.

## 3. Wnioski dla externalizacji (ras)
1. **Podrasa**: zrobione dla mula (SR_HO/SRLIST/tabele cech + łatki 0x541BC4, 0x544FE6, 0x7229C9).
2. **Rasa bazowa**: tablice skoków na 7 ras; okno ras pełne.

## 3a. Przegląd tabel 2DA – odwołania do podras
| Tabela | Postać odwołania | Używana przez EXE | Mul |
|---|---|---|---|
| SRLIST | wiersze podras | tak | dopisany |
| SR_D/E/G/H/HE/HF/HO | listy wierszy SRLIST dla rasy | tak (przez SRTABLE) | SR_HO dopisany |
| ABRACEAD, ABRACERQ, RACESPAB, RACERSMD, SKILLRAC | wiersze po nazwie podrasy | tak | dopisane |
| SAVERACE | wiersze po nazwie; półork jako „HALFORC” (błąd w grze) | tak | dopisany |
| STRTXP | startowe PD podras (wiersze po nazwie) | tak | dopisany (0) |
| FEATS, SKILLS | **kolumny** ras/podras wybierane po numerze w kodzie | tak | **brak – łatka etapu 2** |

## 5. Klasy i kity (podklasy) – analiza

### Nowa klasa bazowa – praktycznie niewykonalna
- 11 klas w tablicach skoków (GetClassRow 0x5421C0, nazwa klasy 0x621CB0 i wiele innych), okno klas pełne (11/11).
- CRE V2.2 trzyma **osobny poziom dla każdej z 11 klas w stałych polach** — nowa klasa wymagałaby zmiany formatu zapisu postaci i setek miejsc w kodzie.

### Nowy kit (podklasa) – wykonalny łatkami
- Nowy bit z wolnej puli 0x01000000–0x80000000 (`KIT.IDS`).
- KITLIST: kod 0x621900 bierze HELP z KITLIST po nazwie wiersza z GetClassRow (sterowane danymi). Etykiety przycisków w kreatorze są zaszyte (strrefy w kodzie).
- ALIGNMNT (dozwolone charaktery) i CLSSRSMD (odporności) — wiersze po nazwie kitu.
- Okno 52: aktualizacja 0x60D280 (przyciski 1–10 w edi, ebp, ebx, [esp+0x68], [esp+0x10..0x24]); kliknięcie 0x621D88 (mnich: 0x8 << (id−1), paladyn: 0x1 << (id−1)); Gotowe = kit ≠ 0 (0x615C50).
- Kliknięcie klasy w oknie 2: 0x61BF63, tablica skoków 0x61C1A8 (id−2) → okno 52 (mnich, paladyn), 12 (kapłan, czarodziej), reszta bez okna.
- Okno 12: aktualizacja 0x60FEE0 (pętla czarodzieja 0x60FF47, kapłana 0x610041 po id 2–9 i 13, etykiety bóstw zaszyte 0x610090..), GetKit przycisku 0x61CCC0, kliknięcie 0x61CEC0 (maska 0xFF8000, opis po bicie 0x61CF09..).
- Bóstwa mają kolumny w FEATS (od 14) i SKILLS (od 15); indeks liczony łańcuchami porównań (0x60CB40, 0x6120BA, …). Dla nieznanego bitu wychodzi indeks poza tabelą → wartość domyślna (brak premii bóstwa, bez wysypki).
- Szkoła czarodzieja: powiązana z systemem szkół czarów (0x703170) — nie dotykać.

## 7. Podklasy – prototyp (test14, komponent 2 moda darksun_rasy)
Kod: `mod/darksun_rasy/darksun_rasy/asm/podklasy.asm`, wstawiony w niewykorzystany koniec .text 0x846900 (rozmiar wirtualny .text podniesiony do 0x446000).
Tabela 0x846C00 (wpisy po 32 B: bit, strref etykiety, nazwa wiersza): PALADIN_DS 0x01000000, BARBARIAN_DS 0x02000000, CLERIC_DS 0x04000000; 0x846C64 strref „barbarzyńca bez podklasy”, 0x846C68 strref opisu bóstwa. Strrefy wpisuje WeiDU (domyślnie −1 = podklasa wyłączona).

| Miejsce | Zmiana |
|---|---|
| 0x541DA0 GetClassRow | bity 0xFF000000 → nazwa wiersza z tabeli |
| 0x61C1A8 (tablica skoków kliknięcia klasy) | barbarzyńca otwiera okno 52 jak mnich/paladyn |
| 0x60D6C3 (okno 52, wybór gałęzi) | gałąź barbarzyńcy: przycisk 1 = bez podklasy, 2 = nowa |
| 0x60D753 (okno 52, paladyn) | przycisk 4 = nowy zakon |
| 0x621DBE (kliknięcie w oknie 52) | paladyn id 4 / barbarzyńca id 2 → bit z tabeli |
| 0x615C50 (Gotowe w oknie 52) | barbarzyńca z kitem 0 dozwolony |
| 0x61CD4A (GetKit okna 12) | kapłan id 14 → bit bóstwa |
| 0x6100F0, 0x61012E (pętla okna 12 kapłana) | etykieta i obsługa przycisku 14 (ukryty, gdy brak tekstu) |
| 0x61001B (pętla okna 12 czarodzieja) | przycisk 14 ukryty |
| 0x61D031 (opis po kliknięciu w oknie 12) | nowy bit → strref 0x846C68 |
| 0x61CEF4, 0x615CFE | maska bóstw 0xFF8000 → 0xFFFF8000 (zmiana bóstwa, przycisk Gotowe) |
GUICG.CHU: okno 12 dostaje przycisk 14 (kopia przycisku 9, y+63) — `tools/iwd2_chu_kontrolka.py`.
Znane braki: brak podświetlenia wybranej nowej podklasy w oknie 52; nowe bóstwo nie ma kolumny w FEATS/SKILLS (gra bierze wartość domyślną – brak premii bóstwa); podklasy nie mają jeszcze własnych zdolności.

## 8. Tablice zdolności CLAB i pozostałe tabele klas (test15)

**Wybór CLAB w exe.** Nazwy CLAB są wpisane na stałe: 20 obiektów C2DArray w obiekcie reguł (0x1468–0x1714, po 0x24 B), wczytywanych przy starcie przez `0x402B70` (Load(CResRef*)), konstruktor `0x5402E0`. Funkcja `GetClabTable(klasa, kit)` pod `0x546030` (thiscall, `ret 8`) wybiera obiekt po klasie (skok `0x546170`): 1 barbarzyńca → CLABFI05, 2 bard → CLABBA01, 3 kapłan → po bicie bóstwa (`kit & 0xFF8000`: CLABCL01–09, inaczej CLABPR01), 4 druid DR01, 5 wojownik FI01, 6 mnich MO01, 7 paladyn PA01, 8 tropiciel RN01, 9 łotrzyk TH01, 10 zaklinacz SR01, 11 czarodziej MA01. Jedyny wywołujący to `0x722D50` (nadawanie zdolności z CLAB przy awansie, także przy tworzeniu postaci). Kolumna ABILITIES w KITLIST nie jest czytana.

Format CLAB: wiersze `ABILITYn`, kolumny 1–40 = poziom klasy; `GA_<SPL>` nadaje zdolność wrodzoną (np. `GA_SPIN236` = Barbarian Rage).

**Łata (podklasy.asm, `clab` 0x846AB8):** `0x546030` → `jmp clab` + 4×nop. Dla kitu z bitem 0xFF000000 i zgodnej klasy (bajt +0x17 wpisu tabeli 0x846C00) zwraca własny obiekt C2DArray w końcówce .data (0xA1AF00 + 0x24·i, flagi 0xA1AF70; VirtualSize .data podniesiony do 0x176000). Obiekt jest konstruowany i wczytywany przy pierwszym użyciu z nazwy pod +0x18 wpisu (`CLABDS01/02/03`). W każdym innym przypadku działa oryginalny kod.

Wpis tabeli kitów (32 B): +0 bit, +4 strref etykiety, +8 nazwa wiersza (do 15 znaków), +0x17 klasa, +0x18 CLAB (8 znaków).

**WeiDU (komponent 2):** `CLABDS01` = CLABPA01 + `GA_SPIN209` (Prayer), `CLABDS02` = CLABFI05 + `GA_SPIN267` (Ilmater's Endurance), `CLABDS03` = CLABPR01 + `GA_SPIN264` (Tempus' Strength). Zdolność testowa trafia do 1. poziomu w pierwszym wolnym wierszu `ABILITYn`.

**Pozostałe tabele.** `GetClassRow` z prawdziwym kitem wołają tylko: AbClasRq (0x5D96F3, 0x60BF13), Alignmnt, ClssRsMd (0x611EF0), KitList. XPLevel, EncMod i inne dostają kit 0. Komponent 2 dopisuje mimo to wiersze PALADIN_DS / BARBARIAN_DS / CLERIC_DS (kopia wiersza klasy bazowej, bez niego zera) do: ABCLASRQ, ABCLSMOD, CHPTXT2–7, CLASWEAP, CLSSRSMD, DUALCLAS, ENCMOD, KITTABLE, LORE, PROFS, PROFSMAX, QSLOTS, SKILLCLS, STRTGOLD, THAC0, XPLEVEL. Kolumn nie dodajemy: FEATCLAS / SKILCOST / SKILLPTS / TRAPSAVE mają kolumny klas, a FEATS / SKILLS czytają kolumny bóstw po indeksie z `0x5472FF`. Nieznany bit daje tam wartość domyślną.

## 9. Test16: półelf, kity pięciu kolejnych klas, pierwsza zdolność klasy wyjęta z exe

Exe budowane skryptem `tools/iwd2_podklasy_exe.py` (nasm + listing → adresy etykiet → haki), baza: test15.

**Półelf atasyjski** (`asm/halfelf.asm`, komponent 3): 0x541A42 GetRaceRow półelfa (podrasa ≠ 0 → `HALF_ELF_DS`, napis w miejscu asercji, 56 B); 0x544EC6 nazwa podrasy na karcie postaci (`mov eax, strref; jmp 0x545009`, strref wpisuje WeiDU pod 0x144EC7); 0x7228E2 zdolności rasowe bez asercji (`je` → `jmp`); 0x61C640 przycisk półelfa → okno podras 54. Tabele: SRLIST, SR_HE, ABRACEAD, ABRACERQ, RACESPAB, RACERSMD, SAVERACE, SKILLRAC, STRTXP, SUBRACE.IDS (0x00030001). Ten sam komponent 2 wpisuje też strref mula pod 0x144FE7 (wcześniej stałe 42801).

**Kity wojownika, tropiciela, druida, barda i zaklinacza** – jak barbarzyńca: przycisk klasy otwiera okno 52 (tablica 0x61C1A8, indeks = klasa − 1 → 0x61C0A5), przycisk 1 = bez podklasy, 2 = podklasa. Kod uogólniony (`szukaj_klase`: wpis tabeli po klasie): okno 52, kliknięcie, Gotowe (kit 0 dozwolony dla każdej klasy z wpisem oprócz paladyna). Nowy układ danych: 8 wpisów po 32 B od 0x846C00 (bity 0x01–0x80 << 24, CLABDS01–08), 0x846D00 koniec, 0x846D04 CLR_HELP, 0x846D08 NOK[klasa] (etykieta „bez podklasy”). Komponent 2 rozpoznaje exe po `FIGHTER_DS` pod 0x446C68; test14/15 (stary układ) nie są zmieniane.
Wszystkie 8 wolnych bitów kitów jest teraz zajętych.

**Zdolności klas zaszyte w exe.** Poziom klasy czyta `0x447990(klasa)` na CDerivedStats (`[obiekt+0x46+klasa]`). Wywołania ze stałą klasą (poza tabelami i rzucaniem czarów 0x7632xx/0x7638xx):
| Klasa | Miejsce | Co robi (stan rozpoznania) | Zamiennik |
|---|---|---|---|
| paladyn ≥ 2 | 0x4A3A5A–0x4A3A84 (funkcja efektów 0x4A3310) | odporność na czar SPWI420 Emotion: Fear (efekt odrzucany, komunikat) – tylko gdy paladyn nie upadł | **zrobione**: warunek wyłączony, `DSPALEMF.SPL` (opcode 206, SPWI420) jako `AP_` na 2. poziomie CLABPA01–04 |
| paladyn ≥ 2 | 0x4A48CF, 0x6F8EF4 | to samo dla sojuszników w promieniu 100 (aura; gra sprawdza wynik ≥ 2 i odległość² < 0x2710) | **zrobione (test19)**: oba `call 0x447990(7)` → `aura` (dodatki.asm): `DSKLASY.2DA` wiersz AURA_COURAGE → 2 albo 0; promień nadal w exe |
| kapłan + paladyn | 0x71B8D0 | poziom odpędzania nieumarłych = kapłan + (paladyn − 2) | wzór, nie zdolność – zostaje |
| mnich 1–30 | 0x723412 | pięść mnicha: przedmiot 00MFIST1–9 zależnie od poziomu (tabela 0x723808, 11 przypadków) | **zrobione (test18)**: hak 0x723417 → `mnich`: przedmiot = wpis `FI_<ITM>` w CLAB mnicha (GetClabTable(6, kit)) w najwyższej kolumnie ≤ poziomowi, domyślnie 00MFIST1; tabela 0x723808 nieużywana. Parser CLAB (0x723093) pomija nieznany prefiks bez asercji |
| mnich | 0x72E354 | +poziom/3 do licznika (prawdopodobnie użycia ataku ogłuszającego) | do rozpoznania |
| mnich ≥ 8, ≥ 12 | 0x739FE4 | −1/−1 do wartości 0x5604 (zakres 0–10; prawdopodobnie szybkość broni) | do rozpoznania |
| mnich | 0x73E194, 0x73E390 | ST = wartość + poziom/2 − 1 (ogłuszenie / drżąca dłoń) | wzór – zostaje |
| druid ≥ 9 | 0x4A7956 | efekt trucizny z typem 0x20 odrzucany (odporność na jad naturalny) | **zrobione (test17)**: warunek wyłączony (0x4A795E `jl` → `jmp`), `DSDRVEN.SPL` (opcode 101, 25 Poison – każda trucizna, decyzja właściciela) jako `AP_` na 9. poziomie CLABDR01–04 |
| barbarzyńca + mnich | 0x72E2EF, 0x72E330 | szybkość ruchu: barbarzyńca ×1,2 (stała 0x84EB58) bez ciężkiego pancerza (0x724690(3): typy ITM 0x3F–0x41); mnich + poziom/3 bez pancerza, +1 z atutem 0xC | **barbarzyńca zrobiony (test19)**: 0x72E2F6 `je` → `jmp`; `AP_DSBBNMV` (opcode 126 +2) na 1. poziomie CLABFI05 (i CLABDS02); ciężkie zbroje: efekt założenia opcode 177 (CLASS = BARBARIAN) → `DSBBNARM.EFF` (opcode 126 −2). Mnich zostaje w exe |
| mnich ≥ 20 | 0x73A7B7, 0x73AA3F | atak bez flagi 0x40 (niemagiczny?) nie działa (Perfect Self) | do rozpoznania flagi |
| łotrzyk | 0x585D50, 0x585D80 (wołane z walki 0x73D9B6) | kości ataku z zaskoczenia = (poziom − 1)/2 + 1, kość k6 – **tego używa walka**; warunek klasy: maska klas, bit 0x100 | **zrobione (test18/19)**: `DSSNEAK.2DA` (wiersz = poziom: DICE; SIDES z 1. wiersza); od test19 klasy z `DSKLASY.2DA` wiersz SNEAK_ATTACK (hak 0x585D55), kości wg poziomu klasy dającej zdolność |
| łotrzyk | 0x71B910 → statystyka 0x9B2 | mnożnik ciosu w plecy z BACKSTAB.2DA (pozostałość BG) – liczony, ale walka go nie używa (czytany tylko w 0x46Cxxx) | zostaje |
| łotrzyk ≥ 2, mnich | 0x585DA0 (z obrażeń 0x4AA0D9, flaga efektu 0x8 = rzut na Refleks) | Unik: udany rzut = brak obrażeń; nie gdy bezradny (stan 0x829) ani w średnim/ciężkim pancerzu (0x724690(2/3)); Improved Evasion to atut 31 (0x4AA343) | **zrobione (test18)**: progi z `DSKLASY.2DA` wiersz EVASION (kolumny = klasy) |
| barbarzyńca ≥ 2, łotrzyk ≥ 3 | 0x73BA1D | Uncanny Dodge: brak utraty premii ZRĘ do KP wobec niewidzialnego atakującego (bez atutu Blind Fight 6) | **zrobione (test18)**: `DSKLASY.2DA` wiersz UNCANNY_DEX |
| barbarzyńca ≥ 5, łotrzyk ≥ 6 | 0x73D95B (komunikat 82 „Uncanny Dodge prevented flank attack”) | Uncanny Dodge: brak ataku z zaskoczenia z flanki, chyba że łotrzyk atakującego ≥ poziom celu + 4 | **zrobione (test18)**: `DSKLASY.2DA` wiersz UNCANNY_FLANK (poziom z bajtów postaci +0x626+klasa) |
| łotrzyk > 0 | 0x4A6744 | atut Slippery Mind (0x3A): ponowny rzut obronny na Wolę | atut – zostaje |
| łotrzyk / mnich | 0x757A80 | akcja ukrycia (tryb 2) tylko dla łotrzyka i mnicha | akcja – zostaje |
| tropiciel | 0x73BC88, 0x73DD3F | ulubiony wróg (rasy w CRE +0x253, 8 B): premia do ataku = ranga (0x546860: liczba wrogów − indeks), do obrażeń +4 | **zrobione (test19)**: klasy z `DSKLASY.2DA` wiersz FAVORED_ENEMY (haki 0x73BC76, 0x73DD34), premie z `DSWROG.2DA` (wiersz = ranga 1–8, kolumny ATTACK, DAMAGE; hak 0x73BCD0) |
| barbarzyńca < 20 | 0x4A5C79 | po szale zmęczenie (od 20. poziomu brak) | do rozpoznania |
| barbarzyńca ≥ 15 | 0x5E5B22 | do rozpoznania | – |
| paladyn + wojownik | 0x737BBE | upadły paladyn: poziomy paladyna przechodzą na wojownika | mechanika, nie zdolność – zostaje |
Inne dostępy do poziomu klasy: `0x762760(klasa)` i `0x762830(klasa)` na postaci, `0x40D7E0(klasa)` (przynależność do klasy; stałe klas w 0x847CA5–0x847CAF), bajty postaci `+0x626+klasa` (walka), statystyki 96–106 (CLASSLEVEL*) w GUI. Dalsze miejsca mnicha: 0x4A4A25 (≥ 3: +2 przeciw szkole 4 – Still Mind), 0x584CE7 (≥ 20: odporność na część stworzeń po animacji), 0x723F66 (pięść/broń mnicha).

**Test19 – kod w drugiej wnęce.** Wnęka 0x846900–0x847000 jest pełna (0x846FCA). Od test18 martwy jest kod dawnej pięści mnicha 0x723430–0x7237A1 (881 B, osiągalny tylko przez tablicę skoków 0x7237DC, której już nikt nie używa; sprawdzone – żaden skok z zewnątrz). Tam trafia `asm/dodatki.asm` (0x723430–0x723585); etykiety z podklasy.asm (`zdolnosc`, `liczba`, `tabela2da`, `sneak_poziom`) podaje `nasm -D`. Wiersze `DSKLASY.2DA`: 0 EVASION, 1 UNCANNY_DEX, 2 UNCANNY_FLANK, 3 SNEAK_ATTACK, 4 FAVORED_ENEMY, 5 AURA_COURAGE; brak wiersza (stara tabela) = zachowanie oryginalne. `DSWROG.2DA` – wskaźnik 0xA1AF28.

**Barbarzyńca – szał i redukcja obrażeń.** Szał jest w danych: `GA_SPIN236` (Rage, 1/4/8/12…) i `GA_SPIN260` (Greater Rage, 16/20/24…) w CLABFI05; SPIN236 to opcody 142, 44 (+4 SIŁ), 10 (+4 KON), 35, 0 (−2 KP), 288 i 440 (Barbarian rage). W exe zostaje tylko zmęczenie po szale poniżej 20. poziomu (0x4A5C79). Redukcja obrażeń 1/– … 7/– jest w CLABFI05 wyłącznie jako tekst `FA_` (39311, 39326–39331) – w exe nie znalazłem kodu, który by ją nakładał (brak odwołań do poziomu barbarzyńcy poza szybkością, Uncanny Dodge, szałem, BAB i CLAB). IWD2 ma opcode 436 Damage Reduction (np. SPWI807 Iron Body: p1 = 50 wartość, p2 = 3 zaczarowanie broni, które ją przebija; p1 = 0 → p1 = 5·p2). Propozycja: `DSBBNDR.SPL` (opcode 436, p1 = 1, timing 9) jako `AP_` na 11/14/17/20/23/26/29 – do sprawdzenia w grze, czy kolejne efekty się sumują i jaką wartość p2 daje „/–”.

**Paladyn – nakładanie rąk** jest w danych: `GA_SPIN109` (Lay on Hands, CLABPA01 poziom 1); SPIN109 leczy (opcode 17, p2 = 3) o pulę z `LAYHANDS.2DA` (wiersz PALADIN: 2, 4, … 40 = poziom × 2) – wartość liczy 0x71B9A0 do statystyki postaci +0x9B4. Nic do wyjmowania z exe; zmiana puli = edycja LAYHANDS.2DA.

**Błąd test16 poprawiony w test17:** obiekty tablic CLAB kitów leżały w końcówce .data (0xA1AF00 + 0x24·i); przy 8 kitach wychodziły poza sekcję (0xA1B000, .rsrc). Teraz `tabela2da` tworzy obiekt przez operator new (0x7FC95B), w .data są tylko wskaźniki (0xA1AF00–0xA1AF1F, pięść mnicha 0xA1AF20).

Nowe tabele (komponent 2): `DSKLASY.2DA`, `DSSNEAK.2DA` – wczytywane przy pierwszym użyciu (`tabela2da`, wskaźniki 0xA1AF20/0xA1AF24). Kod podklas zajmuje teraz 0x846900–0x846FCA (koniec wnęki 0x847000); dodatki 0x723430–0x723585.

Silnik obsługuje w CLAB prefiksy `FA_` (tylko tekst na karcie), `GA_` (zdolność wrodzona), `RA_`, `AP_` (efekty czaru nałożone od razu) – napisy w 0x8F9340, 0x8F9430, 0x8F94E0, 0x8F94C8.

## 10. Zdolności ras zaszyte w exe – rozpoznanie (2026-11-14)
Rasa i podrasa postaci: bajty `+0x26` i `+0x27` obiektu postaci (1 HUMAN, 2 ELF, 3 HALF_ELF, 4 DWARF, 5 HALFLING, 6 GNOME,
7 HALFORC; podrasa 0 czysta, 1/2 jak w SRLIST). Wrogowie: RACE.IDS (111 HOBGOBLIN, 112 KOBOLD, 113 OGRE, 153 GIANT,
155 GOBLIN, 160 ORC, 180 BUGBEAR).
| Miejsce | Co robi | Do tabeli |
|---|---|---|
| 0x722820 (tablica skoków 0x722D30) | przy nadawaniu zdolności: flaga 0x20000 w `+0x5BC` (widzenie w ciemności) dla aasimara, tieflinga, drowa, krasnoludów, głębinowego gnoma, półorka; głębinowy gnom dodatkowo 0x200000 i `+0x5E2` = [0x84EBBC] + 4 | tak: kolumna DARKVISION (+ osobno cecha głębinowego gnoma) |
| 0x73C8C0 (z ataku 0x73BBC9) | premia do trafienia: krasnolud +1 vs 111/155/160/180 (tablica 0x73C988), złoty krasnolud +1 vs aberracje (0x584AA0), gnom +1 vs 111/112/155/180 (0x73C9D8); olbrzym/ogr −4 (0x84EA98) przeciw krasnoludowi i gnomowi (bez głębinowego) | tak: wrogowie rasy + premia, KP przeciw olbrzymom |
| 0x73BC10, 0x73CA66 | niziołek: premia przy broni miotanej/procy (typy przedmiotów 14–29, tablica 0x73CAB4) | tak |
| 0x4A4963 | rzut obronny (typ efektu 0x18): +2 niziołek (strach?), +2 drow | tak |
| 0x4B551B | drow −1 (0x85BCE4), duergar (0x85BCE8) – prawdopodobnie wrażliwość na światło | do potwierdzenia |
| 0x6F6880, 0x6F8D51 | drow/duergar oraz głębinowy gnom – efekty zależne od obszaru (światło dzienne? niewykrywalność?) | do rozpoznania |
| 0x71E9AD | drow i głębinowy gnom: `+0x5F5` += 1 przy awansie (odporność na magię rośnie z poziomem) | tak |
| 0x584CC6, 0x5850AD | aasimar/tiefling wyłączeni z działania (niehumanoidy – np. czary na osoby) | tak |
| 0x7637AE | człowiek: dodatek przy pierwszym poziomie (premia człowieka) | do rozpoznania |
| 0x764020 | tiefling i głębinowy gnom: +2 do poziomu efektywnego | do rozpoznania |
| 0x73C7E1 | duergar: zależne od przedmiotu (`+0x12`, flaga 0x1 w `+0x40`) | do rozpoznania |
Propozycja: `DSRASY.2DA` – wiersze = nazwy wierszy ras z GetRaceRow (jak ABRACEAD: HUMAN_AASIMAR, …, HALF_ORC_MUL),
kolumny = cechy; `DSRWROG.2DA` – wrogowie rasy (lista RACE.IDS + premia). Brak wiersza = zachowanie oryginalne.

## 11. Test20: zdolności ras z tabel (RLAB, DSRASY, DSRWROG)
Kod `asm/rasy.asm` w **nowej sekcji PE `.dsras`** (RVA 0x621000 → adres 0xA21000, 4 KB, RWX, dopisana na końcu pliku;
NumberOfSections 5, SizeOfImage 0x622000). Zmienne 0xA21F00–0xA21FEF (postać dla tablicy rasy, wskaźniki tabel,
pamięć podręczna 16 tablic RLAB). Exe paczki 2 ma więc 5 033 984 B; makra WeiDU dopisują sekcję `INSERT_BYTES`.
| Hak | Zmiana |
|---|---|
| 0x546030 GetClabTable | `clab_rasa`: klasa 12 → tablica z kolumny RLAB wiersza rasy postaci w DSRASY; inne → `clab` (podklasy) |
| 0x722DE3 (procedura CLAB) | `poziom`: dla klasy 12 poziom postaci (statystyki +0x46) zamiast 0x447990 |
| 0x71E996 (awans, po 11 wywołaniach CLAB klas) | `rasa_awans`: procedura CLAB 0x722D50 dla klasy 12 (zdobyte poziomy postaci); przyrost odporności na magię = SR_LEVEL × zdobyte poziomy (brak wartości → oryginał: drow i gnom głębinowy +1) |
| 0x722862 (nadawanie cech rasy 0x722820) | `wzrok`: DARKVISION → flaga 0x20000; gnom głębinowy zachowuje pozostałe cechy (0x200000, +0x5E2) |
| 0x73BC10, 0x73CA66 + operandy 0x73BC4E, 0x73CA9B | `miot_atak`/`miot_info`: THROWN zamiast „niziołek”, premia z `miot_wart` zamiast 0x84EAA8 |
| 0x73C8C0 (premia rasowa do trafienia, z 0x73BBC9) | `wrogowie`: DSRWROG (BONUS × E1–E6 = rasa celu z RACE.IDS, ABERRATION przez 0x584AA0); olbrzym (153) / ogr (113) atakujący − GIANT_AC rasy celu; bez DSRWROG → oryginalna funkcja |
Wiersze tabel = nazwy z GetRaceRow (jak ABRACEAD). Brak tabeli / wiersza / kolumny = zachowanie oryginalne.
Tablica RLAB rasy: format CLAB, kolumny = poziom postaci (suma klas) 1–30; działa przy tworzeniu postaci i awansie.
**Poprawiony błąd test14–19:** łatka maski bóstw pisała 0xFFFF8000 pod adres instrukcji (0x61CEF4, 0x615CFE) zamiast pod
operand (0x61CEF5, 0x615CFF), niszcząc kod (`and eax` / `mov ecx`) przy zmianie bóstwa i przycisku Gotowe kapłana.
Skrypt: `tools/iwd2_podklasy_exe.py --base IWD2_1920x1080_test13.exe --out test20.exe` (sekcja + trzy pliki asm),
`tools/iwd2_paczki_exe.py` (makra, w tym dopisanie sekcji).

## 12. Test21: progresja klas z DSKLPROG.2DA (PW, BAB, rzuty obronne)
Kod w `asm/rasy.asm` (sekcja `.dsras`, do 0xA21798); wynik wyboru zapamiętany w 0xA21B00 (3 × 11 dword), tablice
wczytane po nazwie w pamięci podręcznej 0xA21C00 (64 wpisy, wspólna z RLAB). Obiekty tabel w regułach (+offset):
Save Prs 0x214, War 0x238, Wiz 0x25C, Rog 0x280, Brd 0x2A4, Monk 0x2C8; HP War 0x310, Wiz 0x334, Prs 0x358, Rog 0x37C,
Barb 0x3A0, Monk 0x3C4; BAAT FGT 0x18A0, NFG 0x18C4, MAG 0x18E8, MKU 0x190C.
| Miejsce | Zmiana |
|---|---|
| 0x542CB0 (PW przy awansie; switch po klasie, tablica 0x542E88) | 5 × `lea r, [edi+tabela]` (0x542D30, 0x542D90, 0x542DDA, 0x542E24, 0x542E6E) → `call hp_ecx/hp_edx/hp_eax` (kolumna HP); barbarzyńca: wymuszona kość 12 wyłączona (0x542D54 = 0), domyślnie HPBARB |
| 0x542610 (suma rzutu obronnego po 11 klasach) | 11 × `lea ecx, [edi+SAVExxx]` (0x542677 … 0x54296F) → `call sv_N` (kolumna SAVE) |
| 0x546B60 (premia do ataku, bloki klas inline) | 10 bloków odczytu → `push N; call bab_tab; jmp` (kolumna BAB); mnich z bronią 0x546F37 → `call bab_mnich`, bez broni BAATMKU |
Przewodnik dodawania ras i klas: `docs/dodawanie_ras_i_klas.md`.

## 13. Test22: progresja podklas (wiersze podklas w DSKLPROG)
Podklasa = dword postaci +0x80C (getter 0x728570). `prog_k(kolumna, klasa, postać)`: wiersz podklasy (bity 0xFF000000 →
nazwa z tabeli 0x846C00, tylko gdy +0x17 = klasa; inne kity → `GetClassRow(klasa, kit)`), potem `prog` (wiersz klasy).
Pamięć podręczna 0xA22000 (64 wpisy: klucz, kit, tablica). Sekcja `.dsras` powiększona do 8 KB (kod 0xA21000–0xA21FFF,
dane 0xA22000–0xA22FFF; exe paczki 2 = 5 038 080 B).
Skąd postać: premia do ataku – 1. argument 0x546B60; rzuty (0x5429B0) i PW (0x542FA0) dostają tylko typ obiektu i
statystyki (w kreatorze i na ekranie awansu kopie tymczasowe), więc 17 miejsc wywołania zapamiętuje postać w CTX
(0xA22F18): `ctx_sv_ebp` 0x5D8F3A/5B/7C, 0x5D8FAB/D4/FD; `ctx_sv_esi` 0x612A1E/3F/60, 0x737A05/20/3B, 0x737DB8/D3/EE;
`ctx_hp_ebp` 0x5D908F; `ctx_hp_esi` 0x6129EB.

## 14. Listy czarów – rozpoznanie (2026-11-14)
- **LISTSPLL.2DA**: jedna tabela, kolumny po pozycji (nazw kolumn nie ma w exe): BRD CLR DRD PAL RGR SOR WIZ, wartość = poziom
  czaru 1–9 (0 = czaru nie ma na liście), ostatnia kolumna SPELL_RES_REF. Przy starcie (0x59D778) gra buduje 7 list w obiekcie
  reguł: +0x4C18 + 0x4C·i (i = 0..6, budowa 0x5CA2A0). Inne kolumny są pomijane.
- **Klasa → lista**: `0x5CA5D0(&klasa)` (33 wywołania; 12 z nich liczy adres listy, reszta używa wyniku jako numeru księgi czarów postaci 0–6 – zob. sekcja 16): bard 0, kapłan 1, druid 2, paladyn 3, tropiciel 4, zaklinacz 5,
  czarodziej 6; barbarzyńca, wojownik, mnich, łotrzyk → asercja. Funkcja dostaje tylko numer klasy – **podklasa nie ma wpływu**.
- **LISTDOMN.2DA**: 9 kolumn bóstw (CIL CLA CSE CHE COG CTE CBA CMA CTA) → 9 list domen +0x4E2C + 0x4C·i (0x59D851).
  Bóstwo → indeks: `0x5CA910(&kit)` po bitach 0x8000 … 0x800000 (0–8); inny bit → asercja i indeks 10 (poza 9 listami).
  Wywołania: 0x5CAD72, 0x5E6303, 0x60B871 – kit maskowany `and 0xFF8000` (0x5E62E6, 0x60B85B).
  **Problem podklasy CLERIC_DS (bit 0x04000000)**: po masce zostaje 0 → asercja i lista spoza tablicy.
- **LISTINNT / LISTSONG / LISTSHAP** → +0x4C00 / +0x4C08 / +0x4C10 (wrodzone, pieśni barda, kształty druida).
- **LISTMAGE.2DA** (kolumny szkół) – brak odwołania w exe (nieużywana); szkoły przeciwne – kod 0x703170.
- **Liczba czarów na dzień**: MXSPLBRD/CLR/DRD/PAL/RGR/SOR/WIZ (obiekty reguł +0x454 … +0x52C), MXSPLBON (premia z cechy),
  SPLSRCKN (znane czary zaklinacza) – wybór tabeli po klasie w kodzie.
- **CRE V2.2** trzyma osobną księgę czarów każdej z 7 klas czarujących + domeny + wrodzone/pieśni/kształty – podklasa
  zapisuje czary w księdze swojej klasy; klasy bez księgi (barbarzyńca, wojownik, mnich, łotrzyk) nie mogą mieć listy czarów.

## 15. Test23: domeny bóstwa podklasy kapłana DS
- Hak 0x5CA910 (GetDomainIndex) → `domena`: kit z bitem 0xFF000000 należący do kapłana (wpis 0x846C00, +0x17 = 3) → lista
  domen budowana raz z `LISTDOMN.2DA` (kolumna poziomu = DSKLPROG, wiersz podklasy, kolumna DOMAIN; kolumna nazw
  `DOMAIN_RESREF`) do obiektu listy w `.dsras` (0xA22400 + 0x4C·k, konstruktor 0x59EB60, budowa 0x5CA2A0(tabela,
  &kol_poziomu, &kol_nazw, 0)). Zwracany indeks = ((adres − (reguły + 0x4E2C)) >> 2) · 19⁻¹ mod 2³² – wzór gry
  `reguły + 0x4E2C + idx·0x4C` daje wtedy adres naszej listy bez zmian w trzech miejscach wywołań.
- Maski kitu przed wywołaniem: 0x5E62E6 i 0x60B85B `and 0xFF8000` → `and 0xFFFF8000` (bit podklasy DS dociera do funkcji).
- Kit z bitem DS innej klasy (postać wieloklasowa) → oryginalny wybór po bitach bóstw gry; podklasa kapłana DS bez
  konfiguracji → indeks 0 (domeny Ilmatera) zamiast asercji.
- Pozostałe maski 0xFF8000 (0x541DF6, 0x547303, 0x5E10D7, 0x5E20C8, 0x5E61FF, 0x5E66EE, 0x5E674C, 0x62A59C, 0x7231A2,
  0x763EEC, testy 0x5B9BFE / 0x5BA106) zostają: dla kapłana DS dają „brak bóstwa gry” (np. kolumny bóstw w FEATS/SKILLS).

## 16. Test24: listy czarów podklas DS (LISTSPLL, kolumna SPELLS w DSKLPROG)
- **Dwa użycia `0x5CA5D0`.** Wynik jest (a) indeksem listy: `reguły + 0x4C18 + idx·0x4C` – 13 miejsc, albo (b) numerem
  księgi czarów postaci 0–6 (`cmp idx, 7`, `shl idx, 8` + 0x4284 w CGameSprite itd.) – 20 miejsc. Funkcja zostaje bez zmian;
  podmieniamy tylko wywołania typu (a), więc księgi w CRE dalej są księgami klas.
- **Haki (a)** – `call 0x5CA5D0` → stub podający postać w eax → `lista_klasy` (wynik oryginalny, a gdy postać jest
  CGameSprite (vtable 0x85BDD4), ma kit DS należący do tej klasy i wiersz podklasy w DSKLPROG ma w kolumnie `SPELLS`
  nazwę kolumny LISTSPLL: indeks tej listy wg wzoru z sekcji 15, baza +0x4C18):

  | Miejsce | Funkcja | Co robi | Postać |
  |---|---|---|---|
  | 0x4BCA66 | 0x4BC8C0 (vtable efektu 0x84997C) | nauka czaru czarodzieja (zwój), klasa 11 | cel efektu, `[esp+0x70]` w stubie |
  | 0x5D9BAB, 0x5D9C50 | 0x5D9970 | ekran wyboru czarów barda / zaklinacza | 1. argument, `[esp+0xA4]` |
  | 0x5E14B0, 0x5E152B | 0x5E0FD0 | j.w. (druga ścieżka ekranu) | 2. argument, `[esp+0x94]` |
  | 0x60EFD2, 0x60F092 | 0x60EF70 | ekran czarów kreatora (klasa z postaci +0x3E3E) | 1. argument, `[esp+0x90]` |
  | 0x61827A, 0x618496 | 0x617D80 | nauka czarów czarodzieja przy awansie, klasa 11 | zmienna lokalna, `[esp+0x1C]` |
  | 0x618D5F, 0x618DBB | 0x618D10 | j.w. | 2. argument, `[esp+0x60]` |
  | 0x71EABB | 0x71E9F0 (CGameSprite) | awans: czary kapłana, druida, paladyna, tropiciela (cała lista do księgi) | ebp (this) |

  Pominięte: 0x4EDCB7 (0x4EDCA0 – kod konsoli „wszystkie czary klasy”, lista klasy) i 0x5CAD14 (poziom czaru, niżej).
  Przesunięcia stosu sprawdzone względem odczytów tego samego argumentu w funkcji (wywołania między nimi zdejmują swoje argumenty).
- **Poziom czaru** `0x5CAC30(resref, klasa, kit)` (ret 0xC, 9 = brak): wywołania 0x4ED086, 0x629996, 0x62B3A8, 0x716728 →
  `poziom_czaru`: oryginał, a przy wyniku 9 – szukanie numeru czaru (tablica reguł +0x4BF8, 8 B na czar) na listach
  podklas DS tej klasy (bez postaci; lista budowana przy pierwszym użyciu). Lista klasy ma pierwszeństwo.
- **Budowa list** – wspólna `lista_kitu(nr, opis)` dla domen (test23) i list klas: wiersz podklasy w DSKLPROG, kolumna
  z opisu (`DOMAIN` / `SPELLS`) → nazwa kolumny w LISTDOMN / LISTSPLL (wczytane własną kopią przez cache 2DA), kolumna nazw
  `DOMAIN_RESREF` / `SPELL_RES_REF`, konstruktor 0x59EB60, budowa 0x5CA2A0. Listy klas: 0xA22780 + 0x4C·k, flagi 0xA229F0,
  parametry 0xA229F8.
- Instalator (komponent 5): kolumna `SPELLS` w DSKLPROG (`CLR_DS` dla CLERIC_DS, reszta `*`), kolumna `CLR_DS` w LISTSPLL
  za `SPELL_RES_REF` (kopia `CLR`, do decyzji właściciela).
- Kod `.dsras` 0xA21000–0xA21CB0 (3248 B).
