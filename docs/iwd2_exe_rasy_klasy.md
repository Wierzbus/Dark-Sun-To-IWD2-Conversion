# IWD2.exe – rasy, podrasy, klasy i kity: mapa miejsc zaszytych w kodzie

Plik: IWD2.exe z instalacji GOG, wersja 2.01 (v2.01.1016), 5 029 888 B,
sha256 `18e01d21855f88702c062497aa25dfb42928671973d3b929e42206def2d9df2a`.
Układ PE: ImageBase 0x400000, offset w pliku = adres − 0x400000 dla wszystkich sekcji
(.text 0x401000, .rdata 0x847000, .data 0x8A5000). Narzędzie: `tools/iwd2_re.py` (objdump + Python).
Stan: podrasa mula zrobiona (łatki w `iwd2_exe_gui_1920.md`); podklasy paladyna, barbarzyńcy i kapłana – prototyp (sekcja 7).

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
| paladyn ≥ 2 | 0x4A48CF, 0x6F8EF4 | to samo dla sojuszników w promieniu 100 (aura) | do zrobienia: brak opcode'u aury – zostaje w exe |
| kapłan + paladyn | 0x71B8D0 | poziom odpędzania nieumarłych = kapłan + (paladyn − 2) | wzór, nie zdolność – zostaje |
| mnich 1–30 | 0x723412 | pięść mnicha: przedmiot 00MFIST1–9 zależnie od poziomu (tabela 0x723808, 11 przypadków) | **zrobione (test18)**: hak 0x723417 → `mnich`: przedmiot = wpis `FI_<ITM>` w CLAB mnicha (GetClabTable(6, kit)) w najwyższej kolumnie ≤ poziomowi, domyślnie 00MFIST1; tabela 0x723808 nieużywana. Parser CLAB (0x723093) pomija nieznany prefiks bez asercji |
| mnich | 0x72E354 | +poziom/3 do licznika (prawdopodobnie użycia ataku ogłuszającego) | do rozpoznania |
| mnich ≥ 8, ≥ 12 | 0x739FE4 | −1/−1 do wartości 0x5604 (zakres 0–10; prawdopodobnie szybkość broni) | do rozpoznania |
| mnich | 0x73E194, 0x73E390 | ST = wartość + poziom/2 − 1 (ogłuszenie / drżąca dłoń) | wzór – zostaje |
| druid ≥ 9 | 0x4A7956 | efekt trucizny z typem 0x20 odrzucany (odporność na jad naturalny) | **zrobione (test17)**: warunek wyłączony (0x4A795E `jl` → `jmp`), `DSDRVEN.SPL` (opcode 101, 25 Poison – każda trucizna, decyzja właściciela) jako `AP_` na 9. poziomie CLABDR01–04 |
| barbarzyńca + mnich | 0x72E2EF, 0x72E330 | szybkość ruchu: barbarzyńca ×1,2 (stała 0x84EB58) bez ciężkiego pancerza (0x724690(3)); mnich + poziom/3 bez pancerza, +1 z atutem 0xC | warunek pancerza nie da się zapisać w SPL – zostaje w exe |
| mnich ≥ 20 | 0x73A7B7, 0x73AA3F | atak bez flagi 0x40 (niemagiczny?) nie działa (Perfect Self) | do rozpoznania flagi |
| łotrzyk | 0x585D50, 0x585D80 (wołane z walki 0x73D9B6) | kości ataku z zaskoczenia = (poziom − 1)/2 + 1, kość k6 – **tego używa walka** | **zrobione (test18)**: `DSSNEAK.2DA` (wiersz = poziom: DICE; SIDES z 1. wiersza); brak opcode'u na kości ataku z zaskoczenia w IWD2 |
| łotrzyk | 0x71B910 → statystyka 0x9B2 | mnożnik ciosu w plecy z BACKSTAB.2DA (pozostałość BG) – liczony, ale walka go nie używa (czytany tylko w 0x46Cxxx) | zostaje |
| łotrzyk ≥ 2, mnich | 0x585DA0 (z obrażeń 0x4AA0D9, flaga efektu 0x8 = rzut na Refleks) | Unik: udany rzut = brak obrażeń; nie gdy bezradny (stan 0x829) ani w średnim/ciężkim pancerzu (0x724690(2/3)); Improved Evasion to atut 31 (0x4AA343) | **zrobione (test18)**: progi z `DSKLASY.2DA` wiersz EVASION (kolumny = klasy) |
| barbarzyńca ≥ 2, łotrzyk ≥ 3 | 0x73BA1D | Uncanny Dodge: brak utraty premii ZRĘ do KP wobec niewidzialnego atakującego (bez atutu Blind Fight 6) | **zrobione (test18)**: `DSKLASY.2DA` wiersz UNCANNY_DEX |
| barbarzyńca ≥ 5, łotrzyk ≥ 6 | 0x73D95B (komunikat 82 „Uncanny Dodge prevented flank attack”) | Uncanny Dodge: brak ataku z zaskoczenia z flanki, chyba że łotrzyk atakującego ≥ poziom celu + 4 | **zrobione (test18)**: `DSKLASY.2DA` wiersz UNCANNY_FLANK (poziom z bajtów postaci +0x626+klasa) |
| łotrzyk > 0 | 0x4A6744 | atut Slippery Mind (0x3A): ponowny rzut obronny na Wolę | atut – zostaje |
| łotrzyk / mnich | 0x757A80 | akcja ukrycia (tryb 2) tylko dla łotrzyka i mnicha | akcja – zostaje |
| tropiciel | 0x73BC88, 0x73DD3F | ulubiony wróg: premia z tabeli (0x546860) i +4 | wzór z danych – zostaje |
| barbarzyńca < 20 | 0x4A5C79 | po szale zmęczenie (od 20. poziomu brak) | do rozpoznania |
| barbarzyńca ≥ 15 | 0x5E5B22 | do rozpoznania | – |
| paladyn + wojownik | 0x737BBE | upadły paladyn: poziomy paladyna przechodzą na wojownika | mechanika, nie zdolność – zostaje |
Inne dostępy do poziomu klasy: `0x762760(klasa)` i `0x762830(klasa)` na postaci, `0x40D7E0(klasa)` (przynależność do klasy; stałe klas w 0x847CA5–0x847CAF), bajty postaci `+0x626+klasa` (walka), statystyki 96–106 (CLASSLEVEL*) w GUI. Dalsze miejsca mnicha: 0x4A4A25 (≥ 3: +2 przeciw szkole 4 – Still Mind), 0x584CE7 (≥ 20: odporność na część stworzeń po animacji), 0x723F66 (pięść/broń mnicha).

**Szybkość ruchu (propozycja, niewdrożone):** premię barbarzyńcy ×1,2 (0x72E2EF) można dać przez CLAB (`AP_`, efekt zmiany szybkości ruchu), a warunek pancerza przenieść na przedmioty: ciężkie pancerze dostają efekt przy założeniu „Use EFF file” z warunkiem klasy BARBARIAN, który znosi premię. Do sprawdzenia, czy IWD2 obsługuje te opcode'y tak jak IWD.

**Błąd test16 poprawiony w test17:** obiekty tablic CLAB kitów leżały w końcówce .data (0xA1AF00 + 0x24·i); przy 8 kitach wychodziły poza sekcję (0xA1B000, .rsrc). Teraz `tabela2da` tworzy obiekt przez operator new (0x7FC95B), w .data są tylko wskaźniki (0xA1AF00–0xA1AF1F, pięść mnicha 0xA1AF20).

Nowe tabele (komponent 2): `DSKLASY.2DA`, `DSSNEAK.2DA` – wczytywane przy pierwszym użyciu (`tabela2da`, wskaźniki 0xA1AF20/0xA1AF24). Kod podklas zajmuje teraz 0x846900–0x846FCA (koniec wnęki 0x847000).

Silnik obsługuje w CLAB prefiksy `FA_` (tylko tekst na karcie), `GA_` (zdolność wrodzona), `RA_`, `AP_` (efekty czaru nałożone od razu) – napisy w 0x8F9340, 0x8F9430, 0x8F94E0, 0x8F94C8.
