; Podklasy (kity) dla IWD2 GOG 2.01 – paladyn, barbarzynca (kaplan: osobny etap).
; Kod w niewykorzystanym koncu sekcji .text (0x8468F1..0x847000).
bits 32
org 0x846900

TAB        equ 0x846C00          ; wpisy po 32 B: +0 bit kitu, +4 strref etykiety, +8 nazwa wiersza (ASCIIZ)
BBN0_STR   equ 0x846C64          ; strref etykiety "barbarzynca bez podklasy"
CLR_HELP   equ 0x846C68          ; strref opisu nowego bostwa (okno 12)

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

; ---------------------------------------------------------------- okno 52: wybor galezi (0x60D6C3, eax = klasa-6)
okno52:
    test eax, eax
    je 0x60d758                 ; mnich
    cmp eax, 1
    je 0x60d6d0                 ; paladyn
    cmp eax, -5
    je .barbarzynca
    jmp 0x60d7fb
.barbarzynca:
    push dword [BBN0_STR]
    push edi                    ; przycisk 1
    call tekst
    mov eax, [TAB+32+4]
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
klik:
    movzx ecx, byte [esp+0x18]  ; klasa ([esp+0x14] w funkcji)
    cmp ecx, 7
    jne .b
    cmp dword [esi+0xa], 4
    jne .zapisz
    mov eax, [TAB]
    jmp .zapisz
.b: cmp ecx, 1
    jne .zapisz
    xor eax, eax
    cmp dword [esi+0xa], 2
    jne .zapisz
    mov eax, [TAB+32]
.zapisz:
    mov [edx+0x80c], eax
    ret

; ---------------------------------------------------------------- przycisk Gotowe w oknie 52 (zamiast mov ebp,[ebp+0x80C] w 0x615C50)
; barbarzynca moze nie miec podklasy (kit 0)
gotowe:
    mov ebp, [ebp+0x80c]
    test ebp, ebp
    jnz .r
    cmp byte [esp+0x28], 1      ; klasa ([esp+0x24] w funkcji)
    jne .r
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

times (TAB - 0x846900) - ($ - $$) db 0xcc
dane:
    dd 0x01000000, -1
    db 'PALADIN_DS', 0
    times (TAB + 32) - (0x846900 + ($ - $$)) db 0
    dd 0x02000000, -1
    db 'BARBARIAN_DS', 0
    times (TAB + 64) - (0x846900 + ($ - $$)) db 0
    dd 0x04000000, -1
    db 'CLERIC_DS', 0
    times (TAB + 96) - (0x846900 + ($ - $$)) db 0
    dd 0                        ; koniec tabeli
    dd -1                       ; BBN0_STR
    dd -1                       ; CLR_HELP
