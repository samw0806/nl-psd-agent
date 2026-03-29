import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.lib import build_context, discover_cases, evaluate_assertions, run_command, run_followup_commands


ROOT = Path(__file__).resolve().parents[1]


def summarize(results: list[dict]) -> dict:
    counts = {"passed": 0, "failed": 0, "skipped": 0, "manual": 0}
    for result in results:
        counts[result["status"]] += 1
    counts["total"] = len(results)
    return counts


def evaluate_script_case(case: dict) -> dict:
    context = build_context(ROOT, case)
    if "skip_reason" in context:
        return {
            "case_id": case["id"],
            "status": "skipped",
            "reason": context["skip_reason"],
            "workdir": context["workdir"],
        }

    setup_results = []
    for setup in case.get("setup", []):
        setup_result = run_command(setup, context)
        setup_results.append(setup_result)
        setup_errors = evaluate_assertions(setup.get("assertions", {}), setup_result, context)
        if setup_errors:
            return {
                "case_id": case["id"],
                "status": "failed",
                "stage": "setup",
                "errors": setup_errors,
                "setup": setup_results,
                "workdir": context["workdir"],
            }

    main_result = run_command(case["input"], context)
    errors = evaluate_assertions(case["assertions"], main_result, context)
    followups, followup_errors = run_followup_commands(case["assertions"], context)
    errors.extend(followup_errors)

    return {
        "case_id": case["id"],
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "setup": setup_results,
        "result": main_result,
        "followups": followups,
        "workdir": context["workdir"],
        "tags": case["tags"],
    }


def evaluate_agent_case(case: dict) -> dict:
    return {
        "case_id": case["id"],
        "status": "manual",
        "prompt": case["input"]["prompt"],
        "checks": case["assertions"].get("human_checks", []),
        "tags": case["tags"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run NL-PSD Agent evaluation cases")
    parser.add_argument("--layer", choices=["script", "agent"], required=True)
    parser.add_argument("--case", help="Run only one case by id")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    cases = discover_cases(ROOT / "eval" / "cases" / args.layer)
    if args.case:
        cases = [case for case in cases if case["id"] == args.case]

    if not cases:
        print("No cases matched", file=sys.stderr)
        return 2

    results = []
    evaluator = evaluate_script_case if args.layer == "script" else evaluate_agent_case
    for case in cases:
        results.append(evaluator(case))

    report = {
        "layer": args.layer,
        "summary": summarize(results),
        "results": results,
    }

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Layer: {report['layer']}")
        print(f"Summary: {report['summary']}")
        for result in results:
            print(f"- {result['case_id']}: {result['status']}")
            if result.get("errors"):
                for error in result["errors"]:
                    print(f"  error: {error}")
            if result.get("reason"):
                print(f"  reason: {result['reason']}")

    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
