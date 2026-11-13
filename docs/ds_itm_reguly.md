# Przedmioty Dark Sun → ITM IWD2: propozycja reguł (do decyzji właściciela)

Narzędzie: `tools/ds_itm_plan.py --ds build/darksun --out build/ds_itm`. Tworzy `ds_itm_plan.csv` (każdy przedmiot RDFF: reguła, typ IWD2, parametry, ikona) i `ds_itm_unresolved.csv`. Pliki zawierają nazwy z gry, więc zostają poza Gitem.
Zasada jak w BGtoIWD2 (`docs/zasady_konwersji_i_zgodnosci.md`): **reguły, nie lista wyjątków**. Każdy wiersz zapisuje, która reguła zadziałała. Czego reguła nie rozstrzyga, trafia do `*_unresolved.csv`. Nadpisania właściciela mogą stać nad regułami.

## Wejście (Dark Sun)
- Rekord przedmiotu RDFF (21 B): `item_index` → typ IT1R, `name_idx` → NAME, `icon` / OJFF → grafika BMP, `bonus` (premia magiczna), `charges`, `value`.
- IT1R (20 B): `weapon_type`, `placement` (miejsce), `dice`/`sides`/`mod`, `weight` (1/10 funta), `base_ac`, `flags`, `material`, `legal_class`.
- Wartości `placement` z danych: 1 tułów, 2 pas, 3 ramiona, 4 stopy, 5 dłoń, 6 głowa, 7 szyja, 8 plecy (płaszcz), 9 palec, 10 nogi, 11 amunicja, 12 broń dystansowa, 0 brak (obiekty świata i rzeczy w plecaku).
- `flags` IT1R: 0x80 pancerz. Przy `placement` 0 wartość różna od 0 (0x25 drzwi, 0x04, 0x14, 0x15 skrzynie i zasłony, 0x0D…) oznacza obiekt świata, a nie przedmiot.

## Reguły (pierwsza pasująca wygrywa)
| Reguła | Warunek | Wynik IWD2 | Liczba (stan danych) |
|---|---|---|---|
| R0 OBIEKT | `placement` 0 i `flags` ≠ 0 | **nie ITM**: drzwi / pojemnik / punkt informacji w ARE (słowo w nazwie) | 478 |
| R1 PANCERZ | flaga 0x80, miejsce 1/3/10/6 | tułów → pancerz, ramiona → karwasze, nogi → buty, głowa → hełm; KP z `base_ac` | 207 |
| R2 TARCZA | `weapon_type` 4 | tarcza; wielkość z `base_ac` (1 mała, 2 średnia) | 16 |
| R3 BROŃ | miejsce 5, `weapon_type` 1/17 | typ broni wg słowa w nazwie typu IT1R, potem nazwy przedmiotu, potem kości i wagi; obrażenia `dice d sides + mod` | 189 |
| R4 DYSTANS | miejsce 12 | 2 proca, 10 łuk, 18 chatkcha → broń rzucana | 57 |
| R5 AMUNICJA | miejsce 11 | strzały | 49 |
| R6 UBIÓR | miejsca 2, 4, 7, 8, 9 | pas, buty, amulet, płaszcz, pierścień | 69 |
| R7 RZECZ | miejsce 0 bez flag (lub dłoń bez broni) | zwój, różdżka, księga, klucz, klejnot, mikstura, różne (słowo w nazwie) | 275 |
| — | brak typu IT1R (pułapki) | `ds_itm_unresolved.csv` | 10 |

Typ broni (R3), gdy nazwa nic nie mówi: d4 i waga ≤ 1 funta → sztylet; d10 i waga ≥ 10 funtów → halabarda; d10 → topór; d8 → duży miecz przy wadze ≥ 3 funty, inaczej mały; reszta → buława. Ostrze nazwane jak sztylet, ale z kością d6 lub większą, to mały miecz.

## Parametry
| Pole ITM IWD2 | Źródło | Reguła |
|---|---|---|
| typ | reguła | kody ITM (IESDP); typ pancerza i tarczy IWD2 (0x3C–0x44, 0x2F/0x31/0x35) wybiera generator BGtoIWD2 po medianie wagi (`entities/itm_map.py`) |
| szablon | IWD2 | przedmiot tego samego typu (`entities/itm.py`): biegłość, maska użytkowników, animacja |
| obrażenia | IT1R | `dice`, `sides`, premia `mod` jako premia do obrażeń |
| premia magiczna / enchantment | RDFF `bonus` | +N do trafienia i obrażeń (broń), +N KP (pancerz/tarcza); `bonus` > 0 = przedmiot magiczny |
| KP | IT1R `base_ac` (+ `bonus`) | pancerz: KP zbroi Dark Sun z części tułowia; karwasze i buty z części ramion i nóg dają KP jako premię przedmiotu |
| waga | IT1R `weight` / 10 | funty |
| cena | RDFF `value` | 1:1 (jednostka do sprawdzenia: cena w ceramicznych monetach) |
| ładunki | RDFF `charges` | różdżki i zwoje; wartości 256/1280 wyglądają na pole bitowe (bajt ładunków + bajt czaru) – do sprawdzenia |
| ikona | grafika BMP | `DSI####` (przedmiot), `DSG####` (ziemia) z `tools/ds_ikony.py` |
| nazwa i opis | NAME + teksty oględzin (`items.csv`) | przez SAY w WeiDU; teksty gry nie trafiają do Gita |

## Do decyzji właściciela
1. **Zbroja częściowa.** Dark Sun składa pancerz z tułowia, ramion i nóg. Propozycja: tułów → pancerz IWD2 z KP zbroi, ramiona → karwasze, nogi → buty, każdy z KP z `base_ac`. Alternatywa: części ramion i nóg wtapiane w pancerz (pełny komplet = suma KP), bez osobnych przedmiotów.
2. **Materiał** (`material` 0–5, 128). Dark Sun różnicuje broń z kości, obsydianu, drewna i metalu. Wartości z danych: miecze mają 1, 3, 4. Propozycja: metal = +1 do obrażeń (Athas: metal jest rzadki), kość i drewno = −1. Znaczenie kodów wymaga potwierdzenia (porównanie z grą).
3. **`legal_class`** (maska klas). Kolejność bitów nieznana; do potwierdzenia generator bierze maskę użytkowników z szablonu IWD2.
4. **Broń Athasu bez odpowiednika** (gythka, chatkcha, cahulaki, wyvern hook): proponowany typ w planie; własne animacje broni poza zakresem.
5. **Obiekty świata (R0)** nie są przedmiotami. Trafiają do ARE jako drzwi, pojemniki albo punkty informacji (tekst oględzin z `dialogs.csv`).
