import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvalCaseLoadingTests(unittest.TestCase):
    def test_script_case_files_are_discoverable(self) -> None:
        from eval.lib import discover_cases

        cases = discover_cases(ROOT / "eval" / "cases" / "script")

        self.assertTrue(cases, "expected at least one script evaluation case")
        case_ids = {case["id"] for case in cases}
        self.assertIn("script_info_simple_banner", case_ids)
        self.assertIn("script_position_product", case_ids)
        self.assertIn("script_position_transparent_cutout", case_ids)

    def test_agent_case_files_are_discoverable(self) -> None:
        from eval.lib import discover_cases

        cases = discover_cases(ROOT / "eval" / "cases" / "agent")

        self.assertTrue(cases, "expected at least one agent evaluation case")
        self.assertIn("agent_open_and_describe_simple_banner", {case["id"] for case in cases})
