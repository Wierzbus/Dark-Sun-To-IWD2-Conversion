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
;   MAX_RANK      (test56) maks. ranga atutu 2..15 (atuty 75..150); premie mnoza sie przez range
;   premie liczone przy kazdym przeliczeniu postaci (test55): ALCHEMY ... WILDERNESS_LORE (nazwy z SKILLS.IDS),
;   FORTITUDE, REFLEX, WILL, AC (ogolna, jak opcode 0 typ 0), ATTACK (jak opcode 54)
; Komorka * (albo brak kolumny) = bez wymagania / bez premii.
;
; Przebieg: 0x762890 (ustaw range atutu) - przejscie 0 -> 1 dla atutu >= 75 zapisuje atut jako oczekujacy dla postaci,
; 1 -> 0 kasuje; awans / koniec kreatora (0x71E760, hak 0x71E996) naklada tablice CLAB oczekujacych atutow, ktore
; postac nadal ma (procedura CLAB 0x722D50 z klasa 12 i poziomem 1), i czysci liste.
bits 32
org 0xA28000

N_STARE   equ 75                ; atuty gry 0..74
N_MAX     equ 192               ; test56: bity +0x75C..+0x773 (CRE 0x1C0..0x1D7; 0x1CC..0x1D7 wolne w CRE gry)
N_NOWE    equ N_MAX - N_STARE   ; 117
RANGA_DO  equ 150               ; rangi w polbajtach +0x78E.. (CRE 0x1F2..0x217, 38 B) dla atutow 75..150
RANGI     equ 0x78E
LV_TAB    equ 0xA2A000          ; 192 dword: rangi atutow na poczatku awansu (bylo: ekran awansu +0x650, 75 dword)
CC_TAB    equ 0xA2A300          ; 192 dword: j.w. dla kreatora postaci (bylo: ekran kreatora +0x14B2)
PEND      equ 0xA2A600          ; 8 wpisow po 20 B: postac, maska 4 dword (bit i = atut 75 + i)
N_PEND    equ 8
ATUT      equ 0xA2A700          ; atut, ktorego tablice CLAB naklada procedura CLAB (0 = zwykla tablica rasy)
AW_W      equ 0xA2A704          ; wiersz DSATUTY
AW_T      equ 0xA2A708          ; C2DArray DSATUTY
PR_OK     equ 0xA2A70C          ; 1 = tablica PREM zbudowana z DSATUTY
LICZBA    equ 0x84EA66          ; slowo: liczba atutow na ekranach (.rdata - instalator robi ja zapisywalna)
PREM      equ 0xA2A800          ; 117 wierszy x N_PREM bajtow: 0..20 premie (int8), 21 = MAX_RANK
N_PREM    equ 24                ; 16 umiejetnosci, 3 rzuty, KP, atak, maks. ranga, zapas
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
.n: add esi, 20
    dec edx
    jnz .p
    mov esi, edi
    test esi, esi
    jnz .nowy
    mov esi, PEND               ; brak miejsca: nadpisz pierwszy wpis
.nowy:
    mov [esi], ebx
    xor eax, eax
    mov [esi+4], eax
    mov [esi+8], eax
    mov [esi+12], eax
    mov [esi+16], eax
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
.n: add esi, 20
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
    add esi, 20
    loop .s
    jmp .k
.mam:
    mov dword [esi], 0
    xor ebp, ebp
.b: bt [esi+4], ebp
    jnc .n
    lea eax, [ebp+N_STARE]
    push eax
    mov ecx, edi
    call 0x763150               ; postac nadal ma atut?
    test eax, eax
    jz .n
    lea eax, [ebp+N_STARE]
    mov [ATUT], eax
    push esi
    push 1                      ; jak przy klasach (argument 2 funkcji awansu)
    push 1                      ; zdobyte poziomy: kolumna 1
    push KLASA_RASY
    mov ecx, edi
    call 0x722d50
    pop esi
    mov dword [ATUT], 0
.n: inc ebp
    cmp ebp, N_NOWE
    jb .b
    xor eax, eax
    mov [esi+4], eax
    mov [esi+8], eax
    mov [esi+12], eax
    mov [esi+16], eax
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

;================================================================ test55: liczba atutow z FEATS.2DA
; 0x53EFBA: call 0x402B70 (Load) dla FEATS w regulach (ecx = C2DArray) -> po wczytaniu LICZBA = wiersze (75..96)
feats_wczyt:
    push ecx
    push dword [esp+8]
    call 0x402b70
    pop ecx
    movsx eax, word [ecx+0x22]
    cmp eax, N_MAX
    jle .a
    mov eax, N_MAX
.a: cmp eax, N_STARE
    jge .b
    mov eax, N_STARE
.b: mov [LICZBA], ax
    ret 4

; 0x765DC8 (lista atutow na karcie): "cmp eax, 0x4B; mov [esp+0x10], eax" -> call; nop x2
karta_n:
    mov [esp+0x14], eax
    push edx
    movzx edx, word [LICZBA]
    cmp eax, edx
    pop edx
    ret

; 0x5E1250 (atuty z kolumn FEATS.2DA w kreatorze): "inc esi; cmp esi, 0x4B; jl 0x5E11EB" -> call; nop
kreator_n:
    inc esi
    push eax
    movzx eax, word [LICZBA]
    cmp esi, eax
    pop eax
    jge .k
    mov dword [esp], 0x5e11eb
.k: ret

;================================================================ test55: premie atutow przy przeliczeniu postaci
; 0x734689 (ProcessEffectList, po efektach, przed dodaniem premii 0x4464E0): esi = postac, edi = premie +0x25D0,
; ebx = statystyki +0x920. Umiejetnosci i rzuty jak efekty kumulowane (premie: +0x144+u, +0x1C/+0x1E/+0x20),
; KP i atak jak opcode 0 / 54 (statystyki: +0xC, +0x18).
atut_premie:
    pushad
    cmp dword [PR_OK], 0
    jne .gotowe
    call buduj_prem
.gotowe:
    movzx eax, word [LICZBA]
    mov ebp, eax
    mov ecx, N_STARE
.b: cmp ecx, ebp
    jae .k
    bt [esi+0x75c], ecx
    jnc .n
    push ecx
    push ecx
    call ranga_post             ; eax = ranga (>= 1)
    mov edx, ecx
    sub edx, N_STARE
    imul edx, N_PREM
    add edx, PREM
    push ebp
    mov ebp, eax
    xor ecx, ecx
.u: movsx eax, byte [edx+ecx]
    imul eax, ebp
    add [edi+0x144+ecx], al
    inc ecx
    cmp ecx, 16
    jb .u
    movsx eax, byte [edx+16]
    imul eax, ebp
    add [edi+0x1c], ax
    movsx eax, byte [edx+17]
    imul eax, ebp
    add [edi+0x1e], ax
    movsx eax, byte [edx+18]
    imul eax, ebp
    add [edi+0x20], ax
    movsx eax, byte [edx+19]
    imul eax, ebp
    add [esi+0x92c], ax
    movsx eax, byte [edx+20]
    imul eax, ebp
    add [esi+0x938], ax
    pop ebp
    pop ecx
.n: inc ecx
    jmp .b
.k: popad
    push edi
    mov ecx, ebx
    call 0x4464e0
    jmp 0x734691

; buduj_prem: PREM z DSATUTY (raz na gre; brak tabeli = premie 0, MAX_RANK 1). Zachowuje rejestry.
buduj_prem:
    pushad
    mov dword [PR_OK], 1
    mov edi, PREM
    mov ecx, N_NOWE * N_PREM
    xor eax, eax
    rep stosb
    xor ebx, ebx                ; wiersz
.w: mov edx, ebx
    imul edx, N_PREM
    mov byte [PREM+edx+21], 1
    push ebx
    call aw_tab
    test eax, eax
    jz .nw
    xor esi, esi                ; kolumna premii
.c: push dword [n_prem+esi*4]
    call aw
    cmp eax, -1
    je .cn
    mov edx, ebx
    imul edx, N_PREM
    mov [PREM+edx+esi], al
.cn:
    inc esi
    cmp esi, 21
    jb .c
    push n_maxr
    call aw
    cmp eax, 1
    jle .nw
    cmp eax, 15
    jle .r
    mov eax, 15
.r: cmp ebx, RANGA_DO - N_STARE
    ja .nw                      ; atut ponad 150: bez rang
    mov edx, ebx
    imul edx, N_PREM
    mov [PREM+edx+21], al
.nw:
    inc ebx
    cmp ebx, N_NOWE
    jb .w
    popad
    ret

;================================================================ test56: rangi nowych atutow
; ranga_post(atut) -> eax = ranga postaci esi (atut >= 75, bit ustawiony): polbajt (0 = 1), atut > 150 -> 1. stdcall
ranga_post:
    mov eax, [esp+4]
    cmp eax, RANGA_DO
    ja .jeden
    sub eax, N_STARE
    push ecx
    mov ecx, eax
    shr eax, 1
    movzx eax, byte [esi+RANGI+eax]
    test cl, 1
    jz .m
    shr eax, 4
.m: and eax, 15
    pop ecx
    test eax, eax
    jnz .k
.jeden:
    mov eax, 1
.k: ret 4

; maks_rang(atut) -> eax = MAX_RANK z DSATUTY (1 dla atutow gry i braku tabeli). stdcall, zachowuje rejestry
maks_rang:
    mov eax, [esp+4]
    cmp eax, N_STARE
    jb .jeden
    cmp eax, N_MAX
    jae .jeden
    cmp dword [PR_OK], 0
    jne .g
    call buduj_prem
.g: mov eax, [esp+4]
    sub eax, N_STARE
    imul eax, N_PREM
    movzx eax, byte [PREM+eax+21]
    ret 4
.jeden:
    mov eax, 1
    ret 4

; 0x76290B (SetFeatRank, "ja 0x762D5E" po ustawieniu bitu): edi = atut, ebx = ranga, esi = postac
ranga_zapis:
    cmp edi, N_STARE
    jb 0x762d5e
    cmp edi, RANGA_DO
    ja 0x762d5e
    mov eax, ebx
    test eax, eax
    jge .a
    xor eax, eax
.a: cmp eax, 15
    jle .b
    mov eax, 15
.b: lea ecx, [edi-N_STARE]
    mov edx, ecx
    shr edx, 1
    test cl, 1
    jnz .gorny
    and byte [esi+RANGI+edx], 0xf0
    or [esi+RANGI+edx], al
    jmp 0x762d5e
.gorny:
    shl al, 4
    and byte [esi+RANGI+edx], 0x0f
    or [esi+RANGI+edx], al
    jmp 0x762d5e

; 0x762E6A (GetFeatRank, "ja 0x762FD1" = ranga 1): edi = atut (bit ustawiony), esi = postac
ranga_odczyt:
    cmp edi, N_STARE
    jb 0x762fd1
    push edi
    call ranga_post
    pop edi
    pop esi
    ret 4

; 0x7630C3 (maks. ranga): zamiast "lea eax, [esi-3]; cmp eax, 0x42; pop esi; ja 0x7630F3" - esi = atut
ranga_max:
    cmp esi, N_STARE
    jae .nowy
    lea eax, [esi-3]
    cmp eax, 0x42
    pop esi
    ja 0x7630f3
    jmp 0x7630cc
.nowy:
    push esi
    call maks_rang
    pop esi
    ret 4

; 0x763A6C (czy mozna wybrac atut, "ja 0x763BB7" = jednorangowy): edi = atut, esi = postac, [esp+0x10] = warunki?
wybor_atut:
    cmp edi, N_STARE
    jb 0x763bb7
    push edi
    call maks_rang
    cmp eax, 1
    jle 0x763bb7
    mov ecx, eax
    bt [esi+0x75c], edi
    jnc .ma0
    push edi
    call ranga_post
    cmp eax, ecx
    jge 0x763a9d                ; maks. ranga osiagnieta -> 0
.ma0:
    cmp dword [esp+0x10], 0
    je 0x763bec                 ; bez warunkow -> 1
    push 1
    push edi
    mov ecx, esi
    call 0x763200
    pop edi
    pop esi
    ret 8

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
n_maxr:   db 'MAX_RANK', 0
p00: db 'ALCHEMY', 0
p01: db 'ANIMAL_EMPATHY', 0
p02: db 'BLUFF', 0
p03: db 'CONCENTRATION', 0
p04: db 'DIPLOMACY', 0
p05: db 'DISABLE_DEVICE', 0
p06: db 'HIDE', 0
p07: db 'INTIMIDATE', 0
p08: db 'KNOWLEDGE_ARCANA', 0
p09: db 'MOVE_SILENTLY', 0
p10: db 'OPEN_LOCK', 0
p11: db 'PICK_POCKET', 0
p12: db 'SEARCH', 0
p13: db 'SPELLCRAFT', 0
p14: db 'USE_MAGIC_DEVICE', 0
p15: db 'WILDERNESS_LORE', 0
p16: db 'FORTITUDE', 0
p17: db 'REFLEX', 0
p18: db 'WILL', 0
p19: db 'AC', 0
p20: db 'ATTACK', 0
align 4
n_prem: dd p00, p01, p02, p03, p04, p05, p06, p07, p08, p09, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20
n_cechy:     dd n_str, n_int, n_wis, n_dex, n_con, n_cha
n_cechy_off: db 0x02, 0x03, 0x04, 0x05, 0x06, 0x07     ; + 0x800 nizej
