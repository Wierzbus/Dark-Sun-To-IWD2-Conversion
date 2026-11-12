bits 32
org 0x440400
; skaluje wspolrzedne ekranu ladowania x1,8 (zamiast x2 w trybie podwojnym)
skaluj:
    push esi
    push ebx
    mov esi, tabela
.petla:
    mov ecx, [esi]
    test ecx, ecx
    jz .koniec
    mov eax, [ecx]
    lea eax, [eax+eax*8]
    add eax, 2
    cdq
    mov ebx, 5
    idiv ebx
    mov [ecx], eax
    add esi, 4
    jmp .petla
.koniec:
    pop ebx
    pop esi
    ret

; tlo ekranu ladowania rysowane na calym ekranie 1920x1080 od (0,0)
tlo:
    mov dword [esp+8], 0
    mov dword [esp+0xc], 0
    mov dword [esp+0x10], prostokat
    mov dword [esp+0x14], prostokat
    jmp 0x7b0c80

align 4
prostokat: dd 0, 0, 1920, 1080
tabela:
    dd 0x8a7ba8,0x8a7bac,0x8a7bb0,0x8a7bb4,0x8a7bb8,0x8a7bbc,0x8d0b7c,0x8d0770
    dd 0x8a7bc4,0x8a7bc0,0x8a7bc8,0x8a7bcc,0x8d0b80,0x8a7bd0,0x8a7bd4,0x8d0b8c
    dd 0x8a7bd8,0x8a7bdc,0x8a7be0,0x8d0b90,0x8d0ba0,0x8a7be4,0x8a7be8,0x8a7bec
    dd 0x8a7bf0,0x8a7bf4,0x8a7bf8,0x8a7bfc,0x8a7c00,0x8a7c04,0x8d0ba4,0x8a7c08
    dd 0x8a7c0c,0x8a7c10,0x8a7c14,0x8a7c18,0x8a7c1c,0x8a7c20,0x8a7c24,0x8a7c28
    dd 0x8a7c2c,0x8a7c30,0x8a7c34,0x8a7c38,0x8a7c3c
    dd 0
koniec_kodu:
