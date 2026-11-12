# iwd2_nowe_lokacje

Nowe lokacje Icewind Dale 2 z obrazów własnych. Mod WeiDU wydzielony z BGtoIWD2_mod, gdzie lokacje były komponentami 6 i 7 (gałąź `aktualizacja-reguly-cre-gui`, commit a64fa24).

## Komponenty
| Nr | Lokacja | Opis |
|----|---------|------|
| 1 | AR9020 | pustynny kanion: TIS, WED ze ścianami z SR, ARE (1 wejście START), MOS, SR/HT/LM |
| 2 | AR9021 | labirynt w rzucie ukośnym: plan obrócony o 45°, skrócenie 0,75, czerń poza murami jak we wnętrzach BG1 |

Lokacje nie mają wyjść ani wejść z innych obszarów. Do testu: skok konsolą.

## Budowa
```
python -m geometry.image_area --dir areas_custom/AR9020 --name AR9020
python -m geometry.image_area --dir areas_custom/AR9021 --name AR9021
```
Wyniki trafiają do `mod/iwd2_nowe_lokacje/build/` (poza Gitem). `tools\cykl.cmd` buduje obie lokacje i kopiuje mod do katalogu IWD2. WeiDU uruchamia właściciel.

Test: `python -m unittest tests.test_image_area`

Zależności: numpy, opencv-python, Pillow, scipy (tylko narzędzia `tools/rotuj_plan*.py`).

## Źródła lokacji (`areas_custom/ARxxxx/`)
- `obraz.png`: obraz lokacji
- `SR.BMP`, `HT.BMP`, `LM.BMP`: mapy wyszukiwania, wysokości i światła (autorskie)
- `sciany.png` (opcjonalnie): maska murów, rozmiar zaokrąglony w górę do wielokrotności 64

`tools/rotuj_plan.py` i `tools/mapy_z_rotacji.py` tworzą rzut ukośny z planu (AR9021). `mapy_z_rotacji.py` potrzebuje `inventory/resource_reader.py` i instalacji BG1.

## Konwencje i pomiary
- Ściany WED: wielokąt = sylwetka muru (niepotwierdzone na silniku), maks. 44 wierzchołki na wielokąt.
- Ukośne ściany w BG1: nachylenie ok. 0,7 (szczyt 34–38° od poziomu); komórka SR 16×12, czyli skrócenie 0,75.
- Wnętrza typu dungeon w BG1 (AR2615, AR0516, AR2610): poza układem pomieszczeń czerń, mur jako cienki pas.

## Stan
Nic nie było jeszcze testowane w grze ani w WeiDU.
