"""Latki exe zalezne od rozdzielczosci (dawne test10-test13 i poprawki z testow paczki 1), liczone z W x H.

Stale sprawdzone w grze dla 1920x1080 (r = H/1080 = 1):
  pole portretu P = 64 (z GUIW10 po skalowaniu), ramka zaznaczenia P-2, obraz P-4, nakladka HP P,
  ikona 48, przyciecie przycisku akcji 74, kolka kolorow x5/3, ekran ladowania x H/600.
Dla innych wysokosci wartosci rosna z r. Kazde miejsce jest najpierw sprawdzane (bajty oryginalu GOG 2.01).
"""
from __future__ import annotations

import struct
from math import gcd

BASE = 0x400000
NOP = b"\x90"


def _i32(v: int) -> bytes:
    return struct.pack("<i", v)


def _imul32(modrm: int, k: int) -> bytes:          # imul r32, r/m32, imm32 (69 /r id)
    return bytes([0x69, modrm]) + _i32(k)


TABELA_LAD = [0x8a7ba8, 0x8a7bac, 0x8a7bb0, 0x8a7bb4, 0x8a7bb8, 0x8a7bbc, 0x8d0b7c, 0x8d0770,
              0x8a7bc4, 0x8a7bc0, 0x8a7bc8, 0x8a7bcc, 0x8d0b80, 0x8a7bd0, 0x8a7bd4, 0x8d0b8c,
              0x8a7bd8, 0x8a7bdc, 0x8a7be0, 0x8d0b90, 0x8d0ba0, 0x8a7be4, 0x8a7be8, 0x8a7bec,
              0x8a7bf0, 0x8a7bf4, 0x8a7bf8, 0x8a7bfc, 0x8a7c00, 0x8a7c04, 0x8d0ba4, 0x8a7c08,
              0x8a7c0c, 0x8a7c10, 0x8a7c14, 0x8a7c18, 0x8a7c1c, 0x8a7c20, 0x8a7c24, 0x8a7c28,
              0x8a7c2c, 0x8a7c30, 0x8a7c34, 0x8a7c38, 0x8a7c3c]


def _ladowanie(w: int, h: int) -> tuple[bytes, int]:
    """Kod tools/asm/iwd2_ekran_ladowania.asm zakodowany w Pythonie (bez nasm), stale jako imm32.
    Zwraca (kod od 0x440400, adres etykiety tlo)."""
    g = gcd(h, 600)
    num, den = h // g, 600 // g
    org = 0x440400
    u32 = lambda v: struct.pack("<I", v & 0xFFFFFFFF)
    skaluj = bytearray()
    skaluj += b"\x56\x53"                                  # push esi; push ebx
    p_tab = len(skaluj) + 1
    skaluj += b"\xbe" + u32(0)                              # mov esi, tabela
    petla = len(skaluj)
    skaluj += b"\x8b\x0e\x85\xc9"                          # mov ecx,[esi]; test ecx,ecx
    p_jz = len(skaluj)
    skaluj += b"\x74\x00"                                  # jz .koniec
    skaluj += b"\x8b\x01"                                  # mov eax,[ecx]
    skaluj += b"\x69\xc0" + u32(num)                        # imul eax,eax,LICZ
    skaluj += b"\x05" + u32(den // 2)                       # add eax,MIAN/2
    skaluj += b"\x99"                                      # cdq
    skaluj += b"\xbb" + u32(den)                            # mov ebx,MIAN
    skaluj += b"\xf7\xfb\x89\x01\x83\xc6\x04"              # idiv ebx; mov [ecx],eax; add esi,4
    skaluj += b"\xeb" + bytes([(petla - (len(skaluj) + 2)) & 0xFF])   # jmp .petla
    koniec = len(skaluj)
    skaluj[p_jz + 1] = koniec - (p_jz + 2)
    skaluj += b"\x5b\x5e\xc3"                              # pop ebx; pop esi; ret
    tlo = len(skaluj)
    kod = skaluj + b"\xc7\x44\x24\x08" + u32(0) + b"\xc7\x44\x24\x0c" + u32(0)
    p_pr = len(kod)
    kod += b"\xc7\x44\x24\x10" + u32(0) + b"\xc7\x44\x24\x14" + u32(0)
    kod += b"\xe9" + u32(0x7B0C80 - (org + len(kod) + 5))    # jmp 0x7b0c80
    while len(kod) % 4:
        kod += b"\x90"
    prost = len(kod)
    kod += u32(0) + u32(0) + u32(w) + u32(h)
    tab = len(kod)
    kod += b"".join(u32(a) for a in TABELA_LAD) + u32(0)
    kod[p_tab:p_tab + 4] = u32(org + tab)
    kod[p_pr + 4:p_pr + 8] = u32(org + prost)
    kod[p_pr + 12:p_pr + 16] = u32(org + prost)
    if len(kod) > 663:
        raise SystemExit("STOP: kod ekranu ladowania za dlugi.")
    return bytes(kod), org + tlo


def latki(w: int, h: int, pole: int) -> list[tuple[int, bytes, bytes, str]]:
    """(VA, bajty oryginalu, nowe bajty, opis). pole = bok pola portretu na pasku swiata (GUIW10)."""
    r = h / 1080.0
    s = h / 600.0
    kolko = 5.0 / 3.0 * r
    ikona = round(48 * r)
    akcja = round(74 * r)
    L = []

    def add(va, stare, nowe, opis):
        stare, nowe = bytes.fromhex(stare) if isinstance(stare, str) else stare, bytes.fromhex(nowe) if isinstance(nowe, str) else nowe
        assert len(stare) == len(nowe), (hex(va), opis)
        L.append((va, stare, nowe, opis))

    # panel 800x600 -> W x H
    add(0x85DE3C, "20035802", struct.pack("<HH", w, h), f"panel {w}x{h}")
    # ikony 32 -> 48*r
    add(0x4E66C1, "20000000", struct.pack("<I", ikona), f"rozmiar ikony {ikona}")
    # przyciecie przycisku akcji: 38*eax -> akcja*eax
    add(0x595864, "8d0cc08d04488b0ed1e0", _imul32(0xC0, akcja) + bytes.fromhex("8b0e") + NOP * 2, f"przycisk akcji {akcja}")
    # kolka kolorow: wzor A  lea R1,[eax+eax*2] -> imul R1,eax,k (3 B), wzor B  7*n*3 -> imul R,ecx,K21 + nop
    k3 = round(3 * kolko)
    k21 = round(21 * kolko)
    for va, a_old, a_new in ((0x61E628, "8d0440", "6bc0"), (0x61EFDB, "8d0440", "6bc0"),
                             (0x63241F, "8d1440", "6bd0"), (0x632991, "8d1440", "6bd0")):
        add(va, a_old, a_new + f"{k3:02x}", f"kolka kolorow krok {2 * k3}")
    for va, reg in ((0x61E63D, "8d04cd000000002bc18d0440"), (0x61EFF0, "8d04cd000000002bc18d0440"),
                    (0x632430, "8d04cd000000002bc18d0c40"), (0x6329A2, "8d04cd000000002bc18d0c40")):
        dst = 0xC1 if reg.endswith("0440") else 0xC9                 # imul eax,ecx / imul ecx,ecx
        add(va, reg, _imul32(dst, k21) + NOP * 6, f"kolka kolorow odstep {2 * k21}")
    # portrety: ekrany druzyny (P), nakladka HP (P), ramka zaznaczenia (P-2), obraz (P-4)
    for va in (0x64FB35, 0x6659E5):
        add(va, "8d14dd000000002bd38d14528d1451", _imul32(0xD3, pole) + bytes.fromhex("01ca") + NOP * 7, f"portrety druzyny {pole}")
    for va in (0x64FB66, 0x665A16):
        add(va, "8d04d5000000002bc28d04408d1447", _imul32(0xC2, pole) + bytes.fromhex("8d1407") + NOP * 6, f"portrety druzyny {pole}")
    add(0x704F06, "8d04cd000000002bc18d0440d1e0", _imul32(0xC1, pole) + NOP * 8, f"nakladka HP {pole}")
    add(0x704F2B, "8d0cc5000000002bc88d0449d1e0", _imul32(0xC0, pole) + NOP * 8, f"nakladka HP {pole}")
    add(0x704EBE, "8d54ad008d445500", _imul32(0xC5, pole - 2) + NOP * 2, f"ramka zaznaczenia {pole - 2}")
    add(0x704ED0, "c1e002", NOP * 3, "ramka zaznaczenia (bez shl)")
    add(0x705053, "8d04ed000000002bc58d1c40d1e3", _imul32(0xDD, pole - 4) + NOP * 8, f"obraz portretu {pole - 4}")
    # ekran ladowania: kod skalujacy pozycje x H/600 i tlo na calym ekranie (funkcja 0x440400, 663 B)
    kod, tlo = _ladowanie(w, h)
    o = 0x440400 - BASE
    L.append((0x440400, None, kod.ljust(663, b"\xcc"), f"ekran ladowania x{h}/600 ({len(kod)} B)"))
    sw, sh = round(800 * s), round(600 * s)
    add(0x4414C7, "a13cde8500", "b820039090", "ekran ladowania: 800 (jak test13)")
    add(0x4414EF, "8b153ede8500", "ba5802909090", "ekran ladowania: 600 (jak test13)")
    add(0x441512, "a13cde8500", "b8" + struct.pack("<H", sw).hex() + "9090", f"ekran ladowania: {sw}")
    add(0x441537, "a13ede8500", "b8" + struct.pack("<H", sh).hex() + "9090", f"ekran ladowania: {sh}")
    add(0x441548, "8b153ede85008bf866a13cde8500",
        "ba" + struct.pack("<H", sh).hex() + "9090908bf866b8" + struct.pack("<H", sw).hex() + "9090", f"ekran ladowania: {sw}x{sh}")
    add(0x4416F5, "e886f53600", b"\xe8" + _i32(tlo - (0x4416F5 + 5)), "tlo ekranu ladowania od (0,0)")
    return L


def zastosuj(d: bytearray, orig: bytes, w: int, h: int, pole: int) -> list[str]:
    log = []
    for va, stare, nowe, opis in latki(w, h, pole):
        o = va - BASE
        if stare is None:
            stare = orig[o:o + len(nowe)]
        if bytes(d[o:o + len(stare)]) != stare:
            raise SystemExit(f"STOP: nieoczekiwane bajty pod {va:#x} ({opis}). Nic nie zapisano.")
        d[o:o + len(nowe)] = nowe
        log.append(f"{va:#x}: {opis}")
    return log
