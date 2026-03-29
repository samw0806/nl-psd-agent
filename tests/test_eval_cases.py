import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvalCaseLoadingTests(unittest.TestCase):
    def test_script_case_files_are_discoverable(self) -> None:
        from eval.lib import discover_cases

        cases = discover_cases(ROOT / "eval" / "cases" / "script")

        self.assertTrue(cases, "expected at least one script evaluation case")
        self.assertIn("script_info_simple_banner", {case["id"] for case in cases})

    def test_agent_case_files_are_discoverable(self) -> None:
        from eval.lib import discover_cases

        cases = discover_cases(ROOT / "eval" / "cases" / "agent")

        self.assertTrue(cases, "expected at least one agent evaluation case")
        self.assertIn("agent_open_and_describe_simple_banner", {case["id"] for case in cases})
