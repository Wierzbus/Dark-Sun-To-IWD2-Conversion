"""Latki exe zalezne od rozdzielczosci (dawne test10-test13 i poprawki z testow paczki 1), liczone z W x H.

Stale sprawdzone w grze dla 1920x1080 (r = H/1080 = 1):
  pole portretu P = 64 (z GUIW10 po skalowaniu), ramka zaznaczenia P-2, obraz P-4, nakladka HP P,
  ikona 48, przyciecie przycisku akcji 74, kolka kolorow x5/3, ekran ladowania x H/600.
Dla innych wysokosci wartosci rosna z r. Kazde miejsce jest najpierw sprawdzane (bajty oryginalu GOG 2.01).
"""
from __future__ import annotations

import os
import struct
import subprocess
import tempfile
from math import gcd
from pathlib import Path

BASE = 0x400000
ASM = Path(__file__).resolve().parents[2] / "asm" / "iwd2_ekran_ladowania.asm"
NOP = b"\x90"


def _i32(v: int) -> bytes:
    return struct.pack("<i", v)


def _imul32(modrm: int, k: int) -> bytes:          # imul r32, r/m32, imm32 (69 /r id)
    return bytes([0x69, modrm]) + _i32(k)


def _ladowanie(w: int, h: int) -> tuple[bytes, int]:
    """Kod z tools/asm/iwd2_ekran_ladowania.asm dla W x H; zwraca (kod, adres etykiety tlo)."""
    g = gcd(h, 600)
    num, den = h // g, 600 // g
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "k.bin")
        subprocess.run(["nasm", "-f", "bin", f"-DSZER={w}", f"-DWYS={h}", f"-DLICZ={num}", f"-DMIAN={den}",
                        "-o", out, str(ASM)], check=True)
        kod = Path(out).read_bytes()
    poz = kod.find(bytes.fromhex("c744240800000000"))            # tlo: mov dword [esp+8], 0
    if poz < 0 or len(kod) > 663:
        raise SystemExit("STOP: nieoczekiwany kod ekranu ladowania.")
    tlo = 0x440400 + poz
    return kod, tlo


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
