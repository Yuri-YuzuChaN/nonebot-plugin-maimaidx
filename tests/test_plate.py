import importlib.util
import tempfile
import unittest
from pathlib import Path

# Import the filesystem helper without starting the NoneBot plugin or its jobs.
_MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "nonebot_plugin_maimaidx/core/image/plate.py"
)
_SPEC = importlib.util.spec_from_file_location("maimaidx_plate", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
resolve_plate_path = _MODULE.resolve_plate_path


class ResolvePlatePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "plate_version"
        self.directory.mkdir()
        self.default = self.root / "default.png"
        self.default.touch()

    def resolve(self, name):
        return resolve_plate_path(name, self.directory, self.default)

    def test_exact_name_takes_precedence_over_alias(self):
        exact = self.directory / "鏡極.png"
        exact.touch()
        (self.directory / "镜極.png").touch()
        self.assertEqual(self.resolve("鏡極"), exact)

    def test_known_character_variants(self):
        pairs = (
            ("鏡極", "镜極"),
            ("鏡神", "镜神"),
            ("鏡将", "镜将"),
            ("鏡舞舞", "镜舞舞"),
            ("雙極", "双極"),
            ("晓極", "暁極"),
            ("曉極", "暁極"),
            ("樱極", "櫻極"),
            ("堇極", "菫極"),
            ("辉極", "輝極"),
            ("华極", "華極"),
            ("镜极", "镜極"),
            ("鏡將", "镜将"),
        )
        for name, spelling in pairs:
            with self.subTest(name=name):
                asset = self.directory / f"{spelling}.png"
                asset.touch()
                self.assertEqual(self.resolve(name), asset)

    def test_existing_unmapped_name_is_preserved(self):
        asset = self.directory / "custom.png"
        asset.touch()
        self.assertEqual(self.resolve("custom"), asset)

    def test_missing_name_uses_default(self):
        for name in ("鏡極", "unknown", ""):
            with self.subTest(name=name):
                self.assertEqual(self.resolve(name), self.default)

    def test_directory_is_not_an_image(self):
        (self.directory / "鏡極.png").mkdir()
        self.assertEqual(self.resolve("鏡極"), self.default)

    def test_missing_asset_directory_uses_default(self):
        self.directory.rmdir()
        self.assertEqual(self.resolve("鏡極"), self.default)

    def test_names_cannot_select_files_outside_asset_directory(self):
        (self.root / "outside.png").touch()
        for name in ("../outside", "..\\outside", "/outside", "bad\0name"):
            with self.subTest(name=name):
                self.assertEqual(self.resolve(name), self.default)


if __name__ == "__main__":
    unittest.main()
