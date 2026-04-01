import tempfile
import unittest
from pathlib import Path

from backend.tools import execute_tool


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "eval" / "fixtures" / "simple_banner.psd"


class BackendToolsTests(unittest.TestCase):
    def test_set_layer_position_executes_script(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nl_psd_backend_position_") as tmpdir:
            input_psd = Path(tmpdir) / "simple_banner.psd"
            input_psd.write_bytes(FIXTURE.read_bytes())

            output = execute_tool(
                "set_layer_position",
                {
                    "psd_path": str(input_psd),
                    "layer_path": "Body/ProductShot",
                    "dx": 15,
                    "dy": -8,
                },
            )

            self.assertIn("新位置: left=535, top=80", output)

            info_output = execute_tool("get_psd_info", {"psd_path": str(input_psd)})
            self.assertIn("位置:(535,80)", info_output)
