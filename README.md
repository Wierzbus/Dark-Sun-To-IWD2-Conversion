# Dark Sun To IWD2 Conversion

Przeniesienie Dark Sun: Shattered Lands do Icewind Dale 2 oraz nowe lokacje IWD2 z obrazów własnych.

## Dark Sun: wydobycie danych (`darksun/`)
```
python -m darksun.extract --game "D:\Gry\Dark Sun\dsun1" --out build/darksun
```
Wynik: `names.csv`, `item_types.csv` (IT1R), `items.csv` (wszystkie przedmioty z RDFF z właścicielem, danymi typu IT1R w kolumnach `it_` i ikoną), `creatures.csv` (walka + postać, z przybliżoną rasą i klasami), `texts.csv` (teksty skryptów: wypowiedzi, narracja, opcje gracza), `spells.csv` (opisy czarów), `dialogs.csv` (teksty przypisane do postaci i przedmiotów przez wyzwalacze GPL), `darksun_data.json` i `icons/` (PNG). Wyniki zawierają teksty gry, więc zostają poza Gitem (`build/`).

Deasembler GPL (`darksun/gpl.py`) to port z [OpenDS](https://github.com/VirInvictus/opends) (MIT).

Formaty i stan rozpoznania pól: [docs/darksun_formaty.md](docs/darksun_formaty.md). Test: `python -m unittest tests.test_darksun` (dane syntetyczne, bez plików gry).

## IWD2: pliki ras, podras, klas i kitów (`tools/wyciagnij_rasy.py`)
Wyciąga z instalacji IWD2 (override, potem BIF wg chitin.key) tabele ras i podras, klas i kitów (KITLIST, CLAB*, listy czarów i zdolności), LISTINNT i ekrany kreatora postaci (GUICG*.CHU) do jednego zipa ze spisem źródeł. Tylko czyta instalację.
```
python tools\wyciagnij_rasy.py --game-dir "D:\Gry\Icewind Dale 2" --out iwd2_rasy.zip --tlk
```
`--tlk` dołącza dialog.tlk (nazwy i opisy ras). Wynik zawiera pliki gry, więc nie trafia do Gita.

## Paczki testowe (instalatory WeiDU)
Trzy niezależne paczki, każda z własnym setup-*.exe (kopia WeiDU), rozpakowywane do katalogu IWD2:
1. **iwd2_upscale** (`mod/iwd2_upscale`) – dowolna rozdzielczość. Komponenty 1–4 (wybór 1920x1080 / 2560x1440 /
   3840x2160 / inna) uruchamiają przenośny program `iwd2_upscale/generator/iwd2_gui_buduj/iwd2_gui_buduj.exe`
   (z `tools/iwd2_gui/buduj.py`, budowany raz skryptem `tools/iwd2_gui/zbuduj_program.bat`), który z plików gry buduje
   zestaw w `iwd2_upscale/zestaw`; instalator tworzy `IWD2_<W>.exe`. Komponenty 10–12: GUI, portrety, ikony;
   20: widok świata (tryb gry większy niż monitor przez DDrawCompat). Plan i stan: [docs/iwd2_gui_skala_plan.md](docs/iwd2_gui_skala_plan.md), łatki exe i grafiki: [docs/iwd2_exe_gui.md](docs/iwd2_exe_gui.md).
2. **darksun_rasy** (`mod/darksun_rasy`) – komponent 0 tworzy `IWD2_DS.exe` i `IWD2_<W>_DS.exe` z każdego
   `IWD2_<W>.exe` paczki 1 (łatki ras i klas; exe większe o 8 KB – nowa sekcja PE `.dsras`). Komponenty:
   1 mul, 2 podklasy + zdolności klas z 2DA (DSKLASY, DSSNEAK, DSWROG), 3 półelf atasyjski,
   4 zdolności ras z tabel (DSRASY, DSRWROG, tablice RLAB ras w formacie CLAB),
   5 progresja klas i podklas (DSKLPROG: kość PW, premia do ataku, rzuty obronne, domeny i listy czarów podklas DS).
3. **iwd2_nowe_lokacje** – AR9020, AR9021, AR9022 (Dark Sun) i skok w dialogu Hedrona; lokacje zbudowane przed spakowaniem.

Makra exe (`*_exe.tpa`) zawierają fragmenty kodu gry do kontroli oryginału, więc są generowane, nie commitowane.
Paczka 2 (stan test24):
```
python tools/iwd2_podklasy_exe.py --base IWD2_1920x1080_test13.exe --out IWD2_1920x1080_test24.exe
python tools/iwd2_paczki_exe.py --orig IWD2.exe --upscale IWD2_1920x1080_test13.exe --rasy IWD2_1920x1080_test24.exe --out-upscale upscale_exe.tpa --out-rasy mod/darksun_rasy/darksun_rasy/exe/rasy_exe.tpa
```
Paczka 1: makra powstają w instalatorze (program budujący zestaw).

## Rasy, podrasy, podklasy i zdolności Dark Sun w IWD2 (mod WeiDU `darksun_rasy`, eksperymentalny)
- **Jak dodać rasę / podrasę / podklasę i co wpisać do której tabeli:** [docs/dodawanie_ras_i_klas.md](docs/dodawanie_ras_i_klas.md).
- Mapa miejsc w exe i opis łatek (test14–test24): [docs/iwd2_exe_rasy_klasy.md](docs/iwd2_exe_rasy_klasy.md).
- Kod łatek: `mod/darksun_rasy/darksun_rasy/asm/` (`podklasy.asm` – koniec .text, `dodatki.asm` – martwy kod pięści
  mnicha, `rasy.asm` – sekcja `.dsras`, `halforc.asm`, `halfelf.asm`).
Instalacja: `mod/darksun_rasy/darksun_rasy` i `setup-darksun_rasy.tp2` do katalogu IWD2, obok `setup-darksun_rasy.exe`
(kopia WeiDU). Oryginalne exe nie są zmieniane; grę uruchamia się przez `*_DS.exe`.

## Nowe lokacje z obrazów (mod WeiDU `iwd2_nowe_lokacje`)

Wydzielone z BGtoIWD2_mod, gdzie były komponentami 6 i 7 (gałąź `aktualizacja-reguly-cre-gui`, commit a64fa24).

### Komponenty
| Nr | Lokacja | Opis |
|----|---------|------|
| 1 | AR9020 | pustynny kanion: TIS, WED ze ścianami z SR, ARE (1 wejście START), MOS, SR/HT/LM |
| 2 | AR9021 | labirynt w rzucie ukośnym: plan obrócony o 45°, skrócenie 0,75, czerń poza murami jak we wnętrzach BG1 |

Lokacje nie mają wyjść ani wejść z innych obszarów. Do testu: skok konsolą.

### Budowa
```
python -m geometry.image_area --dir areas_custom/AR9020 --name AR9020
python -m geometry.image_area --dir areas_custom/AR9021 --name AR9021
```
Wyniki trafiają do `mod/iwd2_nowe_lokacje/build/` (poza Gitem). `tools\cykl.cmd` buduje obie lokacje i kopiuje mod do katalogu IWD2. WeiDU uruchamia właściciel.

Test: `python -m unittest tests.test_image_area`

Zależności: numpy, opencv-python, Pillow, scipy (tylko narzędzia `tools/rotuj_plan*.py`).

### Źródła lokacji (`areas_custom/ARxxxx/`)
- `obraz.png`: obraz lokacji
- `SR.BMP`, `HT.BMP`, `LM.BMP`: mapy wyszukiwania, wysokości i światła (autorskie)
- `sciany.png` (opcjonalnie): maska murów, rozmiar zaokrąglony w górę do wielokrotności 64

`tools/rotuj_plan.py` i `tools/mapy_z_rotacji.py` tworzą rzut ukośny z planu (AR9021). `mapy_z_rotacji.py` potrzebuje `inventory/resource_reader.py` i instalacji BG1.

### Konwencje i pomiary
- Ściany WED: wielokąt = sylwetka muru (niepotwierdzone na silniku), maks. 44 wierzchołki na wielokąt.
- Ukośne ściany w BG1: nachylenie ok. 0,7 (szczyt 34–38° od poziomu); komórka SR 16×12, czyli skrócenie 0,75.
- Wnętrza typu dungeon w BG1 (AR2615, AR0516, AR2610): poza układem pomieszczeń czerń, mur jako cienki pas.

### Stan
Nic nie było jeszcze testowane w grze ani w WeiDU.
