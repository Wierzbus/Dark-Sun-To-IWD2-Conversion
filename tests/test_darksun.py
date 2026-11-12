"""Testy czytnikow Dark Sun na syntetycznych danych (bez plikow gry)."""
import struct
import unittest

from darksun.gff import Gff
from darksun.records import (CHAR, COMBAT, HDR, IT1R, ITEM, Character, Combat, Item, ItemType,
                             name_table, rdff_blocks)


def make_gff(plain: dict, segmented: dict) -> bytes:
    """plain: tag -> {id: bytes}; segmented: tag -> (first_id, [bytes...])."""
    body = bytearray()
    loc = 28

    def put(b):
        nonlocal body
        off = loc + len(body)
        body += b
        return off

    toc_types = []
    for tag, res in plain.items():
        toc_types.append((tag, [(rid, put(b), len(b)) for rid, b in res.items()]))
    gffi = []
    for n, (tag, (first, blobs)) in enumerate(segmented.items(), start=1):
        locs = [(put(b), len(b)) for b in blobs]
        tab = struct.pack("<I", len(locs)) + b"".join(struct.pack("<II", *x) for x in locs)
        gffi.append((n, put(tab), len(tab)))
    toc = bytearray(struct.pack("<IIH", 8, 0, len(toc_types) + len(segmented) + (1 if gffi else 0)))
    if gffi:
        toc += b"GFFI" + struct.pack("<I", len(gffi)) + b"".join(struct.pack("<III", *g) for g in gffi)
    for tag, ents in toc_types:
        toc += tag.encode() + struct.pack("<I", len(ents)) + b"".join(struct.pack("<III", *e) for e in ents)
    for n, (tag, (first, blobs)) in enumerate(segmented.items(), start=1):
        toc += tag.encode() + struct.pack("<IIIIII", 0x80000000 | len(blobs), len(blobs), n, 1, first, len(blobs))
    toc_loc = loc + len(body)
    head = struct.pack("<4sIIIIII", b"GFFI", 0x30000, 28, toc_loc, len(toc), 0, 0)
    return head + bytes(body) + bytes(toc)


def block(la, ty, ix, data):
    return HDR.pack(la, 0, ty, ix, 0, len(data)) + data


class GffTest(unittest.TestCase):
    def test_plain_and_segmented(self):
        g = Gff(make_gff({"NAME": {1: b"abc"}}, {"TILE": (5, [b"x", b"yy", b"zzz"])}))
        self.assertEqual(g.get("NAME", 1), b"abc")
        self.assertEqual([(i, b) for i, b in g.items("TILE")], [(5, b"x"), (6, b"yy"), (7, b"zzz")])

    def test_bad_magic(self):
        with self.assertRaises(ValueError):
            Gff(b"XXXX" + bytes(40))


class RecordsTest(unittest.TestCase):
    def test_creature_with_item(self):
        stats = bytes([13, 16, 15, 12, 17, 12])
        combat = COMBAT.pack(46, 0, 95, -5, 0, 0, 0, bytes(8), 0, 0, 0, 10, 12, 1, 4, 2, 12, 6, 0x20,
                             stats, b"Test\0".ljust(18, b"\0"))
        char = CHAR.pack(1000, 1400, 46, 45, 0, 2000, -83, bytes(6), 1, 1, 0, stats, b"\x0a\0\0",
                         b"\x09\0\0", 10, 12, 0, 3, b"\x02\0\0", b"\x01\0\0", b"\x02\0\0", bytes(3),
                         bytes([8, 10, 9, 9, 11]), 4, 0, 0, b"\x09\0\0", 0x43, 0, 0)
        item = ITEM.pack(-1013, 0, 0, 75, 0, 45, 0, 0, 4, 255, 28, 1)
        raw = block(1, 2, 95, combat) + block(3, 4, 95, char) + block(4, 1, 0, item) + b"\xff" + bytes(9)
        bl = rdff_blocks(raw)
        self.assertEqual([b.type for b in bl], [2, 4, 1])
        c = Combat.parse(bl[0].data)
        self.assertEqual((c.name, c.hp, c.ac, c.thac0, c.stats), ("Test", 46, 10, 12, tuple(stats)))
        h = Character.parse(bl[1].data)
        self.assertEqual((h.race, h.real_class, h.level, h.saving_throw), (1, (10, 0, 0), (9, 0, 0), (8, 10, 9, 9, 11)))
        i = Item.parse(bl[2].data)
        self.assertEqual((i.item_index, i.name_idx, i.bonus), (45, 28, 1))

    def test_missing_end(self):
        with self.assertRaises(ValueError):
            rdff_blocks(block(1, 1, 0, bytes(21)))

    def test_tables(self):
        t = ItemType.table(IT1R.pack(1, 0, 48, 30, 250, 3, 5, 1, 1, 8, 1, 0, 0, 0x167E, 0, 1) * 2)
        self.assertEqual((len(t), t[1].index, t[0].sides, t[0].dice, t[0].weight), (2, 1, 8, 1, 30))
        n = name_table(b"Miecz\0junk".ljust(22, b"\0") + struct.pack("<hB", 216, 255))
        self.assertEqual(n, [{"index": 0, "name": "Miecz", "icon": 216, "u_24": 255}])


class BmpTest(unittest.TestCase):
    def test_literal_and_run(self):
        from darksun.bmp import decode_frames, palette
        # klatka 4x2: y0: x0 n2 dosłownie (c=2 -> 2 px), x3 n1 (ostatni); y1: x0 n4: run 3 x 7 + 1 px
        frame = (struct.pack("<HH", 4, 2) + bytes([0, 0, 0, 2, 3, 2, 5, 6, 3, 0x80, 1, 2, 0, 9])
                 + bytes([1, 0, 0x80, 4, 4, 5, 7, 0, 8]) + b"\xff")
        b = struct.pack("<IHI", 10 + len(frame), 1, 10) + frame
        fr = decode_frames(b)[0]
        self.assertEqual((fr.width, fr.height), (4, 2))
        self.assertEqual([fr.pixels.get((x, 0)) for x in range(4)], [5, 6, None, 9])
        self.assertEqual([fr.pixels[(x, 1)] for x in range(4)], [7, 7, 7, 8])
        self.assertEqual(palette(bytes([63, 0, 0]) * 256)[0], (255, 0, 0))

    def test_codes(self):
        from darksun.codes import class_names, race_name
        self.assertEqual(race_name(1), "czlowiek")
        self.assertEqual(class_names((11, 10, 0), (1, 3, 0)), "zachowawca (preserver) 1 / gladiator 3")


class GplTextTest(unittest.TestCase):
    def test_roundtrip_and_merge(self):
        from darksun.gpltext import merged, pack7, scan
        b = (b"\x10\x4f\x00\x73\x92\x05" + pack7("Hello, ") + b"\x4f\x00\x73\x92\x05" + pack7("world.")
             + b"\x22\x4f\x00\x62\x92\x05" + pack7("A\tB") + b"\x92\x05\x00\x00")
        self.assertEqual([t.text for t in scan(b)], ["Hello, ", "world.", "A\tB"])
        m = merged(b)
        self.assertEqual([(t.text, t.buffer, t.parts) for t in m], [("Hello, world.", 0x73, 2), ("A\tB", 0x62, 1)])


if __name__ == "__main__":
    unittest.main()
