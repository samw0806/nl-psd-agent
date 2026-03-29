import json
import shutil
import subprocess
import tempfile
from pathlib import Path


REQUIRED_CASE_KEYS = {
    "id",
    "layer",
    "input",
    "expected_behavior",
    "assertions",
    "tags",
}


def load_case_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_CASE_KEYS - set(data)
    if missing:
        missing_keys = ", ".join(sorted(missing))
        raise ValueError(f"case file {path} is missing required keys: {missing_keys}")
    data["_path"] = str(path)
    return data


def discover_cases(case_dir: Path) -> list[dict]:
    if not case_dir.exists():
        return []
    cases = [load_case_file(path) for path in sorted(case_dir.glob("*.yaml"))]
    return cases


def render_value(value, context: dict):
    if isinstance(value, str):
        return value.format_map(context)
    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    return value


def prepare_fixture(root: Path, case: dict, context: dict) -> tuple[Path | None, str | None]:
    fixture = case.get("fixture")
    if not fixture:
        return None, None

    source = root / fixture["source"]
    if not source.exists():
        if fixture.get("allow_missing"):
            return None, f"fixture missing locally: {source}"
        raise FileNotFoundError(source)

    if fixture.get("copy_to_temp", False):
        target = Path(context["workdir"]) / source.name
        shutil.copy2(source, target)
        return target, None

    return source, None


def build_context(root: Path, case: dict) -> dict:
    workdir = Path(tempfile.mkdtemp(prefix=f"nl_psd_eval_{case['id']}_"))
    context = {
        "root": str(root),
        "workdir": str(workdir),
        "case_id": case["id"],
    }

    for key, value in case.get("paths", {}).items():
        context[key] = render_value(value, context)

    fixture_path, skip_reason = prepare_fixture(root, case, context)
    if skip_reason:
        context["skip_reason"] = skip_reason
        return context

    if fixture_path is not None:
        context["fixture_path"] = str(fixture_path)
    return context


def run_command(command_spec: dict, context: dict) -> dict:
    rendered = render_value(command_spec, context)
    command = rendered["command"]
    cwd = rendered.get("cwd", context["root"])
    proc = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "cwd": cwd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _assert_contains(haystack: str, needles: list[str], label: str, errors: list[str]) -> None:
    for needle in needles:
        if needle not in haystack:
            errors.append(f"{label} missing substring: {needle}")


def evaluate_assertions(assertions: dict, result: dict, context: dict) -> list[str]:
    errors: list[str] = []

    if "exit_code" in assertions and result["returncode"] != assertions["exit_code"]:
        errors.append(
            f"expected exit code {assertions['exit_code']}, got {result['returncode']}"
        )

    _assert_contains(result["stdout"], assertions.get("stdout_contains", []), "stdout", errors)
    _assert_contains(result["stderr"], assertions.get("stderr_contains", []), "stderr", errors)

    if assertions.get("stderr_empty") and result["stderr"].strip():
        errors.append("stderr expected to be empty")

    for raw_path in assertions.get("files_exist", []):
        path = Path(render_value(raw_path, context))
        if not path.exists():
            errors.append(f"expected file to exist: {path}")

    for raw_path, min_size in assertions.get("files_min_size", {}).items():
        path = Path(render_value(raw_path, context))
        if not path.exists():
            errors.append(f"expected file to exist: {path}")
            continue
        if path.stat().st_size < min_size:
            errors.append(
                f"expected file {path} to be at least {min_size} bytes, got {path.stat().st_size}"
            )

    return errors


def run_followup_commands(assertions: dict, context: dict) -> tuple[list[dict], list[str]]:
    followup_results: list[dict] = []
    errors: list[str] = []

    for command_spec in assertions.get("followup_commands", []):
        followup = run_command(command_spec, context)
        followup_results.append(followup)
        errors.extend(evaluate_assertions(command_spec.get("assertions", {}), followup, context))

    return followup_results, errors

