"""Wlasna rozdzielczosc dla Icewind Dale II: lataka na KOPII IWD2.exe + pasujacy GUIW10.CHU.

Uzycie (Anaconda Prompt, z katalogu projektu):
    python tools\\hires_patch.py --iwd2-dir "D:\\Gry\\Icewind Dale 2" --width 1920 --height 1080

Co robi (analiza: out/upscale_analiza.md, 2026-11-09; BEZ testu w grze):
  1. Kopiuje IWD2.exe -> IWD2_<W>x<H>.exe (oryginal nietkniety) i w galezi trybu 1024 (VA 0x422198-0x4222e0)
     podmienia stale ukladu interfejsu na wartosci wyliczone z W i H. Kazda podmieniana stala jest najpierw
     sprawdzana (oryginalne bajty) - przy niezgodnosci skrypt sie zatrzymuje i nic nie zapisuje.
  2. Dla W > 1600 przekierowuje skok "ecx > 1600" prosto do tej galezi (inaczej tryby > 1600 trafialyby do galezi 2048).
  3. Z GUIW10.CHU (z gry) robi wersje dla W x H: okna HUD zostaja w oryginalnej szerokosci 1024, wysrodkowane
     w poziomie i przyklejone do dolu ekranu; plik ma trafic do IWD2\\override\\GUIW10.CHU.
W Icewind2.ini trzeba ustawic Resolution=<W>. Tryb 1024 oryginalnego exe po wgraniu tego CHU przestaje pasowac
(uzywaj IWD2.exe po usunieciu override\\GUIW10.CHU).
"""
from __future__ import annotations

import argparse
import shutil
import struct
import sys
from pathlib import Path

BASE = 0x400000


def _off(va: int) -> int:
    return va - BASE            # IWD2.exe: RVA == offset w pliku (sekcje identycznie rozmieszczone)


def layout(w: int, h: int, s: float = 1.0) -> list[tuple[int, int, int, str]]:
    """(VA operandu imm32, wartosc oryginalna, nowa wartosc, opis) dla galezi 1024. s = skala HUD (stale H-k -> H-round(k*s))."""
    K = lambda k: int(round(k * s))
    return [
        (0x42218E, 1024, w, "cmp ecx, W (rozpoznanie trybu)"),
        (0x422199, 644, h - K(124), "Y okna 8 (H-124)"),
        (0x4221A4, 629, h - K(139), "Y okna 17 (H-139)"),
        (0x4221AF, 601, h - K(167), "Y paska akcji (H-167)"),
        (0x4221BA, 484, h - K(284), "Y okien 7/19/21 (H-284)"),
        (0x4221DD, 661, h - K(107), "Y paska komend (H-107)"),
        (0x4221FB, 708, h - K(60), "Y (H-60)"),
        (0x422206, 960, w - K(64), "X/szer. (W-64)"),
        (0x422217, 658, h - K(110), "Y (H-110)"),
        (0x42224A, 150, (h - 468) // 2, "Y obszaru srodkowego ((H-468)/2)"),
        (0x422255, 522, h - K(246), "Y (H-246)"),
        (0x42225A, 256, (w - 512) // 2, "X obszaru srodkowego ((W-512)/2)"),
        (0x42225F, 768, h, "wysokosc ekranu H (rozmiar trybu i dol pelnego prostokata)"),
        (0x422264, 1024, w, "szerokosc ekranu W"),
        (0x42227E, 534, (h - 468) // 2 + 384, "Y dolna krawedz obszaru srodkowego"),
    ]


CAVE2_VA = 0x8468F1                         # zera na koncu sekcji .text (RVA 0x4468f1-0x447000, 1807 B)
FRAME_HOOK = 0x422B5E                       # mov [esi+0x4f38],ebx (6 B) - tuz przed koncem konstruktora okna gry


def frame_cave(mode: str) -> bytes:
    """Kod wywolywany po ustawieniu czterech prostokatow ramki STON10L/R/T/B (rekordy 0x1c od esi+0x49b4: id,x,y,w,h).
    W oryginale (1024) ramka otacza obszar 800x600 w ukladzie 1024x768: L,R = 112x768, T,B = 800x84. Silnik liczy je z
    (W-800)/2 i (H-600)/2, wiec dla wiekszego ekranu lewa/gorna grafika laduje przy krawedzi prostokata, nie przy srodku.
      none  - ramka poza ekranem (rozmiary bez zmian; wersja z zerowymi rozmiarami nie startowala)
      stock - bez haka: stockowe prostokaty ramki z (W-800)/2, (H-600)/2 + obrazy STON10* na caly ekran (guiscale/frame.py)
      block - ramka dokladnie wokol bloku 1024x768 przesunietego tak jak okna CHU: x += (W-1024)/2, y += H-768."""
    asm = ["mov [esi+0x4f38], ebx", "push eax", "push edx"]
    if True:
        # none: ramka ma niezerowe rozmiary (zero wywalalo silnik przy starcie), ale lezy poza ekranem: lewy gorny rog = (W, H)
        pre = ["mov eax, [0x8e7550]", "mov edx, [0x8e7554]"] if mode == "none" else ["mov eax, [0x8e7550]", "sub eax, 1024", "sar eax, 1", "mov edx, [0x8e7554]", "sub edx, 768"]
        asm += pre + [
                "mov [esi+0x49b8], ax", "mov [esi+0x49ba], dx", "mov word ptr [esi+0x49bc], 112", "mov word ptr [esi+0x49be], 768",
                "add eax, 912", "mov [esi+0x49d4], ax", "mov [esi+0x49d6], dx", "mov word ptr [esi+0x49d8], 112", "mov word ptr [esi+0x49da], 768",
                "sub eax, 800", "mov [esi+0x49f0], ax", "mov [esi+0x49f2], dx", "mov word ptr [esi+0x49f4], 800", "mov word ptr [esi+0x49f6], 84",
                "add edx, 684", "mov [esi+0x4a0c], ax", "mov [esi+0x4a0e], dx", "mov word ptr [esi+0x4a10], 800", "mov word ptr [esi+0x4a12], 84"]
    asm += ["pop edx", "pop eax", "push 0x422B64", "ret"]
    import subprocess, tempfile, os
    with tempfile.TemporaryDirectory() as td:
        src, obj = os.path.join(td, "c.s"), os.path.join(td, "c.o")
        Path(src).write_text(".intel_syntax noprefix\n.text\n" + "\n".join(asm) + "\n")
        subprocess.run(["llvm-mc", "-triple=i686-pc-windows-msvc", "-filetype=obj", src, "-o", obj], check=True)
        o = Path(obj).read_bytes()                                   # COFF: tablica sekcji tuz za 20-bajtowym naglowkiem, sekcja 0 = .text
        nsec, optsz = struct.unpack_from("<H", o, 2)[0], struct.unpack_from("<H", o, 16)[0]
        for i in range(nsec):
            sh = 20 + optsz + 40 * i
            if o[sh:sh + 8].rstrip(b"\0") == b".text":
                size, ptr = struct.unpack_from("<II", o, sh + 16)
                return o[ptr:ptr + size]
        raise SystemExit("STOP: brak sekcji .text w obiekcie kodu ramki.")


def patch_exe(src: Path, dst: Path, w: int, h: int, frame: str = "block", s: float = 1.0) -> list[str]:
    d = bytearray(src.read_bytes())
    log = []
    for va, old, new, what in layout(w, h, s):
        o = _off(va)
        cur = struct.unpack_from("<I", d, o)[0]
        if cur != old:
            raise SystemExit(f"STOP: pod VA {va:#x} ({what}) jest {cur}, oczekiwano {old} - inna wersja exe? Nic nie zapisano.")
        struct.pack_into("<I", d, o, new)
        log.append(f"{va:#x}: {old} -> {new}  ({what})")
    # Prawa krawedz srodkowego prostokata (0x8e79b0) = (W+512)/2. W oryginale 1024 rowna sie 768 = H, wiec kod bierze ja z tego samego
    # rejestru co H (mov [0x8e79b0],edx @0x4222c3). Dla innych rozmiarow trzeba osobnej wartosci: skok do 15 B wolnego miejsca
    # (nop-y miedzy funkcjami, 0x5cc201-0x5cc20f), tam zapis z imm32 i powrot.
    patch_sites = _off(0x4222C3), _off(0x5CC201)
    if bytes(d[patch_sites[0]:patch_sites[0] + 6]) != bytes.fromhex("8915b0798e00") or bytes(d[patch_sites[1]:patch_sites[1] + 15]) != b"\x90" * 15:
        raise SystemExit("STOP: nieoczekiwane bajty w miejscu zapisu 0x8e79b0 lub w wolnym miejscu 0x5cc201. Nic nie zapisano.")
    right = (w - 512) // 2 + 512
    cave = bytes.fromhex("c705b0798e00") + struct.pack("<I", right) + b"\xe9" + struct.pack("<i", 0x4222C9 - (0x5CC201 + 10 + 5))
    d[patch_sites[1]:patch_sites[1] + len(cave)] = cave
    d[patch_sites[0]:patch_sites[0] + 6] = b"\xe9" + struct.pack("<i", 0x5CC201 - (0x4222C3 + 5)) + b"\x90"
    log.append(f"0x4222c3: zapis 0x8e79b0 -> skok do 0x5cc201 (prawa krawedz srodka = {right})")
    if w > 1600:                                   # 0f 8f rel32 (jg) pod 0x422174: omija galaz 2048, idzie do galezi 1024
        o = _off(0x422174)
        if bytes(d[o:o + 2]) != b"\x0f\x8f" or struct.unpack_from("<i", d, o + 2)[0] != 0x346:
            raise SystemExit("STOP: nieoczekiwany skok 'jg' pod 0x422174. Nic nie zapisano.")
        struct.pack_into("<i", d, o + 2, 0x422198 - (0x422174 + 6))
        log.append("0x422174: jg -> galaz 1024 (W > 1600)")
    if frame in ("none", "block"):
        o = _off(FRAME_HOOK)
        if bytes(d[o:o + 6]) != bytes.fromhex("899e384f0000"):
            raise SystemExit("STOP: nieoczekiwane bajty w miejscu hooka ramki 0x422b5e. Nic nie zapisano.")
        cave = frame_cave(frame)
        c = _off(CAVE2_VA)
        if len(cave) > 0x70F or any(d[c:c + len(cave)]):
            raise SystemExit("STOP: brak wolnego miejsca na kod ramki. Nic nie zapisano.")
        d[c:c + len(cave)] = cave
        d[o:o + 6] = b"\xe9" + struct.pack("<i", CAVE2_VA - (FRAME_HOOK + 5)) + b"\x90"
        log.append(f"{FRAME_HOOK:#x}: hook ramki ({frame}) -> {CAVE2_VA:#x}, {len(cave)} B")
    dst.write_bytes(bytes(d))
    return log


def make_chu(chu: bytes, w: int, h: int) -> bytes:
    """GUIW10.CHU (okna HUD 1024x768) -> okna wysrodkowane poziomo i przyklejone do dolu ekranu W x H."""
    if chu[:8] != b"CHUIV1  ":
        raise SystemExit("STOP: to nie jest CHU V1.")
    n, _ctrl_off, win_off = struct.unpack_from("<III", chu, 8)
    out = bytearray(chu)
    dx, dy = (w - 1024) // 2, h - 768
    for i in range(n):
        o = win_off + i * 28
        x, y, ww, hh = struct.unpack_from("<HHHH", out, o + 4)
        struct.pack_into("<HH", out, o + 4, x + dx, y + dy)
    return bytes(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iwd2-dir", required=True)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--gui-scale", type=float, default=1.0, help="skala HUD (np. 1.4 dla 1920x1080); >1 generuje zasoby Z*.BAM/MOS i skalowany GUIW10.CHU")
    ap.add_argument("--font", default=None, help="TTF dla skalowanego GUI (domyslnie Liberation Serif Bold / Arial Bold z Windows)")
    ap.add_argument("--out-dir", default=None, help="domyslnie <projekt>\\mod\\hires")
    a = ap.parse_args()
    if a.width < 1024 or a.height < 768:
        raise SystemExit("Minimum 1024x768.")
    iw = Path(a.iwd2_dir)
    out = Path(a.out_dir) if a.out_dir else Path(__file__).resolve().parents[1] / "mod" / "hires"
    out.mkdir(parents=True, exist_ok=True)
    for fr, suf in (("stock", ""),):
        exe_out = out / f"IWD2_{a.width}x{a.height}{suf}.exe"
        print(f"== {exe_out.name} (ramka: {fr})")
        for line in patch_exe(iw / "IWD2.exe", exe_out, a.width, a.height, fr, a.gui_scale):
            print(line)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from inventory.resource_reader import GameResources
    game = GameResources(str(iw), override_dirs=[])  # tylko oryginaly z BIF
    if a.gui_scale > 1.0:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from guiscale.hudscale import build
        ttf = a.font or next((p for p in (r"C:\Windows\Fonts\georgiab.ttf", r"C:\Windows\Fonts\timesbd.ttf",
                                          "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf") if Path(p).exists()), None)
        if not ttf:
            raise SystemExit("STOP: nie znaleziono czcionki TTF - podaj --font.")
        ov = out / "override"
        for line in build(game, a.width, a.height, a.gui_scale, ttf, ov):
            print(line)
        from guiscale.screens import build_screens
        for line in build_screens(game, a.width, a.height, a.height / 600.0, ttf, ov):
            print(line)
        from guiscale.screens import MENUS
        for line in build_screens(game, a.width, a.height, a.height / 480.0, ttf, ov, MENUS, (640, 480), "X"):
            print(line)
        from guiscale.portraits import build_large
        for line in build_large(game, a.height / 600.0, ov):
            print(line)
        from guiscale.portraits import build as build_por
        for line in build_por(game, a.gui_scale, ov):
            print(line)
        from guiscale.frame import build_frame
        for fn, data in build_frame(game, a.width, a.height).items():
            (ov / fn).write_bytes(data)
            print(f"RAMKA {fn} ({len(data)} B)")
        print(f"\nGotowe: {exe_out}\n        zasoby GUI w {ov} (wszystko do {iw}\\override\\)")
    else:
        (out / "GUIW10.CHU").write_bytes(make_chu(game.read("guiw10", "CHU"), a.width, a.height))
        print(f"\nGotowe: {exe_out}\n        {out / 'GUIW10.CHU'}")
    print(f"Skopiuj exe do {iw}, CHU do {iw}\\override\\, w Icewind2.ini ustaw Resolution={a.width}.")


if __name__ == "__main__":
    main()
