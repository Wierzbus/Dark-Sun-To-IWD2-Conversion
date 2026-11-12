"""Build obu lokacji do katalogu tymczasowego: WED/ARE przechodza wlasne kontrole."""
import os, tempfile, unittest
from geometry import image_area, wed, are_skeleton

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ImageAreaBuild(unittest.TestCase):
    def test_areas(self):
        with tempfile.TemporaryDirectory() as out:
            for name in ("AR9020", "AR9021"):
                r = image_area.build_area(os.path.join(ROOT, "areas_custom", name), name, out)
                d = os.path.join(out, name)
                w = wed.parse_wed(open(os.path.join(d, name + ".WED"), "rb").read())
                self.assertEqual(wed.check_wed(w), [])
                self.assertTrue(all(len(p.vertices) <= image_area.MAX_VERTS for p in w.polygons)
                                if hasattr(w.polygons[0], "vertices") else True)
                are_skeleton.parse_skeleton(open(os.path.join(d, name + ".ARE"), "rb").read())
                self.assertGreater(r["polygons"], 0)


if __name__ == "__main__":
    unittest.main()
