"""Dodaje kontrolke do okna CHU (kopia istniejacej kontrolki z nowym id i pozycja).

Uzycie (przycisk bostwa kaplana w oknie 12 kreatora):
  python tools/iwd2_chu_kontrolka.py GUICG.CHU WYJ.CHU --okno 12 --wzor 9 --id 14 --dy 63
"""
import argparse
import struct


def czytaj(d):
    nw, co, wo = struct.unpack_from("<III", d, 8)
    okna = []
    for w in range(nw):
        rec = bytearray(d[wo + w * 28: wo + w * 28 + 28])
        nc, fc = struct.unpack_from("<HH", rec, 14)[0], struct.unpack_from("<H", rec, 24)[0]
        ktr = []
        for c in range(fc, fc + nc):
            off, ln = struct.unpack_from("<II", d, co + c * 8)
            ktr.append(bytearray(d[off:off + ln]))
        okna.append([rec, ktr])
    return d[:8], okna


def zapisz(sig, okna):
    nw = len(okna)
    wsz = sum(len(k) for _, k in okna)
    wo = 0x14
    co = wo + nw * 28
    dane_off = co + wsz * 8
    okna_b, tab_b, dane_b = b"", b"", b""
    idx = 0
    for rec, ktr in okna:
        rec = bytearray(rec)
        struct.pack_into("<H", rec, 14, len(ktr))
        struct.pack_into("<H", rec, 24, idx)
        okna_b += rec
        for k in ktr:
            tab_b += struct.pack("<II", dane_off + len(dane_b), len(k))
            dane_b += k
            idx += 1
    return sig + struct.pack("<III", nw, co, wo) + okna_b + tab_b + dane_b


def dodaj(d, okno, wzor, nowe_id, dx=0, dy=0):
    sig, okna = czytaj(d)
    for rec, ktr in okna:
        if struct.unpack_from("<H", rec, 0)[0] != okno:
            continue
        if any(struct.unpack_from("<I", k, 0)[0] & 0xFFFF == nowe_id for k in ktr):
            return d  # juz jest
        w = next(k for k in ktr if struct.unpack_from("<I", k, 0)[0] & 0xFFFF == wzor)
        n = bytearray(w)
        cid = struct.unpack_from("<I", n, 0)[0]
        struct.pack_into("<I", n, 0, (cid & 0xFFFF0000) | nowe_id)
        x, y = struct.unpack_from("<HH", n, 4)
        struct.pack_into("<HH", n, 4, x + dx, y + dy)
        ktr.append(n)
        return zapisz(sig, okna)
    raise ValueError("brak okna %d" % okno)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wej")
    ap.add_argument("wyj")
    ap.add_argument("--okno", type=int, required=True)
    ap.add_argument("--wzor", type=int, required=True)
    ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--dx", type=int, default=0)
    ap.add_argument("--dy", type=int, default=0)
    a = ap.parse_args()
    d = open(a.wej, "rb").read()
    open(a.wyj, "wb").write(dodaj(d, a.okno, a.wzor, a.id, a.dx, a.dy))


if __name__ == "__main__":
    main()
