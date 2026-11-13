; Galaz polelfa w GetRaceRow (0x541940, rasa 3): podrasa 0 -> "HALF_ELF", inna -> "HALF_ELF_DS"
; (napis w miejscu dawnego wywolania asercji). Dokladnie 56 B (0x541A42..0x541A7A).
bits 32
org 0x541a42
    mov  esi, [esp+0xc]         ; wynik (CString*)
    cmp  byte [esp+0x14], 0     ; podrasa
    jne  .ds
    push 0x8de964               ; globalny CString "HALF_ELF"
    mov  ecx, esi
    call 0x7fc98f               ; CString::CString(const CString&)
    jmp  short .done
.ds:
    push napis
    mov  ecx, esi
    call 0x7fcc88               ; CString::CString(LPCSTR)
.done:
    mov  eax, esi
    pop  esi
    pop  ecx
    ret  0xc
napis:
    db 'HALF_ELF_DS', 0
