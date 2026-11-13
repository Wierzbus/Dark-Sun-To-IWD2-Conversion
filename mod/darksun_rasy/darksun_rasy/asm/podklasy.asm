; Podklasy (kity) dla IWD2 GOG 2.01 – paladyn, barbarzynca, kaplan, wojownik, tropiciel, druid, bard, zaklinacz;
; tablice CLAB nowych kitow.
; Kod w niewykorzystanym koncu sekcji .text (0x8468F1..0x847000).
bits 32
org 0x846900

TAB        equ 0x846C00          ; wpisy po 32 B: +0 bit kitu, +4 strref etykiety, +8 nazwa wiersza (ASCIIZ, do 15 znakow),
                                 ; +0x17 numer klasy, +0x18 nazwa tablicy CLAB (8 znakow, 0 = brak)
CLR_HELP   equ 0x846D04          ; strref opisu nowego bostwa (okno 12)
NOK        equ 0x846D08          ; 12 x strref etykiety "bez podklasy" wg numeru klasy (okno 52, przycisk 1)
KPTR       equ 0xA1AF00          ; 8 wskaznikow na obiekty C2DArray tablic CLAB kitow (koniec .data, VirtualSize 0x176000)
KPTR_PIESC  equ 0xA1AF20          ; wskaznik na C2DArray tablicy DSMFIST (piesc mnicha)

; ---------------------------------------------------------------- GetClassRow 0x541DA0
; nowe bity (0xFF000000) -> nazwa wiersza z tabeli TAB
klasa_wiersz:
    mov eax, [esp+0xc]
    test eax, 0xff000000
    jz .oryg
    mov edx, TAB
.p: mov ecx, [edx]
    test ecx, ecx
    jz .oryg
    test eax, ecx
    jnz .jest
    add edx, 32
    jmp .p
.jest:
    push esi
    mov esi, [esp+8]
    lea eax, [edx+8]
    push eax
    mov ecx, esi
    call 0x7fcc88               ; CString(const char*)
    mov eax, esi
    pop esi
    ret 0xc
.oryg:
    push ecx
    mov eax, [esp+0xc]
    jmp 0x541da5

; ---------------------------------------------------------------- tekst(przycisk, strref), stdcall
; ustawia tekst przycisku z TLK i wlacza przycisk
tekst:
    push esi
    push ebx
    sub esp, 4
    mov esi, [esp+0x10]
    mov eax, [esp+0x14]
    mov ebx, esp
    push eax
    push ebx
    call 0x427b60               ; CString z TLK (cdecl: cel, strref)
    add esp, 8
    mov ecx, esi
    mov edx, [ecx]
    push eax
    call [edx+0x74]             ; SetText
    mov ecx, esp
    call 0x7fcc1a               ; ~CString
    push 1
    mov ecx, esi
    call 0x4d57c0               ; SetActive(1)
    add esp, 4
    pop ebx
    pop esi
    ret 8

; ---------------------------------------------------------------- szukaj_klase: cl = klasa -> edx = wpis TAB albo 0
szukaj_klase:
    mov edx, TAB
.p: cmp dword [edx], 0
    je .brak
    cmp cl, [edx+0x17]
    je .r
    add edx, 32
    jmp .p
.brak:
    xor edx, edx
.r: ret

; ---------------------------------------------------------------- okno 52: wybor galezi (0x60D6C3, eax = klasa-6)
; mnich i paladyn jak w oryginale; klasa z wpisem w TAB: przycisk 1 = bez podklasy (NOK), 2 = podklasa
okno52:
    test eax, eax
    je 0x60d758                 ; mnich
    cmp eax, 1
    je 0x60d6d0                 ; paladyn
    lea ecx, [eax+6]
    call szukaj_klase
    test edx, edx
    jz .bez
    push edx
    and ecx, 0xff
    push dword [NOK+4*ecx]
    push edi                    ; przycisk 1
    call tekst
    pop edx
    mov eax, [edx+4]
    cmp eax, -1
    je .bez
    push eax
    push ebp                    ; przycisk 2
    call tekst
.bez:
    jmp 0x60d7fb

; ---------------------------------------------------------------- okno 52: 4. zakon paladyna (zamiast jmp 0x60D7DB w 0x60D753)
paladyn4:
    mov eax, [TAB+4]
    cmp eax, -1
    je .k
    push ecx                    ; CString do zniszczenia w 0x60D7DB
    push eax
    push dword [esp+0x70]       ; przycisk 4 ([esp+0x68] w funkcji)
    call tekst
    pop ecx
.k: jmp 0x60d7db

; ---------------------------------------------------------------- klikniecie w oknie 52 (zamiast mov [edx+0x80C],eax w 0x621DBE)
; paladyn: przycisk 4 -> bit z TAB; inne klasy z wpisem: przycisk 2 -> bit, 1 -> 0 (bez podklasy)
klik:
    push edx
    mov ecx, [esp+0x1c]         ; klasa ([esp+0x14] w funkcji)
    call szukaj_klase
    test edx, edx
    jz .zapisz
    cmp byte [esp+0x1c], 7
    jne .inna
    cmp dword [esi+0xa], 4
    jne .zapisz
    mov eax, [edx]
    jmp .zapisz
.inna:
    xor eax, eax
    cmp dword [esi+0xa], 2
    jne .zapisz
    mov eax, [edx]
.zapisz:
    pop edx
    mov [edx+0x80c], eax
    ret

; ---------------------------------------------------------------- przycisk Gotowe w oknie 52 (zamiast mov ebp,[ebp+0x80C] w 0x615C50)
; klasy z wpisem w TAB (poza paladynem) moga nie miec podklasy (kit 0)
gotowe:
    mov ebp, [ebp+0x80c]
    test ebp, ebp
    jnz .r
    cmp byte [esp+0x28], 7      ; klasa ([esp+0x24] w funkcji); paladyn musi miec zakon
    je .r
    push ecx
    push edx
    mov ecx, [esp+0x30]
    call szukaj_klase
    test edx, edx
    pop edx
    pop ecx
    jz .r
    inc ebp
.r: ret

; ================================================================ KAPLAN: nowe bostwo, przycisk 14 w oknie 12
; GetKit przycisku (0x61CD4A, ecx = id, eax = id-2): id 14 -> bit nowego bostwa
k_getkit:
    cmp eax, 0xb
    jbe 0x61cd4f
    cmp ecx, 14
    jne 0x61cd9e
    mov eax, [TAB+64]
    ret 4

; opis po kliknieciu (0x61D031): nowy bit -> CLR_HELP
k_help:
    cmp eax, [TAB+64]
    jne .a
    mov eax, [CLR_HELP]
    jmp 0x61d062
.a: push 0
    push 0x8a636c
    jmp 0x61d038

; etykieta przycisku w petli okna 12 dla kaplana (0x6100F0, edi = id, ebp = strref)
k_etykieta:
    cmp edi, 9
    jne .n
    mov ebp, 0x94db
    jmp 0x6100fa
.n: cmp edi, 14
    jne 0x6100fa
    mov ebp, [TAB+68]
    jmp 0x6100fa

; koniec petli kaplana (0x61012E): po id 13 jeszcze id 14, jesli bostwo ma tekst
k_petla:
    cmp edi, 0xd
    jle 0x610041
    cmp edi, 0xe
    jne 0x610137
    cmp dword [TAB+68], -1
    jne 0x610041
    call ukryj14
    jmp 0x610137

; koniec petli czarodzieja (0x61001B): przycisk 14 ukryty
k_mag:
    call ukryj14
    jmp 0x610152

; ukryj przycisk 14 okna (esi = okno)
ukryj14:
    push 14
    mov ecx, esi
    call 0x4d2ca0               ; GetControl
    test eax, eax
    jz .r
    push 0
    mov ecx, eax
    call 0x4d57c0               ; SetActive(0)
.r: ret

;================================================================ tabela2da: wczytanie 2DA przy pierwszym uzyciu
; wejscie: esi = adres slotu (dword: wskaznik obiektu albo 0), edi = adres nazwy (CResRef, 8 znakow)
; wyjscie: eax = obiekt C2DArray (operator new 0x7FC95B, konstruktor 0x5402E0, Load 0x402B70)
tabela2da:
    mov eax, [esi]
    test eax, eax
    jnz .r
    push ecx
    push edx
    push 0x24
    call 0x7fc95b               ; operator new
    add esp, 4
    test eax, eax
    jz .x
    push eax
    mov ecx, eax
    call 0x5402e0               ; C2DArray()
    mov ecx, [esp]
    push edi
    call 0x402b70               ; Load(CResRef*)
    pop eax
    mov [esi], eax
.x: pop edx
    pop ecx
.r: ret

;================================================================ CLAB: tablica zdolnosci klasy (0x546030)
; GetClabTable(klasa, kit) zwraca wskaznik do C2DArray. Dla nowego kitu i zgodnej klasy:
; wlasny obiekt (PTR[i]) wczytywany przy pierwszym uzyciu z nazwy pod +0x18 wpisu tabeli.
clab:
    mov eax, [esp+8]
    test eax, 0xff000000
    jz .oryg
    push ebx
    mov edx, TAB
.p: mov ebx, [edx]
    test ebx, ebx
    jz .nie
    test eax, ebx
    jnz .jest
    add edx, 32
    jmp .p
.jest:
    mov bl, [edx+0x17]
    cmp bl, [esp+8]             ; klasa (arg 1)
    jne .nie
    cmp byte [edx+0x18], 0
    je .nie
    push esi
    push edi
    mov eax, edx
    sub eax, TAB
    shr eax, 5                  ; numer wpisu
    lea esi, [KPTR+eax*4]
    lea edi, [edx+0x18]
    call tabela2da
    pop edi
    pop esi
    test eax, eax
    jz .nie
    pop ebx
    ret 8
.nie:
    pop ebx
.oryg:
    mov eax, [esp+4]
    and eax, 0xff
    jmp 0x546039

times (TAB - 0x846900) - ($ - $$) db 0xcc
dane:
%macro kit 4                    ; bit, nazwa wiersza, klasa, CLAB
    dd %1, -1
    db %2, 0
    times 0x17 - 8 - (%strlen(%2) + 1) db 0
    db %3
    db %4
%endmacro
    kit 0x01000000, 'PALADIN_DS',   7, 'CLABDS01'
    kit 0x02000000, 'BARBARIAN_DS', 1, 'CLABDS02'
    kit 0x04000000, 'CLERIC_DS',    3, 'CLABDS03'
    kit 0x08000000, 'FIGHTER_DS',   5, 'CLABDS04'
    kit 0x10000000, 'RANGER_DS',    8, 'CLABDS05'
    kit 0x20000000, 'DRUID_DS',     4, 'CLABDS06'
    kit 0x40000000, 'BARD_DS',      2, 'CLABDS07'
    kit 0x80000000, 'SORCERER_DS', 10, 'CLABDS08'
    dd 0                        ; koniec tabeli (0x846D00)
    dd -1                       ; CLR_HELP
    times 12 dd -1              ; NOK[klasa]

;================================================================ piesc mnicha z tabeli DSMFIST.2DA (0x723417)
; W oryginale: poziom mnicha (eax) -> tablica 0x723808 -> jeden z 11 przypadkow tworzacych przedmiot
; 00MFIST1..9 (operator new 0xEE, CResRef 0x78A990, CItem 0x4E7E90) -> [esi+0x4B00] w 0x7237A3.
; Tu: wiersz (poziom - 1) tabeli DSMFIST, kolumna 0 = przedmiot. Brak tabeli -> kod oryginalny.
piesc_nazwa: db 'DSMFIST', 0
mnich:
    push eax                    ; poziom
    push esi
    push edi
    mov esi, KPTR_PIESC
    mov edi, piesc_nazwa
    call tabela2da
    pop edi
    pop esi
    pop ecx                     ; ecx = poziom
    test eax, eax
    jz .oryg
    movsx edx, word [eax+0x22]  ; wiersze
    test edx, edx
    jle .oryg
    dec ecx
    jns .a
    xor ecx, ecx
.a: cmp ecx, edx
    jl .b
    lea ecx, [edx-1]
.b: movsx edx, word [eax+0x20]  ; kolumny
    imul ecx, edx
    mov edx, [eax+0x18]
    mov edx, [edx+ecx*4]        ; CString -> tekst nazwy przedmiotu
    push edx
    push 0xee
    call 0x7fc95b               ; operator new (CItem)
    add esp, 4
    pop edx
    mov edi, eax
    mov [esp+0xc], edi
    mov dword [esp+0x18], 1
    test edi, edi
    je 0x7237a1
    push 0
    push 0
    push 0
    push 0
    push 0
    sub esp, 8
    mov ecx, esp
    mov [esp+0x24], esp
    push edx
    call 0x78a990               ; CResRef(const char*)
    mov ecx, edi
    call 0x4e7e90               ; CItem(CResRef, 0, 0, 0, 0, 0)
    jmp 0x7237a3
.oryg:
    mov eax, ecx
    dec eax
    cmp eax, 0x1d
    ja 0x72375c
    xor ecx, ecx
    mov cl, [eax+0x723808]
    jmp [ecx*4+0x7237dc]
