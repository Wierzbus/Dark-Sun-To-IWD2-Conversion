# IWD2.exe – łatki GUI i rozdzielczości (stan 2026-11-14: generator dowolnej rozdzielczości)

Plik bazowy: IWD2.exe GOG 2.01, offset w pliku = adres − 0x400000. Oryginał nie jest zmieniany: instalator paczki 1
(`mod/iwd2_upscale`) tworzy `IWD2_<W>.exe` makrami WeiDU (`upscale_exe.tpa`) generowanymi razem z zestawem grafik
przez `tools/iwd2_gui/buduj.py --szer W --wys H` (w paczce: przenośny `iwd2_gui_buduj.exe`). Plan i historia:
`docs/iwd2_gui_skala_plan.md`. Sprawdzone w grze: 1920x1080 i 2560x1440 (także na monitorze 1920x1080 z widokiem świata).

## Skale (r = H/1080)
| Element | Skala | 1080 | 1440 |
|---|---|---|---|
| ekrany (prefiks Y*) | H/600 | 1,8 | 2,4 |
| pasek gry GUIW10 (prefiks Z*) | 1,4·r | 1,4 | 1,867 |
| pole portretu P (z GUIW10, okno 1, kontrolka 0) | ≈46·Z | 64 | 86 |
| ikony | 48·r | 48 | 64 |
| czcionki Classica Bold (TTF) | wysokość·r, ramka ≤ najniższa etykieta − 3 | NORMAL 18, YNORMAL 22 … | ×4/3 |

## Łatki exe liczone z W×H (`tools/iwd2_gui/guiscale/exe_skala.py` + układ w `hires_patch.py`)
| Miejsce | Zmiana |
|---|---|
| 0x42218E … 0x42227E, 0x4222C3 → 0x5CC201, 0x422174 | układ okien w gałęzi trybu 1024 (`hires_patch.layout`), prawa krawędź środka, W > 1600 |
| 0x85DE3C | panel 800x600 → W x H |
| 0x4E66C1 | rozmiar ikony 32 → 48·r |
| 0x595864 | przycięcie przycisku akcji 38 → 74·r (`imul`) |
| 0x61E628, 0x61EFDB, 0x63241F, 0x632991 / 0x61E63D, 0x61EFF0, 0x632430, 0x6329A2 | kółka kolorów: krok i odstęp ×5/3·r |
| 0x64FB35, 0x6659E5, 0x64FB66, 0x665A16 | portrety ekranów drużyny: P |
| 0x704F06, 0x704F2B | nakładka HP: P |
| 0x704EBE (+0x704ED0 nop) | ramka zaznaczenia portretu: P − 2 (bok P wychodził poza pole z prawej i z dołu) |
| 0x705053 | obraz portretu: P − 4 (od +2) |
| 0x440400 (663 B) | kod ekranu ładowania: pozycje × H/600 (`imul`/`idiv`), tło od (0,0) na cały ekran (kod generowany w Pythonie) |
| 0x441512, 0x441537, 0x441548 | ekran ładowania 800·S × 600·S; 0x4414C7 / 0x4414EF jak test13 |
| 0x4416F5 | wywołanie rysowania tła → etykieta `tlo` kodu ekranu ładowania |
Ramki STON10L/R/T/B (0x4228B4..0x4229C7) zostają – działają też jako globalne przycięcie (test7 przyciął całe menu).

## Grafiki (kolejność w `buduj.py`)
generator ekranów i paska → `iwd2_napraw_gui` (okna wyśrodkowane rozciągnięte na W, tła pól tekstowych, zielone
obwódki) → pas portretów ekranów postaci (YGACTN10 z fragmentu ZGACTN11) → suwaki YGUISLDR (MOS/BAM ×S, pola suwaka ×S)
→ Continue w dialogu (GUIW10 okno 9: y 0) i waga w ekwipunku (GUIINV okno 2, etykieta 66: −3·r) → pasy po bokach paska
gry (skrajny panel rozciągnięty na czarne pasy; w trybie dialogu wyższe) → brakujące Y*/Z* (`iwd2_gui_brakujace`) →
czcionki Classica z TTF (`iwd2_czcionka_ttf`, jasna rampa palety – tekst nigdy czarny), YSTATES2 = oryginał STATES2 →
ekran ładowania (`iwd2_ekran_ladowania`) → ikony (`iwd2_ikony`, w tym COLGRAD, GUIBTBUT, STORTIN*) → portrety
(`iwd2_portrety`: _S = P−4, _L = 210·S × 330·S).

## Widok świata większy niż monitor
Gra pokazuje tyle świata, ile ma pikseli. Zestaw dla rozdzielczości większej niż monitor + `DDrawCompat-IWD2_<W>.ini`
(`DisplayResolution = desktop`, `DisplayFilter = bilinear(0)`, tryb W×H w `SupportedResolutions`) → DDrawCompat
zmniejsza obraz do pulpitu; GUI ma na ekranie ten sam rozmiar, świata widać więcej (2560x1440 na 1920x1080: ok. 1/3).
Komponent 20 paczki 1.

## Podgląd postaci (ekwipunek, kreator) – ODŁOŻONE NA KONIEC
- Render: 0x61DAC0 (kreator, GUICG okno 13 kontrolka 1) i 0x62E7D0 (ekwipunek, GUIINV kontrolka 50). Animacja rysowana
  od razu na ekran przez okno przycięcia 128·m × 160·m od środka kontrolki (m = 1, w trybie podwójnym 2: 0x61DD46,
  0x61DD5D, 0x62EAF9, 0x62EB10), wywołanie `[edx+0x90]` (0x61DF8F, 0x62ED48).
- Ścieżka ×2 silnika **odrzucona** (test 2026-11-14 na 2560): wspólna flaga podwajania (0x77F520 nagłówek, 0x77F5F0
  piksele) psuje też inne grafiki BAM (pola barw), a podwojone piksele są czytane ze starym opisem klatki → paski.
- Kandydat: własne skalowanie z wygładzaniem po narysowaniu (tło przed/po, różnica = postać, nałożenie w skali H/600).

## Znane pułapki
- MOS: czysta zieleń tylko na indeksie 0 palety kafla (inaczej zielone pasy). BAM: zieleń tylko na indeksie przezroczystym.
- Krawędzie przy skalowaniu: kolor krawędzi rozlany na tło przed filtrem, maska skalowana osobno i progowana.
- BAM w generatorze bez RLE i bez zlib (stara kompresja psuła czcionki).
- Brak pliku czcionki z CHU = asercja ChVidFont.cpp:379; za duża ramka czcionki względem etykiety → tekst się nie mieści.
- Narzędzie ikon łapie też elementy GUI 24–40 px (GUIBTBUT, STORTIN*) – skalowane jak pole, nie jak ikona.
- PyInstaller w Anacondzie: wykluczyć Qt (PyQt/PySide) – `zbuduj_program.bat` to robi.
