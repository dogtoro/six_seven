import os
import unittest

from adcdnet_infer import resolve_paths


class ResolvePathsTests(unittest.TestCase):
    def test_resolves_relative_record_paths_from_dataset_root(self):
        paths = [[r"..\dataset_sample\images\receipt.png", r"work\mask.png", r"work\ocr.png"]]
        resolved = resolve_paths(paths, r"C:\benchmark\dataset_sample")
        self.assertEqual(resolved, [[
            os.path.normpath(r"C:\benchmark\dataset_sample\..\dataset_sample\images\receipt.png"),
            os.path.normpath(r"C:\benchmark\dataset_sample\work\mask.png"),
            os.path.normpath(r"C:\benchmark\dataset_sample\work\ocr.png"),
        ]])

    def test_keeps_absolute_record_paths(self):
        paths = [[r"C:\data\image.png", r"C:\data\mask.png", r"C:\data\ocr.png"]]
        self.assertEqual(resolve_paths(paths, r"C:\other"), paths)


if __name__ == "__main__":
    unittest.main()
