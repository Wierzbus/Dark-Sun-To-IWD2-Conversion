; Galaz polorka w GetRaceRow (0x541940): podrasa 0 -> "HALF_ORC", podrasa 1 -> "HALF_ORC_MUL"
bits 32
org 0x541bc4
    mov  esi, [esp+0xc]         ; wynik (CString*)
    cmp  byte [esp+0x14], 0     ; podrasa
    jne  .mul
    push 0x8de8c4               ; globalny CString "HALF_ORC"
    mov  ecx, esi
    mov  eax, 0x7fc98f          ; CString::CString(const CString&)
    call eax
    jmp  short .done
.mul:
    push 0x542551               ; "HALF_ORC_MUL" w luce wypelnienia
    mov  ecx, esi
    mov  eax, 0x7fcc88          ; CString::CString(LPCSTR)
    call eax
.done:
    mov  eax, esi
    pop  esi
    pop  ecx
    ret  0xc
