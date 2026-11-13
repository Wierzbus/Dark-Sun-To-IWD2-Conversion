# GUI IWD2 ze skalą z parametru – plan

Cel: jeden instalator, który dla podanej rozdzielczości (szer. × wys.) buduje komplet GUI i łatki exe.
Skala S = wys. / 600 (1080 → 1,8). Zmiana rozdzielczości = ponowna instalacja (nie w trakcie gry).

## Etap 0 – dokończenie 1920x1080 (stała skala 1,8)
- ramka zaznaczenia portretu (62 zamiast 64) – czeka na test po przeinstalowaniu komponentu 1,
- podgląd postaci – łatka ×2 wycofana; nowa metoda do opracowania,
- czcionki – test czystej YNORMAL ×1,8; przy wysypce adres z Podglądu zdarzeń.

## Etap 1 – spis tego, co zależy od skali
| Element | Dziś | Do zrobienia |
|---|---|---|
| CHU (okna, kontrolki) | gotowe pliki 1920 z wcześniejszej pracy (Y*/Z*) | generator z oryginałów: S × współrzędne, okna 4:3 wyśrodkowane, pasy boczne do pełnej szerokości |
| MOS (tła okien, ekrany ładowania) | `iwd2_poszerz_tla.py`, `iwd2_ekran_ladowania.py` (×1,8) | parametr S i szerokość ekranu |
| BAM przycisków (Y* ×S, Z* ×S·0,78) | `iwd2_gui_brakujace.py` | parametr S |
| czcionki | ręcznie, część wysypuje grę | metoda zachowująca paletę + rozpoznanie limitu w exe |
| portrety _L/_S | `iwd2_portrety.py` | rozmiar pola z S |
| ikony | `iwd2_ikony.py` (32 → 48) | 32·S/1,2 |
| exe: panel, ramki, portrety, ikony, kółka kolorów, ekran ładowania | stałe w `tools/iwd2_paczki_exe.py` (z test13) | makra WeiDU liczone z S (READ/WRITE z wyrażeniami) |

## Etap 2 – narzędzie `tools/iwd2_gui_skaluj.py --szer W --wys H`
Wejście: pliki gry. Wyjście: folder override + `upscale_exe.tpa`. Te same reguły przezroczystości
co dziś (zieleń tylko na indeksie przezroczystym, rozlanie krawędzi przed filtrem).

## Etap 3 – instalator
WeiDU: komponent pyta o rozdzielczość (albo czyta `icewind2.ini`) i uruchamia Python (`AT_NOW`),
z gotowymi zestawami dla 1920x1080 i 2560x1440 jako zapasem, gdy Pythona nie ma.
