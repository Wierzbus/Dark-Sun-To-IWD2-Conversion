bits 32
org 0x440520
FLAGA equ 0xa1aff0      ; 1 = klatki BAM czytane w podwojnym rozmiarze (podglad postaci)
POWROT equ 0xa1aff4

; wejscie 0x77f520 (naglowek klatki), 3. argument = podwojnie
naglowek:
    mov eax, [FLAGA]
    or [esp+0xc], eax
    mov edx, [ecx+0x64]
    push esi
    test edx, edx
    jmp 0x77f526

; wejscie 0x77f5f0 (piksele klatki), 2. argument = podwojnie
piksele:
    mov eax, [FLAGA]
    or [esp+8], eax
    sub esp, 0x10
    push ebx
    mov ebx, ecx
    jmp 0x77f5f6

; zamiast call [edx+0x90] (rysowanie animacji podgladu): po rysowaniu flaga 0
rysuj:
    pop dword [POWROT]
    call [edx+0x90]
    mov dword [FLAGA], 0
    push dword [POWROT]
    ret

; kreator 0x61de2d: flaga 1 przed ustawieniem klatek animacji
kreator:
    mov dword [FLAGA], 1
    test byte [0x8f3b9c], 1
    ret

; ekwipunek 0x62ebff: flaga 1 przed ustawieniem klatek animacji
ekwipunek:
    mov dword [FLAGA], 1
    mov ecx, [eax+0x50f0]
    ret

; Miejsca wywolan (test12):
;   0x77F520 (6 B) -> jmp naglowek     0x77F5F0 (6 B) -> jmp piksele
;   0x61DE2D (7 B) -> call kreator     0x62EBFF (6 B) -> call ekwipunek
;   0x61DF8F, 0x62ED48 (call [edx+0x90], 6 B) -> call rysuj
; Zmienne w koncu strony .data (poza rozmiarem wirtualnym 0x175E81, nieuzywane).
