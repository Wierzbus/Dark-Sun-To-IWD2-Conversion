# Dark Sun: Shattered Lands – formaty danych (stan rozpoznania)

Ustalone na plikach gry (wersja z katalogu `dsun1`). Brak zewnętrznej dokumentacji, więc znaczenia pól są wnioskami z danych. Oznaczenia: ✔ potwierdzone na wielu rekordach, ? prawdopodobne, – nieznane.

## Pliki
| Plik | Zawartość (typ: liczba) |
|------|------|
| SEGOBJEX.GFF | RDFF 1046 (postacie, przedmioty), OJFF 2775, SCMD 256, BMP 2419 |
| GPLDATA.GFF | GPL 217 i MAS 33 (skrypty i dialogi), IT1R 1, NAME 1, GPLI 1, GPLX 1, PORT 112, PAL 45, WALL 664 |
| RGN02–RGN2D, RGNFF.GFF | 35 regionów: TILE, RMAP, GMAP, ETAB (rozmieszczenie) |
| RESOURCE.GFF | TEXT 60, MONR, RDAT 45, czcionka, interfejs, ikony |
| CINE.GFF | przerywniki |

## GFF ✔
Opis w `darksun/gff.py`. Czytnik obsługuje wszystkie 42 pliki GFF z instalacji, w tym typy segmentowane (tabela położeń w zasobie GFFI).

## RDFF (SEGOBJEX.GFF) ✔
Ciąg bloków z nagłówkiem 10 B: `load_action u8, blocknum u8, type i16, index i16, from i16, len i16`. `load_action = 0xFF` kończy rekord. Wszystkie 1046 rekordów kończą się poprawnie.

| type | rozmiar | znaczenie | wystąpienia |
|------|---------|-----------|-------------|
| 1 | 21 B | przedmiot | 1350 |
| 2 | 58 B | walka (statystyki bojowe, imię) | 291 |
| 4 | 71 B | postać (PD, klasy, poziomy, rzuty obronne) | 290 |
| 3, 5 | 0 B | znaczniki | 1283 / 1340 |

`load_action` przedmiotu: 1 = samodzielny rekord przedmiotu (755), 2 = ? założony (136), 4 = ? w plecaku (459).

### Walka (58 B)
`hp, psp, char_index, id, ready_item_index, weapon_index, pack_index` (i16), `data_block[8]`, `special_attack u8, special_defense u8, icon i16, ac i8, move, status, allegiance, data u8, thac0 i8, priority u8, flags u8, stats[6]` (SIŁ ZRĘ KON INT MĄD CHA) ✔, `name[18]` ✔.
`char_index` = `index` bloku postaci ✔.

### Postać (71 B)
`current_xp i32, high_xp i32, base_hp, high_hp, base_psp` ✔, `u_14` (zwykle 2000) –, `u_16` –, 6 B –, `race, gender, alignment` ?, `stats[6]` ✔ (identyczne jak w bloku walki), `real_class[3], level[3]` ✔ (multiklasa: do 3 wpisów), `base_ac, base_move, magic_resistance` ?, `num_blows, num_attacks[3], num_dice[3], num_sides[3], num_bonuses[3]` ?, `saving_throw[5]` ?, `allegiance, size, spell_group, high_level[3], sound_fx u16, attack_sound u16, psi_group` ?.

Kody ras, klas, płci i charakteru: `darksun/codes.py` z oznaczeniem pewności. Rasy 1–8 (człowiek, krasnolud, elf, półelf, półolbrzym, niziołek, mul, thri-kreen) wg tabeli karty postaci w EXE i imion; 9 nieumarły, 12 potwór, 14 istota pozaplanarna – kategorie potworów. Klasy ✔ wg tabeli nazw w DSUN.EXE (0x49B3C, 29 wskaźników, indeks real_class + 8): 1–4 kapłan (sfery), 5–8 druid (sfery), 9 wojownik, 10 gladiator, 11 zachowawca, 12 psionik, 13–16 tropiciel, 17 złodziej, 18 mag, 19 kapłan, 20 psionik (18–20 ogólne dla NPC; np. „Defiler” = 18, „Templar” = 19). Charakter 1–9 (LG…CE) zgodny z OpenDS.

### Przedmiot (21 B)
`id i16, quantity u16 ?, next i16, value u16 ?, pack_index i16, item_index i16` (rekord IT1R ✔), `icon i16, charges u16 ?, special u8 ?, slot u8, name_idx u16` (NAME ✔, 9999 = brak), `bonus i8` ? (premia magiczna).

## IT1R (GPLDATA.GFF) – 115 rekordów po 20 B
`weapon_type i8 ?, damage_type i8, u_2 u16 –, weight u16 ? (1/10 funta), base_hp u16 ?, material u8 ?, placement u8 ✔, range u8 ?, num_attacks u8 ?, sides u8 ✔, dice u8 ✔, mod i8, flags u8, legal_class u16 ? (maska klas), base_ac i8 ✔, u_19 u8`.
Miejsca (`placement`): 1 tułów, 3 ramiona, 0x0a nogi, 5 dłoń, 0x0b amunicja, 0x0c broń dystansowa; pozostałe do ustalenia.

## NAME (GPLDATA.GFF) – 322 rekordy po 25 B
Nazwa 22 B zakończona zerem (dalej śmieci z bufora), `u16` ? ikona, `u8` –.

## OJFF (SEGOBJEX.GFF) – 2775 rekordów po 16 B
8 × i16. Pole 6 = id grafiki BMP obiektu ✔ (ikona przedmiotu). Pola 3, 4 = ? pozycja. Rekord OJFF o id = |id przedmiotu| istnieje dla 1348 z 1350 przedmiotów.

## BMP (SEGOBJEX 2419, RESOURCE 105) ✔
Opis w `darksun/bmp.py`: wiersze z odcinkami, strumień z bajtami sterującymi (parzysty = dosłownie c/2+1 pikseli, nieparzysty = powtórzenie (c+1)/2). Dekodują się wszystkie 2524 grafiki. Paleta ikon: RESOURCE.GFF PAL 1000 (sprawdzone wizualnie; palety GPLDATA 1–5 dają ten sam wynik dla ikon).

## Teksty w skryptach GPL/MAS ✔
Opis w `darksun/gpltext.py`: znacznik `92 05`, znaki 7-bitowe od najstarszego bitu, kod 3 kończy napis. Przed napisem `4f 00 xx` – bufor: 0x73 wypowiedzi NPC (5883), 0x62 narracja (999); bez bufora i z wcięciem – opcje wyboru gracza (2975). Długie teksty są dzielone na kawałki tego samego bufora stojące bezpośrednio po sobie: 14 050 kawałków → 10 245 tekstów.

## Opisy czarów: SPIN (RESOURCE.GFF) ✔
180 wpisów, zwykły tekst („NAZWA: opis”).

## Kod bajtowy GPL ✔ (`darksun/gpl.py`)
Port deasemblera z OpenDS (MIT; zob. niżej). Wszystkie 250 skryptów (217 GPL + 33 MAS) dekodują się do końca. Instrukcja: opcode (0x00–0x80), parametry jako wyrażenia (`gpl_read_number`): bajt < 0x80 → liczba 14-bitowa; 0x8x/0xCx → zmienne (LSTR, LNUM, GNAME, flagi…), 0x8B liczba 32-bit, 0x8C wywołanie funkcji, 0x8F bajt, 0x91 nazwa obiektu (−id), 0x92 napis, 0xD1–0xDF operatory, 0xE2/0xE1 nawiasy.
`4f 00 73 92 05 …` = `print string(0x73, "…")`; 0x73 wypowiedź, 0x62 narracja.

### Wyzwalacze i powiązanie tekstów z obiektami ✔ (`darksun/dialogs.py`)
Rozmowa (0x6E), oględziny (0x66), użycie (0x6D), podniesienie (0x6C), atak (0x65), brak rozkazów (0x6F): parametry (adres, numer skryptu GPL, obiekt). „Użycie z” (0x70): (obiekt1, obiekt2, adres, skrypt). Obiekt = −id rekordu RDFF/OJFF. Od adresu obsługi zbierane są teksty osiągalne w skrypcie (skoki, if/else, while, menu, local sub; bez global sub).
Wynik: 1125 unikalnych wyzwalaczy; 167 z 291 postaci ma dialog; 136 obiektów-przedmiotów ma tekst oględzin lub użycia.
Ograniczenia: teksty gałęzi są układane wg offsetu (bez warunków); teksty z wywołań global sub i ze zmiennych LSTR nie są dołączane.

## Opisy przedmiotów
Brak osobnej tabeli opisów. Opisy to teksty wyzwalaczy oględzin i użycia (`items.csv`: `opis_ogledziny`, `opis_uzycie`) – dotyczą głównie przedmiotów fabularnych i obiektów świata; zwykła broń i pancerze opisów nie mają.

## Tabele kart postaci w DSUN.EXE ✔
Jawne napisy: MALE, FEMALE; HUMAN, DWARF, ELF, HALF-ELF, HALF-GIANT, HALFLING, MUL, THRI-KREEN; CLERIC, DRUID, FIGHTER, GLADIATOR, PRESERVER, PSIONICIST, RANGER, THIEF; LAWFUL GOOD … CHAOTIC EVIL. Potwierdzają kody ras 1–8, płci 1–2 i charakteru 1–9 (0 = brak). Kody klas wewnętrznych są szersze niż 8 klas gracza (do 19); 9–12 zgodne z kolejnością Fighter, Gladiator, Preserver, Psionicist.

## Regiony RGNxx.GFF ✔ (`darksun/region.py`)
TILE 1–254 (kafel 16×16 w formacie BMP), RMAP i GMAP po 128 × 98 B (numer kafla; znaczniki: 0x80 mur, 0x40 pole nieprzechodnie), ETAB rekordy 8 B (`u16 x, u16 y` lewego górnego rogu sprite'a, `u8 z`, `u8 flagi`, `i16 −id` OJFF/RDFF). Paleta regionu: GPLDATA PAL o id = numer regionu. Pierwszy obszar gry (cele niewolników w Draj) = RGN29; opis i konwersja: `docs/ds_obszar_rgn29.md`.

## Źródła zewnętrzne
- OpenDS (MIT, Brandon LaRocque): https://github.com/VirInvictus/opends – deasembler GPL (port w `darksun/gpl.py`), tabele klas, charakteru, wyzwalaczy. Ich katalog opcodów i dekoder napisów pochodzą z dsoageofheroes/libgff i soloscuro-archive (MIT).

## Do zrobienia
- Tabele kodów: rasy, klasy, charakter, miejsca, typy broni.
- Znaczenie pól ? (porównanie z grą lub podręcznikiem).
- OJFF (obiekty na mapie) i ETAB (rozmieszczenie w regionach): powiązanie postaci z lokacjami.
- Dialogi: warunki gałęzi, teksty z global sub i zmiennych LSTR; drzewo dialogu zamiast listy.
