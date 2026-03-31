import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BackendImportTests(unittest.TestCase):
    def test_backend_is_explicit_package_and_main_exports_app(self) -> None:
        backend_pkg = importlib.import_module("backend")
        self.assertEqual(Path(backend_pkg.__file__), ROOT / "backend" / "__init__.py")

        main_module = importlib.import_module("backend.main")
        self.assertTrue(hasattr(main_module, "app"))
