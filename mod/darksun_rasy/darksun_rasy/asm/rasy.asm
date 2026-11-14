; Zdolnosci ras z tabel (test20) i progresja klas z DSKLPROG.2DA (test21): tablice RLAB ras (jak CLAB klas) i cechy z DSRASY.2DA / DSRWROG.2DA.
; Kod w nowej sekcji PE .dsras (adres 0xA21000, 4 KB, tworzy ja tools/iwd2_podklasy_exe.py i instalator).
; Etykiety z podklasy.asm (clab, komorka, tabela2da) podaje nasm -D.
;
; DSRASY.2DA: wiersze = nazwy wierszy ras z GetRaceRow (HUMAN, HUMAN_AASIMAR, ..., HALF_ORC_MUL, HALF_ELF_DS), kolumny:
;   RLAB        nazwa tablicy zdolnosci rasy (format CLAB: ABILITYn, kolumny 1..30 = poziom postaci), * = brak
;   DARKVISION  1 = widzenie w ciemnosci (flaga 0x20000)
;   GIANT_AC    o ile olbrzymy (RACE 153) i ogry (113) trafiaja gorzej te rase (oryginal: krasnoludy i gnomy 4)
;   THROWN      premia do trafienia bronia miotana / proca (oryginal: niziolki 1)
;   SR_LEVEL    przyrost odpornosci na magie na poziom postaci (oryginal: drow i gnom glebinowy 1)
; DSRWROG.2DA: wiersze jak wyzej, kolumny BONUS (premia do trafienia), ABERRATION (premia przeciw aberracjom),
;   E1..E6 (wrogowie rasy - numery z RACE.IDS, 0 = brak).
; Brak tabeli, wiersza albo kolumny = zachowanie oryginalne gry.
bits 32
org 0xA21000

POST      equ 0xA21F00          ; postac, dla ktorej procedura CLAB czyta tablice rasy (klasa 12)
KPTR_RASY equ 0xA21F04          ; C2DArray DSRASY
KPTR_RWRG equ 0xA21F08          ; C2DArray DSRWROG
BUF       equ 0xA21F0C          ; 8 B nazwa tablicy (RLAB / progresja klas)
KPTR_PROG equ 0xA21F14          ; C2DArray DSKLPROG
PCACHE    equ 0xA21B00          ; 3 x 11 dword: tablica progresji (kolumna, klasa); 0 = nie liczone, 1 = oryginal
CACHE     equ 0xA21C00          ; 64 wpisy po 12 B: nazwa (8), C2DArray (4) - tablice wczytane po nazwie
N_CACHE   equ 64
KLASA_RASY equ 12

;================================================================ pomocnicze
; szukaj(tabela, napis, rodzaj) -> eax = indeks wiersza (rodzaj 0) albo kolumny (1), -1 gdy brak. stdcall
szukaj:
    push ebx
    push esi
    push edi
    push ecx
    push edx
    mov esi, [esp+0x18]
    test esi, esi
    jz .nie
    cmp dword [esp+0x20], 0
    jne .kol
    mov ebx, [esi+0x14]
    movsx edi, word [esi+0x22]
    jmp .s
.kol:
    mov ebx, [esi+0x10]
    movsx edi, word [esi+0x20]
.s: xor esi, esi
.p: cmp esi, edi
    jge .nie
    push dword [esp+0x1c]
    push dword [ebx+esi*4]
    call 0x7e7a54               ; stricmp (cdecl)
    add esp, 8
    test eax, eax
    jz .jest
    inc esi
    jmp .p
.jest:
    mov eax, esi
    jmp .k
.nie:
    or eax, -1
.k: pop edx
    pop ecx
    pop edi
    pop esi
    pop ebx
    ret 12

; tab_rasy / tab_rwrog -> eax = C2DArray albo 0
tab_rasy:
    push esi
    push edi
    mov esi, KPTR_RASY
    mov edi, n_rasy
    jmp tab_wspolne
tab_rwrog:
    push esi
    push edi
    mov esi, KPTR_RWRG
    mov edi, n_rwrog
tab_wspolne:
    call tabela2da
    test eax, eax
    jz .k
    cmp word [eax+0x22], 0      ; pusta (brak pliku) -> 0
    jg .k
    xor eax, eax
.k: pop edi
    pop esi
    ret

; rasa_wiersz(tabela, rasa_podrasa) -> eax = wiersz tabeli dla rasy (bajt 0 rasa 1..7, bajt 1 podrasa) albo -1. stdcall
rasa_wiersz:
    push ecx
    push edx
    mov eax, [esp+0x10]
    movzx ecx, al
    dec ecx
    cmp ecx, 6
    ja .nie
    cmp dword [esp+0xc], 0
    je .nie
    sub esp, 4                  ; CString wyniku
    movzx edx, ah
    push edx
    movzx eax, al
    push eax
    lea eax, [esp+8]
    push eax
    mov ecx, [0x8cf6dc]
    mov ecx, [ecx+0x1c54]
    call 0x541940               ; GetRaceRow(&wynik, rasa, podrasa)
    push 0
    push dword [esp+4]          ; char* nazwy
    push dword [esp+0x18]       ; tabela
    call szukaj
    push eax
    lea ecx, [esp+4]
    call 0x7fcc1a               ; ~CString
    pop eax
    add esp, 4
    jmp .k
.nie:
    or eax, -1
.k: pop edx
    pop ecx
    ret 8

; wartosc(tabela, wiersz, nazwa kolumny) -> eax = liczba albo -1 (brak kolumny / komorki). stdcall
wartosc:
    push ecx
    push edx
    push 1
    push dword [esp+0x18]
    push dword [esp+0x14]
    call szukaj
    cmp eax, -1
    je .k
    push eax
    push dword [esp+0x14]
    mov eax, [esp+0x14]
    call komorka                ; eax = tabela, (wiersz, kolumna) -> char*
    test eax, eax
    jz .brak
    push eax
    call 0x7e7b03               ; atoi (cdecl)
    add esp, 4
    jmp .k
.brak:
    or eax, -1
.k: pop edx
    pop ecx
    ret 12

; cecha(rasa_podrasa, nazwa kolumny) -> eax = wartosc z DSRASY albo -1. stdcall
cecha:
    push ecx
    push edx
    call tab_rasy
    test eax, eax
    jz .nie
    push eax
    push dword [esp+0x10]
    push eax
    call rasa_wiersz
    pop ecx                     ; tabela
    cmp eax, -1
    je .k
    push dword [esp+0x10]
    push eax
    push ecx
    call wartosc
    jmp .k
.nie:
    or eax, -1
.k: pop edx
    pop ecx
    ret 8

;================================================================ tablica zdolnosci rasy (GetClabTable 0x546030, klasa 12)
clab_rasa:
    cmp dword [esp+4], KLASA_RASY
    jne clab
    push ebx
    push esi
    push edi
    xor ebx, ebx                ; wynik
    mov esi, [POST]
    test esi, esi
    jz .k
    call tab_rasy
    test eax, eax
    jz .k
    mov edi, eax
    push 1
    push n_rlab
    push edi
    call szukaj
    cmp eax, -1
    je .k
    push eax                    ; kolumna
    movzx eax, word [esi+0x26]
    push eax
    push edi
    call rasa_wiersz
    pop ecx
    cmp eax, -1
    je .k
    push ecx
    push eax
    mov eax, edi
    call komorka
    test eax, eax
    jz .k
    cmp byte [eax], '*'
    je .k
    cmp byte [eax], 0
    je .k
    push eax
    call wczytaj
    mov ebx, eax
.k: mov eax, ebx
    pop edi
    pop esi
    pop ebx
    ret 8

; wczytaj(char* nazwa) -> eax = C2DArray (wczytana raz, pamiec podreczna 64 tablic) albo 0. stdcall
wczytaj:
    push ecx
    push edx
    push esi
    push edi
    mov eax, [esp+0x14]
    mov dword [BUF], 0
    mov dword [BUF+4], 0
    xor ecx, ecx
.c: mov dl, [eax+ecx]
    test dl, dl
    jz .cache
    cmp dl, 'a'
    jb .z
    cmp dl, 'z'
    ja .z
    sub dl, 0x20
.z: mov [BUF+ecx], dl
    inc ecx
    cmp ecx, 8
    jb .c
.cache:
    mov esi, CACHE
    mov ecx, N_CACHE
.p: mov eax, [esi]
    test eax, eax
    jz .nowy
    cmp eax, [BUF]
    jne .n
    mov eax, [esi+4]
    cmp eax, [BUF+4]
    jne .n
    mov eax, [esi+8]
    jmp .k
.n: add esi, 12
    loop .p
    xor eax, eax                ; pamiec podreczna pelna
    jmp .k
.nowy:
    mov eax, [BUF]
    mov [esi], eax
    mov eax, [BUF+4]
    mov [esi+4], eax
    lea edi, [esi]              ; nazwa (CResRef)
    lea esi, [esi+8]            ; slot
    call tabela2da
.k: pop edi
    pop esi
    pop edx
    pop ecx
    ret 4

; poziom w procedurze CLAB (0x722DE3: call 0x447990(klasa), ecx = statystyki): dla klasy 12 poziom postaci (+0x46)
poziom:
    cmp dword [esp+4], KLASA_RASY
    jne 0x447990
    movzx eax, byte [ecx+0x46]
    ret 4

;================================================================ awans 0x71E996 (edi = postac, ebx = stare statystyki)
; po 11 wywolaniach procedury CLAB klas: tablica rasy (klasa 12) i przyrost odpornosci na magie z SR_LEVEL
rasa_awans:
    movzx eax, byte [edi+0x966]
    movzx edx, byte [ebx+0x46]
    sub eax, edx                ; zdobyte poziomy postaci
    jle .sr
    push eax
    mov [POST], edi
    push dword [esp+0x1c]       ; 2. argument funkcji awansu (jak przy klasach)
    push eax
    push KLASA_RASY
    mov ecx, edi
    call 0x722d50
    mov dword [POST], 0
    pop eax
.sr:
    push eax
    push n_sr
    movzx ecx, word [edi+0x26]
    push ecx
    call cecha
    pop ecx                     ; zdobyte poziomy
    cmp eax, -1
    je .oryg
    test ecx, ecx
    jle 0x71e9e2
    imul eax, ecx
    add [edi+0x5f5], al
    jmp 0x71e9e2
.oryg:
    xor eax, eax
    mov al, [edi+0x966]
    jmp 0x71e99e

;================================================================ widzenie w ciemnosci 0x722862 (ebp = postac, [esp+0x56] rasa, [esp+0x57] podrasa)
wzrok:
    push n_dv
    movzx eax, word [esp+0x5a]
    push eax
    call cecha
    cmp eax, -1
    je .oryg
    test eax, eax
    jz .gnom
    or dword [ebp+0x5bc], 0x20000
.gnom:
    cmp word [esp+0x56], 0x0106 ; gnom glebinowy: pozostale cechy jak w oryginale
    jne 0x7229f5
    or dword [ebp+0x5bc], 0x200000
    mov eax, [0x84ebbc]
    add eax, 4
    mov [ebp+0x5e2], ax
    jmp 0x7229f5
.oryg:
    mov edx, [esp+0x56]
    and edx, 0xff
    jmp 0x72286c

;================================================================ bron miotana: 0x73BC10 (atak) i 0x73CA66 (wyswietlanie)
; zamiast "niziolek": THROWN z DSRASY; premie czytaja instrukcje 0x73BC4D / 0x73CA99 z miot_wart (zamiast 0x84EAA8)
miot_atak:
    mov dword [esp+0x14], 0
    push n_miot
    movzx eax, word [esi+0x26]
    push eax
    call cecha
    cmp eax, -1
    jne .t
    cmp byte [esi+0x26], 5
    jne 0x73bc56
    mov eax, [0x84eaa8]
.t: test eax, eax
    jle 0x73bc56
    mov [miot_wart], eax
    jmp 0x73bc1e

miot_info:
    xor edi, edi
    push n_miot
    movzx eax, word [esi+0x26]
    push eax
    call cecha
    cmp eax, -1
    jne .t
    cmp byte [esi+0x26], 5
    jne 0x73ca9f
    mov eax, [0x84eaa8]
.t: test eax, eax
    jle 0x73ca9f
    mov [miot_wart], eax
    jmp 0x73ca6f

;================================================================ wrogowie rasy 0x73C8C0 (thiscall: ecx = atakujacy, [esp+4] = cel; ax = premia)
wrogowie:
    push ebx
    push esi
    push edi
    push ebp
    mov esi, ecx
    mov edi, [esp+0x14]
    call tab_rwrog
    test eax, eax
    jz .oryg
    mov ebx, eax
    xor ebp, ebp                ; suma
    ; --- premie atakujacego
    movzx eax, word [esi+0x26]
    push eax
    push ebx
    call rasa_wiersz
    cmp eax, -1
    je .olbrzym
    push eax                    ; [esp] = wiersz
    push n_bonus
    push eax
    push ebx
    call wartosc
    cmp eax, -1
    jne .b
    xor eax, eax
.b: push eax                    ; [esp] = premia, [esp+4] = wiersz
    mov byte [n_e+1], '1'
.e: push n_e
    push dword [esp+8]
    push ebx
    call wartosc
    test eax, eax
    jle .en
    movzx ecx, byte [edi+0x26]
    cmp eax, ecx
    jne .en
    add ebp, [esp]
.en:
    inc byte [n_e+1]
    cmp byte [n_e+1], '6'
    jbe .e
    push n_aber
    push dword [esp+8]
    push ebx
    call wartosc
    add esp, 8                  ; zdejmij premie i wiersz
    test eax, eax
    jle .olbrzym
    push eax
    push edi
    call 0x584aa0               ; aberracja? (cdecl)
    add esp, 4
    pop ecx
    cmp al, 1
    jne .olbrzym
    add ebp, ecx
.olbrzym:
    ; --- olbrzym / ogr atakuje rase z GIANT_AC
    mov al, [esi+0x26]
    cmp al, 0x99
    je .g
    cmp al, 0x71
    jne .k
.g: push n_giant
    movzx eax, word [edi+0x26]
    push eax
    call cecha
    cmp eax, -1
    je .gor
    sub ebp, eax
    jmp .k
.gor:                           ; oryginal: krasnolud albo gnom (bez glebinowego)
    mov al, [edi+0x26]
    cmp al, 4
    je .gk
    cmp al, 6
    jne .k
    cmp byte [edi+0x27], 1
    je .k
.gk:
    add ebp, [0x84ea98]
.k: mov eax, ebp
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret 4
.oryg:                          ; bez DSRWROG: oryginalna funkcja (przeniesione instrukcje)
    pop ebp
    pop edi
    pop esi
    pop ebx
    push ebp
    push esi
    push edi
    mov edi, [esp+0x10]
    jmp 0x73c8c7

;================================================================ progresja klas z DSKLPROG.2DA (test21)
; wiersze = klasy (BARBARIAN ... WIZARD), kolumny HP / BAB / SAVE = nazwy tablic (HPWAR, BAATFGT, SAVEWAR ...), * = oryginal.
; prog(kolumna 0 HP / 1 BAB / 2 SAVE, klasa 1..11) -> eax = C2DArray albo 0 (oryginal). stdcall, wynik zapamietany.
prog:
    push ebp
    mov ebp, esp
    push ecx
    push edx
    push ebx
    push esi
    push edi
    mov ecx, [ebp+0xc]
    dec ecx
    cmp ecx, 10
    ja .zero
    mov eax, [ebp+8]
    cmp eax, 2
    ja .zero
    imul ebx, eax, 11
    add ebx, ecx
    mov eax, [PCACHE+ebx*4]
    test eax, eax
    jz .licz
    cmp eax, 1
    je .zero
    jmp .k
.licz:
    mov esi, KPTR_PROG
    mov edi, n_prog
    call tabela2da
    test eax, eax
    jz .brak
    cmp word [eax+0x22], 0
    jle .brak
    mov edi, eax
    push 0
    push dword [nazwy_klas+ecx*4]
    push edi
    call szukaj
    cmp eax, -1
    je .brak
    mov esi, eax                ; wiersz
    mov eax, [ebp+8]
    push 1
    push dword [nazwy_kol+eax*4]
    push edi
    call szukaj
    cmp eax, -1
    je .brak
    push eax
    push esi
    mov eax, edi
    call komorka
    test eax, eax
    jz .brak
    cmp byte [eax], '*'
    je .brak
    cmp byte [eax], 0
    je .brak
    push eax
    call wczytaj
    test eax, eax
    jz .brak
    cmp word [eax+0x22], 0
    jle .brak
    mov [PCACHE+ebx*4], eax
    jmp .k
.brak:
    mov dword [PCACHE+ebx*4], 1
.zero:
    xor eax, eax
.k: pop edi
    pop esi
    pop ebx
    pop edx
    pop ecx
    pop ebp
    ret 8

; ---- PW 0x542CB0 (esi = klasa, edi = obiekt regul): zamiast lea r, [edi+tabela]
hp_tab:
    push ecx
    push esi
    push 0
    call prog
    test eax, eax
    jnz .k
    mov ecx, [dom_hp+esi*4-4]
    lea eax, [edi+ecx]
.k: pop ecx
    ret
hp_ecx:
    push eax
    call hp_tab
    mov ecx, eax
    pop eax
    ret
hp_edx:
    push eax
    call hp_tab
    mov edx, eax
    pop eax
    ret
hp_eax:
    jmp hp_tab

; ---- rzuty obronne 0x542610 (edi = obiekt regul): 11 miejsc "lea ecx, [edi+tabela]" -> call sv_N
sv_1:
    push 1
    jmp sv_wsp
sv_2:
    push 2
    jmp sv_wsp
sv_3:
    push 3
    jmp sv_wsp
sv_4:
    push 4
    jmp sv_wsp
sv_5:
    push 5
    jmp sv_wsp
sv_6:
    push 6
    jmp sv_wsp
sv_7:
    push 7
    jmp sv_wsp
sv_8:
    push 8
    jmp sv_wsp
sv_9:
    push 9
    jmp sv_wsp
sv_10:
    push 10
    jmp sv_wsp
sv_11:
    push 11
    jmp sv_wsp
sv_wsp:                         ; [esp] = klasa, [esp+4] = powrot
    push eax
    push edx
    push dword [esp+8]
    push 2
    call prog
    test eax, eax
    jnz .k
    mov ecx, [esp+8]
    mov ecx, [dom_sv+ecx*4-4]
    lea eax, [edi+ecx]
.k: mov ecx, eax
    pop edx
    pop eax
    add esp, 4
    ret

; ---- premia do ataku 0x546B60 (esi = obiekt regul): blok klasy "push N; call bab_tab; jmp" zamiast odczytu z tabeli
; wejscie eax = poziom klasy; wyjscie eax = char* wartosci BASE_ATTACK (jak w oryginale: domyslna wartosc tabeli poza zakresem)
bab_tab:
    push ebp
    mov ebp, esp
    push ecx
    push edx
    push eax
    push dword [ebp+8]
    push 1
    call prog
    test eax, eax
    jnz .t
    mov ecx, [ebp+8]
    mov ecx, [dom_bab+ecx*4-4]
    lea eax, [esi+ecx]
.t: mov ecx, eax
    pop eax
    dec eax
    push 0
    push eax
    mov eax, ecx
    call komorka
    test eax, eax
    jnz .k
    mov eax, [ecx+0x1c]
.k: pop edx
    pop ecx
    pop ebp
    ret 4
; mnich z bronia 0x546F37: zamiast "lea ecx, [esi+BAATNFG]" (bez broni zostaje BAATMKU)
bab_mnich:
    push eax
    push edx
    push 6
    push 1
    call prog
    test eax, eax
    jnz .k
    lea eax, [esi+0x18c4]
.k: mov ecx, eax
    pop edx
    pop eax
    ret

;================================================================ dane
align 4
miot_wart:
          dd 1
n_rasy:   db 'DSRASY', 0, 0
n_rwrog:  db 'DSRWROG', 0
n_rlab:   db 'RLAB', 0
n_dv:     db 'DARKVISION', 0
n_giant:  db 'GIANT_AC', 0
n_miot:   db 'THROWN', 0
n_sr:     db 'SR_LEVEL', 0
n_bonus:  db 'BONUS', 0
n_aber:   db 'ABERRATION', 0
n_e:      db 'E1', 0
n_prog:   db 'DSKLPROG'          ; CResRef: 8 znakow
          db 0
k_hp:     db 'HP', 0
k_bab:    db 'BAB', 0
k_save:   db 'SAVE', 0
c1:  db 'BARBARIAN', 0
c2:  db 'BARD', 0
c3:  db 'CLERIC', 0
c4:  db 'DRUID', 0
c5:  db 'FIGHTER', 0
c6:  db 'MONK', 0
c7:  db 'PALADIN', 0
c8:  db 'RANGER', 0
c9:  db 'ROGUE', 0
c10: db 'SORCERER', 0
c11: db 'WIZARD', 0
align 4
nazwy_kol:  dd k_hp, k_bab, k_save
nazwy_klas: dd c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11
; tablice oryginalne w obiekcie regul (klasa 1..11); barbarzynca: HPBARB (oryginal: HPWAR z kostka 12 - to samo)
dom_hp:  dd 0x3a0, 0x37c, 0x358, 0x358, 0x310, 0x3c4, 0x310, 0x310, 0x37c, 0x334, 0x334
dom_bab: dd 0x18a0, 0x18c4, 0x18c4, 0x18c4, 0x18a0, 0x18c4, 0x18a0, 0x18a0, 0x18c4, 0x18e8, 0x18e8
dom_sv:  dd 0x238, 0x2a4, 0x214, 0x214, 0x238, 0x2c8, 0x238, 0x238, 0x280, 0x25c, 0x25c
koniec_rasy:
