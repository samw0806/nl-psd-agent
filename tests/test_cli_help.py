import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"


class CliHelpTests(unittest.TestCase):
    def assert_help_works(self, script_name: str) -> None:
        proc = subprocess.run(
            [str(PYTHON), str(ROOT / "scripts" / script_name), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"{script_name} --help failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        self.assertIn("usage:", proc.stdout.lower())

    def test_opacity_help(self) -> None:
        self.assert_help_works("opacity.py")

    def test_add_layer_help(self) -> None:
        self.assert_help_works("add_layer.py")

    def test_resample_layer_help(self) -> None:
        self.assert_help_works("resample_layer.py")

    def test_position_layer_help(self) -> None:
        self.assert_help_works("position_layer.py")
