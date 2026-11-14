; Podklasy (kity) Dark Sun - tabela (bit, klasa) i cala obsluga podklas (test25).
; Kod w sekcji .dsras pod 0xA24000 (czwarta strona sekcji), tabela i zmienne na trzeciej stronie 0xA23000.
; Ten sam bit (0x01000000 ... 0x80000000) moze oznaczac rozne podklasy w roznych klasach: wpis wyszukuje sie po parze
; (bit, klasa). Tabele wypelnia WeiDU (komponent 2) - pusta tabela = zachowanie oryginalnej gry.
; Etykiety z innych plikow (szukaj, wczytaj z rasy.asm; komorka, tabela2da z podklasy.asm) podaje nasm -D.
;
; Wpis tabeli KITY (32 B): +0 bit, +4 strref etykiety przycisku, +8 nazwa wiersza (ASCIIZ, do 15 znakow),
; +0x17 klasa (1..11), +0x18 nazwa tablicy CLAB (8 znakow, 0 = brak). Koniec tabeli: wpis z bitem 0.
; Kolejnosc wpisow jednej klasy = kolejnosc przyciskow w oknie 52 / 12.
bits 32
org 0xA24000

KITY      equ 0xA23000          ; do 31 wpisow + wpis konczacy
N_KITY    equ 31
NOK2      equ 0xA235C0          ; 12 x strref etykiety "bez podklasy" (okno 52, przycisk 1) wg klasy
HELP2     equ 0xA23600          ; 32 x strref opisu podklasy (okno 12, po kliknieciu)
DLPTR     equ 0xA23680          ; 32 x wskaznik listy domen (test23)
SLPTR     equ 0xA23700          ; 32 x wskaznik listy czarow (test24)
DFLG      equ 0xA23780          ; 32 B: 0 = nie budowano, 1 = brak konfiguracji, 2 = gotowa
SFLG      equ 0xA237A0
DPAR      equ 0xA237C0          ; 2 dword: kolumna poziomu, kolumna nazwy czaru
SPAR      equ 0xA237C8
KPTR_PROG equ 0xA22F14          ; C2DArray DSKLPROG (wspolny z rasy.asm)
INV19     equ 0x286BCA1B        ; odwrotnosc 19 mod 2^32

;================================================================ wejscia o stalych adresach (dla rasy.asm i WeiDU)
    db 'DSKITY01'               ; 0xA24000: znacznik ukladu (WeiDU rozpoznaje po nim exe)
k_wpis_we:    jmp near kit_wpis     ; 0xA24008
k_wiersz_we:  jmp near kit_wiersz   ; 0xA2400D
k_clab_we:    jmp near clab2        ; 0xA24012

;================================================================ wyszukiwanie w tabeli
; kit_wpis: eax = kit (dword postaci), cl = klasa -> edx = wpis albo 0
kit_wpis:
    mov edx, KITY
.p: cmp dword [edx], 0
    je .brak
    test eax, [edx]
    jz .n
    cmp cl, [edx+0x17]
    je .r
.n: add edx, 32
    jmp .p
.brak:
    xor edx, edx
.r: ret

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
    mov ebx, [edx]
    jmp .zapisz
.pm:
    sub eax, 4
    jb .zapisz
    call kit_nty
    test edx, edx
    jz .zapisz
    mov ebx, [edx]
.zapisz:
    mov eax, ebx
    pop ebx
    pop edx
    pop ecx
    mov [edx+0x80c], eax
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
    mov eax, [edx]
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
    mov eax, [esp+0x1c]
    test eax, [edx]
    setnz al
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
    mov eax, [esi+0x80c]
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
