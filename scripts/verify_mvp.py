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
RESEARCH_CASE_IDS = {
    "RESEARCH-BOM-JSON", "RESEARCH-BOM-TRANSCRIPT", "RESEARCH-VALID-MULTIBYTE",
    "RESEARCH-REJECT-INVALID", "RESEARCH-REJECT-TRUNCATED",
    "RESEARCH-STALE-INVALID-A-FIRST", "RESEARCH-STALE-INVALID-B-FIRST",
    "RESEARCH-CLEARED-INVALID", "R6-LATEST-FILE-A-FIRST",
}
RESEARCH_REQUEST_CASE_IDS = {
    "RESEARCH-CURRENT-RESOURCE-GET-ERROR", "RESEARCH-CURRENT-NOTE-GET-ERROR",
    "RESEARCH-STALE-GET-ERROR-AFTER-NEW-SELECTION", "RESEARCH-STALE-GET-ERROR-AFTER-LOGOUT",
}
NAVIGATION_ERROR_CASE_IDS = {
    "RESEARCH-STALE-RESOURCE-ERROR-AFTER-B-DRAFT", "RESEARCH-CURRENT-RESOURCE-ERROR-STILL-HANDLED",
    "RESEARCH-STALE-ANCHOR-ERROR-AFTER-B-DRAFT", "RESEARCH-CURRENT-ANCHOR-ERROR-STILL-HANDLED",
    "RESEARCH-STALE-LIST-ERROR-AFTER-B-DRAFT", "RESEARCH-CURRENT-LIST-ERROR-STILL-HANDLED",
}
SAVE_ERROR_CASE_IDS = {
    "RESEARCH-STALE-SAVE-401-AFTER-B-DRAFT", "RESEARCH-STALE-SAVE-409-AFTER-B-DRAFT",
    "RESEARCH-CURRENT-SAVE-409-SHOWS-ERROR-KEEPS-DRAFT", "RESEARCH-CURRENT-SAVE-401-SHOWS-ERROR-CLEARS-AUTH-CONTEXT",
}
NAVIGATION_CASE_IDS = {
    "RESEARCH-NAV-DELETE-DISABLED-NO-REQUEST", "RESEARCH-NAV-LEGACY-DELETE-CANNOT-CLEAR-B-DRAFT",
    "RESEARCH-NAV-CURRENT-DELETE-CLEARS", "RESEARCH-NAV-LATE-A-DELETE-ERROR-CANNOT-REPORT-ON-B",
}
KNOWLEDGE_DELETION_CASE_IDS = {
    'KNOWLEDGE-DELETED-DISPLAYED-DESCENDANT-CLEARED-WITH-ANCESTOR-SURVIVING',
    'KNOWLEDGE-LATE-DELETION-READ-CANNOT-CLEAR-NEW-INDEPENDENT-SOURCE-DRAFT',
    'KNOWLEDGE-HELD-CREATED-ACK-CANNOT-RESURRECT-CASCADED-DESCENDANT',
}
KNOWLEDGE_FOLLOWUP_CASE_IDS = {
    'ui-knowledge-ack': {'KNOWLEDGE-CACHED-EXACT-ACK-CANNOT-REAPPLY-DELETED-DESCENDANT'},
    'ui-knowledge-reconcile-error': {'KNOWLEDGE-STALE-DELETION-ERROR-CANNOT-CLEAR-NEW-DRAFT-AUTH'},
    'ui-knowledge-read-deletion': {'KNOWLEDGE-CACHED-OPEN-CANNOT-DISPLAY-DELETED-DESCENDANT','KNOWLEDGE-CACHED-LIST-CANNOT-RESTORE-DELETED-DESCENDANT'},
    'ui-knowledge-proposal-delete': {'KNOWLEDGE-PROPOSAL-DELETE-CANNOT-RESURRECT-SAME-RULE-CACHED-OPEN'},
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


def knowledge_version_binding() -> dict:
    baseline=read_json(ROOT / 'evidence/mvp/knowledge-baseline.json')
    version=read_json(ROOT / 'evidence/mvp/knowledge-source-version.json')
    current=version.get('current_sha256', {})
    checks={
        'exact_intake': baseline.get('intake_main') == 'd92ded9743b591030a55e355e914ab238589e447',
        'exact_baseline_paths': set(baseline.get('sha256', {})) == {'web_r4/research.js','web_r4/index.html','coach_v1/server.py','coach_v1/backup.py'},
        'parent_research_errors': baseline.get('sha256', {}).get('web_r4/research.js') == read_json(ROOT / 'evidence/mvp/research-navigation-errors-after.json').get('source_sha256') == read_json(ROOT / 'evidence/mvp/research-save-errors-final.json').get('source_sha256'),
        'parent_history_sources': all(baseline.get('sha256', {}).get(p) == read_json(ROOT / 'evidence/mvp/note-history-source-version.json')['current_sha256'][p] for p in ('web_r4/index.html','coach_v1/server.py')),
        'exact_version_paths': set(current) == set(baseline.get('sha256', {})) | {'coach_v1/knowledge.py','web_r4/knowledge.js'},
        'actual_current_hashes': all((ROOT / p).is_file() and (read_json(ROOT / 'evidence/mvp/knowledge-ui-proposal-delete-before.json').get('source_sha256') if p == 'web_r4/knowledge.js' else sha(ROOT / p)) == h for p,h in current.items()),
        'legacy_store_unchanged': baseline.get('unchanged_research_store_sha256') == sha(ROOT / 'coach_v1/research.py') == '42912d1e7ac660c67b00514d7aa76b6d10252e77c0a478db55bc37ad21d3eb27',
        'independent_lifecycle_tests_present': all((ROOT / p).is_file() for p in ('tests_mvp/test_knowledge.py','tests_mvp/test_knowledge_backup.py','tests_mvp/test_knowledge_http.py','tests_mvp/browser_knowledge.cjs')),
        'migration_scope': version.get('research_schema') == 2 and version.get('main_schema') == 1 and version.get('engine_activation') is False,
        'deletion_repair_history': knowledge_deletion_binding()['status'] == 'PASS',
        'proposal_deletion_repair': knowledge_proposal_delete_binding()['status'] == 'PASS',
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'baseline_sha256':sha(ROOT / 'evidence/mvp/knowledge-baseline.json'),
            'version_sha256':sha(ROOT / 'evidence/mvp/knowledge-source-version.json')}


def knowledge_browser_repair_binding() -> dict:
    repair = read_json(ROOT / 'evidence/mvp/knowledge-browser-repair.json')
    failed = read_json(ROOT / repair['failure_receipt'])
    browser = failed['browser']['browser_receipt']
    archive = ROOT / repair['archived_before']
    checks = {
        'actual_first_run_failure_retained': failed['run']['id'] == repair['failed_run'] == 37268245767 and failed['run']['attempt'] == 1 and failed['run']['conclusion'] == 'failure' and failed['regression']['status'] == 'PASS' and browser['passed'] is False,
        'exact_first_failure': [r['id'] for r in browser['checks'] if r['passed'] is False] == [repair['failure_id']],
        'actual_failed_source_archived': sha(archive) == repair['browser_test_before_sha256'] == browser['source_sha256']['tests_mvp/browser_knowledge.cjs'],
        'current_repaired_verifier': sha(ROOT / 'tests_mvp/browser_knowledge.cjs') == repair['browser_test_after_sha256'],
        'production_unchanged_by_verifier_repair': sha(ROOT / 'web_r4/knowledge.js') == repair['production_knowledge_sha256'] == browser['source_sha256']['web_r4/knowledge.js'],
        'tested_tree_bound': failed['tested_commit']['tree'] == repair['failed_tree'] and failed['tested_commit']['sha'] == repair['failed_tested_commit'] == failed['browser']['commit_sha'],
        'required_count_preserved': repair['required_browser_checks'] == 79 and repair['knowledge_cases'] == 16,
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}


def knowledge_deletion_binding() -> dict:
    names=('knowledge-ui-before.json','knowledge-ui-after.json','knowledge-ui-final.json')
    before,after,final=[read_json(ROOT / 'evidence/mvp' / name) for name in names]
    checks={
        'same_three_cases': all(row.get('total') == 3 and {r.get('id') for r in row.get('results', [])} == KNOWLEDGE_DELETION_CASE_IDS for row in (before,after,final)),
        'same_test_fixture': before.get('test_sha256') == after.get('test_sha256') == final.get('test_sha256') == sha(ROOT / 'tests_mvp/ui_knowledge_deletion.cjs') and before.get('fixture_sha256') == after.get('fixture_sha256') == final.get('fixture_sha256'),
        'actual_three_initial_failures': before.get('passed') == 0 and all(r.get('passed') is False for r in before.get('results', [])),
        'repaired_three_passes': after.get('passed') == 3 and all(r.get('passed') is True for r in after.get('results', [])),
        'later_three_passes': final.get('passed') == 3 and all(r.get('passed') is True for r in final.get('results', [])),
        'first_repair_followup_parent': all(after.get('source_sha256') == read_json(ROOT / ('evidence/mvp/knowledge-ui-'+name+'-before.json')).get('source_sha256') for name in ('ack','error')),
        'second_repair_followup_parent': final.get('source_sha256') == read_json(ROOT / 'evidence/mvp/knowledge-ui-read-before.json').get('source_sha256'),
        'later_request_ownership_binding': knowledge_followup_binding()['status'] == 'PASS',
        'distinct_sources': before.get('source_sha256') != after.get('source_sha256'),
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'receipt_sha256':{name:sha(ROOT / 'evidence/mvp' / name) for name in names}}


def knowledge_followup_binding() -> dict:
    checks={};hashes={}
    middle=read_json(ROOT / 'evidence/mvp/knowledge-ui-final.json')['source_sha256']
    for suffix,script,key in (('ack','ui_knowledge_ack.cjs','ui-knowledge-ack'),
                             ('error','ui_knowledge_reconcile_error.cjs','ui-knowledge-reconcile-error'),
                             ('read','ui_knowledge_read_deletion.cjs','ui-knowledge-read-deletion')):
        paths=['evidence/mvp/knowledge-ui-'+suffix+'-'+stage+'.json' for stage in ('before','after')]
        before,after=[read_json(ROOT / p) for p in paths];expected=KNOWLEDGE_FOLLOWUP_CASE_IDS[key]
        checks[suffix+'_exact_cases']=all(r.get('total') == len(expected) and {c.get('id') for c in r.get('results', [])} == expected for r in (before,after))
        checks[suffix+'_same_test_fixture']=before.get('test_sha256') == after.get('test_sha256') == sha(ROOT / ('tests_mvp/'+script)) and before.get('fixture_sha256') == after.get('fixture_sha256')
        checks[suffix+'_initial_failures']=before.get('passed') == 0 and all(c.get('passed') is False for c in before.get('results', []))
        checks[suffix+'_repair_pass']=after.get('passed') == len(expected) and all(c.get('passed') is True for c in after.get('results', []))
        checks[suffix+'_repair_source']=after.get('source_sha256') == (read_json(ROOT / 'evidence/mvp/knowledge-source-version.json')['current_sha256']['web_r4/knowledge.js'] if suffix == 'read' else middle)
        checks[suffix+'_distinct_sources']=before.get('source_sha256') != after.get('source_sha256')
        if suffix == 'read':
            archived=ROOT / ('evidence/mvp/knowledge-ui-sources/'+before['source_sha256']+'.js')
            checks['read_actual_parent_bytes_preserved']=archived.is_file() and sha(archived) == before['source_sha256'] == middle
        hashes.update({p:sha(ROOT / p) for p in paths})
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'receipt_sha256':hashes}


def knowledge_proposal_delete_binding() -> dict:
    names=('knowledge-ui-proposal-delete-before.json','knowledge-ui-proposal-delete-after.json')
    before,after=[read_json(ROOT / 'evidence/mvp' / name) for name in names]
    expected=KNOWLEDGE_FOLLOWUP_CASE_IDS['ui-knowledge-proposal-delete']
    archived=ROOT / ('evidence/mvp/knowledge-ui-sources/'+before['source_sha256']+'.js')
    checks={
        'exact_case':all(row.get('total') == 1 and {c.get('id') for c in row.get('results', [])} == expected for row in (before,after)),
        'same_test_fixture':before.get('test_sha256') == after.get('test_sha256') == sha(ROOT / 'tests_mvp/ui_knowledge_proposal_delete.cjs') and before.get('fixture_sha256') == after.get('fixture_sha256'),
        'initial_failure':before.get('passed') == 0 and before['results'][0].get('passed') is False,
        'repaired_pass':after.get('passed') == 1 and after['results'][0].get('passed') is True,
        'original_version_bound':before.get('source_sha256') == read_json(ROOT / 'evidence/mvp/knowledge-source-version.json')['current_sha256']['web_r4/knowledge.js'] == read_json(ROOT / 'evidence/mvp/knowledge-ui-read-after.json').get('source_sha256'),
        'actual_parent_bytes':archived.is_file() and sha(archived) == before['source_sha256'],
        'actual_current_source':after.get('source_sha256') == sha(ROOT / 'web_r4/knowledge.js'),
        'distinct_sources':before.get('source_sha256') != after.get('source_sha256'),
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'receipt_sha256':{name:sha(ROOT / 'evidence/mvp' / name) for name in names}}


def navigation_error_binding() -> dict:
    names = ("research-navigation-errors-before.json", "research-navigation-errors-after.json")
    before, after = [read_json(ROOT / "evidence/mvp" / n) for n in names]
    checks = {
        "exact_same_six_cases": all(row.get("total") == 6 and {r.get("id") for r in row["results"]} == NAVIGATION_ERROR_CASE_IDS for row in (before, after)),
        "same_test_and_fixture": before.get("test_sha256") == after.get("test_sha256") == sha(ROOT / "tests_mvp/ui_research_navigation_errors.cjs") and before.get("fixture_sha256") == after.get("fixture_sha256"),
        "actual_initial_failures": before.get("passed") == 3 and before.get("process", {}).get("exit_code") == 1 and {r.get("id") for r in before["results"] if r.get("passed") is False} == {"RESEARCH-STALE-RESOURCE-ERROR-AFTER-B-DRAFT", "RESEARCH-STALE-ANCHOR-ERROR-AFTER-B-DRAFT", "RESEARCH-STALE-LIST-ERROR-AFTER-B-DRAFT"},
        "actual_repair_pass": after.get("passed") == 6 and after.get("process", {}).get("exit_code") == 0 and all(r.get("passed") is True for r in after["results"]),
        "binds_save_repair_parent": before.get("source_sha256") == read_json(ROOT / "evidence/mvp/research-save-errors-after.json").get("source_sha256"),
        "binds_knowledge_parent_source": after.get("source_sha256") == read_json(ROOT / "evidence/mvp/knowledge-baseline.json")["sha256"]["web_r4/research.js"],
        "knowledge_version_binding": knowledge_version_binding()["status"] == "PASS",
        "separate_sources": before.get("source_sha256") != after.get("source_sha256"),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "receipt_sha256": {"evidence/mvp/" + n: sha(ROOT / "evidence/mvp" / n) for n in names}}


def save_error_binding() -> dict:
    names = ("research-save-errors-before.json", "research-save-errors-after.json", "research-save-errors-final.json")
    before, after, final = [read_json(ROOT / "evidence/mvp" / name) for name in names]
    checks = {
        "exact_same_four_cases": all(row.get("total") == 4 and {r.get("id") for r in row["results"]} == SAVE_ERROR_CASE_IDS for row in (before, after, final)),
        "same_test_and_fixture": before.get("test_sha256") == after.get("test_sha256") == final.get("test_sha256") == sha(ROOT / "tests_mvp/ui_research_save_errors.cjs") and before.get("fixture_sha256") == after.get("fixture_sha256") == final.get("fixture_sha256"),
        "actual_initial_failures": before.get("passed") == 2 and before.get("process", {}).get("exit_code") == 1 and {r.get("id") for r in before["results"] if r.get("passed") is False} == {"RESEARCH-STALE-SAVE-401-AFTER-B-DRAFT", "RESEARCH-STALE-SAVE-409-AFTER-B-DRAFT"},
        "actual_repair_pass": after.get("passed") == 4 and after.get("process", {}).get("exit_code") == 0 and all(r.get("passed") is True for r in after["results"]),
        "binds_history_source": before.get("source_sha256") == read_json(ROOT / "evidence/mvp/note-history-source-version.json")["current_sha256"]["web_r4/research.js"],
        "binds_final_parent_source": final.get("source_sha256") == read_json(ROOT / "evidence/mvp/knowledge-baseline.json")["sha256"]["web_r4/research.js"],
        "final_four_pass": final.get("passed") == 4 and final.get("process", {}).get("exit_code") == 0 and all(r.get("passed") is True for r in final["results"]),
        "navigation_error_repair": navigation_error_binding()["status"] == "PASS",
        "separate_sources": len({r.get("source_sha256") for r in (before, after, final)}) == 3,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "receipt_sha256": {"evidence/mvp/" + name: sha(ROOT / "evidence/mvp" / name) for name in names}}


def history_version_binding() -> dict:
    baseline = read_json(ROOT / "evidence/mvp/note-history-baseline.json")
    version = read_json(ROOT / "evidence/mvp/note-history-source-version.json")
    parent = {
        "web_r4/research.js": "327a951630c8d629c9208160acdd9f3142baae3de0b97d472fc1940a7e333b4e",
        "web_r4/index.html": "680714346cfff1a2bf2856fea267012cf6c13d224d64d5e66a44634c1fbddb70",
        "coach_v1/server.py": "b1601a55950438f5ec1093dfdccd0bce7bc393b6299e653b0a5aa103160581e9",
    }
    current = version.get("current_sha256", {})
    checks = {
        "exact_intake_main": baseline.get("intake_main") == "321ecbd9515fa50a3ef8bff67dd0cbdd322d9fe4",
        "exact_parent_source": baseline.get("sha256") == parent,
        "versioned_paths_only": set(current) == set(parent),
        "current_source_bound": all((read_json(ROOT / "evidence/mvp/research-save-errors-before.json").get("source_sha256") if p == "web_r4/research.js" else read_json(ROOT / "evidence/mvp/knowledge-baseline.json")["sha256"][p]) == v for p, v in current.items()),
        "later_save_error_repair_binding": save_error_binding()["status"] == "PASS",
        "prior_navigation_source_preserved": read_json(ROOT / "evidence/mvp/research-navigation-final.json").get("source_sha256") == parent["web_r4/research.js"],
        "unchanged_storage_schema": version.get("unchanged_research_store_sha256") == sha(ROOT / "coach_v1/research.py") == "42912d1e7ac660c67b00514d7aa76b6d10252e77c0a478db55bc37ad21d3eb27",
        "read_only_module_and_tests_present": all((ROOT / p).is_file() for p in (
            "coach_v1/note_history.py", "tests_mvp/test_note_history.py", "tests_mvp/test_note_history_http.py", "tests_mvp/browser_note_history.cjs")),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "baseline_sha256": sha(ROOT / "evidence/mvp/note-history-baseline.json"),
            "version_sha256": sha(ROOT / "evidence/mvp/note-history-source-version.json"),
            "authorized_versioned_paths": sorted(current)}


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
    research = research_binding()
    history = history_version_binding()
    authorized = {"web_r4/app.js"}
    if research["status"] == "PASS":
        authorized.add("web_r4/research.js")
    if history["status"] == "PASS":
        authorized.update(("web_r4/index.html", "coach_v1/server.py"))
    protected_errors = [p for p in differences if p not in authorized]
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
        "mvp_authorized_changed_paths": sorted(authorized),
        "research_repair_binding": research,
        "note_history_version_binding": history,
        "knowledge_version_binding": knowledge_version_binding(),
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
    elif name == "ui-research-bytes":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == RESEARCH_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
        passed = passed and receipt.get("fixed_result", {}).get("passed") is True
    elif name == "ui-research-requests":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == RESEARCH_REQUEST_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    elif name == "ui-research-navigation":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == NAVIGATION_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    elif name == "ui-research-navigation-errors":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == NAVIGATION_ERROR_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    elif name == "ui-research-save-errors":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == SAVE_ERROR_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    elif name == "ui-knowledge-deletion":
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == KNOWLEDGE_DELETION_CASE_IDS
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    elif name in KNOWLEDGE_FOLLOWUP_CASE_IDS:
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == KNOWLEDGE_FOLLOWUP_CASE_IDS[name]
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
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


def navigation_binding() -> dict:
    names = ("research-navigation-before.json", "research-navigation-after.json", "research-navigation-final.json")
    before, first, final = [read_json(ROOT / "evidence/mvp" / n) for n in names]
    rows = (before, first, final)
    checks = {
        "exact_same_four_cases": all(row.get("total") == 4 and {r["id"] for r in row["results"]}
                                     == NAVIGATION_CASE_IDS for row in rows),
        "same_current_test": all(row.get("test_sha256") == sha(ROOT / "tests_mvp/ui_research_navigation.cjs") for row in rows),
        "actual_before_failures": before.get("passed") == 1 and {r["id"] for r in before["results"]
            if r.get("passed") is False} == NAVIGATION_CASE_IDS - {"RESEARCH-NAV-CURRENT-DELETE-CLEARS"},
        "repaired_all_pass": all(row.get("passed") == 4 and all(r.get("passed") is True
            for r in row["results"]) for row in (first, final)),
        "binds_previous_source": before.get("source_sha256") == read_json(ROOT / "evidence/mvp/research-request-after.json").get("source_sha256"),
        "binds_note_history_parent": final.get("source_sha256") == read_json(ROOT / "evidence/mvp/note-history-baseline.json")["sha256"]["web_r4/research.js"],
        "note_history_version_binding": history_version_binding()["status"] == "PASS",
        "separate_repair_versions": len({row.get("source_sha256") for row in rows}) == 3,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "receipt_sha256": {"evidence/mvp/" + n: sha(ROOT / "evidence/mvp" / n) for n in names}}


def research_binding() -> dict:
    names = ("research-bytes-before.json", "research-bytes-after.json", "research-bytes-final.json", "research-bytes-request-repair.json")
    before, first, final, current = [read_json(ROOT / "evidence/mvp" / n) for n in names]
    test_sha = sha(ROOT / "tests_mvp/ui_research_bytes.cjs")
    rows = (before, first, final, current)
    request_names = ("research-request-before.json", "research-request-after.json")
    req_before, req_after = [read_json(ROOT / "evidence/mvp" / n) for n in request_names]
    failed_ids = {r["id"] for r in before["results"] if r.get("passed") is False}
    checks = {
        "same_nine_case_ids": all({r["id"] for r in row["results"]} == RESEARCH_CASE_IDS
                                   and row.get("total") == 9 for row in rows),
        "same_fixture": all(row.get("fixture_sha256") == before.get("fixture_sha256") for row in rows),
        "same_current_test": all(row.get("test_sha256") == test_sha for row in rows),
        "before_exact_failures": before.get("passed") == 5 and failed_ids == {
            "RESEARCH-BOM-JSON", "RESEARCH-BOM-TRANSCRIPT", "RESEARCH-REJECT-INVALID", "RESEARCH-REJECT-TRUNCATED"},
        "actual_exit_history": [row.get("process", {}).get("exit_code") for row in rows] == [1, 0, 0, 0],
        "repaired_all_pass": all(row.get("passed") == 9 and all(r.get("passed") is True
                                    for r in row["results"]) for row in (first, final, current)),
        "before_binds_preserved_source": before.get("source_sha256") ==
            read_json(ROOT / R6_SOURCE_RECEIPT)["source_sha256"]["web_r4/research.js"],
        "current_binds_navigation_parent": current.get("source_sha256") == read_json(ROOT / "evidence/mvp/research-navigation-before.json").get("source_sha256"),
        "navigation_repair_binding": navigation_binding()["status"] == "PASS",
        "separate_repair_versions": len({row.get("source_sha256") for row in rows}) == 4,
        "request_source_chain": req_before.get("source_sha256") == final.get("source_sha256")
            and req_after.get("source_sha256") == current.get("source_sha256"),
        "request_same_test_fixture": req_before.get("test_sha256") == req_after.get("test_sha256")
            == sha(ROOT / "tests_mvp/ui_research_requests.cjs")
            and req_before.get("fixture_sha256") == req_after.get("fixture_sha256"),
        "request_exact_cases": all(row.get("total") == 4 and {r["id"] for r in row["results"]}
                                   == RESEARCH_REQUEST_CASE_IDS for row in (req_before, req_after)),
        "request_actual_failures": req_before.get("passed") == 2 and req_before.get("process", {}).get("exit_code") == 1
            and {r["id"] for r in req_before["results"] if r.get("passed") is False} == {
                "RESEARCH-CURRENT-RESOURCE-GET-ERROR", "RESEARCH-CURRENT-NOTE-GET-ERROR"},
        "request_after_pass": req_after.get("passed") == 4 and req_after.get("process", {}).get("exit_code") == 0
            and all(r.get("passed") is True for r in req_after["results"]),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "receipt_sha256": {"evidence/mvp/" + n: sha(ROOT / "evidence/mvp" / n) for n in (*names, *request_names)},
            "historical_r6_harness": "Unchanged text-only File stub; its exact A-first expectations are rerun by R6-LATEST-FILE-A-FIRST with both native codec paths. No old expected value changed."}


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
    values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp/knowledge-ui-sources').glob('*.js')) if p.is_file()})
    values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp/knowledge-browser-sources').glob('*.cjs')) if p.is_file()})
    for name in ("FREEZE_MANIFEST.json", "requirements-r3.txt", R7_SOURCE_RECEIPT, R6_SOURCE_RECEIPT,
                 "evidence/r7/baseline-tree.json", "evidence/mvp/save-race-before.json",
                 "evidence/mvp/save-race-after.json", "evidence/mvp/ci-cost-basis.json",
                 "evidence/mvp/import-race-before.json", "evidence/mvp/import-race-after.json",
                 "evidence/mvp/research-bytes-before.json", "evidence/mvp/research-bytes-after.json",
                 "evidence/mvp/research-bytes-final.json",
                 "evidence/mvp/research-bytes-request-repair.json",
                 "evidence/mvp/research-request-before.json", "evidence/mvp/research-request-after.json",
                 "evidence/mvp/research-navigation-before.json", "evidence/mvp/research-navigation-after.json",
                 "evidence/mvp/research-navigation-final.json",
                 "evidence/mvp/note-history-baseline.json", "evidence/mvp/note-history-source-version.json",
                 "evidence/mvp/research-save-errors-before.json", "evidence/mvp/research-save-errors-after.json",
                 "evidence/mvp/research-save-errors-final.json", "evidence/mvp/research-navigation-errors-before.json", "evidence/mvp/research-navigation-errors-after.json",
                 "evidence/mvp/knowledge-baseline.json", "evidence/mvp/knowledge-source-version.json",
                 "evidence/mvp/knowledge-ui-before.json", "evidence/mvp/knowledge-ui-after.json",
                 "evidence/mvp/knowledge-ui-final.json", "evidence/mvp/knowledge-ui-ack-before.json", "evidence/mvp/knowledge-ui-ack-after.json",
                 "evidence/mvp/knowledge-ui-error-before.json", "evidence/mvp/knowledge-ui-error-after.json", "evidence/mvp/knowledge-ui-read-before.json", "evidence/mvp/knowledge-ui-read-after.json",
                 "evidence/mvp/knowledge-ui-proposal-delete-before.json", "evidence/mvp/knowledge-ui-proposal-delete-after.json",
                 "evidence/mvp/knowledge-browser-repair.json", "evidence/mvp/knowledge-ci-37268245767-failure.json",
                 "evidence/mvp/github-ci-visibility.json",
                 "docs/MVP_VALIDATION.md", "docs/MVP_BACKUP.md", "docs/MVP_KNOWLEDGE_PROPOSALS.md"):
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
        checks["knowledge_browser_repair_binding"] = knowledge_browser_repair_binding()
        save(out, "knowledge-browser-repair-binding.json", checks["knowledge_browser_repair_binding"])
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
        checks["note_history_store"] = run_suite(out, "note-history-store", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_note_history.py", top_level_dir=str(ROOT)), 19)
        checks["note_history_http"] = run_suite(out, "note-history-http", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_note_history_http.py", top_level_dir=str(ROOT)), 5)
        checks["knowledge_store"] = run_suite(out, "knowledge-store", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_knowledge.py", top_level_dir=str(ROOT)), 42)
        checks["knowledge_backup"] = run_suite(out, "knowledge-backup", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_knowledge_backup.py", top_level_dir=str(ROOT)), 19)
        checks["knowledge_http"] = run_suite(out, "knowledge-http", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_knowledge_http.py", top_level_dir=str(ROOT)), 5)
        if checks["note_history_store"]["tests_run"] == 0:
            checks["note_history_store"]["status"] = "FAIL"
        checks["ui_save"] = node_check(out, "ui-save", "tests_mvp/ui_save_race.cjs", "web_r4/app.js", 7)
        checks["ui_delete_import"] = node_check(out, "ui-delete-import", "tests_r4/ui_races.cjs", "web_r4/app.js", 2)
        checks["ui_research_bytes"] = node_check(out, "ui-research-bytes", "tests_mvp/ui_research_bytes.cjs", "web_r4/research.js", 9)
        checks["ui_research_requests"] = node_check(out, "ui-research-requests", "tests_mvp/ui_research_requests.cjs", "web_r4/research.js", 4)
        checks["ui_research_navigation"] = node_check(out, "ui-research-navigation", "tests_mvp/ui_research_navigation.cjs", "web_r4/research.js", 4)
        checks["ui_research_save_errors"] = node_check(out, "ui-research-save-errors", "tests_mvp/ui_research_save_errors.cjs", "web_r4/research.js", 4)
        checks["ui_research_navigation_errors"] = node_check(out, "ui-research-navigation-errors", "tests_mvp/ui_research_navigation_errors.cjs", "web_r4/research.js", 6)
        checks["ui_knowledge_deletion"] = node_check(out, "ui-knowledge-deletion", "tests_mvp/ui_knowledge_deletion.cjs", "web_r4/knowledge.js", 3)
        checks["ui_knowledge_ack"] = node_check(out, "ui-knowledge-ack", "tests_mvp/ui_knowledge_ack.cjs", "web_r4/knowledge.js", 1)
        checks["ui_knowledge_reconcile_error"] = node_check(out, "ui-knowledge-reconcile-error", "tests_mvp/ui_knowledge_reconcile_error.cjs", "web_r4/knowledge.js", 1)
        checks["ui_knowledge_read_deletion"] = node_check(out, "ui-knowledge-read-deletion", "tests_mvp/ui_knowledge_read_deletion.cjs", "web_r4/knowledge.js", 2)
        checks["ui_knowledge_proposal_delete"] = node_check(out, "ui-knowledge-proposal-delete", "tests_mvp/ui_knowledge_proposal_delete.cjs", "web_r4/knowledge.js", 1)
        checks["ui_file_race"] = {"status": checks["ui_research_bytes"]["status"],
            "required_cases": 1, "case_id": "R6-LATEST-FILE-A-FIRST",
            "receipt_path": checks["ui_research_bytes"]["receipt_path"],
            "scope": "Original R6 A-first ordering expectations in current ArrayBuffer-capable harness; old test file preserved"}
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
