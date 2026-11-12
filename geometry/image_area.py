"""Obraz (PNG/RGB) + mapy SR/HT/LM -> kompletny obszar: TIS, WED (ściany z mapy SR),
ARE V9.1 z jednym wejściem, MOS (minimapa), BMP map, install.tph.

Użycie: python -m geometry.image_area --dir areas_custom/AR9020 --name AR9020 [--out KATALOG_BUILD]
Katalog --dir: obraz.png, SR.BMP, HT.BMP, LM.BMP (autorskie, wersjonowane w Git).
Obraz dopełniany do wielokrotności 64 (powtórzenie ostatniego wiersza/kolumny).
Kafle identyczne są scalane. Indeks 0 palety = (0,255,0) (klucz przezroczystości),
kolory obrazu zajmują indeksy 1..255; przy >255 kolorach w kaflu - kwantyzacja.
"""
from __future__ import annotations
import argparse, os, sys, struct
import cv2
import numpy as np
from PIL import Image
from .tis import Tis, write_tis, require_tiles
from .wed import (Wed, Overlay, Cell, Polygon, write_wed, parse_wed, check_wed, expected_wall_groups,
                  limit_polygon_vertices, SLOTS)
from . import maps as M, mos, are_skeleton as AS


def slice_tiles(img: Image.Image):
    a = np.asarray(img.convert("RGB"))
    H, W, _ = a.shape
    tw, th = -(-W // 64), -(-H // 64)
    a = np.pad(a, ((0, th * 64 - H), (0, tw * 64 - W), (0, 0)), mode="edge")
    return a, tw, th


def tile_bytes(t: np.ndarray) -> bytes:
    flat = t.reshape(-1, 3)
    cols, inv = np.unique(flat, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    if len(cols) > 255:
        q = Image.fromarray(t).quantize(255, dither=Image.NONE)
        pal = np.array(q.getpalette()[:765], np.uint8).reshape(-1, 3)
        idx = np.asarray(q).reshape(-1)
        cols = pal[:255]
        inv = idx
    pal = bytearray(1024)
    pal[0:4] = bytes((0, 255, 0, 0))
    for i, (r, g, b) in enumerate(cols):
        pal[(i + 1) * 4:(i + 2) * 4] = bytes((int(b), int(g), int(r), 0))
    return bytes(pal) + (inv.astype(np.uint8) + 1).tobytes()


def build(img: Image.Image, name: str, sr: 'M.Bmp | None' = None, walls: 'np.ndarray | None' = None):
    a, tw, th = slice_tiles(img)
    uniq, order, lookup = {}, [], []
    for ty in range(th):
        for tx in range(tw):
            b = tile_bytes(a[ty * 64:(ty + 1) * 64, tx * 64:(tx + 1) * 64])
            if b not in uniq:
                uniq[b] = len(order); order.append(b)
            lookup.append(uniq[b])
    tis = Tis(b"".join(order))
    base = Overlay(tw, th, name, 0, 0,
                   [Cell(i, 1, 0xFFFF, 0) for i in range(tw * th)], lookup)
    ovs = [base] + [Overlay(0, 0, "") for _ in range(SLOTS - 1)]
    if walls is not None:
        polys = polygons_from_mask(walls)
    else:
        polys = wall_polygons(sr, tw * 64, th * 64) if sr is not None else []
    w = assemble_walls(ovs, polys, tw, th)
    return tis, w


CELL_W, CELL_H = 16, 12          # komórka mapy SR/HT/LM w pikselach
MAX_VERTS = 44                   # maksimum w stockowych WED IWD2 (patrz wed.limit_polygon_vertices)
MIN_AREA = 600                   # px^2: mniejsze plamy nie dostają ściany
EPS = 5.0                        # tolerancja uproszczenia obrysu [px]


def _split(mask: np.ndarray, x0: int, y0: int, out: list):
    """Obrys każdego komponentu maski. Komponent dzielony na pół (po dłuższym boku ramki), gdy obrys ma
    > MAX_VERTS wierzchołków albo wypełniony obrys zakrywałby dziury (pokoje w pierścieniu murów)."""
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cs:
        if cv2.contourArea(c) < MIN_AREA:
            continue
        ring = cv2.approxPolyDP(c, EPS, True).reshape(-1, 2)
        if len(ring) < 3:
            continue
        bx, by, bw, bh = cv2.boundingRect(c)
        filled = np.zeros((bh, bw), np.uint8)
        cv2.drawContours(filled, [c - np.array([bx, by])], -1, 1, thickness=cv2.FILLED)
        real = (mask[by:by + bh, bx:bx + bw] > 0).astype(np.uint8) & filled
        holey = real.sum() < 0.9 * filled.sum()
        if len(ring) <= MAX_VERTS and not holey:
            out.append([(int(x) + x0, int(y) + y0) for x, y in ring])
            continue
        if max(bw, bh) < 24:
            hull = cv2.approxPolyDP(cv2.convexHull(c), EPS * 2, True).reshape(-1, 2)
            out.append([(int(x) + x0, int(y) + y0) for x, y in hull[:MAX_VERTS]])
            continue
        if bw >= bh:
            m = bw // 2
            _split(real[:, :m], x0 + bx, y0 + by, out)
            _split(real[:, m:], x0 + bx + m, y0 + by, out)
        else:
            m = bh // 2
            _split(real[:m, :], x0 + bx, y0 + by, out)
            _split(real[m:, :], x0 + bx, y0 + by + m, out)


BAND = 110                       # px: sylwetki scian dalej od podlogi nie zaslaniaja nikogo


def polygons_from_mask(mask: np.ndarray) -> list:
    """Wielokaty scian z maski sylwetki (sciany.png): tylko pas BAND px wokol podlogi, wygladzenie, obrysy."""
    m = (mask > 0).astype(np.uint8)
    floor = cv2.dilate((1 - m).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * BAND + 1, 2 * BAND + 1)))
    m = m & floor
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    out: list = []
    _split(m, 0, 0, out)
    return out


def wall_polygons(sr: "M.Bmp", width: int, height: int) -> list[list[tuple[int, int]]]:
    """Obrysy komórek SR == 0 (ściana: klify/skały) jako wielokąty ścian w pikselach obszaru."""
    cells = np.frombuffer(sr.pixels, np.uint8).reshape(sr.height, sr.width)
    px = np.kron((cells == 0).astype(np.uint8), np.ones((CELL_H, CELL_W), np.uint8))
    px = px[:height, :width]
    px = np.pad(px, ((0, height - px.shape[0]), (0, width - px.shape[1])))
    px = cv2.morphologyEx(px, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))   # wygładzenie schodków
    out: list = []
    _split(px, 0, 0, out)
    return out


def assemble_walls(ovs, polys, tw, th) -> Wed:
    """Tabele wielokątów, wierzchołków i grup ścian (grupa 10 x 7,5 kafla = 640 x 480 px, wierszami)."""
    polygons, verts = [], []
    for ring in polys:
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        polygons.append(Polygon(0, 255, (min(xs), max(xs), min(ys), max(ys)), len(verts), len(ring)))
        verts.extend(ring)
    gw = -(-tw // 10)
    gh = -(-th * 2 // 15)
    pidx, groups = [], []
    for gy in range(gh):
        for gx in range(gw):
            x0, x1, y0, y1 = gx * 640, (gx + 1) * 640, gy * 480, (gy + 1) * 480
            ids = [i for i, p in enumerate(polygons)
                   if p.bbox[0] < x1 and p.bbox[1] >= x0 and p.bbox[2] < y1 and p.bbox[3] >= y0]
            groups.append((len(pidx), len(ids))); pidx.extend(ids)
    w = Wed(ovs, [], [], groups, polygons, len(polygons), pidx, verts)
    return w


def entrance_point(sr: "M.Bmp") -> tuple[int, int]:
    """Środek największej otwartej przestrzeni (SR != 0,8 w promieniu 4 komórek), blisko środka mapy."""
    c = np.frombuffer(sr.pixels, np.uint8).reshape(sr.height, sr.width)
    ok = ((c != 0) & (c != 8)).astype(np.uint8)
    dist = cv2.distanceTransform(ok, cv2.DIST_L2, 3)
    yy, xx = np.mgrid[0:sr.height, 0:sr.width]
    score = np.where(dist >= 4, -((xx - sr.width / 2) ** 2 + (yy - sr.height * 0.6) ** 2), -1e18)
    y, x = np.unravel_index(int(np.argmax(score)), score.shape)
    return int(x) * CELL_W + CELL_W // 2, int(y) * CELL_H + CELL_H // 2


def build_area(src: str, name: str, out_root: str) -> dict:
    img = Image.open(os.path.join(src, "obraz.png")).convert("RGB")
    bm = {k: M.read_bmp(open(os.path.join(src, k + ".BMP"), "rb").read(), name=k) for k in ("SR", "HT", "LM")}
    sp = os.path.join(src, "sciany.png")
    walls = np.asarray(Image.open(sp).convert("L")) if os.path.exists(sp) else None
    if walls is not None and walls.shape != (-(-img.height // 64) * 64, -(-img.width // 64) * 64):
        sys.exit(f"sciany.png {walls.shape} nie pasuje do obrazu {img.size}")
    tis, w = build(img, name, bm["SR"], walls)
    w, notes = limit_polygon_vertices(w, MAX_VERTS)
    bad = check_wed(w, tile_count=tis.count)
    require_tiles(tis, max(w.base.lookup))
    if bad:
        sys.exit("WED: " + "; ".join(bad))
    wed_b = write_wed(w)
    check_wed(parse_wed(wed_b), tile_count=tis.count)
    ent = entrance_point(bm["SR"])
    are_b = AS.build_are(name, AS.SkeletonSource(area_flags_bit0=0, area_type=7), entrance=ent)
    AS.parse_skeleton(are_b)
    files = {f"{name}.TIS": write_tis(tis), f"{name}.WED": wed_b, f"{name}.ARE": are_b,
             f"{name}.MOS": mos.write_mos(mos.build_minimap(img))}
    for k in ("SR", "HT", "LM"):
        files[f"{name}{k}.BMP"] = M.write_bmp(bm[k])
    dest = os.path.join(out_root, name)
    os.makedirs(dest, exist_ok=True)
    for n, b in files.items():
        open(os.path.join(dest, n), "wb").write(b)
    names = " ".join(f"~{n}~" for n in sorted(files))
    open(os.path.join(dest, "install.tph"), "w", encoding="latin-1").write(
        "// WYGENEROWANE przez geometry.image_area - nie edytowac recznie.\n"
        f"ACTION_FOR_EACH file IN {names} BEGIN\n"
        f"  ACTION_IF NOT FILE_EXISTS ~iwd2_nowe_lokacje/build/{name}/%file%~ BEGIN\n"
        f"    FAIL ~Brak iwd2_nowe_lokacje/build/{name}/%file% - uruchom: python -m geometry.image_area~\n"
        "  END\n"
        f"  COPY_LARGE ~iwd2_nowe_lokacje/build/{name}/%file%~ ~override/%file%~\n"
        "END\n")
    return {"name": name, "tiles": (w.base.width, w.base.height), "unique": tis.count,
            "polygons": len(w.polygons), "vertices": len(w.vertices), "entrance": ent, "notes": notes}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--out", default="mod/iwd2_nowe_lokacje/build")
    o = ap.parse_args(argv)
    r = build_area(o.dir, o.name, o.out)
    print(r)


if __name__ == "__main__":
    main()


