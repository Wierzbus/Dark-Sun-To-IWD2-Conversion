; Nowe atuty (test54): numery FEATS.IDS od 75 w gore (bity postaci +0x75C..+0x767 mieszcza 96 atutow).
; Kod w sekcji .dsras od 0xA28000, dane od 0xA28C00. Etykiety z innych plikow podaje nasm -D
; (szukaj, wczytaj, komorka, clab_rasa, poziom, rasa_awans, pr_bab).
;
; DSATUTY.2DA: wiersz i = atut o numerze 75 + i (kolejnosc jak nowe wiersze FEATS.2DA). Kolumny:
;   CLAB          tablica w formacie CLAB (kolumna 1): AP_ / GA_ / FA_ nakladane raz, przy zdobyciu atutu
;   MIN_STR, MIN_DEX, MIN_CON, MIN_INT, MIN_WIS, MIN_CHA   minimalna cecha (bazowa)
;   MIN_BAB       minimalna premia do ataku (jak w warunkach klas prestizowych)
;   MIN_LEVEL, MAX_LEVEL   poziom postaci (MAX_LEVEL 1 = tylko na 1. poziomie)
;   CLASS, CLASS_LEVEL     klasa (CLASS.IDS 1..11) i jej minimalny poziom
;   FEAT          wymagany atut (FEATS.IDS)
;   SKILL, SKILL_RANK      umiejetnosc (SKILLS.IDS 0..15) i minimalna ranga
;   RACE, SUBRACE rasa (RACE.IDS 1..7) i podrasa
; Komorka * (albo brak kolumny) = bez wymagania.
;
; Przebieg: 0x762890 (ustaw range atutu) - przejscie 0 -> 1 dla atutu >= 75 zapisuje atut jako oczekujacy dla postaci,
; 1 -> 0 kasuje; awans / koniec kreatora (0x71E760, hak 0x71E996) naklada tablice CLAB oczekujacych atutow, ktore
; postac nadal ma (procedura CLAB 0x722D50 z klasa 12 i poziomem 1), i czysci liste.
bits 32
org 0xA28000

N_STARE   equ 75                ; atuty gry 0..74
N_MAX     equ 96                ; 3 dwordy bitow
LV_TAB    equ 0xA28C00          ; 96 dword: rangi atutow na poczatku awansu (bylo: ekran awansu +0x650, 75 dword)
CC_TAB    equ 0xA28D80          ; 96 dword: j.w. dla kreatora postaci (bylo: ekran kreatora +0x14B2)
PEND      equ 0xA28F00          ; 8 wpisow: postac, maska (bit i = atut 75 + i)
N_PEND    equ 8
ATUT      equ 0xA28F40          ; atut, ktorego tablice CLAB naklada procedura CLAB (0 = zwykla tablica rasy)
AW_W      equ 0xA28F44          ; wiersz DSATUTY
AW_T      equ 0xA28F48          ; C2DArray DSATUTY
KLASA_RASY equ 12

    db 'DSATUTY1'               ; znacznik (sprawdza skrypt budujacy)

;================================================================ 0x762897 (w 0x762890 SetFeatRank): zamiast
; "cmp edi, 0x4B; mov esi, ecx" - call atut_ustaw; po powrocie flagi z "cmp edi, 96" dla nastepnego jb
atut_ustaw:
    mov esi, ecx
    cmp edi, N_STARE
    jb .k
    cmp edi, N_MAX
    jae .k
    push eax
    push ecx
    push edx
    mov ecx, edi
    and ecx, 31
    mov edx, 1
    shl edx, cl
    mov eax, edi
    shr eax, 5
    test [esi+0x75c+eax*4], edx ; atut juz jest?
    setnz cl
    mov eax, [esp+0x24]         ; ranga (argument 2 funkcji 0x762890)
    test eax, eax
    jle .zdejmij
    test cl, cl
    jnz .p                      ; 1 -> 1: nic
    lea eax, [edi-N_STARE]
    push eax
    push esi
    call pend_ustaw
    jmp .p
.zdejmij:
    test cl, cl
    jz .p                       ; 0 -> 0: nic
    lea eax, [edi-N_STARE]
    push eax
    push esi
    call pend_kasuj
.p: pop edx
    pop ecx
    pop eax
.k: cmp edi, N_MAX
    ret

; pend_ustaw(postac, bit) / pend_kasuj(postac, bit), stdcall; zachowuja rejestry
pend_ustaw:
    pushad
    mov ebx, [esp+0x24]
    mov ecx, [esp+0x28]
    mov esi, PEND
    xor edi, edi                ; pierwszy wolny
    mov edx, N_PEND
.p: mov eax, [esi]
    cmp eax, ebx
    je .jest
    test eax, eax
    jnz .n
    test edi, edi
    jnz .n
    mov edi, esi
.n: add esi, 8
    dec edx
    jnz .p
    mov esi, edi
    test esi, esi
    jnz .nowy
    mov esi, PEND               ; brak miejsca: nadpisz pierwszy wpis
.nowy:
    mov [esi], ebx
    mov dword [esi+4], 0
.jest:
    bts [esi+4], ecx
    popad
    ret 8

pend_kasuj:
    pushad
    mov ebx, [esp+0x24]
    mov ecx, [esp+0x28]
    mov esi, PEND
    mov edx, N_PEND
.p: cmp [esi], ebx
    jne .n
    btr [esi+4], ecx
.n: add esi, 8
    dec edx
    jnz .p
    popad
    ret 8

;================================================================ hak 0x71E996 (awans i koniec kreatora: edi = postac)
; tablice CLAB oczekujacych atutow, potem dotychczasowy kod (tablica rasy, SR_LEVEL)
awans_atut:
    pushad
    mov esi, PEND
    mov ecx, N_PEND
.s: cmp [esi], edi
    je .mam
    add esi, 8
    loop .s
    jmp .k
.mam:
    mov ebx, [esi+4]
    mov dword [esi], 0
    mov dword [esi+4], 0
    xor ebp, ebp
.b: bt ebx, ebp
    jnc .n
    lea eax, [ebp+N_STARE]
    push eax
    mov ecx, edi
    call 0x763150               ; postac nadal ma atut?
    test eax, eax
    jz .n
    lea eax, [ebp+N_STARE]
    mov [ATUT], eax
    push 1                      ; jak przy klasach (argument 2 funkcji awansu)
    push 1                      ; zdobyte poziomy: kolumna 1
    push KLASA_RASY
    mov ecx, edi
    call 0x722d50
    mov dword [ATUT], 0
.n: inc ebp
    cmp ebp, N_MAX - N_STARE
    jb .b
.k: popad
    jmp rasa_awans

;================================================================ GetClabTable 0x546030: tablica atutu (klasa 12, ATUT)
clab_atut:
    cmp dword [esp+4], KLASA_RASY
    jne clab_rasa
    cmp dword [ATUT], 0
    je clab_rasa
    push ecx
    push edx
    mov eax, [ATUT]
    sub eax, N_STARE
    push eax
    call aw_tab                 ; eax = DSATUTY albo 0, AW_W = wiersz
    test eax, eax
    jz .nie
    push 1
    push n_clab
    push eax
    call szukaj
    cmp eax, -1
    je .nie
    push eax
    push dword [AW_W]
    mov eax, [AW_T]
    call komorka
    test eax, eax
    jz .nie
    cmp byte [eax], '*'
    je .nie
    cmp byte [eax], 0
    je .nie
    push eax
    call wczytaj
    jmp .k
.nie:
    xor eax, eax
.k: pop edx
    pop ecx
    ret 8

; procedura CLAB 0x722DE3 (call poziom): dla tablicy atutu poziom 1
poziom_atut:
    cmp dword [esp+4], KLASA_RASY
    jne poziom
    cmp dword [ATUT], 0
    je poziom
    mov eax, 1
    ret 4

;================================================================ pomocnicze
; aw_tab(wiersz) -> eax = C2DArray DSATUTY (AW_T) albo 0 (brak tabeli / wiersza); AW_W = wiersz. stdcall
aw_tab:
    push n_atuty
    call wczytaj
    test eax, eax
    jz .nie
    movsx ecx, word [eax+0x22]
    mov edx, [esp+4]
    cmp edx, ecx
    jae .nie
    mov [AW_T], eax
    mov [AW_W], edx
    ret 4
.nie:
    xor eax, eax
    ret 4

; aw(nazwa kolumny) -> eax = liczba z komorki (AW_T, AW_W) albo -1 (brak kolumny, pusta, *). stdcall
aw:
    push ecx
    push edx
    push 1
    push dword [esp+0x10]
    push dword [AW_T]
    call szukaj
    cmp eax, -1
    je .k
    push eax
    push dword [AW_W]
    mov eax, [AW_T]
    call komorka
    test eax, eax
    jz .brak
    mov cl, [eax]
    cmp cl, '*'
    je .brak
    test cl, cl
    jz .brak
    push eax
    call 0x7e7b03               ; atoi (cdecl)
    add esp, 4
    jmp .k
.brak:
    or eax, -1
.k: pop edx
    pop ecx
    ret 4

;================================================================ warunki atutu: 0x763270 "ja 0x7638FD" (numer > 74)
; esi = postac, ebp = atut; na stosie edi, esi, ebp, ebx funkcji 0x763200. Wynik w ebx, dalej 0x7638FD (epilog).
atut_wymog:
    xor ebx, ebx
    cmp ebp, N_MAX
    jae .k
    lea eax, [ebp-N_STARE]
    push eax
    call aw_tab
    test eax, eax
    jz .k
    ; cechy bazowe (+0x802: SIL, INT, MAD, ZRE, KON, CHA)
    xor edi, edi
.c: push dword [n_cechy+edi*4]
    call aw
    test eax, eax
    jle .cn
    movzx ecx, byte [n_cechy_off+edi]
    movzx ecx, byte [esi+ecx+0x800]
    cmp ecx, eax
    jl .k
.cn:
    inc edi
    cmp edi, 6
    jb .c
    push n_bab
    call aw
    test eax, eax
    jle .lv
    mov edi, eax
    push esi
    call pr_bab
    cmp eax, edi
    jl .k
.lv:
    movzx edi, byte [esi+0x966] ; poziom postaci
    push n_minlv
    call aw
    test eax, eax
    jle .mx
    cmp edi, eax
    jl .k
.mx:
    push n_maxlv
    call aw
    test eax, eax
    jle .kl
    cmp edi, eax
    jg .k
.kl:
    push n_class
    call aw
    dec eax
    cmp eax, 10
    ja .at
    movzx edi, byte [esi+0x627+eax]
    test edi, edi
    jz .k
    push n_clevel
    call aw
    cmp edi, eax
    jl .k
.at:
    push n_feat
    call aw
    test eax, eax
    js .um
    cmp eax, N_MAX
    jae .k
    push eax
    mov ecx, esi
    call 0x763150
    test eax, eax
    jz .k
.um:
    push n_skill
    call aw
    cmp eax, 15
    ja .rasa
    movzx edi, byte [esi+0x7b4+eax]
    push n_rank
    call aw
    cmp edi, eax
    jl .k
.rasa:
    push n_race
    call aw
    test eax, eax
    jle .pod
    cmp [esi+0x26], al
    jne .k
.pod:
    push n_subrace
    call aw
    test eax, eax
    js .ok
    cmp [esi+0x27], al
    jne .k
.ok:
    mov ebx, 1
.k: jmp 0x7638fd

n_atuty:  db 'DSATUTY', 0
n_clab:   db 'CLAB', 0
n_str:    db 'MIN_STR', 0
n_int:    db 'MIN_INT', 0
n_wis:    db 'MIN_WIS', 0
n_dex:    db 'MIN_DEX', 0
n_con:    db 'MIN_CON', 0
n_cha:    db 'MIN_CHA', 0
n_bab:    db 'MIN_BAB', 0
n_minlv:  db 'MIN_LEVEL', 0
n_maxlv:  db 'MAX_LEVEL', 0
n_class:  db 'CLASS', 0
n_clevel: db 'CLASS_LEVEL', 0
n_feat:   db 'FEAT', 0
n_skill:  db 'SKILL', 0
n_rank:   db 'SKILL_RANK', 0
n_race:   db 'RACE', 0
n_subrace: db 'SUBRACE', 0
align 4
n_cechy:     dd n_str, n_int, n_wis, n_dex, n_con, n_cha
n_cechy_off: db 0x02, 0x03, 0x04, 0x05, 0x06, 0x07     ; + 0x800 nizej
