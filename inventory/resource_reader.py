"""Czytnik zasobów Infinity Engine: chitin.key + BIF/BIFC + override.

Źródła specyfikacji (wyłącznie IESDP):
  * KEY V1   - file_formats/ie_formats/key_v1.htm
  * BIFF V1, BIFC V1, BIFC V1.0 - file_formats/ie_formats/bif_v1.htm
  * tabela resType <-> rozszerzenie - file_formats/general.htm

Założenia NIEWYNIKAJĄCE wprost ze stron IESDP są oznaczone w kodzie
komentarzem "ZAŁOŻENIE" i zebrane w `GameResources.ASSUMPTIONS`.

Python 3.11+, bez zależności zewnętrznych.
"""
from __future__ import annotations

import argparse
import io
import os
import struct
import sys
import zlib
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

# --------------------------------------------------------------------------
# Typy zasobów (general.htm). Klucz: resType, wartość: rozszerzenia.
# Pierwsze rozszerzenie jest kanoniczne (używane w nazwach typów).
# Pominięto wpisy "N/A" (key, bif, cbf, tlk, acm, mus, sav, baf, var, res).
# --------------------------------------------------------------------------
RESOURCE_TYPES: dict[int, tuple[str, ...]] = {
    0x0001: ("bmp",),
    0x0002: ("mve",),
    0x0004: ("wav", "wac"),
    0x0005: ("wfx",),
    0x0006: ("plt",),
    0x03E8: ("bam",),
    0x03E9: ("wed",),
    0x03EA: ("chu",),
    0x03EB: ("tis",),
    0x03EC: ("mos",),
    0x03ED: ("itm",),
    0x03EE: ("spl",),
    0x03EF: ("bcs",),
    0x03F0: ("ids",),
    0x03F1: ("cre",),
    0x03F2: ("are",),
    0x03F3: ("dlg",),
    0x03F4: ("2da",),
    0x03F5: ("gam",),
    0x03F6: ("sto",),
    0x03F7: ("wmp",),
    0x03F8: ("eff",),
    0x03F9: ("bs",),
    0x03FA: ("chr",),
    0x03FB: ("vvc",),
    0x03FC: ("vef",),
    0x03FD: ("pro",),
    0x03FE: ("bio",),
    0x03FF: ("wbm",),
    0x0400: ("fnt",),
    0x0402: ("gui",),
    0x0403: ("sql",),
    0x0404: ("pvrz",),
    0x0405: ("glsl",),
    0x0406: ("tot",),
    0x0407: ("toh",),
    0x0408: ("menu",),
    0x0409: ("lua",),
    0x040A: ("ttf",),
    0x040B: ("png",),
    0x044C: ("bah",),
    0x0802: ("ini",),
    0x0803: ("src",),
    0x0804: ("maze",),
}
EXT_TO_TYPE: dict[str, int] = {
    ext: t for t, exts in RESOURCE_TYPES.items() for ext in exts
}
TYPE_TIS = 0x03EB  # bif_v1.htm: "Type of this resource (always 0x3eb - TIS)"


def type_label(t: int) -> str:
    exts = RESOURCE_TYPES.get(t)
    return exts[0].upper() if exts else f"0x{t:04X}"


def normalize_type(t: int | str) -> int:
    """Przyjmuje resType (int) albo rozszerzenie ('ARE', '.are')."""
    if isinstance(t, int):
        return t
    ext = t.strip().lstrip(".").lower()
    try:
        return EXT_TO_TYPE[ext]
    except KeyError:
        raise ValueError(f"Nieznany typ zasobu: {t!r}") from None


def normalize_name(name: str) -> str:
    return name.strip().lower()


# --------------------------------------------------------------------------
# Wyjątki
# --------------------------------------------------------------------------
class ResourceError(Exception):
    pass


class ResourceFormatError(ResourceError):
    """Plik KEY/BIF niezgodny ze specyfikacją."""


class ResourceMissingInBifError(ResourceFormatError):
    """KEY wymienia zasób, ale wskazany BIF go nie zawiera (niespójne pliki gry,
    np. BIF zmieniony łatką przy niezmienionym chitin.key) - to NIE jest
    uszkodzony plik."""


class ResourceNotFoundError(ResourceError, LookupError):
    pass


# --------------------------------------------------------------------------
# KEY V1 (key_v1.htm)
# --------------------------------------------------------------------------
# Nagłówek: 0x00 sig(4) 0x04 ver(4) 0x08 #BIF 0x0c #res 0x10 off BIF 0x14 off res
_KEY_HEADER = struct.Struct("<4s4sIIII")  # 0x18 bajtów
# BIF entry: 0x00 length(4) 0x04 name offset(4) 0x08 name len(2) 0x0a flags(2)
_KEY_BIF = struct.Struct("<IIHH")  # 12 bajtów
# Resource entry: 0x00 resref(8) 0x08 type(2) 0x0a locator(4)
_KEY_RES = struct.Struct("<8sHI")  # 14 bajtów

# Flagi lokalizacji (bity pola 0x0a): bit H (0) = \data, bit G (1) = \cache,
# bity F..A (2..7) = CD1..CD6.
FLAG_DATA = 0x01
FLAG_CACHE = 0x02
FLAG_CD_MASK = 0xFC


@dataclass(frozen=True)
class BifEntry:
    length: int
    filename: str  # tak jak w KEY (zwykle z backslashami)
    flags: int


@dataclass(frozen=True)
class KeyResource:
    bif_index: int      # bity 31-20 locatora
    tileset_index: int  # bity 19-14
    file_index: int     # bity 13-0


def _decode_resref(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("latin-1").lower()


def parse_key(data: bytes) -> tuple[list[BifEntry], list[tuple[str, int, KeyResource]]]:
    if len(data) < _KEY_HEADER.size:
        raise ResourceFormatError("KEY: plik krótszy niż nagłówek")
    sig, ver, n_bif, n_res, off_bif, off_res = _KEY_HEADER.unpack_from(data, 0)
    if sig != b"KEY " or ver.rstrip(b" \0") != b"V1":
        raise ResourceFormatError(f"KEY: zły podpis/wersja: {sig!r} {ver!r}")
    if off_bif + n_bif * _KEY_BIF.size > len(data):
        raise ResourceFormatError("KEY: tablica wpisów BIF wykracza poza plik")
    if off_res + n_res * _KEY_RES.size > len(data):
        raise ResourceFormatError("KEY: tablica zasobów wykracza poza plik")

    bifs: list[BifEntry] = []
    for i in range(n_bif):
        length, name_off, name_len, flags = _KEY_BIF.unpack_from(
            data, off_bif + i * _KEY_BIF.size
        )
        raw = data[name_off:name_off + name_len]
        if len(raw) != name_len:
            raise ResourceFormatError(f"KEY: nazwa BIF #{i} wykracza poza plik")
        name = raw.split(b"\0", 1)[0].decode("latin-1")
        bifs.append(BifEntry(length, name, flags))

    resources: list[tuple[str, int, KeyResource]] = []
    for i in range(n_res):
        raw, rtype, loc = _KEY_RES.unpack_from(data, off_res + i * _KEY_RES.size)
        resources.append((
            _decode_resref(raw),
            rtype,
            KeyResource(
                bif_index=(loc >> 20) & 0xFFF,
                tileset_index=(loc >> 14) & 0x3F,
                file_index=loc & 0x3FFF,
            ),
        ))
    return bifs, resources


# --------------------------------------------------------------------------
# BIF (bif_v1.htm): BIFF V1, BIFC V1 ('BIF ' V1.0), BIFC V1.0 ('BIFC')
# --------------------------------------------------------------------------
# Nagłówek BIFF: 0x00 sig 0x04 ver 0x08 #files 0x0c #tilesets 0x10 off files
_BIFF_HEADER = struct.Struct("<4s4sIII")  # 0x14 bajtów
# File entry: locator(4) offset(4) size(4) type(2) unknown(2)
_BIFF_FILE = struct.Struct("<IIIHH")  # 16 bajtów
# Tileset entry: locator(4) offset(4) tile count(4) tile size(4) type(2) unk(2)
_BIFF_TILE = struct.Struct("<IIIIHH")  # 20 bajtów


def _ver(v: bytes) -> bytes:
    return v.rstrip(b" \0")


def _decompress_bif_container(raw: bytes) -> bytes:
    """Rozpakowuje BIFC V1.0 ('BIFC') albo BIFC V1 ('BIF ', V1.0)."""
    sig, ver = raw[:4], _ver(raw[4:8])
    if sig == b"BIFC" and ver == b"V1.0":
        # 0x08: rozmiar po dekompresji; dalej bloki:
        # [dword rozm. po dekompresji][dword rozm. skompresowany][dane zlib]
        if len(raw) < 12:
            raise ResourceFormatError("BIFC: nagłówek obcięty")
        total = struct.unpack_from("<I", raw, 8)[0]
        pos, out = 12, bytearray()
        while len(out) < total:
            if pos + 8 > len(raw):
                raise ResourceFormatError("BIFC: obcięty nagłówek bloku")
            dsize, csize = struct.unpack_from("<II", raw, pos)
            pos += 8
            chunk = raw[pos:pos + csize]
            if len(chunk) != csize:
                raise ResourceFormatError("BIFC: obcięty blok danych")
            pos += csize
            try:
                block = zlib.decompress(chunk)
            except zlib.error as e:
                raise ResourceFormatError(f"BIFC: błąd zlib: {e}") from e
            if len(block) != dsize:
                raise ResourceFormatError("BIFC: rozmiar bloku != zadeklarowany")
            out += block
        if len(out) != total:
            raise ResourceFormatError("BIFC: rozmiar całości != zadeklarowany")
        return bytes(out)

    if sig == b"BIF " and ver == b"V1.0":
        # 0x08: dł. nazwy; potem nazwa; potem [rozm. nieskompr.][rozm. skompr.][dane]
        if len(raw) < 12:
            raise ResourceFormatError("BIF V1.0: nagłówek obcięty")
        name_len = struct.unpack_from("<I", raw, 8)[0]
        pos = 12 + name_len
        if pos + 8 > len(raw):
            raise ResourceFormatError("BIF V1.0: nagłówek obcięty")
        usize, csize = struct.unpack_from("<II", raw, pos)
        pos += 8
        chunk = raw[pos:pos + csize]
        if len(chunk) != csize:
            raise ResourceFormatError("BIF V1.0: obcięte dane")
        try:
            out = zlib.decompress(chunk)
        except zlib.error as e:
            raise ResourceFormatError(f"BIF V1.0: błąd zlib: {e}") from e
        if len(out) != usize:
            raise ResourceFormatError("BIF V1.0: rozmiar != zadeklarowany")
        return out

    raise ResourceFormatError(f"Nieznany kontener BIF: {sig!r} {ver!r}")


class _Biff:
    """Otwarty archiwum BIF z zaindeksowanymi wpisami."""

    def __init__(self, path: Path):
        self.path = path
        head = b""
        with open(path, "rb") as fh:
            head = fh.read(8)
        sig, ver = head[:4], _ver(head[4:8])
        self._stream: BinaryIO
        if sig == b"BIFF" and ver == b"V1":
            self._stream = open(path, "rb")
            self.compressed = False
        elif (sig, ver) in ((b"BIFC", b"V1.0"), (b"BIF ", b"V1.0")):
            self._stream = io.BytesIO(_decompress_bif_container(path.read_bytes()))
            self.compressed = True
        else:
            raise ResourceFormatError(f"{path}: nieznany podpis BIF {sig!r} {ver!r}")

        try:
            s = self._stream
            s.seek(0, os.SEEK_END)
            self._size = s.tell()
            s.seek(0)
            hdr = s.read(_BIFF_HEADER.size)
            if len(hdr) < _BIFF_HEADER.size:
                raise ResourceFormatError(f"{path}: nagłówek BIFF obcięty")
            sig, ver, n_files, n_tiles, off_files = _BIFF_HEADER.unpack(hdr)
            if sig != b"BIFF" or _ver(ver) != b"V1":
                raise ResourceFormatError(f"{path}: zły podpis BIFF po dekompresji")

            s.seek(off_files)
            blob = s.read(n_files * _BIFF_FILE.size + n_tiles * _BIFF_TILE.size)
            if len(blob) != n_files * _BIFF_FILE.size + n_tiles * _BIFF_TILE.size:
                raise ResourceFormatError(f"{path}: tablice wpisów wykraczają poza plik")

            # file index = bity 0-13 locatora
            self.files: dict[int, tuple[int, int, int]] = {}
            for i in range(n_files):
                loc, off, size, rtype, _unk = _BIFF_FILE.unpack_from(blob, i * _BIFF_FILE.size)
                self.files[loc & 0x3FFF] = (off, size, rtype)

            # ZAŁOŻENIE: wpisy tilesetów leżą bezpośrednio za wpisami plików
            # (kolejność "File entries, Tileset entries" ze strony IESDP; nagłówek
            # nie zawiera osobnego offsetu).
            base = n_files * _BIFF_FILE.size
            # tileset index = bity 14-19 locatora
            self.tiles: dict[int, tuple[int, int, int, int]] = {}
            for i in range(n_tiles):
                loc, off, count, tsize, rtype, _unk = _BIFF_TILE.unpack_from(
                    blob, base + i * _BIFF_TILE.size
                )
                self.tiles[(loc >> 14) & 0x3F] = (off, count, tsize, rtype)
        except BaseException:
            self._stream.close()
            raise

    def _read_at(self, off: int, size: int) -> bytes:
        if off + size > self._size:
            raise ResourceFormatError(
                f"{self.path}: dane [{off}, {off + size}) poza plikiem ({self._size})"
            )
        self._stream.seek(off)
        return self._stream.read(size)

    def read_file(self, file_index: int) -> tuple[bytes, int]:
        off, size, rtype = self.files[file_index]
        return self._read_at(off, size), rtype

    def read_tileset(self, tile_index: int) -> tuple[bytes, int]:
        """Surowe dane kafelków (count * size); BEZ nagłówka TIS."""
        off, count, tsize, rtype = self.tiles[tile_index]
        return self._read_at(off, count * tsize), rtype

    def close(self) -> None:
        self._stream.close()


# --------------------------------------------------------------------------
# Wyszukiwanie ścieżek bez rozróżniania wielkości liter
# --------------------------------------------------------------------------
def _find_ci(base: Path, rel: str) -> Path | None:
    cur = base
    for part in (p for p in rel.replace("\\", "/").split("/") if p and p != "."):
        if not cur.is_dir():
            return None
        cand = cur / part
        if cand.exists():
            cur = cand
            continue
        low = part.lower()
        try:
            match = next((n for n in os.listdir(cur) if n.lower() == low), None)
        except OSError:
            return None
        if match is None:
            return None
        cur = cur / match
    return cur if cur.exists() else None


# --------------------------------------------------------------------------
# GameResources
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ResourceSource:
    kind: str                    # "override" | "bif"
    path: Path | None            # override: plik; bif: rozwiązana ścieżka (lub None)
    bif_name: str | None = None  # nazwa BIF z KEY
    bif_index: int | None = None

    def __str__(self) -> str:
        if self.kind == "override":
            return f"override:{self.path}"
        where = self.path if self.path else "(BIF nie znaleziony)"
        return f"bif:{self.bif_name}#{self.bif_index} -> {where}"


class GameResources:
    ASSUMPTIONS = (
        "Wpisy tilesetów w BIF leżą bezpośrednio za wpisami plików.",
        "Zasób KEY typu TIS: najpierw szukany wśród tilesetów (indeks z bitów "
        "14-19), a jeśli brak - wśród plików (bity 0-13). Inne typy: tylko pliki.",
        "Duplikaty (nazwa,typ) w KEY: wygrywa pierwszy wpis.",
        "BIF-y rozwiązywane względem katalogu gry i (EE) katalogu lang/<kod>; "
        "dla .bif próbowany też wariant .cbf. BIF-y z bitem CD<n> w KEY są "
        "szukane też w podkatalogu CD<n> (nazwa katalogu: założenie spoza IESDP).",
        "Pliki override o nazwie dłuższej niż 8 znaków lub nieznanym "
        "rozszerzeniu są ignorowane (policzone w .ignored_override_files).",
        "read() dla tilesetu zwraca surowe dane kafelków bez nagłówka TIS.",
    )

    def __init__(
        self,
        game_dir: str | os.PathLike[str],
        engine: str = "classic",
        *,
        lang: str | None = None,
        key_name: str = "chitin.key",
        override_dirs: list[str | os.PathLike[str]] | None = None,
        max_open_bifs: int = 3,
    ):
        if engine not in ("classic", "ee"):
            raise ValueError("engine musi być 'classic' albo 'ee'")
        if lang is not None and engine != "ee":
            raise ValueError("lang ma sens tylko dla engine='ee'")
        self.game_dir = Path(game_dir)
        self.engine = engine
        self.lang = lang
        if not self.game_dir.is_dir():
            raise FileNotFoundError(f"Brak katalogu gry: {self.game_dir}")

        key_path = _find_ci(self.game_dir, key_name)
        if key_path is None:
            raise FileNotFoundError(f"Nie znaleziono {key_name} w {self.game_dir}")
        self.key_path = key_path

        # korzenie, względem których rozwiązywane są ścieżki BIF z KEY
        self.bif_roots: list[Path] = [self.game_dir]
        if engine == "ee" and lang:
            lang_dir = _find_ci(self.game_dir, f"lang/{lang}")
            if lang_dir is None:
                raise FileNotFoundError(f"Brak katalogu lang/{lang} w {self.game_dir}")
            self.bif_roots.append(lang_dir)

        if override_dirs is None:
            ov = _find_ci(self.game_dir, "override")
            self.override_dirs = [ov] if ov else []
        else:
            self.override_dirs = [Path(p) for p in override_dirs]

        self.bifs, key_resources = parse_key(key_path.read_bytes())
        self.key_index: dict[tuple[str, int], KeyResource] = {}
        self.key_duplicates = 0
        self.key_bad_bif_refs = 0
        for name, rtype, kr in key_resources:
            if kr.bif_index >= len(self.bifs):
                self.key_bad_bif_refs += 1
                continue
            k = (name, rtype)
            if k in self.key_index:
                self.key_duplicates += 1
                continue
            self.key_index[k] = kr

        self.warnings: list[str] = []
        self.override_index: dict[tuple[str, int], Path] = {}
        self.ignored_override_files = 0
        self.rescan_override()

        self._max_open = max(1, max_open_bifs)
        self._open: OrderedDict[int, _Biff] = OrderedDict()
        self._bif_paths: dict[int, Path | None] = {}

    # -- override ----------------------------------------------------------
    def rescan_override(self) -> None:
        self.override_index = {}
        self.ignored_override_files = 0
        for d in self.override_dirs:
            if not d.is_dir():
                continue
            with os.scandir(d) as it:
                for e in it:
                    if not e.is_file():
                        continue
                    stem, dot, ext = e.name.rpartition(".")
                    if not dot or ext.lower() not in EXT_TO_TYPE or len(stem) > 8 or not stem:
                        self.ignored_override_files += 1
                        continue
                    # katalogi override wcześniej na liście mają pierwszeństwo
                    self.override_index.setdefault(
                        (stem.lower(), EXT_TO_TYPE[ext.lower()]), Path(e.path)
                    )

    # -- BIF ---------------------------------------------------------------
    def _resolve_bif(self, idx: int) -> Path | None:
        if idx in self._bif_paths:
            return self._bif_paths[idx]
        entry = self.bifs[idx]
        rel = entry.filename.replace("\\", "/")
        base = rel.rsplit("/", 1)[-1]
        rels = [rel]
        if entry.flags & FLAG_DATA:
            rels += [f"data/{rel}", f"data/{base}"]
        if entry.flags & FLAG_CACHE:
            rels += [f"cache/{base}", f"cache/{rel}"]
        # Bity CD z KEY (key_v1.htm: bity A..F = CD6..CD1, czyli bit 2 = CD1 ...
        # bit 7 = CD6). ZAŁOŻENIE spoza IESDP: płyta n to podkatalog 'CD<n>'
        # katalogu gry (potwierdzone na instalacji IWD2: CD2\\Data\\*.bif).
        for bit in range(2, 8):
            if entry.flags & (1 << bit):
                n = bit - 1
                rels += [f"CD{n}/{rel}", f"CD{n}/data/{base}"]
        # wariant .cbf dla każdej kandydatury .bif
        rels += [r[:-4] + ".cbf" for r in list(rels) if r.lower().endswith(".bif")]
        found: Path | None = None
        for root in self.bif_roots:
            for r in dict.fromkeys(rels):
                found = _find_ci(root, r)
                if found and found.is_file():
                    break
                found = None
            if found:
                break
        self._bif_paths[idx] = found
        return found

    def _get_biff(self, idx: int) -> _Biff:
        if idx in self._open:
            self._open.move_to_end(idx)
            return self._open[idx]
        path = self._resolve_bif(idx)
        if path is None:
            raise FileNotFoundError(
                f"Nie znaleziono BIF '{self.bifs[idx].filename}' "
                f"(flagi 0x{self.bifs[idx].flags:04x}) w {[str(r) for r in self.bif_roots]}"
            )
        biff = _Biff(path)
        self._open[idx] = biff
        while len(self._open) > self._max_open:
            _, old = self._open.popitem(last=False)
            old.close()
        return biff

    def missing_bifs(self) -> list[BifEntry]:
        """BIF-y z KEY, których nie udało się znaleźć na dysku."""
        return [b for i, b in enumerate(self.bifs) if self._resolve_bif(i) is None]

    def dangling(self) -> list[tuple[str, int, str, bool]]:
        """Wpisy KEY, których nie ma w wskazanym BIF-ie (BIF-y nieznalezione na
        dysku są pomijane - patrz missing_bifs). Zwraca (nazwa, typ, plik BIF,
        czy_nadpisany_w_override). Otwiera każdy BIF raz (dla BIFC to pełna
        dekompresja, więc może chwilę potrwać)."""
        by_bif: dict[int, list[tuple[str, int, KeyResource]]] = {}
        for (name, rtype), kr in self.key_index.items():
            by_bif.setdefault(kr.bif_index, []).append((name, rtype, kr))
        out: list[tuple[str, int, str, bool]] = []
        for idx in sorted(by_bif):
            path = self._resolve_bif(idx)
            if path is None:
                continue
            biff = _Biff(path)
            try:
                for name, rtype, kr in by_bif[idx]:
                    # ta sama logika co w read()
                    ok = ((rtype == TYPE_TIS and kr.tileset_index in biff.tiles)
                          or kr.file_index in biff.files)
                    if not ok:
                        out.append((name, rtype, self.bifs[idx].filename,
                                    (name, rtype) in self.override_index))
            finally:
                biff.close()
        return sorted(out)

    # -- API ---------------------------------------------------------------
    @staticmethod
    def _key(name: str, rtype: int | str) -> tuple[str, int]:
        return normalize_name(name), normalize_type(rtype)

    def exists(self, name: str, rtype: int | str) -> bool:
        k = self._key(name, rtype)
        return k in self.override_index or k in self.key_index

    def locate(self, name: str, rtype: int | str) -> ResourceSource | None:
        k = self._key(name, rtype)
        if k in self.override_index:
            return ResourceSource("override", self.override_index[k])
        kr = self.key_index.get(k)
        if kr is None:
            return None
        e = self.bifs[kr.bif_index]
        return ResourceSource("bif", self._resolve_bif(kr.bif_index), e.filename, kr.bif_index)

    def source(self, name: str, rtype: int | str) -> str | None:
        loc = self.locate(name, rtype)
        return None if loc is None else str(loc)

    def read(self, name: str, rtype: int | str) -> bytes:
        k = self._key(name, rtype)
        if k in self.override_index:
            return self.override_index[k].read_bytes()
        kr = self.key_index.get(k)
        if kr is None:
            raise ResourceNotFoundError(f"{k[0]}.{type_label(k[1]).lower()}")
        biff = self._get_biff(kr.bif_index)
        label = f"{k[0]}.{type_label(k[1]).lower()}"
        if k[1] == TYPE_TIS and kr.tileset_index in biff.tiles:
            data, etype = biff.read_tileset(kr.tileset_index)
        elif kr.file_index in biff.files:
            data, etype = biff.read_file(kr.file_index)
        else:
            raise ResourceMissingInBifError(
                f"{label}: BIF {biff.path.name} nie zawiera wpisu "
                f"(plik {kr.file_index}, tileset {kr.tileset_index})"
            )
        if etype != k[1]:
            self.warnings.append(
                f"{label}: typ w KEY 0x{k[1]:04x} != typ w BIF 0x{etype:04x}"
            )
        return data

    # -- statystyki --------------------------------------------------------
    def iter_resources(self) -> Iterator[tuple[str, int]]:
        yield from dict.fromkeys([*self.override_index.keys(), *self.key_index.keys()])

    def summary(self) -> dict[str, dict[str, int]]:
        """Na typ: total (unikalne po scaleniu), in_key, override_only, overridden."""
        out: dict[int, Counter] = {}
        for k in self.iter_resources():
            c = out.setdefault(k[1], Counter())
            c["total"] += 1
            in_key, in_ov = k in self.key_index, k in self.override_index
            c["in_key"] += in_key
            c["override_only"] += in_ov and not in_key
            c["overridden"] += in_ov and in_key
        return {type_label(t): dict(c) for t, c in sorted(out.items())}

    def close(self) -> None:
        for b in self._open.values():
            b.close()
        self._open.clear()

    def __enter__(self) -> "GameResources":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def format_summary(gr: GameResources) -> str:
    s = gr.summary()
    lines = [
        f"Gra: {gr.game_dir}   engine={gr.engine}" + (f"   lang={gr.lang}" if gr.lang else ""),
        f"KEY: {len(gr.bifs)} BIF, {len(gr.key_index)} unikalnych zasobów "
        f"(duplikaty: {gr.key_duplicates}, złe odwołania do BIF: {gr.key_bad_bif_refs})",
        f"Override: {len(gr.override_index)} zasobów "
        f"(zignorowane pliki: {gr.ignored_override_files})",
        "",
        f"{'typ':<8}{'razem':>9}{'w KEY':>9}{'tylko ovr':>11}{'nadpis.':>9}",
    ]
    tot = Counter()
    for label, c in s.items():
        lines.append(
            f"{label:<8}{c['total']:>9}{c.get('in_key', 0):>9}"
            f"{c.get('override_only', 0):>11}{c.get('overridden', 0):>9}"
        )
        tot.update(c)
    lines.append(
        f"{'SUMA':<8}{tot['total']:>9}{tot['in_key']:>9}"
        f"{tot['override_only']:>11}{tot['overridden']:>9}"
    )
    missing = gr.missing_bifs()
    if missing:
        lines += ["", f"UWAGA: nie znaleziono {len(missing)} BIF z KEY:"]
        lines += [f"  {b.filename} (flagi 0x{b.flags:04x})" for b in missing[:20]]
        if len(missing) > 20:
            lines.append(f"  ... i {len(missing) - 20} więcej")
    return "\n".join(lines)


def format_dangling(gr: GameResources, limit: int = 30) -> str:
    d = gr.dangling()
    if not d:
        return "Spójność KEY/BIF: wszystkie wpisy KEY są obecne w swoich BIF-ach."
    per_type = Counter(type_label(t) for _, t, _, _ in d)
    lines = [f"Wpisy KEY nieobecne w swoich BIF-ach: {len(d)} "
             f"({', '.join(f'{k}={v}' for k, v in sorted(per_type.items()))})"]
    for name, t, bif, ov in d[:limit]:
        lines.append(f"  {name}.{type_label(t).lower():<5} w {bif}" + ("  [jest w override]" if ov else ""))
    if len(d) > limit:
        lines.append(f"  ... i {len(d) - limit} więcej")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Podsumowanie zasobów Infinity Engine")
    ap.add_argument("--game-dir", required=True)
    ap.add_argument("--engine", choices=("classic", "ee"), default="classic")
    ap.add_argument("--lang", help="EE: podkatalog lang/<kod>, np. en_US")
    ap.add_argument("--check-bifs", action="store_true",
                    help="wypisz wpisy KEY nieobecne w swoich BIF-ach (niespójne pliki gry)")
    ap.add_argument("--extract", metavar="NAZWA.TYP", help="zapisz zasób do --out")
    ap.add_argument("--out", help="plik wyjściowy dla --extract")
    a = ap.parse_args(argv)
    with GameResources(a.game_dir, a.engine, lang=a.lang) as gr:
        if a.extract:
            name, _, ext = a.extract.rpartition(".")
            data = gr.read(name, ext)
            Path(a.out or a.extract).write_bytes(data)
            print(f"{a.extract}: {len(data)} B z {gr.source(name, ext)}")
            return 0
        print(format_summary(gr))
        if a.check_bifs:
            print("\n" + format_dangling(gr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
