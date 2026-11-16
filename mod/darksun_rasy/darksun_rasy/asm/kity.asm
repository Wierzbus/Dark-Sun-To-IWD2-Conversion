; Podklasy (kity) Dark Sun - tabela podklas i cala obsluga podklas (test25, od test26 numery podklas w bajtach klas).
; Kod w sekcji .dsras pod 0xA26000, tabela 0xA23000 (do 255 wpisow), zmienne 0xA25000.
; Tabele wypelnia WeiDU (komponent 2) - pusta tabela = zachowanie oryginalnej gry.
; Etykiety z innych plikow (szukaj, wczytaj z rasy.asm; komorka, tabela2da z podklasy.asm) podaje nasm -D.
;
; Wpis tabeli KITY (32 B): +0 = 1 (wpis istnieje), +4 strref etykiety przycisku, +8 nazwa wiersza (ASCIIZ, do 15 znakow),
; +0x17 klasa (1..11), +0x18 nazwa tablicy CLAB (8 znakow, 0 = brak). Koniec tabeli: wpis z +0 = 0.
; Kolejnosc wpisow jednej klasy = kolejnosc przyciskow w oknie 52 / 12.
bits 32
org 0xA26000

; test26: numer podklasy zamiast bitu. Wpis tabeli nr k (0..254) ma wartosc kitu (k+1) << 24.
; Postac trzyma podklase DS kazdej klasy w bajcie naglowka CRE (plik 0x30C + klasa - 1 = postac +0x8A8 + klasa - 1):
; 0 = brak, k+1 = wpis k. Starszy bajt pola kitu (+0x80C) = "glowna" podklasa DS (z kreatora; kaplan ma pierwszenstwo)
; - dla kodu gry, ktory zna tylko pole kitu (GetClassRow, domeny, maski Gotowe).
KITY      equ 0xA23000          ; 255 wpisow po 32 B + wpis konczacy (0xA24FE0)
N_KITY    equ 255
NOK2      equ 0xA25000          ; 12 x strref etykiety "bez podklasy" wg klasy
HELP2     equ 0xA25040          ; 255 x strref opisu podklasy
DLPTR     equ 0xA25440          ; 255 x wskaznik listy domen
SLPTR     equ 0xA25840          ; 255 x wskaznik listy czarow
DFLG      equ 0xA25C40          ; 255 B flag list domen
SFLG      equ 0xA25D40          ; 255 B flag list czarow
DPAR      equ 0xA25E40
SPAR      equ 0xA25E48
PR_WIECEJ equ 0xA25F00          ; strref napisu przycisku 2 "wiecej klas prestizowych" (komponent 2, test40)
PR_STRONA equ 0xA25F04          ; klas prestizowych na stronie okna 6 (1..8, przyciski 3..10; 0 = 8) - komponent 2 / 7
BAJTY     equ 0x8A8             ; bajt podklasy klasy 1 w postaci (plik CRE 0x30C)
KPTR_PROG equ 0xA22F14
INV19     equ 0x286BCA1B

;================================================================ wejscia o stalych adresach (dla rasy.asm i WeiDU)
    db 'DSKITY02'               ; 0xA26000: znacznik ukladu
k_wpis_we:    jmp near kit_wpis     ; 0xA26008
k_wiersz_we:  jmp near kit_wiersz   ; 0xA2600D
k_clab_we:    jmp near clab2        ; 0xA26012
k_synt_we:    jmp near kit_synt     ; 0xA26017
k_kol_we:     jmp near kol_kitu     ; 0xA2601C
k_progp_we:   jmp near prog_p       ; 0xA26021

;================================================================ wyszukiwanie w tabeli
; kit_wpis: eax = kit (starszy bajt = numer wpisu + 1), cl = klasa -> edx = wpis tej klasy albo 0
kit_wpis:
    mov edx, eax
    shr edx, 24
    jz .r
    dec edx
    shl edx, 5
    add edx, KITY
    cmp dword [edx], 0
    je .brak
    cmp cl, [edx+0x17]
    je .r
.brak:
    xor edx, edx
.r: ret

; wartosc: edx = wpis -> eax = wartosc kitu (nr + 1) << 24
wartosc:
    mov eax, edx
    sub eax, KITY
    shr eax, 5
    inc eax
    shl eax, 24
    ret

; kit_synt(postac, klasa, kit) -> eax = kit ze starszym bajtem = podklasa DS tej klasy (bajt postaci), stdcall
kit_synt:
    mov eax, [esp+0xc]
    mov ecx, [esp+8]
    dec ecx
    cmp ecx, 10
    ja .k
    mov edx, [esp+4]
    test edx, edx
    jz .k
    movzx edx, byte [edx+BAJTY+ecx]
    test edx, edx
    jz .k
    and eax, 0x00ffffff
    shl edx, 24
    or eax, edx
.k: ret 12

; ustaw_bajty(postac): bajty klas = podklasa ze starszego bajtu kitu (kreator: jedna klasa). stdcall, zachowuje rejestry i flagi
ustaw_bajty:
    pushfd
    push eax
    push ecx
    push edx
    push edi
    mov edi, [esp+0x18]
    xor eax, eax
    mov [edi+BAJTY], eax
    mov [edi+BAJTY+4], eax
    mov [edi+BAJTY+8], ax
    mov [edi+BAJTY+10], al
    mov eax, [edi+0x80c]
    shr eax, 24
    jz .k
    lea edx, [eax-1]
    shl edx, 5
    movzx ecx, byte [KITY+edx+0x17]
    dec ecx
    cmp ecx, 10
    ja .k
    mov [edi+BAJTY+ecx], al
.k: pop edi
    pop edx
    pop ecx
    pop eax
    popfd
    ret 4

; kit_nty: cl = klasa, eax = n -> edx = n-ty wpis tej klasy (od 0) albo 0
kit_nty:
    push eax
    mov edx, KITY
.p: cmp dword [edx], 0
    je .brak
    cmp cl, [edx+0x17]
    jne .n
    test eax, eax
    jz .r
    dec eax
.n: add edx, 32
    jmp .p
.brak:
    xor edx, edx
.r: pop eax
    ret

; kit_nr: edx = wpis -> eax = numer wpisu wsrod wpisow tej samej klasy
kit_nr:
    push ecx
    push esi
    mov cl, [edx+0x17]
    xor eax, eax
    mov esi, KITY
.p: cmp esi, edx
    jae .k
    cmp cl, [esi+0x17]
    jne .n
    inc eax
.n: add esi, 32
    jmp .p
.k: pop esi
    pop ecx
    ret

;================================================================ GetClassRow 0x541DA0 (wynik, klasa, kit), ret 0xC
klasa_wiersz2:
    mov eax, [esp+0xc]
    test eax, 0xff000000
    jz .oryg
    mov cl, [esp+8]
    call kit_wpis
    test edx, edx
    jz .oryg
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

;================================================================ GetClabTable 0x546030 (klasa, kit), thiscall, ret 8
clab2:
    mov eax, [esp+8]
    test eax, 0xff000000
    jz .oryg
    push ecx
    push edx
    mov cl, [esp+0xc]
    call kit_wpis
    test edx, edx
    jz .nie
    cmp byte [edx+0x18], 0
    je .nie
    lea eax, [edx+0x18]
    push eax
    call wczytaj
    test eax, eax
    jz .nie
    pop edx
    pop ecx
    ret 8
.nie:
    pop edx
    pop ecx
.oryg:
    mov eax, [esp+4]
    and eax, 0xff
    jmp 0x546039

; kit_wiersz(tabela, klasa, kit) -> eax = wiersz podklasy w tabeli albo -1. stdcall (dla rasy.asm: progresja)
; podklasa DS tej klasy: nazwa z tabeli; inne kity: nazwa z GetClassRow(klasa, kit).
kit_wiersz:
    push ebp
    mov ebp, esp
    push ecx
    push edx
    mov eax, [ebp+0x10]
    test eax, 0xff000000
    jz .wan
    mov cl, [ebp+0xc]
    call kit_wpis
    test edx, edx
    jz .wan
    lea eax, [edx+8]
    push 0
    push eax
    push dword [ebp+8]
    call szukaj
    jmp .k
.wan:
    sub esp, 4
    push dword [ebp+0x10]
    push dword [ebp+0xc]
    lea eax, [esp+8]
    push eax
    mov ecx, [0x8cf6dc]
    mov ecx, [ecx+0x1c54]
    call 0x541da0               ; GetClassRow(&wynik, klasa, kit)
    push 0
    push dword [esp+4]
    push dword [ebp+8]
    call szukaj
    push eax
    lea ecx, [esp+4]
    call 0x7fcc1a               ; ~CString
    pop eax
    add esp, 4
.k: pop edx
    pop ecx
    pop ebp
    ret 12

;================================================================ przyciski okien (esi = okno)
; napis_id(id, strref): tekst przycisku z TLK i wlaczenie przycisku. stdcall, zachowuje rejestry poza eax
napis_id:
    push ebx
    push ecx
    push edx
    push dword [esp+0x10]
    mov ecx, esi
    call 0x4d2ca0               ; GetControl
    test eax, eax
    jz .k
    mov ebx, eax
    sub esp, 4                  ; CString
    mov eax, esp
    push dword [esp+0x18]       ; strref
    push eax
    call 0x427b60               ; CString z TLK (cdecl: cel, strref)
    add esp, 8
    mov ecx, ebx
    mov edx, [ecx]
    push eax
    call [edx+0x74]             ; SetText
    mov ecx, esp
    call 0x7fcc1a               ; ~CString
    add esp, 4
    push 1
    mov ecx, ebx
    call 0x4d57c0               ; SetActive(1)
.k: pop edx
    pop ecx
    pop ebx
    ret 8

; zaznacz_id(id, stan): SetSelected przycisku. stdcall, zachowuje rejestry poza eax
zaznacz_id:
    push ecx
    push edx
    push dword [esp+0xc]
    mov ecx, esi
    call 0x4d2ca0
    test eax, eax
    jz .k
    push dword [esp+0x10]
    mov ecx, eax
    call 0x4d5ae0               ; SetSelected
.k: pop edx
    pop ecx
    ret 8

; dodaj_kity(klasa, pierwszy id) -> eax = liczba podklas tej klasy wpisanych na przyciski (id .. 10). stdcall
dodaj_kity:
    push ebx
    push ecx
    push edx
    xor ebx, ebx
.p: mov ecx, [esp+0x10]
    mov eax, ebx
    call kit_nty
    test edx, edx
    jz .k
    mov eax, [esp+0x14]
    add eax, ebx
    cmp eax, 10
    ja .k
    push dword [edx+4]
    push eax
    call napis_id
    inc ebx
    jmp .p
.k: mov eax, ebx
    pop edx
    pop ecx
    pop ebx
    ret 8

;================================================================ klikniecie klasy w oknie 2 (0x61C09E: jmp [ecx*4+0x61C1A8],
; ecx = id - 2 = klasa - 1): klasa z podklasami DS (poza kaplanem, czarodziejem, paladynem i mnichem, ktore maja
; wlasne okna) otwiera okno 52; bez podklas - jak w oryginale (bez okna).
okno_klasy:
    push eax
    push edx
    push ecx
    lea eax, [ecx+1]
    cmp eax, 3
    je .gra
    cmp eax, 6
    je .gra
    cmp eax, 7
    je .gra
    cmp eax, 11
    je .gra
    mov cl, al
    xor eax, eax
    call kit_nty
    test edx, edx
    pop ecx
    pop edx
    pop eax
    jz .oryg
    jmp 0x61c0a5                ; okno 52
.gra:
    pop ecx
    pop edx
    pop eax
.oryg:
    jmp [ecx*4+0x61c1a8]

;================================================================ okno 52 (aktualizacja 0x60D280: esi = okno, [esp+0x6c] = postac)
; 0x60D6C3 (eax = klasa - 6): mnich i paladyn jak w oryginale, inne klasy: 1 = bez podklasy, 2.. = podklasy klasy
okno52:
    test eax, eax
    je 0x60d758                 ; mnich
    cmp eax, 1
    je 0x60d6d0                 ; paladyn
    add eax, 6
    push eax
    push 2
    push eax
    call dodaj_kity
    pop ecx
    test eax, eax
    jz .bez
    and ecx, 0xff
    cmp ecx, 11
    ja .bez
    push dword [NOK2+4*ecx]
    push 1
    call napis_id
.bez:
    jmp 0x60d7fb

; 0x60D753 (paladyn, zamiast jmp 0x60D7DB): podklasy DS paladyna od przycisku 4
paladyn52:
    push ecx                    ; CString do zniszczenia w 0x60D7DB
    push 4
    push 7
    call dodaj_kity
    pop ecx
    jmp 0x60d7db

; 0x60D7D2 (mnich, zamiast mov byte [esp+0x60], 3): podklasy DS mnicha od przycisku 4
mnich52:
    mov byte [esp+0x60], 3
    push 4
    push 6
    call dodaj_kity
    lea ecx, [esp+0x40]
    jmp 0x60d7db

; 0x60D871 (zaznaczenie wybranego przycisku): podklasa DS -> jej przycisk; brak podklasy -> przycisk 1
podswietl:
    mov eax, [esp+0x6c]
    movzx ecx, byte [eax+0x3e3e]
    mov eax, [esp+0x44]         ; kit postaci
    test eax, 0xff000000
    jz .zero
    call kit_wpis
    test edx, edx
    jz .zero
    call kit_nr
    add eax, 2
    cmp ecx, 6
    je .pm
    cmp ecx, 7
    jne .ok
.pm:
    add eax, 2
.ok:
    push 1
    push eax
    call zaznacz_id
    jmp 0x60d8a1
.zero:
    cmp dword [esp+0x44], 0
    jne .oryg
    cmp ecx, 6
    je .oryg
    cmp ecx, 7
    je .oryg
    xor eax, eax
    call kit_nty
    test edx, edx
    jz .oryg
    push 1
    push 1
    call zaznacz_id
    jmp 0x60d8a1
.oryg:
    mov edx, [esp+0x44]
    lea eax, [edx-1]
    jmp 0x60d878

; 0x621DBE klikniecie w oknie 52 (call, zamiast mov [edx+0x80C], eax; esi = przycisk, klasa [esp+0x18])
; paladyn / mnich: przyciski 1-3 jak w grze, 4.. podklasy DS; inne klasy: 1 = bez podklasy, 2.. podklasy
klik52:
    push ecx
    push edx
    push ebx
    mov ebx, eax                ; wynik gry
    movzx ecx, byte [esp+0x24]  ; klasa
    mov eax, [esi+0xa]          ; id przycisku
    cmp ecx, 7
    je .pm
    cmp ecx, 6
    je .pm
    xor ebx, ebx
    sub eax, 2
    jb .zapisz
    call kit_nty
    test edx, edx
    jz .zapisz
    call wartosc
    mov ebx, eax
    jmp .zapisz
.pm:
    sub eax, 4
    jb .zapisz
    call kit_nty
    test edx, edx
    jz .zapisz
    call wartosc
    mov ebx, eax
.zapisz:
    mov eax, ebx
    pop ebx
    pop edx
    pop ecx
    mov [edx+0x80c], eax
    push edx
    call ustaw_bajty
    ret

; 0x615C50 przycisk Gotowe (call, zamiast mov ebp, [ebp+0x80C]; klasa [esp+0x28]):
; klasa z podklasami (poza paladynem i mnichem) moze nie miec podklasy (kit 0)
gotowe52:
    mov ebp, [ebp+0x80c]
    test ebp, ebp
    jnz .r
    cmp byte [esp+0x28], 7
    je .r
    cmp byte [esp+0x28], 6
    je .r
    push ecx
    push edx
    push eax
    movzx ecx, byte [esp+0x34]
    xor eax, eax
    call kit_nty
    test edx, edx
    pop eax
    pop edx
    pop ecx
    jz .r
    inc ebp
.r: ret

;================================================================ okno 12 (bostwa kaplana, szkoly czarodzieja)
; GetKit przycisku 0x61CCC0 (ecx = przycisk -> id, [esp+4] = klasa), ret 4. Przyciski od id 14 = podklasy DS.
; 0x61CD4A (kaplan, eax = id - 2, ecx = id)
getkit_k:
    cmp eax, 0xb
    jbe 0x61cd4f
    push 3
    jmp getkit_wsp
; 0x61CCCE (czarodziej)
getkit_m:
    cmp eax, 0xb
    jbe 0x61ccd3
    push 11
getkit_wsp:
    pop edx                     ; klasa
    cmp ecx, 14
    jb .zero
    lea eax, [ecx-14]
    mov ecx, edx
    call kit_nty
    test edx, edx
    jz .zero
    call wartosc
    ret 4
.zero:
    xor eax, eax
    ret 4

; petla12(klasa, kit): przyciski 14, 15, ... okna 12 = kolejne podklasy klasy; brak podklasy -> przycisk ukryty.
; esi = okno. stdcall
petla12:
    push ebx
    push ecx
    push edx
    push edi
    xor ebx, ebx
.p: lea eax, [ebx+14]
    push eax
    mov ecx, esi
    call 0x4d2ca0               ; GetControl
    test eax, eax
    jz .k
    mov edi, eax
    mov ecx, [esp+0x14]
    mov eax, ebx
    call kit_nty
    test edx, edx
    jz .ukryj
    push edx
    call wartosc
    mov ecx, [esp+0x1c]
    and ecx, 0xff000000
    cmp eax, ecx
    sete al
    movzx eax, al
    push eax
    mov ecx, edi
    call 0x4d5ae0               ; SetSelected
    pop edx
    push dword [edx+4]
    lea eax, [ebx+14]
    push eax
    call napis_id
    jmp .n
.ukryj:
    push 0
    mov ecx, edi
    call 0x4d57c0               ; SetActive(0)
.n: inc ebx
    cmp ebx, 16
    jb .p
.k: pop edi
    pop edx
    pop ecx
    pop ebx
    ret 8

; 0x61012E koniec petli kaplana (zamiast cmp edi, 0xD; jle 0x610041): po id 13 przyciski podklas
petla_k:
    cmp edi, 0xd
    jle 0x610041
    mov eax, [esp+0x34]         ; postac
    push dword [eax+0x80c]
    push 3
    call petla12
    jmp 0x610137

; 0x61001B koniec petli czarodzieja (zamiast jmp 0x610152)
petla_m:
    mov eax, [esp+0x34]
    push dword [eax+0x80c]
    push 11
    call petla12
    jmp 0x610152

; 0x61D031 opis po kliknieciu w oknie 12, nieznany bit (eax = bit, klasa [esp+0x1C]) -> HELP2 podklasy
pomoc12:
    movzx ecx, byte [esp+0x1c]
    call kit_wpis
    test edx, edx
    jz .a
    sub edx, KITY
    shr edx, 5
    mov eax, [HELP2+edx*4]
    jmp 0x61d062
.a: push 0
    push 0x8a636c
    jmp 0x61d038

;================================================================ zapis podklasy w kreatorze: bajty klas postaci
; 0x61BF5D klikniecie klasy w oknie 2 (call, zamiast mov [eax+0x80C], edi): kit 0 i wyzerowane bajty
klasa_zeruj:
    mov [eax+0x80c], edi
    push eax
    call ustaw_bajty
    ret
; 0x61CF0E klikniecie w oknie 12 (call, zamiast mov [edx+0x80C], ecx; flagi z cmp przed zapisem musza zostac)
zapisz12:
    mov [edx+0x80c], ecx
    push edx
    call ustaw_bajty
    ret
; 0x722D9C procedura CLAB (call zamiast call 0x728570 = kit postaci, ecx = postac, klasa = [esp+0xAEC]):
; kit ze starszym bajtem = podklasa DS tej klasy (bajt postaci)
kit_722:
    push ecx
    call 0x728570
    pop ecx
    push eax
    push dword [esp+0xaf0]
    push ecx
    call kit_synt
    ret

;================================================================ GetClassRow z kitem postaci: podklasa DS tej klasy z bajtu klasy
; (wymagania ABCLASRQ przy awansie i w kreatorze, odpornosci CLSSRSMD, opis KITLIST) - zamiast starszego bajtu kitu
; 0x5D96DB (awans, zamiast mov edi, [edi+0x80C]; edi = postac, klasa [esp+0x24]; eax musi zostac)
abclas_aw:
    push eax
    push ecx
    push edx
    push dword [edi+0x80c]
    movzx eax, byte [esp+0x34]
    push eax
    push edi
    call kit_synt
    mov edi, eax
    pop edx
    pop ecx
    pop eax
    ret
; 0x60BEFD (kreator, zamiast mov edi, [edi+0x80C]; edi = postac, ebx = klasa; eax musi zostac)
abclas_kr:
    push eax
    push ecx
    push edx
    push dword [edi+0x80c]
    movzx eax, bl
    push eax
    push edi
    call kit_synt
    mov edi, eax
    pop edx
    pop ecx
    pop eax
    ret
; 0x611EDE (odpornosci, zamiast call 0x728570; ecx = postac, klasa [esp+0x28])
clss_kit:
    push ecx
    call 0x728570
    pop ecx
    push eax
    movzx eax, byte [esp+0x2c]
    push eax
    push ecx
    call kit_synt
    ret
; 0x62193F (opis KITLIST, zamiast mov esi, [esi+0x80C]; esi = postac, klasa [esp+0x18])
klist_kit:
    push dword [esi+0x80c]
    movzx eax, byte [esp+0x1c]
    push eax
    push esi
    call kit_synt
    mov esi, eax
    ret

;================================================================ czary klas prestizowych (test34)
; DSPREST.2DA kolumna SPELLCLASS (klasa 2..11): kazdy poziom klasy prestizowej liczy sie jak poziom tej klasy przy
; miejscach na czary (MXSPLxxx, 0x5431E0) i przy najwyzszym kregu czarow kaplana / druida przy awansie (0x71EB3B).
CTX_R     equ 0xA22F18          ; postac z ostatniego liczenia rzutow / PW (rasy.asm)

; pr_spellcl(wpis) -> eax = SPELLCLASS podklasy z DSPREST.2DA (0 gdy brak). stdcall, zachowuje rejestry poza eax
pr_spellcl:
    push ecx
    push edx
    push esi
    mov edx, [esp+0x10]
    push edx
    push n_prest
    call wczytaj
    pop edx
    test eax, eax
    jz .zero
    cmp word [eax+0x22], 0
    jle .zero
    mov esi, eax
    push 0
    lea ecx, [edx+8]
    push ecx
    push esi
    call szukaj
    cmp eax, -1
    je .zero
    push n_spellcl
    push eax
    push esi
    call pr_wart
    jmp .k
.zero:
    xor eax, eax
.k: pop esi
    pop edx
    pop ecx
    ret 4

; ekran_wpis: ebx = ekran awansu -> edx = wpis klasy prestizowej wybranej w oknie 6 (starszy bajt [+0x846], klasa 1)
; albo z kopii naglowka postaci sprzed awansu ([+0x85A] + 0x304 = bajt klasy 1), albo 0
ekran_wpis:
    mov edx, [ebx+0x846]
    shr edx, 24
    jz .kopia
    dec edx
    shl edx, 5
    add edx, KITY
    cmp byte [edx+0x17], KL_PREST
    je .k
.kopia:
    mov edx, [ebx+0x85a]
    test edx, edx
    jz .zero
    movzx edx, byte [edx+0x304]
    test edx, edx
    jz .zero
    dec edx
    shl edx, 5
    add edx, KITY
    ret
.zero:
    xor edx, edx
.k: ret

; pr_czar(statystyki, klasa) -> eax = poziomy klasy prestizowej doliczane do tej klasy (0 gdy brak). stdcall
pr_czar:
    push ebx
    push ecx
    push edx
    push esi
    push edi
    mov esi, [esp+0x18]         ; statystyki (poziom klasy k pod +0x46 + k)
    xor edi, edi
    test esi, esi
    jz .k
    movzx edi, byte [esi+0x46+KL_PREST]
    test edi, edi
    jz .k
    xor edx, edx
    ; postac: statystyki w postaci (+0x920 / +0x1778)
    lea ebx, [esi-0x920]
    cmp dword [ebx], 0x85bdd4
    je .post
    lea ebx, [esi-0x1778]
    cmp dword [ebx], 0x85bdd4
    je .post
    ; kopia statystyk ekranu awansu ([ekran+0x85E]) - bajt klasy z kopii naglowka
    mov ebx, [0x8cf6dc]
    mov ebx, [ebx+0x1c60]
    test ebx, ebx
    jz .ctx
    cmp esi, [ebx+0x85e]
    jne .ctx
    call ekran_wpis
    jmp .wpis
.ctx:
    mov ebx, [CTX_R]
    test ebx, ebx
    jz .ekran
    cmp dword [ebx], 0x85bdd4
    jne .ekran
.post:
    movzx edx, byte [ebx+BAJTY+KL_PREST-1]
    test edx, edx
    jz .ekran
    dec edx
    shl edx, 5
    add edx, KITY
    jmp .wpis
.ekran:                         ; awans na 1. poziom klasy prestizowej: bajt jeszcze pusty - wybor z okna 6
    mov ebx, [0x8cf6dc]
    mov ebx, [ebx+0x1c60]
    test ebx, ebx
    jz .zero
    call ekran_wpis
.wpis:
    test edx, edx
    jz .zero
    push edx
    call pr_spellcl
    cmp eax, [esp+0x1c]         ; klasa
    je .k
.zero:
    xor edi, edi
.k: mov eax, edi
    pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    ret 8

; wirt(ekran) -> eax = klasa awansu dla okien czarow: [+0x106], a dla klasy prestizowej z SPELLCLASS 2 / 10 (bard,
; zaklinacz) - ta klasa (okno 8: wybor znanych czarow). stdcall, zachowuje rejestry poza eax
wirt:
    push ebx
    push ecx
    push edx
    mov ebx, [esp+0x10]
    movzx eax, byte [ebx+0x106]
    cmp eax, KL_PREST
    jne .k
    call ekran_wpis
    test edx, edx
    jz .p
    push edx
    call pr_spellcl
    cmp eax, 2
    je .k
    cmp eax, 10
    je .k
.p: mov eax, KL_PREST
.k: mov [KL_WIRT], al
    pop edx
    pop ecx
    pop ebx
    ret 4

; okno 8 (wybor znanych czarow barda / zaklinacza) - klasa z wirt zamiast [ekran+0x106]
; 0x5E126C (czy pokazac okno 8; esi = ekran)
kw_a:
    push eax
    push esi
    call wirt
    mov cl, al
    pop eax
    mov edx, KL_WIRT
    cmp cl, 2
    jmp 0x5e127b
; 0x5D99C9 (aktualizacja okna 8; ebp = ekran)
kw_b:
    push ebp
    call wirt
    mov eax, KL_WIRT
    mov [esp+0x18], eax
    mov al, [eax]
    jmp 0x5d99d5
; 0x5D9F04
kw_c:
    push ebp
    call wirt
    jmp 0x5d9f0a
; 0x5DA005 (edx = ekran)
kw_d:
    push edx
    call wirt
    jmp 0x5da00d
; 0x5E57F6 (zatwierdzenie awansu: znane czary barda / zaklinacza; esi = ekran)
kw_e:
    push esi
    call wirt
    mov edi, KL_WIRT
    jmp 0x5e5802
; 0x5EC067 (call; esi = ekran) -> cl = klasa
kw_f:
    push eax
    push esi
    call wirt
    mov cl, al
    pop eax
    ret

; zamiast "call 0x447990" (poziom klasy, thiscall ecx = statystyki, [esp+4] = klasa) w miejscach liczenia czarow
cz_lvl:
    push ecx
    push dword [esp+8]
    call 0x447990
    pop ecx
    push eax
    push dword [esp+8]
    push ecx
    call pr_czar
    pop ecx
    add eax, ecx
    ret 4

; zamiast "call 0x447950" (suma poziomow klas z maski, [esp+4] = maska): kaplan (4) i druid (8)
cz_maska:
    push ecx
    push dword [esp+8]
    call 0x447950
    pop ecx
    push eax
    mov eax, [esp+8]
    bsf eax, eax
    inc eax                     ; klasa = bit + 1
    push eax
    push ecx
    call pr_czar
    pop ecx
    add eax, ecx
    ret 4

;================================================================ klasy prestizowe: slot 1 (dawny barbarzynca), test30
; DSPREST.2DA: wiersz = nazwa podklasy klasy 1, kolumny LEVEL (poziom postaci), BAB (suma premii do ataku klas),
; CLASS (klasa 1..11) i CLASS_LEVEL (jej poziom), SUBCLASS (nazwa wiersza podklasy DS, ktora postac musi miec, * = dowolna).
; Wartosc 0 / * = bez warunku. Charakter - wiersz podklasy w ALIGNMNT (0x544A60).
KL_PREST  equ 1

; pr_wart(tabela, wiersz, nazwa kolumny) -> eax = liczba (0 gdy brak / *). stdcall
pr_wart:
    push ecx
    push edx
    push 1
    push dword [esp+0x18]
    push dword [esp+0x14]
    call szukaj
    cmp eax, -1
    je .zero
    push eax
    push dword [esp+0x14]
    mov eax, [esp+0x14]
    call komorka
    test eax, eax
    jz .zero
    push eax
    call 0x7e7b03               ; atoi
    add esp, 4
    jmp .k
.zero:
    xor eax, eax
.k: pop edx
    pop ecx
    ret 12

; kit_nazwa(char*) -> edx = wpis tabeli o tej nazwie albo 0. Zachowuje rejestry poza edx.
kit_nazwa:
    push eax
    push ecx
    mov edx, KITY
.p: cmp dword [edx], 0
    je .brak
    push edx
    lea eax, [edx+8]
    push eax
    push dword [esp+0x14]
    call 0x7e7a54               ; stricmp (cdecl)
    add esp, 8
    pop edx
    test eax, eax
    jz .k
    add edx, 32
    jmp .p
.brak:
    xor edx, edx
.k: pop ecx
    pop eax
    ret 4

; pr_bab(postac) -> eax = suma premii do ataku klas postaci (tablice BAB klas / podklas, lv_wart z rasy.asm). stdcall
pr_bab:
    push ebx
    push ecx
    push edx
    push esi
    mov ebx, [esp+0x14]
    xor esi, esi
    mov dword [lv_kl], 1
.p: mov eax, [lv_kl]
    movzx eax, byte [ebx+0x626+eax]
    test eax, eax
    jz .n
    mov [lv_poz], eax
    push 1
    call lv_wart
    test eax, eax
    jle .n
    add esi, eax
.n: inc dword [lv_kl]
    cmp dword [lv_kl], 11
    jbe .p
    mov eax, esi
    pop esi
    pop edx
    pop ecx
    pop ebx
    ret 4

; pr_wpis(wpis, postac) -> eax = 1 gdy postac spelnia warunki DSPREST.2DA i charakter (ALIGNMNT) podklasy. stdcall
pr_wpis:
    push ebx
    push ecx
    push edx
    push esi
    push edi
    mov esi, [esp+0x18]         ; wpis
    mov ebx, [esp+0x1c]         ; postac
    push n_prest
    call wczytaj
    test eax, eax
    jz .war_ok
    cmp word [eax+0x22], 0
    jle .war_ok
    mov edi, eax
    push 0
    lea eax, [esi+8]
    push eax
    push edi
    call szukaj
    cmp eax, -1
    je .war_ok
    mov [pr_w], eax
    ; poziom postaci
    push n_level
    push dword [pr_w]
    push edi
    call pr_wart
    test eax, eax
    jle .bab
    movzx ecx, byte [ebx+0x966]
    cmp ecx, eax
    jl .nie
.bab:
    push n_bab
    push dword [pr_w]
    push edi
    call pr_wart
    test eax, eax
    jle .kl
    push eax
    push ebx
    call pr_bab
    pop ecx
    cmp eax, ecx
    jl .nie
.kl:
    push n_class
    push dword [pr_w]
    push edi
    call pr_wart
    dec eax
    cmp eax, 10
    ja .pod
    mov [pr_k], eax
    push n_clevel
    push dword [pr_w]
    push edi
    call pr_wart
    mov ecx, [pr_k]
    movzx ecx, byte [ebx+0x627+ecx]
    cmp ecx, eax
    jl .nie
    test ecx, ecx
    jz .nie
.pod:
    ; test33: rasa, atuty, rangi umiejetnosci, poziom czarow tajemnych
    push n_race
    push dword [pr_w]
    push edi
    call pr_wart
    test eax, eax
    jle .atuty
    cmp [ebx+0x26], al          ; rasa (RACE.IDS 1..7)
    jne .nie
.atuty:
    mov dword [pr_k], 0
.at:
    mov eax, [pr_k]
    push dword [n_featy+eax*4]
    push dword [pr_w]
    push edi
    call pr_wart
    test eax, eax
    jle .atn
    push eax
    mov ecx, ebx
    call 0x763150               ; postac ma atut (FEATS.IDS)?
    test eax, eax
    jz .nie
.atn:
    inc dword [pr_k]
    cmp dword [pr_k], 3
    jb .at
    mov dword [pr_k], 0
.um:
    mov eax, [pr_k]
    push dword [n_rangi+eax*4]
    push dword [pr_w]
    push edi
    call pr_wart
    test eax, eax
    jle .umn
    push eax                    ; ranga
    mov eax, [pr_k]
    push dword [n_umiej+eax*4]
    push dword [pr_w]
    push edi
    call pr_wart                ; umiejetnosc (SKILLS.IDS 0..15)
    pop ecx
    cmp eax, 15
    ja .nie
    movzx eax, byte [ebx+0x7b4+eax]
    cmp eax, ecx
    jl .nie
.umn:
    inc dword [pr_k]
    cmp dword [pr_k], 2
    jb .um
    push n_arcane
    push dword [pr_w]
    push edi
    call pr_wart
    test eax, eax
    jle .pod2
    movzx ecx, byte [ebx+0x626+2]   ; bard
    movzx edx, byte [ebx+0x626+10]  ; zaklinacz
    add ecx, edx
    movzx edx, byte [ebx+0x626+11]  ; czarodziej
    add ecx, edx
    cmp ecx, eax
    jl .nie
.pod2:
    push 1
    push n_subclass
    push edi
    call szukaj
    cmp eax, -1
    je .war_ok
    push eax
    push dword [pr_w]
    mov eax, edi
    call komorka
    test eax, eax
    jz .war_ok
    cmp byte [eax], '*'
    je .war_ok
    push eax
    call kit_nazwa
    test edx, edx
    jz .nie
    movzx ecx, byte [edx+0x17]
    dec ecx
    cmp ecx, 10
    ja .nie
    mov eax, edx
    sub eax, KITY
    shr eax, 5
    inc eax
    movzx ecx, byte [ebx+BAJTY+ecx]
    cmp ecx, eax
    jne .nie
.war_ok:                        ; charakter: ALIGNMNT, wiersz podklasy
    mov edx, esi
    call wartosc                ; eax = (nr + 1) << 24
    push eax
    movzx eax, byte [ebx+0x3e4b]
    push eax
    push KL_PREST
    mov ecx, [0x8cf6dc]
    mov ecx, [ecx+0x1c54]
    call 0x544a60
    test eax, eax
    setnz al
    movzx eax, al
    jmp .k
.nie:
    xor eax, eax
.k: pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    ret 8

; pr_dost(postac) -> eax = 1 gdy postac moze wziac klase 1: ma juz jej poziomy albo spelnia warunki ktorejs podklasy
pr_dost:
    push ecx
    push edx
    mov ecx, [esp+0xc]
    movzx eax, byte [ecx+0x626+KL_PREST]
    test eax, eax
    jz .szukaj
    push eax                    ; ma juz klase prestizowa: awans do MAX_LEVEL
    push ecx
    call pr_max
    pop ecx
    cmp ecx, eax
    jl .tak
    jmp .nie
.szukaj:
    xor eax, eax
.p: push eax
    mov ecx, KL_PREST
    call kit_nty
    pop eax
    test edx, edx
    jz .nie
    push eax
    push dword [esp+0x10]
    push edx
    call pr_wpis
    test eax, eax
    pop eax
    jnz .tak
    inc eax
    jmp .p
.tak:
    mov eax, 1
    jmp .k
.nie:
    xor eax, eax
.k: pop edx
    pop ecx
    ret 4

; pr_max(postac) -> eax = najwyzszy poziom klasy prestizowej postaci (DSPREST.2DA kolumna MAX_LEVEL; 0 / brak = 10)
pr_max:
    push ecx
    push edx
    mov ecx, [esp+0xc]
    movzx edx, byte [ecx+BAJTY+KL_PREST-1]
    test edx, edx
    jz .dom
    dec edx
    shl edx, 5
    add edx, KITY
    push edx
    push n_prest
    call wczytaj
    pop edx
    test eax, eax
    jz .dom
    cmp word [eax+0x22], 0
    jle .dom
    push eax
    push 0
    lea ecx, [edx+8]
    push ecx
    push eax
    call szukaj
    pop ecx                     ; tabela
    cmp eax, -1
    je .dom
    push n_maxlev
    push eax
    push ecx
    call pr_wart
    test eax, eax
    jg .k
.dom:
    mov eax, 10
.k: pop edx
    pop ecx
    ret 4

; 0x5E8DB8 okno 54 ekranu awansu (wybor klasy): zamiast "mov esi, eax; neg esi; sbb esi, esi; neg esi"
; [esp+0x10] = klasa przycisku, [esp+0xE94] = postac. Klasa 1: aktywna wedlug pr_dost (charakter barbarzyncy nie liczy sie).
prest54:
    mov dword [pr_str], 0
    mov esi, eax
    neg esi
    sbb esi, esi
    neg esi
    cmp byte [esp+0x10], KL_PREST
    jne .k
    push dword [esp+0xe94]
    call pr_dost
    mov esi, eax
.k: test esi, esi
    jmp 0x5e8dc0

;================================================================ okno 6 klasy 1: strony po 8 klas prestizowych (test40)
; Na liscie tylko klasy prestizowe, ktorych warunki postac spelnia (pr_wpis); przyciski 3..10 = pozycje
; pr_str .. pr_str + 7; przycisk 2 (u innych klas "bez podklasy") = nastepna strona, gdy klas jest wiecej niz 8.
pr_str:     dd 0                ; pierwsza pozycja strony
pr_post:    dd 0                ; postac z ostatniego odswiezenia okna 6

; prest_nty: eax = n -> edx = wpis n-tej (od 0) klasy prestizowej dostepnej dla [pr_post] albo 0. Zachowuje eax, ecx.
prest_nty:
    push eax
    push ecx
    push ebx
    mov ebx, eax                ; ile jeszcze pominac
    xor ecx, ecx
.p: push ecx
    mov eax, ecx
    mov ecx, KL_PREST
    call kit_nty
    pop ecx
    test edx, edx
    jz .k
    push ecx
    push edx
    push dword [pr_post]
    push edx
    call pr_wpis
    pop edx
    pop ecx
    test eax, eax
    jz .n
    test ebx, ebx
    jz .k
    dec ebx
.n: inc ecx
    jmp .p
.k: pop ebx
    pop ecx
    pop eax
    ret

; pr_ns: -> eax = liczba klas prestizowych na stronie (1..8)
pr_ns:
    mov eax, [PR_STRONA]
    test eax, eax
    jz .d
    cmp eax, 8
    jbe .k
.d: mov eax, 8
.k: ret

; prest_ile: -> eax = liczba klas prestizowych dostepnych dla [pr_post]
prest_ile:
    push edx
    xor eax, eax
.p: call prest_nty
    test edx, edx
    jz .k
    inc eax
    jmp .p
.k: pop edx
    ret

; prest_lista(postac): esi = okno, ebp = wybrany wpis + 1 albo 0. stdcall
prest_lista:
    push ecx
    push edx
    push edi
    mov eax, [esp+0x10]
    mov [pr_post], eax
    call prest_ile
    mov edi, eax                ; m
    mov eax, [pr_str]
    cmp eax, edi
    jb .str_ok
    mov dword [pr_str], 0
.str_ok:
    xor ecx, ecx                ; j
.p: cmp ecx, 8
    jae .wiecej
    call pr_ns
    cmp ecx, eax
    jae .pusty
    mov eax, [pr_str]
    add eax, ecx
    call prest_nty
    lea eax, [ecx+3]            ; id
    test edx, edx
    jz .ukryj
    push eax
    push dword [edx+4]
    push eax
    call napis_id
    call wartosc
    shr eax, 24
    cmp eax, ebp
    sete al
    movzx eax, al
    pop edx                     ; id
    push eax
    push edx
    call zaznacz_id
    jmp .n
.pusty:
    lea eax, [ecx+3]
.ukryj:
    push eax
    call ukryj_id
.n: inc ecx
    jmp .p
.wiecej:
    call pr_ns
    cmp edi, eax
    jbe .bez
    push dword [PR_WIECEJ]
    push 2
    call napis_id
    push 0
    push 2
    call zaznacz_id
    jmp .k
.bez:
    push 2
    call ukryj_id
.k: pop edi
    pop edx
    pop ecx
    ret 4

; 0x5ED780 klikniecie przycisku okna 6 (ebx = przycisk, edi = ekran awansu; zamiast "mov ecx, ebx; call 0x5ED5A0"):
; klasa 1, przycisk 2 -> nastepna strona (bez zmiany wyboru), potem odswiezenie okna (0x5ED94E)
klik6:
    cmp byte [edi+0x106], KL_PREST
    jne .oryg
    cmp dword [ebx+0xa], 2
    jne .oryg
    call pr_ns
    add [pr_str], eax
    jmp 0x5ed94e
.oryg:
    mov ecx, ebx
    call 0x5ed5a0
    jmp 0x5ed787

; 0x7647C2 kara PD za wieloklasowosc (petla po klasach, esi = klasa): klasa 1 (prestizowa) nie liczy sie
xp_kara:
    cmp esi, KL_PREST
    je 0x7647ec
    cmp esi, [esp+0x18]
    je 0x7647ec
    jmp 0x7647c8
; 0x764764 (najwyzsza klasa do kary PD): klasa 1 pomijana
xp_najw:
    cmp esi, KL_PREST
    je 0x764794
    cmp esi, ebp
    je 0x764794
    push esi
    mov ecx, ebx
    jmp 0x76476b
;================================================================ atuty barbarzyncy (test39)
; Warunki atutow (0x763200, switch po atucie, esi = postac) sprawdzaly poziom klasy 1 (dawny barbarzynca), teraz
; klasy prestizowej. Barbarzynca = podklasa wojownika BARBARIAN_F (bajt podklasy wojownika, wpis o tej nazwie wiersza).
; czy_barb: esi = postac -> eax = 1 gdy postac ma poziomy wojownika z podklasa BARBARIAN_F. Zachowuje rejestry poza eax.
czy_barb:
    push edx
    xor eax, eax
    cmp byte [esi+0x626+5], 0
    je .k
    movzx edx, byte [esi+BAJTY+5-1]
    test edx, edx
    jz .k
    dec edx
    shl edx, 5
    add edx, KITY
    cmp dword [edx+8], 'BARB'
    jne .k
    cmp dword [edx+12], 'ARIA'
    jne .k
    cmp dword [edx+16], 'N_F'
    jne .k
    inc eax
.k: pop edx
    ret
; 0x76345B Extra Rage (atut 20; oryginal: klasa 1 >= 1)
at_szal:
    call czy_barb
    test eax, eax
    jz 0x7638fd
    jmp 0x763468
; 0x76355D Heroic Inspiration (atut 29; oryginal: barbarzynca, bard albo mnich >= 1)
at_heroic:
    call czy_barb
    test eax, eax
    jnz 0x763580
    mov eax, 1
    jmp 0x76356c

; 0x76479A (zamiast "push edi; mov ecx, ebx; call 0x447990"): edi = najwyzsza klasa poza ulubiona i prestizowa.
; Gdy innych klas brak (np. gladiator + klasa prestizowa), edi = 0 - gra wolala 0x447990(0) (asercja
; CDerivedStats.cpp 2070). Wtedy bez kary PD.
xp_zero:
    test edi, edi
    jz 0x7647ab
    push edi
    mov ecx, ebx
    call 0x447990
    jmp 0x7647a2

;================================================================ szal barbarzyncy bez klasy 1 (test31)
; Exe liczyl zmeczenie po szale i Greater Rage z poziomu klasy 1 (barbarzynca). Teraz z DSKLASY: wiersz 6 GREATER_RAGE
; (od tego poziomu klasy szal = Greater Rage, oryginal 15), wiersz 7 TIRELESS_RAGE (bez zmeczenia, oryginal 20);
; kolumna klasy albo podklasy (np. BARBARIAN_F). Bez tych wierszy w DSKLASY - zachowanie oryginalne (klasa 1).
W_GREATER equ 6
W_TIRELESS equ 7

; zdol(wiersz, postac) -> eax = 1 gdy ktoras klasa postaci (poziom ze statystyk +0x920) osiaga prog z DSKLASY,
; 0 gdy nie, -1 gdy brak wiersza / tabeli. stdcall, zachowuje rejestry poza eax.
zdol:
    push ebx
    push ecx
    push edx
    push esi
    xor esi, esi
    mov ebx, 1
.p: push dword [esp+0x18]       ; postac
    push ebx
    push dword [esp+0x1c]       ; wiersz
    call prog_p
    cmp eax, -1
    je .k
    test eax, eax
    jle .n
    mov edx, eax
    push ebx
    mov ecx, [esp+0x1c]
    add ecx, 0x920
    call 0x447990               ; poziom klasy
    cmp eax, edx
    jl .n
    mov esi, 1
.n: inc ebx
    cmp ebx, 11
    jle .p
    mov eax, esi
.k: pop esi
    pop edx
    pop ecx
    pop ebx
    ret 8

; 0x4A5C71 zmeczenie po szale (ebx = postac): bez zmeczenia, gdy TIRELESS_RAGE; oryginal: klasa 1 >= 20
szal_zmecz:
    push ebx
    push W_TIRELESS
    call zdol
    cmp eax, -1
    je .oryg
    test eax, eax
    jg 0x4a5d90
    jmp 0x4a5c87
.oryg:
    push 1
    lea ecx, [ebx+0x920]
    call 0x447990
    cmp eax, 0x14
    jge 0x4a5d90
    jmp 0x4a5c87

; 0x71E66F atut Extra Rage (esi = postac, ebx = stare statystyki): dodatkowe uzycia Greater Rage (SPIN260) albo szalu
; (SPIN236). Z tabela: Greater Rage, gdy GREATER_RAGE; oryginal: klasa 1 >= 15 teraz i < 15 wczesniej
szal_atut:
    push esi
    push W_GREATER
    call zdol
    cmp eax, -1
    je .oryg
    test eax, eax
    jg 0x71e68f
    jmp 0x71e69b
.oryg:
    push 1
    lea ecx, [esi+0x920]
    call 0x447990
    cmp eax, 0xf
    jl 0x71e69b
    push 1
    mov ecx, ebx
    call 0x447990
    cmp eax, 0xf
    jge 0x71e69b
    jmp 0x71e68f

; 0x5E5B1A awans (ebp = postac): zamiana szalu na Greater Rage. Z tabela: gdy GREATER_RAGE; oryginal: klasa 1 >= 15
szal_awans:
    push ebp
    push W_GREATER
    call zdol
    cmp eax, -1
    je .oryg
    test eax, eax
    jle 0x5e6154
    jmp 0x5e5b30
.oryg:
    push 1
    lea ecx, [ebp+0x920]
    call 0x447990
    cmp eax, 0xf
    jl 0x5e6154
    jmp 0x5e5b30

;================================================================ kolumny podklas w tabelach klas (test29)
; kol_kitu(tabela, klasa, postac) -> eax = indeks kolumny o nazwie podklasy DS tej klasy (nazwa wiersza wpisu, np.
; BARBARIAN_F) albo -1 (brak podklasy / kolumny). stdcall, zachowuje ecx i edx.
kol_kitu:
    push ecx
    push edx
    mov eax, [esp+0xc]
    test eax, eax
    jz .nie
    mov edx, [esp+0x14]
    test edx, edx
    jz .nie
    push dword [edx+0x80c]
    push dword [esp+0x14]
    push edx
    call kit_synt
    mov ecx, [esp+0x10]
    call kit_wpis
    test edx, edx
    jz .nie
    push 1
    lea eax, [edx+8]
    push eax
    push dword [esp+0x14]
    call szukaj
    jmp .k
.nie:
    or eax, -1
.k: pop edx
    pop ecx
    ret 12

; prog_p(wiersz, klasa, postac) -> eax = prog zdolnosci z DSKLASY: kolumna podklasy postaci, a bez niej klasy (prog_kl).
; stdcall, zachowuje ecx i edx. Wywoluja unik i zdolnosc z podklasy.asm (stale wejscie 0xA26021).
prog_p:
    push ecx
    push edx
    call tab_klasy
    test eax, eax
    jz .zw
    push eax
    push dword [esp+0x18]
    push dword [esp+0x18]
    push dword [esp+8]
    call kol_kitu
    pop ecx
    cmp eax, -1
    je .zw
    push eax
    push dword [esp+0x10]
    mov eax, ecx
    call liczba
    jmp .k
.zw:
    push dword [esp+0x10]
    push dword [esp+0x10]
    call prog_kl
.k: pop edx
    pop ecx
    ret 12

; 0x763D26 (liczba atutow przy awansie, FEATCLAS; zamiast "lea ecx, [ebp-1]; dec edx; cmp ecx, eax"):
; ebp = klasa, edi = postac, esi = reguly, eax = liczba kolumn, edx = poziom klasy -> ecx = kolumna (podklasy albo klasy)
featclas:
    lea ecx, [ebp-1]
    dec edx
    push eax
    push edx
    push edi
    push ebp
    lea eax, [esi+0xd30]
    push eax
    call kol_kitu
    test eax, eax
    jl .k
    mov ecx, eax
.k: pop edx
    pop eax
    cmp ecx, eax
    ret

; 0x763DBA (punkty umiejetnosci, SKILLPTS; zamiast "lea eax, [ecx-1]; cmp eax, edx"): ecx = klasa, ebx = postac,
; esi = reguly, edx = liczba kolumn -> eax = kolumna (podklasy albo klasy)
skillpts:
    push ecx
    push edx
    push ebx
    push ecx
    lea edx, [esi+0xd9c]
    push edx
    call kol_kitu
    pop edx
    pop ecx
    test eax, eax
    jge .k
    lea eax, [ecx-1]
.k: cmp eax, edx
    ret

;================================================================ nazwa klasy z podklasa (0x544120, karta postaci, portrety, awans)
; 0x5442A7 (zamiast "and ebx, 0xff; lea eax, [ebx-1]"): ebx = klasa, ebp = kit, na stosie ebx z 0x5441FA.
; Podklasa DS tej klasy (starszy bajt kitu) -> esi = strref nazwy podklasy (+4 wpisu), dalej jak gra (0x54446E).
nazwa_kl:
    and ebx, 0xff
    push ecx
    push edx
    mov eax, ebp
    mov cl, bl
    call kit_wpis
    test edx, edx
    jz .nie
    mov eax, [edx+4]
    test eax, eax
    jle .nie
    mov esi, eax
    pop edx
    pop ecx
    pop ebx
    jmp 0x54446E
.nie:
    pop edx
    pop ecx
    lea eax, [ebx-1]
    jmp 0x5442B0

; 0x5DCB31 karta postaci, sekcja Levels (zamiast "push ecx; mov ecx, [esp+0x24]"): ecx = kit, edx = klasa,
; ebx = postac -> kit z podklasa DS tej klasy (bajt klasy), wiec kazda klasa wieloklasowca ma swoja nazwe.
karta_kl:
    push edx
    push ecx
    push edx
    push ebx
    call kit_synt
    pop edx
    push eax
    mov ecx, [esp+0x24]
    jmp 0x5DCB36

;================================================================ ekran awansu (obiekt gry +0x1C60, GUIREC.CHU), okno 6 = wybor podklasy
; ukryj_id(id): SetActive(0) przycisku okna esi. stdcall, zachowuje rejestry poza eax
ukryj_id:
    push ecx
    push edx
    push dword [esp+0xc]
    mov ecx, esi
    call 0x4d2ca0
    test eax, eax
    jz .k
    push 0
    mov ecx, eax
    call 0x4d57c0
.k: pop edx
    pop ecx
    ret 4

; wybor_awans: ebx = ekran awansu -> eax = numer wpisu + 1 wybranej podklasy DS tej klasy albo 0
wybor_awans:
    push ecx
    push edx
    mov eax, [ebx+0x846]
    shr eax, 24
    jz .k
    lea edx, [eax-1]
    shl edx, 5
    mov cl, [ebx+0x106]
    cmp cl, [KITY+edx+0x17]
    je .k
    xor eax, eax
.k: pop edx
    pop ecx
    ret

; 0x5E1020 (czy pokazac okno 6; esi = ekran): gra - tylko czarodziej, mnich, paladyn, kaplan na 1. poziomie klasy;
; dodatkowo kazda inna klasa, ktora ma podklasy DS w tabeli (tez tylko nowa klasa)
okno6_czy:
    mov al, [esi+0x106]
    cmp al, 0xb
    je 0x5e103a
    cmp al, 6
    je 0x5e103a
    cmp al, 7
    je 0x5e103a
    cmp al, 3
    je 0x5e103a
    movzx ecx, al
    xor eax, eax
    call kit_nty
    test edx, edx
    jz 0x5e189f
    mov eax, ecx
    jmp 0x5e103a

; 0x5DA8EB (petla przyciskow okna 6, galaz poza czarodziejem i kaplanem): inne klasy niz paladyn i mnich -> przycisk ukryty
inne6:
    mov al, [ebx+0x106]
    cmp al, 7
    je .o
    cmp al, 6
    je .o
    jmp 0x5da9cd
.o: cmp edi, 4
    jg 0x5da9cd
    jmp 0x5da8f4

; 0x5DA9FB (po petli okna 6; ebx = ekran, [esp+0x24] = okno): przyciski podklas DS
; paladyn, mnich: od id 5; czarodziej, kaplan: id 14, 15 (dopisane do GUIREC.CHU); inne: 2 = bez podklasy, 3.. podklasy
okno6_po:
    push esi
    push edi
    push ebp
    mov esi, [esp+0x30]         ; okno
    movzx edi, byte [ebx+0x106] ; klasa
    call wybor_awans
    mov ebp, eax                ; wybrany wpis + 1 albo 0
    cmp edi, KL_PREST
    jne .niep
    push dword [esp+0x50]       ; postac (1. argument 0x5DA6E0)
    call prest_lista
    jmp .k
.niep:
    cmp edi, 7
    je .pm
    cmp edi, 6
    je .pm
    cmp edi, 11
    je .kw
    cmp edi, 3
    je .kw
    cmp edi, 11
    ja .k
    push dword [NOK2+edi*4]
    push 2
    call napis_id
    xor eax, eax
    test ebp, ebp
    sete al
    push eax
    push 2
    call zaznacz_id
    push 3
    jmp .lista
.pm:
    push 5
    jmp .lista
.kw:
    push 14
.lista:                         ; [esp] = pierwszy id
    xor ecx, ecx                ; n
.p: push ecx
    mov eax, ecx
    mov ecx, edi
    call kit_nty
    pop ecx
    test edx, edx
    jz .reszta
    mov eax, [esp]
    add eax, ecx                ; id
    cmp dword [esp], 14
    je .ok
    cmp eax, 10
    ja .reszta
.ok:
    push eax
    push dword [edx+4]
    push eax
    call napis_id
    call wartosc                ; eax = (nr + 1) << 24
    shr eax, 24
    cmp eax, ebp
    sete al
    movzx eax, al
    pop edx                     ; id
    push eax
    push edx
    call zaznacz_id
    inc ecx
    jmp .p
.reszta:                        ; ukryj nieuzyte przyciski 14, 15 (sa w oknie dla kazdej klasy)
    mov eax, [esp]
    cmp eax, 14
    jne .uk
    add eax, ecx
    jmp .uk2
.uk:
    mov eax, 14
.uk2:
    cmp eax, 15
    ja .po
    push eax
    push eax
    call ukryj_id
    pop eax
    inc eax
    jmp .uk2
.po:
    add esp, 4
.k: pop ebp
    pop edi
    pop esi
    mov ecx, [esp+0x24]
    push 0
    jmp 0x5daa01

; 0x5ED5A0 GetKit przycisku okna 6 (ecx = przycisk, klasa z ekranu awansu), ret
getkit6:
    push ecx
    push edx
    mov eax, [0x8cf6dc]
    mov edx, [eax+0x1c60]
    movzx edx, byte [edx+0x106]
    mov ecx, [ecx+0xa]          ; id
    cmp edx, KL_PREST
    jne .niep
    sub ecx, 3
    jb .zero                    ; id 2 = nastepna strona
    add ecx, [pr_str]
    mov eax, ecx
    call prest_nty
    test edx, edx
    jz .zero
    call wartosc
    pop edx
    pop ecx
    ret
.niep:
    cmp edx, 7
    je .pm
    cmp edx, 6
    je .pm
    cmp edx, 11
    je .kw
    cmp edx, 3
    je .kw
    sub ecx, 3
    jb .zero                    ; id 2 = bez podklasy
    jmp .szukaj
.pm:
    sub ecx, 5
    jb .oryg
    jmp .szukaj
.kw:
    sub ecx, 14
    jb .oryg
.szukaj:
    mov eax, ecx
    mov ecx, edx
    call kit_nty
    test edx, edx
    jz .zero
    call wartosc
    pop edx
    pop ecx
    ret
.zero:
    xor eax, eax
    pop edx
    pop ecx
    ret
.oryg:
    pop edx
    pop ecx
    mov eax, [0x8cf6dc]
    jmp 0x5ed5a5

; 0x5ED913 opis po kliknieciu w oknie 6, nieznany kit (eax = kit albo -1 dla 0; edi = ekran awansu)
pomoc6:
    cmp eax, -1
    je .brak
    mov edx, eax
    shr edx, 24
    jz .a
    dec edx
    mov eax, [HELP2+edx*4]
    jmp 0x5ed93d
.brak:
    movzx edx, byte [edi+0x106]
    cmp edx, 11
    ja .a
    mov eax, [NOK2+edx*4]
    jmp 0x5ed93d
.a: push 0
    push 0x8a636c
    jmp 0x5ed91a

; 0x5E2089 Gotowe okna 6 (esi = ekran -> esi = 1 gotowe): podklasa DS tej klasy wybrana albo klasa bez podklas gry
gotowe6:
    push ebx
    mov ebx, esi
    call wybor_awans
    pop ebx
    test eax, eax
    jnz .tak
    mov cl, [esi+0x106]
    cmp cl, KL_PREST
    je .o
    cmp cl, 0xb
    je .o
    cmp cl, 7
    je .o
    cmp cl, 6
    je .o
    cmp cl, 3
    je .o
.tak:
    mov esi, 1
    jmp 0x5e2177
.o: xor eax, eax
    jmp 0x5e2091

; 0x5E2E39 zatwierdzenie okna 6 (ebp = ekran, [esp+0x10] = postac): kit = stary | nowy (bez starszego bajtu nowego);
; wybrana podklasa DS nowej klasy -> bajt klasy postaci; starszy bajt kitu: stary, a gdy pusty albo podklasa kaplana - nowy
kit_awans:
    push ebx
    push edx
    push esi
    push edi
    mov ebx, ebp
    call wybor_awans
    mov esi, eax                ; nr + 1 albo 0
    mov edi, [esp+0x20]         ; postac
    movzx ecx, byte [ebp+0x106]
    dec ecx
    cmp ecx, 10
    ja .kit
    mov edx, esi
    mov [edi+BAJTY+ecx], dl     ; bajt klasy (0 = bez podklasy DS)
.kit:
    mov eax, [ebp+0x846]
    and eax, 0x00ffffff
    or eax, [ebp+0x77c]
    test esi, esi
    jz .zapisz
    mov edx, [ebp+0x77c]
    shr edx, 24
    jz .nowy
    cmp byte [ebp+0x106], 3
    jne .zapisz
.nowy:
    and eax, 0x00ffffff
    mov edx, esi
    shl edx, 24
    or eax, edx
.zapisz:
    mov [edi+0x80c], eax
    pop edi
    pop esi
    pop edx
    pop ebx
    jmp 0x5e2e51

;================================================================ listy czarow i domen podklas (test23, test24)
; lista_kitu(nr wpisu, opis) -> eax = obiekt listy czarow albo 0 (brak konfiguracji). stdcall.
; Lista budowana raz: wiersz podklasy w DSKLPROG, kolumna opis+0 = nazwa kolumny poziomow w tabeli opis+4, nazwy czarow
; z kolumny opis+8; wskaznik obiektu (0x4C B, operator new) pod opis+12 + 4*nr, flaga opis+16 + nr, parametry opis+20.
lista_kitu:
    push ebx
    push esi
    push edi
    push ebp
    mov ebx, [esp+0x14]
    mov ebp, [esp+0x18]
    cmp ebx, N_KITY
    jae .zero
    mov edx, [ebp+16]
    cmp byte [edx+ebx], 0
    jne .gotowe
    mov byte [edx+ebx], 1
    mov esi, KPTR_PROG
    mov edi, n_prog
    call tabela2da
    test eax, eax
    jz .gotowe
    cmp word [eax+0x22], 0
    jle .gotowe
    mov esi, eax                ; DSKLPROG
    mov eax, ebx
    shl eax, 5
    add eax, KITY+8             ; nazwa wiersza podklasy
    push 0
    push eax
    push esi
    call szukaj
    cmp eax, -1
    je .gotowe
    push eax                    ; wiersz
    push 1
    push dword [ebp]
    push esi
    call szukaj
    pop ecx
    cmp eax, -1
    je .gotowe
    push eax
    push ecx
    mov eax, esi
    call komorka                ; char* nazwy kolumny poziomow
    test eax, eax
    jz .gotowe
    cmp byte [eax], '*'
    je .gotowe
    cmp byte [eax], 0
    je .gotowe
    push eax                    ; nazwa kolumny (zachowana)
    push dword [ebp+4]
    call wczytaj                ; LISTSPLL / LISTDOMN
    pop ecx
    test eax, eax
    jz .gotowe
    mov esi, eax
    push 1
    push ecx
    push esi
    call szukaj
    cmp eax, -1
    je .gotowe
    mov edx, [ebp+20]
    mov [edx], eax              ; kolumna poziomu
    push 1
    push dword [ebp+8]
    push esi
    call szukaj
    cmp eax, -1
    je .gotowe
    mov edx, [ebp+20]
    mov [edx+4], eax            ; kolumna nazw czarow
    push 0x4c
    call 0x7fc95b               ; operator new
    add esp, 4
    test eax, eax
    jz .gotowe
    mov edi, eax
    mov edx, [ebp+12]
    mov [edx+ebx*4], edi
    mov ecx, edi
    call 0x59eb60               ; konstruktor listy
    mov edx, [ebp+20]
    push 0                      ; bez listy kontrolnej
    lea eax, [edx+4]
    push eax                    ; &kolumna nazw
    push edx                    ; &kolumna poziomu
    push esi                    ; tabela
    mov ecx, edi
    call 0x5ca2a0               ; budowa listy (ret 0x10)
    mov edx, [ebp+16]
    mov byte [edx+ebx], 2
.gotowe:
    mov edx, [ebp+16]
    xor eax, eax
    cmp byte [edx+ebx], 2
    jne .k
    mov edx, [ebp+12]
    mov eax, [edx+ebx*4]
    jmp .k
.zero:
    xor eax, eax
.k: pop ebp
    pop edi
    pop esi
    pop ebx
    ret 8

; ---- domeny bostw (test23), hak 0x5CA910: GetDomainIndex(&kit), thiscall (ecx = reguly), ret 4.
; Gra liczy adres listy: reguly + 0x4E2C + idx*0x4C; dla podklasy DS kaplana zwracamy idx naszej listy (mod 2^32).
domena:
    mov eax, [esp+4]
    mov eax, [eax]
    test eax, 0xff000000
    jnz .ds
    jmp 0x5ca916
.ds:
    push ebx
    push ebp
    mov ebp, ecx                ; reguly
    mov cl, 3
    call kit_wpis
    test edx, edx
    jz .inna
    mov ebx, edx
    sub ebx, KITY
    shr ebx, 5
    push opis_dom
    push ebx
    call lista_kitu
    test eax, eax
    jz .k                       ; brak konfiguracji: domeny 1. bostwa (bez asercji)
    sub eax, ebp
    sub eax, 0x4e2c
    shr eax, 2
    imul eax, eax, INV19
.k: pop ebp
    pop ebx
    ret 4
.inna:                          ; bit podklasy innej klasy (wieloklasowa postac): bostwo z bitow gry
    pop ebp
    pop ebx
    mov eax, [esp+4]
    mov eax, [eax]
    and eax, 0xff8000
    jmp 0x5ca916

; ---- listy czarow klas (test24): miejsca liczace adres listy klasy (reguly + 0x4C18 + idx*0x4C) z 0x5CA5D0(&klasa).
lk_esp1c:
    mov eax, [esp+0x1c]
    jmp lista_klasy
lk_esp60:
    mov eax, [esp+0x60]
    jmp lista_klasy
lk_esp70:
    mov eax, [esp+0x70]
    jmp lista_klasy
lk_esp90:
    mov eax, [esp+0x90]
    jmp lista_klasy
lk_esp94:
    mov eax, [esp+0x94]
    jmp lista_klasy
lk_espa4:
    mov eax, [esp+0xa4]
    jmp lista_klasy
lk_ebp:
    mov eax, ebp
; lista_klasy: eax = postac (sprawdzamy vtable CGameSprite), ecx = reguly, [esp+4] = &klasa
lista_klasy:
    push ebx
    push esi
    push ebp
    mov ebp, ecx
    mov esi, eax
    push dword [esp+0x10]
    call 0x5ca5d0               ; indeks listy klasy (oryginal)
    mov ebx, eax
    cmp esi, 0x10000
    jb .k
    cmp dword [esi], 0x85bdd4   ; CGameSprite
    jne .k
    mov ecx, [esp+0x10]
    movzx ecx, byte [ecx]
    push dword [esi+0x80c]
    push ecx
    push esi
    call kit_synt               ; podklasa DS tej klasy z bajtu postaci
    test eax, 0xff000000
    jz .k
    mov ecx, [esp+0x10]
    mov cl, [ecx]
    call kit_wpis
    test edx, edx
    jz .k
    sub edx, KITY
    shr edx, 5
    push opis_spl
    push edx
    call lista_kitu
    test eax, eax
    jz .k
    sub eax, ebp
    sub eax, 0x4c18
    shr eax, 2
    imul ebx, eax, INV19
.k: mov eax, ebx
    pop ebp
    pop esi
    pop ebx
    ret 4

; ---- poziom czaru dla klasy: zamiast call 0x5CAC30(resref*, klasa, kit) (stdcall, ret 0xC; 9 = brak).
; Gdy czaru nie ma na liscie klasy (ani domeny), szukamy go na listach podklas DS tej klasy.
poziom_czaru:
    push dword [esp+0xc]
    push dword [esp+0xc]
    push dword [esp+0xc]
    call 0x5cac30
    cmp eax, 9
    jb .k
    push ebx
    push esi
    push edi
    push ebp
    mov ecx, [0x8cf6dc]
    mov ecx, [ecx+0x1c54]
    mov edx, [esp+0x14]         ; resref czaru
    mov esi, [ecx+0x4bf8]       ; tablica czarow gry (8 B na czar)
    mov edi, [ecx+0x4bfc]
    xor ebp, ebp
.s: cmp ebp, edi
    jae .nie
    mov eax, [esi+ebp*8]
    cmp eax, [edx]
    jne .sn
    mov eax, [esi+ebp*8+4]
    cmp eax, [edx+4]
    je .zn
.sn:inc ebp
    jmp .s
.zn:movzx ebx, byte [esp+0x18]  ; klasa
    xor edi, edi                ; numer wpisu
.kit:
    cmp edi, N_KITY
    jae .nie
    mov eax, edi
    shl eax, 5
    cmp dword [KITY+eax], 0
    je .nie
    movzx ecx, byte [KITY+eax+0x17]
    cmp ecx, ebx
    jne .kn
    push opis_spl
    push edi
    call lista_kitu
    test eax, eax
    jz .kn
    xor ecx, ecx                ; poziom 0..8
.l: mov esi, [eax+ecx*8]
    mov edx, [eax+ecx*8+4]
    test esi, esi
    jz .ln
.e: test edx, edx
    jz .ln
    cmp [esi], ebp
    je .jest
    add esi, 8
    dec edx
    jmp .e
.ln:inc ecx
    cmp ecx, 9
    jb .l
.kn:inc edi
    jmp .kit
.jest:
    mov eax, ecx
    jmp .w
.nie:
    mov eax, 9
.w: pop ebp
    pop edi
    pop esi
    pop ebx
.k: ret 0xc

;================================================================ dane
n_prest:    db 'DSPREST', 0
n_level:    db 'LEVEL', 0
n_bab:      db 'BAB', 0
n_class:    db 'CLASS', 0
n_clevel:   db 'CLASS_LEVEL', 0
n_subclass: db 'SUBCLASS', 0
n_maxlev:   db 'MAX_LEVEL', 0
n_race:     db 'RACE', 0
n_feat1:    db 'FEAT1', 0
n_feat2:    db 'FEAT2', 0
n_feat3:    db 'FEAT3', 0
n_skill1:   db 'SKILL1', 0
n_skill2:   db 'SKILL2', 0
n_rank1:    db 'RANK1', 0
n_rank2:    db 'RANK2', 0
n_arcane:   db 'ARCANE', 0
n_spellcl:  db 'SPELLCLASS', 0
align 4
n_featy:    dd n_feat1, n_feat2, n_feat3
n_umiej:    dd n_skill1, n_skill2
n_rangi:    dd n_rank1, n_rank2
align 4
pr_w:       dd 0
pr_k:       dd 0
KL_WIRT:    db 0
align 4
align 4
opis_dom:   dd k_dom, n_listdomn, k_domres, DLPTR, DFLG, DPAR
opis_spl:   dd k_spells, n_listspll, k_splres, SLPTR, SFLG, SPAR
n_prog:     db 'DSKLPROG'       ; CResRef: 8 znakow
            db 0
k_dom:      db 'DOMAIN', 0
k_domres:   db 'DOMAIN_RESREF', 0
n_listdomn: db 'LISTDOMN', 0
k_spells:   db 'SPELLS', 0
k_splres:   db 'SPELL_RES_REF', 0
n_listspll: db 'LISTSPLL', 0
koniec_kity:
