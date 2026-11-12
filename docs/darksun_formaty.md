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

Kody ras i klas: przybliżone tabele z oznaczeniem pewności w `darksun/codes.py`. Pewne (potwierdzone imionami): rasa 1 człowiek, 3 elf, 7 mul, 8 thri-kreen, 9 nieumarły; klasa 6 druid, 9 wojownik, 10 gladiator, 12 psionik, 15 tropiciel, 18 skalacz, 19 templariusz. Rasy 2, 4, 5, 6 przyjęte wg kolejności z podręcznika (krasnolud, półelf, półolbrzym, niziołek). Płeć 1/2 niepewna („Chief Daughter” ma kod 1).

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

## Opisy przedmiotów
Brak czytelnej tabeli opisów. Jedyny jawny zbiór opisów to SPIN (RESOURCE.GFF, 173 wpisy) – czary. Teksty w GPL/MAS są skompresowane w kodzie bajtowym (np. po sekwencji `4f 00 73 92 05`), więc opisy przedmiotów, jeśli istnieją, trzeba szukać tam.

## Do zrobienia
- Tabele kodów: rasy, klasy, charakter, miejsca, typy broni.
- Znaczenie pól ? (porównanie z grą lub podręcznikiem).
- OJFF (obiekty na mapie) i ETAB (rozmieszczenie w regionach): powiązanie postaci z lokacjami.
- GPL/MAS: kod bajtowy skryptów i dialogów.
