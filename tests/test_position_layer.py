import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
FIXTURE = ROOT / "eval" / "fixtures" / "simple_banner.psd"
sys.path.insert(0, str(ROOT / "scripts"))
import _utils  # noqa: E402
from psd_tools import PSDImage  # noqa: E402


class PositionLayerScriptTests(unittest.TestCase):
    def _create_transparent_cutout_psd(self, path: Path) -> None:
        psd = PSDImage.new(mode="RGB", size=(500, 300), depth=8)
        background = Image.new("RGBA", (500, 300), (240, 240, 240, 255))
        psd.append(psd.create_pixel_layer(background, name="Background", top=0, left=0))

        cutout = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
        draw = ImageDraw.Draw(cutout)
        draw.ellipse((20, 20, 160, 160), fill=(200, 0, 0, 255))
        draw.rectangle((80, 0, 100, 179), fill=(255, 215, 0, 180))
        psd.append(psd.create_pixel_layer(cutout, name="Cutout", top=60, left=260))
        psd.save(path)

    def test_moves_leaf_layer_by_delta(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nl_psd_position_") as tmpdir:
            input_psd = Path(tmpdir) / "simple_banner.psd"
            output_psd = Path(tmpdir) / "moved.psd"
            input_psd.write_bytes(FIXTURE.read_bytes())

            proc = subprocess.run(
                [
                    str(PYTHON),
                    str(ROOT / "scripts" / "position_layer.py"),
                    str(input_psd),
                    "Body/ProductShot",
                    "--dx",
                    "40",
                    "--dy",
                    "20",
                    "--output",
                    str(output_psd),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                proc.returncode,
                0,
                msg=f"position_layer failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            self.assertIn("旧位置: left=520, top=88", proc.stdout)
            self.assertIn("新位置: left=560, top=108", proc.stdout)

            info = subprocess.run(
                [str(PYTHON), str(ROOT / "scripts" / "info.py"), str(output_psd)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                info.returncode,
                0,
                msg=f"info failed\nstdout:\n{info.stdout}\nstderr:\n{info.stderr}",
            )
            self.assertIn("ProductShot", info.stdout)
            self.assertIn("位置:(560,108)", info.stdout)

    def test_rejects_group_layer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nl_psd_position_group_") as tmpdir:
            input_psd = Path(tmpdir) / "simple_banner.psd"
            input_psd.write_bytes(FIXTURE.read_bytes())

            proc = subprocess.run(
                [
                    str(PYTHON),
                    str(ROOT / "scripts" / "position_layer.py"),
                    str(input_psd),
                    "Body",
                    "--dx",
                    "10",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("组图层", proc.stderr)

    def test_moves_transparent_pixel_layer_without_desyncing_mask(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nl_psd_position_alpha_") as tmpdir:
            input_psd = Path(tmpdir) / "alpha.psd"
            output_psd = Path(tmpdir) / "moved.psd"
            exported_png = Path(tmpdir) / "moved.png"
            self._create_transparent_cutout_psd(input_psd)

            proc = subprocess.run(
                [
                    str(PYTHON),
                    str(ROOT / "scripts" / "position_layer.py"),
                    str(input_psd),
                    "Cutout",
                    "--dx",
                    "-120",
                    "--dy",
                    "20",
                    "--output",
                    str(output_psd),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                proc.returncode,
                0,
                msg=f"position_layer failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )

            export = subprocess.run(
                [
                    str(PYTHON),
                    str(ROOT / "scripts" / "export.py"),
                    str(output_psd),
                    str(exported_png),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                export.returncode,
                0,
                msg=f"export failed\nstdout:\n{export.stdout}\nstderr:\n{export.stderr}",
            )

            moved = PSDImage.open(output_psd)
            layer = next(child for child in moved if child.name == "Cutout")
            self.assertTrue(layer.has_mask(), "transparent pixel layer should keep its user mask")
            self.assertEqual(layer.bbox, (140, 80, 320, 260))
            self.assertEqual(layer.mask.bbox, layer.bbox)

            image = Image.open(exported_png).convert("RGBA")
            black_opaque_pixels = 0
            for y in range(image.height):
                for x in range(image.width):
                    if image.getpixel((x, y)) == (0, 0, 0, 255):
                        black_opaque_pixels += 1

            self.assertEqual(black_opaque_pixels, 0, "moving the layer should not introduce black fill")
