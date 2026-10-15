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
NOTE_RECOVERY_CASE_IDS = {
    'NOTE-RECOVERY-EXACT-UNICODE-DRAFT-KEEPS-CURRENT-CAS-NO-PUT',
    'NOTE-RECOVERY-NATIVE-CANCEL-LEAVES-DIRTY-EDITOR-UNCHANGED',
    'NOTE-RECOVERY-LOADING-AND-PENDING-SAVE-HANDLER-BLOCKED',
    'NOTE-RECOVERY-NAVIGATION-VIEW-LOGOUT-DELETION-PREVIEW-BLOCKED',
    'NOTE-RECOVERY-NEXT-SAVE-USES-LOADED-LATEST-NOT-HISTORICAL-REVISION',
}
NOTE_RECOVERY_DELETE_CASE_IDS = {
    'NOTE-DELETE-READY-SAME-RESOURCE-OTHER-ANCHOR-PURGES-SAVED-EXPORT',
    'NOTE-DELETE-PENDING-SAME-RESOURCE-READ-CANNOT-REVIVE-DELETED-NOTE',
    'NOTE-DELETE-PENDING-DIFFERENT-RESOURCE-LOAD-SURVIVES-DELETED-CACHE-PURGE',
}
DRAFT_UI_CASE_IDS = {
    'DRAFT-UI-LATE-ACK-KEEPS-LATER-DRAFT-AND-NEXT-CAS',
    'DRAFT-UI-OLD-409-401-CANNOT-CHANGE-NEW-B-DRAFT-OR-AUTH',
    'DRAFT-UI-CURRENT-CONFLICT-RETAINS-DRAFT-CURRENT-401-CLEARS',
    'DRAFT-UI-HISTORY-READONLY-KEEPS-CURRENT-CAS-AND-SAVED-EXPORT',
    'DRAFT-UI-LATE-HISTORY-CANNOT-FOLLOW-NAVIGATION-NEW-LOGOUT',
    'DRAFT-UI-DELETE-INVALIDATES-SAME-CAPTURE-CACHED-OPEN-EXPORT',
    'DRAFT-UI-INACTIVE-A-DELETE-PURGES-CACHE-PRESERVES-PENDING-B',
}
DRAFT_ROUNDTRIP_CASE_IDS = {
    'DRAFT-ROUNDTRIP-UNTOUCHED-NULL-MEMBERSHIP-ORDER',
    'DRAFT-ROUNDTRIP-SELECTIVE-EDITS-PRESERVE-OTHER-ROWS',
    'DRAFT-ROUNDTRIP-LATE-ACK-KEEPS-CAPTURED-DRAFT-BASE',
    'DRAFT-ROUNDTRIP-NEW-INPUT-NO-INFERRED-ROLE-ROWS',
}
DRAFT_RETRY_CASE_IDS = {
    'DRAFT-RETRY-NETWORK-LOSS-REUSES-EXACT-REQUEST-THEN-ROTATES-KEY',
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


REVIEW_PARENT_PATHS = frozenset(('coach_v1/knowledge.py','coach_v1/server.py',
    'web_r4/knowledge.js','web_r4/index.html','scripts/verify_mvp.py',
    'scripts/browser_mvp.py','tests_mvp/browser_save_race.cjs',
    'tests_mvp/browser_knowledge.cjs','tests_mvp/browser_note_recovery.cjs'))


def review_parent_sha(path):
    """Compare historical gates to archived parents only with exact current binding."""
    current = sha(ROOT / path)
    if path not in REVIEW_PARENT_PATHS:
        return current
    version = read_json(ROOT / 'evidence/mvp/knowledge-review-version.json')
    parent = read_json(ROOT / 'evidence/mvp/knowledge-review-parent.json')
    archive = ROOT / 'evidence/mvp/knowledge-review-parent' / path
    if (current == version['current_sha256'].get(path)
        and sha(archive) == parent['prior_sha256'].get(path)):
        return parent['prior_sha256'][path]
    return current


def knowledge_review_binding():
    parent = read_json(ROOT / 'evidence/mvp/knowledge-review-parent.json')
    version = read_json(ROOT / 'evidence/mvp/knowledge-review-version.json')
    amendment = read_json(ROOT / 'contracts/amendments/2026-10-09-knowledge-review.json')
    expected = REVIEW_PARENT_PATHS | {'web_r4/knowledge_review.js',
        'tests_mvp/test_knowledge_review.py','tests_mvp/browser_knowledge_review.cjs',
        'docs/MVP_KNOWLEDGE_REVIEW.md','contracts/amendments/2026-10-09-knowledge-review.json'}
    checks = {
        'exact_intake': parent['intake_main'] == '92c49522dc5eca3a091a991dddfee3f3d3d6aa92',
        'exact_parent_paths': set(parent['prior_sha256']) == REVIEW_PARENT_PATHS,
        'archived_parent_bytes': all(sha(ROOT/'evidence/mvp/knowledge-review-parent'/p) == h
            for p,h in parent['prior_sha256'].items()),
        'exact_current_paths': set(version['current_sha256']) == expected,
        'current_bytes_bound': all(sha(ROOT/p) == h for p,h in version['current_sha256'].items()),
        'explicit_user_authority': amendment['authority'] == 'USER_DECISION_2026-10-09',
        'frozen_parent_preserved': amendment['parent_freeze_sha256'] == sha(ROOT/'FREEZE_MANIFEST.json'),
        'amendment_contract_bound': amendment['contract_sha256'] == sha(ROOT/amendment['contract']),
        'ai_consensus_stays_forbidden': amendment['ai_consensus_promotion_allowed'] is False,
        'browser_harness_only_cleanup_change': all((ROOT/'evidence/mvp/knowledge-review-parent'/p).read_text().replace('await page.unroute(pattern,handler);','') == (ROOT/p).read_text() for p in ('tests_mvp/browser_knowledge.cjs','tests_mvp/browser_note_recovery.cjs')),
        'no_engine_or_sql_change': amendment['engine_activation'] is False and amendment['sql_schema_change'] is False,
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}


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
        'actual_current_hashes': all((ROOT / p).is_file() and (read_json(ROOT / 'evidence/mvp/note-recovery-baseline.json')['sha256'][p] if p in ('web_r4/research.js','web_r4/index.html') else read_json(ROOT / 'evidence/mvp/knowledge-ui-proposal-delete-before.json').get('source_sha256') if p == 'web_r4/knowledge.js' else read_json(ROOT / 'evidence/mvp/draft-baseline.json')['sha256'][p] if p in ('coach_v1/server.py','coach_v1/backup.py') else review_parent_sha(p)) == h for p,h in current.items()),
        'later_recovery_source_chain': note_recovery_version_binding()['status'] == 'PASS',
        'legacy_store_unchanged': baseline.get('unchanged_research_store_sha256') == sha(ROOT / 'coach_v1/research.py') == '42912d1e7ac660c67b00514d7aa76b6d10252e77c0a478db55bc37ad21d3eb27',
        'independent_lifecycle_tests_present': all((ROOT / p).is_file() for p in ('tests_mvp/test_knowledge.py','tests_mvp/test_knowledge_backup.py','tests_mvp/test_knowledge_http.py','tests_mvp/browser_knowledge.cjs')),
        'migration_scope': version.get('research_schema') == 2 and version.get('main_schema') == 1 and version.get('engine_activation') is False,
        'deletion_repair_history': knowledge_deletion_binding()['status'] == 'PASS',
        'proposal_deletion_repair': knowledge_proposal_delete_binding()['status'] == 'PASS',
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'baseline_sha256':sha(ROOT / 'evidence/mvp/knowledge-baseline.json'),
            'version_sha256':sha(ROOT / 'evidence/mvp/knowledge-source-version.json')}


def note_recovery_version_binding() -> dict:
    baseline = read_json(ROOT / 'evidence/mvp/note-recovery-baseline.json')
    version = read_json(ROOT / 'evidence/mvp/note-recovery-source-version.json')
    before, after = [read_json(ROOT / ('evidence/mvp/note-recovery-'+stage+'.json')) for stage in ('before','after')]
    final = read_json(ROOT / 'evidence/mvp/note-recovery-final.json')
    deleted_before, deleted_after = [read_json(ROOT / ('evidence/mvp/note-recovery-delete-'+stage+'.json')) for stage in ('before','after')]
    current = version['current_sha256']
    checks = {
        'exact_intake': baseline['intake_main'] == '594ef3cf6138421de8a8c77c7ec1c390e7cfedea',
        'exact_version_paths': set(baseline['sha256']) == set(current) == {'web_r4/research.js','web_r4/index.html'},
        'preserved_parent': all(baseline['sha256'][p] == read_json(ROOT / 'evidence/mvp/knowledge-source-version.json')['current_sha256'][p] for p in current),
        'actual_current_source': all((read_json(ROOT / 'evidence/mvp/draft-baseline.json')['sha256'][p] if p == 'web_r4/index.html' else review_parent_sha(p)) == h for p,h in current.items()),
        'later_manual_draft_source_chain': draft_version_binding()['status'] == 'PASS',
        'actual_parent_archive': sha(ROOT / version['archived_parent']) == baseline['sha256']['web_r4/research.js'] == before['source_sha256'],
        'fixed_cases': all(row['total'] == 5 and {r['id'] for r in row['results']} == NOTE_RECOVERY_CASE_IDS for row in (before,after,final)),
        'first_missing_capability_failures': before['passed'] == 0 and all(r['passed'] is False for r in before['results']),
        'same_test_fixture': before['test_sha256'] == after['test_sha256'] == final['test_sha256'] == sha(ROOT / 'tests_mvp/ui_note_recovery.cjs') and before['fixture_sha256'] == after['fixture_sha256'] == final['fixture_sha256'],
        'intermediate_recovery_passes': after['passed'] == 5 and all(r['passed'] is True for r in after['results']) and after['source_sha256'] == sha(ROOT / version['archived_intermediate']) == deleted_before['source_sha256'],
        'current_recovery_passes': final['passed'] == 5 and all(r['passed'] is True for r in final['results']) and final['source_sha256'] == current['web_r4/research.js'],
        'fixed_deletion_cases': all(row['total'] == 3 and {r['id'] for r in row['results']} == NOTE_RECOVERY_DELETE_CASE_IDS for row in (deleted_before,deleted_after)),
        'first_actual_deletion_failures': deleted_before['passed'] == 0 and all(r['passed'] is False for r in deleted_before['results']),
        'same_deletion_test_fixture': deleted_before['test_sha256'] == deleted_after['test_sha256'] == sha(ROOT / 'tests_mvp/ui_note_recovery_delete.cjs') and deleted_before['fixture_sha256'] == deleted_after['fixture_sha256'],
        'repaired_deletion_passes': deleted_after['passed'] == 3 and all(r['passed'] is True for r in deleted_after['results']) and deleted_after['source_sha256'] == current['web_r4/research.js'],
        'bounded_scope': baseline['schema_change'] is False and baseline['api_change'] is False and version['automatic_write'] is False and version['loaded_revision_cas'] is True,
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}


def draft_version_binding() -> dict:
    import ast
    baseline = read_json(ROOT / 'evidence/mvp/draft-baseline.json')
    version = read_json(ROOT / 'evidence/mvp/draft-source-version.json')
    current = version['current_sha256']
    ui_before = read_json(ROOT / 'evidence/mvp/draft-ui-before-service-head-correction.json')
    ui_after = read_json(ROOT / 'evidence/mvp/draft-ui-after.json')
    stored = read_json(ROOT / 'evidence/mvp/draft-storage-after-corrected.json')
    backed = read_json(ROOT / 'evidence/mvp/draft-backup-after.json')
    ui_final = read_json(ROOT / 'evidence/mvp/draft-ui-scalar-final.json')
    original_ui_test = ROOT / ('evidence/mvp/draft-ui-test-sources/' + ui_after['test_sha256'] + '.cjs')
    backup = (ROOT / 'coach_v1/backup.py').read_text()
    main_validator = next(node for node in ast.parse(backup).body if isinstance(node, ast.FunctionDef) and node.name == '_validate_main_content')
    checks = {
        'exact_intake': baseline['intake_main'] == '0f2b333e44c1918e7a2a9dd7d9f6fce67d1d76a2',
        'exact_current_paths': set(current) == {'coach_v1/draft.py','coach_v1/server.py','coach_v1/backup.py','web_r4/index.html','web_r4/draft.js'},
        'pr8_source_version_retained': set(current) == {'coach_v1/draft.py','coach_v1/server.py','coach_v1/backup.py','web_r4/index.html','web_r4/draft.js'},
        'parent_server_and_backup': all(baseline['sha256'][p] == read_json(ROOT / 'evidence/mvp/knowledge-source-version.json')['current_sha256'][p] for p in ('coach_v1/server.py','coach_v1/backup.py')),
        'parent_index': baseline['sha256']['web_r4/index.html'] == read_json(ROOT / 'evidence/mvp/note-recovery-source-version.json')['current_sha256']['web_r4/index.html'],
        'original_store_unchanged': sha(ROOT / 'coach_v1/storage.py') == baseline['sha256']['coach_v1/storage.py'] == '45e4c4725fd516c66cf9348f1afe9aba8c8bebe8aae574939f8d47394f1ce6e0',
        'research_and_knowledge_unchanged': all(review_parent_sha(p) == baseline['sha256'][p] for p in ('web_r4/research.js','web_r4/knowledge.js')),
        'legacy_main_validator_unchanged': hashlib.sha256(ast.get_source_segment(backup,main_validator).encode()).hexdigest() == '8aad8a6fed29b8305963486421877b2555283a65a5b02eb34864f73c732df690',
        'storage_native_suite_bound': stored['exit_code'] == 0 and stored['draft_tests'] == 31 and stored['legacy_storage_tests'] == 11 and stored['test_sha256'] == sha(ROOT / 'tests_mvp/test_draft_capture.py') and stored['draft_source_sha256'] == current['coach_v1/draft.py'],
        'fixed_ui_cases_bound': ui_before['total'] == ui_after['total'] == 7 and {row['id'] for row in ui_before['results']} == {row['id'] for row in ui_after['results']} and ui_before['test_sha256'] == ui_after['test_sha256'] == sha(original_ui_test) and ui_before['fixture_sha256'] == ui_after['fixture_sha256'],
        'actual_missing_ui_and_repaired_pass': ui_before['source_exists'] is False and ui_before['source_sha256'] is None and ui_before['passed'] == 0 and ui_after['passed'] == 7 and all(row['passed'] for row in ui_after['results']) and ui_after['source_sha256'] == sha(ROOT / version['archived_initial_ui']),
        'pr8_seven_ui_guards': ui_final['passed'] == ui_final['total'] == 7 and all(row['passed'] for row in ui_final['results']) and ui_final['source_sha256'] == current['web_r4/draft.js'] and ui_final['test_sha256'] == ui_after['test_sha256'] == sha(original_ui_test) and ui_final['fixture_sha256'] == ui_after['fixture_sha256'],
        'backup_native_suite_bound': backed['source_sha256'] == current['coach_v1/backup.py'] and backed['draft_source_sha256'] == current['coach_v1/draft.py'] and backed['test_sha256'] == sha(ROOT / 'tests_mvp/test_draft_backup.py') and backed['tests_run'] == 61 and backed['failed_test_methods'] == backed['failure_events'] == backed['error_events'] == 0 and backed['suite_counts'] == {'new_draft_backup':19,'unchanged_legacy_backup':23,'unchanged_knowledge_backup':19},
        'exact_roundtrip_repair': draft_roundtrip_binding()['status'] == 'PASS',
        'bounded_manual_capture': version['main_schema'] == 2 and version['research_schema'] == 2 and version['engine_activation'] is False and version['real_match_coaching_validation_gain'] is False and version['frozen_design_change'] is False,
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}



def draft_roundtrip_binding() -> dict:
    version = read_json(ROOT / 'evidence/mvp/draft-source-version.json')
    first, array_pass, scalar_before, scalar_after = [read_json(ROOT / ('evidence/mvp/draft-roundtrip-'+name+'.json')) for name in ('before','after','scalar-before','scalar-after')]
    cases = {'DRAFT-ROUNDTRIP-UNTOUCHED-NULL-MEMBERSHIP-ORDER', 'DRAFT-ROUNDTRIP-SELECTIVE-EDITS-PRESERVE-OTHER-ROWS', 'DRAFT-ROUNDTRIP-LATE-ACK-KEEPS-CAPTURED-DRAFT-BASE', 'DRAFT-ROUNDTRIP-NEW-INPUT-NO-INFERRED-ROLE-ROWS'}
    checks = {
        'fixed_case_identities': all(row['total'] == 4 and {item['id'] for item in row['results']} == cases for row in (first,array_pass,scalar_before,scalar_after)),
        'original_actual_failure_preserved': first['passed'] == 0 and all(item['passed'] is False for item in first['results']) and first['source_sha256'] == sha(ROOT / version['archived_initial_ui']),
        'array_first_pass_preserved': array_pass['passed'] == 4 and all(item['passed'] is True for item in array_pass['results']) and first['test_sha256'] == array_pass['test_sha256'] and first['fixture_sha256'] == array_pass['fixture_sha256'],
        'array_source_archived': sha(ROOT / version['archived_array_ui']) == array_pass['source_sha256'] == scalar_before['source_sha256'],
        'scalar_actual_failure_preserved': scalar_before['passed'] < 4 and any(item['passed'] is False for item in scalar_before['results']),
        'scalar_fixed_test_fixture': scalar_before['test_sha256'] == scalar_after['test_sha256'] == sha(ROOT / 'tests_mvp/ui_draft_roundtrip.cjs') and scalar_before['fixture_sha256'] == scalar_after['fixture_sha256'],
        'pr8_exact_roundtrip_pass': scalar_after['passed'] == 4 and all(item['passed'] is True for item in scalar_after['results']) and scalar_after['source_sha256'] == version['current_sha256']['web_r4/draft.js'],
        'no_fake_native_evidence': 'synthetic' in scalar_after['verifier'].lower(),
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}



def draft_browser_repair_binding() -> dict:
    import re
    repair = read_json(ROOT / 'evidence/mvp/draft-browser-repair.json')
    failed = read_json(ROOT / repair['failure_receipt'])
    browser = failed['browser']['browser_receipt']
    old = ROOT / repair['archived_before']
    current = ROOT / 'tests_mvp/browser_draft_capture.cjs'
    repaired = ROOT / ('evidence/mvp/draft-browser-sources/' + repair['browser_after_sha256'] + '.cjs')
    identities = lambda p: re.findall(r"check\('([^']+)'", p.read_text())
    checks = {
        'actual_first_failure_retained': failed['run']['id'] == repair['failed_run'] == 37276347795 and failed['run']['attempt'] == repair['failed_attempt'] == 1 and failed['run']['conclusion'] == 'failure' and failed['regression']['status'] == 'PASS' and browser['passed'] is False,
        'actual_visibility_failure': browser['first_failure']['stage'] == 'manual-draft-capture' and 'd-pick-ALLY-1' in browser['first_failure']['error'] and 'not visible' in browser['first_failure']['error'],
        'prior_checks_preserved': len(browser['checks']) == 87 and all(row['passed'] is True for row in browser['checks']) and not browser['page_errors'],
        'actual_test_bytes_archived': sha(old) == repair['browser_before_sha256'] == browser['source_sha256']['tests_mvp/browser_draft_capture.cjs'],
        'repaired_test_archived': sha(repaired) == repair['browser_after_sha256'],
        'same_original_literal_cases': identities(old) == identities(repaired) == identities(current) == repair['literal_case_ids'] and len(identities(current)) == repair['manual_case_count'] == 19 and repair['required_browser_checks'] == 108,
        'production_unchanged_in_failed_run': all(h == browser['source_sha256'][p] for p,h in repair['production_sha256'].items()),
        'actual_tested_tree_and_parents': failed['tested_commit']['sha'] == repair['failed_tested_commit'] == failed['browser']['commit_sha'] and failed['tested_commit']['tree'] == repair['failed_tree'] and failed['tested_commit']['parents'] == [repair['intake_main'],repair['failed_pr_head']],
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}


def draft_retry_binding() -> dict:
    version = read_json(ROOT / 'evidence/mvp/draft-retry-version.json')
    before = read_json(ROOT / 'evidence/mvp/draft-retry-ui-before.json')
    after = read_json(ROOT / 'evidence/mvp/draft-retry-ui-after.json')
    prior = read_json(ROOT / 'evidence/mvp/draft-source-version.json')['current_sha256']
    launch = read_json(ROOT / version['local_browser_launch_failure'] / 'runner.json')
    first_full = read_json(ROOT / version['first_full_verifier_failure'] / 'verification.json')
    case = 'DRAFT-RETRY-NETWORK-LOSS-REUSES-EXACT-REQUEST-THEN-ROTATES-KEY'
    checks = {
        'exact_intake': version['intake_main'] == '6f5c2c30db54f962ac5881a8d628336ca62cd7e5',
        'prior_manual_sources_bound': all(version['prior_sha256'][p] == prior[p]
            for p in ('coach_v1/draft.py', 'coach_v1/server.py', 'web_r4/draft.js')),
        'current_sources_bound': all(review_parent_sha(p) == h for p,h in version['current_sha256'].items()),
        'no_schema_or_activation_change': version['main_schema'] == 2 and version['schema_change'] is False
            and version['coaching_activation'] is False and version['real_match_evidence_gain'] is False,
        'same_ui_case_red_green': before['case_id'] == after['case_id'] == case
            and before['test_sha256'] == after['test_sha256'] == sha(ROOT / 'tests_mvp/ui_draft_retry.cjs'),
        'actual_ui_red': before['passed'] == 0 and before['total'] == 1
            and before['source_sha256'] == prior['web_r4/draft.js'],
        'actual_ui_green': after['passed'] == after['total'] == 1
            and after['source_sha256'] == sha(ROOT / 'web_r4/draft.js'),
        'first_local_browser_failure_retained': launch['passed'] is False
            and launch['browser_receipt_present'] is True
            and launch['browser_receipt_validation']['actual_fresh_browser'] is False,
        'first_full_routing_failure_retained': first_full['passed'] is False
            and first_full['checks']['ui_draft_retry']['status'] == 'FAIL'
            and first_full['checks']['ui_draft_retry']['process_exit_code'] == 0,
        'browser_retry_is_required': version['required_actual_browser_checks'] == 111
            and sha(ROOT / 'tests_mvp/browser_draft_retry.cjs') == version['current_sha256']['tests_mvp/browser_draft_retry.cjs'],
        'frozen_history_preserved': version['frozen_design_change'] is False
            and version['expected_result_change'] is False,
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}


def knowledge_browser_repair_binding() -> dict:
    repair = read_json(ROOT / 'evidence/mvp/knowledge-browser-repair.json')
    failed = read_json(ROOT / repair['failure_receipt'])
    browser = failed['browser']['browser_receipt']
    archive = ROOT / repair['archived_before']
    checks = {
        'actual_first_run_failure_retained': failed['run']['id'] == repair['failed_run'] == 37268245767 and failed['run']['attempt'] == 1 and failed['run']['conclusion'] == 'failure' and failed['regression']['status'] == 'PASS' and browser['passed'] is False,
        'exact_first_failure': [r['id'] for r in browser['checks'] if r['passed'] is False] == [repair['failure_id']],
        'actual_failed_source_archived': sha(archive) == repair['browser_test_before_sha256'] == browser['source_sha256']['tests_mvp/browser_knowledge.cjs'],
        'current_repaired_verifier': review_parent_sha('tests_mvp/browser_knowledge.cjs') == repair['browser_test_after_sha256'],
        'production_unchanged_by_verifier_repair': review_parent_sha('web_r4/knowledge.js') == repair['production_knowledge_sha256'] == browser['source_sha256']['web_r4/knowledge.js'],
        'tested_tree_bound': failed['tested_commit']['tree'] == repair['failed_tree'] and failed['tested_commit']['sha'] == repair['failed_tested_commit'] == failed['browser']['commit_sha'],
        'required_count_preserved': repair['required_browser_checks'] == 79 and repair['knowledge_cases'] == 16,
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}


def note_recovery_browser_repair_binding() -> dict:
    repair = read_json(ROOT / 'evidence/mvp/note-recovery-browser-repair.json')
    failed = read_json(ROOT / repair['failure_receipt'])
    browser = failed['browser']['browser_receipt']
    checks = {
        'actual_first_failure_retained': failed['run']['id'] == repair['failed_run'] == 37270809307 and failed['run']['attempt'] == 1 and failed['run']['conclusion'] == 'failure' and failed['regression']['status'] == 'PASS' and browser['passed'] is False,
        'exact_first_failure': [row['id'] for row in browser['checks'] if row['passed'] is False] == [repair['failure_id']],
        'failed_test_bytes_archived': sha(ROOT / repair['archived_before']) == repair['browser_test_before_sha256'] == browser['source_sha256']['tests_mvp/browser_note_recovery.cjs'],
        'current_repaired_test': review_parent_sha('tests_mvp/browser_note_recovery.cjs') == repair['browser_test_after_sha256'],
        'production_unchanged': sha(ROOT / 'web_r4/research.js') == repair['production_research_sha256'] == browser['source_sha256']['web_r4/research.js'],
        'tested_tree_and_parents': failed['tested_commit']['tree'] == repair['failed_tree'] and failed['tested_commit']['sha'] == repair['failed_tested_commit'] == failed['browser']['commit_sha'] and failed['tested_commit']['parents'] == [read_json(ROOT / 'evidence/mvp/note-recovery-baseline.json')['intake_main'], failed['run']['head']],
        'required_count_preserved': repair['required_browser_checks'] == 89 and repair['recovery_cases'] == 10,
        'independent_completion_reproduction': sha(ROOT / repair['independent_reproducer']) == repair['independent_reproducer_sha256'] == read_json(ROOT / repair['independent_reproduction'])['reproducer_sha256'] and read_json(ROOT / repair['independent_reproduction'])['source_sha256'] == repair['production_research_sha256'] and read_json(ROOT / repair['independent_reproduction'])['changedKeys'] == ['notice'] and all(read_json(ROOT / repair['independent_reproduction'])['checks'].values()),
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
        'actual_current_source':after.get('source_sha256') == review_parent_sha('web_r4/knowledge.js'),
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
    elif name in ("ui-note-recovery", "ui-note-recovery-delete"):
        passed = receipt.get("passed") == count and receipt.get("total") == count
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == (NOTE_RECOVERY_CASE_IDS if name == "ui-note-recovery" else NOTE_RECOVERY_DELETE_CASE_IDS)
        passed = passed and all(row.get("passed") is True for row in receipt.get("results", []))
    elif name in ("ui-draft-capture", "ui-draft-roundtrip", "ui-draft-retry"):
        passed = receipt.get("passed") == count and receipt.get("total") == count
        cases = (DRAFT_UI_CASE_IDS if name == "ui-draft-capture" else
                 DRAFT_ROUNDTRIP_CASE_IDS if name == "ui-draft-roundtrip" else DRAFT_RETRY_CASE_IDS)
        passed = passed and {row.get("id") for row in receipt.get("results", [])} == cases
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
    values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp/note-recovery-sources').glob('*.js')) if p.is_file()})
    values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp/note-recovery-browser-sources').glob('*.cjs')) if p.is_file()})
    values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp').glob('draft-*')) if p.is_file()})
    for folder,pattern in (('draft-ui-test-sources','*.cjs'),('draft-storage-sources','*.py'),('draft-roundtrip-sources','*'),('draft-browser-sources','*.cjs')):
        values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp' / folder).glob(pattern)) if p.is_file()})
    values.update({p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT / 'evidence/mvp/knowledge-review-parent').rglob('*')) if p.is_file()})
    for name in ("evidence/mvp/knowledge-review-parent.json", "evidence/mvp/knowledge-review-version.json", "docs/MVP_KNOWLEDGE_REVIEW.md", "FREEZE_MANIFEST.json", "requirements-r3.txt", R7_SOURCE_RECEIPT, R6_SOURCE_RECEIPT,
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
                 "evidence/mvp/note-recovery-baseline.json", "evidence/mvp/note-recovery-source-version.json", "evidence/mvp/note-recovery-before.json", "evidence/mvp/note-recovery-after.json",
                 "evidence/mvp/note-recovery-final.json", "evidence/mvp/note-recovery-delete-before.json", "evidence/mvp/note-recovery-delete-after.json",
                 "evidence/mvp/note-recovery-browser-repair.json", "evidence/mvp/note-recovery-ci-37270809307-failure.json",
                 "evidence/mvp/note-recovery-delete-order-repro.cjs", "evidence/mvp/note-recovery-delete-order-repro.json",
                 "evidence/mvp/github-ci-visibility.json", "evidence/mvp/manual-capture-ci-37276347795-failure.json",
                 "docs/MVP_DRAFT_CAPTURE.md", "docs/superpowers/plans/2026-10-05-manual-draft-capture.md", "docs/MVP_VALIDATION.md", "docs/MVP_BACKUP.md", "docs/MVP_KNOWLEDGE_PROPOSALS.md", "docs/MVP_NOTE_RECOVERY.md"):
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
        checks["knowledge_review_binding"] = knowledge_review_binding()
        save(out, "knowledge-review-binding.json", checks["knowledge_review_binding"])
        checks["preservation"] = preservation_gate()
        save(out, "preservation.json", checks["preservation"])
        checks["draft_browser_repair_binding"] = draft_browser_repair_binding()
        save(out, "draft-browser-repair-binding.json", checks["draft_browser_repair_binding"])
        checks["knowledge_browser_repair_binding"] = knowledge_browser_repair_binding()
        save(out, "knowledge-browser-repair-binding.json", checks["knowledge_browser_repair_binding"])
        checks["note_recovery_browser_repair_binding"] = note_recovery_browser_repair_binding()
        save(out, "note-recovery-browser-repair-binding.json", checks["note_recovery_browser_repair_binding"])
        checks["ui_repair_receipt_binding"] = repair_binding()
        save(out, "ui-repair-receipt-binding.json", checks["ui_repair_receipt_binding"])
        if any(checks[name]["status"] != "PASS" for name in checks):
            raise RuntimeError("Preservation or UI receipt binding gate failed")
        checks["draft_version_binding"] = draft_version_binding()
        save(out, "draft-version-binding.json", checks["draft_version_binding"])
        if checks["draft_version_binding"]["status"] != "PASS":
            raise RuntimeError("Manual draft source binding gate failed")
        checks["draft_retry_binding"] = draft_retry_binding()
        save(out, "draft-retry-binding.json", checks["draft_retry_binding"])
        if checks["draft_retry_binding"]["status"] != "PASS":
            raise RuntimeError("Manual draft retry binding gate failed")
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
        checks["draft_store"] = run_suite(out, "draft-store", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_draft_capture.py", top_level_dir=str(ROOT)), 31)
        checks["draft_http"] = run_suite(out, "draft-http", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_draft_http.py", top_level_dir=str(ROOT)), 17)
        checks["draft_backup"] = run_suite(out, "draft-backup", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_draft_backup.py", top_level_dir=str(ROOT)), 19)
        checks["note_history_store"] = run_suite(out, "note-history-store", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_note_history.py", top_level_dir=str(ROOT)), 19)
        checks["note_history_http"] = run_suite(out, "note-history-http", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_note_history_http.py", top_level_dir=str(ROOT)), 5)
        checks["knowledge_review"] = run_suite(out, "knowledge-review", unittest.defaultTestLoader.discover(
            str(ROOT / "tests_mvp"), pattern="test_knowledge_review.py", top_level_dir=str(ROOT)), 13)
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
        checks["ui_note_recovery"] = node_check(out, "ui-note-recovery", "tests_mvp/ui_note_recovery.cjs", "web_r4/research.js", 5)
        checks["ui_draft_capture"] = node_check(out, "ui-draft-capture", "tests_mvp/ui_draft_capture.cjs", "web_r4/draft.js", 7)
        checks["ui_draft_roundtrip"] = node_check(out, "ui-draft-roundtrip", "tests_mvp/ui_draft_roundtrip.cjs", "web_r4/draft.js", 4)
        checks["ui_draft_retry"] = node_check(out, "ui-draft-retry", "tests_mvp/ui_draft_retry.cjs", "web_r4/draft.js", 1)
        checks["ui_note_recovery_delete"] = node_check(out, "ui-note-recovery-delete", "tests_mvp/ui_note_recovery_delete.cjs", "web_r4/research.js", 3)
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
