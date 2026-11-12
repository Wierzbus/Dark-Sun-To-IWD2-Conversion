"""WED V1.3 - pełny odczyt, kontrola spójności, zapis, przepisanie nazw TIS.

Źródło: docs/WED file format.html ("Applies to: BG1 ... IWD2"). Rozmiary struktur
wyliczone z tabel strony: nagłówek 0x20, overlay 0x18, secondary header 0x14,
drzwi 0x1A, tilemap 0x0A, wall group 4, polygon 0x12, wierzchołek 4.

Które tabele wskazują na które (docs/WED):
  tilemap[komórka] -> (start,count) w tablicy lookup overlaya -> indeks kafla w TIS;
  door cells       -> indeksy w tilemapie overlaya 0;
  wall group       -> (start,count) w tablicy indeksów wielokątów -> wielokąty;
  polygon          -> (start,count) w tablicy wierzchołków;
  door             -> (offset,count) wielokątów otwartych/zamkniętych (w tej samej
                      tabeli wielokątów, za wielokątami ścian), oraz (first,count)
                      door cells.

OBSERWACJE na plikach BG1/IWD2 (nie z docs), na których oparty jest zapis:
  * nagłówek ma 5 slotów overlayów (0 użytych slotów ma szerokość 0 i pustą nazwę);
  * liczba wall groups = ceil(W/10)*ceil(H/7.5) (docs to podają) - zgodna z danymi;
  * liczba w secondary header = tylko wielokąty ścian; wielokąty drzwi leżą za nimi;
  * kolejność tabel: nagłówek, overlaye, secondary, drzwi, tilemapy, door cells,
    lookupy, wall groups, wielokąty, indeksy wielokątów, wierzchołki;
  * puste sloty overlayów: offset tilemapy = koniec obszaru tilemap, offset lookupu
    = koniec obszaru lookupów; offset wielokątów drzwi bez wielokątów = ich
    miejsce w tabeli (pierwszy wielokąt drzwi tego typu).
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

HEADER = 0x20
OVERLAY = 0x18
SECONDARY = 0x14
DOOR = 0x1A
TILEMAP = 0x0A
POLYGON = 0x12
SLOTS = 5

# bity flag wielokąta opisane w docs: 0 shade wall, 1 hovering, 2/3 cover animations,
# 4..6 unknown, 7 door
POLY_KNOWN_MASK = 0b10001111
# bity flag tilemapy: bit 0 unused, 1..7 draw overlay 1..7
TILE_KNOWN_MASK = 0b11111110


class WedFormatError(ValueError):
    """WED niezgodny ze specyfikacją (podpis, wersja, zakresy, spójność)."""


@dataclass
class Cell:
    start: int
    count: int
    secondary: int          # surowe u16 (0xFFFF = brak)
    flags: int
    unknown: bytes = b"\0\0\0"


@dataclass
class Overlay:
    width: int
    height: int
    tileset: str
    unique_tiles: int = 0
    movement: int = 0
    cells: list[Cell] = field(default_factory=list)
    lookup: list[int] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return self.width == 0 and self.height == 0


@dataclass
class Door:
    name: str
    state: int
    first_cell: int
    n_cells: int
    open_first: int          # indeks w tabeli wielokątów
    n_open: int
    closed_first: int
    n_closed: int


@dataclass
class Polygon:
    flags: int
    height: int
    bbox: tuple[int, int, int, int]      # minX, maxX, minY, maxY (jak w pliku)
    start: int                           # pierwszy wierzchołek
    n_vertices: int


@dataclass
class Wed:
    overlays: list[Overlay]              # zawsze SLOTS slotów (puste na końcu)
    doors: list[Door]
    door_cells: list[int]
    wall_groups: list[tuple[int, int]]
    polygons: list[Polygon]              # ściany, potem wielokąty drzwi
    n_wall_polygons: int
    polygon_indices: list[int]
    vertices: list[tuple[int, int]]
    issues: list[str] = field(default_factory=list)

    @property
    def base(self) -> Overlay:
        return self.overlays[0]


def _u16(d, o): return struct.unpack_from("<H", d, o)[0]
def _u32(d, o): return struct.unpack_from("<I", d, o)[0]


def expected_wall_groups(w: int, h: int) -> int:
    """docs/WED: grupa ma 10 x 7,5 kafla."""
    return math.ceil(w / 10) * math.ceil(h / 7.5)


def _name(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("latin-1")


def parse_wed(data: bytes, *, name: str = "WED") -> Wed:
    n = len(data)
    if n < HEADER:
        raise WedFormatError(f"{name}: plik krótszy niż nagłówek ({n} B)")
    if data[:4] != b"WED ":
        raise WedFormatError(f"{name}: zły podpis {data[:4]!r}")
    if data[4:8] != b"V1.3":
        raise WedFormatError(f"{name}: wersja {data[4:8]!r}, obsługiwana tylko 'V1.3'")
    n_ov, n_doors, ov_off, sec_off, door_off, dcell_off = struct.unpack_from("<6I", data, 8)

    def need(off, size, what):
        if off + size > n:
            raise WedFormatError(f"{name}: {what} (0x{off:X}+{size}) wykracza poza plik ({n} B)")

    if n_ov != SLOTS:
        raise WedFormatError(f"{name}: nagłówek deklaruje {n_ov} overlayów (obserwacja: {SLOTS})")
    need(ov_off, n_ov * OVERLAY, "overlaye")
    need(sec_off, SECONDARY, "secondary header")
    need(door_off, n_doors * DOOR, "drzwi")
    n_poly, poly_off, vert_off, wg_off, pidx_off = struct.unpack_from("<5I", data, sec_off)

    raw_ov = []
    for i in range(n_ov):
        o = ov_off + i * OVERLAY
        w, h = struct.unpack_from("<HH", data, o)
        raw_ov.append((w, h, _name(data[o + 4:o + 12]), _u16(data, o + 12),
                       _u16(data, o + 14), _u32(data, o + 16), _u32(data, o + 20)))
    if raw_ov[0][0] == 0 or raw_ov[0][1] == 0:
        raise WedFormatError(f"{name}: overlay 0 ma wymiar {raw_ov[0][0]}x{raw_ov[0][1]}")

    # wszystkie początki tabel - do wyznaczania długości tablic (różnica offsetów)
    starts = {sec_off, door_off, dcell_off, poly_off, vert_off, wg_off, pidx_off, n}
    for w, h, _nm, _u, _m, tm, tl in raw_ov:
        if w and h:
            starts.add(tm)
            starts.add(tl)
    ordered = sorted(starts)

    def next_after(off):
        for s in ordered:
            if s > off:
                return s
        return n

    overlays: list[Overlay] = []
    for i, (w, h, nm, uq, mv, tm, tl) in enumerate(raw_ov):
        ov = Overlay(w, h, nm, uq, mv)
        if w and h:
            need(tm, w * h * TILEMAP, f"tilemap overlaya {i}")
            for c in range(w * h):
                o = tm + c * TILEMAP
                ov.cells.append(Cell(_u16(data, o), _u16(data, o + 2), _u16(data, o + 4),
                                     data[o + 6], bytes(data[o + 7:o + 10])))
            ln = (next_after(tl) - tl) // 2
            need(tl, ln * 2, f"lookup overlaya {i}")
            ov.lookup = list(struct.unpack_from(f"<{ln}H", data, tl))
        overlays.append(ov)

    doors: list[Door] = []
    for i in range(n_doors):
        o = door_off + i * DOOR
        st, fc, nc, no, ncl, of, cf = struct.unpack_from("<HHHHHII", data, o + 8)
        for what, off in (("otwartych", of), ("zamkniętych", cf)):
            if off < poly_off or (off - poly_off) % POLYGON:
                raise WedFormatError(
                    f"{name}: drzwi {i}: offset wielokątów {what} 0x{off:X} poza tabelą/niewyrównany")
        doors.append(Door(_name(data[o:o + 8]), st, fc, nc, (of - poly_off) // POLYGON, no,
                          (cf - poly_off) // POLYGON, ncl))

    total_poly = max([n_poly] + [d.open_first + d.n_open for d in doors]
                     + [d.closed_first + d.n_closed for d in doors])
    need(poly_off, total_poly * POLYGON, "wielokąty")
    polygons = []
    for i in range(total_poly):
        o = poly_off + i * POLYGON
        sv, nv, fl, ht, x0, x1, y0, y1 = struct.unpack_from("<IIBBhhhh", data, o)
        polygons.append(Polygon(fl, ht, (x0, x1, y0, y1), sv, nv))

    n_vert = (next_after(vert_off) - vert_off) // 4
    need(vert_off, n_vert * 4, "wierzchołki")
    verts = [struct.unpack_from("<hh", data, vert_off + 4 * i) for i in range(n_vert)]

    tl0 = raw_ov[0][6]
    if tl0 < dcell_off or (tl0 - dcell_off) % 2:
        raise WedFormatError(f"{name}: door cells 0x{dcell_off:X} a lookup overlaya 0 0x{tl0:X}")
    n_dcells = (tl0 - dcell_off) // 2    # door cells leżą bezpośrednio przed lookupami
    need(dcell_off, n_dcells * 2, "door cells")
    dcells = list(struct.unpack_from(f"<{n_dcells}H", data, dcell_off))

    ng = expected_wall_groups(overlays[0].width, overlays[0].height)
    need(wg_off, ng * 4, "wall groups")
    groups = [struct.unpack_from("<HH", data, wg_off + 4 * i) for i in range(ng)]

    n_pidx = (next_after(pidx_off) - pidx_off) // 2
    need(pidx_off, n_pidx * 2, "indeksy wielokątów")
    pidx = list(struct.unpack_from(f"<{n_pidx}H", data, pidx_off))

    wed = Wed(overlays, doors, dcells, [tuple(g) for g in groups], polygons, n_poly, pidx,
              [tuple(v) for v in verts])
    wed.issues.extend(check_wed(wed, name=name))
    return wed


def check_wed(w: Wed, *, name: str = "WED", tile_count: int | None = None) -> list[str]:
    """Zwraca listę naruszeń spójności (puste = OK). `tile_count`: liczba kafli TIS
    bazowego overlaya (kontrola zakresu)."""
    bad: list[str] = []
    base = w.overlays[0]
    nv, np_, ncell = len(w.vertices), len(w.polygons), len(base.cells)
    for i, ov in enumerate(w.overlays):
        if ov.empty:
            continue
        if len(ov.cells) != ov.width * ov.height:
            bad.append(f"overlay {i}: {len(ov.cells)} komórek != {ov.width}*{ov.height}")
        for c, cell in enumerate(ov.cells):
            if cell.start + cell.count > len(ov.lookup):
                bad.append(f"overlay {i} komórka {c}: lookup {cell.start}+{cell.count} > {len(ov.lookup)}")
        if ov.lookup and i == 0 and tile_count is not None and max(ov.lookup) >= tile_count:
            bad.append(f"overlay 0: indeks kafla {max(ov.lookup)} >= liczba kafli TIS {tile_count}")
    for i, d in enumerate(w.doors):
        if d.first_cell + d.n_cells > len(w.door_cells):
            bad.append(f"drzwi {i}: door cells {d.first_cell}+{d.n_cells} > {len(w.door_cells)}")
        for what, f_, c_ in (("otwarte", d.open_first, d.n_open), ("zamknięte", d.closed_first, d.n_closed)):
            if f_ + c_ > np_:
                bad.append(f"drzwi {i}: wielokąty {what} {f_}+{c_} > {np_}")
    for i, c in enumerate(w.door_cells):
        if c >= ncell:
            bad.append(f"door cell {i}: {c} >= liczba komórek {ncell}")
    if len(w.wall_groups) != expected_wall_groups(base.width, base.height):
        bad.append(f"wall groups: {len(w.wall_groups)} != "
                   f"{expected_wall_groups(base.width, base.height)} wg docs")
    for i, (s, c) in enumerate(w.wall_groups):
        if s + c > len(w.polygon_indices):
            bad.append(f"wall group {i}: {s}+{c} > {len(w.polygon_indices)}")
    for i, p in enumerate(w.polygon_indices):
        if p >= np_:
            bad.append(f"indeks wielokąta {i}: {p} >= liczba wielokątów {np_}")
    for i, p in enumerate(w.polygons):
        if p.start + p.n_vertices > nv:
            bad.append(f"wielokąt {i}: wierzchołki {p.start}+{p.n_vertices} > {nv}")
    return bad


def write_wed(w: Wed) -> bytes:
    """Zapis w standardowej kolejności tabel (patrz docstring modułu)."""
    if len(w.overlays) != SLOTS:
        raise WedFormatError(f"overlayów musi być {SLOTS}")
    base = w.overlays[0]
    ov_off = HEADER
    sec_off = ov_off + SLOTS * OVERLAY
    door_off = sec_off + SECONDARY
    tm_start = door_off + len(w.doors) * DOOR
    tm_offs, cur = [], tm_start
    for ov in w.overlays:
        if ov.empty:
            tm_offs.append(None)
        else:
            tm_offs.append(cur)
            cur += len(ov.cells) * TILEMAP
    tm_end = cur
    dcell_off = tm_end
    lk_start = dcell_off + len(w.door_cells) * 2
    lk_offs, cur = [], lk_start
    for ov in w.overlays:
        if ov.empty:
            lk_offs.append(None)
        else:
            lk_offs.append(cur)
            cur += len(ov.lookup) * 2
    lk_end = cur
    wg_off = lk_end
    poly_off = wg_off + len(w.wall_groups) * 4
    pidx_off = poly_off + len(w.polygons) * POLYGON
    vert_off = pidx_off + len(w.polygon_indices) * 2
    end = vert_off + len(w.vertices) * 4

    out = bytearray()
    out += b"WED V1.3" + struct.pack("<6I", SLOTS, len(w.doors), ov_off, sec_off, door_off, dcell_off)
    for ov, tm, lk in zip(w.overlays, tm_offs, lk_offs):
        nm = ov.tileset.encode("latin-1")
        if len(nm) > 8:
            raise WedFormatError(f"nazwa tilesetu {ov.tileset!r} dłuższa niż 8 znaków")
        out += struct.pack("<HH8sHHII", ov.width, ov.height, nm, ov.unique_tiles, ov.movement,
                           tm_end if tm is None else tm, lk_end if lk is None else lk)
    out += struct.pack("<5I", w.n_wall_polygons, poly_off, vert_off, wg_off, pidx_off)
    for d in w.doors:
        out += struct.pack("<8sHHHHHII", d.name.encode("latin-1"), d.state, d.first_cell, d.n_cells,
                           d.n_open, d.n_closed, poly_off + d.open_first * POLYGON,
                           poly_off + d.closed_first * POLYGON)
    for ov in w.overlays:
        for c in ov.cells:
            out += struct.pack("<HHHB", c.start, c.count, c.secondary, c.flags) + c.unknown
    out += struct.pack(f"<{len(w.door_cells)}H", *w.door_cells)
    for ov in w.overlays:
        out += struct.pack(f"<{len(ov.lookup)}H", *ov.lookup)
    for s, c in w.wall_groups:
        out += struct.pack("<HH", s, c)
    for p in w.polygons:
        out += struct.pack("<IIBBhhhh", p.start, p.n_vertices, p.flags, p.height, *p.bbox)
    out += struct.pack(f"<{len(w.polygon_indices)}H", *w.polygon_indices)
    for x, y in w.vertices:
        out += struct.pack("<hh", x, y)
    assert len(out) == end
    return bytes(out)


def rename_tilesets(w: Wed, name_map: dict[str, str]) -> Wed:
    """Zwraca kopię z przepisanymi nazwami TIS (klucze bez rozróżniania wielkości
    liter). Każdy użyty tileset musi być w tabeli - inaczej WedFormatError."""
    import copy
    m = {k.lower(): v.upper() for k, v in name_map.items()}
    new = copy.deepcopy(w)
    for i, ov in enumerate(new.overlays):
        if ov.empty:
            continue
        key = ov.tileset.lower()
        if key not in m:
            raise WedFormatError(f"overlay {i}: tileset {ov.tileset!r} nie ma wpisu w tabeli nazw")
        ov.tileset = m[key]
    return new


def flag_report(w: Wed) -> dict:
    """Liczności flag; wartości spoza opisanych w docs trafiają do 'nierozpoznane'."""
    tiles: dict[int, int] = {}
    unk_bytes = 0
    for ov in w.overlays:
        for c in ov.cells:
            tiles[c.flags] = tiles.get(c.flags, 0) + 1
            unk_bytes += c.unknown != b"\0\0\0"
    polys: dict[int, int] = {}
    for p in w.polygons:
        polys[p.flags] = polys.get(p.flags, 0) + 1
    return {
        "tile_flags": dict(sorted(tiles.items())),
        "polygon_flags": dict(sorted(polys.items())),
        "nierozpoznane_bity_tile": sorted(f for f in tiles if f & ~TILE_KNOWN_MASK),
        "nierozpoznane_bity_polygon": sorted(f for f in polys if f & ~POLY_KNOWN_MASK),
        "tilemap_unknown_niezerowe": unk_bytes,
    }


def convert_wed(src: Wed, name_map: dict[str, str]) -> tuple[Wed, list[str]]:
    """BG1 -> IWD2: kopia struktury, przepisane nazwy TIS; flagi, bbox i wielokąty
    drzwi bez zmian (decyzja użytkownika: flagi 1:1). Zwraca (WED, uwagi)."""
    notes: list[str] = []
    used = [i for i, o in enumerate(src.overlays) if not o.empty]
    if len(used) > 1:
        notes.append(f"{len(used)} overlayów: renderowanie overlayów wodnych w IWD2 "
                     "niezweryfikowane (w próbce IWD2 brak)")
    new = rename_tilesets(src, name_map)
    rep = flag_report(new)
    if rep["nierozpoznane_bity_polygon"]:
        notes.append(f"flagi wielokątów z bitami spoza docs: {rep['nierozpoznane_bity_polygon']}")
    if rep["nierozpoznane_bity_tile"]:
        notes.append(f"flagi kafli z bitami spoza docs: {rep['nierozpoznane_bity_tile']}")
    if rep["tilemap_unknown_niezerowe"]:
        notes.append(f"{rep['tilemap_unknown_niezerowe']} komórek z niezerowymi bajtami 'unknown'")
    new.issues = check_wed(new)
    return new, notes


def _dp(points: list[tuple[int, int]], eps: float) -> list[int]:
    """Douglas-Peucker na łamanej (indeksy zachowanych punktów, z końcami)."""
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = points[a], points[b]
        dx, dy = bx - ax, by - ay
        norm = (dx * dx + dy * dy) ** 0.5 or 1.0
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / norm if (dx or dy) else ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
            if d > best:
                best, bi = d, i
        if bi >= 0 and best > eps:
            keep.add(bi)
            stack += [(a, bi), (bi, b)]
    return sorted(keep)


def _simple(ring: list[tuple[int, int]]) -> bool:
    """Brak przecięć niesąsiednich krawędzi (zamknięty wielokąt)."""
    n = len(ring)

    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])

    def inter(p1, p2, p3, p4):
        d1, d2, d3, d4 = ccw(p3, p4, p1), ccw(p3, p4, p2), ccw(p1, p2, p3), ccw(p1, p2, p4)
        return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 and d2 and d3 and d4
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if inter(ring[i], ring[(i + 1) % n], ring[j], ring[(j + 1) % n]):
                return False
    return True


def _simplify_ring(ring: list[tuple[int, int]], max_vertices: int) -> tuple[list[tuple[int, int]], float]:
    far = max(range(len(ring)), key=lambda k: (ring[k][0] - ring[0][0]) ** 2 + (ring[k][1] - ring[0][1]) ** 2)
    part1, part2 = ring[:far + 1], ring[far:] + [ring[0]]

    def build(eps: float) -> list[tuple[int, int]]:
        a, b = _dp(part1, eps), _dp(part2, eps)
        return [part1[k] for k in a[:-1]] + [part2[k] for k in b[:-1]]
    lo, hi = 0.0, 400.0
    for _ in range(30):                                   # najmniejsza tolerancja dająca <= limit
        mid = (lo + hi) / 2
        if len(build(mid)) <= max_vertices:
            hi = mid
        else:
            lo = mid
    eps = hi
    need_simple = _simple(ring)                           # obrys wyjściowy nieprosty (BG1): nie wymagamy prostoty wyniku
    while eps < 400:
        cand = build(eps)
        if len(cand) >= 3 and (not need_simple or _simple(cand)):
            return cand, eps
        eps *= 1.05
    raise WedFormatError(f"nie udało się uprościć {len(ring)} wierzchołków do {max_vertices}")


def limit_polygon_vertices(w: Wed, max_vertices: int = 100) -> tuple[Wed, list[str]]:
    """IWD2 zgłasza assert ChVidPoly.cpp:546 ('Excessive poly vertex count') dla wielokąta ściany z 382 wierzchołkami
    (BG1 AR2600). Maksima w stockowych plikach IWD2: WED 44, ARE (regiony) 117 - limit 100 jest poniżej wartości
    sprawdzonych. Wielokąty powyżej limitu są upraszczane (Douglas-Peucker na zamkniętym obrysie, najmniejsza tolerancja
    spełniająca limit, bez samoprzecięć); bbox liczony od nowa; tabela wierzchołków przebudowana kolejno."""
    notes: list[str] = []
    new_polys, new_verts = [], []
    for i, p in enumerate(w.polygons):
        pts = list(w.vertices[p.start:p.start + p.n_vertices])
        if len(pts) > max_vertices:
            cand, eps = _simplify_ring(pts, max_vertices)
            notes.append(f"wielokąt {i}: {len(pts)} -> {len(cand)} wierzchołków (tolerancja {eps:.1f} px; limit IWD2, patrz ChVidPoly.cpp:546)")
            pts = cand
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        bbox = (min(xs), max(xs), min(ys), max(ys)) if pts else p.bbox
        new_polys.append(Polygon(p.flags, p.height, bbox, len(new_verts), len(pts)))
        new_verts.extend(pts)
    if not notes:
        return w, notes
    import dataclasses
    return dataclasses.replace(w, polygons=new_polys, vertices=new_verts), notes
