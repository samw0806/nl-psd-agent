import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"


class EvalRunnerTests(unittest.TestCase):
    def test_script_runner_executes_synthetic_case(self) -> None:
        generate = subprocess.run(
            [str(PYTHON), str(ROOT / "eval" / "generate_fixtures.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            generate.returncode,
            0,
            msg=f"fixture generation failed\nstdout:\n{generate.stdout}\nstderr:\n{generate.stderr}",
        )

        proc = subprocess.run(
            [
                str(PYTHON),
                str(ROOT / "eval" / "runner.py"),
                "--layer",
                "script",
                "--case",
                "script_info_simple_banner",
                "--format",
                "json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"runner failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        report = json.loads(proc.stdout)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 0)
