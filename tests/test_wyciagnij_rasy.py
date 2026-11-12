"""Skrypt wyciagania plikow ras na sztucznej instalacji (KEY + BIF + override)."""
import os
import struct
import tempfile
import unittest
import zipfile

from inventory.resource_reader import normalize_type
from tools.wyciagnij_rasy import main


def _key(bifs, resources):
    off_bif = 0x18
    pos = off_bif + 12 * len(bifs)
    names, entries = [], []
    for name, length, flags in bifs:
        blob = name.encode() + b"\0"
        entries.append(struct.pack("<IIHH", length, pos, len(blob), flags))
        names.append(blob)
        pos += len(blob)
    res = b"".join(struct.pack("<8sHI", n.encode().ljust(8, b"\0"), t, loc) for n, t, loc in resources)
    return (struct.pack("<4s4sIIII", b"KEY ", b"V1  ", len(bifs), len(resources), off_bif, pos)
            + b"".join(entries) + b"".join(names) + res)


def _biff(files):
    pos, blobs, ent = 0x14, [], []
    for idx, t, data in files:
        ent.append(struct.pack("<IIIHH", idx, pos, len(data), t, 0))
        blobs.append(data)
        pos += len(data)
    return struct.pack("<4s4sIII", b"BIFF", b"V1  ", len(files), 0, pos) + b"".join(blobs) + b"".join(ent)


class WyciagnijRasy(unittest.TestCase):
    def test_zip(self):
        t = normalize_type
        files = [(0, t("2da"), b"SRLIST"), (1, t("ids"), b"SUBRACE"), (2, t("chu"), b"CHUI"),
                 (3, t("2da"), b"SPCH_T"), (4, t("2da"), b"ITEMS"), (5, t("2da"), b"KITLIST"), (6, t("2da"), b"CLABPA01")]
        names = ["SRLIST", "SUBRACE", "GUICG", "SPCH_T", "ITEMS", "KITLIST", "CLABPA01"]
        with tempfile.TemporaryDirectory() as g:
            os.makedirs(f"{g}/data")
            os.makedirs(f"{g}/override")
            with open(f"{g}/data/a.bif", "wb") as f:
                f.write(_biff(files))
            with open(f"{g}/chitin.key", "wb") as f:
                f.write(_key([("data\\a.bif", 0, 1)], [(n, ty, i) for n, (i, ty, _) in zip(names, files)]))
            with open(f"{g}/override/ABRACEAD.2DA", "wb") as f:
                f.write(b"OVR")
            out = f"{g}/x.zip"
            main(["--game-dir", g, "--out", out])
            z = zipfile.ZipFile(out)
            self.assertEqual(sorted(z.namelist()),
                             ["ABRACEAD.2DA", "CLABPA01.2DA", "GUICG.CHU", "KITLIST.2DA", "SPCH_T.2DA", "SPIS.txt", "SRLIST.2DA", "SUBRACE.IDS"])
            self.assertEqual(z.read("ABRACEAD.2DA"), b"OVR")
            self.assertIn("Nie znaleziono: ABRACERQ.2DA", z.read("SPIS.txt").decode())


if __name__ == "__main__":
    unittest.main()
