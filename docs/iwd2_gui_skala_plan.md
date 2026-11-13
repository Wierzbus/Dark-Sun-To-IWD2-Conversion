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

## Punkt wyjscia
W repo BGtoIWD2_mod (galaz aktualizacja-reguly-cre-gui) jest wczesniejszy generator GUI z parametrem rozdzielczosci:
`tools/hires_patch.py --width W --height H` i pakiet `tools/guiscale/` (bamio, bamscale, mosio, fontgen z TTF,
hudscale = GUIW10 i prefiks Z, screens = pozostale ekrany i prefiks Y/X). To z niego pochodza pliki Y*/Z*.
Plan: przeniesc go tutaj, poprawic (zapis BAM bez kompresji RLE, zielen tylko na indeksie przezroczystym,
suwaki GUISLDR, czcionki z limitem rozmiaru w grze) i podpiac pod instalator.

## Etap 2 – narzędzie `tools/iwd2_gui_skaluj.py --szer W --wys H`
Wejście: pliki gry. Wyjście: folder override + `upscale_exe.tpa`. Te same reguły przezroczystości
co dziś (zieleń tylko na indeksie przezroczystym, rozlanie krawędzi przed filtrem).

## Etap 3 – instalator
WeiDU: komponent pyta o rozdzielczość (albo czyta `icewind2.ini`) i uruchamia Python (`AT_NOW`),
z gotowymi zestawami dla 1920x1080 i 2560x1440 jako zapasem, gdy Pythona nie ma.

## Stan 2026-11-13 (wieczór)
- Paczka 1 dla 1920x1080 przetestowana w grze: GUI, portrety, ikony, czcionki Classica, suwaki, pasy boczne, Continue – OK.
- Generator przeniesiony do `tools/iwd2_gui/` (z BGtoIWD2_mod): `python tools/iwd2_gui/hires_patch.py --iwd2-dir GRA
  --width 1920 --height 1080 --gui-scale 1.4 --font Classica-Bold.ttf --out-dir WYNIK` (czyta tylko BIF, bez Override).
  Wynik: exe identyczny z IWD2_1920x1080.exe (50 B łatek układu) i 390 plików GUI, z czego 363 to te same nazwy co w paczce.
- Brakuje w generatorze (do dołożenia jako kolejne kroki tego samego narzędzia):
  1. łatki test13 z parametru: ekran ładowania (×H/600), ikony (32→48·S/1,8), portrety 64 i ramka 62, kółka kolorów, przycisk akcji;
  2. ekrany ładowania LOAD*/GTR*/GPROGBAR/SKULANIM (`iwd2_ekran_ladowania.py`), ikony (`iwd2_ikony.py`), portrety _S;
  3. poprawki z testów: brakujące Y*/Z* (`iwd2_gui_brakujace.py`), suwaki YGUISLDR, pasy boczne HUD, czcionki z TTF
     (`iwd2_czcionka_ttf.py`, ramka ≤ najniższe pole − 3 px), Continue i waga;
  4. zapis BAM bez kompresji RLE (stara kompresja psuła czcionki).

## Widok świata większy niż monitor (2026-11-13)
- Gra pokazuje tyle świata, ile ma pikseli w swojej rozdzielczości. Zestaw zbudowany dla rozdzielczości większej
  niż monitor (np. 2560x1440 na 1920x1080) pokazuje ok. 33% więcej świata w każdym kierunku; DDrawCompat
  (`DisplayResolution = desktop`, domyślnie) emuluje tryb gry i zmniejsza obraz do pulpitu (`DisplayFilter`, domyślnie bilinear).
- Skala GUI to zawsze H/600 rozdzielczości gry, więc po zmniejszeniu przez DDrawCompat GUI ma na ekranie ten sam rozmiar
  co zestaw dla rozdzielczości monitora. Nie trzeba osobnego parametru – wystarczy zbudować zestaw dla większej rozdzielczości.
- Tryb musi być na liście `SupportedResolutions` w `DDrawCompat-<nazwa exe>.ini` (np. `DDrawCompat-IWD2_2560.ini`).
- Zastrzeżenia: obraz świata lekko zmiękczony, na małych mapach czarne marginesy.

## Stan 2026-11-13 (noc) – `tools/iwd2_gui/buduj.py`
Jedno polecenie buduje komplet paczki 1 dla dowolnego W x H (tylko z BIF, oryginalny exe nietknięty):
`python tools/iwd2_gui/buduj.py --gra GRA --szer W --wys H --ttf Classica-Bold.ttf --out WYNIK`
→ `IWD2_<W>.exe`, `upscale_exe.tpa` (makra WeiDU), `override/gui|ikony|portrety`.
Kroki: generator (exe układu, GUIW10 ×1,4·H/1080, ekrany ×H/600) → łatki exe z `guiscale/exe_skala.py`
(panel, ikony 48·r, przycisk akcji 74·r, kółka kolorów ×5/3·r, portrety P/P−2/P−4 z pola w GUIW10, ekran ładowania ×H/600)
→ `iwd2_napraw_gui.napraw` (okna na całą szerokość) → pas portretów → suwaki Y* → Continue i waga → pasy boczne HUD
→ brakujące Y*/Z* → czcionki Classica (×H/1080, ramka ≤ najniższa etykieta − 3) → ekran ładowania, ikony, portrety.
Zapis BAM w generatorze: bez RLE i bez zlib.
Sprawdzenie 1920x1080 względem przetestowanej paczki: te same nazwy plików (+STONFORM, YGUIHITP), 196 plików GUI
identycznych, pozostałe z tą samą geometrią (różnice palety po kwantyzacji) poza 8 BAM różniącymi się o 1 px;
ikony identyczne; łatki exe o tych samych wartościach (zapis `imul` zamiast `lea`).
- 2026-11-14: paczka 2560x1440 z `buduj.py` (z komponentem 5 – DDrawCompat-IWD2_2560.ini) przetestowana w grze na monitorze
  1920x1080: wszystko działa (widok świata większy, GUI tej samej wielkości).
- Dalej: instalator z wyborem rozdzielczości (Python przez AT_NOW + gotowe zestawy), paczka 2 (rasy) dla dowolnego IWD2_<W>.exe.
