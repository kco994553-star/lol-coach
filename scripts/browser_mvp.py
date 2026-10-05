"""Run new MVP browser regression against an isolated real synthetic server.

Every invocation creates a unique evidence directory and preserves failed runs.
CHROMIUM_EXECUTABLE optionally selects an installed Chromium-compatible binary.
No token values, request headers, or browser traces are written to evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BROWSER_CHECK_COUNT = 50
BROWSER_SOURCE_FILES = ['web_r4/app.js', 'web_r4/index.html', 'web_r4/styles.css',
    'coach_v1/server.py', 'coach_v1/storage.py', 'examples/r3/compare-wait-retreat.json',
    'tests_mvp/browser_save_race.cjs', 'scripts/browser_mvp.py',
    'web_r4/research.js', 'coach_v1/research.py', 'coach_intake/io.py',
    'coach_intake/audit.py', 'coach_intake/video.py', 'tests_mvp/browser_research_bytes.cjs', 'tests_mvp/browser_research_navigation.cjs']


def now():
    return datetime.now(timezone.utc).isoformat()


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in BROWSER_SOURCE_FILES}


def validate_browser_receipt(receipt, hashes):
    if not isinstance(receipt, dict):
        return dict(receipt_present=False)
    checks = receipt.get('checks')
    check_rows = checks if isinstance(checks, list) else []
    check_ids = [row.get('id') for row in check_rows if isinstance(row, dict)]
    valid_check_ids = all(isinstance(value, str) and bool(value) for value in check_ids)
    return dict(receipt_present=True, receipt_passed=receipt.get('passed') is True,
        actual_fresh_browser=receipt.get('evidence_kind') == 'FRESH_BROWSER_EXECUTION',
        browser_version_present=isinstance(receipt.get('browser_version'), str) and bool(receipt['browser_version']),
        check_count_exact=len(check_rows) == EXPECTED_BROWSER_CHECK_COUNT,
        check_ids_unique=valid_check_ids and len(check_ids) == EXPECTED_BROWSER_CHECK_COUNT and len(set(check_ids)) == EXPECTED_BROWSER_CHECK_COUNT,
        all_checks_passed=bool(check_rows) and all(isinstance(row, dict) and row.get('passed') is True for row in check_rows),
        no_first_failure=receipt.get('first_failure') is None,
        no_page_errors=receipt.get('page_errors') == [],
        tested_source_hashes_match_current=receipt.get('source_sha256') == hashes)


def main():
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    evidence = ROOT / 'evidence' / 'mvp' / ('browser-' + run_id)
    evidence.mkdir(parents=True, exist_ok=False)
    started = now()
    initial_source_hashes = source_hashes()
    github_binding = {name: os.environ.get(name) for name in
        ['GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_REPOSITORY', 'GITHUB_WORKFLOW', 'GITHUB_JOB']}
    process_exit = None
    runner_error = None
    server = None
    server_started = False
    child_stdout = ''
    child_stderr = ''
    server_stdout = ''
    token = ''
    with tempfile.TemporaryDirectory(prefix='lol-coach-mvp-browser-') as temporary:
        token_path = Path(temporary) / 'token'
        database = Path(temporary) / 'db.sqlite'
        with (evidence / 'server-stderr.log').open('w') as server_stderr:
            try:
                server_command = [sys.executable, '-m', 'coach_v1.server', '--db', str(database),
                    '--token-file', str(token_path), '--port', '0', '--max-body-bytes', '1000000',
                    '--max-observations', '1000', '--max-actions', '24', '--max-scenarios', '16',
                    '--max-comparisons', '512', '--max-pending-jobs', '8']
                server = subprocess.Popen(server_command, cwd=ROOT, stdout=subprocess.PIPE,
                    stderr=server_stderr, text=True)
                selector = selectors.DefaultSelector()
                selector.register(server.stdout, selectors.EVENT_READ)
                if not selector.select(timeout=20):
                    raise RuntimeError('Isolated server did not announce readiness within 20 seconds')
                startup = server.stdout.readline()
                server_stdout = startup
                selector.close()
                url = startup.strip().split()[-1] if startup.strip() else ''
                if not url.startswith('http://127.0.0.1:'):
                    raise RuntimeError('Isolated server did not return a loopback URL')
                server_started = True
                token = token_path.read_text().strip()
                env = dict(os.environ, WORKBENCH_URL=url, WORKBENCH_TOKEN_FILE=str(token_path),
                    MVP_BROWSER_EVIDENCE_DIR=str(evidence))
                child = subprocess.run(['node', 'tests_mvp/browser_save_race.cjs'], cwd=ROOT,
                    env=env, capture_output=True, text=True, timeout=180)
                process_exit = child.returncode
                child_stdout = child.stdout.replace(token, '[REDACTED]')
                child_stderr = child.stderr.replace(token, '[REDACTED]')
            except Exception as error:
                runner_error = str(error)
                for attribute, log_name in [('stdout', 'child_stdout'), ('stderr', 'child_stderr')]:
                    captured = getattr(error, attribute, None)
                    if captured:
                        captured = captured.decode(errors='replace') if isinstance(captured, bytes) else captured
                        if log_name == 'child_stdout':
                            child_stdout = captured
                        else:
                            child_stderr = captured
                if token_path.exists():
                    token = token_path.read_text().strip()
                    runner_error = runner_error.replace(token, '[REDACTED]')
                    child_stdout = child_stdout.replace(token, '[REDACTED]')
                    child_stderr = child_stderr.replace(token, '[REDACTED]')
            finally:
                if server is not None:
                    server.terminate()
                    try:
                        server.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait(timeout=10)
                    server_stdout += server.stdout.read()
                    if token_path.exists():
                        server_stdout = server_stdout.replace(token_path.read_text().strip(), '[REDACTED]')
                    server.stdout.close()
    (evidence / 'browser-stdout.log').write_text(child_stdout)
    (evidence / 'browser-stderr.log').write_text(child_stderr)
    (evidence / 'server-stdout.log').write_text(server_stdout)
    current_source_hashes = source_hashes()
    browser_receipt = None
    browser_receipt_error = None
    if (evidence / 'receipt.json').exists():
        try:
            browser_receipt = json.loads((evidence / 'receipt.json').read_text())
        except Exception as error:
            browser_receipt_error = str(error)
    validation = validate_browser_receipt(browser_receipt, current_source_hashes)
    validation['launcher_source_hashes_unchanged_during_run'] = initial_source_hashes == current_source_hashes
    verified = process_exit == 0 and runner_error is None and browser_receipt_error is None and all(validation.values())
    receipt = dict(verifier='Actual browser subprocess and isolated synthetic server launcher',
        started_at=started, finished_at=now(), server_started=server_started,
        process_exit_code=process_exit, runner_error=runner_error,
        passed=verified,
        command=['node', 'tests_mvp/browser_save_race.cjs'],
        chromium_executable_override=bool(os.environ.get('CHROMIUM_EXECUTABLE')),
        source_sha256=current_source_hashes, github_binding=github_binding,
        expected_browser_check_count=EXPECTED_BROWSER_CHECK_COUNT, browser_receipt_validation=validation,
        browser_receipt_error=browser_receipt_error,
        browser_receipt_present=(evidence / 'receipt.json').exists(),
        credential_handling='Isolated temporary token file; token values and Authorization headers excluded from logs')
    (evidence / 'runner.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    emitted = json.dumps(dict(runner_receipt=receipt, browser_receipt=browser_receipt,
        evidence_directory=str(evidence)), ensure_ascii=False)
    print(emitted.replace(token, '[REDACTED]') if token else emitted)
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
