"""Fresh, scoped MVP checks without rewriting historical validation evidence.

The old R7 verifier deliberately binds the pre-repair web app. Its identity gate
is retained; this additive entry point verifies the authorized MVP repair and
all other protected bytes. Standard-library orchestration only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OLD_FOLDERS = ("tests_r3", "tests_r4", "tests_r5", "tests_r6", "tests_r7")
R7_SOURCE_RECEIPT = "evidence/r7/20261005T004048234257Z/verification.json"
R6_SOURCE_RECEIPT = "evidence/r6/20261004T104558015957Z.json"
SAVE_CASE_IDS = {
    "MVP-SAVE-TYPING-REVISION", "MVP-SAVE-UNCHANGED-CANONICAL",
    "MVP-CREATE-TYPING-ACK", "MVP-OLD-SAVE-RESET-SWITCH",
    "MVP-DIRTY-CURRENT-REOPEN-CANCEL", "MVP-DIRTY-REFRESHED-REOPEN-CANCEL",
    "MVP-OLD-CREATE-AFTER-RESET",
}
IMPORT_CASE_IDS = {
    "MVP-IMPORT-A-FIRST-B-LATEST", "MVP-IMPORT-B-FIRST-B-LATEST", "MVP-IMPORT-CLEARED-SELECTION",
    "MVP-IMPORT-SESSION-SWITCH", "MVP-IMPORT-DIRTY-CANCEL",
    "MVP-IMPORT-STALE-PARSE-ERROR", "MVP-IMPORT-STALE-READ-ERROR",
}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    value = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(out: Path, name: str, value: dict) -> None:
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                     allow_nan=False) + "\n", encoding="utf-8")


def historical_evidence() -> dict[str, str]:
    return {p.relative_to(ROOT).as_posix(): sha(p)
            for p in sorted((ROOT / "evidence").rglob("*"))
            if p.is_file() and "mvp" not in p.relative_to(ROOT / "evidence").parts}


def manifest_hash(values: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def preservation_gate() -> dict:
    frozen = read_json(ROOT / "FREEZE_MANIFEST.json")["payload_sha256"]
    frozen_errors = [p for p, expected in frozen.items()
                     if not (ROOT / p).is_file() or sha(ROOT / p) != expected]
    tree = read_json(ROOT / "evidence/r7/baseline-tree.json")["tree"]
    historical = [row for row in tree if row["type"] == "blob"
                  and row["path"] != "CURRENT_HANDOFF.md"]
    differences = [row["path"] for row in historical
                   if not (ROOT / row["path"]).is_file()
                   or git_blob(ROOT / row["path"]) != row["sha"]]
    protected_errors = [p for p in differences if p != "web_r4/app.js"]
    r7_sources = read_json(ROOT / R7_SOURCE_RECEIPT)["source_sha256"]
    r7_errors = [p for p, expected in r7_sources.items()
                 if not (ROOT / p).is_file() or sha(ROOT / p) != expected]
    pinned_paths = {row["path"] for row in historical} | set(r7_sources)
    test_file_set_errors = []
    for folder in OLD_FOLDERS:
        expected = {p for p in pinned_paths if p.startswith(folder + "/")}
        actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts}
        if actual != expected:
            test_file_set_errors.append({"folder": folder, "added": sorted(actual - expected),
                                         "missing": sorted(expected - actual)})
    return {
        "status": "PASS" if len(frozen) == 27 and not frozen_errors
                  and not protected_errors and not r7_errors
                  and not test_file_set_errors else "FAIL",
        "frozen_payload_files": len(frozen), "frozen_errors": frozen_errors,
        "historical_r0_r6_blob_count": len(historical),
        "historical_exact_identity_matches": len(historical) - len(differences),
        "historical_exact_identity_differences": differences,
        "historical_r7_verifier_identity_status": "FAIL" if differences else "PASS",
        "historical_verifier_executed": False,
        "historical_identity_note": "The unchanged verify_r7.py gate binds the pre-repair app; "
            "an authorized UI repair causes its exact-byte identity gate to fail.",
        "mvp_authorized_changed_path": "web_r4/app.js",
        "other_historical_byte_errors": protected_errors,
        "historical_source_receipt": R7_SOURCE_RECEIPT,
        "historical_source_receipt_sha256": sha(ROOT / R7_SOURCE_RECEIPT),
        "r7_sources_pinned": len(r7_sources), "r7_source_errors": r7_errors,
        "old_test_file_set_errors": test_file_set_errors,
    }


def run_suite(out: Path, name: str, suite: unittest.TestSuite,
              expected_count: int | None = None) -> dict:
    discovered = suite.countTestCases()
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (out / (name + ".log")).write_text(log.getvalue(), encoding="utf-8")
    passed = result.wasSuccessful() and not result.skipped and not result.expectedFailures
    passed = passed and not result.unexpectedSuccesses
    if expected_count is not None:
        passed = passed and discovered == expected_count and result.testsRun == expected_count
    report = {
        "status": "PASS" if passed else "FAIL", "tests_discovered": discovered,
        "tests_run": result.testsRun, "required_count": expected_count,
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped),
        "skip_details": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "log_path": name + ".log",
    }
    save(out, name + ".json", report)
    return report


def run_command(command: list[str], *, cwd: Path, timeout: int = 120,
                env: dict | None = None) -> dict:
    started = utc()
    try:
        child = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                               timeout=timeout, env=env)
        return {"command": command, "started_at": started, "finished_at": utc(),
                "exit_code": child.returncode, "stdout": child.stdout,
                "stderr": child.stderr, "runner_error": None}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": command, "started_at": started, "finished_at": utc(),
                "exit_code": None, "stdout": "", "stderr": "",
                "runner_error": type(error).__name__ + ": " + str(error)}


def protected_validation(out: Path) -> dict:
    # The frozen validator updates evidence/validation.json and its history.
    # Its writes are confined to a throwaway tree, never the working tree.
    with tempfile.TemporaryDirectory(prefix="lol-mvp-protected-") as directory:
        isolated = Path(directory) / "copy"
        shutil.copytree(ROOT, isolated, ignore=shutil.ignore_patterns(
            "__pycache__", ".git", "private", "private-*"))
        process = run_command([sys.executable, "-m", "validation"], cwd=isolated)
    save(out, "protected-process.json", process)
    try:
        result = json.loads(process["stdout"])
    except (ValueError, TypeError):
        result = {"error": "Protected validator did not emit a JSON report"}
    checks = result.get("checks", [])
    passed = process["exit_code"] == 0 and result.get("passed") == 9
    passed = passed and result.get("failed") == 0 and len(checks) == 9
    passed = passed and all(row.get("status") == "PASS" for row in checks)
    report = {"status": "PASS" if passed else "FAIL", "scope": "Protected nine legacy checks",
              "execution": "Temporary isolated working-tree copy", "result": result}
    save(out, "protected-regression.json", report)
    return report


def node_check(out: Path, name: str, script: str, source: str,
               count: int) -> dict:
    destination = out / (name + ".json")
    process = run_command(["node", script, str(destination)], cwd=ROOT, timeout=45)
    save(out, name + "-process.json", process)
    receipt = read_json(destination) if destination.is_file() else {}
    if name == "ui-delete-import":
        result = receipt.get("fixed_results", {})
        passed = result.get("passed") == count and result.get("total") == count
        passed = passed and all(row.get("passed") is True for row in result.get("results", []))
    elif name == "ui-file-race":
        passed = receipt.get("fixed_result", {}).get("passed") is True
    elif name == "ui-import":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == IMPORT_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    else:
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == SAVE_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    passed = passed and process["exit_code"] == 0 and receipt.get("source_sha256") == sha(ROOT / source)
    return {"status": "PASS" if passed else "FAIL", "receipt_path": destination.name,
            "receipt_sha256": sha(destination) if destination.is_file() else None,
            "source_path": source, "source_sha256": sha(ROOT / source),
            "required_cases": count, "process_exit_code": process["exit_code"],
            "scope": "Synthetic Node VM DOM stub; not browser E2E"}


def repair_binding() -> dict:
    names = ("save-race-before.json", "save-race-after.json")
    receipts = {name: read_json(ROOT / "evidence/mvp" / name) for name in names}
    before, after = (receipts[name] for name in names)
    fixture_hash = sha(ROOT / "examples/r3/compare-wait-retreat.json")
    checks = {
        "before_captured_failures": before.get("total") == 7 and before.get("passed") == 3
            and before.get("process", {}).get("exit_code") == 1,
        "after_all_seven_passed": after.get("total") == 7 and after.get("passed") == 7
            and after.get("process", {}).get("exit_code") == 0,
        "before_after_same_case_ids": {r.get("id") for r in before.get("results", [])}
            == {r.get("id") for r in after.get("results", [])} == SAVE_CASE_IDS,
        "before_after_same_fixture": before.get("fixture_sha256")
            == after.get("fixture_sha256") == fixture_hash,
        "save_repair_binds_import_repair_parent": after.get("source_sha256")
            == read_json(ROOT / "evidence/mvp/import-race-before.json").get("source_sha256"),
        "source_changed": before.get("source_sha256") != after.get("source_sha256"),
        "before_binds_preserved_r6_source": before.get("source_sha256")
            == read_json(ROOT / R6_SOURCE_RECEIPT)["source_sha256"]["web_r4/app.js"],
        "honest_execution_receipts": all(r.get("evidence_kind") == "FRESH_EXECUTION"
            for r in receipts.values()),
    }
    import_before = read_json(ROOT / "evidence/mvp/import-race-before.json")
    import_after = read_json(ROOT / "evidence/mvp/import-race-after.json")
    checks.update({
        "import_before_has_actual_failure": import_before.get("process", {}).get("exit_code") == 1
            and import_before.get("passed", 0) < import_before.get("total", 0),
        "import_after_all_cases_passed": import_after.get("passed") == len(IMPORT_CASE_IDS)
            and import_after.get("total") == len(IMPORT_CASE_IDS)
            and import_after.get("process", {}).get("exit_code") == 0
            and all(r.get("passed") is True for r in import_after.get("results", [])),
        "import_same_case_ids": {r.get("id") for r in import_before.get("results", [])}
            == {r.get("id") for r in import_after.get("results", [])} == IMPORT_CASE_IDS,
        "import_same_source_fixture": import_before.get("fixture_sha256")
            == import_after.get("fixture_sha256") == fixture_hash,
        "import_test_binds_current_script": import_before.get("test_sha256")
            == import_after.get("test_sha256") == sha(ROOT / "tests_mvp/ui_import_races.cjs"),
        "import_repair_binds_current_source": import_after.get("source_sha256") == sha(ROOT / "web_r4/app.js"),
        "import_source_changed": import_before.get("source_sha256") != import_after.get("source_sha256"),
        "import_honest_execution_receipts": all(r.get("evidence_kind") == "FRESH_EXECUTION"
            for r in (import_before, import_after)),
    })
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "receipt_sha256": {"evidence/mvp/" + n: sha(ROOT / "evidence/mvp" / n) for n in names},
            "before_source_sha256": before.get("source_sha256"),
            "after_source_sha256": after.get("source_sha256"),
            "current_source_sha256": sha(ROOT / "web_r4/app.js"),
            "import_receipt_sha256": {"evidence/mvp/" + name: sha(ROOT / "evidence/mvp" / name)
                for name in ("import-race-before.json", "import-race-after.json")},
            "before_source_reference": R6_SOURCE_RECEIPT,
            "before_source_reference_sha256": sha(ROOT / R6_SOURCE_RECEIPT)}


def postgame_checks(out: Path, raw_directory: str | None) -> dict:
    from tests_r7_player_grounded.test_postgame import PostGameSchemaTests, PinnedPostGameSourceTests
    loader = unittest.defaultTestLoader
    schema = run_suite(out, "postgame-schema", loader.loadTestsFromTestCase(PostGameSchemaTests), 13)
    if raw_directory:
        raw = Path(raw_directory).expanduser().resolve()
        os.environ["R7_POSTGAME_RAW_DIR"] = str(raw)
        integration = run_suite(out, "postgame-pinned", loader.loadTestsFromTestCase(PinnedPostGameSourceTests), 4)
        integration["input_sha256"] = {name: sha(raw / name) if (raw / name).is_file() else None
                                       for name in ("match.json", "timeline.json")}
        integration["raw_bytes_copied_to_evidence"] = False
        save(out, "postgame-pinned.json", integration)
    else:
        integration = {"status": "NOT_RUN", "tests_planned": 4, "tests_run": 0,
                       "skipped": 0, "reason": "R7_POSTGAME_RAW_DIR or --postgame-raw-dir not supplied; "
                       "preserved exact-byte private sources are unavailable to default CI",
                       "required_for_default_mvp_scope": False}
        save(out, "postgame-pinned.json", integration)
    return {"schema": schema, "pinned_source_integration": integration,
            "all_17_passed": schema["status"] == "PASS" and integration["status"] == "PASS",
            "coaching_accuracy_validated": False}


def input_hashes() -> dict[str, str]:
    folders = ("coach_v1", "coach_intake", "coach_audit", *OLD_FOLDERS, "tests_mvp",
               "tests_r7_player_grounded", "web_r4", "fixtures", "contracts", "schemas",
               "examples", "legacy", "validation", "scripts", ".github/workflows")
    values = {p.relative_to(ROOT).as_posix(): sha(p) for folder in folders
              for p in sorted((ROOT / folder).rglob("*"))
              if p.is_file() and "__pycache__" not in p.parts}
    for name in ("FREEZE_MANIFEST.json", "requirements-r3.txt", R7_SOURCE_RECEIPT, R6_SOURCE_RECEIPT,
                 "evidence/r7/baseline-tree.json", "evidence/mvp/save-race-before.json",
                 "evidence/mvp/save-race-after.json", "evidence/mvp/ci-cost-basis.json",
                 "evidence/mvp/import-race-before.json", "evidence/mvp/import-race-after.json",
                 "evidence/mvp/github-ci-visibility.json",
                 "docs/MVP_VALIDATION.md", "docs/MVP_BACKUP.md"):
        if (ROOT / name).is_file():
            values[name] = sha(ROOT / name)
    return dict(sorted(values.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgame-raw-dir", default=os.environ.get("R7_POSTGAME_RAW_DIR"),
                        help="Optional private directory containing pinned match.json/timeline.json")
    args = parser.parse_args()
    out = ROOT / "evidence/mvp" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                                 + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    historical_before = historical_evidence()
    inputs_before = input_hashes()
    checks = {}
    errors = []
    try:
        checks["preservation"] = preservation_gate()
        save(out, "preservation.json", checks["preservation"])
        checks["ui_repair_receipt_binding"] = repair_binding()
        save(out, "ui-repair-receipt-binding.json", checks["ui_repair_receipt_binding"])
        if any(checks[name]["status"] != "PASS" for name in checks):
            raise RuntimeError("Preservation or UI receipt binding gate failed")
        checks["protected_regression"] = protected_validation(out)
        suite = unittest.TestSuite()
        for folder in OLD_FOLDERS:
            suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / folder), top_level_dir=str(ROOT)))
        checks["old_regression"] = run_suite(out, "old-regression", suite, 111)
        checks["backup"] = run_suite(out, "backup", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_backup.py", top_level_dir=str(ROOT)))
        if checks["backup"]["tests_run"] == 0:
            checks["backup"]["status"] = "FAIL"
            save(out, "backup.json", checks["backup"])
        checks["ui_save"] = node_check(out, "ui-save", "tests_mvp/ui_save_race.cjs", "web_r4/app.js", 7)
        checks["ui_delete_import"] = node_check(out, "ui-delete-import", "tests_r4/ui_races.cjs", "web_r4/app.js", 2)
        checks["ui_file_race"] = node_check(out, "ui-file-race", "tests_r6/ui_file_race.cjs", "web_r4/research.js", 1)
        checks["ui_import"] = node_check(out, "ui-import", "tests_mvp/ui_import_races.cjs", "web_r4/app.js", len(IMPORT_CASE_IDS))
        checks["postgame"] = postgame_checks(out, args.postgame_raw_dir)
    except Exception as error:
        errors.append(type(error).__name__ + ": " + str(error))
    historical_after = historical_evidence()
    changed_history = sorted(p for p in set(historical_before) | set(historical_after)
                             if historical_before.get(p) != historical_after.get(p))
    inputs_after = input_hashes()
    changed_inputs = sorted(p for p in set(inputs_before) | set(inputs_after)
                            if inputs_before.get(p) != inputs_after.get(p))
    required = [v["status"] == "PASS" for k, v in checks.items() if k != "postgame"]
    postgame = checks.get("postgame", {})
    required.append(postgame.get("schema", {}).get("status") == "PASS")
    if args.postgame_raw_dir:
        required.append(postgame.get("pinned_source_integration", {}).get("status") == "PASS")
    passed = not errors and not changed_history and not changed_inputs and all(required)
    report = {
        "at_utc": utc(), "evidence_kind": "FRESH_SCOPED_MVP_EXECUTION",
        "status": "PASS" if passed else "FAIL", "passed": passed,
        "scope": "Frozen payload, preserved regressions, local backup/restore, and synthetic UI mechanics",
        "python": platform.python_version(), "run_directory": out.relative_to(ROOT).as_posix(),
        "checks": checks, "runner_errors": errors,
        "input_source_sha256": inputs_before, "inputs_changed_during_run": changed_inputs,
        "historical_evidence": {"files_checked": len(historical_before),
            "before_manifest_sha256": manifest_hash(historical_before),
            "after_manifest_sha256": manifest_hash(historical_after), "changed": changed_history},
        "github_actions_run_status": "STEP_EXECUTION_ONLY_WORKFLOW_CONCLUSION_NOT_OBSERVED"
            if os.environ.get("GITHUB_ACTIONS") == "true" else "NOT_RUN_BY_THIS_LOCAL_VERIFIER",
        "github_actions_context": {"run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "commit_sha": os.environ.get("GITHUB_SHA")},
        "full_postgame_17_passed": postgame.get("all_17_passed", False),
        "real_match_coaching_validation_passed": False, "coaching_enabled": False,
        "browser_e2e_executed": False, "historical_R1_reproduced": False,
    }
    save(out, "verification.json", report)
    print(json.dumps({k: report[k] for k in ("status", "passed", "run_directory",
                     "full_postgame_17_passed", "github_actions_run_status", "runner_errors")}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
