# Pierwszy obszar Dark Sun → AR9022 (IWD2)

## Który region jest pierwszy
Postacie z ETAB regionów (`creatures.csv` + ETAB) wskazują RGN29: Kurzak, Legcrusher, Scar ze swoimi ludźmi, Merzol, Mirlon, Dinos, Gilal, Trustee, templariusze i straż areny. To cele niewolników pod areną w Draj, gdzie zaczyna się gra. Ten sam układ (basen, korytarze) ma AR9021 zrobiony wcześniej ze zrzutu ekranu. AR9022 powstaje z danych gry, nie ze zrzutu.

## Format regionu (ustalone na plikach, `darksun/region.py`)
| Zasób | Zawartość |
|---|---|
| TILE 1–254 | kafelek 16×16 w formacie BMP Dark Sun |
| RMAP | 128 × 98 B: numer kafelka |
| GMAP | 128 × 98 B: bit 0x80 mur, bit 0x40 pole nieprzechodnie (mur, woda, przeszkoda), bity 0–3 wartości 1–13 przy murach (? wysokość/oświetlenie) |
| ETAB | rekordy 8 B: `u16 x, u16 y` (lewy górny róg sprite'a w pikselach), `u8 z`, `u8 flagi` (13–15), `i16 −id` (OJFF/RDFF) |
| paleta | GPLDATA PAL o id = numer regionu (RGN29 → PAL 41) |

OJFF (16 B) pole 6 = id grafiki BMP obiektu (SEGOBJEX). Sprite wklejony w (x, y) z ETAB pokrywa się z obrazem gry (sprawdzone wizualnie).
RGN29: 30 postaci (17 różnych), 268 obiektów (meble, beczki, łóżka, broń na stojakach), 112 przedmiotów.
Kafle: podłoga 28, cień przy murze 26, cegła (góra muru) 2, lico muru 18/19/21, basen 171.

## Rzut 45° (jak AR9021)
`darksun/obszar45.py` używa tej samej geometrii co `tools/rotuj_plan.py`: skrócenie K = 0,75, obrót o 45°, mur wyciągnięty o 32 px, cegła tylko do 40 px w głąb (dalej czerń jak we wnętrzach BG1), cień muru. Różnice względem AR9021:
- mury z GMAP (bit 0x80) zamiast z kolorów zrzutu; ślad muru bez dolnego wiersza (lico narysowane w rzucie Dark Sun),
- podłoga z kafla podłogi, zdobienia (basen, płyty) z obrazu regionu,
- obiekty ETAB jako sprite'y w punkcie stopy (wszystkie, nie tylko widoczne na zrzucie),
- SR: mur = 0, przeszkoda (GMAP 0x40 i podstawy sprite'ów) = 8, reszta 1; palety SR/HT/LM z AR9021.
Wynik: 2966 × 2266 px, 47 × 36 kafli, 810 unikalnych kafli, 64 wielokąty ścian.

## Postacie, dialogi, skrypty (`tools/ds_obszar.py`)
- **Aktorzy ARE:** położenie ze stopy sprite'a postaci, przeliczone do rzutu i przesunięte na najbliższe przechodnie pole SR. Bajt 0x2F = 7 (w IWD2 bez bitu 0 aktor znika przy wczytaniu obszaru).
- **CRE** (`darksun/cre_iwd2.py`): wersja robocza (HP, cechy, klasa, poziom, animacja, charakter z Dark Sun; BAB i rzuty 3E). Pełna konwersja według przewodnika: `docs/ds_cre_guide.md`. Bez ekwipunku i czarów.
- **Dialogi:** D WeiDU z tekstów wyzwalacza „rozmowa” (GPL). Szkic liniowy: kolejne wypowiedzi NPC, opcje gracza jako odpowiedzi prowadzące do następnej wypowiedzi, „Goodbye” kończy. Warunków gałęzi GPL jeszcze nie odczytujemy.
- **Skrypty BAF** (slot Override): straż wroga w Dark Sun (allegiance 2) staje się wrogiem po ataku drużyny; wrogowie atakują najbliższego przeciwnika. Okrzyki w walce z wyzwalacza „atak” wyłączone domyślnie (`--okrzyki`), bo wydobycie skleja w nich przypadkowe teksty.
- Nazwy: CRE `DS29nnnn`, dialog `DD29nnnn`, skrypt `DB29nnnn` (nnnn = id RDFF).

## Do decyzji i dalszej pracy
1. Wejście do obszaru: dziś pierwszy przechodni punkt SR; w Dark Sun drużyna zaczyna w celi – do wskazania.
2. Wrogość straży od początku (EA ENEMY) czy po ataku (obecnie).
3. Drzwi (OJFF „Door”) są dziś sprite'ami; drzwi IWD2 wymagają poligonów WED – następny etap.
4. Przedmioty na ziemi i w pojemnikach (112) – po konwersji ITM (`docs/ds_itm_reguly.md`).
5. Warunki gałęzi dialogów i zmienne GPL → zmienne IWD2.
