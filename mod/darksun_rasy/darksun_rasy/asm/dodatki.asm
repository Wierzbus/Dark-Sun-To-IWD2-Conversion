; Dodatki do podklasy.asm (test19): zdolnosci klas z DSKLASY.2DA / DSWROG.2DA.
; Kod w martwym fragmencie dawnej obslugi piesci mnicha 0x723430..0x7237A1 (od test18 piesc idzie przez
; etykiete "mnich" w podklasy.asm, a tablica skokow 0x7237DC/0x723808 nie jest juz uzywana).
; Etykiety z podklasy.asm (zdolnosc, liczba, tabela2da, sneak_poziom) podaje nasm -D z tools/iwd2_podklasy_exe.py.
bits 32
org 0x723430

KPTR_WROG  equ 0xA1AF28          ; wskaznik na C2DArray tablicy DSWROG (preferowany wrog)

; wiersze DSKLASY: 0 EVASION, 1 UNCANNY_DEX, 2 UNCANNY_FLANK, 3 SNEAK_ATTACK, 4 FAVORED_ENEMY, 5 AURA_COURAGE
; Brak wiersza (stary DSKLASY) -> zdolnosc zwraca -1 -> zachowanie oryginalne.

;================================================================ atak z zaskoczenia 0x585D55 (esi = postac)
; zamiast "klasa lotrzyka" (maska klas, bit 0x100): dowolna klasa >= progu SNEAK_ATTACK;
; liczba kosci z DSSNEAK wg poziomu tej klasy.
sneak_klasa:
    push esi
    push 3
    call zdolnosc
    cmp eax, -1
    je .oryg
    test eax, eax
    jle 0x585d7a                ; brak zdolnosci -> 0 kosci
    mov edx, eax
    jmp sneak_poziom
.oryg:
    mov eax, [esi]
    mov ecx, esi
    call [eax+0x10]
    mov ecx, [eax+0x18]
    test ch, 1
    je 0x585d7a
    jmp 0x585d64

;================================================================ preferowany wrog
; atak 0x73BC76 (esi = atakujacy): zamiast "jest tropicielem" - prog FAVORED_ENEMY
wrog_klasa:
    mov dword [esp+0x14], 0
    push esi
    push 4
    call zdolnosc
    cmp eax, -1
    je .oryg
    test eax, eax
    jle 0x73bcd9
    jmp 0x73bc91
.oryg:
    push 8
    lea ecx, [esi+0x20]
    call 0x40d7e0
    test eax, eax
    je 0x73bcd9
    jmp 0x73bc91

; 0x73BCD0: call 0x546860 (ranga wroga 1..8) -> ATTACK z DSWROG (oryginal: ranga)
wrog_atak:
    push dword [esp+8]
    push dword [esp+8]
    call 0x546860
    push 0
    push eax
    call wrog_wart
    ret 8

; obrazenia 0x73DD34 (ebp = atakujacy, [esp+0xfc] = cel): zamiast "tropiciel: +4" - DAMAGE z DSWROG
wrog_obr:
    push ebp
    push 4
    call zdolnosc
    cmp eax, -1
    je .oryg
    test eax, eax
    jle 0x73dd4d
    mov edx, [esp+0xfc]
    add edx, 6                  ; rasa celu
    lea eax, [ebp+0x5a4]
    push eax
    push edx
    mov ecx, [0x8cf6dc]
    mov ecx, [ecx+0x1c54]
    call 0x546860               ; ranga
    push 1
    push eax
    call wrog_wart
    add [esp+0x14], eax
    jmp 0x73dd4d
.oryg:
    push 8
    lea ecx, [ebp+0x20]
    call 0x40d7e0
    test eax, eax
    je 0x73dd4d
    add dword [esp+0x14], 4
    jmp 0x73dd4d

; wrog_wart(ranga, kolumna) -> eax (stdcall); bez tabeli: ATTACK = ranga, DAMAGE = 4
wrog_wart:
    push esi
    push edi
    mov esi, KPTR_WROG
    mov edi, nazwa_wrog
    call tabela2da
    mov ecx, [esp+0xc]
    dec ecx
    push dword [esp+0x10]
    push ecx
    call liczba
    cmp eax, -1
    jne .k
    mov eax, [esp+0xc]
    cmp dword [esp+0x10], 0
    je .k
    mov eax, 4
.k: pop edi
    pop esi
    ret 8
nazwa_wrog: db 'DSWROG', 0

;================================================================ aura paladyna (sojusznicy odporni na strach)
; 0x4A48CF i 0x6F8EF4: call 0x447990(7) z ecx = postac+0x920, gra sprawdza wynik >= 2 i odleglosc < 100.
; Tu: prog AURA_COURAGE z DSKLASY -> 2 (ma aure) albo 0.
aura:
    push ecx
    lea eax, [ecx-0x920]
    push eax
    push 5
    call zdolnosc
    pop ecx
    cmp eax, -1
    je 0x447990
    test eax, eax
    jle .z
    mov eax, 2
    ret 4
.z: xor eax, eax
    ret 4
