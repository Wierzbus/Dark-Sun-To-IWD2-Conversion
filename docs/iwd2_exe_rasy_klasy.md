# IWD2.exe – rasy, podrasy, klasy i kity: mapa miejsc zaszytych w kodzie (etap 1)

Plik: IWD2.exe z instalacji GOG, wersja 2.01 (v2.01.1016), 5 029 888 B,
sha256 `18e01d21855f88702c062497aa25dfb42928671973d3b929e42206def2d9df2a`.
Układ PE: ImageBase 0x400000, offset w pliku = adres − 0x400000 dla wszystkich sekcji
(.text 0x401000, .rdata 0x847000, .data 0x8A5000). Narzędzie: `tools/iwd2_re.py` (objdump + Python).
Stan: tylko analiza, bez łatek.

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
- `KITTABLE` / `K_<klasa>_<rasa>.2DA`: listy kitów dla par klasa+rasa (np. K_C_H: 0, 19, 20, 21).

### Ekrany kreatora (GUICG.CHU, oryginał z BIF)
| Okno | Tytuł | Przyciski wyboru | Zajęte |
|---|---|---|---|
| 8 | Race | 2–8 (7) | 7 |
| 54 | Subrace | 1–4 (4) | maks. 3 (czysta + 2) |
| 2 | Class | 2–12 (11) | 11 |
| 52 | (bóstwo / zakon) | 1–10 (10) | kapłan 9 |
| 12 | Wizard (szkoła) | 8 | 8 |
Wniosek: w oknie podras jest 1 wolne miejsce dla każdej rasy (3 dla półelfa i półorka); w oknie klas brak miejsca.

## 2. Co jest zaszyte w kodzie

Wszystkie nazwy wierszy ras, podras, klas i kitów są globalnymi napisami (CString, konstruktor 0x7FCC88,
przypisanie 0x7FC98F) i każda jest użyta **dokładnie w jednej funkcji**:

### 0x541940 – nazwa wiersza rasy: `CString GetRaceRow(BYTE rasa, BYTE podrasa)`
- Konwencja: ukryty wskaźnik wyniku + 2 argumenty, `ret 0xC`.
- `rasa − 1` przez tablicę skoków 0x541BFC (7 wpisów: człowiek, elf, półelf, krasnolud, niziołek, gnom, półork);
  w każdej gałęzi podrasa 0/1/2 → napis (np. 0x8DE958 „HUMAN_AASIMAR”).
- Półelf: asercja, gdy podrasa ≠ 0. Inne przypadki: asercja (0x780C00) i pusty napis.
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
użyciem każdy – funkcje ładujące w okolicy 0x53EF8B–0x5401A1.

## 3. Wnioski dla externalizacji

1. **Podrasa (najmniejszy zakres)**: wpisy w `SR_<rasa>.2DA` + `SRLIST.2DA` + wiersze w tabelach cech
   wystarczą kreatorowi (do sprawdzenia w grze), ale 0x541940 zwróci pusty napis dla nowego ID
   → tabele cech nie znajdą wiersza. Łatka: zastąpić gałęzie 0x541940 odczytem nazwy wiersza z SRLIST
   (rasa przez SR_<rasa>, podrasa przez kolumnę ID).
2. **Kit**: nowy bit z wolnej puli + łatka 0x541DA0 (odczyt nazwy z KITLIST po bicie) + wpisy K_*_*.2DA.
   Okno kitów ma 10 miejsc; dla klas bez kitów trzeba sprawdzić, czy kreator w ogóle pokazuje okno 52.
3. **Rasa i klasa bazowa**: tablice skoków na 7 ras i 11 klas, a okna kreatora mają stałą liczbę przycisków;
   do tego zapewne inne porównania kodu klasy/rasy w wielu miejscach (etap 2: wyszukanie porównań
   z polami rasy/klasy obiektu postaci).

## 3a. Przegląd wszystkich tabel 2DA (312 plików: BIF + Override) – odwołania do podras
| Tabela | Postać odwołania | Używana przez EXE | Mul (komponent 1) |
|---|---|---|---|
| SRLIST | wiersze podras (nazwa, teksty, ID, palety) | tak | dopisany |
| SR_D/E/G/H/HE/HF/HO | listy wierszy SRLIST dla rasy | tak (przez SRTABLE) | SR_HO dopisany |
| ABRACEAD, ABRACERQ, RACESPAB, RACERSMD, SKILLRAC | wiersze po nazwie podrasy | tak | dopisane |
| SAVERACE | wiersze po nazwie; półork jako „HALFORC” (błąd w grze – wiersz nigdy nie pasuje) | tak | dopisany |
| STRTXP | startowe PD podras z ECL (wiersze po nazwie) | tak | dopisany (0) |
| FEATS, SKILLS | **kolumny** ras/podras pod innymi nazwami (AASIMAR, DROW, GOLD_DWARF, STRONGHEART_HALFLLING…) z danymi (np. elfie broń, premie do umiejętności); nazw kolumn nie ma w EXE → wybór kolumny po numerze w kodzie | tak (pośrednio) | **brak – wymaga łatki etapu 2** |
| KITTABLE, SRTABLE | kolumny/wiersze tylko ras (bez podras) | tak | nie trzeba |
| RACEXPMD, SUBRACES | wiersze/kolumny podras, inne nazwy (ELF_WOOD, HALFLING_LIGHTFOOT) | **nie** (brak odwołań w EXE) | nie trzeba |
| CHARSTR, CRELIGHT, REVERB, SPRKLCLR | dźwięki postaci / światło potworów / pogłos / kolory iskier – zbieżność słów | nie dotyczy | nie trzeba |
Brakujący wiersz w tabeli „po nazwie” nie wywraca gry (przykład: SAVERACE/HALFORC), ale cecha wtedy nie działa.

## 4. Następne kroki
- Etap 2: wybór kolumny rasy/podrasy w FEATS i SKILLS (mapowanie numeryczne w kodzie); miejsca porównujące kod rasy/klasy i maski kitów poza dwiema funkcjami; kod kreatora
  (budowanie listy podras z SR_*.2DA, warunek wyświetlenia okna kitów).
- Test bez łatek: dopisanie podrasy półorka w SR_HO/SRLIST/ABRACEAD i sprawdzenie, czy pojawia się w kreatorze
  (oczekiwany wynik: pojawi się, ale cechy z tabel nie zadziałają do czasu łatki 0x541940).
